"""Native installed-app OAuth storage and flow support.

Native records are persisted only through reviewed OS keyring backends. The
non-secret marker records durable local intent before a keyring mutation, so a
broken native record cannot silently change the identity selected by ADC.
"""

from __future__ import annotations

import contextlib
import importlib
import json
import os
import platform
import secrets
import stat
import sys
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


def preflight_keyring() -> None:
    """Prove the approved backend can perform a non-secret CRUD round trip."""
    backend = _approved_backend()
    username = f"preflight:{secrets.token_urlsafe(16)}"
    sentinel = secrets.token_urlsafe(24)
    _keyring_call(backend.set_password, OAUTH_SERVICE, username, sentinel)
    try:
        if _keyring_call(backend.get_password, OAUTH_SERVICE, username) != sentinel:
            raise OAuthAuthenticationError(
                "Secure credential storage verification failed."
            )
    finally:
        _keyring_call(backend.delete_password, OAUTH_SERVICE, username)


def _marker_components(path: Path) -> tuple[Path, Path, Path, Path]:
    try:
        tool_directory = path.parent
        oauth_directory = tool_directory.parent
        app_root = oauth_directory.parent
    except IndexError as exc:
        raise OAuthAuthenticationError("Native credential marker is invalid.") from exc
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


def native_marker_exists(tool: ToolName, access: str) -> bool:
    return _validate_marker(marker_path(tool, access))


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
                os.mkdir(directory, mode=0o700)
                _validate_app_directory(directory)
        for directory in (app_root, oauth_directory, tool_directory):
            try:
                _validate_app_directory(directory)
            except FileNotFoundError:
                if directory != app_root:
                    _validate_app_directory(directory.parent)
                os.mkdir(directory, mode=0o700)
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
            os.mkdir(directory, mode=0o700)
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


def validate_native_record(tool: ToolName, access: str, scope: str) -> UserCredentials:
    """Validate a marked record without refreshing or contacting Google."""
    if not _validate_marker(marker_path(tool, access)):
        raise OAuthAuthenticationError("Native credential marker is missing.")
    backend = _approved_backend()
    serialized = _keyring_call(
        backend.get_password, OAUTH_SERVICE, _record_name(tool, access)
    )
    if not isinstance(serialized, str):
        raise OAuthAuthenticationError(
            "Native credential is missing from secure storage."
        )
    return _credentials_from_record(serialized, scope)


def load_native_credentials(tool: ToolName, access: str, scope: str) -> Credentials:
    """Load the marked credential, refreshing only its in-memory access token."""
    credentials = validate_native_record(tool, access, scope)
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


def store_native_credentials(
    tool: ToolName, access: str, credentials: UserCredentials
) -> None:
    """Store a verified record after durable marker intent is established."""
    scope = scope_for_access(tool, access)
    serialized = _record_from_credentials(credentials, scope)
    _validate_windows_blob_size(serialized)
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


def forget_native_credentials(tool: ToolName, access: str) -> None:
    """Delete and verify the secret before removing its recovery marker."""
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


def revoke_native_credentials(tool: ToolName, access: str) -> None:
    scope = scope_for_access(tool, access)
    credentials = validate_native_record(tool, access, scope)
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
        forget_native_credentials(tool, access)
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
