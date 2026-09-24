"""Keep the GA4 Admin public command tree complete and discoverable."""

from __future__ import annotations

from typer import _click as click
from typer.main import get_command
from typer.testing import CliRunner

from ga4adminctl.cli import app


def _leaf_commands(
    command: click.Command, prefix: tuple[str, ...] = ()
) -> dict[str, click.Command]:
    """Return concrete public commands keyed by their full CLI path."""
    children = getattr(command, "commands", None)
    if children is None:
        return {"ga4adminctl " + " ".join(prefix): command}

    leaves: dict[str, click.Command] = {}
    for name, child in children.items():
        leaves.update(_leaf_commands(child, (*prefix, name)))
    return leaves


def test_ga4_admin_api_command_tree_is_complete_and_excludes_unsupported_paths() -> (
    None
):
    """Detect removed API leaves without maintaining a prose command catalog."""
    leaves = _leaf_commands(get_command(app))
    api_paths = set(leaves) - {"ga4adminctl sdk schema"}

    assert len(api_paths) == 50
    assert "ga4adminctl sdk schema" in leaves
    assert not api_paths.intersection(
        {
            "ga4adminctl audiences create",
            "ga4adminctl properties conversion-events create",
            "ga4adminctl properties conversion-events delete",
            "ga4adminctl properties conversion-events get",
            "ga4adminctl properties conversion-events list",
            "ga4adminctl properties conversion-events patch",
        }
    )


def test_ga4_admin_leaf_commands_have_descriptions_and_working_help() -> None:
    """Keep every registered API leaf discoverable through generated help."""
    runner = CliRunner()
    for path, command in _leaf_commands(get_command(app)).items():
        assert command.help and command.help.strip(), path
        result = runner.invoke(app, [*path.split()[1:], "--help"])
        assert result.exit_code == 0, f"{path}: {result.output}"
