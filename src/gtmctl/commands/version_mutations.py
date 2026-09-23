"""GTM container version mutation command registration."""

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
    validate_container_parent,
    validate_version_path,
)
from gtmctl.operations import mutations, reads


def register_version_mutation_commands(versions_app: typer.Typer) -> None:
    """Add ordinary GTM container-version mutations."""

    @versions_app.command("get")
    def versions_get(
        path: Annotated[
            str, typer.Option("--path", help="GTM container version resource path.")
        ],
        container_version_id: Annotated[
            str | None,
            typer.Option(
                "--container-version-id",
                help="Official container version ID query parameter.",
            ),
        ] = None,
    ) -> None:
        """Get one official container version."""
        run_command(
            command="gtmctl accounts containers versions get",
            operation=lambda: (
                validate_version_path(path),
                reads.get_version(path, container_version_id=container_version_id),
            )[1],
        )

    @versions_app.command("live")
    def versions_live(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM container resource path.")
        ],
    ) -> None:
        """Get the official live container version."""
        run_command(
            command="gtmctl accounts containers versions live",
            operation=lambda: (
                validate_container_parent(parent),
                reads.get_live_version(parent),
            )[1],
        )

    @versions_app.command("update")
    def versions_update(
        path: Annotated[
            str, typer.Option("--path", help="GTM container version resource path.")
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
        """Update one container version."""

        def operation() -> dict[str, Any]:
            validate_version_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_fingerprint(fingerprint)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="versions.update",
                    target=path,
                    body=request_body,
                    fingerprint=fingerprint,
                )
            return mutations.update_version(path, request_body, fingerprint)

        run_command(
            command="gtmctl accounts containers versions update", operation=operation
        )

    @versions_app.command("delete")
    def versions_delete(
        path: Annotated[
            str, typer.Option("--path", help="GTM container version resource path.")
        ],
        acknowledge_delete: Annotated[
            bool,
            typer.Option(
                "--acknowledge-version-delete",
                help="Acknowledge permanent deletion of this container version.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Delete one container version."""

        def operation() -> dict[str, Any]:
            validate_version_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_delete:
                raise RequestValidationError(
                    "--acknowledge-version-delete is required before deleting a version."
                )
            if dry_run:
                return _dry_run(operation="versions.delete", target=path)
            return mutations.delete_version(path)

        run_command(
            command="gtmctl accounts containers versions delete", operation=operation
        )

    @versions_app.command("publish")
    def versions_publish(
        path: Annotated[
            str, typer.Option("--path", help="GTM container version resource path.")
        ],
        fingerprint: Annotated[
            str | None,
            typer.Option(
                "--fingerprint", help="Current official resource fingerprint."
            ),
        ] = None,
        acknowledge_publish: Annotated[
            bool,
            typer.Option(
                "--acknowledge-publish",
                help="Acknowledge that this publishes the container version.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a publish plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Publish the container version.")
        ] = False,
    ) -> None:
        """Publish one container version."""

        def operation() -> dict[str, Any]:
            validate_version_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_fingerprint(fingerprint)
            if not acknowledge_publish:
                raise RequestValidationError(
                    "--acknowledge-publish is required before publishing a version."
                )
            if dry_run:
                plan = _dry_run(
                    operation="versions.publish", target=path, fingerprint=fingerprint
                )
                plan["versionPublished"] = False
                return plan
            return mutations.publish_version(path, fingerprint)

        run_command(
            command="gtmctl accounts containers versions publish", operation=operation
        )

    @versions_app.command("set-latest")
    def versions_set_latest(
        path: Annotated[
            str, typer.Option("--path", help="GTM container version resource path.")
        ],
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Set one container version as latest."""

        def operation() -> dict[str, Any]:
            validate_version_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if dry_run:
                return _dry_run(operation="versions.set-latest", target=path)
            return mutations.set_latest_version(path)

        run_command(
            command="gtmctl accounts containers versions set-latest",
            operation=operation,
        )

    @versions_app.command("undelete")
    def versions_undelete(
        path: Annotated[
            str, typer.Option("--path", help="GTM container version resource path.")
        ],
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Restore one deleted container version."""

        def operation() -> dict[str, Any]:
            validate_version_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if dry_run:
                return _dry_run(operation="versions.undelete", target=path)
            return mutations.undelete_version(path)

        run_command(
            command="gtmctl accounts containers versions undelete", operation=operation
        )
