"""GTM read command tree and offline validation contracts."""

from __future__ import annotations

import json
import socket
from typing import Any

import pytest
import urllib3.connectionpool
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import reads


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


def test_nested_read_command_help() -> None:
    result = CliRunner().invoke(app, ["accounts", "containers", "workspaces", "--help"])

    assert result.exit_code == 0
    assert "list" in result.output
    assert "get" in result.output


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["accounts", "get", "--path", "accounts/1/containers/2"], "canonical GTM"),
        (
            ["accounts", "containers", "list", "--parent", "accounts/1/containers/2"],
            "canonical GTM",
        ),
        (
            ["accounts", "list", "--page-token", " token "],
            "leading or trailing whitespace",
        ),
        (["accounts", "containers", "lookup"], "Specify exactly one"),
        (
            [
                "accounts",
                "containers",
                "lookup",
                "--destination-id",
                "destination-1",
                "--tag-id",
                "G-1",
            ],
            "Specify exactly one",
        ),
    ],
)
def test_invalid_read_inputs_do_not_load_credentials(
    monkeypatch: pytest.MonkeyPatch, args: list[str], message: str
) -> None:
    monkeypatch.setattr(
        reads,
        "service_account_credentials",
        lambda _: pytest.fail("credentials must not load during local validation"),
    )

    result = CliRunner().invoke(app, args)

    assert result.exit_code == 2
    assert message in result.output


def test_read_command_writes_direct_response_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(reads, "get_account", lambda _: {"path": "accounts/1"})

    result = CliRunner().invoke(app, ["accounts", "get", "--path", "accounts/1"])

    assert result.exit_code == 0
    assert '"command": "gtmctl accounts get"' in result.output
    assert '"path": "accounts/1"' in result.output


def test_container_lookup_requires_one_selector_and_forwards_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, str | None]] = []
    monkeypatch.setattr(
        reads,
        "lookup_container",
        lambda *, destination_id, tag_id: (
            calls.append({"destination_id": destination_id, "tag_id": tag_id}),
            {"path": "accounts/1/containers/2"},
        )[1],
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "lookup",
            "--destination-id",
            "destination-1",
        ],
    )

    assert result.exit_code == 0
    assert calls == [{"destination_id": "destination-1", "tag_id": None}]
    assert json.loads(result.output)["command"] == "gtmctl accounts containers lookup"


def test_container_lookup_help_describes_mutually_exclusive_selectors() -> None:
    result = CliRunner().invoke(app, ["accounts", "containers", "lookup", "--help"])

    assert result.exit_code == 0
    assert result.output.count("mutually exclusive") == 2


def test_workspace_discovery_command_writes_response_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        reads, "list_tags", lambda _, *, page_token: {"tag": [{"tagId": "4"}]}
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "list",
            "--parent",
            "accounts/1/containers/2/workspaces/3",
        ],
    )

    assert result.exit_code == 0
    assert (
        '"command": "gtmctl accounts containers workspaces tags list"' in result.output
    )
    assert '"tagId": "4"' in result.output
