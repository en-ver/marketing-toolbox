"""Child-resource GA4 Admin Typer command families."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Annotated, Any

import typer

from ga4adminctl.foundation.validation import read_json_body
from ga4adminctl.operations.resources import (
    archive_custom_dimension,
    archive_custom_metric,
    create_custom_dimension,
    create_custom_metric,
    create_data_stream,
    create_firebase_link,
    create_google_ads_link,
    create_key_event,
    delete_data_stream,
    delete_firebase_link,
    delete_google_ads_link,
    delete_key_event,
    get_custom_dimension,
    get_custom_metric,
    get_data_stream,
    get_key_event,
    list_custom_dimensions,
    list_custom_metrics,
    list_data_streams,
    list_firebase_links,
    list_google_ads_links,
    list_key_events,
    update_custom_dimension,
    update_custom_metric,
    update_data_stream,
    update_google_ads_link,
    update_key_event,
)

from ._common import (
    require_exactly_one_mutation_mode,
    run_command,
)
from .secrets import measurement_protocol_secrets_app

data_streams_app = typer.Typer(
    help="Manage GA4 data streams through stable Admin API v1beta.",
    no_args_is_help=True,
)
custom_dimensions_app = typer.Typer(
    help="Manage GA4 custom dimensions through stable Admin API v1beta.",
    no_args_is_help=True,
)
custom_metrics_app = typer.Typer(
    help="Manage GA4 custom metrics through stable Admin API v1beta.",
    no_args_is_help=True,
)
firebase_links_app = typer.Typer(
    help="Manage GA4 Firebase links through stable Admin API v1beta.",
    no_args_is_help=True,
)
google_ads_links_app = typer.Typer(
    help="Manage GA4 Google Ads links through stable Admin API v1beta.",
    no_args_is_help=True,
)
key_events_app = typer.Typer(
    help="Manage GA4 key events through stable Admin API v1beta.", no_args_is_help=True
)
data_streams_app.add_typer(
    measurement_protocol_secrets_app, name="measurement-protocol-secrets"
)


def _install_child_commands(
    group: typer.Typer,
    collection_label: str,
    get_operation: Callable[[str], dict[str, Any]] | None,
    list_operation: Callable[..., dict[str, Any]],
) -> None:
    if get_operation is not None:

        @group.command("get", help=f"Get one {collection_label} resource.")
        def get(
            name: Annotated[
                str, typer.Option("--name", help="Canonical child resource name.")
            ],
        ) -> None:
            """Get one dynamically registered property child resource."""
            run_command(
                command=f"ga4adminctl properties {collection_label} get",
                operation=lambda: get_operation(name),
            )

    @group.command("list", help=f"List {collection_label} resources for one property.")
    def list_resources(
        property_name: Annotated[
            str,
            typer.Option(
                "--property", help="Parent property resource name: properties/<id>."
            ),
        ],
        page_size: Annotated[
            int,
            typer.Option(
                "--page-size", help="Maximum resources in this one page (1-200)."
            ),
        ] = 50,
        page_token: Annotated[
            str,
            typer.Option(
                "--page-token", help="Continuation token from a prior list response."
            ),
        ] = "",
    ) -> None:
        """List dynamically registered property child resources for one property."""
        run_command(
            command=f"ga4adminctl properties {collection_label} list",
            operation=lambda: list_operation(
                property_name, page_size=page_size, page_token=page_token
            ),
        )


_install_child_commands(
    data_streams_app, "data-streams", get_data_stream, list_data_streams
)
_install_child_commands(
    custom_dimensions_app,
    "custom-dimensions",
    get_custom_dimension,
    list_custom_dimensions,
)


def _custom_definition_patch(
    *,
    command: str,
    name: str,
    body_source: str,
    update_mask: str,
    dry_run: bool,
    apply: bool,
    operation: Callable[..., dict[str, Any]],
) -> None:
    """Run one safeguarded custom-definition update."""

    def execute() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        return operation(
            name, read_json_body(body_source, stdin=sys.stdin), update_mask, apply=apply
        )

    run_command(command=command, operation=execute)


def _custom_definition_mutation(
    *,
    command: str,
    name: str,
    body_source: str | None,
    dry_run: bool,
    apply: bool,
    operation: Callable[..., dict[str, Any]],
) -> None:
    """Run a create or archive custom-definition operation with explicit apply."""

    def execute() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        if body_source is None:
            return operation(name, apply=apply)
        return operation(
            name, read_json_body(body_source, stdin=sys.stdin), apply=apply
        )

    run_command(command=command, operation=execute)


def _install_custom_definition_lifecycle_commands(
    group: typer.Typer,
    label: str,
    create_operation: Callable[..., dict[str, Any]],
    archive_operation: Callable[..., dict[str, Any]],
) -> None:
    @group.command("create", help=f"Create one {label} resource.")
    def create(
        property_name: Annotated[
            str, typer.Option("--property", help="Parent property resource name.")
        ],
        body_source: Annotated[
            str,
            typer.Option(
                "--body", help="UTF-8 JSON request file, or - for standard input."
            ),
        ],
        dry_run: Annotated[
            bool,
            typer.Option(
                "--dry-run",
                help="Validate and print the request without calling Google.",
            ),
        ] = False,
        apply: Annotated[
            bool,
            typer.Option("--apply", help="Explicitly create this custom definition."),
        ] = False,
    ) -> None:
        """Create one dynamically registered custom-definition resource."""
        _custom_definition_mutation(
            command=f"ga4adminctl properties {label} create",
            name=property_name,
            body_source=body_source,
            dry_run=dry_run,
            apply=apply,
            operation=create_operation,
        )

    @group.command("archive", help=f"Archive one {label} resource.")
    def archive(
        name: Annotated[
            str,
            typer.Option("--name", help="Custom-definition resource name to archive."),
        ],
        dry_run: Annotated[
            bool,
            typer.Option(
                "--dry-run",
                help="Validate and print the request without calling Google.",
            ),
        ] = False,
        apply: Annotated[
            bool,
            typer.Option("--apply", help="Explicitly archive this custom definition."),
        ] = False,
    ) -> None:
        """Archive one dynamically registered custom-definition resource."""
        _custom_definition_mutation(
            command=f"ga4adminctl properties {label} archive",
            name=name,
            body_source=None,
            dry_run=dry_run,
            apply=apply,
            operation=archive_operation,
        )


@custom_dimensions_app.command("patch")
def custom_dimensions_patch(
    name: Annotated[
        str, typer.Option("--name", help="Custom-dimension resource name.")
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
        bool,
        typer.Option("--apply", help="Explicitly apply this custom-dimension update."),
    ] = False,
) -> None:
    """Update bounded custom-dimension fields with explicit apply control."""
    _custom_definition_patch(
        command="ga4adminctl properties custom-dimensions patch",
        name=name,
        body_source=body_source,
        update_mask=update_mask,
        dry_run=dry_run,
        apply=apply,
        operation=update_custom_dimension,
    )


@custom_metrics_app.command("patch")
def custom_metrics_patch(
    name: Annotated[str, typer.Option("--name", help="Custom-metric resource name.")],
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
        bool,
        typer.Option("--apply", help="Explicitly apply this custom-metric update."),
    ] = False,
) -> None:
    """Update bounded custom-metric fields with explicit apply control."""
    _custom_definition_patch(
        command="ga4adminctl properties custom-metrics patch",
        name=name,
        body_source=body_source,
        update_mask=update_mask,
        dry_run=dry_run,
        apply=apply,
        operation=update_custom_metric,
    )


_install_custom_definition_lifecycle_commands(
    custom_dimensions_app,
    "custom-dimensions",
    create_custom_dimension,
    archive_custom_dimension,
)
_install_custom_definition_lifecycle_commands(
    custom_metrics_app, "custom-metrics", create_custom_metric, archive_custom_metric
)


@data_streams_app.command("patch")
def data_streams_patch(
    name: Annotated[str, typer.Option("--name", help="Data-stream resource name.")],
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
        bool, typer.Option("--apply", help="Explicitly apply this data-stream update.")
    ] = False,
) -> None:
    """Update bounded data-stream fields with explicit apply control."""
    _custom_definition_patch(
        command="ga4adminctl properties data-streams patch",
        name=name,
        body_source=body_source,
        update_mask=update_mask,
        dry_run=dry_run,
        apply=apply,
        operation=update_data_stream,
    )


@data_streams_app.command("create")
def data_streams_create(
    property_name: Annotated[
        str, typer.Option("--property", help="Parent property resource name.")
    ],
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
        bool, typer.Option("--apply", help="Explicitly create this data stream.")
    ] = False,
) -> None:
    """Create one bounded Web data stream with explicit apply control."""
    _custom_definition_mutation(
        command="ga4adminctl properties data-streams create",
        name=property_name,
        body_source=body_source,
        dry_run=dry_run,
        apply=apply,
        operation=create_data_stream,
    )


@data_streams_app.command("delete")
def data_streams_delete(
    name: Annotated[
        str, typer.Option("--name", help="Data-stream resource name to delete.")
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly delete this data stream.")
    ] = False,
) -> None:
    """Delete one data stream with explicit apply control; deletion is irreversible."""
    _custom_definition_mutation(
        command="ga4adminctl properties data-streams delete",
        name=name,
        body_source=None,
        dry_run=dry_run,
        apply=apply,
        operation=delete_data_stream,
    )


@firebase_links_app.command("create")
def firebase_links_create(
    property_name: Annotated[
        str, typer.Option("--property", help="Parent property resource name.")
    ],
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
        bool, typer.Option("--apply", help="Explicitly create this Firebase link.")
    ] = False,
) -> None:
    """Create one Firebase link with explicit apply control."""
    _custom_definition_mutation(
        command="ga4adminctl properties firebase-links create",
        name=property_name,
        body_source=body_source,
        dry_run=dry_run,
        apply=apply,
        operation=create_firebase_link,
    )


@firebase_links_app.command("delete")
def firebase_links_delete(
    name: Annotated[
        str, typer.Option("--name", help="Firebase link resource name to delete.")
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly delete this Firebase link.")
    ] = False,
) -> None:
    """Delete one Firebase link with explicit apply control; deletion is irreversible."""
    _custom_definition_mutation(
        command="ga4adminctl properties firebase-links delete",
        name=name,
        body_source=None,
        dry_run=dry_run,
        apply=apply,
        operation=delete_firebase_link,
    )


@google_ads_links_app.command("patch")
def google_ads_links_patch(
    name: Annotated[str, typer.Option("--name", help="Google Ads link resource name.")],
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
        bool,
        typer.Option("--apply", help="Explicitly apply this Google Ads link update."),
    ] = False,
) -> None:
    """Update Google Ads link personalization with explicit apply control."""
    _custom_definition_patch(
        command="ga4adminctl properties google-ads-links patch",
        name=name,
        body_source=body_source,
        update_mask=update_mask,
        dry_run=dry_run,
        apply=apply,
        operation=update_google_ads_link,
    )


@google_ads_links_app.command("create")
def google_ads_links_create(
    property_name: Annotated[
        str, typer.Option("--property", help="Parent property resource name.")
    ],
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
        bool, typer.Option("--apply", help="Explicitly create this Google Ads link.")
    ] = False,
) -> None:
    """Create one Google Ads link with explicit apply control."""
    _custom_definition_mutation(
        command="ga4adminctl properties google-ads-links create",
        name=property_name,
        body_source=body_source,
        dry_run=dry_run,
        apply=apply,
        operation=create_google_ads_link,
    )


@google_ads_links_app.command("delete")
def google_ads_links_delete(
    name: Annotated[
        str, typer.Option("--name", help="Google Ads link resource name to delete.")
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly delete this Google Ads link.")
    ] = False,
) -> None:
    """Delete one Google Ads link with explicit apply control; deletion is irreversible."""
    _custom_definition_mutation(
        command="ga4adminctl properties google-ads-links delete",
        name=name,
        body_source=None,
        dry_run=dry_run,
        apply=apply,
        operation=delete_google_ads_link,
    )


@key_events_app.command("patch")
def key_events_patch(
    name: Annotated[str, typer.Option("--name", help="Key-event resource name.")],
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
        bool, typer.Option("--apply", help="Explicitly apply this key-event update.")
    ] = False,
) -> None:
    """Update bounded KeyEvent settings with explicit apply control."""
    _custom_definition_patch(
        command="ga4adminctl properties key-events patch",
        name=name,
        body_source=body_source,
        update_mask=update_mask,
        dry_run=dry_run,
        apply=apply,
        operation=update_key_event,
    )


@key_events_app.command("create")
def key_events_create(
    property_name: Annotated[
        str, typer.Option("--property", help="Parent property resource name.")
    ],
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
        bool, typer.Option("--apply", help="Explicitly create this key event.")
    ] = False,
) -> None:
    """Create one KeyEvent with explicit apply control."""
    _custom_definition_mutation(
        command="ga4adminctl properties key-events create",
        name=property_name,
        body_source=body_source,
        dry_run=dry_run,
        apply=apply,
        operation=create_key_event,
    )


@key_events_app.command("delete")
def key_events_delete(
    name: Annotated[
        str, typer.Option("--name", help="Key-event resource name to delete.")
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly delete this key event.")
    ] = False,
) -> None:
    """Delete one KeyEvent with explicit apply control; deletion is irreversible."""
    _custom_definition_mutation(
        command="ga4adminctl properties key-events delete",
        name=name,
        body_source=None,
        dry_run=dry_run,
        apply=apply,
        operation=delete_key_event,
    )


_install_child_commands(
    custom_metrics_app, "custom-metrics", get_custom_metric, list_custom_metrics
)
_install_child_commands(firebase_links_app, "firebase-links", None, list_firebase_links)
_install_child_commands(
    google_ads_links_app, "google-ads-links", None, list_google_ads_links
)
_install_child_commands(key_events_app, "key-events", get_key_event, list_key_events)
