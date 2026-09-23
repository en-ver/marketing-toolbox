"""Keep the GTM v1 specification complete and internally consistent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, cast

from typer.main import get_command

from gtmctl.cli import app

SPEC_DIR = Path(__file__).parents[1] / "docs/specification/v1/gtmctl"


class ClickCommand(Protocol):
    """The Click command attributes exercised by this specification test."""

    params: list[Any]


class ClickGroup(ClickCommand, Protocol):
    """A Click command that exposes nested commands."""

    commands: dict[str, ClickCommand]


def test_gtm_v1_catalog_covers_the_official_discovery_snapshot() -> None:
    """Every upstream operation has exactly one catalog row with its status."""
    inventory = json.loads((SPEC_DIR / "upstream-inventory.json").read_text())
    methods = inventory["methods"]
    catalog = (SPEC_DIR / "catalog.md").read_text()
    rows = [
        line
        for line in catalog.splitlines()
        if line.startswith("| ") and line.split("|")[1].strip().isdigit()
    ]

    assert len(methods) == 106
    assert len(rows) == len(methods)
    assert (
        sum(method["publicContractStatus"] == "stable-target" for method in methods)
        == 104
    )
    assert {
        method["googleMethod"]
        for method in methods
        if method["publicContractStatus"] == "excluded"
    } == {
        "tagmanager.accounts.containers.destinations.get",
        "tagmanager.accounts.containers.destinations.link",
    }
    for method in methods:
        assert f"`{method['cliCommand']}`" in catalog
        assert f"`{method['googleMethod']}`" in catalog


def test_gtm_registered_leaf_commands_match_stable_catalog_targets() -> None:
    """The catalog cannot claim a stable target that the Typer app omits."""
    inventory = json.loads((SPEC_DIR / "upstream-inventory.json").read_text())

    def leaves(command: object, prefix: list[str] | None = None) -> set[str]:
        prefix = [] if prefix is None else prefix
        children = getattr(command, "commands", None)
        if children is None:
            return {"gtmctl " + " ".join(prefix)}
        return set().union(
            *(leaves(child, [*prefix, name]) for name, child in children.items())
        )

    registered = leaves(get_command(app))
    stable = {
        method["cliCommand"]
        for method in inventory["methods"]
        if method["publicContractStatus"] == "stable-target"
    }
    excluded = {
        method["cliCommand"]
        for method in inventory["methods"]
        if method["publicContractStatus"] == "excluded"
    }
    # ``sdk schema`` reads the bundled official Discovery artifact locally;
    # it is intentionally not represented as an upstream GTM API method.
    assert registered == stable | {"gtmctl sdk schema"}
    assert not registered & excluded


def test_gtm_cli_option_requiredness_matches_the_discovery_inventory() -> None:
    """Optional upstream query inputs, including fingerprints, stay optional."""
    inventory = json.loads((SPEC_DIR / "upstream-inventory.json").read_text())

    def command_for(path: str) -> ClickCommand:
        command = cast(ClickCommand, get_command(app))
        for part in path.split()[1:]:
            command = cast(ClickGroup, command).commands[part]
        return command

    for method in inventory["methods"]:
        if method["publicContractStatus"] != "stable-target":
            continue
        params = {
            param.name: param for param in command_for(method["cliCommand"]).params
        }
        for parameter in method["parameters"]:
            option_name = "".join(
                "_" + char.lower() if char.isupper() else char
                for char in parameter["name"]
            ).lstrip("_")
            option_name = {"type": "variable_type"}.get(option_name, option_name)
            if option_name in params:
                assert params[option_name].required is parameter["required"]
