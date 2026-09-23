"""Local official Discovery-document serialization for SDK introspection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import Any, cast

import googleapiclient.discovery_cache


@dataclass(frozen=True)
class DiscoverySchemaTarget:
    """One registered CLI leaf mapped to an official Discovery method id."""

    cli_path: tuple[str, ...]
    official_method: str
    path_or_query_fields: tuple[str, ...] = ()
    body_forbidden_fields: tuple[str, ...] = ()


def _document_path(api: str, api_version: str) -> Path:
    return (
        Path(googleapiclient.discovery_cache.__file__).parent
        / "documents"
        / f"{api}.{api_version}.json"
    )


def load_local_discovery_document(api: str, api_version: str) -> dict[str, Any]:
    """Read a bundled official Discovery document without constructing a client."""
    path = _document_path(api, api_version)
    with path.open(encoding="utf-8") as source:
        return cast(dict[str, Any], json.load(source))


def _walk_methods(node: dict[str, Any]) -> list[dict[str, Any]]:
    methods = list(node.get("methods", {}).values())
    for resource in node.get("resources", {}).values():
        methods.extend(_walk_methods(resource))
    return methods


def _method(document: dict[str, Any], method_id: str) -> dict[str, Any]:
    for method in _walk_methods(document):
        if method.get("id") == method_id:
            return method
    raise ValueError(f"Official Discovery method is not present: {method_id}")


def _schema_references(value: Any) -> set[str]:
    """Return every official Discovery ``$ref`` nested in a schema fragment."""
    if isinstance(value, dict):
        references = {value["$ref"]} if isinstance(value.get("$ref"), str) else set()
        for nested in value.values():
            references.update(_schema_references(nested))
        return references
    if isinstance(value, list):
        return set().union(*(_schema_references(nested) for nested in value))
    return set()


def _schema_payload(
    schema_name: str,
    schemas: dict[str, Any],
    definitions: dict[str, dict[str, Any]],
    active: set[str],
) -> dict[str, Any]:
    """Serialize one official schema and all reachable official ``$ref`` types."""
    schema = schemas[schema_name]
    payload: dict[str, Any] = {"type": schema_name}
    for key in ("description", "properties", "required", "additionalProperties"):
        if key in schema:
            payload[key] = schema[key]
    if schema_name in active:
        return payload
    active.add(schema_name)
    for reference in sorted(_schema_references(schema)):
        if reference not in schemas or reference in definitions:
            continue
        definitions[reference] = _schema_payload(
            reference, schemas, definitions, active
        )
    active.remove(schema_name)
    return payload


def discovery_method_parameters(
    *, api: str, api_version: str, method_id: str
) -> dict[str, Any]:
    """Return the official parameters for one bundled Discovery method."""
    return cast(
        dict[str, Any],
        _method(load_local_discovery_document(api, api_version), method_id).get(
            "parameters", {}
        ),
    )


def discovery_schema_response(
    *,
    target: DiscoverySchemaTarget,
    api: str,
    api_version: str,
) -> dict[str, Any]:
    """Build a source-provenance response from a bundled Discovery artifact."""
    document = load_local_discovery_document(api, api_version)
    method = _method(document, target.official_method)
    request_ref = method.get("request", {}).get("$ref")
    schemas = document.get("schemas", {})
    body: dict[str, Any]
    if request_ref is None:
        # GTM Gallery import is the supported exception: its CLI body transports
        # official query parameters rather than a Discovery request resource.
        body = {
            "type": "official-query-parameter-envelope",
            "fields": [
                {"name": name, **parameter}
                for name, parameter in method.get("parameters", {}).items()
                if parameter.get("location") != "path"
                and name not in target.body_forbidden_fields
            ],
            "definitions": {},
        }
    else:
        definitions: dict[str, dict[str, Any]] = {}
        body = _schema_payload(request_ref, schemas, definitions, set())
        body["definitions"] = definitions
    parameters = method.get("parameters", {})
    return {
        "cliPath": list(target.cli_path),
        "officialMethod": target.official_method,
        "source": {
            "kind": "installed-discovery-document",
            "package": "google-api-python-client",
            "packageVersion": version("google-api-python-client"),
            "apiVersion": document.get("version", api_version),
            "revision": document.get("revision"),
        },
        "request": {
            "type": request_ref or "none",
            "pathOrQueryFields": list(target.path_or_query_fields),
            "bodyForbiddenFields": list(target.body_forbidden_fields),
            "body": body,
            "officialParameters": parameters,
        },
    }
