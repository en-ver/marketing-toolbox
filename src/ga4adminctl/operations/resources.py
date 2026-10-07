"""Ordinary GA4 Admin child-resource operations."""

from __future__ import annotations

import re
from collections.abc import Collection, Mapping
from typing import Any

from google.analytics.admin_v1beta.types import (
    ArchiveCustomDimensionRequest,
    ArchiveCustomMetricRequest,
    CreateCustomDimensionRequest,
    CreateCustomMetricRequest,
    CreateDataStreamRequest,
    CreateFirebaseLinkRequest,
    CreateGoogleAdsLinkRequest,
    CreateKeyEventRequest,
    CustomDimension,
    CustomMetric,
    DataStream,
    DeleteDataStreamRequest,
    DeleteFirebaseLinkRequest,
    DeleteGoogleAdsLinkRequest,
    DeleteKeyEventRequest,
    FirebaseLink,
    GetCustomDimensionRequest,
    GetCustomMetricRequest,
    GetDataStreamRequest,
    GetKeyEventRequest,
    GoogleAdsLink,
    KeyEvent,
    ListCustomDimensionsRequest,
    ListCustomDimensionsResponse,
    ListCustomMetricsRequest,
    ListCustomMetricsResponse,
    ListDataStreamsRequest,
    ListDataStreamsResponse,
    ListFirebaseLinksRequest,
    ListFirebaseLinksResponse,
    ListGoogleAdsLinksRequest,
    ListGoogleAdsLinksResponse,
    ListKeyEventsRequest,
    ListKeyEventsResponse,
    UpdateCustomDimensionRequest,
    UpdateCustomMetricRequest,
    UpdateDataStreamRequest,
    UpdateGoogleAdsLinkRequest,
    UpdateKeyEventRequest,
)

from ga4adminctl.foundation.serialization import (
    empty_response as _empty_response,
)
from ga4adminctl.foundation.serialization import (
    message_response as _message_response,
)
from ga4adminctl.foundation.validation import (
    DATA_STREAM_PATTERN,
    FIREBASE_LINK_PATTERN,
    GOOGLE_ADS_LINK_PATTERN,
    KEY_EVENT_PATTERN,
    PROPERTY_PATTERN,
    RequestValidationError,
    parse_sdk_message,
    reject_route_fields,
    validate_page_request,
    validate_resource_name,
)
from ga4adminctl.operations import transport

CUSTOM_DIMENSION_PATCH_WRITABLE_FIELDS = (
    "displayName",
    "description",
    "disallowAdsPersonalization",
)
CUSTOM_METRIC_PATCH_WRITABLE_FIELDS = (
    "displayName",
    "description",
    "measurementUnit",
    "restrictedMetricType",
)
DATA_STREAM_PATCH_WRITABLE_FIELDS = ("displayName", "webStreamData.defaultUri")
GOOGLE_ADS_LINK_PATCH_WRITABLE_FIELDS = ("adsPersonalizationEnabled",)
KEY_EVENT_PATCH_WRITABLE_FIELDS = (
    "countingMethod",
    "defaultValue.numericValue",
    "defaultValue.currencyCode",
)


def _canonical_body_leaf_paths(body: Mapping[str, Any], message_type: Any) -> set[str]:
    """Return canonical protobuf paths for supplied child-update body leaves."""

    def resolve_field(descriptor: Any, key: str) -> Any:
        field = descriptor.fields_by_name.get(key)
        if field is not None:
            return field
        return next(field for field in descriptor.fields if field.json_name == key)

    def collect(
        value: Mapping[str, Any], descriptor: Any, prefix: str = ""
    ) -> set[str]:
        paths: set[str] = set()
        for key, nested_value in value.items():
            field = resolve_field(descriptor, key)
            path = f"{prefix}.{field.name}" if prefix else field.name
            if (
                field.message_type is not None
                and isinstance(nested_value, Mapping)
                and not field.message_type.GetOptions().map_entry
                and not field.message_type.full_name.startswith("google.protobuf.")
            ):
                paths.update(collect(nested_value, field.message_type, path))
            elif field.message_type is None or nested_value is not None:
                paths.add(path)
        return paths

    return collect(body, message_type.pb().DESCRIPTOR)


def _update_child(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    collection: str,
    mutable_fields: Collection[str],
    message_type: Any,
    request_type: Any,
    request_field: str,
    request_json_field: str,
    method: str,
    apply: bool,
    name_pattern: re.Pattern[str] | None = None,
) -> dict[str, Any]:
    """Plan or apply one bounded custom-definition update."""
    pattern, _ = _child_patterns(collection)
    if name_pattern is not None:
        pattern = name_pattern
    validate_resource_name(name, flag="--name", pattern=pattern)
    reject_route_fields(body, "name")
    message = parse_sdk_message(body, message_type)
    message.name = name
    mask_fields = update_mask.split(",") if update_mask else []
    if (
        not mask_fields
        or any(not field or field.strip() != field for field in mask_fields)
        or len(set(mask_fields)) != len(mask_fields)
        or not set(mask_fields).issubset(mutable_fields)
    ):
        raise RequestValidationError(
            "--update-mask must be a nonempty, comma-separated set of mutable body fields."
        )
    if {field.split(".", 1)[0] for field in mask_fields} != set(body):
        raise RequestValidationError(
            "--update-mask fields must match --body fields exactly."
        )
    normalized_mask_paths = set(request_type(update_mask=update_mask).update_mask.paths)
    if _canonical_body_leaf_paths(body, message_type) != normalized_mask_paths:
        raise RequestValidationError(
            "--update-mask fields must match --body fields exactly."
        )
    if not apply:
        return {
            "dryRun": True,
            "request": {
                request_json_field: {"name": name, **dict(body)},
                "updateMask": update_mask,
            },
        }
    request = request_type(**{request_field: message, "update_mask": update_mask})
    return transport.write(request, method, _message_response(message_type))


def update_custom_dimension(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    return _update_child(
        name,
        body,
        update_mask,
        collection="customDimensions",
        mutable_fields=CUSTOM_DIMENSION_PATCH_WRITABLE_FIELDS,
        message_type=CustomDimension,
        request_type=UpdateCustomDimensionRequest,
        request_field="custom_dimension",
        request_json_field="customDimension",
        method="update_custom_dimension",
        apply=apply,
    )


def update_custom_metric(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    return _update_child(
        name,
        body,
        update_mask,
        collection="customMetrics",
        mutable_fields=CUSTOM_METRIC_PATCH_WRITABLE_FIELDS,
        message_type=CustomMetric,
        request_type=UpdateCustomMetricRequest,
        request_field="custom_metric",
        request_json_field="customMetric",
        method="update_custom_metric",
        apply=apply,
    )


def _create_custom_definition(
    property_name: str,
    body: Mapping[str, Any],
    *,
    message_type: Any,
    request_type: Any,
    request_field: str,
    request_json_field: str,
    method: str,
    apply: bool,
) -> dict[str, Any]:
    """Plan or create one bounded custom definition without automatic retry."""
    validate_resource_name(property_name, flag="--property", pattern=PROPERTY_PATTERN)
    message = parse_sdk_message(body, message_type)
    if not apply:
        return {
            "dryRun": True,
            "request": {"parent": property_name, request_json_field: dict(body)},
        }
    request = request_type(parent=property_name, **{request_field: message})
    return transport.write(request, method, _message_response(message_type))


def create_custom_dimension(
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
) -> dict[str, Any]:
    return _create_custom_definition(
        property_name,
        body,
        message_type=CustomDimension,
        request_type=CreateCustomDimensionRequest,
        request_field="custom_dimension",
        request_json_field="customDimension",
        method="create_custom_dimension",
        apply=apply,
    )


def create_custom_metric(
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
) -> dict[str, Any]:
    return _create_custom_definition(
        property_name,
        body,
        message_type=CustomMetric,
        request_type=CreateCustomMetricRequest,
        request_field="custom_metric",
        request_json_field="customMetric",
        method="create_custom_metric",
        apply=apply,
    )


def _archive_custom_definition(
    name: str,
    *,
    collection: str,
    request_type: Any,
    method: str,
    apply: bool,
) -> dict[str, Any]:
    """Plan or archive a custom definition; archive is never retried."""
    pattern, _ = _child_patterns(collection)
    validate_resource_name(name, flag="--name", pattern=pattern)
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return transport.write(request_type(name=name), method, _empty_response)


def archive_custom_dimension(
    name: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    return _archive_custom_definition(
        name,
        collection="customDimensions",
        request_type=ArchiveCustomDimensionRequest,
        method="archive_custom_dimension",
        apply=apply,
    )


def archive_custom_metric(
    name: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    return _archive_custom_definition(
        name,
        collection="customMetrics",
        request_type=ArchiveCustomMetricRequest,
        method="archive_custom_metric",
        apply=apply,
    )


def update_data_stream(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or apply one bounded, non-retried DataStream update."""
    return _update_child(
        name,
        body,
        update_mask,
        collection="dataStreams",
        mutable_fields=DATA_STREAM_PATCH_WRITABLE_FIELDS,
        message_type=DataStream,
        request_type=UpdateDataStreamRequest,
        request_field="data_stream",
        request_json_field="dataStream",
        method="update_data_stream",
        apply=apply,
    )


def create_data_stream(
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or create one bounded Web DataStream without automatic retry."""
    return _create_custom_definition(
        property_name,
        body,
        message_type=DataStream,
        request_type=CreateDataStreamRequest,
        request_field="data_stream",
        request_json_field="dataStream",
        method="create_data_stream",
        apply=apply,
    )


def delete_data_stream(
    name: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or delete one DataStream; deletion is irreversible and never retried."""
    validate_resource_name(name, flag="--name", pattern=DATA_STREAM_PATTERN)
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return transport.write(
        DeleteDataStreamRequest(name=name), "delete_data_stream", _empty_response
    )


def create_firebase_link(
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or create one Firebase link without automatic retry."""
    return _create_custom_definition(
        property_name,
        body,
        message_type=FirebaseLink,
        request_type=CreateFirebaseLinkRequest,
        request_field="firebase_link",
        request_json_field="firebaseLink",
        method="create_firebase_link",
        apply=apply,
    )


def delete_firebase_link(
    name: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or delete one Firebase link; deletion is irreversible and never retried."""
    validate_resource_name(name, flag="--name", pattern=FIREBASE_LINK_PATTERN)
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return transport.write(
        DeleteFirebaseLinkRequest(name=name), "delete_firebase_link", _empty_response
    )


def create_google_ads_link(
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or create one Google Ads link without automatic retry."""
    return _create_custom_definition(
        property_name,
        body,
        message_type=GoogleAdsLink,
        request_type=CreateGoogleAdsLinkRequest,
        request_field="google_ads_link",
        request_json_field="googleAdsLink",
        method="create_google_ads_link",
        apply=apply,
    )


def delete_google_ads_link(
    name: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or delete one Google Ads link; deletion is irreversible and never retried."""
    validate_resource_name(name, flag="--name", pattern=GOOGLE_ADS_LINK_PATTERN)
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return transport.write(
        DeleteGoogleAdsLinkRequest(name=name),
        "delete_google_ads_link",
        _empty_response,
    )


def create_key_event(
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or create one KeyEvent without automatic retry."""
    return _create_custom_definition(
        property_name,
        body,
        message_type=KeyEvent,
        request_type=CreateKeyEventRequest,
        request_field="key_event",
        request_json_field="keyEvent",
        method="create_key_event",
        apply=apply,
    )


def delete_key_event(
    name: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or delete one KeyEvent; deletion is irreversible and never retried."""
    validate_resource_name(name, flag="--name", pattern=KEY_EVENT_PATTERN)
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return transport.write(
        DeleteKeyEventRequest(name=name), "delete_key_event", _empty_response
    )


def update_google_ads_link(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or apply one bounded, non-retried Google Ads link update."""
    return _update_child(
        name,
        body,
        update_mask,
        collection="googleAdsLinks",
        mutable_fields=GOOGLE_ADS_LINK_PATCH_WRITABLE_FIELDS,
        message_type=GoogleAdsLink,
        request_type=UpdateGoogleAdsLinkRequest,
        request_field="google_ads_link",
        request_json_field="googleAdsLink",
        method="update_google_ads_link",
        apply=apply,
    )


def update_key_event(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or apply one bounded, non-retried KeyEvent update."""
    return _update_child(
        name,
        body,
        update_mask,
        collection="keyEvents",
        mutable_fields=KEY_EVENT_PATCH_WRITABLE_FIELDS,
        message_type=KeyEvent,
        request_type=UpdateKeyEventRequest,
        request_field="key_event",
        request_json_field="keyEvent",
        method="update_key_event",
        apply=apply,
    )


def _child_patterns(collection: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    escaped = re.escape(collection)
    return (
        re.compile(rf"^properties/[0-9]+/{escaped}/[^/]+$"),
        re.compile(r"^properties/[0-9]+$"),
    )


def _get_child(
    name: str, collection: str, request_type: Any, response_type: Any, method: str
) -> dict[str, Any]:
    pattern, _ = _child_patterns(collection)
    validate_resource_name(name, flag="--name", pattern=pattern)
    return transport.read(request_type(name=name), method, response_type)


def _list_child(
    parent: str,
    page_size: int,
    page_token: str,
    collection: str,
    request_type: Any,
    response_type: Any,
    method: str,
) -> dict[str, Any]:
    _, parent_pattern = _child_patterns(collection)
    validate_resource_name(parent, flag="--property", pattern=parent_pattern)
    validate_page_request(page_size, page_token)
    return transport.list_page(
        request_type(parent=parent, page_size=page_size, page_token=page_token),
        method,
        response_type,
    )


def get_data_stream(name: str) -> dict[str, Any]:
    return _get_child(
        name, "dataStreams", GetDataStreamRequest, DataStream, "get_data_stream"
    )


def list_data_streams(
    parent: str, *, page_size: int, page_token: str
) -> dict[str, Any]:
    return _list_child(
        parent,
        page_size,
        page_token,
        "dataStreams",
        ListDataStreamsRequest,
        ListDataStreamsResponse,
        "list_data_streams",
    )


def get_custom_dimension(name: str) -> dict[str, Any]:
    return _get_child(
        name,
        "customDimensions",
        GetCustomDimensionRequest,
        CustomDimension,
        "get_custom_dimension",
    )


def list_custom_dimensions(
    parent: str, *, page_size: int, page_token: str
) -> dict[str, Any]:
    return _list_child(
        parent,
        page_size,
        page_token,
        "customDimensions",
        ListCustomDimensionsRequest,
        ListCustomDimensionsResponse,
        "list_custom_dimensions",
    )


def get_custom_metric(name: str) -> dict[str, Any]:
    return _get_child(
        name, "customMetrics", GetCustomMetricRequest, CustomMetric, "get_custom_metric"
    )


def list_custom_metrics(
    parent: str, *, page_size: int, page_token: str
) -> dict[str, Any]:
    return _list_child(
        parent,
        page_size,
        page_token,
        "customMetrics",
        ListCustomMetricsRequest,
        ListCustomMetricsResponse,
        "list_custom_metrics",
    )


def list_firebase_links(
    parent: str, *, page_size: int, page_token: str
) -> dict[str, Any]:
    return _list_child(
        parent,
        page_size,
        page_token,
        "firebaseLinks",
        ListFirebaseLinksRequest,
        ListFirebaseLinksResponse,
        "list_firebase_links",
    )


def list_google_ads_links(
    parent: str, *, page_size: int, page_token: str
) -> dict[str, Any]:
    return _list_child(
        parent,
        page_size,
        page_token,
        "googleAdsLinks",
        ListGoogleAdsLinksRequest,
        ListGoogleAdsLinksResponse,
        "list_google_ads_links",
    )


def get_key_event(name: str) -> dict[str, Any]:
    return _get_child(name, "keyEvents", GetKeyEventRequest, KeyEvent, "get_key_event")


def list_key_events(parent: str, *, page_size: int, page_token: str) -> dict[str, Any]:
    return _list_child(
        parent,
        page_size,
        page_token,
        "keyEvents",
        ListKeyEventsRequest,
        ListKeyEventsResponse,
        "list_key_events",
    )
