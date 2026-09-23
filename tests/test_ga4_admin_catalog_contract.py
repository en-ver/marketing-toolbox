"""Keep the GA4 Admin catalog option names aligned with Typer help."""

from __future__ import annotations

import re
from pathlib import Path

from typer import _click as click
from typer.main import get_command
from typer.testing import CliRunner

from ga4adminctl.cli import app

CATALOG_PATH = (
    Path(__file__).parents[1] / "docs/specification/v1/ga4adminctl/catalog.md"
)
ROW_PATTERN = re.compile(r"\| (\d+) \|")
OPTION_PATTERN = re.compile(r"--[a-z][a-z-]*")
UNESCAPED_PIPE_PATTERN = re.compile(r"(?<!\\)\|")
COMMAND_PATTERN = re.compile(r"`(ga4adminctl [^`]+)`")


def _catalog_commands() -> set[str]:
    return {
        match.group(1)
        for line in CATALOG_PATH.read_text(encoding="utf-8").splitlines()
        if ROW_PATTERN.match(line)
        if (match := COMMAND_PATTERN.search(line)) is not None
    }


def _leaf_command_paths(
    command: click.Command, prefix: tuple[str, ...] = ()
) -> set[str]:
    """Return actual leaf paths from Typer's generated public Click command tree."""
    commands = getattr(command, "commands", None)
    if commands is None:
        return {"ga4adminctl " + " ".join(prefix)}

    leaves: set[str] = set()
    for name, child in commands.items():
        leaves.update(_leaf_command_paths(child, (*prefix, name)))
    return leaves


def test_ga4_admin_catalog_option_names_match_typer_help() -> None:
    """Every catalog row documents exactly the options exposed by its command."""
    rows = [
        line
        for line in CATALOG_PATH.read_text(encoding="utf-8").splitlines()
        if ROW_PATTERN.match(line)
    ]

    assert len(rows) == 50

    runner = CliRunner()
    discrepancies: list[str] = []
    for line in rows:
        columns = UNESCAPED_PIPE_PATTERN.split(line)
        row = ROW_PATTERN.match(line)
        assert row is not None
        command = COMMAND_PATTERN.search(columns[2])
        assert command is not None

        result = runner.invoke(app, [*command.group(1).split()[1:], "--help"])
        assert result.exit_code == 0, result.output

        documented_options = set(OPTION_PATTERN.findall(f"{columns[6]} {columns[9]}"))
        help_options = set(OPTION_PATTERN.findall(result.output)) - {"--help"}
        if documented_options != help_options:
            discrepancies.append(
                f"row {row.group(1)} ({command.group(1)}): "
                f"catalog={sorted(documented_options)}, help={sorted(help_options)}"
            )

    assert not discrepancies, "\n".join(discrepancies)


def test_public_typer_leaf_commands_exactly_match_the_stable_catalog() -> None:
    """Prevent alpha/deprecated paths or catalog omissions from becoming public."""
    actual = _leaf_command_paths(get_command(app))
    expected = _catalog_commands()

    # ``sdk schema`` is a local-only descriptor tool, not an Admin API target,
    # so it intentionally remains outside the official-operation catalog.
    assert actual == expected | {"ga4adminctl sdk schema"}

    excluded = {
        "ga4adminctl audiences create",
        "ga4adminctl properties conversion-events create",
        "ga4adminctl properties conversion-events delete",
        "ga4adminctl properties conversion-events get",
        "ga4adminctl properties conversion-events list",
        "ga4adminctl properties conversion-events patch",
    }
    assert not actual.intersection(excluded)


def _leaf_commands(command: click.Command) -> list[click.Command]:
    """Return all concrete public commands in one generated Click tree."""
    children = getattr(command, "commands", None)
    if children is None:
        return [command]
    return [leaf for child in children.values() for leaf in _leaf_commands(child)]


def test_public_typer_leaf_commands_have_help_descriptions() -> None:
    """Keep generated command families discoverable through ``--help``."""
    undocumented = [
        command.name
        for command in _leaf_commands(get_command(app))
        if not command.help or not command.help.strip()
    ]

    assert not undocumented, f"Leaf commands without help: {undocumented}"
