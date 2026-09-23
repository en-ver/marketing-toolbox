"""Focused contracts for ordinary GTM container version mutations."""

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


class FakeVersionResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeVersionResource:
        return self

    def containers(self) -> FakeVersionResource:
        return self

    def versions(self) -> FakeVersionResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            fake_request = FakeRequest(self.response)
            self.requests.append(fake_request)
            return fake_request

        return request


@pytest.fixture
def fake_service(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FakeVersionResource, list[list[str]]]:
    service = FakeVersionResource({"containerVersionId": "4"})
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
    ("operation", "args", "expected", "scope"),
    [
        (
            mutations.update_version,
            ("accounts/1/containers/2/versions/4", {"name": "version"}, "abc"),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/versions/4",
                    "body": {"name": "version"},
                    "fingerprint": "abc",
                },
            ),
            mutations.TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        ),
        (
            mutations.delete_version,
            ("accounts/1/containers/2/versions/4",),
            ("delete", {"path": "accounts/1/containers/2/versions/4"}),
            mutations.TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        ),
        (
            mutations.set_latest_version,
            ("accounts/1/containers/2/versions/4",),
            ("set_latest", {"path": "accounts/1/containers/2/versions/4"}),
            mutations.TAG_MANAGER_EDIT_SCOPE,
        ),
        (
            mutations.undelete_version,
            ("accounts/1/containers/2/versions/4",),
            ("undelete", {"path": "accounts/1/containers/2/versions/4"}),
            mutations.TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        ),
    ],
)
def test_version_mutations_use_one_official_request_and_correct_scope(
    fake_service: tuple[FakeVersionResource, list[list[str]]],
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
    scope: str,
) -> None:
    service, scopes = fake_service

    assert operation(*args, service_factory=lambda _: service) == service.response
    assert service.calls == [expected]
    assert [request.calls for request in service.requests] == [[0]]
    assert scopes == [[scope]]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "version.json"
    path.write_text('{"name":"private"}')
    return str(path)


def test_version_update_apply_maps_path_body_and_fingerprint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []
    monkeypatch.setattr(
        mutations,
        "update_version",
        lambda path, body, fingerprint: (
            calls.__iadd__([(path, body, fingerprint)]),
            {"containerVersionId": "4"},
        )[1],
    )
    path = "accounts/1/containers/2/versions/4"

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "versions",
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
