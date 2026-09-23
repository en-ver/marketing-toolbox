"""Official GTM account and container read command families."""

from __future__ import annotations

from typing import Annotated

import typer

from gtmctl.commands._common import run_command
from gtmctl.commands.container_actions import register_container_action_commands
from gtmctl.commands.core_mutations import (
    register_container_core_mutation_commands,
    register_workspace_core_mutation_commands,
)
from gtmctl.commands.environment_mutations import register_environment_mutation_commands
from gtmctl.commands.tag_mutations import (
    _dry_run,
    _validate_execution_mode,
    _validate_fingerprint,
)
from gtmctl.commands.version_mutations import register_version_mutation_commands
from gtmctl.commands.workspace_discovery import register_workspace_discovery_commands
from gtmctl.commands.workspace_operations import register_workspace_action_commands
from gtmctl.foundation.body import read_json_object
from gtmctl.foundation.validation import (
    RequestValidationError,
    validate_account_parent,
    validate_account_path,
    validate_container_path,
    validate_page_token,
    validate_user_permission_path,
    validate_workspace_parent,
    validate_workspace_path,
)
from gtmctl.operations import mutations, reads

accounts_app = typer.Typer(
    help="Official GTM account operations.", no_args_is_help=True
)
containers_app = typer.Typer(
    help="Official GTM container operations within an account.", no_args_is_help=True
)
workspaces_app = typer.Typer(
    help="Official GTM workspace operations within a container.", no_args_is_help=True
)
containers_app.add_typer(workspaces_app, name="workspaces")
accounts_app.add_typer(containers_app, name="containers")
register_workspace_discovery_commands(workspaces_app)
register_workspace_core_mutation_commands(workspaces_app)
register_workspace_action_commands(workspaces_app)
register_container_core_mutation_commands(containers_app)
register_container_action_commands(containers_app)

user_permissions_app = typer.Typer(
    help="Sensitive official GTM account user-permission operations.",
    no_args_is_help=True,
)
accounts_app.add_typer(user_permissions_app, name="user-permissions")

environments_app = typer.Typer(
    help="Official GTM container environment mutations.", no_args_is_help=True
)
containers_app.add_typer(environments_app, name="environments")
register_environment_mutation_commands(environments_app)

versions_app = typer.Typer(
    help="Official GTM container version mutations.", no_args_is_help=True
)
containers_app.add_typer(versions_app, name="versions")
register_version_mutation_commands(versions_app)


@accounts_app.command("list")
def accounts_list(
    page_token: Annotated[
        str | None, typer.Option("--page-token", help="Official continuation token.")
    ] = None,
    include_google_tags: Annotated[
        bool, typer.Option("--include-google-tags", help="Include Google tag accounts.")
    ] = False,
) -> None:
    """List one official page of accessible GTM accounts."""
    run_command(
        command="gtmctl accounts list",
        operation=lambda: (
            validate_page_token(page_token),
            reads.list_accounts(
                page_token=page_token, include_google_tags=include_google_tags
            ),
        )[1],
    )


@accounts_app.command("get")
def accounts_get(
    path: Annotated[str, typer.Option("--path", help="GTM account resource path.")],
) -> None:
    """Get one official GTM account resource."""
    run_command(
        command="gtmctl accounts get",
        operation=lambda: (validate_account_path(path), reads.get_account(path))[1],
    )


@accounts_app.command("update")
def accounts_update(
    path: Annotated[str, typer.Option("--path", help="GTM account resource path.")],
    body: Annotated[
        str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
    ],
    fingerprint: Annotated[
        str | None,
        typer.Option("--fingerprint", help="Current official resource fingerprint."),
    ] = None,
    acknowledge_account_update: Annotated[
        bool,
        typer.Option(
            "--acknowledge-account-update",
            help="Acknowledge this high-impact GTM account update.",
        ),
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Execute the Google API mutation.")
    ] = False,
) -> None:
    """Update one GTM account after explicit acknowledgement."""

    def operation() -> dict[str, object]:
        validate_account_path(path)
        _validate_execution_mode(dry_run=dry_run, apply=apply)
        _validate_fingerprint(fingerprint)
        if not acknowledge_account_update:
            raise RequestValidationError(
                "--acknowledge-account-update is required before updating an account."
            )
        request_body = read_json_object(body)
        if dry_run:
            return _dry_run(
                operation="accounts.update",
                target=path,
                body=request_body,
                fingerprint=fingerprint,
            )
        return mutations.update_account(path, request_body, fingerprint)

    run_command(command="gtmctl accounts update", operation=operation)


def _require_permission_acknowledgement(value: bool) -> None:
    if not value:
        raise RequestValidationError(
            "--acknowledge-permission-change is required before changing account user permissions."
        )


@user_permissions_app.command("get")
def user_permissions_get(
    path: Annotated[
        str, typer.Option("--path", help="GTM account user-permission resource path.")
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge that this response contains sensitive access data.",
        ),
    ] = False,
) -> None:
    """Get one sensitive GTM account user-permission resource."""

    def operation() -> dict[str, object]:
        validate_user_permission_path(path)
        if not acknowledge_sensitive_data:
            raise RequestValidationError(
                "--acknowledge-sensitive-data is required before reading account user permissions."
            )
        return reads.get_user_permission(path)

    run_command(command="gtmctl accounts user-permissions get", operation=operation)


@user_permissions_app.command("list")
def user_permissions_list(
    parent: Annotated[str, typer.Option("--parent", help="GTM account resource path.")],
    page_token: Annotated[
        str | None, typer.Option("--page-token", help="Official continuation token.")
    ] = None,
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge that this response contains sensitive access data.",
        ),
    ] = False,
) -> None:
    """List one official page of sensitive account user permissions."""

    def operation() -> dict[str, object]:
        validate_account_parent(parent)
        validate_page_token(page_token)
        if not acknowledge_sensitive_data:
            raise RequestValidationError(
                "--acknowledge-sensitive-data is required before reading account user permissions."
            )
        return reads.list_user_permissions(parent, page_token=page_token)

    run_command(command="gtmctl accounts user-permissions list", operation=operation)


@user_permissions_app.command("create")
def user_permissions_create(
    parent: Annotated[str, typer.Option("--parent", help="GTM account resource path.")],
    body: Annotated[
        str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
    ],
    acknowledge_permission_change: Annotated[
        bool,
        typer.Option(
            "--acknowledge-permission-change",
            help="Acknowledge this account user-permission change.",
        ),
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Execute the Google API mutation.")
    ] = False,
) -> None:
    """Create one account user permission after explicit acknowledgement."""

    def operation() -> dict[str, object]:
        validate_account_parent(parent)
        _validate_execution_mode(dry_run=dry_run, apply=apply)
        _require_permission_acknowledgement(acknowledge_permission_change)
        request_body = read_json_object(body)
        if dry_run:
            return _dry_run(
                operation="user-permissions.create", target=parent, body=request_body
            )
        return mutations.create_user_permission(parent, request_body)

    run_command(command="gtmctl accounts user-permissions create", operation=operation)


@user_permissions_app.command("update")
def user_permissions_update(
    path: Annotated[
        str, typer.Option("--path", help="GTM account user-permission resource path.")
    ],
    body: Annotated[
        str, typer.Option("--body", help="UTF-8 JSON object file, or - for stdin.")
    ],
    acknowledge_permission_change: Annotated[
        bool,
        typer.Option(
            "--acknowledge-permission-change",
            help="Acknowledge this account user-permission change.",
        ),
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Execute the Google API mutation.")
    ] = False,
) -> None:
    """Update one account user permission after explicit acknowledgement."""

    def operation() -> dict[str, object]:
        validate_user_permission_path(path)
        _validate_execution_mode(dry_run=dry_run, apply=apply)
        _require_permission_acknowledgement(acknowledge_permission_change)
        request_body = read_json_object(body)
        if dry_run:
            return _dry_run(
                operation="user-permissions.update", target=path, body=request_body
            )
        return mutations.update_user_permission(path, request_body)

    run_command(command="gtmctl accounts user-permissions update", operation=operation)


@user_permissions_app.command("delete")
def user_permissions_delete(
    path: Annotated[
        str, typer.Option("--path", help="GTM account user-permission resource path.")
    ],
    acknowledge_permission_change: Annotated[
        bool,
        typer.Option(
            "--acknowledge-permission-change",
            help="Acknowledge this account user-permission change.",
        ),
    ] = False,
    acknowledge_user_permission_delete: Annotated[
        bool,
        typer.Option(
            "--acknowledge-user-permission-delete",
            help="Acknowledge removal of this account user permission.",
        ),
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Execute the Google API mutation.")
    ] = False,
) -> None:
    """Delete one account user permission after explicit acknowledgements."""

    def operation() -> dict[str, object]:
        validate_user_permission_path(path)
        _validate_execution_mode(dry_run=dry_run, apply=apply)
        _require_permission_acknowledgement(acknowledge_permission_change)
        if not acknowledge_user_permission_delete:
            raise RequestValidationError(
                "--acknowledge-user-permission-delete is required before deleting an account user permission."
            )
        if dry_run:
            return _dry_run(operation="user-permissions.delete", target=path)
        return mutations.delete_user_permission(path)

    run_command(command="gtmctl accounts user-permissions delete", operation=operation)


@containers_app.command("list")
def containers_list(
    parent: Annotated[str, typer.Option("--parent", help="GTM account resource path.")],
    page_token: Annotated[
        str | None, typer.Option("--page-token", help="Official continuation token.")
    ] = None,
) -> None:
    """List one official page of containers for an account."""
    run_command(
        command="gtmctl accounts containers list",
        operation=lambda: (
            validate_account_parent(parent),
            validate_page_token(page_token),
            reads.list_containers(parent, page_token=page_token),
        )[2],
    )


@containers_app.command("get")
def containers_get(
    path: Annotated[str, typer.Option("--path", help="GTM container resource path.")],
) -> None:
    """Get one official GTM container resource."""
    run_command(
        command="gtmctl accounts containers get",
        operation=lambda: (validate_container_path(path), reads.get_container(path))[1],
    )


@containers_app.command("lookup")
def containers_lookup(
    destination_id: Annotated[
        str | None, typer.Option("--destination-id", help="Official destination ID.")
    ] = None,
    tag_id: Annotated[
        str | None, typer.Option("--tag-id", help="Official Google tag ID.")
    ] = None,
) -> None:
    """Look up the official GTM container for a destination or Google tag."""

    def operation() -> dict[str, object]:
        if not destination_id and not tag_id:
            from gtmctl.foundation.validation import RequestValidationError

            raise RequestValidationError(
                "Specify at least one of --destination-id or --tag-id."
            )
        return reads.lookup_container(destination_id=destination_id, tag_id=tag_id)

    run_command(command="gtmctl accounts containers lookup", operation=operation)


@workspaces_app.command("list")
def workspaces_list(
    parent: Annotated[
        str, typer.Option("--parent", help="GTM container resource path.")
    ],
    page_token: Annotated[
        str | None, typer.Option("--page-token", help="Official continuation token.")
    ] = None,
) -> None:
    """List one official page of workspaces for a container."""
    run_command(
        command="gtmctl accounts containers workspaces list",
        operation=lambda: (
            validate_workspace_parent(parent),
            validate_page_token(page_token),
            reads.list_workspaces(parent, page_token=page_token),
        )[2],
    )


@workspaces_app.command("get")
def workspaces_get(
    path: Annotated[str, typer.Option("--path", help="GTM workspace resource path.")],
) -> None:
    """Get one official GTM workspace resource."""
    run_command(
        command="gtmctl accounts containers workspaces get",
        operation=lambda: (validate_workspace_path(path), reads.get_workspace(path))[1],
    )


destinations_app = typer.Typer(
    help="Official GTM container destination discovery.", no_args_is_help=True
)
version_headers_app = typer.Typer(
    help="Official GTM container version-header discovery.", no_args_is_help=True
)
containers_app.add_typer(destinations_app, name="destinations")
containers_app.add_typer(version_headers_app, name="version-headers")


@containers_app.command("snippet")
def containers_snippet(
    path: Annotated[str, typer.Option("--path", help="GTM container resource path.")],
) -> None:
    """Get the official installation snippet for one container."""
    run_command(
        command="gtmctl accounts containers snippet",
        operation=lambda: (
            validate_container_path(path),
            reads.get_container_snippet(path),
        )[1],
    )


@destinations_app.command("list")
def destinations_list(
    parent: Annotated[
        str, typer.Option("--parent", help="GTM container resource path.")
    ],
) -> None:
    """List official container destinations."""
    run_command(
        command="gtmctl accounts containers destinations list",
        operation=lambda: (
            validate_workspace_parent(parent),
            reads.list_destinations(parent),
        )[1],
    )


@version_headers_app.command("list")
def version_headers_list(
    parent: Annotated[
        str, typer.Option("--parent", help="GTM container resource path.")
    ],
    page_token: Annotated[
        str | None, typer.Option("--page-token", help="Official continuation token.")
    ] = None,
    include_deleted: Annotated[
        bool, typer.Option("--include-deleted", help="Include deleted version headers.")
    ] = False,
) -> None:
    """List one official page of version headers."""
    run_command(
        command="gtmctl accounts containers version-headers list",
        operation=lambda: (
            validate_workspace_parent(parent),
            validate_page_token(page_token),
            reads.list_version_headers(
                parent, page_token=page_token, include_deleted=include_deleted
            ),
        )[2],
    )


@version_headers_app.command("latest")
def version_headers_latest(
    parent: Annotated[
        str, typer.Option("--parent", help="GTM container resource path.")
    ],
) -> None:
    """Get the official latest container version header."""
    run_command(
        command="gtmctl accounts containers version-headers latest",
        operation=lambda: (
            validate_workspace_parent(parent),
            reads.get_latest_version_header(parent),
        )[1],
    )
