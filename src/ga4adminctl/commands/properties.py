"""Core property-side GA4 Admin Typer command families and attachment points."""

from __future__ import annotations

import sys
from typing import Annotated, Any

import typer

from ga4adminctl.foundation.validation import (
    PROPERTY_PATTERN,
    read_json_body,
)
from ga4adminctl.operations.properties import (
    acknowledge_user_data_collection,
    create_property,
    delete_property,
    get_data_retention_settings,
    get_property,
    list_properties,
    update_data_retention_settings,
    update_property,
)

from ._common import (
    require_exactly_one_mutation_mode,
    require_sensitive_acknowledgement,
    run_access_report_command,
    run_command,
)

properties_app = typer.Typer(
    help="Manage GA4 Properties through stable Admin API v1beta.", no_args_is_help=True
)
data_retention_settings_app = typer.Typer(
    help="Manage property data-retention settings through stable Admin API v1beta.",
    no_args_is_help=True,
)
property_access_reports_app = typer.Typer(
    help="Run acknowledged, sensitive property access reports through stable Admin API v1beta.",
    no_args_is_help=True,
)
from .resources import (
    custom_dimensions_app,
    custom_metrics_app,
    data_streams_app,
    firebase_links_app,
    google_ads_links_app,
    key_events_app,
)

properties_app.add_typer(data_retention_settings_app, name="data-retention-settings")
properties_app.add_typer(property_access_reports_app, name="access-reports")
properties_app.add_typer(data_streams_app, name="data-streams")
properties_app.add_typer(custom_dimensions_app, name="custom-dimensions")
properties_app.add_typer(custom_metrics_app, name="custom-metrics")
properties_app.add_typer(firebase_links_app, name="firebase-links")
properties_app.add_typer(google_ads_links_app, name="google-ads-links")
properties_app.add_typer(key_events_app, name="key-events")


@properties_app.command("get")
def properties_get(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
) -> None:
    """Get one GA4 Property through stable Admin API v1beta."""
    run_command(
        command="ga4adminctl properties get",
        operation=lambda: get_property(property_name),
    )


@properties_app.command("list")
def properties_list(
    filter_expression: Annotated[
        str,
        typer.Option(
            "--filter", help="Official account or Firebase project property filter."
        ),
    ],
    page_size: Annotated[
        int,
        typer.Option(
            "--page-size", help="Maximum properties in this one page (1-200)."
        ),
    ] = 50,
    page_token: Annotated[
        str,
        typer.Option(
            "--page-token", help="Continuation token from a prior list response."
        ),
    ] = "",
    show_deleted: Annotated[
        bool, typer.Option("--show-deleted", help="Include soft-deleted properties.")
    ] = False,
) -> None:
    """Return exactly one bounded GA4 Property page; never auto-paginate."""
    run_command(
        command="ga4adminctl properties list",
        operation=lambda: list_properties(
            filter_expression,
            page_size=page_size,
            page_token=page_token,
            show_deleted=show_deleted,
        ),
    )


@properties_app.command("patch")
def properties_patch(
    name: Annotated[str, typer.Option("--name", help="Property resource name.")],
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    update_mask: Annotated[
        str,
        typer.Option(
            "--update-mask", help="Comma-separated mutable body fields to update."
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly apply this Property update.")
    ] = False,
) -> None:
    """Update bounded Property fields with explicit apply control."""

    def operation() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        return update_property(
            name,
            read_json_body(body_source, stdin=sys.stdin),
            update_mask,
            apply=apply,
        )

    run_command(command="ga4adminctl properties patch", operation=operation)


@properties_app.command("create")
def properties_create(
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly create this Property.")
    ] = False,
) -> None:
    """Create one bounded Property with explicit apply control."""

    def operation() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        return create_property(
            read_json_body(body_source, stdin=sys.stdin), apply=apply
        )

    run_command(command="ga4adminctl properties create", operation=operation)


@properties_app.command("delete")
def properties_delete(
    name: Annotated[
        str, typer.Option("--name", help="Property resource name to delete.")
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly delete this Property.")
    ] = False,
) -> None:
    """Delete one Property with explicit apply control; deletion is irreversible."""

    def operation() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        return delete_property(name, apply=apply)

    run_command(command="ga4adminctl properties delete", operation=operation)


@properties_app.command("acknowledge-user-data-collection")
def properties_acknowledge_user_data_collection(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this confirms user-data collection privacy terms.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Explicitly acknowledge user-data collection."),
    ] = False,
) -> None:
    """Acknowledge user-data collection terms with explicit sensitive controls."""

    def operation() -> dict[str, Any]:
        require_sensitive_acknowledgement(acknowledge_sensitive_data)
        require_exactly_one_mutation_mode(dry_run, apply)
        return acknowledge_user_data_collection(
            property_name,
            read_json_body(body_source, stdin=sys.stdin),
            apply=apply,
        )

    run_command(
        command="ga4adminctl properties acknowledge-user-data-collection",
        operation=operation,
    )


@data_retention_settings_app.command("get")
def properties_data_retention_settings_get(
    name: Annotated[
        str, typer.Option("--name", help="Data-retention settings resource name.")
    ],
) -> None:
    """Get one property's data-retention settings."""
    run_command(
        command="ga4adminctl properties data-retention-settings get",
        operation=lambda: get_data_retention_settings(name),
    )


@data_retention_settings_app.command("update")
def properties_data_retention_settings_update(
    name: Annotated[
        str, typer.Option("--name", help="Data-retention settings resource name.")
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    update_mask: Annotated[
        str,
        typer.Option(
            "--update-mask",
            help="Comma-separated mutable body fields to update.",
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option(
            "--apply", help="Explicitly apply this retention settings update."
        ),
    ] = False,
) -> None:
    """Update bounded property retention settings with explicit apply control."""

    def operation() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        return update_data_retention_settings(
            name,
            read_json_body(body_source, stdin=sys.stdin),
            update_mask,
            apply=apply,
        )

    run_command(
        command="ga4adminctl properties data-retention-settings update",
        operation=operation,
    )


@property_access_reports_app.command("run")
def properties_access_reports_run(
    entity: Annotated[
        str, typer.Option("--entity", help="Property resource name: properties/<id>.")
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this response can contain access and audit data.",
        ),
    ] = False,
) -> None:
    """Run one sensitive, read-only property access report."""
    run_command(
        command="ga4adminctl properties access-reports run",
        operation=lambda: run_access_report_command(
            entity=entity,
            body_source=body_source,
            acknowledge_sensitive_data=acknowledge_sensitive_data,
            entity_pattern=PROPERTY_PATTERN,
        ),
    )
