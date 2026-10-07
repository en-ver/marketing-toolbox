"""Contracts for ordinary GTM workspace entity mutation families."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from httplib2 import Response

from gtmctl.operations import mutations, transport


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.retries: list[int] = []
        self.callbacks: list[Callable[[Response], None]] = []

    def add_response_callback(self, callback: Callable[[Response], None]) -> None:
        self.callbacks.append(callback)

    def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
        self.retries.append(num_retries)
        for callback in self.callbacks:
            callback(Response({"status": "200"}))
        return self.response


class FakeWorkspaceResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeWorkspaceResource:
        return self

    def containers(self) -> FakeWorkspaceResource:
        return self

    def workspaces(self) -> FakeWorkspaceResource:
        return self

    def __getattr__(self, name: str) -> Any:
        if name in {"clients", "zones", "transformations", "templates"}:
            return lambda: self

        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            result = FakeRequest(self.response)
            self.requests.append(result)
            return result

        return request


@pytest.mark.parametrize("entity", ["templates"])
@pytest.mark.parametrize("action", ["create", "update", "revert", "delete"])
def test_entity_mutations_map_to_one_official_edit_request(
    monkeypatch: pytest.MonkeyPatch, entity: str, action: str
) -> None:
    service = FakeWorkspaceResource({"resourceId": "4"})
    accesses: list[str] = []
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda value: (accesses.append(value), object())[1],
    )
    singular = entity[:-1] if entity != "transformations" else "transformation"
    parent = "accounts/1/containers/2/workspaces/3"
    path = f"{parent}/{entity}/4"
    operation = getattr(mutations, f"{action}_{singular}")
    if action == "create":
        args: tuple[Any, ...] = (parent, {"name": entity})
        expected = ("create", {"parent": parent, "body": {"name": entity}})
    elif action == "update":
        args = (path, {"name": entity}, "abc")
        expected = (
            "update",
            {"path": path, "body": {"name": entity}, "fingerprint": "abc"},
        )
    elif action == "revert":
        args = (path, "abc")
        expected = ("revert", {"path": path, "fingerprint": "abc"})
    else:
        args = (path,)
        expected = ("delete", {"path": path})

    assert operation(*args, service_factory=lambda _: service) == {"resourceId": "4"}
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    assert accesses == ["containers"]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "resource.json"
    path.write_text('{"name":"private"}')
    return str(path)
