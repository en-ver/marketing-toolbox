"""Local official-SDK request descriptor discovery for GA4 Admin CLI leaves."""

from __future__ import annotations

from typing import Annotated

import typer
from google.analytics.admin_v1beta.types import (
    Account,
    AcknowledgeUserDataCollectionRequest,
    CreateCustomDimensionRequest,
    CreateCustomMetricRequest,
    CreateDataStreamRequest,
    CreateFirebaseLinkRequest,
    CreateGoogleAdsLinkRequest,
    CreateKeyEventRequest,
    CreateMeasurementProtocolSecretRequest,
    CreatePropertyRequest,
    CustomDimension,
    CustomMetric,
    DataRetentionSettings,
    DataStream,
    FirebaseLink,
    GoogleAdsLink,
    KeyEvent,
    MeasurementProtocolSecret,
    Property,
    ProvisionAccountTicketRequest,
    RunAccessReportRequest,
    SearchChangeHistoryEventsRequest,
    UpdateAccountRequest,
    UpdateCustomDimensionRequest,
    UpdateCustomMetricRequest,
    UpdateDataRetentionSettingsRequest,
    UpdateDataStreamRequest,
    UpdateGoogleAdsLinkRequest,
    UpdateKeyEventRequest,
    UpdateMeasurementProtocolSecretRequest,
    UpdatePropertyRequest,
)

from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.introspection import (
    ProtobufSchemaTarget,
    protobuf_schema_response,
    resolve_schema_target,
)

app = typer.Typer(
    help="Inspect locally installed official GA4 Admin SDK request descriptors.",
    no_args_is_help=True,
)


def _target(
    path: tuple[str, ...],
    method: str,
    request_type: type[object],
    *,
    body_type: type[object] | None = None,
    path_or_query_fields: tuple[str, ...] = (),
    body_forbidden_fields: tuple[str, ...] = (),
) -> ProtobufSchemaTarget:
    return ProtobufSchemaTarget(
        cli_path=path,
        official_method=method,
        request_type=request_type,
        body_type=body_type,
        path_or_query_fields=path_or_query_fields,
        body_forbidden_fields=body_forbidden_fields,
    )


_SCHEMA_TARGETS: dict[tuple[str, ...], ProtobufSchemaTarget] = {
    ("accounts", "patch"): _target(
        ("accounts", "patch"),
        "analyticsadmin.accounts.patch",
        UpdateAccountRequest,
        body_type=Account,
        path_or_query_fields=("account.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("accounts", "provision-account-ticket"): _target(
        ("accounts", "provision-account-ticket"),
        "analyticsadmin.accounts.provisionAccountTicket",
        ProvisionAccountTicketRequest,
    ),
    ("accounts", "access-reports", "run"): _target(
        ("accounts", "access-reports", "run"),
        "analyticsadmin.accounts.runAccessReport",
        RunAccessReportRequest,
        path_or_query_fields=("entity",),
        body_forbidden_fields=("entity",),
    ),
    ("accounts", "change-history", "search"): _target(
        ("accounts", "change-history", "search"),
        "analyticsadmin.accounts.searchChangeHistoryEvents",
        SearchChangeHistoryEventsRequest,
        path_or_query_fields=("account",),
        body_forbidden_fields=("account",),
    ),
    ("properties", "acknowledge-user-data-collection"): _target(
        ("properties", "acknowledge-user-data-collection"),
        "analyticsadmin.properties.acknowledgeUserDataCollection",
        AcknowledgeUserDataCollectionRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    ("properties", "create"): _target(
        ("properties", "create"),
        "analyticsadmin.properties.create",
        CreatePropertyRequest,
        body_type=Property,
    ),
    ("properties", "patch"): _target(
        ("properties", "patch"),
        "analyticsadmin.properties.patch",
        UpdatePropertyRequest,
        body_type=Property,
        path_or_query_fields=("property.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("properties", "access-reports", "run"): _target(
        ("properties", "access-reports", "run"),
        "analyticsadmin.properties.runAccessReport",
        RunAccessReportRequest,
        path_or_query_fields=("entity",),
        body_forbidden_fields=("entity",),
    ),
    ("properties", "data-retention-settings", "update"): _target(
        ("properties", "data-retention-settings", "update"),
        "analyticsadmin.properties.updateDataRetentionSettings",
        UpdateDataRetentionSettingsRequest,
        body_type=DataRetentionSettings,
        path_or_query_fields=("dataRetentionSettings.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("properties", "custom-dimensions", "create"): _target(
        ("properties", "custom-dimensions", "create"),
        "analyticsadmin.properties.customDimensions.create",
        CreateCustomDimensionRequest,
        body_type=CustomDimension,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    ("properties", "custom-dimensions", "patch"): _target(
        ("properties", "custom-dimensions", "patch"),
        "analyticsadmin.properties.customDimensions.patch",
        UpdateCustomDimensionRequest,
        body_type=CustomDimension,
        path_or_query_fields=("customDimension.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("properties", "custom-metrics", "create"): _target(
        ("properties", "custom-metrics", "create"),
        "analyticsadmin.properties.customMetrics.create",
        CreateCustomMetricRequest,
        body_type=CustomMetric,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    ("properties", "custom-metrics", "patch"): _target(
        ("properties", "custom-metrics", "patch"),
        "analyticsadmin.properties.customMetrics.patch",
        UpdateCustomMetricRequest,
        body_type=CustomMetric,
        path_or_query_fields=("customMetric.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("properties", "data-streams", "create"): _target(
        ("properties", "data-streams", "create"),
        "analyticsadmin.properties.dataStreams.create",
        CreateDataStreamRequest,
        body_type=DataStream,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    ("properties", "data-streams", "patch"): _target(
        ("properties", "data-streams", "patch"),
        "analyticsadmin.properties.dataStreams.patch",
        UpdateDataStreamRequest,
        body_type=DataStream,
        path_or_query_fields=("dataStream.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("properties", "data-streams", "measurement-protocol-secrets", "create"): _target(
        ("properties", "data-streams", "measurement-protocol-secrets", "create"),
        "analyticsadmin.properties.dataStreams.measurementProtocolSecrets.create",
        CreateMeasurementProtocolSecretRequest,
        body_type=MeasurementProtocolSecret,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent", "secretValue"),
    ),
    ("properties", "data-streams", "measurement-protocol-secrets", "patch"): _target(
        ("properties", "data-streams", "measurement-protocol-secrets", "patch"),
        "analyticsadmin.properties.dataStreams.measurementProtocolSecrets.patch",
        UpdateMeasurementProtocolSecretRequest,
        body_type=MeasurementProtocolSecret,
        path_or_query_fields=("measurementProtocolSecret.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("properties", "firebase-links", "create"): _target(
        ("properties", "firebase-links", "create"),
        "analyticsadmin.properties.firebaseLinks.create",
        CreateFirebaseLinkRequest,
        body_type=FirebaseLink,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    ("properties", "google-ads-links", "create"): _target(
        ("properties", "google-ads-links", "create"),
        "analyticsadmin.properties.googleAdsLinks.create",
        CreateGoogleAdsLinkRequest,
        body_type=GoogleAdsLink,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    ("properties", "google-ads-links", "patch"): _target(
        ("properties", "google-ads-links", "patch"),
        "analyticsadmin.properties.googleAdsLinks.patch",
        UpdateGoogleAdsLinkRequest,
        body_type=GoogleAdsLink,
        path_or_query_fields=("googleAdsLink.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    ("properties", "key-events", "create"): _target(
        ("properties", "key-events", "create"),
        "analyticsadmin.properties.keyEvents.create",
        CreateKeyEventRequest,
        body_type=KeyEvent,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    ("properties", "key-events", "patch"): _target(
        ("properties", "key-events", "patch"),
        "analyticsadmin.properties.keyEvents.patch",
        UpdateKeyEventRequest,
        body_type=KeyEvent,
        path_or_query_fields=("keyEvent.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
}


@app.command("schema")
def schema(
    command: Annotated[
        str,
        typer.Option(
            "--command",
            help="Exact existing leaf path, excluding ga4adminctl; for example: properties create.",
        ),
    ],
) -> None:
    """Return an installed official SDK descriptor without credentials or network."""
    target = resolve_schema_target(command=command, targets=_SCHEMA_TARGETS)
    if target is None:
        exit_with_diagnostic(
            exit_code=2,
            category="invalid_arguments",
            message="--command must name an eligible registered ga4adminctl leaf.",
            command="ga4adminctl sdk schema",
        )
    write_success(
        command="ga4adminctl sdk schema",
        data=protobuf_schema_response(
            target=target,
            package="google-analytics-admin",
            api_version="v1beta",
        ),
    )
