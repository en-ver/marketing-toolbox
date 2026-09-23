"""Protobuf and secret-safe response serialization for GA4 Admin."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from google.protobuf.json_format import MessageToDict


def message_response(message_type: Any) -> Callable[[Any], dict[str, Any]]:
    """Render a protobuf response with the established Admin JSON semantics."""
    return lambda response: MessageToDict(
        message_type.pb(response), preserving_proto_field_name=False
    )


def raw_message_response(response: Any) -> dict[str, Any]:
    """Render a raw protobuf response with established Admin JSON semantics."""
    return MessageToDict(response, preserving_proto_field_name=False)


def empty_response(_response: Any) -> dict[str, Any]:
    """Render successful empty RPC responses, including GAPIC ``None`` values."""
    return {}


def remove_secret_values(data: dict[str, Any]) -> dict[str, Any]:
    """Strip output-only secret values from all secret command responses."""
    data.pop("secretValue", None)
    for secret in data.get("measurementProtocolSecrets", []):
        if isinstance(secret, dict):
            secret.pop("secretValue", None)
    return data


def secret_metadata_response(response: Any) -> dict[str, Any]:
    """Render secret metadata while unconditionally withholding secret values."""
    data = MessageToDict(type(response).pb(response), preserving_proto_field_name=False)
    return remove_secret_values(data)
