"""SDK-independent request validation and JSON body intake for GA4 Data."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TextIO

from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from ga4datactl.schemas import (
    BATCH_RUN_PIVOT_REPORTS_BODY_SCHEMA,
    BATCH_RUN_REPORTS_BODY_SCHEMA,
    CHECK_COMPATIBILITY_BODY_SCHEMA,
    CREATE_AUDIENCE_EXPORT_BODY_SCHEMA,
    RUN_PIVOT_REPORT_BODY_SCHEMA,
    RUN_REALTIME_REPORT_BODY_SCHEMA,
    RUN_REPORT_BODY_SCHEMA,
)

PROPERTY_PATTERN = re.compile(r"^properties/[0-9]+$")
AUDIENCE_EXPORT_PATTERN = re.compile(r"^properties/[0-9]+/audienceExports/[^/]+$")
AUDIENCE_PATTERN = re.compile(r"^properties/[0-9]+/audiences/[^/]+$")
MAX_BODY_CHARACTERS = 1_048_576


class RequestValidationError(ValueError):
    """Raised when CLI request inputs violate the public command contract."""


RUN_REPORT_BODY_VALIDATOR = Draft202012Validator(RUN_REPORT_BODY_SCHEMA)
BATCH_RUN_REPORTS_BODY_VALIDATOR = Draft202012Validator(BATCH_RUN_REPORTS_BODY_SCHEMA)
BATCH_RUN_PIVOT_REPORTS_BODY_VALIDATOR = Draft202012Validator(
    BATCH_RUN_PIVOT_REPORTS_BODY_SCHEMA
)
RUN_PIVOT_REPORT_BODY_VALIDATOR = Draft202012Validator(RUN_PIVOT_REPORT_BODY_SCHEMA)
RUN_REALTIME_REPORT_BODY_VALIDATOR = Draft202012Validator(
    RUN_REALTIME_REPORT_BODY_SCHEMA
)
CHECK_COMPATIBILITY_BODY_VALIDATOR = Draft202012Validator(
    CHECK_COMPATIBILITY_BODY_SCHEMA
)
CREATE_AUDIENCE_EXPORT_BODY_VALIDATOR = Draft202012Validator(
    CREATE_AUDIENCE_EXPORT_BODY_SCHEMA
)


def _validate_schema(body: Mapping[str, Any], validator: Draft202012Validator) -> None:
    """Raise a normalized validation error for the first schema violation."""
    error = next(validator.iter_errors(body), None)
    if error is None:
        return
    location = ".".join(str(part) for part in error.absolute_path)
    suffix = f" at {location}" if location else ""
    raise RequestValidationError(
        f"--body violates the request schema{suffix}: {error.message}"
    )


def _reject_nonstandard_json_constant(constant: str) -> None:
    """Reject JSON extensions that Python's decoder otherwise accepts."""
    raise ValueError(f"Unsupported JSON constant: {constant}")


def _read_limited_text(source: TextIO) -> str:
    """Read at most one complete bounded request body from a text stream."""
    raw = source.read(MAX_BODY_CHARACTERS + 1)
    if len(raw) > MAX_BODY_CHARACTERS:
        raise RequestValidationError(
            f"--body must not exceed {MAX_BODY_CHARACTERS} characters."
        )
    return raw


def read_json_body(body_source: str, *, stdin: TextIO) -> dict[str, Any]:
    """Read one bounded UTF-8 JSON object from a file path or standard input."""
    try:
        if body_source == "-":
            raw = _read_limited_text(stdin)
        else:
            with Path(body_source).open(encoding="utf-8") as source:
                raw = _read_limited_text(source)
    except (OSError, UnicodeDecodeError) as exc:
        raise RequestValidationError(
            "--body must name a readable UTF-8 JSON file."
        ) from exc

    try:
        body = json.loads(raw, parse_constant=_reject_nonstandard_json_constant)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise RequestValidationError("--body must contain valid JSON.") from exc

    if not isinstance(body, dict):
        raise RequestValidationError("--body must contain a JSON object.")
    return body


def _validate_property(property_name: str) -> None:
    if not PROPERTY_PATTERN.fullmatch(property_name):
        raise RequestValidationError("--property must match properties/<numeric-id>.")


def validate_get_audience_export_request(property_name: str, name: str) -> None:
    """Validate an audience export name belongs to the selected property."""
    _validate_property(property_name)
    if not AUDIENCE_EXPORT_PATTERN.fullmatch(name):
        raise RequestValidationError(
            "--name must match properties/<numeric-id>/audienceExports/<id>."
        )
    if not name.startswith(f"{property_name}/audienceExports/"):
        raise RequestValidationError("--name must belong to --property.")


def validate_query_audience_export_request(
    property_name: str, name: str, limit: int, offset: int
) -> None:
    """Validate one explicitly bounded audience-export user-row query."""
    validate_get_audience_export_request(property_name, name)
    if not 1 <= limit <= 1_000:
        raise RequestValidationError("--limit must be between 1 and 1000.")
    if offset < 0:
        raise RequestValidationError("--offset must be zero or greater.")


def validate_list_audience_exports_request(
    property_name: str, page_size: int, page_token: str | None
) -> None:
    """Validate one explicit audience-export list page request."""
    _validate_property(property_name)
    if not 1 <= page_size <= 1_000:
        raise RequestValidationError("--page-size must be between 1 and 1000.")
    if page_token is not None and not page_token:
        raise RequestValidationError("--page-token must not be empty when supplied.")


def validate_create_audience_export_request(
    property_name: str, body: Mapping[str, Any]
) -> None:
    """Validate a create payload and keep its audience within --property."""
    _validate_property(property_name)
    _validate_schema(body, CREATE_AUDIENCE_EXPORT_BODY_VALIDATOR)
    audience = body["audience"]
    if not AUDIENCE_PATTERN.fullmatch(audience):
        raise RequestValidationError(
            "--body.audience must match properties/<numeric-id>/audiences/<id>."
        )
    if not audience.startswith(f"{property_name}/audiences/"):
        raise RequestValidationError("--body.audience must belong to --property.")


def validate_run_report_request(property_name: str, body: Mapping[str, Any]) -> None:
    """Validate the public `reports run` identifier and JSON request body."""
    _validate_property(property_name)
    _validate_schema(body, RUN_REPORT_BODY_VALIDATOR)


def validate_batch_run_reports_request(
    property_name: str, body: Mapping[str, Any]
) -> None:
    """Validate the public `reports batch-run` identifier and JSON request body."""
    _validate_property(property_name)
    _validate_schema(body, BATCH_RUN_REPORTS_BODY_VALIDATOR)


def validate_batch_run_pivot_reports_request(
    property_name: str, body: Mapping[str, Any]
) -> None:
    """Validate a batch pivot report and every nested pivot report request."""
    _validate_property(property_name)
    _validate_schema(body, BATCH_RUN_PIVOT_REPORTS_BODY_VALIDATOR)
    for request in body["requests"]:
        validate_run_pivot_report_request(property_name, request)


def validate_run_pivot_report_request(
    property_name: str, body: Mapping[str, Any]
) -> None:
    """Validate pivot-only rules that the structural schema cannot express."""
    _validate_property(property_name)
    _validate_schema(body, RUN_PIVOT_REPORT_BODY_VALIDATOR)

    requested_dimensions = body.get("dimensions", [])
    if len(requested_dimensions) > 9:
        raise RequestValidationError("Pivot reports support at most 9 dimensions.")
    date_ranges = body.get("dateRanges", [])
    if len(date_ranges) > 4:
        raise RequestValidationError("Pivot reports support at most 4 dateRanges.")

    dimensions = {dimension["name"] for dimension in requested_dimensions}
    metrics = {metric["name"] for metric in body["metrics"]}
    used_dimensions: set[str] = set()
    pivot_limit_product = 1

    for pivot in body["pivots"]:
        field_names = pivot.get("fieldNames", [])
        if not field_names:
            raise RequestValidationError(
                "Each pivot must name at least one fieldNames dimension."
            )
        for field_name in field_names:
            if field_name != "dateRange" and field_name not in dimensions:
                raise RequestValidationError(
                    f"Pivot fieldNames contains undeclared dimension: {field_name}."
                )
            if field_name != "dateRange" and field_name in used_dimensions:
                raise RequestValidationError(
                    f"A declared dimension cannot appear in more than one pivot: {field_name}."
                )
            if field_name != "dateRange":
                used_dimensions.add(field_name)

        pivot_limit_product *= int(pivot["limit"])
        if pivot_limit_product > 250_000:
            raise RequestValidationError(
                "The product of all pivot limits must not exceed 250000."
            )

        for order_by in pivot.get("orderBys", []):
            dimension_order = order_by.get("dimension")
            if (
                dimension_order
                and dimension_order.get("dimensionName") not in field_names
            ):
                raise RequestValidationError(
                    "Pivot dimension orderBys must reference a fieldNames dimension."
                )
            metric_order = order_by.get("metric")
            if metric_order and metric_order.get("metricName") not in metrics:
                raise RequestValidationError(
                    "Pivot metric orderBys must reference a requested metric."
                )
            pivot_order = order_by.get("pivot")
            if pivot_order and pivot_order.get("metricName") not in metrics:
                raise RequestValidationError(
                    "Pivot selected-pivot orderBys must reference a requested metric."
                )
            if pivot_order:
                for selection in pivot_order.get("pivotSelections", []):
                    if selection.get("dimensionName") not in dimensions:
                        raise RequestValidationError(
                            "Pivot selections must reference a requested dimension."
                        )


def validate_run_realtime_report_request(
    property_name: str, body: Mapping[str, Any]
) -> None:
    """Validate realtime-only API limits before credential lookup."""
    _validate_property(property_name)
    _validate_schema(body, RUN_REALTIME_REPORT_BODY_VALIDATOR)

    if "limit" in body and int(body["limit"]) > 250_000:
        raise RequestValidationError("Realtime report limit must not exceed 250000.")

    for minute_range in body.get("minuteRanges", []):
        start = minute_range.get("startMinutesAgo", 29)
        end = minute_range.get("endMinutesAgo", 0)
        if start < end:
            raise RequestValidationError(
                "Each realtime minuteRange startMinutesAgo must be at least "
                "endMinutesAgo."
            )


def validate_check_compatibility_request(
    property_name: str, body: Mapping[str, Any]
) -> None:
    """Validate a core-report compatibility probe before credential lookup."""
    _validate_property(property_name)
    _validate_schema(body, CHECK_COMPATIBILITY_BODY_VALIDATOR)
