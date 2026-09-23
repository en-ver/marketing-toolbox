"""GA4 audience-export command family."""

from __future__ import annotations

import sys
from typing import Annotated, Any

import typer

from ga4datactl.commands._common import run_command
from ga4datactl.foundation.validation import RequestValidationError, read_json_body
from ga4datactl.operations.audience_exports import (
    create_audience_export,
    get_audience_export,
    list_audience_exports,
    query_audience_export,
)
from ga4datactl.schemas import CREATE_AUDIENCE_EXPORT_BODY_SCHEMA
from marketing_common.cli import make_schema_callback

app = typer.Typer(
    help="Discover existing GA4 audience-export metadata.", no_args_is_help=True
)
_create_audience_export_schema_callback = make_schema_callback(
    "ga4datactl audience-exports create", CREATE_AUDIENCE_EXPORT_BODY_SCHEMA
)


def _run_audience_export_create_command(
    *, property_name: str, body_source: str, dry_run: bool, apply: bool
) -> None:
    """Validate and either plan or explicitly initiate one export create."""
    command = "ga4datactl audience-exports create"

    def create_with_body() -> dict[str, Any]:
        if dry_run == apply:
            raise RequestValidationError(
                "Specify exactly one of --dry-run or --apply for this mutation."
            )
        body = read_json_body(body_source, stdin=sys.stdin)
        return create_audience_export(property_name, body, apply=apply)

    run_command(command=command, operation=create_with_body)


@app.command("get")
def audience_exports_get(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    name: Annotated[
        str,
        typer.Option(
            "--name",
            help="Audience export name: properties/<id>/audienceExports/<id>.",
        ),
    ],
) -> None:
    """Return sensitive audience-export metadata for one property-scoped export."""
    run_command(
        command="ga4datactl audience-exports get",
        operation=lambda: get_audience_export(property_name, name),
    )


@app.command("list")
def audience_exports_list(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    page_size: Annotated[
        int,
        typer.Option("--page-size", help="Required maximum results for this one page."),
    ],
    page_token: Annotated[
        str | None,
        typer.Option("--page-token", help="Token from a prior list response."),
    ] = None,
) -> None:
    """Return one explicit audience-export metadata page without auto-pagination."""
    run_command(
        command="ga4datactl audience-exports list",
        operation=lambda: list_audience_exports(property_name, page_size, page_token),
    )


@app.command("create")
def audience_exports_create(
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
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Validate and print the create request without calling Google.",
        ),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option(
            "--apply",
            help="Explicitly initiate the Google audience-export creation operation.",
        ),
    ] = False,
    schema: Annotated[
        bool | None,
        typer.Option(
            "--schema",
            callback=_create_audience_export_schema_callback,
            help="Write the exact code-bundled request JSON Schema and exit.",
            is_eager=True,
        ),
    ] = None,
) -> None:
    """Plan or explicitly initiate a GA4 audience export; never poll it.

    Use `--dry-run` to validate and inspect the request. `--apply` is required
    to call Google and returns only the initiated operation name.
    """
    _run_audience_export_create_command(
        property_name=property_name,
        body_source=body_source,
        dry_run=dry_run,
        apply=apply,
    )


@app.command("query")
def audience_exports_query(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    name: Annotated[
        str,
        typer.Option(
            "--name",
            help="Audience export name: properties/<id>/audienceExports/<id>.",
        ),
    ],
    limit: Annotated[
        int,
        typer.Option("--limit", help="Required user-row count, from 1 through 1000."),
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Required acknowledgement that this returns sensitive user-row data.",
        ),
    ],
    offset: Annotated[
        int,
        typer.Option("--offset", help="Zero-based row offset for this one request."),
    ] = 0,
) -> None:
    """Return one explicitly bounded page of sensitive audience-export user rows.

    No pagination, persistence, logging, redaction, or transformation is
    performed. Supply --acknowledge-sensitive-data for every query.
    """
    del acknowledge_sensitive_data
    run_command(
        command="ga4datactl audience-exports query",
        operation=lambda: query_audience_export(property_name, name, limit, offset),
    )
