"""Guarded GTM Gallery template import command registration."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from gtmctl.commands._common import run_command
from gtmctl.commands.tag_mutations import _dry_run, _validate_execution_mode
from gtmctl.foundation.body import read_json_object
from gtmctl.foundation.validation import (
    RequestValidationError,
    validate_workspace_entity_parent,
)
from gtmctl.operations import mutations

_GALLERY_QUERY_FIELDS = frozenset({"galleryOwner", "gallerySha", "galleryRepository"})


def _gallery_query_parameters(body: dict[str, Any]) -> dict[str, str | None]:
    """Validate and extract the documented Gallery import query parameters."""
    unsupported = set(body) - _GALLERY_QUERY_FIELDS
    if unsupported:
        fields = ", ".join(sorted(unsupported))
        raise RequestValidationError(
            f"--body contains unsupported Gallery import field(s): {fields}."
        )
    query: dict[str, str | None] = {}
    for field in _GALLERY_QUERY_FIELDS:
        value = body.get(field)
        if value is not None and not isinstance(value, str):
            raise RequestValidationError(f"--body field {field} must be a string.")
        query[field] = value
    return query


def register_gallery_template_import_command(templates_app: typer.Typer) -> None:
    """Add the permission-acknowledged Gallery custom-template import."""

    @templates_app.command("import-from-gallery")
    def templates_import_from_gallery(
        parent: Annotated[
            str, typer.Option("--parent", help="GTM workspace resource path.")
        ],
        body: Annotated[
            str,
            typer.Option(
                "--body",
                help=(
                    "UTF-8 JSON object with official galleryOwner, gallerySha, and "
                    "galleryRepository query fields; use - for stdin."
                ),
            ),
        ],
        acknowledge_template_import_permissions: Annotated[
            bool,
            typer.Option(
                "--acknowledge-template-import-permissions",
                help="Acknowledge granting the imported Gallery template's declared permissions.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print an import plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Import the Gallery template.")
        ] = False,
    ) -> None:
        """Import one Gallery custom template after acknowledging its permissions."""

        def operation() -> dict[str, Any]:
            validate_workspace_entity_parent(parent)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            request_body = read_json_object(body)
            query = _gallery_query_parameters(request_body)
            if not acknowledge_template_import_permissions:
                raise RequestValidationError(
                    "--acknowledge-template-import-permissions is required before "
                    "importing a Gallery template."
                )
            if dry_run:
                return _dry_run(
                    operation="templates.import-from-gallery",
                    target=parent,
                    body=request_body,
                ) | {"permissionsAcknowledged": True}
            return mutations.import_template_from_gallery(
                parent,
                gallery_owner=query["galleryOwner"],
                gallery_sha=query["gallerySha"],
                gallery_repository=query["galleryRepository"],
                acknowledge_permissions=True,
            )

        run_command(
            command="gtmctl accounts containers workspaces templates import-from-gallery",
            operation=operation,
        )
