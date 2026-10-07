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

from ga4adminctl.operations.accounts import ACCOUNT_PATCH_WRITABLE_FIELDS
from ga4adminctl.operations.properties import PROPERTY_PATCH_WRITABLE_FIELDS
from ga4adminctl.operations.resources import (
    CUSTOM_DIMENSION_PATCH_WRITABLE_FIELDS,
    CUSTOM_METRIC_PATCH_WRITABLE_FIELDS,
    DATA_STREAM_PATCH_WRITABLE_FIELDS,
    GOOGLE_ADS_LINK_PATCH_WRITABLE_FIELDS,
    KEY_EVENT_PATCH_WRITABLE_FIELDS,
)
from ga4adminctl.operations.secrets import (
    MEASUREMENT_PROTOCOL_SECRET_PATCH_WRITABLE_FIELDS,
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
    writable_fields: tuple[str, ...] | None = None,
) -> ProtobufSchemaTarget:
    return ProtobufSchemaTarget(
        cli_path=path,
        official_method=method,
        request_type=request_type,
        body_type=body_type,
        path_or_query_fields=path_or_query_fields,
        body_forbidden_fields=body_forbidden_fields,
        request_cli_constraints=(
            {
                "allowedUpdateMaskFields": list(writable_fields),
                "bodyFieldsMustExactlyMatchUpdateMask": True,
            }
            if writable_fields is not None
            else None
        ),
    )


_SCHEMA_TARGET_DECLARATIONS: tuple[ProtobufSchemaTarget, ...] = (
    _target(
        ("accounts", "patch"),
        "analyticsadmin.accounts.patch",
        UpdateAccountRequest,
        body_type=Account,
        path_or_query_fields=("account.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=ACCOUNT_PATCH_WRITABLE_FIELDS,
    ),
    _target(
        ("accounts", "provision-account-ticket"),
        "analyticsadmin.accounts.provisionAccountTicket",
        ProvisionAccountTicketRequest,
    ),
    _target(
        ("accounts", "access-reports", "run"),
        "analyticsadmin.accounts.runAccessReport",
        RunAccessReportRequest,
        path_or_query_fields=("entity",),
        body_forbidden_fields=("entity",),
    ),
    _target(
        ("accounts", "change-history", "search"),
        "analyticsadmin.accounts.searchChangeHistoryEvents",
        SearchChangeHistoryEventsRequest,
        path_or_query_fields=("account",),
        body_forbidden_fields=("account",),
    ),
    _target(
        ("properties", "acknowledge-user-data-collection"),
        "analyticsadmin.properties.acknowledgeUserDataCollection",
        AcknowledgeUserDataCollectionRequest,
        path_or_query_fields=("property",),
        body_forbidden_fields=("property",),
    ),
    _target(
        ("properties", "create"),
        "analyticsadmin.properties.create",
        CreatePropertyRequest,
        body_type=Property,
    ),
    _target(
        ("properties", "patch"),
        "analyticsadmin.properties.patch",
        UpdatePropertyRequest,
        body_type=Property,
        path_or_query_fields=("property.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=PROPERTY_PATCH_WRITABLE_FIELDS,
    ),
    _target(
        ("properties", "access-reports", "run"),
        "analyticsadmin.properties.runAccessReport",
        RunAccessReportRequest,
        path_or_query_fields=("entity",),
        body_forbidden_fields=("entity",),
    ),
    _target(
        ("properties", "data-retention-settings", "update"),
        "analyticsadmin.properties.updateDataRetentionSettings",
        UpdateDataRetentionSettingsRequest,
        body_type=DataRetentionSettings,
        path_or_query_fields=("dataRetentionSettings.name", "updateMask"),
        body_forbidden_fields=("name",),
    ),
    _target(
        ("properties", "custom-dimensions", "create"),
        "analyticsadmin.properties.customDimensions.create",
        CreateCustomDimensionRequest,
        body_type=CustomDimension,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    _target(
        ("properties", "custom-dimensions", "patch"),
        "analyticsadmin.properties.customDimensions.patch",
        UpdateCustomDimensionRequest,
        body_type=CustomDimension,
        path_or_query_fields=("customDimension.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=CUSTOM_DIMENSION_PATCH_WRITABLE_FIELDS,
    ),
    _target(
        ("properties", "custom-metrics", "create"),
        "analyticsadmin.properties.customMetrics.create",
        CreateCustomMetricRequest,
        body_type=CustomMetric,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    _target(
        ("properties", "custom-metrics", "patch"),
        "analyticsadmin.properties.customMetrics.patch",
        UpdateCustomMetricRequest,
        body_type=CustomMetric,
        path_or_query_fields=("customMetric.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=CUSTOM_METRIC_PATCH_WRITABLE_FIELDS,
    ),
    _target(
        ("properties", "data-streams", "create"),
        "analyticsadmin.properties.dataStreams.create",
        CreateDataStreamRequest,
        body_type=DataStream,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    _target(
        ("properties", "data-streams", "patch"),
        "analyticsadmin.properties.dataStreams.patch",
        UpdateDataStreamRequest,
        body_type=DataStream,
        path_or_query_fields=("dataStream.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=DATA_STREAM_PATCH_WRITABLE_FIELDS,
    ),
    _target(
        ("properties", "data-streams", "measurement-protocol-secrets", "create"),
        "analyticsadmin.properties.dataStreams.measurementProtocolSecrets.create",
        CreateMeasurementProtocolSecretRequest,
        body_type=MeasurementProtocolSecret,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent", "secretValue", "secret_value"),
    ),
    _target(
        ("properties", "data-streams", "measurement-protocol-secrets", "patch"),
        "analyticsadmin.properties.dataStreams.measurementProtocolSecrets.patch",
        UpdateMeasurementProtocolSecretRequest,
        body_type=MeasurementProtocolSecret,
        path_or_query_fields=("measurementProtocolSecret.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=MEASUREMENT_PROTOCOL_SECRET_PATCH_WRITABLE_FIELDS,
    ),
    _target(
        ("properties", "firebase-links", "create"),
        "analyticsadmin.properties.firebaseLinks.create",
        CreateFirebaseLinkRequest,
        body_type=FirebaseLink,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    _target(
        ("properties", "google-ads-links", "create"),
        "analyticsadmin.properties.googleAdsLinks.create",
        CreateGoogleAdsLinkRequest,
        body_type=GoogleAdsLink,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    _target(
        ("properties", "google-ads-links", "patch"),
        "analyticsadmin.properties.googleAdsLinks.patch",
        UpdateGoogleAdsLinkRequest,
        body_type=GoogleAdsLink,
        path_or_query_fields=("googleAdsLink.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=GOOGLE_ADS_LINK_PATCH_WRITABLE_FIELDS,
    ),
    _target(
        ("properties", "key-events", "create"),
        "analyticsadmin.properties.keyEvents.create",
        CreateKeyEventRequest,
        body_type=KeyEvent,
        path_or_query_fields=("parent",),
        body_forbidden_fields=("parent",),
    ),
    _target(
        ("properties", "key-events", "patch"),
        "analyticsadmin.properties.keyEvents.patch",
        UpdateKeyEventRequest,
        body_type=KeyEvent,
        path_or_query_fields=("keyEvent.name", "updateMask"),
        body_forbidden_fields=("name",),
        writable_fields=KEY_EVENT_PATCH_WRITABLE_FIELDS,
    ),
)

_SCHEMA_TARGETS: dict[tuple[str, ...], ProtobufSchemaTarget] = {
    target.cli_path: target for target in _SCHEMA_TARGET_DECLARATIONS
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
    """Return a local request descriptor for an explicitly curated body target.

    Reads and bodyless deletes are ineligible: use their leaf help. This is not
    a response schema and does not express all CLI requiredness or API semantics.
    """
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
