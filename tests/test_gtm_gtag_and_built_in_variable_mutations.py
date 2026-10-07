"""Contracts for safe GTM gtag-config and built-in-variable mutations."""

from __future__ import annotations

import json
import socket
from collections.abc import Callable
from typing import Any

import pytest
import urllib3.connectionpool
from httplib2 import Response
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.foundation.validation import RequestValidationError
from gtmctl.operations import mutations, transport
from marketing_common.discovery import discovery_method_parameters


@pytest.fixture(autouse=True)
def _block_external_transport_and_ambient_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BlockedSocket(socket.socket):
        def connect(self, address: Any) -> None:
            del address
            pytest.fail("external sockets are forbidden")

        def connect_ex(self, address: Any) -> int:
            del address
            pytest.fail("external sockets are forbidden")

    def blocked_urlopen(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("urllib3 dispatch is forbidden")

    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: pytest.fail("external sockets are forbidden"),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: pytest.fail("external DNS is forbidden"),
    )
    monkeypatch.setattr(socket, "socket", BlockedSocket)
    monkeypatch.setattr(
        urllib3.connectionpool.HTTPConnectionPool, "urlopen", blocked_urlopen
    )
    monkeypatch.setattr(
        urllib3.connectionpool.HTTPSConnectionPool, "urlopen", blocked_urlopen
    )
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda _access: pytest.fail("ambient credential resolution is forbidden"),
    )


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
    accesses: list[str] = []
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda value: (accesses.append(value), object())[1],
    )

    assert operation(*args, service_factory=lambda _: service) == {"resourceId": "4"}
    assert service.calls == [expected]
    assert [request.retries for request in service.requests] == [[0]]
    assert accesses == ["containers"]


def test_gtag_config_exposes_only_its_catalogued_mutations() -> None:
    result = CliRunner().invoke(
        app, ["accounts", "containers", "workspaces", "gtag-config", "--help"]
    )

    assert result.exit_code == 0
    assert all(command in result.output for command in ("create", "update", "delete"))
    assert "revert" not in result.output


@pytest.mark.parametrize(
    ("action", "adapter_name", "arguments", "expected_forwarding"),
    [
        (
            "create",
            "create_gtag_config",
            ["--parent", "accounts/1/containers/2/workspaces/3", "--body"],
            ("accounts/1/containers/2/workspaces/3", {"name": "Google tag"}),
        ),
        (
            "update",
            "update_gtag_config",
            [
                "--path",
                "accounts/1/containers/2/workspaces/3/gtag_config/4",
                "--body",
            ],
            (
                "accounts/1/containers/2/workspaces/3/gtag_config/4",
                {"name": "Google tag"},
                None,
            ),
        ),
        (
            "delete",
            "delete_gtag_config",
            ["--path", "accounts/1/containers/2/workspaces/3/gtag_config/4"],
            ("accounts/1/containers/2/workspaces/3/gtag_config/4",),
        ),
    ],
)
def test_gtag_config_generated_commands_use_canonical_envelopes_for_all_modes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
    action: str,
    adapter_name: str,
    arguments: list[str],
    expected_forwarding: tuple[Any, ...],
) -> None:
    body_path = tmp_path / "gtag.json"
    body_path.write_text('{"name":"Google tag"}')
    command = [
        "accounts",
        "containers",
        "workspaces",
        "gtag-config",
        action,
        *arguments,
    ]
    if "--body" in command:
        command[command.index("--body") + 1 : command.index("--body") + 1] = [
            str(body_path)
        ]
    if action == "delete":
        command.append("--acknowledge-gtag-config-delete")

    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        mutations,
        adapter_name,
        lambda *args: (calls.append(args), {"resourceId": "4"})[1],
    )
    applied = CliRunner().invoke(app, [*command, "--apply"])
    dry_run = CliRunner().invoke(app, [*command, "--dry-run"])

    assert applied.exit_code == 0
    assert json.loads(applied.output)["command"] == (
        f"gtmctl accounts containers workspaces gtag-config {action}"
    )
    assert calls == [expected_forwarding]
    assert dry_run.exit_code == 0
    dry_run_envelope = json.loads(dry_run.output)
    assert dry_run_envelope["command"] == (
        f"gtmctl accounts containers workspaces gtag-config {action}"
    )
    assert dry_run_envelope["data"]["operation"] == f"gtag_config.{action}"

    monkeypatch.setattr(
        mutations,
        adapter_name,
        lambda *_args: (_ for _ in ()).throw(RequestValidationError("synthetic")),
    )
    rejected = CliRunner().invoke(app, [*command, "--apply"])

    assert rejected.exit_code == 2
    assert json.loads(rejected.output)["command"] == (
        f"gtmctl accounts containers workspaces gtag-config {action}"
    )


@pytest.mark.parametrize(
    ("action", "method_id", "path_option", "target", "acknowledgement"),
    [
        (
            "create",
            "tagmanager.accounts.containers.workspaces.built_in_variables.create",
            "--parent",
            "accounts/1/containers/2/workspaces/3",
            None,
        ),
        (
            "delete",
            "tagmanager.accounts.containers.workspaces.built_in_variables.delete",
            "--path",
            "accounts/1/containers/2/workspaces/3/built_in_variables",
            "--acknowledge-built-in-variable-delete",
        ),
        (
            "revert",
            "tagmanager.accounts.containers.workspaces.built_in_variables.revert",
            "--path",
            "accounts/1/containers/2/workspaces/3",
            None,
        ),
    ],
)
def test_built_in_variable_type_enums_are_visible_and_invalid_values_fail_pre_auth(
    action: str,
    method_id: str,
    path_option: str,
    target: str,
    acknowledgement: str | None,
) -> None:
    prefix = [
        "accounts",
        "containers",
        "workspaces",
        "built-in-variables",
        action,
    ]
    help_result = CliRunner().invoke(app, [*prefix, "--help"])
    expected_types = discovery_method_parameters(
        api="tagmanager", api_version="v2", method_id=method_id
    )["type"]["enum"]

    assert help_result.exit_code == 0
    normalized_help = "".join(help_result.output.split())
    assert "Validvalues:" in normalized_help
    assert all(variable_type in normalized_help for variable_type in expected_types)

    for mode in ("--dry-run", "--apply"):
        arguments = [*prefix, path_option, target, "--type", "not-an-official-type"]
        if acknowledgement is not None:
            arguments.append(acknowledgement)
        result = CliRunner().invoke(app, [*arguments, mode])

        assert result.exit_code == 2
        envelope = json.loads(result.output)
        assert envelope["category"] == "invalid_request"
        assert "not-an-official-type" not in envelope["message"]


def test_built_in_variable_revert_keeps_its_type_optional() -> None:
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "built-in-variables",
            "revert",
            "--path",
            "accounts/1/containers/2/workspaces/3",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.output)["data"]["type"] is None
