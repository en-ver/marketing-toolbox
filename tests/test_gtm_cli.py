"""GTM read command tree and offline validation contracts."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import reads


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
        (["accounts", "containers", "lookup"], "Specify at least one"),
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
