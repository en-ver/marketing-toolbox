"""Focused contracts for ordinary GTM folder mutations."""

from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[int] = []

    def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
        self.calls.append(num_retries)
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
) -> tuple[FakeFolderResource, list[list[str]]]:
    service = FakeFolderResource({"folderId": "4"})
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )
    return service, scopes


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
    fake_service: tuple[FakeFolderResource, list[list[str]]],
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service, scopes = fake_service

    assert operation(*args, service_factory=lambda _: service) == service.response
    assert service.calls == [expected]
    assert scopes == [[mutations.TAG_MANAGER_EDIT_SCOPE]]


def test_folder_move_forwards_a_supplied_optional_body(
    fake_service: tuple[FakeFolderResource, list[list[str]]],
) -> None:
    service, _scopes = fake_service

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
