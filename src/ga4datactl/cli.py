"""CLI entry point for Google Analytics Data API operations."""

from __future__ import annotations

from typing import Annotated

import typer

from ga4datactl import __version__
from ga4datactl.commands import audience_exports, metadata, reports, sdk
from ga4datactl.service import (
    batch_run_pivot_reports,
    batch_run_reports,
    check_compatibility,
    create_audience_export,
    get_audience_export,
    get_metadata,
    list_audience_exports,
    query_audience_export,
    run_pivot_report,
    run_realtime_report,
    run_report,
)
from marketing_common.cli import make_version_callback, run_typer_application

# Static operation re-exports preserve established direct imports from this root.
__all__ = [
    "app",
    "batch_run_pivot_reports",
    "batch_run_reports",
    "check_compatibility",
    "create_audience_export",
    "get_audience_export",
    "get_metadata",
    "list_audience_exports",
    "main",
    "query_audience_export",
    "root_callback",
    "run_pivot_report",
    "run_realtime_report",
    "run_report",
]

app = typer.Typer(
    name="ga4datactl",
    help="Query Google Analytics 4 reporting data through the official Data API client.",
    no_args_is_help=True,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)
app.add_typer(reports.app, name="reports")
app.add_typer(metadata.app, name="metadata")
app.add_typer(audience_exports.app, name="audience-exports")
app.add_typer(sdk.app, name="sdk")

_version_callback = make_version_callback("ga4datactl", __version__)


@app.callback()
def root_callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            help="Show the installed version.",
            is_eager=True,
        ),
    ] = None,
) -> None:
    """A CLI façade for the official Google Analytics Data API Python client."""


def main() -> None:
    """Run the installed ga4datactl console command."""
    run_typer_application(app, command="ga4datactl")
