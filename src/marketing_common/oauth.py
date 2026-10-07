"""Native installed-app OAuth storage and flow support.

Native records are persisted only through reviewed OS keyring backends. The
non-secret marker records durable local intent before a keyring mutation, so a
broken native record cannot silently change the identity selected by ADC.
"""

from __future__ import annotations

import contextlib
import errno
import importlib
import json
import os
import platform
import secrets
import stat
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal, cast
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

import keyring
import typer
from google.auth.credentials import Credentials, TokenState
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]

ToolName = Literal["ga4datactl", "ga4adminctl", "gtmctl"]

OAUTH_SERVICE = "marketing-toolbox.oauth"
MARKER_VERSION = 1
RECORD_VERSION = 1
WINDOWS_CREDENTIAL_BLOB_LIMIT = 2560
CALLBACK_TIMEOUT_SECONDS = 600
REVOCATION_ENDPOINT = "https://oauth2.googleapis.com/revoke"
_NATIVE_OAUTH_LOCK_TIMEOUT_SECONDS = 5.0
_NATIVE_OAUTH_LOCK_POLL_SECONDS = 0.05
_native_oauth_thread_lock = threading.Lock()

SCOPE_CATALOG: dict[ToolName, dict[str, str]] = {
    "ga4datactl": {"read": "https://www.googleapis.com/auth/analytics.readonly"},
    "ga4adminctl": {
        "read": "https://www.googleapis.com/auth/analytics.readonly",
        "edit": "https://www.googleapis.com/auth/analytics.edit",
    },
    "gtmctl": {
        "read": "https://www.googleapis.com/auth/tagmanager.readonly",
        "users": "https://www.googleapis.com/auth/tagmanager.manage.users",
        "accounts": "https://www.googleapis.com/auth/tagmanager.manage.accounts",
        "containers": "https://www.googleapis.com/auth/tagmanager.edit.containers",
        "versions": "https://www.googleapis.com/auth/tagmanager.edit.containerversions",
        "publish": "https://www.googleapis.com/auth/tagmanager.publish",
        "delete": "https://www.googleapis.com/auth/tagmanager.delete.containers",
    },
}


class OAuthAuthenticationError(ValueError):
    """Raised for safe-to-display native OAuth and storage failures."""


class OAuthRequestError(ValueError):
    """Raised when native OAuth command inputs violate their contract."""


class RemoteRevokedCleanupError(OAuthAuthenticationError):
    """The remote grant was revoked, but local record cleanup did not complete."""


def scope_for_access(tool: ToolName, access: str) -> str:
    try:
        return SCOPE_CATALOG[tool][access]
    except KeyError as exc:
        raise OAuthRequestError("Unsupported native OAuth access tier.") from exc


def validate_login_request(
    tool: ToolName, access: str, *, open_browser: bool, port: int | None
) -> str:
    """Validate native login inputs before accessing credentials or the browser."""
    scope = scope_for_access(tool, access)
    if not open_browser and port is None:
        raise OAuthRequestError("--port is required with --no-open-browser.")
    if port is not None and not 1 <= port <= 65535:
        raise OAuthRequestError("--port must be between 1 and 65535.")
    return scope


def access_for_scope(tool: ToolName, scopes: list[str] | tuple[str, ...]) -> str | None:
    if len(scopes) != 1:
        return None
    return next(
        (access for access, scope in SCOPE_CATALOG[tool].items() if scope == scopes[0]),
        None,
    )


def _record_name(tool: ToolName, access: str) -> str:
    return f"{tool}:{access}"


def marker_path(tool: ToolName, access: str) -> Path:
    return (
        Path(typer.get_app_dir("marketing-toolbox", roaming=False))
        / "oauth"
        / tool
        / f"{access}.json"
    )


def _approved_backend() -> Any:
    """Return only exact reviewed keyring classes on their native platforms."""
    approved = {
        "Darwin": ("keyring.backends.macOS", "Keyring"),
        "Windows": ("keyring.backends.Windows", "WinVaultKeyring"),
        "Linux": ("keyring.backends.SecretService", "Keyring"),
    }.get(platform.system())
    if approved is None:
        raise OAuthAuthenticationError(
            "An approved encrypted OS keyring is unavailable; configure Keychain, "
            "Windows Credential Locker, or Secret Service, or use externally managed ADC."
        )
    try:
        module = importlib.import_module(approved[0])
        expected_class = getattr(module, approved[1])
        backend = keyring.get_keyring()
    except Exception as exc:
        raise OAuthAuthenticationError(
            "An approved encrypted OS keyring is unavailable; configure Keychain, "
            "Windows Credential Locker, or Secret Service, or use externally managed ADC."
        ) from exc
    if type(backend) is not expected_class:
        raise OAuthAuthenticationError(
            "An approved encrypted OS keyring is unavailable; configure Keychain, "
            "Windows Credential Locker, or Secret Service, or use externally managed ADC."
        )
    return backend


def _keyring_call(operation: Any, *args: str) -> Any:
    try:
        return operation(*args)
    except Exception as exc:  # keyring backends expose backend-specific errors
        raise OAuthAuthenticationError(
            "Secure credential storage is unavailable."
        ) from exc


def _preflight_keyring_unlocked() -> None:
    """Prove the approved backend can perform a non-secret CRUD round trip."""
    backend = _approved_backend()
    username = f"preflight:{secrets.token_urlsafe(16)}"
    sentinel = secrets.token_urlsafe(24)
    try:
        _keyring_call(backend.set_password, OAUTH_SERVICE, username, sentinel)
    except OAuthAuthenticationError:
        with contextlib.suppress(OAuthAuthenticationError):
            _keyring_call(backend.delete_password, OAUTH_SERVICE, username)
        raise
    try:
        if _keyring_call(backend.get_password, OAUTH_SERVICE, username) != sentinel:
            raise OAuthAuthenticationError(
                "Secure credential storage verification failed."
            )
    finally:
        _keyring_call(backend.delete_password, OAUTH_SERVICE, username)


def preflight_keyring() -> None:
    with _native_oauth_lock():
        _preflight_keyring_unlocked()


def _marker_components(path: Path) -> tuple[Path, Path, Path, Path]:
    tool_directory = path.parent
    oauth_directory = tool_directory.parent
    app_root = oauth_directory.parent
    return app_root.parent, app_root, oauth_directory, tool_directory


def _validate_posix_ancestor(details: os.stat_result, *, allow_symlink: bool) -> None:
    if stat.S_ISLNK(details.st_mode):
        if allow_symlink and details.st_uid in (os.geteuid(), 0):
            return
        raise ValueError("unsafe marker ancestor")
    if not stat.S_ISDIR(details.st_mode):
        raise ValueError("unsafe marker ancestor")
    if details.st_uid not in (os.geteuid(), 0):
        raise ValueError("unsafe marker ancestor")
    writable = details.st_mode & 0o022
    if writable and not details.st_mode & stat.S_ISVTX:
        raise ValueError("unsafe marker ancestor")


def _validate_posix_boundary(base: Path, *, allow_missing: bool) -> None:
    """Validate existing lexical and resolved ancestors of a configuration base."""
    lexical = Path(os.path.abspath(base))
    anchor = lexical
    while True:
        try:
            anchor.lstat()
            break
        except FileNotFoundError:
            if not allow_missing or anchor.parent == anchor:
                raise
            anchor = anchor.parent

    for candidate in (anchor, *anchor.parents):
        _validate_posix_ancestor(candidate.lstat(), allow_symlink=True)

    resolved = anchor.resolve(strict=True)
    for candidate in (resolved, *resolved.parents):
        _validate_posix_ancestor(candidate.lstat(), allow_symlink=False)


def _validate_app_directory(directory: Path) -> None:
    details = directory.lstat()
    if not stat.S_ISDIR(details.st_mode):
        raise ValueError("unsafe marker directory")
    if os.name == "posix" and (
        details.st_uid != os.geteuid() or details.st_mode & 0o022
    ):
        raise ValueError("unsafe marker directory")
    if os.name == "nt":
        from . import _win32_marker

        if _win32_marker.is_reparse_point(directory):
            raise ValueError("unsafe marker directory")


def _validate_marker_hierarchy(path: Path, *, allow_missing: bool) -> None:
    base, app_root, oauth_directory, tool_directory = _marker_components(path)
    if os.name == "posix":
        _validate_posix_boundary(base, allow_missing=allow_missing)
    for directory in (app_root, oauth_directory, tool_directory):
        try:
            _validate_app_directory(directory)
        except FileNotFoundError:
            if allow_missing:
                return
            raise


def _validate_marker(path: Path) -> bool:
    try:
        details = path.lstat()
    except FileNotFoundError:
        try:
            _validate_marker_hierarchy(path, allow_missing=True)
        except (OSError, ValueError) as exc:
            raise OAuthAuthenticationError(
                "Native credential marker is invalid."
            ) from exc
        return False
    except OSError as exc:
        raise OAuthAuthenticationError("Native credential marker is invalid.") from exc
    try:
        _validate_marker_hierarchy(path, allow_missing=False)
        if not stat.S_ISREG(details.st_mode) or (
            os.name == "posix"
            and (details.st_uid != os.geteuid() or details.st_mode & 0o077)
        ):
            raise ValueError("unsafe marker")
        if os.name == "nt":
            from . import _win32_marker

            if _win32_marker.is_reparse_point(path):
                raise ValueError("unsafe marker")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data != {"version": MARKER_VERSION, "storage": "keyring"}:
            raise ValueError("invalid marker")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise OAuthAuthenticationError("Native credential marker is invalid.") from exc
    return True


def _validated_native_marker_present_unlocked(tool: ToolName, access: str) -> bool:
    return _validate_marker(marker_path(tool, access))


def _canonical_oauth_lock_path() -> Path:
    """Return the stable per-user lock path, independent of marker overrides."""
    if os.name == "nt":
        from . import _win32_marker

        return (
            _win32_marker.canonical_local_app_data()
            / "marketing-toolbox"
            / "oauth"
            / "_locks"
            / f"{OAUTH_SERVICE}.lock"
        )
    try:
        import pwd

        home = Path(pwd.getpwuid(os.geteuid()).pw_dir)
    except (ImportError, KeyError, OSError) as exc:
        raise OAuthAuthenticationError(
            "Native credential storage coordination is unavailable."
        ) from exc
    base = home / (
        "Library/Application Support" if platform.system() == "Darwin" else ".config"
    )
    return base / "marketing-toolbox" / "oauth" / "_locks" / f"{OAUTH_SERVICE}.lock"


def _validate_lock_hierarchy(path: Path, *, allow_missing: bool) -> None:
    """Require the app-owned lock hierarchy to remain private."""
    _validate_marker_hierarchy(path, allow_missing=allow_missing)
    if os.name != "posix":
        return
    _, app_root, oauth_directory, locks_directory = _marker_components(path)
    for directory in (app_root, oauth_directory, locks_directory):
        try:
            details = directory.lstat()
        except FileNotFoundError:
            if allow_missing:
                return
            raise
        if stat.S_IMODE(details.st_mode) != 0o700:
            raise ValueError("unsafe lock directory")


def _validate_lock_file(path: Path, descriptor: int, *, created: bool) -> None:
    details = os.fstat(descriptor)
    if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
        raise ValueError("unsafe lock file")
    if os.name == "posix":
        if details.st_uid != os.geteuid():
            raise ValueError("unsafe lock file")
        if created:
            os.fchmod(descriptor, 0o600)
            details = os.fstat(descriptor)
        if stat.S_IMODE(details.st_mode) != 0o600:
            raise ValueError("unsafe lock file")
    elif os.name == "nt":
        from . import _win32_marker

        if _win32_marker.is_reparse_point(path):
            raise ValueError("unsafe lock file")


def _open_native_oauth_lock_file(path: Path) -> int:
    """Open the persistent lock file using the marker hierarchy protections."""
    _validate_lock_hierarchy(path, allow_missing=True)
    try:
        _validate_lock_hierarchy(path, allow_missing=False)
    except FileNotFoundError:
        _ensure_marker_directory(path)
        _validate_lock_hierarchy(path, allow_missing=False)
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    created = False
    try:
        descriptor = os.open(path, flags, 0o600)
        created = True
    except FileExistsError:
        descriptor = os.open(
            path,
            os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    try:
        os.set_inheritable(descriptor, False)
        _validate_lock_file(path, descriptor, created=created)
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _lock_is_contended(exc: OSError) -> bool:
    return exc.errno in (errno.EACCES, errno.EAGAIN)


def _acquire_os_lock(descriptor: int, timeout_seconds: float) -> None:
    if os.name == "nt":
        import msvcrt

        def try_lock() -> None:
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)  # type: ignore[attr-defined]

    else:
        import fcntl

        def try_lock() -> None:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)

    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            try_lock()
            return
        except OSError as exc:
            if not _lock_is_contended(exc):
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise OAuthAuthenticationError(
                    "Native credential storage is busy; retry."
                ) from exc
            time.sleep(min(_NATIVE_OAUTH_LOCK_POLL_SECONDS, remaining))


def _release_os_lock(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)  # type: ignore[attr-defined]
    else:
        import fcntl

        fcntl.flock(descriptor, fcntl.LOCK_UN)


@contextlib.contextmanager
def _native_oauth_lock() -> Iterator[None]:
    """Serialize local marker/keyring transactions for the shared service."""
    try:
        path = _canonical_oauth_lock_path()
    except OAuthAuthenticationError:
        raise
    except Exception as exc:
        raise OAuthAuthenticationError(
            "Native credential storage coordination is unavailable."
        ) from exc

    thread_wait_started = time.monotonic()
    if not _native_oauth_thread_lock.acquire(
        timeout=_NATIVE_OAUTH_LOCK_TIMEOUT_SECONDS
    ):
        raise OAuthAuthenticationError("Native credential storage is busy; retry.")
    os_contention_budget = max(
        0.0,
        _NATIVE_OAUTH_LOCK_TIMEOUT_SECONDS - (time.monotonic() - thread_wait_started),
    )
    descriptor: int | None = None
    locked = False
    try:
        try:
            # Opening and validating the persistent lock file is filesystem work,
            # not lock contention. Only thread and OS lock waits share this budget.
            descriptor = _open_native_oauth_lock_file(path)
            _acquire_os_lock(descriptor, os_contention_budget)
            locked = True
        except OAuthAuthenticationError:
            raise
        except (OSError, ValueError) as exc:
            raise OAuthAuthenticationError(
                "Native credential storage coordination is unavailable."
            ) from exc
        yield
    finally:
        try:
            if descriptor is not None:
                try:
                    if locked:
                        _release_os_lock(descriptor)
                finally:
                    os.close(descriptor)
        except OSError as exc:
            raise OAuthAuthenticationError(
                "Native credential storage coordination is unavailable."
            ) from exc
        finally:
            _native_oauth_thread_lock.release()


def _sync_file(file_descriptor: int) -> None:
    os.fsync(file_descriptor)


def _sync_directory(directory: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_marker_directory(path: Path) -> None:
    base, app_root, oauth_directory, tool_directory = _marker_components(path)
    if os.name == "posix":
        _validate_posix_boundary(base, allow_missing=True)
        lexical_base = Path(os.path.abspath(base))
        base_directories = (*reversed(lexical_base.parents), lexical_base)
        for directory in base_directories:
            try:
                directory.lstat()
            except FileNotFoundError:
                try:
                    os.mkdir(directory, mode=0o700)
                except FileExistsError:
                    pass
                _validate_app_directory(directory)
        for directory in (app_root, oauth_directory, tool_directory):
            try:
                _validate_app_directory(directory)
            except FileNotFoundError:
                if directory != app_root:
                    _validate_app_directory(directory.parent)
                try:
                    os.mkdir(directory, mode=0o700)
                except FileExistsError:
                    pass
                _validate_app_directory(directory)

        # Re-sync every entry from the configured base to the tool directory.
        # This makes a retry recover from a prior mkdir whose parent sync failed.
        synchronized: set[Path] = set()
        for directory in (
            *base_directories[1:],
            app_root,
            oauth_directory,
            tool_directory,
        ):
            parent = directory.parent
            if parent not in synchronized:
                _sync_directory(parent)
                synchronized.add(parent)
        return

    for directory in (app_root, oauth_directory, tool_directory):
        try:
            _validate_app_directory(directory)
        except FileNotFoundError:
            parent = directory.parent
            if directory != app_root:
                _validate_app_directory(parent)
            try:
                os.mkdir(directory, mode=0o700)
            except FileExistsError:
                pass
            _sync_directory(parent)
            _validate_app_directory(directory)


def _replace_marker(temporary: Path, path: Path) -> None:
    if os.name == "nt":
        from . import _win32_marker

        _win32_marker.replace_file(temporary, path)
    else:
        os.replace(temporary, path)
    _sync_directory(path.parent)


def _write_marker(path: Path) -> None:
    """Durably create or rewrite marker intent before a secret mutation."""
    temporary: Path | None = None
    try:
        _validate_marker(path)
        _ensure_marker_directory(path)
        temporary = path.parent / f".{path.name}.{secrets.token_hex(8)}.tmp"
        descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump({"version": MARKER_VERSION, "storage": "keyring"}, file)
            file.flush()
            _sync_file(file.fileno())
        _replace_marker(temporary, path)
    except (OSError, ValueError) as exc:
        raise OAuthAuthenticationError(
            "Could not write the native credential marker."
        ) from exc
    finally:
        if temporary is not None:
            with contextlib.suppress(OSError):
                temporary.unlink()


def _delete_marker(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise OAuthAuthenticationError(
            "Could not remove the native credential marker."
        ) from exc
    try:
        _sync_directory(path.parent)
    except OSError as exc:
        raise OAuthAuthenticationError(
            "Could not remove the native credential marker."
        ) from exc


def _record_from_credentials(credentials: UserCredentials, scope: str) -> str:
    data = {
        "record_version": RECORD_VERSION,
        "refresh_token": credentials.refresh_token,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": [scope],
    }
    if not all(
        isinstance(data[field], str) and data[field]
        for field in ("refresh_token", "client_id", "client_secret")
    ):
        raise OAuthAuthenticationError(
            "OAuth authorization did not return a refresh token."
        )
    return json.dumps(data, separators=(",", ":"))


def _credentials_from_record(serialized: str, scope: str) -> UserCredentials:
    try:
        info = json.loads(serialized)
        if not isinstance(info, dict) or info.get("scopes") != [scope]:
            raise ValueError
        credential_fields: tuple[str, ...]
        if "record_version" in info:
            required = {
                "record_version",
                "refresh_token",
                "client_id",
                "client_secret",
                "scopes",
            }
            if (
                set(info) != required
                or info["record_version"] != RECORD_VERSION
                or type(info["record_version"]) is not int
            ):
                raise ValueError
            credential_fields = ("refresh_token", "client_id", "client_secret")
        else:
            credential_fields = (
                "refresh_token",
                "client_id",
                "client_secret",
                "token_uri",
            )
        if not all(
            isinstance(info.get(field), str) and info[field]
            for field in credential_fields
        ):
            raise ValueError
        credentials = cast(
            UserCredentials,
            UserCredentials.from_authorized_user_info(info),  # type: ignore[no-untyped-call]
        )
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise OAuthAuthenticationError("Stored native credential is invalid.") from exc
    return credentials


def _validate_windows_blob_size(serialized: str) -> None:
    """Enforce the pinned Windows backend's length-delimited UTF-16LE limit."""
    if (
        platform.system() == "Windows"
        and len(serialized.encode("utf-16-le")) > WINDOWS_CREDENTIAL_BLOB_LIMIT
    ):
        raise OAuthAuthenticationError(
            "Native credential is too large for Windows Credential Locker; "
            "use externally managed ADC."
        )


def _read_native_record_unlocked(
    tool: ToolName, access: str, scope: str
) -> tuple[str, UserCredentials]:
    """Read one marked keyring record while the native lifecycle lock is held."""
    if not _validated_native_marker_present_unlocked(tool, access):
        raise OAuthAuthenticationError("Native credential marker is missing.")
    backend = _approved_backend()
    serialized = _keyring_call(
        backend.get_password, OAUTH_SERVICE, _record_name(tool, access)
    )
    if not isinstance(serialized, str):
        raise OAuthAuthenticationError(
            "Native credential is missing from secure storage."
        )
    return serialized, _credentials_from_record(serialized, scope)


def _read_optional_native_record(
    tool: ToolName, access: str, scope: str
) -> UserCredentials | None:
    """Read a strict local snapshot only while its validated marker remains present."""
    if not _validated_native_marker_present_unlocked(tool, access):
        return None
    with _native_oauth_lock():
        if not _validated_native_marker_present_unlocked(tool, access):
            return None
        _, credentials = _read_native_record_unlocked(tool, access, scope)
        return credentials


def native_record_status(tool: ToolName, access: str, scope: str) -> bool:
    """Validate a present marker/keyring record as one local snapshot."""
    return _read_optional_native_record(tool, access, scope) is not None


def _refresh_native_credentials(
    credentials: UserCredentials, scope: str
) -> Credentials:
    """Refresh only after the local record snapshot lock has been released."""
    if credentials.token_state is not TokenState.FRESH:
        original_refresh_token = credentials.refresh_token
        try:
            credentials.refresh(Request())  # type: ignore[no-untyped-call]
        except Exception as exc:
            raise OAuthAuthenticationError(
                "Native credential refresh failed; run auth login again."
            ) from exc
        if credentials.refresh_token != original_refresh_token:
            raise OAuthAuthenticationError(
                "Native credential refresh rotated its token; run auth login again."
            )
        granted = credentials.granted_scopes
        if granted is not None and scope not in granted:
            raise OAuthAuthenticationError(
                "Native credential no longer grants the required scope."
            )
    return credentials


def load_native_credentials_if_present(
    tool: ToolName, access: str, scope: str
) -> Credentials | None:
    """Atomically load a selected native record or report its safe absence."""
    credentials = _read_optional_native_record(tool, access, scope)
    if credentials is None:
        return None
    return _refresh_native_credentials(credentials, scope)


def _restore_record(backend: Any, name: str, old: str | None) -> bool:
    """Best-effort compensation that succeeds only after readback verification."""
    if old is not None:
        try:
            _keyring_call(backend.set_password, OAUTH_SERVICE, name, old)
            return (
                cast(
                    str | None, _keyring_call(backend.get_password, OAUTH_SERVICE, name)
                )
                == old
            )
        except OAuthAuthenticationError:
            return False
    with contextlib.suppress(OAuthAuthenticationError):
        _keyring_call(backend.delete_password, OAUTH_SERVICE, name)
    try:
        return (
            cast(str | None, _keyring_call(backend.get_password, OAUTH_SERVICE, name))
            is None
        )
    except OAuthAuthenticationError:
        return False


def _mark_inconsistent_state(path: Path) -> None:
    """Retain durable recovery intent without mutating an uncertain secret."""
    _write_marker(path)
    raise OAuthAuthenticationError(
        "Local credential state is inconsistent; run auth forget, then login again."
    )


def _store_native_credentials_unlocked(
    tool: ToolName, access: str, scope: str, serialized: str
) -> None:
    """Store a record and compensate while the native lifecycle lock is held."""
    backend = _approved_backend()
    name = _record_name(tool, access)
    path = marker_path(tool, access)
    has_marker = _validate_marker(path)
    old = _keyring_call(backend.get_password, OAUTH_SERVICE, name)

    if has_marker:
        if not isinstance(old, str):
            _mark_inconsistent_state(path)
        try:
            _credentials_from_record(old, scope)
        except OAuthAuthenticationError:
            _mark_inconsistent_state(path)
    elif old is not None:
        _mark_inconsistent_state(path)

    initial = not has_marker
    _write_marker(path)
    try:
        _keyring_call(backend.set_password, OAUTH_SERVICE, name, serialized)
        readback = _keyring_call(backend.get_password, OAUTH_SERVICE, name)
        if readback != serialized:
            raise OAuthAuthenticationError(
                "Secure credential storage verification failed."
            )
        _credentials_from_record(readback, scope)
    except OAuthAuthenticationError as exc:
        if not _restore_record(backend, name, old):
            raise OAuthAuthenticationError(
                "Credential storage failed; local credential state is uncertain."
            ) from exc
        if not initial:
            raise OAuthAuthenticationError(
                "Credential storage failed; the previous credential was restored."
            ) from exc
        try:
            _delete_marker(path)
        except OAuthAuthenticationError as cleanup_exc:
            raise OAuthAuthenticationError(
                "Credential storage failed; local cleanup is incomplete; run auth forget."
            ) from cleanup_exc
        raise OAuthAuthenticationError(
            "Credential storage failed; the partial credential was removed."
        ) from exc


def store_native_credentials(
    tool: ToolName, access: str, credentials: UserCredentials
) -> None:
    """Store a verified record after durable marker intent is established."""
    scope = scope_for_access(tool, access)
    serialized = _record_from_credentials(credentials, scope)
    _validate_windows_blob_size(serialized)
    with _native_oauth_lock():
        _store_native_credentials_unlocked(tool, access, scope, serialized)


def _forget_native_credentials_unlocked(tool: ToolName, access: str) -> None:
    """Delete and verify a marked secret while the lifecycle lock is held."""
    path = marker_path(tool, access)
    if not _validate_marker(path):
        return
    backend = _approved_backend()
    name = _record_name(tool, access)
    existing = _keyring_call(backend.get_password, OAUTH_SERVICE, name)
    if existing is not None:
        _keyring_call(backend.delete_password, OAUTH_SERVICE, name)
    if _keyring_call(backend.get_password, OAUTH_SERVICE, name) is not None:
        raise OAuthAuthenticationError(
            "Secure credential storage deletion could not be verified."
        )
    _delete_marker(path)


def forget_native_credentials(tool: ToolName, access: str) -> None:
    """Delete and verify the secret before removing its recovery marker."""
    if not _validated_native_marker_present_unlocked(tool, access):
        return
    with _native_oauth_lock():
        _forget_native_credentials_unlocked(tool, access)


def revoke_native_credentials(tool: ToolName, access: str) -> None:
    scope = scope_for_access(tool, access)
    with _native_oauth_lock():
        serialized, credentials = _read_native_record_unlocked(tool, access, scope)
    refresh_token = credentials.refresh_token
    assert refresh_token is not None
    request = UrlRequest(
        REVOCATION_ENDPOINT,
        data=urlencode({"token": refresh_token}).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            if response.status not in (200, 204):
                raise OSError("unexpected revocation response")
    except (OSError, URLError) as exc:
        raise OAuthAuthenticationError(
            "Remote revocation failed; local credential was retained."
        ) from exc
    try:
        with _native_oauth_lock():
            path = marker_path(tool, access)
            if not _validate_marker(path):
                return
            backend = _approved_backend()
            current = _keyring_call(
                backend.get_password, OAUTH_SERVICE, _record_name(tool, access)
            )
            if current is None:
                _delete_marker(path)
                return
            if current != serialized:
                raise RemoteRevokedCleanupError(
                    "Remote grant was revoked, but a concurrent local replacement was preserved; review it before running auth forget."
                )
            _forget_native_credentials_unlocked(tool, access)
    except RemoteRevokedCleanupError:
        raise
    except OAuthAuthenticationError as exc:
        raise RemoteRevokedCleanupError(
            "Remote grant was revoked, but local cleanup is incomplete; run auth forget."
        ) from exc


def login_native_credentials(
    tool: ToolName,
    access: str,
    client_secrets: Path,
    *,
    open_browser: bool,
    port: int | None,
) -> None:
    """Run the loopback installed-app flow after storage is proven usable."""
    scope = validate_login_request(tool, access, open_browser=open_browser, port=port)
    preflight_keyring()
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets), scopes=[scope], autogenerate_code_verifier=True
        )
        if flow.client_type != "installed":
            raise ValueError("not an installed client")
        with contextlib.redirect_stdout(sys.stderr):
            credentials = flow.run_local_server(
                host="127.0.0.1",
                bind_addr="127.0.0.1",
                port=0 if port is None else port,
                open_browser=open_browser,
                authorization_prompt_message="Open this URL to authorize: {url}",
                timeout_seconds=CALLBACK_TIMEOUT_SECONDS,
                access_type="offline",
            )
    except OAuthAuthenticationError:
        raise
    except Exception as exc:
        raise OAuthAuthenticationError("OAuth login did not complete.") from exc
    if not isinstance(credentials, UserCredentials):
        raise OAuthAuthenticationError("OAuth login did not return user credentials.")
    granted = credentials.granted_scopes
    if granted is not None and scope not in granted:
        raise OAuthAuthenticationError("OAuth login did not grant the required scope.")
    store_native_credentials(tool, access, credentials)
