"""Contracts for safe GTM gtag-config and built-in-variable mutations."""

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

    def gtag_config(self) -> FakeWorkspaceResource:
        return self

    def built_in_variables(self) -> FakeWorkspaceResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            result = FakeRequest({"resourceId": "4"})
            self.requests.append(result)
            return result

        return request


@pytest.mark.parametrize(
    ("operation", "args", "expected"),
    [
        (
            mutations.create_gtag_config,
            ("accounts/1/containers/2/workspaces/3", {"name": "Google tag"}),
            (
                "create",
                {
                    "parent": "accounts/1/containers/2/workspaces/3",
                    "body": {"name": "Google tag"},
                },
            ),
        ),
        (
            mutations.update_gtag_config,
            (
                "accounts/1/containers/2/workspaces/3/gtag_config/4",
                {"name": "Google tag"},
                "abc",
            ),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/workspaces/3/gtag_config/4",
                    "body": {"name": "Google tag"},
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.delete_gtag_config,
            ("accounts/1/containers/2/workspaces/3/gtag_config/4",),
            ("delete", {"path": "accounts/1/containers/2/workspaces/3/gtag_config/4"}),
        ),
        (
            mutations.create_built_in_variable,
            ("accounts/1/containers/2/workspaces/3", ["pageUrl", "clickId"]),
            (
                "create",
                {
                    "parent": "accounts/1/containers/2/workspaces/3",
                    "type": ["pageUrl", "clickId"],
                },
            ),
        ),
        (
            mutations.delete_built_in_variable,
            (
                "accounts/1/containers/2/workspaces/3/built_in_variables",
                ["pageUrl", "clickId"],
            ),
            (
                "delete",
                {
                    "path": "accounts/1/containers/2/workspaces/3/built_in_variables",
                    "type": ["pageUrl", "clickId"],
                },
            ),
        ),
        (
            mutations.revert_built_in_variable,
            ("accounts/1/containers/2/workspaces/3", "pageUrl"),
            (
                "revert",
                {"path": "accounts/1/containers/2/workspaces/3", "type": "pageUrl"},
            ),
        ),
    ],
)
def test_new_entity_mutations_make_one_official_edit_request(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
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

    assert operation(*args, service_factory=lambda _: service) == {"resourceId": "4"}
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    assert scopes == [[mutations.TAG_MANAGER_EDIT_SCOPE]]


def test_gtag_config_exposes_only_its_catalogued_mutations() -> None:
    result = CliRunner().invoke(
        app, ["accounts", "containers", "workspaces", "gtag-config", "--help"]
    )

    assert result.exit_code == 0
    assert all(command in result.output for command in ("create", "update", "delete"))
    assert "revert" not in result.output
