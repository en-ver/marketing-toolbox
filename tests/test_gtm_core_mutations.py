"""Focused contracts for standard GTM container and workspace mutations."""

from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.retries: list[int] = []

    def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
        self.retries.append(num_retries)
        return self.response


class FakeCoreResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeCoreResource:
        return self

    def containers(self) -> FakeCoreResource:
        return self

    def workspaces(self) -> FakeCoreResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            fake_request = FakeRequest(self.response)
            self.requests.append(fake_request)
            return fake_request

        return request


@pytest.mark.parametrize(
    ("operation", "args", "expected"),
    [
        (
            mutations.create_container,
            ("accounts/1", {"name": "container"}),
            ("create", {"parent": "accounts/1", "body": {"name": "container"}}),
        ),
        (
            mutations.update_container,
            ("accounts/1/containers/2", {"name": "container"}, "fingerprint"),
            (
                "update",
                {
                    "path": "accounts/1/containers/2",
                    "body": {"name": "container"},
                    "fingerprint": "fingerprint",
                },
            ),
        ),
        (
            mutations.create_workspace,
            ("accounts/1/containers/2", {"name": "workspace"}),
            (
                "create",
                {
                    "parent": "accounts/1/containers/2",
                    "body": {"name": "workspace"},
                },
            ),
        ),
        (
            mutations.update_workspace,
            (
                "accounts/1/containers/2/workspaces/3",
                {"name": "workspace"},
                "fingerprint",
            ),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/workspaces/3",
                    "body": {"name": "workspace"},
                    "fingerprint": "fingerprint",
                },
            ),
        ),
        (
            mutations.delete_container,
            ("accounts/1/containers/2",),
            ("delete", {"path": "accounts/1/containers/2"}),
        ),
        (
            mutations.delete_workspace,
            ("accounts/1/containers/2/workspaces/3",),
            ("delete", {"path": "accounts/1/containers/2/workspaces/3"}),
        ),
    ],
)
def test_core_mutations_map_one_official_edit_request(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service = FakeCoreResource({"name": "response"})
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )

    assert operation(*args, service_factory=lambda _: service) == service.response
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    expected_scope = (
        mutations.TAG_MANAGER_DELETE_CONTAINERS_SCOPE
        if operation in {mutations.delete_container, mutations.delete_workspace}
        else mutations.TAG_MANAGER_EDIT_SCOPE
    )
    assert scopes == [[expected_scope]]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "body.json"
    path.write_text('{"name":"private"}')
    return str(path)


@pytest.mark.parametrize(
    ("args", "operation", "expected_call"),
    [
        (
            ["accounts", "containers", "update", "--path", "accounts/1/containers/2"],
            mutations.update_container,
            ("accounts/1/containers/2", {"name": "private"}, "abc"),
        ),
        (
            [
                "accounts",
                "containers",
                "workspaces",
                "update",
                "--path",
                "accounts/1/containers/2/workspaces/3",
            ],
            mutations.update_workspace,
            ("accounts/1/containers/2/workspaces/3", {"name": "private"}, "abc"),
        ),
    ],
)
def test_core_update_apply_maps_path_body_and_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    args: list[str],
    operation: Any,
    expected_call: tuple[str, dict[str, Any], str],
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []
    monkeypatch.setattr(
        mutations,
        operation.__name__,
        lambda path, body, fingerprint: (
            calls.__iadd__([(path, body, fingerprint)]),
            {"name": "response"},
        )[1],
    )

    result = CliRunner().invoke(
        app, [*args, "--body", _body_file(tmp_path), "--fingerprint", "abc", "--apply"]
    )

    assert result.exit_code == 0
    assert calls == [expected_call]
