"""Guarded GTM built-in variable mutation command registration."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from gtmctl.commands._common import run_command
from gtmctl.commands.tag_mutations import _dry_run, _validate_execution_mode
from gtmctl.foundation.validation import (
    RequestValidationError,
    validate_built_in_variables_path,
    validate_workspace_path,
)
from gtmctl.operations import mutations


def _validate_variable_types(variable_types: str | list[str] | None) -> None:
    values = [variable_types] if isinstance(variable_types, str) else variable_types
    if values is not None and any(
        not variable_type or variable_type.strip() != variable_type
        for variable_type in values
    ):
        raise RequestValidationError(
            "--type must be a non-empty built-in variable type without surrounding whitespace."
        )


def register_built_in_variable_mutation_commands(entity_app: typer.Typer) -> None:
    """Add guarded create, delete, and revert commands for built-in variables."""

    @entity_app.command("create")
    def built_in_variables_create(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM workspace resource path.")
        ],
        variable_type: Annotated[
            list[str] | None,
            typer.Option(
                "--type", help="Official built-in variable type to enable (repeatable)."
            ),
        ] = None,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Enable one built-in variable in a workspace."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(parent)
            _validate_variable_types(variable_type)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if dry_run:
                return _dry_run(
                    operation="built-in-variables.create", target=parent
                ) | {"type": variable_type}
            return mutations.create_built_in_variable(parent, variable_type)

        run_command(
            command="gtmctl accounts containers workspaces built-in-variables create",
            operation=operation,
        )

    @entity_app.command("delete")
    def built_in_variables_delete(
        path: Annotated[
            str,
            typer.Option(
                "--path", help="GTM built-in variables collection resource path."
            ),
        ],
        variable_type: Annotated[
            list[str] | None,
            typer.Option(
                "--type",
                help="Official built-in variable type to disable (repeatable).",
            ),
        ] = None,
        acknowledge_delete: Annotated[
            bool,
            typer.Option(
                "--acknowledge-built-in-variable-delete",
                help="Acknowledge removal of this built-in variable from the workspace.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Disable one built-in variable in a workspace."""

        def operation() -> dict[str, Any]:
            validate_built_in_variables_path(path)
            _validate_variable_types(variable_type)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_delete:
                raise RequestValidationError(
                    "--acknowledge-built-in-variable-delete is required before disabling a built-in variable."
                )
            if dry_run:
                return _dry_run(operation="built-in-variables.delete", target=path) | {
                    "type": variable_type
                }
            return mutations.delete_built_in_variable(path, variable_type)

        run_command(
            command="gtmctl accounts containers workspaces built-in-variables delete",
            operation=operation,
        )

    @entity_app.command("revert")
    def built_in_variables_revert(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
        variable_type: Annotated[
            str | None,
            typer.Option("--type", help="Official built-in variable type to revert."),
        ] = None,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Revert one built-in variable to its base workspace state."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_variable_types(variable_type)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if dry_run:
                return _dry_run(operation="built-in-variables.revert", target=path) | {
                    "type": variable_type
                }
            return mutations.revert_built_in_variable(path, variable_type)

        run_command(
            command="gtmctl accounts containers workspaces built-in-variables revert",
            operation=operation,
        )
