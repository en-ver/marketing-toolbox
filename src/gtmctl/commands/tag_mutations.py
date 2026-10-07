"""Guarded GTM workspace entity mutation command registration."""

from collections.abc import Callable
from typing import Annotated, Any, cast

import typer

from gtmctl.commands._common import (
    DRY_RUN_HELP,
    build_dry_run_plan,
    run_command,
    validate_execution_mode,
    validate_fingerprint,
)
from gtmctl.foundation.body import read_json_object
from gtmctl.foundation.validation import (
    RequestValidationError,
    validate_workspace_entity_parent,
    validate_workspace_entity_path,
)
from gtmctl.operations import mutations


def _mutation_adapter(name: str) -> Callable[..., dict[str, Any]]:
    """Resolve one explicitly named local mutation adapter."""
    return cast(Callable[..., dict[str, Any]], getattr(mutations, name))


def register_workspace_entity_mutation_commands(
    entity_app: typer.Typer,
    *,
    entity: str,
    singular: str | None = None,
    cli_name: str | None = None,
    include_revert: bool = True,
) -> None:
    """Add the applicable ordinary mutations for one GTM workspace entity type."""
    singular = entity[:-1] if singular is None else singular
    cli_name = entity if cli_name is None else cli_name

    @entity_app.command("create")
    def entity_create(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM workspace resource path.")
        ],
        body: Annotated[
            str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
        ],
        dry_run: Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Create one resource in a workspace."""
        command = f"gtmctl accounts containers workspaces {cli_name} create"

        def operation() -> dict[str, Any]:
            validate_workspace_entity_parent(parent)
            validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            if dry_run:
                return build_dry_run_plan(
                    operation=f"{entity}.create", target=parent, body=request_body
                )
            return _mutation_adapter(f"create_{singular}")(parent, request_body)

        run_command(command=command, operation=operation)

    @entity_app.command("update")
    def entity_update(
        path: Annotated[str, typer.Option("--path", help="GTM resource path.")],
        body: Annotated[
            str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
        ],
        fingerprint: Annotated[
            str | None,
            typer.Option(
                "--fingerprint", help="Current official resource fingerprint."
            ),
        ] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Update one resource in a workspace."""
        command = f"gtmctl accounts containers workspaces {cli_name} update"

        def operation() -> dict[str, Any]:
            validate_workspace_entity_path(path, entity)
            validate_execution_mode(dry_run=dry_run, apply=apply)
            validate_fingerprint(fingerprint)
            request_body = read_json_object(body)
            if dry_run:
                return build_dry_run_plan(
                    operation=f"{entity}.update",
                    target=path,
                    body=request_body,
                    fingerprint=fingerprint,
                )
            return _mutation_adapter(f"update_{singular}")(
                path, request_body, fingerprint
            )

        run_command(command=command, operation=operation)

    if include_revert:

        @entity_app.command("revert")
        def entity_revert(
            path: Annotated[str, typer.Option("--path", help="GTM resource path.")],
            fingerprint: Annotated[
                str | None,
                typer.Option(
                    "--fingerprint", help="Current official resource fingerprint."
                ),
            ] = None,
            dry_run: Annotated[
                bool, typer.Option("--dry-run", help=DRY_RUN_HELP)
            ] = False,
            apply: Annotated[
                bool, typer.Option("--apply", help="Execute the Google API mutation.")
            ] = False,
        ) -> None:
            """Revert one resource to its base workspace state."""
            command = f"gtmctl accounts containers workspaces {cli_name} revert"

            def operation() -> dict[str, Any]:
                validate_workspace_entity_path(path, entity)
                validate_execution_mode(dry_run=dry_run, apply=apply)
                validate_fingerprint(fingerprint)
                if dry_run:
                    return build_dry_run_plan(
                        operation=f"{entity}.revert",
                        target=path,
                        fingerprint=fingerprint,
                    )
                return _mutation_adapter(f"revert_{singular}")(path, fingerprint)

            run_command(command=command, operation=operation)

    @entity_app.command("delete")
    def entity_delete(
        path: Annotated[str, typer.Option("--path", help="GTM resource path.")],
        acknowledge_delete: Annotated[
            bool,
            typer.Option(
                f"--acknowledge-{cli_name.rstrip('s')}-delete",
                help=f"Acknowledge permanent deletion of this {cli_name.rstrip('s')} from the workspace.",
            ),
        ] = False,
        dry_run: Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Delete one workspace resource; requires containers access, not delete access."""
        command = f"gtmctl accounts containers workspaces {cli_name} delete"

        def operation() -> dict[str, Any]:
            validate_workspace_entity_path(path, entity)
            validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_delete:
                raise RequestValidationError(
                    f"--acknowledge-{cli_name.rstrip('s')}-delete is required before deleting a {cli_name.rstrip('s')}."
                )
            if dry_run:
                return build_dry_run_plan(operation=f"{entity}.delete", target=path)
            return _mutation_adapter(f"delete_{singular}")(path)

        run_command(command=command, operation=operation)
