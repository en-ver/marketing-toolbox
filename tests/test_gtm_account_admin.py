"""Contracts for guarded GTM account and account-permission administration."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest
from httplib2 import Response
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations, reads, transport


class FakeRequest:
    def __init__(self, response: dict[str, Any] | None) -> None:
        self.response = response
        self.retries: list[int] = []
        self.callbacks: list[Callable[[Response], None]] = []

    def add_response_callback(self, callback: Callable[[Response], None]) -> None:
        self.callbacks.append(callback)

    def execute(self, *, num_retries: int = 0) -> dict[str, Any] | None:
        self.retries.append(num_retries)
        for callback in self.callbacks:
            callback(Response({"status": "200"}))
        return self.response


class FakeAdminResource:
    def __init__(self, response: dict[str, Any] | None) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeAdminResource:
        return self

    def user_permissions(self) -> FakeAdminResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            fake_request = FakeRequest(self.response)
            self.requests.append(fake_request)
            return fake_request

        return request


@pytest.mark.parametrize(
    ("operation", "args", "expected", "access"),
    [
        (
            mutations.update_account,
            ("accounts/1", {"name": "account"}, "fp"),
            (
                "update",
                {
                    "path": "accounts/1",
                    "body": {"name": "account"},
                    "fingerprint": "fp",
                },
            ),
            "accounts",
        ),
        (
            mutations.create_user_permission,
            ("accounts/1", {"emailAddress": "a@example.test"}),
            (
                "create",
                {"parent": "accounts/1", "body": {"emailAddress": "a@example.test"}},
            ),
            "users",
        ),
        (
            mutations.update_user_permission,
            ("accounts/1/user_permissions/2", {"emailAddress": "a@example.test"}),
            (
                "update",
                {
                    "path": "accounts/1/user_permissions/2",
                    "body": {"emailAddress": "a@example.test"},
                },
            ),
            "users",
        ),
        (
            mutations.delete_user_permission,
            ("accounts/1/user_permissions/2",),
            ("delete", {"path": "accounts/1/user_permissions/2"}),
            "users",
        ),
    ],
)
def test_account_admin_mutations_use_exact_discovery_calls_and_access_tiers(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
    access: str,
) -> None:
    service = FakeAdminResource({"path": "response"})
    requested_accesses: list[str] = []
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda value: (requested_accesses.append(value), object())[1],
    )

    assert operation(*args, service_factory=lambda _: service) == {"path": "response"}
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    assert requested_accesses == [access]


def test_user_permission_delete_normalizes_empty_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeAdminResource(None)
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())

    assert (
        mutations.delete_user_permission(
            "accounts/1/user_permissions/2", service_factory=lambda _: service
        )
        == {}
    )


@pytest.mark.parametrize(
    ("operation", "args", "expected"),
    [
        (
            reads.get_user_permission,
            ("accounts/1/user_permissions/2",),
            ("get", {"path": "accounts/1/user_permissions/2"}),
        ),
        (
            reads.list_user_permissions,
            ("accounts/1",),
            ("list", {"parent": "accounts/1", "pageToken": "next"}),
        ),
    ],
)
def test_user_permission_reads_use_one_direct_manage_users_request(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service = FakeAdminResource({"nextPageToken": "next", "userPermission": []})
    requested_accesses: list[str] = []
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda value: (requested_accesses.append(value), object())[1],
    )
    kwargs = {"page_token": "next"} if operation is reads.list_user_permissions else {}

    assert (
        operation(*args, **kwargs, service_factory=lambda _: service)
        == service.response
    )
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    assert requested_accesses == ["users"]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "body.json"
    path.write_text(
        '{"emailAddress":"private@example.test","accountAccess":{"permission":"admin"}}'
    )
    return str(path)


@pytest.mark.parametrize(
    ("args", "acknowledgement"),
    [
        (
            [
                "accounts",
                "update",
                "--path",
                "accounts/1",
                "--body",
                "ignored",
                "--fingerprint",
                "fp",
                "--apply",
            ],
            "--acknowledge-account-update",
        ),
        (
            [
                "accounts",
                "user-permissions",
                "create",
                "--parent",
                "accounts/1",
                "--body",
                "ignored",
                "--apply",
            ],
            "--acknowledge-permission-change",
        ),
        (
            [
                "accounts",
                "user-permissions",
                "update",
                "--path",
                "accounts/1/user_permissions/2",
                "--body",
                "ignored",
                "--apply",
            ],
            "--acknowledge-permission-change",
        ),
        (
            [
                "accounts",
                "user-permissions",
                "delete",
                "--path",
                "accounts/1/user_permissions/2",
                "--apply",
            ],
            "--acknowledge-permission-change",
        ),
    ],
)
def test_account_admin_mutations_require_operation_acknowledgements(
    args: list[str], acknowledgement: str
) -> None:
    result = CliRunner().invoke(app, args)

    assert result.exit_code == 2
    assert acknowledgement in result.output


def test_user_permission_delete_requires_explicit_delete_acknowledgement() -> None:
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "user-permissions",
            "delete",
            "--path",
            "accounts/1/user_permissions/2",
            "--acknowledge-permission-change",
            "--dry-run",
        ],
    )

    assert result.exit_code == 2
    assert "--acknowledge-user-permission-delete" in result.output


def test_account_update_apply_maps_canonical_path_body_and_fingerprint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []
    monkeypatch.setattr(
        mutations,
        "update_account",
        lambda path, body, fingerprint: (
            calls.__iadd__([(path, body, fingerprint)]),
            {"path": path},
        )[1],
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "update",
            "--path",
            "accounts/1",
            "--body",
            _body_file(tmp_path),
            "--fingerprint",
            "fp",
            "--acknowledge-account-update",
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        (
            "accounts/1",
            {
                "emailAddress": "private@example.test",
                "accountAccess": {"permission": "admin"},
            },
            "fp",
        )
    ]


@pytest.mark.parametrize(
    "args",
    [
        [
            "accounts",
            "user-permissions",
            "get",
            "--path",
            "accounts/1/user_permissions/2",
        ],
        ["accounts", "user-permissions", "list", "--parent", "accounts/1"],
    ],
)
def test_permission_reads_require_sensitive_data_ack_before_credentials(
    monkeypatch: pytest.MonkeyPatch, args: list[str]
) -> None:
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda _: pytest.fail("credentials must not load"),
    )
    result = CliRunner().invoke(app, args)

    assert result.exit_code == 2
    assert "--acknowledge-sensitive-data" in result.output


def test_permission_read_returns_direct_one_page_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response = {
        "nextPageToken": "next",
        "userPermission": [{"emailAddress": "private@example.test"}],
    }
    monkeypatch.setattr(
        reads, "list_user_permissions", lambda parent, page_token: response
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "user-permissions",
            "list",
            "--parent",
            "accounts/1",
            "--page-token",
            "first",
            "--acknowledge-sensitive-data",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.output)["data"] == response
