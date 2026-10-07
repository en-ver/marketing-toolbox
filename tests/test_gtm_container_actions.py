"""Contracts for guarded GTM environment reauthorization."""

from __future__ import annotations

import json
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
        self.retries: list[int] = []
        self.callbacks: list[Callable[[Response], None]] = []

    def add_response_callback(self, callback: Callable[[Response], None]) -> None:
        self.callbacks.append(callback)

    def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
        self.retries.append(num_retries)
        for callback in self.callbacks:
            callback(Response({"status": "200"}))
        return self.response


class FakeResource:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeResource:
        return self

    def containers(self) -> FakeResource:
        return self

    def environments(self) -> FakeResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            result = FakeRequest({"operation": name})
            self.requests.append(result)
            return result

        return request


def test_reauthorize_environment_uses_one_official_request_with_publish_access_tier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeResource()
    accesses: list[str] = []
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda value: (accesses.append(value), object())[1],
    )

    assert mutations.reauthorize_environment(
        "accounts/1/containers/2/environments/3",
        {"name": "env"},
        service_factory=lambda _: service,
    ) == {"operation": "reauthorize"}
    assert service.calls == [
        (
            "reauthorize",
            {
                "path": "accounts/1/containers/2/environments/3",
                "body": {"name": "env"},
            },
        )
    ]
    assert [request.retries for request in service.requests] == [[0]]
    assert accesses == ["publish"]


def test_reauthorize_requires_operation_specific_acknowledgement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda _: pytest.fail("missing acknowledgement must not load credentials"),
    )
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "environments",
            "reauthorize",
            "--path",
            "accounts/1/containers/2/environments/3",
            "--body",
            "ignored.json",
            "--apply",
        ],
    )

    assert result.exit_code == 2
    assert "--acknowledge-environment-reauthorize" in result.output


def test_reauthorize_dry_run_is_bounded_and_never_loads_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    body = tmp_path / "environment.json"
    body.write_text('{"name":"private"}')
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda _: pytest.fail("dry run must not load credentials"),
    )
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "environments",
            "reauthorize",
            "--path",
            "accounts/1/containers/2/environments/3",
            "--body",
            str(body),
            "--acknowledge-environment-reauthorize",
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert json.loads(result.output)["data"]["operation"] == "environments.reauthorize"
