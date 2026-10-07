"""Focused contracts for ordinary GTM folder mutations."""

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


class FakeFolderResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def accounts(self) -> FakeFolderResource:
        return self

    def containers(self) -> FakeFolderResource:
        return self

    def workspaces(self) -> FakeFolderResource:
        return self

    def folders(self) -> FakeFolderResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            return FakeRequest(self.response)

        return request


@pytest.fixture
def fake_service(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FakeFolderResource, list[str]]:
    service = FakeFolderResource({"folderId": "4"})
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
            mutations.create_folder,
            ("accounts/1/containers/2/workspaces/3", {"name": "folder"}),
            (
                "create",
                {
                    "parent": "accounts/1/containers/2/workspaces/3",
                    "body": {"name": "folder"},
                },
            ),
        ),
        (
            mutations.update_folder,
            (
                "accounts/1/containers/2/workspaces/3/folders/4",
                {"name": "folder"},
                "abc",
            ),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/workspaces/3/folders/4",
                    "body": {"name": "folder"},
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.revert_folder,
            ("accounts/1/containers/2/workspaces/3/folders/4", "abc"),
            (
                "revert",
                {
                    "path": "accounts/1/containers/2/workspaces/3/folders/4",
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.delete_folder,
            ("accounts/1/containers/2/workspaces/3/folders/4",),
            ("delete", {"path": "accounts/1/containers/2/workspaces/3/folders/4"}),
        ),
        (
            mutations.move_folder_entities_to_folder,
            ("accounts/1/containers/2/workspaces/3/folders/4",),
            (
                "move_entities_to_folder",
                {"path": "accounts/1/containers/2/workspaces/3/folders/4"},
            ),
        ),
    ],
)
def test_folder_mutations_use_one_official_edit_request(
    fake_service: tuple[FakeFolderResource, list[str]],
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service, accesses = fake_service

    assert operation(*args, service_factory=lambda _: service) == service.response
    assert service.calls == [expected]
    assert accesses == ["containers"]


def test_folder_move_forwards_a_supplied_optional_body(
    fake_service: tuple[FakeFolderResource, list[str]],
) -> None:
    service, _accesses = fake_service

    mutations.move_folder_entities_to_folder(
        "accounts/1/containers/2/workspaces/3/folders/4",
        body={"folderId": "4"},
        variable_ids=["1"],
        service_factory=lambda _: service,
    )

    assert service.calls == [
        (
            "move_entities_to_folder",
            {
                "path": "accounts/1/containers/2/workspaces/3/folders/4",
                "body": {"folderId": "4"},
                "variableId": ["1"],
            },
        )
    ]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "folder.json"
    path.write_text('{"name":"private"}')
    return str(path)


def test_folder_update_apply_maps_folder_path_body_and_fingerprint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []
    monkeypatch.setattr(
        mutations,
        "update_folder",
        lambda path, body, fingerprint: (
            calls.__iadd__([(path, body, fingerprint)]),
            {"folderId": "4"},
        )[1],
    )
    path = "accounts/1/containers/2/workspaces/3/folders/4"

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "folders",
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
