"""GA4 reporting command family."""

from __future__ import annotations

from typing import Annotated

import typer

from ga4datactl.commands._common import run_report_command
from ga4datactl.operations.reports import (
    batch_run_pivot_reports,
    batch_run_reports,
    check_compatibility,
    run_pivot_report,
    run_realtime_report,
    run_report,
)

app = typer.Typer(help="Run GA4 reporting operations.", no_args_is_help=True)


@app.command("run")
def reports_run(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body",
            help="Opaque official GA4 Data API request JSON file, or - for standard input.",
        ),
    ],
) -> None:
    """Run one standard GA4 core report.

    Pass an opaque official RunReportRequest JSON body without `property`.
    See the official GA4 Data API/SDK documentation. One response page is
    returned; use its `rowCount`, request `offset`, and request `limit` to page.
    """
    run_report_command(
        command="ga4datactl reports run",
        property_name=property_name,
        body_source=body_source,
        operation=run_report,
    )


@app.command("batch-run")
def batch_report(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body",
            help="Opaque official GA4 Data API request JSON file, or - for standard input.",
        ),
    ],
) -> None:
    """Run up to five standard GA4 reports in one API request.

    Pass an opaque official BatchRunReportsRequest JSON body. Every nested
    request uses the top-level `--property`; nested `property` fields are rejected.
    See the official GA4 Data API/SDK documentation for request fields.
    """
    run_report_command(
        command="ga4datactl reports batch-run",
        property_name=property_name,
        body_source=body_source,
        operation=batch_run_reports,
    )


@app.command("pivot-run")
def pivot_report(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body",
            help="Opaque official GA4 Data API request JSON file, or - for standard input.",
        ),
    ],
) -> None:
    """Run one GA4 pivot report.

    Pass an opaque official RunPivotReportRequest JSON body without `property`.
    See the official GA4 Data API/SDK documentation; pivot pagination uses each
    pivot's `offset`.
    """
    run_report_command(
        command="ga4datactl reports pivot-run",
        property_name=property_name,
        body_source=body_source,
        operation=run_pivot_report,
    )


@app.command("realtime-run")
def realtime_report(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body",
            help="Opaque official GA4 Data API request JSON file, or - for standard input.",
        ),
    ],
) -> None:
    """Run one GA4 realtime report for the last 30 (or GA360 60) minutes.

    Pass an opaque official RunRealtimeReportRequest JSON body without
    `property`. See the official GA4 Data API/SDK documentation; use up to two
    `minuteRanges` to select realtime windows.
    """
    run_report_command(
        command="ga4datactl reports realtime-run",
        property_name=property_name,
        body_source=body_source,
        operation=run_realtime_report,
    )


@app.command("batch-pivot-run")
def batch_pivot_report(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body",
            help="Opaque official GA4 Data API request JSON file, or - for standard input.",
        ),
    ],
) -> None:
    """Run up to five GA4 pivot reports in one API request.

    Pass an opaque official BatchRunPivotReportsRequest JSON body. Every nested
    request uses the top-level `--property`; nested `property` fields are rejected.
    See the official GA4 Data API/SDK documentation for request fields.
    """
    run_report_command(
        command="ga4datactl reports batch-pivot-run",
        property_name=property_name,
        body_source=body_source,
        operation=batch_run_pivot_reports,
    )


@app.command("compatibility-check")
def reports_compatibility_check(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body",
            help="Opaque official GA4 Data API request JSON file, or - for standard input.",
        ),
    ],
) -> None:
    """Check whether candidate core-report dimensions and metrics are compatible.

    Pass an opaque official CheckCompatibilityRequest JSON body without
    `property`; `--property` selects the GA4 property. See the official GA4
    Data API/SDK documentation for request fields.
    """
    run_report_command(
        command="ga4datactl reports compatibility-check",
        property_name=property_name,
        body_source=body_source,
        operation=check_compatibility,
    )
