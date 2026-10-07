"""Read-only workspace entity discovery command registration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any

import typer

from gtmctl.commands._common import (
    DRY_RUN_HELP,
    build_dry_run_plan,
    run_command,
    validate_execution_mode,
)
from gtmctl.commands.built_in_variable_mutations import (
    register_built_in_variable_mutation_commands,
)
from gtmctl.commands.gallery_template_import import (
    register_gallery_template_import_command,
)
from gtmctl.commands.tag_mutations import register_workspace_entity_mutation_commands
from gtmctl.foundation.body import read_json_object
from gtmctl.foundation.validation import (
    validate_page_token,
    validate_workspace_entity_parent,
    validate_workspace_entity_path,
    validate_workspace_folder_path,
    validate_workspace_path,
)
from gtmctl.operations import mutations, reads

EntityListOperation = Callable[..., dict[str, Any]]
EntityGetOperation = Callable[..., dict[str, Any]]


@dataclass(frozen=True)
class _WorkspaceEntity:
    """One ordinary workspace entity's discovery and mutation registration data."""

    cli_name: str
    resource_name: str
    list_operation: EntityListOperation
    get_operation: EntityGetOperation
    mutation_entity: str
    mutation_singular: str
    include_revert: bool


_WORKSPACE_ENTITIES: tuple[_WorkspaceEntity, ...] = (
    _WorkspaceEntity(
        "tags",
        "tags",
        reads.list_tags,
        reads.get_tag,
        "tags",
        "tag",
        True,
    ),
    _WorkspaceEntity(
        "variables",
        "variables",
        reads.list_variables,
        reads.get_variable,
        "variables",
        "variable",
        True,
    ),
    _WorkspaceEntity(
        "triggers",
        "triggers",
        reads.list_triggers,
        reads.get_trigger,
        "triggers",
        "trigger",
        True,
    ),
    _WorkspaceEntity(
        "clients",
        "clients",
        reads.list_clients,
        reads.get_client,
        "clients",
        "client",
        True,
    ),
    _WorkspaceEntity(
        "folders",
        "folders",
        reads.list_folders,
        reads.get_folder,
        "folders",
        "folder",
        True,
    ),
    _WorkspaceEntity(
        "zones",
        "zones",
        reads.list_zones,
        reads.get_zone,
        "zones",
        "zone",
        True,
    ),
    _WorkspaceEntity(
        "transformations",
        "transformations",
        reads.list_transformations,
        reads.get_transformation,
        "transformations",
        "transformation",
        True,
    ),
    _WorkspaceEntity(
        "templates",
        "templates",
        reads.list_templates,
        reads.get_template,
        "templates",
        "template",
        True,
    ),
    _WorkspaceEntity(
        "gtag-config",
        "gtag_config",
        reads.list_gtag_configs,
        reads.get_gtag_config,
        "gtag_config",
        "gtag_config",
        False,
    ),
)


def _add_entity_commands(
    workspace_app: typer.Typer, entity: _WorkspaceEntity
) -> typer.Typer:
    """Register canonical get/list commands for one workspace collection."""
    entity_app = typer.Typer(
        help=(f"Official GTM workspace {entity.cli_name} discovery."),
        no_args_is_help=True,
    )

    @entity_app.command("list")
    def entity_list(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM workspace resource path.")
        ],
        page_token: Annotated[
            str | None,
            typer.Option("--page-token", help="Official continuation token."),
        ] = None,
    ) -> None:
        """List one official page of workspace resources."""
        run_command(
            command=f"gtmctl accounts containers workspaces {entity.cli_name} list",
            operation=lambda: (
                validate_workspace_entity_parent(parent),
                validate_page_token(page_token),
                getattr(reads, entity.list_operation.__name__)(
                    parent, page_token=page_token
                ),
            )[2],
        )

    @entity_app.command("get")
    def entity_get(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
    ) -> None:
        """Get one official workspace resource."""
        run_command(
            command=f"gtmctl accounts containers workspaces {entity.cli_name} get",
            operation=lambda: (
                validate_workspace_entity_path(path, entity.resource_name),
                getattr(reads, entity.get_operation.__name__)(path),
            )[1],
        )

    workspace_app.add_typer(entity_app, name=entity.cli_name)
    return entity_app


def register_workspace_discovery_commands(workspace_app: typer.Typer) -> None:
    """Attach read-only Discovery-client workspace commands to the workspace tree."""
    entity_apps = {
        entity.cli_name: _add_entity_commands(workspace_app, entity)
        for entity in _WORKSPACE_ENTITIES
    }
    folders_app = entity_apps["folders"]
    templates_app = entity_apps["templates"]

    built_in_variables_app = typer.Typer(
        help="Official GTM workspace built-in variable discovery.", no_args_is_help=True
    )

    @built_in_variables_app.command("list")
    def built_in_variables_list(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM workspace resource path.")
        ],
        page_token: Annotated[
            str | None,
            typer.Option("--page-token", help="Official continuation token."),
        ] = None,
    ) -> None:
        """List one official page of built-in variables for a workspace."""
        run_command(
            command="gtmctl accounts containers workspaces built-in-variables list",
            operation=lambda: (
                validate_workspace_entity_parent(parent),
                validate_page_token(page_token),
                reads.list_built_in_variables(parent, page_token=page_token),
            )[2],
        )

    workspace_app.add_typer(built_in_variables_app, name="built-in-variables")
    register_built_in_variable_mutation_commands(built_in_variables_app)

    @workspace_app.command("get-status")
    def workspace_get_status(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace resource path.")
        ],
    ) -> None:
        """Get official workspace status."""
        run_command(
            command="gtmctl accounts containers workspaces get-status",
            operation=lambda: (
                validate_workspace_path(path),
                reads.get_workspace_status(path),
            )[1],
        )

    for entity in _WORKSPACE_ENTITIES:
        register_workspace_entity_mutation_commands(
            entity_apps[entity.cli_name],
            entity=entity.mutation_entity,
            singular=entity.mutation_singular,
            cli_name=entity.cli_name,
            include_revert=entity.include_revert,
        )
    register_gallery_template_import_command(templates_app)

    @folders_app.command("entities")
    def folders_entities_list(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace folder resource path.")
        ],
        page_token: Annotated[
            str | None,
            typer.Option("--page-token", help="Official continuation token."),
        ] = None,
    ) -> None:
        """List one official page of entities assigned to a workspace folder."""
        run_command(
            command="gtmctl accounts containers workspaces folders entities",
            operation=lambda: (
                validate_workspace_folder_path(path),
                validate_page_token(page_token),
                reads.list_folder_entities(path, page_token=page_token),
            )[2],
        )

    @folders_app.command("move-entities-to-folder")
    def folders_move_entities_to_folder(
        path: Annotated[
            str, typer.Option("--path", help="GTM workspace folder resource path.")
        ],
        body: Annotated[
            str | None,
            typer.Option(
                "--body", help="Optional UTF-8 JSON Folder object file, or - for stdin."
            ),
        ] = None,
        variable_id: Annotated[
            list[str] | None,
            typer.Option(
                "--variable-id", help="Official variable ID to move (repeatable)."
            ),
        ] = None,
        trigger_id: Annotated[
            list[str] | None,
            typer.Option(
                "--trigger-id", help="Official trigger ID to move (repeatable)."
            ),
        ] = None,
        tag_id: Annotated[
            list[str] | None,
            typer.Option("--tag-id", help="Official tag ID to move (repeatable)."),
        ] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run", help=DRY_RUN_HELP)] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Move selected workspace entities into a folder."""

        def operation() -> dict[str, Any]:
            validate_workspace_folder_path(path)
            validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body) if body is not None else None
            if dry_run:
                return build_dry_run_plan(
                    operation="folders.move-entities-to-folder",
                    target=path,
                    body=request_body,
                ) | {
                    "variableId": variable_id,
                    "triggerId": trigger_id,
                    "tagId": tag_id,
                }
            return mutations.move_folder_entities_to_folder(
                path,
                body=request_body,
                variable_ids=variable_id,
                trigger_ids=trigger_id,
                tag_ids=tag_id,
            )

        run_command(
            command="gtmctl accounts containers workspaces folders move-entities-to-folder",
            operation=operation,
        )
