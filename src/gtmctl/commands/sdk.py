"""Local official-Discovery request descriptor discovery for GTM CLI leaves."""

from __future__ import annotations

from typing import Annotated

import typer
from typer.main import get_command

from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.discovery import (
    DiscoverySchemaTarget,
    discovery_method_parameters,
    discovery_schema_response,
)


def _registered_body_options(root: typer.Typer) -> dict[tuple[str, ...], set[str]]:
    """Derive eligible body leaves and their actual Click option names."""
    leaves: dict[tuple[str, ...], set[str]] = {}

    def visit(command: object, path: tuple[str, ...]) -> None:
        children = getattr(command, "commands", None)
        if children:
            for name, child in children.items():
                visit(child, (*path, name))
            return
        params = getattr(command, "params", ())
        if any("--body" in getattr(parameter, "opts", ()) for parameter in params):
            leaves[path] = {
                name
                for parameter in params
                if (name := getattr(parameter, "name", None)) is not None
            }

    visit(get_command(root), ())
    return leaves


def _registered_body_paths(root: typer.Typer) -> set[tuple[str, ...]]:
    """Return the registered body paths retained for catalog contract tests."""
    return set(_registered_body_options(root))


def _method_id(path: tuple[str, ...]) -> str:
    return "tagmanager." + ".".join(part.replace("-", "_") for part in path)


_CLI_PARAMETER_ALIASES: dict[tuple[str, ...], tuple[str, ...]] = {
    # The Gallery import acknowledgement maps to the official query parameter
    # without exposing that raw parameter as a user-facing CLI option.
    ("accounts", "containers", "workspaces", "templates", "import-from-gallery"): (
        "acknowledgePermissions",
    ),
}


def _snake_case(name: str) -> str:
    return "".join(
        "_" + character.lower() if character.isupper() else character
        for character in name
    ).lstrip("_")


def _target_for_path(
    *, path: tuple[str, ...], option_names: set[str]
) -> DiscoverySchemaTarget:
    """Classify the CLI-owned official method parameters for one body leaf."""
    method_id = _method_id(path)
    parameters = discovery_method_parameters(
        api="tagmanager", api_version="v2", method_id=method_id
    )
    aliases = _CLI_PARAMETER_ALIASES.get(path, ())
    supplied = tuple(
        name
        for name in parameters
        if _snake_case(name) in option_names or name in aliases
    )
    return DiscoverySchemaTarget(
        cli_path=path,
        official_method=method_id,
        path_or_query_fields=supplied,
        body_forbidden_fields=supplied,
    )


def register_sdk_commands(root: typer.Typer) -> typer.Typer:
    """Attach ``gtmctl sdk schema`` after the complete registered tree exists."""
    app = typer.Typer(
        help="Inspect locally installed official GTM Discovery request descriptors.",
        no_args_is_help=True,
    )

    @app.command("schema")
    def schema(
        command: Annotated[
            str,
            typer.Option(
                "--command",
                help="Exact existing leaf path, excluding gtmctl; for example: accounts update.",
            ),
        ],
    ) -> None:
        """Return a bundled official Discovery descriptor without credentials or network."""
        path = tuple(part for part in command.split(" ") if part)
        body_options = _registered_body_options(root)
        if path not in body_options:
            exit_with_diagnostic(
                exit_code=2,
                category="invalid_arguments",
                message="--command must name an eligible registered gtmctl body leaf.",
                command="gtmctl sdk schema",
            )
        target = _target_for_path(path=path, option_names=body_options[path])
        try:
            data = discovery_schema_response(
                target=target,
                api="tagmanager",
                api_version="v2",
            )
        except ValueError:
            exit_with_diagnostic(
                exit_code=2,
                category="invalid_arguments",
                message="--command does not have an official Discovery request descriptor.",
                command="gtmctl sdk schema",
            )
        write_success(command="gtmctl sdk schema", data=data)

    root.add_typer(app, name="sdk")
    return app
