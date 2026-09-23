"""Sensitive GA4 Admin Measurement Protocol secret operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from google.analytics.admin_v1beta.types import (
    CreateMeasurementProtocolSecretRequest,
    DeleteMeasurementProtocolSecretRequest,
    GetMeasurementProtocolSecretRequest,
    ListMeasurementProtocolSecretsRequest,
    ListMeasurementProtocolSecretsResponse,
    MeasurementProtocolSecret,
    UpdateMeasurementProtocolSecretRequest,
)

from ga4adminctl.foundation.serialization import (
    empty_response as _empty_response,
)
from ga4adminctl.foundation.serialization import (
    remove_secret_values as _remove_secret_values,
)
from ga4adminctl.foundation.serialization import (
    secret_metadata_response as _secret_metadata_response,
)
from ga4adminctl.foundation.validation import (
    DATA_STREAM_PATTERN,
    MEASUREMENT_PROTOCOL_SECRET_PATTERN,
    parse_sdk_message,
    reject_sensitive_fields,
    validate_page_request,
    validate_resource_name,
)
from ga4adminctl.operations import mutations, reads, resources

PropertiesClientFactory = reads.PropertiesClientFactory
_update_child = resources._update_child


def get_measurement_protocol_secret(name: str) -> dict[str, Any]:
    """Get acknowledged Measurement Protocol secret metadata without secret values."""
    validate_resource_name(
        name, flag="--name", pattern=MEASUREMENT_PROTOCOL_SECRET_PATTERN
    )
    return _remove_secret_values(
        reads._read_v1beta(
            GetMeasurementProtocolSecretRequest(name=name),
            "get_measurement_protocol_secret",
            MeasurementProtocolSecret,
        )
    )


def list_measurement_protocol_secrets(
    parent: str, *, page_size: int, page_token: str
) -> dict[str, Any]:
    """Return exactly one acknowledged Measurement Protocol secret page."""
    validate_resource_name(parent, flag="--data-stream", pattern=DATA_STREAM_PATTERN)
    validate_page_request(page_size, page_token)
    return _remove_secret_values(
        reads._list_v1beta(
            ListMeasurementProtocolSecretsRequest(
                parent=parent, page_size=page_size, page_token=page_token
            ),
            "list_measurement_protocol_secrets",
            ListMeasurementProtocolSecretsResponse,
        )
    )


def create_measurement_protocol_secret(
    data_stream: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
    client_factory: PropertiesClientFactory | None = None,
) -> dict[str, Any]:
    """Plan or create sensitive secret metadata without exposing secretValue."""
    validate_resource_name(
        data_stream, flag="--data-stream", pattern=DATA_STREAM_PATTERN
    )
    reject_sensitive_fields(body, "secretValue")
    secret = parse_sdk_message(body, MeasurementProtocolSecret)
    if not apply:
        return {
            "dryRun": True,
            "request": {"parent": data_stream, "measurementProtocolSecret": dict(body)},
        }
    return mutations._write_v1beta(
        CreateMeasurementProtocolSecretRequest(
            parent=data_stream, measurement_protocol_secret=secret
        ),
        "create_measurement_protocol_secret",
        _secret_metadata_response,
        client_factory=client_factory,
    )


def update_measurement_protocol_secret(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
    client_factory: PropertiesClientFactory | None = None,
) -> dict[str, Any]:
    """Plan or update sensitive secret metadata without exposing secretValue."""
    return _remove_secret_values(
        _update_child(
            name,
            body,
            update_mask,
            collection="measurementProtocolSecrets",
            mutable_fields={"displayName"},
            message_type=MeasurementProtocolSecret,
            request_type=UpdateMeasurementProtocolSecretRequest,
            request_field="measurement_protocol_secret",
            request_json_field="measurementProtocolSecret",
            method="update_measurement_protocol_secret",
            apply=apply,
            client_factory=client_factory,
            name_pattern=MEASUREMENT_PROTOCOL_SECRET_PATTERN,
        )
    )


def delete_measurement_protocol_secret(
    name: str,
    *,
    apply: bool = False,
    client_factory: PropertiesClientFactory | None = None,
) -> dict[str, Any]:
    """Plan or irreversibly delete a secret; never retry the dispatch."""
    validate_resource_name(
        name, flag="--name", pattern=MEASUREMENT_PROTOCOL_SECRET_PATTERN
    )
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return mutations._write_v1beta(
        DeleteMeasurementProtocolSecretRequest(name=name),
        "delete_measurement_protocol_secret",
        _empty_response,
        client_factory=client_factory,
    )
