"""Focused contracts for guarded GTM container-version publishing."""

from __future__ import annotations

import json
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

    def publish(self, **kwargs: Any) -> FakeRequest:
        self.calls.append(("publish", kwargs))
        request = FakeRequest(self.response)
        self.requests.append(request)
        return request


def test_publish_maps_official_parameters_scope_and_no_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeVersionResource({"containerVersion": {"containerVersionId": "4"}})
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )

    response = mutations.publish_version(
        "accounts/1/containers/2/versions/4",
        "abc",
        service_factory=lambda _: service,
    )

    assert response == service.response
    assert service.calls == [
        (
            "publish",
            {
                "path": "accounts/1/containers/2/versions/4",
                "fingerprint": "abc",
            },
        )
    ]
    assert [request.retries for request in service.requests] == [[0]]
    assert scopes == [[mutations.TAG_MANAGER_PUBLISH_SCOPE]]


def test_publish_dry_run_is_deterministic_and_never_loads_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry run must not load credentials"),
    )
    args = [
        "accounts",
        "containers",
        "versions",
        "publish",
        "--path",
        "accounts/1/containers/2/versions/4",
        "--fingerprint",
        "abc",
        "--acknowledge-publish",
        "--dry-run",
    ]

    first = CliRunner().invoke(app, args)
    second = CliRunner().invoke(app, args)

    assert first.exit_code == second.exit_code == 0
    assert first.output == second.output
    assert json.loads(first.output)["data"] == {
        "applied": False,
        "mode": "dry-run",
        "operation": "versions.publish",
        "target": "accounts/1/containers/2/versions/4",
        "fingerprint": "abc",
        "versionPublished": False,
    }


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (
            [
                "--fingerprint",
                "abc",
                "--acknowledge-publish",
                "--apply",
            ],
            "Missing option '--path'",
        ),
        (
            [
                "--path",
                "accounts/1/containers/2/versions/4",
                "--fingerprint",
                " ",
                "--acknowledge-publish",
                "--apply",
            ],
            "--fingerprint must be a non-empty",
        ),
        (
            [
                "--path",
                "accounts/1/containers/2/versions/4",
                "--fingerprint",
                "abc",
                "--acknowledge-publish",
            ],
            "exactly one",
        ),
        (
            [
                "--path",
                "accounts/1/containers/2/versions/4",
                "--fingerprint",
                "abc",
                "--acknowledge-publish",
                "--dry-run",
                "--apply",
            ],
            "exactly one",
        ),
        (
            [
                "--path",
                "accounts/1/containers/2/versions/4",
                "--fingerprint",
                "abc",
                "--apply",
            ],
            "--acknowledge-publish",
        ),
    ],
)
def test_publish_requires_all_guardrails(args: list[str], expected: str) -> None:
    result = CliRunner().invoke(
        app, ["accounts", "containers", "versions", "publish", *args]
    )

    assert result.exit_code == 2
    assert expected in result.output


def test_publish_validates_canonical_path_before_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("credentials must not load before route validation"),
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "versions",
            "publish",
            "--path",
            "accounts/1/containers/2/workspaces/3/versions/4",
            "--fingerprint",
            "abc",
            "--acknowledge-publish",
            "--apply",
        ],
    )

    assert result.exit_code == 2
    assert "canonical GTM" in result.output


def test_publish_apply_preserves_the_standard_response_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        mutations,
        "publish_version",
        lambda path, fingerprint: (
            calls.__iadd__([(path, fingerprint)]),
            {"compilerError": False, "containerVersion": {"containerVersionId": "4"}},
        )[1],
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "versions",
            "publish",
            "--path",
            "accounts/1/containers/2/versions/4",
            "--fingerprint",
            "abc",
            "--acknowledge-publish",
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert calls == [("accounts/1/containers/2/versions/4", "abc")]
    assert json.loads(result.output)["data"] == {
        "compilerError": False,
        "containerVersion": {"containerVersionId": "4"},
    }
