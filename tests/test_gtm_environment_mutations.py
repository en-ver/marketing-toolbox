"""Focused contracts for ordinary GTM container environment mutations."""

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


class FakeEnvironmentResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeEnvironmentResource:
        return self

    def containers(self) -> FakeEnvironmentResource:
        return self

    def environments(self) -> FakeEnvironmentResource:
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
) -> tuple[FakeEnvironmentResource, list[list[str]]]:
    service = FakeEnvironmentResource({"environmentId": "4"})
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
            mutations.create_environment,
            ("accounts/1/containers/2", {"name": "environment"}),
            (
                "create",
                {"parent": "accounts/1/containers/2", "body": {"name": "environment"}},
            ),
        ),
        (
            mutations.update_environment,
            (
                "accounts/1/containers/2/environments/4",
                {"name": "environment"},
                "abc",
            ),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/environments/4",
                    "body": {"name": "environment"},
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.delete_environment,
            ("accounts/1/containers/2/environments/4",),
            ("delete", {"path": "accounts/1/containers/2/environments/4"}),
        ),
    ],
)
def test_environment_mutations_use_one_official_edit_request(
    fake_service: tuple[FakeEnvironmentResource, list[list[str]]],
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service, scopes = fake_service

    assert operation(*args, service_factory=lambda _: service) == service.response
    assert service.calls == [expected]
    assert [request.calls for request in service.requests] == [[0]]
    assert scopes == [[mutations.TAG_MANAGER_EDIT_SCOPE]]


def _body_file(tmp_path: Any) -> str:
    path = tmp_path / "environment.json"
    path.write_text('{"name":"private"}')
    return str(path)


def test_environment_update_apply_maps_path_body_and_fingerprint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []
    monkeypatch.setattr(
        mutations,
        "update_environment",
        lambda path, body, fingerprint: (
            calls.__iadd__([(path, body, fingerprint)]),
            {"environmentId": "4"},
        )[1],
    )
    path = "accounts/1/containers/2/environments/4"

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "environments",
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
