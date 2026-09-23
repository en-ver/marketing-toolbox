"""GTM container environment mutation command registration."""

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
    validate_environment_parent,
    validate_environment_path,
    validate_page_token,
)
from gtmctl.operations import mutations, reads


def register_environment_mutation_commands(environments_app: typer.Typer) -> None:
    """Add ordinary GTM container environment mutations."""

    @environments_app.command("get")
    def environments_get(
        path: Annotated[
            str, typer.Option("--path", help="GTM environment resource path.")
        ],
    ) -> None:
        """Get one official GTM environment."""
        run_command(
            command="gtmctl accounts containers environments get",
            operation=lambda: (
                validate_environment_path(path),
                reads.get_environment(path),
            )[1],
        )

    @environments_app.command("list")
    def environments_list(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM container resource path.")
        ],
        page_token: Annotated[
            str | None,
            typer.Option("--page-token", help="Official continuation token."),
        ] = None,
    ) -> None:
        """List one official page of environments."""
        run_command(
            command="gtmctl accounts containers environments list",
            operation=lambda: (
                validate_environment_parent(parent),
                validate_page_token(page_token),
                reads.list_environments(parent, page_token=page_token),
            )[2],
        )

    @environments_app.command("create")
    def environments_create(
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
        """Create one environment in a container."""

        def operation() -> dict[str, Any]:
            validate_environment_parent(parent)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="environments.create", target=parent, body=request_body
                )
            return mutations.create_environment(parent, request_body)

        run_command(
            command="gtmctl accounts containers environments create",
            operation=operation,
        )

    @environments_app.command("update")
    def environments_update(
        path: Annotated[
            str, typer.Option("--path", help="GTM environment resource path.")
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
        """Update one environment in a container."""

        def operation() -> dict[str, Any]:
            validate_environment_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_fingerprint(fingerprint)
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="environments.update",
                    target=path,
                    body=request_body,
                    fingerprint=fingerprint,
                )
            return mutations.update_environment(path, request_body, fingerprint)

        run_command(
            command="gtmctl accounts containers environments update",
            operation=operation,
        )

    @environments_app.command("delete")
    def environments_delete(
        path: Annotated[
            str, typer.Option("--path", help="GTM environment resource path.")
        ],
        acknowledge_delete: Annotated[
            bool,
            typer.Option(
                "--acknowledge-environment-delete",
                help="Acknowledge permanent deletion of this environment from the container.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Delete one environment from a container."""

        def operation() -> dict[str, Any]:
            validate_environment_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_delete:
                raise RequestValidationError(
                    "--acknowledge-environment-delete is required before deleting an environment."
                )
            if dry_run:
                return _dry_run(operation="environments.delete", target=path)
            return mutations.delete_environment(path)

        run_command(
            command="gtmctl accounts containers environments delete",
            operation=operation,
        )

    @environments_app.command("reauthorize")
    def environments_reauthorize(
        path: Annotated[
            str, typer.Option("--path", help="GTM environment resource path.")
        ],
        body: Annotated[
            str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
        ],
        acknowledge_reauthorize: Annotated[
            bool,
            typer.Option(
                "--acknowledge-environment-reauthorize",
                help="Acknowledge reauthorization of this environment.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Reauthorize one GTM environment with the official publish scope."""

        def operation() -> dict[str, Any]:
            validate_environment_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            if not acknowledge_reauthorize:
                raise RequestValidationError(
                    "--acknowledge-environment-reauthorize is required before reauthorizing an environment."
                )
            request_body = read_json_object(body)
            if dry_run:
                return _dry_run(
                    operation="environments.reauthorize", target=path, body=request_body
                )
            return mutations.reauthorize_environment(path, request_body)

        run_command(
            command="gtmctl accounts containers environments reauthorize",
            operation=operation,
        )
