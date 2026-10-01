"""Guarded GTM built-in variable mutation command registration."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from gtmctl.commands._common import DRY_RUN_HELP, run_command
from gtmctl.commands.tag_mutations import _dry_run, _validate_execution_mode
from gtmctl.foundation.validation import (
    RequestValidationError,
    validate_built_in_variables_path,
    validate_workspace_path,
)
from gtmctl.operations import mutations
from marketing_common.discovery import discovery_method_parameters


def _official_variable_types(method_id: str) -> tuple[str, ...]:
    """Read the closed ``type`` enum for one official built-in-variable method."""
    parameter = discovery_method_parameters(
        api="tagmanager", api_version="v2", method_id=method_id
    )["type"]
    return tuple(parameter["enum"])


_CREATE_VARIABLE_TYPES = _official_variable_types(
    "tagmanager.accounts.containers.workspaces.built_in_variables.create"
)
_DELETE_VARIABLE_TYPES = _official_variable_types(
    "tagmanager.accounts.containers.workspaces.built_in_variables.delete"
)
_REVERT_VARIABLE_TYPES = _official_variable_types(
    "tagmanager.accounts.containers.workspaces.built_in_variables.revert"
)


def _variable_type_help(action: str, variable_types: tuple[str, ...]) -> str:
    return f"Official built-in variable type to {action}. Valid values: " + ", ".join(
        variable_types
    )


def _validate_variable_types(
    variable_types: str | list[str] | None, allowed_types: tuple[str, ...]
) -> None:
    values = [variable_types] if isinstance(variable_types, str) else variable_types
    if values is not None and any(
        not variable_type or variable_type.strip() != variable_type
        for variable_type in values
    ):
        raise RequestValidationError(
            "--type must be a non-empty built-in variable type without surrounding whitespace."
        )
    if values is not None and any(
        variable_type not in allowed_types for variable_type in values
    ):
        raise RequestValidationError(
            "--type must be one of: " + ", ".join(allowed_types) + "."
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
                "--type",
                help=_variable_type_help("enable (repeatable)", _CREATE_VARIABLE_TYPES),
            ),
        ] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Enable one built-in variable in a workspace."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(parent)
            _validate_variable_types(variable_type, _CREATE_VARIABLE_TYPES)
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
                help=_variable_type_help(
                    "disable (repeatable)", _DELETE_VARIABLE_TYPES
                ),
            ),
        ] = None,
        acknowledge_delete: Annotated[
            bool,
            typer.Option(
                "--acknowledge-built-in-variable-delete",
                help="Acknowledge removal of this built-in variable from the workspace.",
            ),
        ] = False,
        dry_run: Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Disable one built-in variable in a workspace."""

        def operation() -> dict[str, Any]:
            validate_built_in_variables_path(path)
            _validate_variable_types(variable_type, _DELETE_VARIABLE_TYPES)
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
            typer.Option(
                "--type", help=_variable_type_help("revert", _REVERT_VARIABLE_TYPES)
            ),
        ] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Revert one built-in variable to its base workspace state."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_variable_types(variable_type, _REVERT_VARIABLE_TYPES)
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
