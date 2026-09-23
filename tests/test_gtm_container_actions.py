"""Contracts for guarded GTM environment and container actions."""

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


@pytest.mark.parametrize(
    ("operation", "args", "expected", "scope"),
    [
        (
            mutations.reauthorize_environment,
            ("accounts/1/containers/2/environments/3", {"name": "env"}),
            (
                "reauthorize",
                {
                    "path": "accounts/1/containers/2/environments/3",
                    "body": {"name": "env"},
                },
            ),
            mutations.TAG_MANAGER_PUBLISH_SCOPE,
        ),
        (
            mutations.combine_container,
            ("accounts/1/containers/2",),
            (
                "combine",
                {
                    "path": "accounts/1/containers/2",
                    "containerId": "9",
                    "allowUserPermissionFeatureUpdate": False,
                    "settingSource": "other",
                },
            ),
            mutations.TAG_MANAGER_EDIT_SCOPE,
        ),
        (
            mutations.move_container_tag_id,
            ("accounts/1/containers/2",),
            (
                "move_tag_id",
                {
                    "path": "accounts/1/containers/2",
                    "copySettings": True,
                    "allowUserPermissionFeatureUpdate": False,
                    "tagId": "G-ABC",
                    "tagName": "tag",
                    "copyUsers": False,
                    "copyTermsOfService": False,
                },
            ),
            mutations.TAG_MANAGER_EDIT_SCOPE,
        ),
    ],
)
def test_actions_use_one_official_request_with_catalogued_scope(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
    scope: str,
) -> None:
    service = FakeResource()
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )
    kwargs: dict[str, Any] = {}
    if operation is mutations.combine_container:
        kwargs = {
            "container_id": "9",
            "allow_user_permission_feature_update": False,
            "setting_source": "other",
        }
    if operation is mutations.move_container_tag_id:
        kwargs = {
            "copy_settings": True,
            "allow_user_permission_feature_update": False,
            "tag_id": "G-ABC",
            "tag_name": "tag",
            "copy_users": False,
            "copy_terms_of_service": False,
        }

    assert operation(*args, **kwargs, service_factory=lambda _: service) == {
        "operation": expected[0]
    }
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    assert scopes == [[scope]]


@pytest.mark.parametrize(
    ("args", "acknowledgement"),
    [
        (
            [
                "accounts",
                "containers",
                "combine",
                "--path",
                "accounts/1/containers/2",
                "--apply",
            ],
            "--acknowledge-container-combine",
        ),
        (
            [
                "accounts",
                "containers",
                "move-tag-id",
                "--path",
                "accounts/1/containers/2",
                "--apply",
            ],
            "--acknowledge-container-move-tag-id",
        ),
        (
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
            "--acknowledge-environment-reauthorize",
        ),
    ],
)
def test_high_impact_actions_require_operation_specific_acknowledgement(
    args: list[str], acknowledgement: str
) -> None:
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 2
    assert acknowledgement in result.output


def test_reauthorize_dry_run_is_bounded_and_never_loads_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    body = tmp_path / "environment.json"
    body.write_text('{"name":"private"}')
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
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
