"""Compact registration contracts for generated GTM workspace commands."""

from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Any

import pytest
import urllib3.connectionpool
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations, reads

_WORKSPACE = "accounts/1/containers/2/workspaces/3"


@dataclass(frozen=True)
class ExpectedEntity:
    cli_name: str
    resource_name: str
    list_adapter: str
    get_adapter: str
    create_adapter: str


# This expected table is intentionally independent of workspace_discovery.py's
# registration tuple. It exercises the shared registration path without copying
# every generated leaf into a separate test.
_EXPECTED_ENTITIES = (
    ExpectedEntity("tags", "tags", "list_tags", "get_tag", "create_tag"),
    ExpectedEntity(
        "variables", "variables", "list_variables", "get_variable", "create_variable"
    ),
    ExpectedEntity(
        "triggers", "triggers", "list_triggers", "get_trigger", "create_trigger"
    ),
    ExpectedEntity("clients", "clients", "list_clients", "get_client", "create_client"),
    ExpectedEntity("folders", "folders", "list_folders", "get_folder", "create_folder"),
    ExpectedEntity("zones", "zones", "list_zones", "get_zone", "create_zone"),
    ExpectedEntity(
        "transformations",
        "transformations",
        "list_transformations",
        "get_transformation",
        "create_transformation",
    ),
    ExpectedEntity(
        "templates", "templates", "list_templates", "get_template", "create_template"
    ),
    ExpectedEntity(
        "gtag-config",
        "gtag_config",
        "list_gtag_configs",
        "get_gtag_config",
        "create_gtag_config",
    ),
)


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
        reads,
        "service_account_credentials",
        lambda _scopes: pytest.fail("ambient credential resolution is forbidden"),
    )
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _scopes: pytest.fail("ambient credential resolution is forbidden"),
    )


@pytest.mark.parametrize("expected", _EXPECTED_ENTITIES, ids=lambda row: row.cli_name)
def test_generated_workspace_discovery_commands_use_expected_names_and_adapters(
    monkeypatch: pytest.MonkeyPatch, expected: ExpectedEntity
) -> None:
    list_calls: list[tuple[str, str | None]] = []
    get_calls: list[str] = []

    def list_adapter(parent: str, *, page_token: str | None) -> dict[str, Any]:
        list_calls.append((parent, page_token))
        return {"resource": expected.resource_name}

    def get_adapter(path: str) -> dict[str, Any]:
        get_calls.append(path)
        return {"resource": expected.resource_name}

    monkeypatch.setattr(reads, expected.list_adapter, list_adapter)
    monkeypatch.setattr(reads, expected.get_adapter, get_adapter)

    listed = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            expected.cli_name,
            "list",
            "--parent",
            _WORKSPACE,
            "--page-token",
            "page-2",
        ],
    )
    path = f"{_WORKSPACE}/{expected.resource_name}/4"
    retrieved = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            expected.cli_name,
            "get",
            "--path",
            path,
        ],
    )

    assert listed.exit_code == 0
    assert retrieved.exit_code == 0
    assert list_calls == [(_WORKSPACE, "page-2")]
    assert get_calls == [path]
    assert json.loads(listed.output)["command"] == (
        f"gtmctl accounts containers workspaces {expected.cli_name} list"
    )
    assert json.loads(retrieved.output)["command"] == (
        f"gtmctl accounts containers workspaces {expected.cli_name} get"
    )


@pytest.mark.parametrize("expected", _EXPECTED_ENTITIES, ids=lambda row: row.cli_name)
def test_generated_workspace_create_commands_forward_arguments_and_cli_identity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any, expected: ExpectedEntity
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    body = {"name": expected.cli_name}
    body_path = tmp_path / f"{expected.cli_name}.json"
    body_path.write_text(json.dumps(body))
    monkeypatch.setattr(
        mutations,
        expected.create_adapter,
        lambda parent, request_body: (
            calls.append((parent, request_body)),
            {"resource": expected.resource_name},
        )[1],
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            expected.cli_name,
            "create",
            "--parent",
            _WORKSPACE,
            "--body",
            str(body_path),
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert calls == [(_WORKSPACE, body)]
    assert json.loads(result.output)["command"] == (
        f"gtmctl accounts containers workspaces {expected.cli_name} create"
    )
