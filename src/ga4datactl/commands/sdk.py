"""Local official-SDK request descriptor discovery for GA4 Data CLI leaves."""

from __future__ import annotations

from typing import Annotated

import typer
from google.analytics.data_v1beta.types import (
    AudienceExport,
    BatchRunPivotReportsRequest,
    BatchRunReportsRequest,
    CheckCompatibilityRequest,
    CreateAudienceExportRequest,
    RunPivotReportRequest,
    RunRealtimeReportRequest,
    RunReportRequest,
)

from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.introspection import (
    ProtobufSchemaTarget,
    protobuf_schema_response,
    resolve_schema_target,
)

app = typer.Typer(
    help="Inspect locally installed official GA4 Data SDK request descriptors.",
    no_args_is_help=True,
)

_SCHEMA_TARGETS: dict[tuple[str, ...], ProtobufSchemaTarget] = {
    ("reports", "run"): ProtobufSchemaTarget(
        cli_path=("reports", "run"),
        official_method="analyticsdata.properties.runReport",
        request_type=RunReportRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    ("reports", "batch-run"): ProtobufSchemaTarget(
        cli_path=("reports", "batch-run"),
        official_method="analyticsdata.properties.batchRunReports",
        request_type=BatchRunReportsRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    ("reports", "pivot-run"): ProtobufSchemaTarget(
        cli_path=("reports", "pivot-run"),
        official_method="analyticsdata.properties.runPivotReport",
        request_type=RunPivotReportRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    ("reports", "realtime-run"): ProtobufSchemaTarget(
        cli_path=("reports", "realtime-run"),
        official_method="analyticsdata.properties.runRealtimeReport",
        request_type=RunRealtimeReportRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    ("reports", "batch-pivot-run"): ProtobufSchemaTarget(
        cli_path=("reports", "batch-pivot-run"),
        official_method="analyticsdata.properties.batchRunPivotReports",
        request_type=BatchRunPivotReportsRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    ("reports", "compatibility-check"): ProtobufSchemaTarget(
        cli_path=("reports", "compatibility-check"),
        official_method="analyticsdata.properties.checkCompatibility",
        request_type=CheckCompatibilityRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    ("audience-exports", "create"): ProtobufSchemaTarget(
        cli_path=("audience-exports", "create"),
        official_method="analyticsdata.properties.audienceExports.create",
        request_type=CreateAudienceExportRequest,
        body_type=AudienceExport,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent", "audienceExport"),
    ),
}


@app.command("schema")
def schema(
    command: Annotated[
        str,
        typer.Option(
            "--command",
            help="Exact existing leaf path, excluding ga4datactl; for example: reports run.",
        ),
    ],
) -> None:
    """Return an installed official SDK descriptor without credentials or network."""
    target = resolve_schema_target(command=command, targets=_SCHEMA_TARGETS)
    if target is None:
        exit_with_diagnostic(
            exit_code=2,
            category="invalid_arguments",
            message="--command must name an eligible registered ga4datactl leaf.",
            command="ga4datactl sdk schema",
        )
    write_success(
        command="ga4datactl sdk schema",
        data=protobuf_schema_response(
            target=target,
            package="google-analytics-data",
            api_version="v1beta",
        ),
    )
