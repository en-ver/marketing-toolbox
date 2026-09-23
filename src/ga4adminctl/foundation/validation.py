"""SDK-independent operational validation and JSON body intake for GA4 Admin."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO, cast

from google.protobuf.json_format import (
    ParseDict,
    ParseError,
)

PROPERTY_PATTERN = re.compile(r"^properties/[0-9]+$")
ACCOUNT_PATTERN = re.compile(r"^accounts/[^/]+$")
DATA_SHARING_SETTINGS_PATTERN = re.compile(r"^accounts/[^/]+/dataSharingSettings$")
DATA_RETENTION_SETTINGS_PATTERN = re.compile(
    r"^properties/[0-9]+/dataRetentionSettings$"
)
MEASUREMENT_PROTOCOL_SECRET_PATTERN = re.compile(
    r"^properties/[0-9]+/dataStreams/[^/]+/measurementProtocolSecrets/[^/]+$"
)
DATA_STREAM_PATTERN = re.compile(r"^properties/[0-9]+/dataStreams/[^/]+$")
FIREBASE_LINK_PATTERN = re.compile(r"^properties/[0-9]+/firebaseLinks/[^/]+$")
GOOGLE_ADS_LINK_PATTERN = re.compile(r"^properties/[0-9]+/googleAdsLinks/[^/]+$")
KEY_EVENT_PATTERN = re.compile(r"^properties/[0-9]+/keyEvents/[^/]+$")
PROPERTY_LIST_FILTER_PATTERN = re.compile(
    r"^(?:parent|ancestor):accounts/[0-9]+$|^firebase_project:projects/[A-Za-z0-9][A-Za-z0-9-]{4,28}[A-Za-z0-9]$"
)
MAX_BODY_CHARACTERS = 1_048_576
MAX_PROPERTY_PAGE_SIZE = 200


class RequestValidationError(ValueError):
    """Raised when CLI request inputs violate the public command contract."""


def read_json_body(source: str, *, stdin: TextIO) -> dict[str, Any]:
    """Read one bounded, strict JSON object from a file or standard input."""
    try:
        if source == "-":
            text = stdin.read(MAX_BODY_CHARACTERS + 1)
        else:
            with Path(source).open(encoding="utf-8") as body_file:
                text = body_file.read(MAX_BODY_CHARACTERS + 1)
    except (OSError, UnicodeDecodeError) as exc:
        raise RequestValidationError(
            "--body must name a readable UTF-8 JSON file."
        ) from exc
    if len(text) > MAX_BODY_CHARACTERS:
        raise RequestValidationError(
            f"--body must not exceed {MAX_BODY_CHARACTERS} characters."
        )
    try:
        body = json.loads(
            text, parse_constant=lambda _: (_ for _ in ()).throw(ValueError())
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise RequestValidationError(
            "--body must contain a valid JSON object."
        ) from exc
    if not isinstance(body, dict):
        raise RequestValidationError("--body must contain a JSON object.")
    return cast(dict[str, Any], body)


def validate_property_name(property_name: str) -> None:
    """Validate the exact stable GA4 Property resource-name format."""
    if not PROPERTY_PATTERN.fullmatch(property_name):
        raise RequestValidationError("--property must match properties/<numeric-id>.")


def validate_resource_name(name: str, *, flag: str, pattern: re.Pattern[str]) -> None:
    """Validate an exact canonical resource name before loading credentials."""
    if not pattern.fullmatch(name):
        raise RequestValidationError(f"{flag} must be a canonical GA4 resource name.")


def validate_page_request(page_size: int, page_token: str) -> None:
    """Validate the shared bounded single-page list contract."""
    if not 1 <= page_size <= MAX_PROPERTY_PAGE_SIZE:
        raise RequestValidationError(
            f"--page-size must be between 1 and {MAX_PROPERTY_PAGE_SIZE}."
        )
    if page_token and page_token.strip() != page_token:
        raise RequestValidationError(
            "--page-token must not have leading or trailing whitespace."
        )


def validate_properties_list_request(
    filter_expression: str, page_size: int, page_token: str
) -> None:
    """Validate the bounded, documented ListProperties request inputs."""
    if not PROPERTY_LIST_FILTER_PATTERN.fullmatch(filter_expression):
        raise RequestValidationError(
            "--filter must be one of parent:accounts/<numeric-id>, "
            "ancestor:accounts/<numeric-id>, or firebase_project:projects/<project-id>."
        )
    validate_page_request(page_size, page_token)


def reject_route_fields(body: Mapping[str, Any], *fields: str) -> None:
    """Prevent a JSON body from overriding a route value injected by the CLI."""
    for field in fields:
        if field in body:
            raise RequestValidationError(
                f"--body must not contain route field {field}."
            )


def reject_sensitive_fields(body: Mapping[str, Any], *fields: str) -> None:
    """Reject fields whose values must never be accepted or rendered by the CLI."""
    for field in fields:
        if field in body:
            raise RequestValidationError(
                f"--body must not contain sensitive field {field}."
            )


def parse_sdk_message(body: Mapping[str, Any], message_type: Any) -> Any:
    """Build an official Admin SDK message from protobuf JSON before dispatch.

    This is deliberately the only structural body boundary: the pinned Google
    Admin SDK owns accepted fields, JSON spelling, nested messages, and enums.
    """
    message = message_type()
    try:
        ParseDict(dict(body), message_type.pb(message), ignore_unknown_fields=False)
    except (ParseError, TypeError, ValueError) as exc:
        raise RequestValidationError(
            f"--body cannot be converted to a {message_type.__name__}: {exc}"
        ) from exc
    return message
