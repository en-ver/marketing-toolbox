"""Ordinary GA4 Admin property and property-settings operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from google.analytics.admin_v1beta.types import (
    AcknowledgeUserDataCollectionRequest,
    AcknowledgeUserDataCollectionResponse,
    CreatePropertyRequest,
    DataRetentionSettings,
    DataSharingSettings,
    DeletePropertyRequest,
    GetDataRetentionSettingsRequest,
    GetDataSharingSettingsRequest,
    GetPropertyRequest,
    ListPropertiesRequest,
    ListPropertiesResponse,
    Property,
    UpdateDataRetentionSettingsRequest,
    UpdatePropertyRequest,
)

from ga4adminctl.foundation.serialization import message_response as _message_response
from ga4adminctl.foundation.validation import (
    DATA_RETENTION_SETTINGS_PATTERN,
    DATA_SHARING_SETTINGS_PATTERN,
    PROPERTY_PATTERN,
    RequestValidationError,
    parse_sdk_message,
    reject_route_fields,
    validate_properties_list_request,
    validate_property_name,
    validate_resource_name,
)
from ga4adminctl.operations import transport

PROPERTY_PATCH_WRITABLE_FIELDS = (
    "displayName",
    "industryCategory",
    "timeZone",
    "currencyCode",
)


def get_property(property_name: str) -> dict[str, Any]:
    """Get one Property through the official Admin API v1beta client."""
    validate_property_name(property_name)
    return transport.read(
        GetPropertyRequest(name=property_name), "get_property", Property
    )


def list_properties(
    filter_expression: str,
    *,
    page_size: int,
    page_token: str,
    show_deleted: bool,
) -> dict[str, Any]:
    """Return exactly one raw ListProperties response page from Admin v1beta."""
    validate_properties_list_request(filter_expression, page_size, page_token)
    return transport.list_page(
        ListPropertiesRequest(
            filter=filter_expression,
            page_size=page_size,
            page_token=page_token,
            show_deleted=show_deleted,
        ),
        "list_properties",
        ListPropertiesResponse,
    )


def create_property(body: Mapping[str, Any], *, apply: bool = False) -> dict[str, Any]:
    """Plan or create one bounded Property without automatic retry."""
    property_message = parse_sdk_message(body, Property)
    if not apply:
        return {"dryRun": True, "request": {"property": dict(body)}}
    return transport.write(
        CreatePropertyRequest(property=property_message),
        "create_property",
        _message_response(Property),
    )


def delete_property(name: str, *, apply: bool = False) -> dict[str, Any]:
    """Plan or move one Property to trash; never retry the request."""
    validate_resource_name(name, flag="--name", pattern=PROPERTY_PATTERN)
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return transport.write(
        DeletePropertyRequest(name=name), "delete_property", _message_response(Property)
    )


def acknowledge_user_data_collection(
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or acknowledge user-data collection once, without automatic retry."""
    validate_resource_name(property_name, flag="--property", pattern=PROPERTY_PATTERN)
    reject_route_fields(body, "property")
    request_body = {"property": property_name, **dict(body)}
    request = parse_sdk_message(request_body, AcknowledgeUserDataCollectionRequest)
    if not apply:
        return {"dryRun": True, "request": request_body}
    return transport.write(
        request,
        "acknowledge_user_data_collection",
        _message_response(AcknowledgeUserDataCollectionResponse),
    )


def get_data_sharing_settings(name: str) -> dict[str, Any]:
    validate_resource_name(name, flag="--name", pattern=DATA_SHARING_SETTINGS_PATTERN)
    return transport.read(
        GetDataSharingSettingsRequest(name=name),
        "get_data_sharing_settings",
        DataSharingSettings,
    )


def get_data_retention_settings(name: str) -> dict[str, Any]:
    validate_resource_name(name, flag="--name", pattern=DATA_RETENTION_SETTINGS_PATTERN)
    return transport.read(
        GetDataRetentionSettingsRequest(name=name),
        "get_data_retention_settings",
        DataRetentionSettings,
    )


def update_data_retention_settings(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or apply one bounded, non-retried retention-settings update."""
    validate_resource_name(name, flag="--name", pattern=DATA_RETENTION_SETTINGS_PATTERN)
    reject_route_fields(body, "name")
    settings = parse_sdk_message(body, DataRetentionSettings)
    settings.name = name
    mutable_fields = {
        "eventDataRetention",
        "userDataRetention",
        "resetUserDataOnNewActivity",
    }
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
    if set(mask_fields) - set(body):
        raise RequestValidationError("--update-mask fields must be present in --body.")
    if set(body) - set(mask_fields):
        raise RequestValidationError("--body fields must be named by --update-mask.")
    if not apply:
        return {
            "dryRun": True,
            "request": {
                "dataRetentionSettings": {"name": name, **dict(body)},
                "updateMask": update_mask,
            },
        }
    request = UpdateDataRetentionSettingsRequest(
        data_retention_settings=settings, update_mask=update_mask
    )
    return transport.write(
        request,
        "update_data_retention_settings",
        _message_response(DataRetentionSettings),
    )


def update_property(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or apply one bounded, non-retried Property update."""
    validate_resource_name(name, flag="--name", pattern=PROPERTY_PATTERN)
    reject_route_fields(body, "name")
    property_message = parse_sdk_message(body, Property)
    property_message.name = name
    mask_fields = update_mask.split(",") if update_mask else []
    if (
        not mask_fields
        or any(not field or field.strip() != field for field in mask_fields)
        or len(set(mask_fields)) != len(mask_fields)
        or not set(mask_fields).issubset(PROPERTY_PATCH_WRITABLE_FIELDS)
    ):
        raise RequestValidationError(
            "--update-mask must be a nonempty, comma-separated set of mutable body fields."
        )
    if set(mask_fields) - set(body):
        raise RequestValidationError("--update-mask fields must be present in --body.")
    if set(body) - set(mask_fields):
        raise RequestValidationError("--body fields must be named by --update-mask.")
    if not apply:
        return {
            "dryRun": True,
            "request": {
                "property": {"name": name, **dict(body)},
                "updateMask": update_mask,
            },
        }
    request = UpdatePropertyRequest(property=property_message, update_mask=update_mask)
    return transport.write(request, "update_property", _message_response(Property))
