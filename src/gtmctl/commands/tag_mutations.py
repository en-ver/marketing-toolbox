"""Guarded GTM workspace entity mutation command registration."""

from collections.abc import Callable
from typing import Annotated, Any, cast

import typer

from gtmctl.commands._common import run_command
from gtmctl.foundation.body import body_sha256, read_json_object
from gtmctl.foundation.validation import (
    RequestValidationError,
    validate_workspace_entity_parent,
    validate_workspace_entity_path,
)
from gtmctl.operations import mutations


def _validate_execution_mode(*, dry_run: bool, apply: bool) -> None:
    if dry_run == apply:
        raise RequestValidationError("Specify exactly one of --dry-run or --apply.")


def _validate_fingerprint(fingerprint: str | None) -> None:
    if fingerprint is not None and (
        not fingerprint or fingerprint.strip() != fingerprint
    ):
        raise RequestValidationError(
            "--fingerprint must be a non-empty value without surrounding whitespace."
        )


def _mutation_adapter(name: str) -> Callable[..., dict[str, Any]]:
    """Resolve one explicitly named local mutation adapter."""
    return cast(Callable[..., dict[str, Any]], getattr(mutations, name))


def _dry_run(
    *,
    operation: str,
    target: str,
    body: dict[str, Any] | None = None,
    fingerprint: str | None = None,
) -> dict[str, Any]:
    """Produce a deterministic plan without exposing the request body."""
    plan: dict[str, Any] = {
        "applied": False,
        "mode": "dry-run",
        "operation": operation,
        "target": target,
    }
    if fingerprint is not None:
        plan["fingerprint"] = fingerprint
    if body is not None:
        plan["bodySha256"] = body_sha256(body)
    return plan


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
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Create one resource in a workspace."""
        command = f"gtmctl accounts containers workspaces {entity} create"

        def operation() -> dict[str, Any]:
            validate_workspace_entity_parent(parent)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
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
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Update one resource in a workspace."""
        command = f"gtmctl accounts containers workspaces {entity} update"

        def operation() -> dict[str, Any]:
            validate_workspace_entity_path(path, entity)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_fingerprint(fingerprint)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
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
                bool,
                typer.Option("--dry-run", help="Validate and print a mutation plan."),
            ] = False,
            apply: Annotated[
                bool, typer.Option("--apply", help="Execute the Google API mutation.")
            ] = False,
        ) -> None:
            """Revert one resource to its base workspace state."""
            command = f"gtmctl accounts containers workspaces {entity} revert"

            def operation() -> dict[str, Any]:
                validate_workspace_entity_path(path, entity)
                _validate_execution_mode(dry_run=dry_run, apply=apply)
                _validate_fingerprint(fingerprint)
                if dry_run:
                    return _dry_run(
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
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Delete one resource from a workspace."""
        command = f"gtmctl accounts containers workspaces {entity} delete"

        def operation() -> dict[str, Any]:
            validate_workspace_entity_path(path, entity)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_delete:
                raise RequestValidationError(
                    f"--acknowledge-{cli_name.rstrip('s')}-delete is required before deleting a {cli_name.rstrip('s')}."
                )
            if dry_run:
                return _dry_run(operation=f"{entity}.delete", target=path)
            return _mutation_adapter(f"delete_{singular}")(path)

        run_command(command=command, operation=operation)


def register_tag_mutation_commands(tags_app: typer.Typer) -> None:
    """Add the four catalogued ordinary tag workspace mutations."""
    register_workspace_entity_mutation_commands(tags_app, entity="tags")
