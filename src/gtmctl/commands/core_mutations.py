"""GTM container and workspace core mutation command registration."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from gtmctl.commands._common import run_command
from gtmctl.commands.tag_mutations import (
    _dry_run,
    _validate_execution_mode,
    _validate_fingerprint,
)
from gtmctl.foundation.body import read_json_object
from gtmctl.foundation.validation import (
    RequestValidationError,
    validate_account_parent,
    validate_container_parent,
    validate_container_path,
    validate_workspace_path,
)
from gtmctl.operations import mutations


def register_container_core_mutation_commands(containers_app: typer.Typer) -> None:
    """Add standard non-destructive container mutations."""

    @containers_app.command("create")
    def containers_create(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM account resource path.")
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
        """Create one container in an account."""

        def operation() -> dict[str, Any]:
            validate_account_parent(parent)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="containers.create", target=parent, body=request_body
                )
            return mutations.create_container(parent, request_body)

        run_command(command="gtmctl accounts containers create", operation=operation)

    @containers_app.command("update")
    def containers_update(
        path: Annotated[
            str, typer.Option("--path", help="GTM container resource path.")
        ],
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
        """Update one container."""

        def operation() -> dict[str, Any]:
            validate_container_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_fingerprint(fingerprint)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="containers.update",
                    target=path,
                    body=request_body,
                    fingerprint=fingerprint,
                )
            return mutations.update_container(path, request_body, fingerprint)

        run_command(command="gtmctl accounts containers update", operation=operation)

    @containers_app.command("delete")
    def containers_delete(
        path: Annotated[
            str, typer.Option("--path", help="GTM container resource path.")
        ],
        acknowledge_delete: Annotated[
            bool,
            typer.Option(
                "--acknowledge-container-delete",
                help="Acknowledge permanent deletion of this container.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a deletion plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API deletion.")
        ] = False,
    ) -> None:
        """Delete one container after explicit acknowledgement."""

        def operation() -> dict[str, Any]:
            validate_container_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_delete:
                raise RequestValidationError(
                    "--acknowledge-container-delete is required before deleting a container."
                )
            if dry_run:
                return _dry_run(operation="containers.delete", target=path)
            return mutations.delete_container(path)

        run_command(command="gtmctl accounts containers delete", operation=operation)


def register_workspace_core_mutation_commands(workspaces_app: typer.Typer) -> None:
    """Add standard non-destructive workspace mutations."""

    @workspaces_app.command("create")
    def workspaces_create(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM container resource path.")
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
        """Create one workspace in a container."""

        def operation() -> dict[str, Any]:
            validate_container_parent(parent)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="workspaces.create", target=parent, body=request_body
                )
            return mutations.create_workspace(parent, request_body)

        run_command(
            command="gtmctl accounts containers workspaces create", operation=operation
        )

    @workspaces_app.command("update")
    def workspaces_update(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
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
        """Update one workspace."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_fingerprint(fingerprint)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="workspaces.update",
                    target=path,
                    body=request_body,
                    fingerprint=fingerprint,
                )
            return mutations.update_workspace(path, request_body, fingerprint)

        run_command(
            command="gtmctl accounts containers workspaces update", operation=operation
        )

    @workspaces_app.command("delete")
    def workspaces_delete(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
        acknowledge_delete: Annotated[
            bool,
            typer.Option(
                "--acknowledge-workspace-delete",
                help="Acknowledge permanent deletion of this workspace.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a deletion plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API deletion.")
        ] = False,
    ) -> None:
        """Delete one workspace after explicit acknowledgement."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_delete:
                raise RequestValidationError(
                    "--acknowledge-workspace-delete is required before deleting a workspace."
                )
            if dry_run:
                return _dry_run(operation="workspaces.delete", target=path)
            return mutations.delete_workspace(path)

        run_command(
            command="gtmctl accounts containers workspaces delete", operation=operation
        )
