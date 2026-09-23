"""Contracts for guarded GTM workspace action endpoints."""

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


class FakeWorkspaceResource:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeWorkspaceResource:
        return self

    def containers(self) -> FakeWorkspaceResource:
        return self

    def workspaces(self) -> FakeWorkspaceResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            result = FakeRequest({"operation": name})
            self.requests.append(result)
            return result

        return request


@pytest.mark.parametrize(
    ("operation", "args", "expected", "scope"),
    [
        (
            mutations.sync_workspace,
            ("accounts/1/containers/2/workspaces/3",),
            ("sync", {"path": "accounts/1/containers/2/workspaces/3"}),
            mutations.TAG_MANAGER_EDIT_SCOPE,
        ),
        (
            mutations.quick_preview_workspace,
            ("accounts/1/containers/2/workspaces/3",),
            ("quick_preview", {"path": "accounts/1/containers/2/workspaces/3"}),
            mutations.TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        ),
        (
            mutations.resolve_workspace_conflict,
            ("accounts/1/containers/2/workspaces/3", {"type": "tag"}, "abc"),
            (
                "resolve_conflict",
                {
                    "path": "accounts/1/containers/2/workspaces/3",
                    "body": {"type": "tag"},
                    "fingerprint": "abc",
                },
            ),
            mutations.TAG_MANAGER_EDIT_SCOPE,
        ),
        (
            mutations.bulk_update_workspace,
            ("accounts/1/containers/2/workspaces/3", {"changeStatus": "added"}),
            (
                "bulk_update",
                {
                    "path": "accounts/1/containers/2/workspaces/3",
                    "body": {"changeStatus": "added"},
                },
            ),
            mutations.TAG_MANAGER_EDIT_SCOPE,
        ),
        (
            mutations.create_workspace_version,
            ("accounts/1/containers/2/workspaces/3", {"name": "release"}),
            (
                "create_version",
                {
                    "path": "accounts/1/containers/2/workspaces/3",
                    "body": {"name": "release"},
                },
            ),
            mutations.TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        ),
    ],
)
def test_workspace_actions_use_one_official_request_and_catalogued_scope(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
    scope: str,
) -> None:
    service = FakeWorkspaceResource()
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )

    assert operation(*args, service_factory=lambda _: service) == {
        "operation": expected[0]
    }
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    assert scopes == [[scope]]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "action.json"
    path.write_text('{"name":"private"}')
    return str(path)


@pytest.mark.parametrize(
    ("action", "body", "acknowledgement"),
    [
        ("quick-preview", False, "--acknowledge-quick-preview"),
        ("bulk-update", True, "--acknowledge-workspace-bulk-update"),
        ("create-version", True, "--acknowledge-version-create"),
    ],
)
def test_high_impact_workspace_actions_require_specific_acknowledgement(
    tmp_path: Any, action: str, body: bool, acknowledgement: str
) -> None:
    args = [
        "accounts",
        "containers",
        "workspaces",
        action,
        "--path",
        "accounts/1/containers/2/workspaces/3",
    ]
    if body:
        args.extend(["--body", _body_file(tmp_path)])
    args.append("--apply")

    result = CliRunner().invoke(app, args)

    assert result.exit_code == 2
    assert acknowledgement in result.output
