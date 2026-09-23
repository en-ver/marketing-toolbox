"""Local-only SDK descriptor serialization for the CLI introspection surface.

This module deliberately accepts already imported official descriptor objects.  It
never constructs a Google client, reads credentials, or makes a network call.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib.metadata import version
from typing import Any

from google.protobuf.descriptor import (
    Descriptor,
    EnumDescriptor,
    FieldDescriptor,
)


@dataclass(frozen=True)
class ProtobufSchemaTarget:
    """One registered CLI leaf mapped to its official protobuf request type."""

    cli_path: tuple[str, ...]
    official_method: str
    request_type: type[Any]
    body_type: type[Any] | None = None
    path_or_query_fields: tuple[str, ...] = ()
    body_forbidden_fields: tuple[str, ...] = ()


_FIELD_KIND_NAMES: dict[int, str] = {
    value: name.removeprefix("TYPE_").lower()
    for name, value in vars(FieldDescriptor).items()
    if name.startswith("TYPE_") and isinstance(value, int)
}


def _field_kind(field: FieldDescriptor) -> str:
    """Return the official protobuf scalar/message kind name."""
    return _FIELD_KIND_NAMES[field.type]


def _enum_values(descriptor: EnumDescriptor) -> list[dict[str, int | str]]:
    return [{"name": value.name, "number": value.number} for value in descriptor.values]


def _field_payload(field: FieldDescriptor) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": field.json_name,
        "protoName": field.name,
        "kind": _field_kind(field),
        "repeated": field.is_repeated,
    }
    if field.containing_oneof is not None:
        payload["oneof"] = field.containing_oneof.name
    if field.message_type is not None:
        payload["messageType"] = field.message_type.full_name
    if field.enum_type is not None:
        payload["enumType"] = field.enum_type.full_name
        payload["enumValues"] = _enum_values(field.enum_type)
    return payload


def _message_payload(
    descriptor: Descriptor,
    definitions: dict[str, dict[str, Any]],
    active: set[str],
    *,
    excluded_json_names: frozenset[str] = frozenset(),
) -> None:
    """Add a message and its reachable types once, safely handling cycles."""
    if descriptor.full_name in definitions or descriptor.full_name in active:
        return
    active.add(descriptor.full_name)
    definitions[descriptor.full_name] = {
        "type": descriptor.full_name,
        "fields": [
            _field_payload(field)
            for field in descriptor.fields
            if field.json_name not in excluded_json_names
        ],
    }
    for field in descriptor.fields:
        if field.message_type is not None:
            _message_payload(field.message_type, definitions, active)
    active.remove(descriptor.full_name)


def protobuf_body_schema(
    request_type: type[Any], *, excluded_json_names: frozenset[str] = frozenset()
) -> dict[str, Any]:
    """Serialize an official generated protobuf request descriptor.

    ``proto-plus`` message classes supplied by the Google Analytics SDK expose
    their real protobuf class via ``pb()``.  That operation is descriptor-only.
    """
    descriptor = request_type.pb().DESCRIPTOR
    definitions: dict[str, dict[str, Any]] = {}
    _message_payload(
        descriptor, definitions, set(), excluded_json_names=excluded_json_names
    )
    root = definitions.pop(descriptor.full_name)
    return {**root, "definitions": definitions}


def protobuf_schema_response(
    *,
    target: ProtobufSchemaTarget,
    package: str,
    api_version: str,
) -> dict[str, Any]:
    """Build source-provenance response data for one registered CLI leaf."""
    return {
        "cliPath": list(target.cli_path),
        "officialMethod": target.official_method,
        "source": {
            "kind": "installed-sdk-descriptor",
            "package": package,
            "packageVersion": version(package),
            "apiVersion": api_version,
        },
        "request": {
            "type": target.request_type.pb().DESCRIPTOR.full_name,
            "pathOrQueryFields": list(target.path_or_query_fields),
            "bodyForbiddenFields": list(target.body_forbidden_fields),
            "body": protobuf_body_schema(
                target.body_type or target.request_type,
                excluded_json_names=frozenset(target.body_forbidden_fields),
            ),
        },
    }


def resolve_schema_target(
    *,
    command: str,
    targets: Mapping[tuple[str, ...], ProtobufSchemaTarget],
) -> ProtobufSchemaTarget | None:
    """Resolve an exact registered CLI leaf path; no dynamic SDK lookup occurs."""
    path = tuple(part for part in command.split(" ") if part)
    return targets.get(path)


def target_paths(
    targets: Mapping[tuple[str, ...], ProtobufSchemaTarget],
) -> Sequence[tuple[str, ...]]:
    """Expose registered mappings for catalog/registration contract tests."""
    return tuple(targets)
