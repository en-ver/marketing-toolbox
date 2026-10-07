"""Focused contracts for ordinary GTM variable and trigger mutations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from httplib2 import Response
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations, transport


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[int] = []
        self.callbacks: list[Callable[[Response], None]] = []

    def add_response_callback(self, callback: Callable[[Response], None]) -> None:
        self.callbacks.append(callback)

    def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
        self.calls.append(num_retries)
        for callback in self.callbacks:
            callback(Response({"status": "200"}))
        return self.response


class FakeWorkspaceResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def accounts(self) -> FakeWorkspaceResource:
        return self

    def containers(self) -> FakeWorkspaceResource:
        return self

    def workspaces(self) -> FakeWorkspaceResource:
        return self

    def variables(self) -> FakeWorkspaceResource:
        return self

    def triggers(self) -> FakeWorkspaceResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            return FakeRequest(self.response)

        return request


@pytest.fixture
def fake_service(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FakeWorkspaceResource, list[str]]:
    service = FakeWorkspaceResource({"resourceId": "4"})
    accesses: list[str] = []
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda value: (accesses.append(value), object())[1],
    )
    return service, accesses


@pytest.mark.parametrize(
    ("operation", "args", "expected"),
    [
        (
            mutations.create_variable,
            ("accounts/1/containers/2/workspaces/3", {"name": "variable"}),
            (
                "create",
                {
                    "parent": "accounts/1/containers/2/workspaces/3",
                    "body": {"name": "variable"},
                },
            ),
        ),
        (
            mutations.update_variable,
            (
                "accounts/1/containers/2/workspaces/3/variables/4",
                {"name": "variable"},
                "abc",
            ),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/workspaces/3/variables/4",
                    "body": {"name": "variable"},
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.revert_variable,
            ("accounts/1/containers/2/workspaces/3/variables/4", "abc"),
            (
                "revert",
                {
                    "path": "accounts/1/containers/2/workspaces/3/variables/4",
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.delete_variable,
            ("accounts/1/containers/2/workspaces/3/variables/4",),
            ("delete", {"path": "accounts/1/containers/2/workspaces/3/variables/4"}),
        ),
        (
            mutations.create_trigger,
            ("accounts/1/containers/2/workspaces/3", {"name": "trigger"}),
            (
                "create",
                {
                    "parent": "accounts/1/containers/2/workspaces/3",
                    "body": {"name": "trigger"},
                },
            ),
        ),
        (
            mutations.update_trigger,
            (
                "accounts/1/containers/2/workspaces/3/triggers/4",
                {"name": "trigger"},
                "abc",
            ),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/workspaces/3/triggers/4",
                    "body": {"name": "trigger"},
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.revert_trigger,
            ("accounts/1/containers/2/workspaces/3/triggers/4", "abc"),
            (
                "revert",
                {
                    "path": "accounts/1/containers/2/workspaces/3/triggers/4",
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.delete_trigger,
            ("accounts/1/containers/2/workspaces/3/triggers/4",),
            ("delete", {"path": "accounts/1/containers/2/workspaces/3/triggers/4"}),
        ),
    ],
)
def test_variable_and_trigger_mutations_use_one_official_edit_request(
    fake_service: tuple[FakeWorkspaceResource, list[str]],
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service, accesses = fake_service

    assert operation(*args, service_factory=lambda _: service) == service.response
    assert service.calls == [expected]
    assert accesses == ["containers"]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "resource.json"
    path.write_text('{"name":"private"}')
    return str(path)


@pytest.mark.parametrize("entity", ["triggers"])
def test_entity_update_apply_maps_cli_values_to_resource_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, entity: str
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []
    monkeypatch.setattr(
        mutations,
        f"update_{entity[:-1]}",
        lambda path, body, fingerprint: (
            calls.__iadd__([(path, body, fingerprint)]),
            {"resourceId": "4"},
        )[1],
    )
    path = f"accounts/1/containers/2/workspaces/3/{entity}/4"

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            entity,
            "update",
            "--path",
            path,
            "--body",
            _body_file(tmp_path),
            "--fingerprint",
            "abc",
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert calls == [(path, {"name": "private"}, "abc")]
