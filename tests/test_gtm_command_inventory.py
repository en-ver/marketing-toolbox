"""Keep the GTM command tree aligned with its upstream Discovery inventory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol, cast

from typer.main import get_command

from gtmctl.cli import app

INVENTORY_PATH = Path(__file__).parent / "data/gtmctl/upstream-inventory.json"

# This is a CLI-owned rename, not a fallback: the Discovery parameter ``type``
# conflicts with Python's built-in name and is exposed as ``variable_type``.
PARAMETER_OPTION_ALIASES = {"type": "variable_type"}


class ClickCommand(Protocol):
    """The Click command attributes exercised by this inventory test."""

    params: list[Any]


class ClickGroup(ClickCommand, Protocol):
    """A Click command that exposes nested commands."""

    commands: dict[str, ClickCommand]


def _inventory() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(INVENTORY_PATH.read_text(encoding="utf-8")))


def _leaves(command: object, prefix: tuple[str, ...] = ()) -> set[str]:
    children = getattr(command, "commands", None)
    if children is None:
        return {"gtmctl " + " ".join(prefix)}
    return set().union(
        *(_leaves(child, (*prefix, name)) for name, child in children.items())
    )


def _command_for(path: str) -> ClickCommand:
    command = cast(ClickCommand, get_command(app))
    for part in path.split()[1:]:
        command = cast(ClickGroup, command).commands[part]
    return command


def _option_name(parameter_name: str) -> str:
    snake_case = "".join(
        "_" + character.lower() if character.isupper() else character
        for character in parameter_name
    ).lstrip("_")
    return PARAMETER_OPTION_ALIASES.get(snake_case, snake_case)


def test_gtm_inventory_covers_the_pinned_discovery_snapshot() -> None:
    """The inventory is a complete, unique snapshot of the upstream surface."""
    methods = _inventory()["methods"]

    assert len(methods) == 106
    assert len({method["googleMethod"] for method in methods}) == len(methods)
    assert len({method["cliCommand"] for method in methods}) == len(methods)
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


def test_gtm_registered_leaf_commands_match_stable_inventory_targets() -> None:
    """The command tree implements every stable inventory entry, and no excluded one."""
    methods = _inventory()["methods"]
    registered = _leaves(get_command(app))
    stable = {
        method["cliCommand"]
        for method in methods
        if method["publicContractStatus"] == "stable-target"
    }
    excluded = {
        method["cliCommand"]
        for method in methods
        if method["publicContractStatus"] == "excluded"
    }

    assert registered == stable | {
        "gtmctl sdk schema",
        "gtmctl auth login",
        "gtmctl auth status",
        "gtmctl auth forget",
        "gtmctl auth revoke",
    }
    assert not registered & excluded


def test_gtm_cli_required_options_cover_required_inventory_parameters() -> None:
    """Every required Discovery parameter has a required runtime CLI option."""
    for method in _inventory()["methods"]:
        if method["publicContractStatus"] != "stable-target":
            continue

        params = {
            param.name: param for param in _command_for(method["cliCommand"]).params
        }
        for parameter in method["parameters"]:
            option_name = _option_name(parameter["name"])
            if parameter["required"]:
                assert option_name in params, (
                    f"{method['cliCommand']} omits required Discovery parameter "
                    f"{parameter['name']}"
                )
            if option_name in params:
                assert params[option_name].required is parameter["required"], (
                    f"{method['cliCommand']} option {option_name} requiredness differs "
                    f"from Discovery parameter {parameter['name']}"
                )
