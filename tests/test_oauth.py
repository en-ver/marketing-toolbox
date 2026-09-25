"""Focused native OAuth, secure-storage, and generic resolver contracts."""

from __future__ import annotations

import json
import os
import stat
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from google.oauth2.credentials import Credentials as UserCredentials
from typer.testing import CliRunner

from ga4datactl.cli import app as data_app
from ga4datactl.operations import audience_exports
from marketing_common import auth, oauth


class _MemoryBackend:
    def __init__(self) -> None:
        self.records: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.records.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.records[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        del self.records[(service, username)]


def _approved_memory_backend(monkeypatch: pytest.MonkeyPatch) -> _MemoryBackend:
    backend_type = type(
        "Keyring", (_MemoryBackend,), {"__module__": "keyring.backends.macOS"}
    )
    backend = backend_type()
    monkeypatch.setattr(oauth.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        oauth.importlib,
        "import_module",
        lambda _name: SimpleNamespace(Keyring=backend_type),
    )
    monkeypatch.setattr(oauth.keyring, "get_keyring", lambda: backend)
    return backend


def _stored_user_credentials(
    scope: str, *, refresh_token: str = "refresh-token"
) -> UserCredentials:
    return UserCredentials(
        token="access-token",
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes=[scope],
    )


def test_scope_catalog_and_audience_export_use_readonly_access() -> None:
    assert oauth.SCOPE_CATALOG["ga4datactl"] == {
        "read": "https://www.googleapis.com/auth/analytics.readonly"
    }
    assert audience_exports.ANALYTICS_SCOPE == audience_exports.ANALYTICS_READONLY_SCOPE
    assert oauth.SCOPE_CATALOG["ga4adminctl"]["edit"].endswith("analytics.edit")
    assert oauth.SCOPE_CATALOG["gtmctl"]["publish"].endswith("tagmanager.publish")


def test_generic_resolver_precedence_and_explicit_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inline = object()
    file = object()
    ambient = object()
    monkeypatch.setattr(
        auth.service_account.Credentials,
        "from_service_account_info",
        lambda *_args, **_kwargs: inline,
    )
    monkeypatch.setattr(
        auth.google.auth,
        "load_credentials_from_file",
        lambda *_args, **_kwargs: (file, "project"),
    )
    monkeypatch.setattr(
        auth.google.auth, "default", lambda **_kwargs: (ambient, "project")
    )

    assert (
        auth.resolve_credentials(
            ["scope"], tool="ga4datactl", env={"GOOGLE_SERVICE_ACCOUNT_JSON": "{}"}
        )
        is inline
    )
    assert (
        auth.resolve_credentials(
            ["scope"],
            tool="ga4datactl",
            env={"GOOGLE_APPLICATION_CREDENTIALS": "/credentials.json"},
        )
        is file
    )

    def bad_file(*_args: object, **_kwargs: object) -> tuple[object, str]:
        raise OSError("secret path")

    monkeypatch.setattr(auth.google.auth, "load_credentials_from_file", bad_file)
    with pytest.raises(
        auth.CredentialConfigurationError, match="valid readable credential"
    ):
        auth.resolve_credentials(
            ["scope"], tool="ga4datactl", env={"GOOGLE_APPLICATION_CREDENTIALS": "/bad"}
        )


def test_generic_resolver_uses_marked_native_before_ambient(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = object()
    monkeypatch.setattr(auth, "native_marker_exists", lambda *_args: True)
    monkeypatch.setattr(auth, "load_native_credentials", lambda *_args: expected)
    monkeypatch.setattr(
        auth.google.auth,
        "default",
        lambda **_kwargs: pytest.fail("ADC must not be selected"),
    )

    assert (
        auth.resolve_credentials(
            [oauth.SCOPE_CATALOG["ga4datactl"]["read"]], tool="ga4datactl", env={}
        )
        is expected
    )


def test_keyring_allowlist_rejects_unknown_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(oauth.keyring, "get_keyring", lambda: _MemoryBackend())
    monkeypatch.setattr(oauth.platform, "system", lambda: "Darwin")

    with pytest.raises(oauth.OAuthAuthenticationError, match="approved encrypted"):
        oauth.preflight_keyring()


def test_keyring_allowlist_and_sentinel_crud_accept_exact_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = _approved_memory_backend(monkeypatch)

    oauth.preflight_keyring()

    assert backend.records == {}


def test_minimal_record_round_trip_omits_access_token_and_legacy_is_accepted() -> None:
    scope = oauth.SCOPE_CATALOG["ga4datactl"]["read"]
    serialized = oauth._record_from_credentials(_stored_user_credentials(scope), scope)
    minimal = json.loads(serialized)

    assert minimal == {
        "record_version": 1,
        "refresh_token": "refresh-token",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "scopes": [scope],
    }
    assert {"token", "expiry", "token_uri"}.isdisjoint(minimal)
    reconstructed = oauth._credentials_from_record(serialized, scope)
    assert reconstructed.token is None

    legacy = {
        "token": "access-token",
        "refresh_token": "refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "scopes": [scope],
    }
    assert (
        oauth._credentials_from_record(json.dumps(legacy), scope).token
        == "access-token"
    )


def test_record_validation_rejects_scope_mismatch_and_malformed_legacy() -> None:
    scope = oauth.SCOPE_CATALOG["ga4datactl"]["read"]
    minimal = {
        "record_version": 1,
        "refresh_token": "refresh-token",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "scopes": [scope],
    }
    with pytest.raises(oauth.OAuthAuthenticationError, match="invalid"):
        oauth._credentials_from_record(
            json.dumps({**minimal, "scopes": ["other"]}), scope
        )

    legacy_without_token_uri = {
        "token": "access-token",
        "refresh_token": "refresh-token",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "scopes": [scope],
    }
    with pytest.raises(oauth.OAuthAuthenticationError, match="invalid"):
        oauth._credentials_from_record(json.dumps(legacy_without_token_uri), scope)


def test_minimal_record_status_is_offline_and_refresh_stays_in_memory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _approved_memory_backend(monkeypatch)
    scope = oauth.SCOPE_CATALOG["ga4datactl"]["read"]
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    oauth.store_native_credentials(
        "ga4datactl", "read", _stored_user_credentials(scope)
    )
    original = backend.records[(oauth.OAUTH_SERVICE, "ga4datactl:read")]

    def refresh_must_not_run(*_args: object, **_kwargs: object) -> None:
        pytest.fail("status must not refresh")

    monkeypatch.setattr(UserCredentials, "refresh", refresh_must_not_run)
    status = CliRunner().invoke(data_app, ["auth", "status", "--access", "read"])
    assert status.exit_code == 0

    refreshed: list[bool] = []

    def refresh_in_memory(credentials: UserCredentials, _request: object) -> None:
        refreshed.append(True)
        credentials.token = "refreshed-access-token"
        credentials.expiry = datetime.now(UTC) + timedelta(hours=1)
        credentials._granted_scopes = [scope]

    monkeypatch.setattr(UserCredentials, "refresh", refresh_in_memory)
    loaded = oauth.load_native_credentials("ga4datactl", "read", scope)
    assert refreshed == [True]
    assert loaded.token == "refreshed-access-token"
    assert backend.records[(oauth.OAUTH_SERVICE, "ga4datactl:read")] == original


def test_windows_blob_size_limit_has_no_bom_or_terminator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(oauth.platform, "system", lambda: "Windows")

    oauth._validate_windows_blob_size("a" * 1280)
    with pytest.raises(oauth.OAuthAuthenticationError, match="externally managed ADC"):
        oauth._validate_windows_blob_size("a" * 1281)


def test_oversized_windows_record_fails_before_marker_or_secret_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _approved_memory_backend(monkeypatch)
    monkeypatch.setattr(oauth.platform, "system", lambda: "Windows")
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    scope = oauth.SCOPE_CATALOG["ga4datactl"]["read"]
    credentials = _stored_user_credentials(scope)
    credentials._client_secret = "x" * 2000

    with pytest.raises(oauth.OAuthAuthenticationError, match="externally managed ADC"):
        oauth.store_native_credentials("ga4datactl", "read", credentials)

    assert not path.exists()
    assert backend.records == {}


def test_marker_storage_and_forget_ordering_are_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _approved_memory_backend(monkeypatch)
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    credentials = _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"])

    oauth.store_native_credentials("ga4datactl", "read", credentials)
    assert json.loads(path.read_text()) == {"version": 1, "storage": "keyring"}
    assert backend.records

    oauth.forget_native_credentials("ga4datactl", "read")
    assert not path.exists()
    assert backend.records == {}


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("failure", ["mismatch", "read_error"])
def test_store_rolls_back_readback_failures_after_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    existing: bool,
    failure: str,
) -> None:
    class ReadbackFailureBackend(_MemoryBackend):
        failure: str | None = None
        fail_next_read = False

        def get_password(self, service: str, username: str) -> str | None:
            if self.fail_next_read:
                self.fail_next_read = False
                if self.failure == "read_error":
                    raise RuntimeError("keyring read failed")
                return "mismatch"
            return super().get_password(service, username)

        def set_password(self, service: str, username: str, password: str) -> None:
            super().set_password(service, username, password)
            if self.failure is not None:
                self.fail_next_read = True

    backend_type = type(
        "Keyring", (ReadbackFailureBackend,), {"__module__": "keyring.backends.macOS"}
    )
    backend = backend_type()
    monkeypatch.setattr(oauth.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        oauth.importlib,
        "import_module",
        lambda _name: SimpleNamespace(Keyring=backend_type),
    )
    monkeypatch.setattr(oauth.keyring, "get_keyring", lambda: backend)
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    credentials = _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"])

    if existing:
        oauth.store_native_credentials("ga4datactl", "read", credentials)
    old = backend.records.get((oauth.OAUTH_SERVICE, "ga4datactl:read"))
    backend.failure = failure

    replacement = _stored_user_credentials(
        oauth.SCOPE_CATALOG["ga4datactl"]["read"], refresh_token="replacement-token"
    )
    with pytest.raises(
        oauth.OAuthAuthenticationError, match="Credential storage failed"
    ):
        oauth.store_native_credentials("ga4datactl", "read", replacement)

    assert backend.records.get((oauth.OAUTH_SERVICE, "ga4datactl:read")) == old
    assert path.exists() is existing


def test_store_preserves_a_fail_closed_marker_when_cleanup_is_indeterminate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class IndeterminateReadBackend(_MemoryBackend):
        reads = 0

        def get_password(self, service: str, username: str) -> str | None:
            self.reads += 1
            if self.reads > 1:
                raise RuntimeError("keyring read failed")
            return super().get_password(service, username)

    backend_type = type(
        "Keyring", (IndeterminateReadBackend,), {"__module__": "keyring.backends.macOS"}
    )
    backend = backend_type()
    monkeypatch.setattr(oauth.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        oauth.importlib,
        "import_module",
        lambda _name: SimpleNamespace(Keyring=backend_type),
    )
    monkeypatch.setattr(oauth.keyring, "get_keyring", lambda: backend)
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    with pytest.raises(oauth.OAuthAuthenticationError, match="state is uncertain"):
        oauth.store_native_credentials(
            "ga4datactl",
            "read",
            _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
        )

    assert path.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX marker checks")
def test_marker_rejects_unsafe_parent_permissions_and_foreign_ownership(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"version": 1, "storage": "keyring"}')
    path.chmod(0o600)
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    path.parent.chmod(0o722)
    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.native_marker_exists("ga4datactl", "read")

    path.parent.chmod(0o700)
    owner = os.geteuid()
    monkeypatch.setattr(oauth.os, "geteuid", lambda: owner + 1)
    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.native_marker_exists("ga4datactl", "read")


def test_marker_rejects_symlinks_and_non_directory_parents(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    path.parent.mkdir(parents=True)
    target = tmp_path / "marker.json"
    target.write_text('{"version": 1, "storage": "keyring"}')
    path.symlink_to(target)
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.native_marker_exists("ga4datactl", "read")

    path.unlink()
    path.parent.rmdir()
    path.parent.write_text("not a directory")
    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.native_marker_exists("ga4datactl", "read")


def test_validate_native_record_requires_a_marker_before_keyring_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        oauth,
        "marker_path",
        lambda *_args: tmp_path / "oauth" / "ga4datactl" / "read.json",
    )
    monkeypatch.setattr(
        oauth,
        "_approved_backend",
        lambda: pytest.fail("an absent marker must not initialize keyring"),
    )

    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is missing"):
        oauth.validate_native_record(
            "ga4datactl", "read", oauth.SCOPE_CATALOG["ga4datactl"]["read"]
        )


def test_forget_retains_marker_when_secret_deletion_is_uncertain(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class FailingDeleteBackend(_MemoryBackend):
        def delete_password(self, service: str, username: str) -> None:
            raise RuntimeError("locked")

    backend_type = type(
        "Keyring", (FailingDeleteBackend,), {"__module__": "keyring.backends.macOS"}
    )
    backend = backend_type()
    monkeypatch.setattr(oauth.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        oauth.importlib,
        "import_module",
        lambda _name: SimpleNamespace(Keyring=backend_type),
    )
    monkeypatch.setattr(oauth.keyring, "get_keyring", lambda: backend)
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"version": 1, "storage": "keyring"}')
    path.chmod(0o600)
    backend.records[(oauth.OAUTH_SERVICE, "ga4datactl:read")] = "value"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    with pytest.raises(oauth.OAuthAuthenticationError, match="unavailable"):
        oauth.forget_native_credentials("ga4datactl", "read")
    assert path.exists()


def test_login_uses_loopback_pkce_offline_and_no_forced_consent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(oauth.OAuthRequestError, match="--port is required"):
        oauth.login_native_credentials(
            "ga4datactl",
            "read",
            tmp_path / "client.json",
            open_browser=False,
            port=None,
        )

    captured: dict[str, Any] = {}

    class Flow:
        client_type = "installed"

        def run_local_server(self, **kwargs: Any) -> UserCredentials:
            captured.update(kwargs)
            return _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"])

    def from_file(*_args: object, **kwargs: Any) -> Flow:
        captured["factory"] = kwargs
        return Flow()

    monkeypatch.setattr(oauth.InstalledAppFlow, "from_client_secrets_file", from_file)
    monkeypatch.setattr(oauth, "preflight_keyring", lambda: None)
    monkeypatch.setattr(oauth, "store_native_credentials", lambda *_args: None)

    oauth.login_native_credentials(
        "ga4datactl", "read", tmp_path / "client.json", open_browser=False, port=8765
    )

    assert captured["factory"]["autogenerate_code_verifier"] is True
    assert captured["host"] == captured["bind_addr"] == "127.0.0.1"
    assert captured["port"] == 8765
    assert captured["access_type"] == "offline"
    assert "prompt" not in captured


def test_keyring_initialization_failure_is_a_sanitized_cli_authentication_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "oauth" / "ga4datactl" / "read.json"
    path.parent.mkdir(parents=True)
    path.write_text('{"version": 1, "storage": "keyring"}')
    path.chmod(0o600)
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(
        oauth.importlib,
        "import_module",
        lambda _name: SimpleNamespace(Keyring=_MemoryBackend),
    )
    monkeypatch.setattr(
        oauth.keyring,
        "get_keyring",
        lambda: (_ for _ in ()).throw(RuntimeError("configured backend failed")),
    )

    result = CliRunner().invoke(data_app, ["auth", "status", "--access", "read"])

    assert result.exit_code == 4
    diagnostic = json.loads(result.stderr)
    assert diagnostic["category"] == "authentication"
    assert "configured backend failed" not in diagnostic["message"]


def test_auth_commands_are_registered_and_preserve_json_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    called: dict[str, Any] = {}
    monkeypatch.setattr(
        "marketing_common.oauth_cli.login_native_credentials",
        lambda *args, **kwargs: called.update(args=args, kwargs=kwargs),
    )
    client = tmp_path / "client.json"
    client.write_text("{}")
    runner = CliRunner()

    help_result = runner.invoke(data_app, ["auth", "--help"])
    result = runner.invoke(
        data_app, ["auth", "login", "--client-secrets", str(client), "--access", "read"]
    )

    assert help_result.exit_code == 0
    assert (
        "forget" in help_result.stdout
        and "revoke" in help_result.stdout
        and "logout" not in help_result.stdout
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"] == {"stored": True, "access": "read"}
    assert called["kwargs"] == {"open_browser": True, "port": None}

    monkeypatch.setattr(
        "marketing_common.oauth_cli.login_native_credentials",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            oauth.OAuthAuthenticationError("storage unavailable")
        ),
    )
    failed = runner.invoke(
        data_app, ["auth", "login", "--client-secrets", str(client), "--access", "read"]
    )
    assert failed.exit_code == 4
    assert json.loads(failed.stderr)["category"] == "authentication"


@pytest.mark.parametrize("subcommand", ["login", "status", "forget", "revoke"])
def test_auth_commands_reject_unsupported_access_before_actions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, subcommand: str
) -> None:
    def action(*_args: object, **_kwargs: object) -> None:
        pytest.fail("unsupported access must be rejected before auth actions")

    monkeypatch.setattr("marketing_common.oauth_cli.login_native_credentials", action)
    monkeypatch.setattr("marketing_common.oauth_cli.native_marker_exists", action)
    monkeypatch.setattr("marketing_common.oauth_cli.forget_native_credentials", action)
    monkeypatch.setattr("marketing_common.oauth_cli.revoke_native_credentials", action)
    client = tmp_path / "client.json"
    client.write_text("{}")
    args = ["auth", subcommand, "--access", "unsupported"]
    if subcommand == "login":
        args.extend(["--client-secrets", str(client)])
    if subcommand == "revoke":
        args.extend(["--apply", "--acknowledge-project-wide-revocation"])

    result = CliRunner().invoke(data_app, args)

    assert result.exit_code == 2
    diagnostic = json.loads(result.stderr)
    assert diagnostic["category"] == "invalid_request"
    assert diagnostic["message"] == "Unsupported native OAuth access tier."


def test_forget_reports_local_only_without_claiming_remote_grant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "marketing_common.oauth_cli.forget_native_credentials", lambda *_args: None
    )

    result = CliRunner().invoke(data_app, ["auth", "forget", "--access", "read"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["data"] == {
        "forgotten": True,
        "access": "read",
        "remoteRevocationAttempted": False,
    }


def test_auth_login_rejects_no_browser_without_port_before_actions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        "marketing_common.oauth_cli.login_native_credentials",
        lambda *_args, **_kwargs: pytest.fail("invalid options must not start login"),
    )
    client = tmp_path / "client.json"
    client.write_text("{}")

    result = CliRunner().invoke(
        data_app,
        [
            "auth",
            "login",
            "--client-secrets",
            str(client),
            "--access",
            "read",
            "--no-open-browser",
        ],
    )

    assert result.exit_code == 2
    diagnostic = json.loads(result.stderr)
    assert diagnostic["category"] == "invalid_request"
    assert diagnostic["message"] == "--port is required with --no-open-browser."


def test_revoke_retains_local_record_on_remote_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"])
    monkeypatch.setattr(oauth, "validate_native_record", lambda *_args: credentials)
    monkeypatch.setattr(
        oauth,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("offline")),
    )
    monkeypatch.setattr(
        oauth,
        "forget_native_credentials",
        lambda *_args: pytest.fail("must retain local record"),
    )

    with pytest.raises(
        oauth.OAuthAuthenticationError, match="local credential was retained"
    ):
        oauth.revoke_native_credentials("ga4datactl", "read")


def test_revoke_requires_explicit_acknowledgement_and_reports_blast_radius(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "marketing_common.oauth_cli.revoke_native_credentials", lambda *_args: None
    )
    runner = CliRunner()

    denied = runner.invoke(data_app, ["auth", "revoke", "--access", "read"])
    applied = runner.invoke(
        data_app,
        [
            "auth",
            "revoke",
            "--access",
            "read",
            "--apply",
            "--acknowledge-project-wide-revocation",
        ],
    )

    assert denied.exit_code == 2
    assert json.loads(denied.stderr)["category"] == "invalid_request"
    assert applied.exit_code == 0
    assert "other affected local tiers" in json.loads(applied.stdout)["data"]["warning"]


def test_marker_is_durable_before_initial_secret_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _MemoryBackend()
    path = tmp_path / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)
    monkeypatch.setattr(
        oauth,
        "_write_marker",
        lambda *_args: (_ for _ in ()).throw(
            oauth.OAuthAuthenticationError("marker durability failed")
        ),
    )

    with pytest.raises(oauth.OAuthAuthenticationError, match="marker durability"):
        oauth.store_native_credentials(
            "ga4datactl",
            "read",
            _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
        )

    assert backend.records == {}


@pytest.mark.parametrize("after_commit", [False, True])
def test_interrupted_initial_store_retains_marker_and_blocks_adc(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, after_commit: bool
) -> None:
    class InterruptBackend(_MemoryBackend):
        def set_password(self, service: str, username: str, password: str) -> None:
            if after_commit:
                super().set_password(service, username, password)
            raise KeyboardInterrupt

    backend = InterruptBackend()
    path = tmp_path / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)

    with pytest.raises(KeyboardInterrupt):
        oauth.store_native_credentials(
            "ga4datactl",
            "read",
            _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
        )

    assert oauth.native_marker_exists("ga4datactl", "read")
    monkeypatch.setattr(
        auth,
        "load_native_credentials",
        lambda *_args: (_ for _ in ()).throw(
            oauth.OAuthAuthenticationError("marked state requires recovery")
        ),
    )
    monkeypatch.setattr(
        auth.google.auth,
        "default",
        lambda **_kwargs: pytest.fail("ADC must not be selected for a marked state"),
    )
    with pytest.raises(auth.CredentialConfigurationError, match="requires recovery"):
        auth.resolve_credentials(
            [oauth.SCOPE_CATALOG["ga4datactl"]["read"]], tool="ga4datactl", env={}
        )


def test_ordinary_post_commit_failure_is_compensated_for_initial_store(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class CommitThenFailBackend(_MemoryBackend):
        def set_password(self, service: str, username: str, password: str) -> None:
            super().set_password(service, username, password)
            raise RuntimeError("ordinary backend failure")

    backend = CommitThenFailBackend()
    path = tmp_path / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)

    with pytest.raises(
        oauth.OAuthAuthenticationError, match="partial credential was removed"
    ):
        oauth.store_native_credentials(
            "ga4datactl",
            "read",
            _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
        )

    assert backend.records == {}
    assert not path.exists()


def test_inconsistent_record_and_marker_is_preserved_for_forget_recovery(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _MemoryBackend()
    path = tmp_path / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    backend.records[(oauth.OAUTH_SERVICE, "ga4datactl:read")] = "unmarked-value"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)

    with pytest.raises(oauth.OAuthAuthenticationError, match="auth forget"):
        oauth.store_native_credentials(
            "ga4datactl",
            "read",
            _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
        )

    assert oauth.native_marker_exists("ga4datactl", "read")
    assert backend.records[(oauth.OAUTH_SERVICE, "ga4datactl:read")] == "unmarked-value"


def test_marked_missing_secret_is_not_overwritten_by_login(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _MemoryBackend()
    path = tmp_path / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)
    oauth._write_marker(path)

    with pytest.raises(oauth.OAuthAuthenticationError, match="auth forget"):
        oauth.store_native_credentials(
            "ga4datactl",
            "read",
            _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
        )

    assert oauth.native_marker_exists("ga4datactl", "read")
    assert backend.records == {}


def test_forget_verifies_absence_and_can_retry_marked_missing_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class StaleReadBackend(_MemoryBackend):
        stale_readback = True

        def get_password(self, service: str, username: str) -> str | None:
            if self.stale_readback and (service, username) not in self.records:
                self.stale_readback = False
                return "stale"
            return super().get_password(service, username)

    backend = StaleReadBackend()
    path = tmp_path / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)
    oauth._write_marker(path)
    backend.records[(oauth.OAUTH_SERVICE, "ga4datactl:read")] = "value"

    with pytest.raises(oauth.OAuthAuthenticationError, match="could not be verified"):
        oauth.forget_native_credentials("ga4datactl", "read")
    assert path.exists()

    oauth.forget_native_credentials("ga4datactl", "read")
    assert not path.exists()
    assert backend.records == {}


@pytest.mark.skipif(os.name != "posix", reason="POSIX marker checks")
def test_missing_config_is_absent_without_keyring_or_directory_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    missing_base = tmp_path / "missing" / "config"
    path = missing_base / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    ambient = object()
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(
        oauth,
        "_approved_backend",
        lambda: pytest.fail("an absent marker must not initialize keyring"),
    )
    monkeypatch.setattr(auth.google.auth, "default", lambda **_kwargs: (ambient, None))

    assert not oauth.native_marker_exists("ga4datactl", "read")
    assert (
        auth.resolve_credentials(
            [oauth.SCOPE_CATALOG["ga4datactl"]["read"]],
            tool="ga4datactl",
            env={},
        )
        is ambient
    )
    assert (
        CliRunner().invoke(data_app, ["auth", "status", "--access", "read"]).exit_code
        == 0
    )
    assert (
        CliRunner().invoke(data_app, ["auth", "forget", "--access", "read"]).exit_code
        == 0
    )
    assert not missing_base.exists()


@pytest.mark.skipif(os.name != "posix", reason="POSIX marker checks")
def test_first_store_creates_nested_missing_config_components_privately(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    backend = _MemoryBackend()
    base = tmp_path / "missing" / "nested-config"
    path = base / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)

    oauth.store_native_credentials(
        "ga4datactl",
        "read",
        _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
    )

    for directory in (
        tmp_path / "missing",
        base,
        base / "marketing-toolbox",
        base / "marketing-toolbox" / "oauth",
        base / "marketing-toolbox" / "oauth" / "ga4datactl",
    ):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert path.exists()
    assert backend.records


@pytest.mark.skipif(os.name != "posix", reason="POSIX marker checks")
def test_missing_marker_under_an_existing_unsafe_ancestor_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = tmp_path / "unsafe-config"
    base.mkdir(mode=0o700)
    base.chmod(0o722)
    path = base / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.native_marker_exists("ga4datactl", "read")


@pytest.mark.skipif(os.name != "posix", reason="POSIX fsync ordering")
@pytest.mark.parametrize(
    ("base", "failed_parent", "created_directory"),
    [
        (
            lambda tmp_path: tmp_path / "missing" / "nested-config",
            lambda tmp_path: tmp_path,
            lambda tmp_path: tmp_path / "missing",
        ),
        (
            lambda tmp_path: tmp_path / "existing-config",
            lambda tmp_path: tmp_path / "existing-config",
            lambda tmp_path: tmp_path / "existing-config" / "marketing-toolbox",
        ),
    ],
    ids=["configured-base", "app-root"],
)
def test_store_retry_resyncs_partial_directory_creation_before_marker_and_secret(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    base: Any,
    failed_parent: Any,
    created_directory: Any,
) -> None:
    base_path = base(tmp_path)
    if base_path.name == "existing-config":
        base_path.mkdir(mode=0o700)
    path = base_path / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    parent_to_resync = failed_parent(tmp_path)
    backend = _MemoryBackend()
    events: list[tuple[str, Path | None]] = []
    fail_once = True
    original_replace = oauth._replace_marker
    original_set = backend.set_password

    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(oauth, "_approved_backend", lambda: backend)

    def sync(directory: Path) -> None:
        nonlocal fail_once
        events.append(("sync", directory))
        if fail_once and directory == parent_to_resync:
            fail_once = False
            raise OSError("interrupted parent sync")

    def replace(temporary: Path, destination: Path) -> None:
        events.append(("marker", None))
        original_replace(temporary, destination)

    def set_password(service: str, username: str, password: str) -> None:
        events.append(("secret", None))
        original_set(service, username, password)

    monkeypatch.setattr(oauth, "_sync_directory", sync)
    monkeypatch.setattr(oauth, "_replace_marker", replace)
    monkeypatch.setattr(backend, "set_password", set_password)

    with pytest.raises(oauth.OAuthAuthenticationError, match="Could not write"):
        oauth.store_native_credentials(
            "ga4datactl",
            "read",
            _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
        )
    assert created_directory(tmp_path).is_dir()
    assert backend.records == {}

    events.clear()
    oauth.store_native_credentials(
        "ga4datactl",
        "read",
        _stored_user_credentials(oauth.SCOPE_CATALOG["ga4datactl"]["read"]),
    )

    assert events.index(("sync", parent_to_resync)) < events.index(("marker", None))
    assert events.index(("marker", None)) < events.index(("secret", None))


@pytest.mark.skipif(os.name != "posix", reason="POSIX marker checks")
def test_marker_hierarchy_rejects_unsafe_ancestors_and_app_symlinks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = tmp_path / "base"
    app_root = base / "marketing-toolbox"
    path = app_root / "oauth" / "ga4datactl" / "read.json"
    path.parent.mkdir(parents=True)
    base.chmod(0o700)
    app_root.chmod(0o722)
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.native_marker_exists("ga4datactl", "read")

    app_root.chmod(0o700)
    for child in (app_root / "oauth" / "ga4datactl", app_root / "oauth"):
        child.rmdir()
    app_root.rmdir()
    target = base / "target"
    target.mkdir()
    app_root.symlink_to(target, target_is_directory=True)

    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.native_marker_exists("ga4datactl", "read")


@pytest.mark.skipif(os.name != "posix", reason="POSIX marker checks")
def test_forget_rejects_unsafe_path_before_keyring_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    base = tmp_path / "base"
    app_root = base / "marketing-toolbox"
    path = app_root / "oauth" / "ga4datactl" / "read.json"
    path.parent.mkdir(parents=True)
    base.chmod(0o700)
    app_root.chmod(0o722)
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)
    monkeypatch.setattr(
        oauth,
        "_approved_backend",
        lambda: pytest.fail("unsafe paths must not initialize keyring"),
    )

    with pytest.raises(oauth.OAuthAuthenticationError, match="marker is invalid"):
        oauth.forget_native_credentials("ga4datactl", "read")


@pytest.mark.skipif(os.name != "posix", reason="POSIX marker checks")
def test_marker_creates_private_components_under_permissive_umask_and_allows_redirect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    target_base = tmp_path / "target-base"
    target_base.mkdir(mode=0o700)
    redirect_base = tmp_path / "redirect-base"
    redirect_base.symlink_to(target_base, target_is_directory=True)
    path = redirect_base / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    previous_umask = os.umask(0)
    try:
        oauth._write_marker(path)
    finally:
        os.umask(previous_umask)

    assert oauth.native_marker_exists("ga4datactl", "read")
    for directory in (
        target_base / "marketing-toolbox",
        target_base / "marketing-toolbox" / "oauth",
        target_base / "marketing-toolbox" / "oauth" / "ga4datactl",
    ):
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS /var redirect")
def test_marker_accepts_macos_var_to_private_redirect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    private_var = Path("/private/var")
    if not Path("/var").is_symlink() or not tmp_path.is_relative_to(private_var):
        pytest.skip("temporary directory is not under macOS /private/var")
    base = tmp_path / "marker-base"
    base.mkdir(mode=0o700)
    redirected_base = Path("/var") / base.relative_to(private_var)
    path = redirected_base / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    monkeypatch.setattr(oauth, "marker_path", lambda *_args: path)

    oauth._write_marker(path)

    assert oauth.native_marker_exists("ga4datactl", "read")


@pytest.mark.skipif(os.name != "posix", reason="POSIX fsync ordering")
def test_marker_durability_syncs_file_before_replace_and_directory_after(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = (
        tmp_path / "base" / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    )
    path.parent.mkdir(parents=True)
    events: list[str] = []
    original_replace = os.replace
    monkeypatch.setattr(oauth, "_sync_file", lambda _descriptor: events.append("file"))
    monkeypatch.setattr(
        oauth, "_sync_directory", lambda _directory: events.append("directory")
    )

    def replace(source: Path | str, destination: Path | str) -> None:
        events.append("replace")
        original_replace(source, destination)

    monkeypatch.setattr(oauth.os, "replace", replace)
    oauth._write_marker(path)

    assert events[-3:] == ["file", "replace", "directory"]


@pytest.mark.skipif(os.name != "posix", reason="POSIX fsync ordering")
def test_marker_deletion_syncs_its_containing_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = (
        tmp_path / "base" / "marketing-toolbox" / "oauth" / "ga4datactl" / "read.json"
    )
    path.parent.mkdir(parents=True)
    path.write_text('{"version": 1, "storage": "keyring"}', encoding="utf-8")
    path.chmod(0o600)
    synchronized: list[Path] = []
    monkeypatch.setattr(
        oauth, "_sync_directory", lambda directory: synchronized.append(directory)
    )

    oauth._delete_marker(path)

    assert synchronized == [path.parent]
    assert not path.exists()


def test_windows_reparse_points_are_rejected_in_app_directories(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from marketing_common import _win32_marker

    monkeypatch.setattr(oauth.os, "name", "nt")
    monkeypatch.setattr(_win32_marker, "is_reparse_point", lambda _path: True)

    with pytest.raises(ValueError, match="unsafe marker directory"):
        oauth._validate_app_directory(tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="requires native Windows APIs")
def test_windows_marker_helper_replaces_flushed_temp_file(tmp_path: Path) -> None:
    from marketing_common import _win32_marker

    temporary = tmp_path / "marker.tmp"
    destination = tmp_path / "marker.json"
    temporary.write_text("new", encoding="utf-8")
    with temporary.open("r+", encoding="utf-8") as file:
        file.flush()
        os.fsync(file.fileno())
    destination.write_text("old", encoding="utf-8")

    _win32_marker.replace_file(temporary, destination)

    assert destination.read_text(encoding="utf-8") == "new"
    assert not temporary.exists()
