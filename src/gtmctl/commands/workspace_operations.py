"""Guarded GTM workspace action command registration."""

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
from gtmctl.foundation.validation import RequestValidationError, validate_workspace_path
from gtmctl.operations import mutations


def _require_acknowledgement(value: bool, flag: str, action: str) -> None:
    if not value:
        raise RequestValidationError(f"{flag} is required before {action}.")


def register_workspace_action_commands(workspaces_app: typer.Typer) -> None:
    """Add guarded official workspace action endpoints."""

    @workspaces_app.command("sync")
    def workspaces_sync(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Synchronize one workspace with its latest container version."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if dry_run:
                return _dry_run(operation="workspaces.sync", target=path)
            return mutations.sync_workspace(path)

        run_command(
            command="gtmctl accounts containers workspaces sync", operation=operation
        )

    @workspaces_app.command("quick-preview")
    def workspaces_quick_preview(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
        acknowledge_quick_preview: Annotated[
            bool,
            typer.Option(
                "--acknowledge-quick-preview",
                help="Acknowledge creation of a temporary workspace preview.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a preview plan.")
        ] = False,
        apply: Annotated[
            bool,
            typer.Option("--apply", help="Create the temporary workspace preview."),
        ] = False,
    ) -> None:
        """Create a temporary preview for one workspace."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _require_acknowledgement(
                acknowledge_quick_preview,
                "--acknowledge-quick-preview",
                "creating a workspace quick preview",
            )
            if dry_run:
                return _dry_run(operation="workspaces.quick-preview", target=path)
            return mutations.quick_preview_workspace(path)

        run_command(
            command="gtmctl accounts containers workspaces quick-preview",
            operation=operation,
        )

    @workspaces_app.command("resolve-conflict")
    def workspaces_resolve_conflict(
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
        """Resolve one workspace conflict with an official entity payload."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_fingerprint(fingerprint)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="workspaces.resolve-conflict",
                    target=path,
                    body=request_body,
                    fingerprint=fingerprint,
                )
            return mutations.resolve_workspace_conflict(path, request_body, fingerprint)

        run_command(
            command="gtmctl accounts containers workspaces resolve-conflict",
            operation=operation,
        )

    @workspaces_app.command("bulk-update")
    def workspaces_bulk_update(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
        body: Annotated[
            str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
        ],
        acknowledge_bulk_update: Annotated[
            bool,
            typer.Option(
                "--acknowledge-workspace-bulk-update",
                help="Acknowledge applying all proposed workspace changes.",
            ),
        ] = False,
        dry_run: Annotated[
            bool,
            typer.Option("--dry-run", help="Validate and print a bulk-update plan."),
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the workspace bulk update.")
        ] = False,
    ) -> None:
        """Apply the official proposed changes to one workspace."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            _require_acknowledgement(
                acknowledge_bulk_update,
                "--acknowledge-workspace-bulk-update",
                "applying a workspace bulk update",
            )
            if dry_run:
                return _dry_run(
                    operation="workspaces.bulk-update", target=path, body=request_body
                )
            return mutations.bulk_update_workspace(path, request_body)

        run_command(
            command="gtmctl accounts containers workspaces bulk-update",
            operation=operation,
        )

    @workspaces_app.command("create-version")
    def workspaces_create_version(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
        body: Annotated[
            str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
        ],
        acknowledge_version_create: Annotated[
            bool,
            typer.Option(
                "--acknowledge-version-create",
                help="Acknowledge irreversible creation of a container version from this workspace.",
            ),
        ] = False,
        dry_run: Annotated[
            bool,
            typer.Option(
                "--dry-run", help="Validate and print a version-creation plan."
            ),
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Create the container version.")
        ] = False,
    ) -> None:
        """Create a container version from one workspace."""

        def operation() -> dict[str, Any]:
            validate_workspace_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            _require_acknowledgement(
                acknowledge_version_create,
                "--acknowledge-version-create",
                "creating a container version",
            )
            if dry_run:
                return _dry_run(
                    operation="workspaces.create-version",
                    target=path,
                    body=request_body,
                )
            return mutations.create_workspace_version(path, request_body)

        run_command(
            command="gtmctl accounts containers workspaces create-version",
            operation=operation,
        )
