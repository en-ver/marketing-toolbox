"""Sensitive GA4 Admin access-report and change-history operations."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from google.analytics.admin_v1beta.types import (
    RunAccessReportRequest,
    RunAccessReportResponse,
    SearchChangeHistoryEventsRequest,
    SearchChangeHistoryEventsResponse,
)
from google.protobuf.json_format import (
    ParseDict,
    ParseError,
)

from ga4adminctl.foundation.validation import (
    ACCOUNT_PATTERN,
    MAX_PROPERTY_PAGE_SIZE,
    RequestValidationError,
    validate_resource_name,
)
from ga4adminctl.operations import reads


def run_access_report(
    entity: str,
    body: Mapping[str, Any],
    *,
    entity_pattern: re.Pattern[str],
) -> dict[str, Any]:
    """Run one acknowledged, read-only Admin access report.

    The route entity is intentionally injected rather than accepted in the
    request body, preventing a body from silently overriding its CLI scope.
    ``ParseDict`` provides the official protobuf JSON boundary and rejects
    unknown request fields before credentials are loaded.
    """
    validate_resource_name(entity, flag="--entity", pattern=entity_pattern)
    if "entity" in body:
        raise RequestValidationError("--body must not contain route field entity.")
    request = RunAccessReportRequest(entity=entity)
    try:
        ParseDict(
            dict(body),
            RunAccessReportRequest.pb(request),
            ignore_unknown_fields=False,
        )
    except (ParseError, TypeError, ValueError) as exc:
        raise RequestValidationError(
            f"--body cannot be converted to a RunAccessReportRequest: {exc}"
        ) from exc
    if len(request.dimensions) > 9:
        raise RequestValidationError(
            "--body permits at most 9 access-report dimensions."
        )
    if len(request.metrics) > 10:
        raise RequestValidationError("--body permits at most 10 access-report metrics.")
    if len(request.date_ranges) > 2:
        raise RequestValidationError(
            "--body permits at most 2 access-report date ranges."
        )
    if "limit" in body and not 1 <= request.limit <= 100_000:
        raise RequestValidationError("--body limit must be between 1 and 100000.")
    if "offset" in body and request.offset < 0:
        raise RequestValidationError("--body offset must be zero or greater.")
    if entity.startswith("accounts/") and request.return_entity_quota:
        raise RequestValidationError(
            "--body returnEntityQuota must be false for an account access report."
        )
    return reads._read_v1beta(request, "run_access_report", RunAccessReportResponse)


def search_change_history_events(
    account: str, body: Mapping[str, Any]
) -> dict[str, Any]:
    """Search acknowledged, sensitive account change history through Admin v1beta.

    The account route is injected from the CLI so a body cannot change the
    account being queried. The API requires the edit scope even though this
    operation is read-only; it makes exactly one bounded SDK call.
    """
    validate_resource_name(account, flag="--account", pattern=ACCOUNT_PATTERN)
    if "account" in body:
        raise RequestValidationError("--body must not contain route field account.")
    request = SearchChangeHistoryEventsRequest(account=account)
    try:
        ParseDict(
            dict(body),
            SearchChangeHistoryEventsRequest.pb(request),
            ignore_unknown_fields=False,
        )
    except (ParseError, TypeError, ValueError) as exc:
        raise RequestValidationError(
            f"--body cannot be converted to a SearchChangeHistoryEventsRequest: {exc}"
        ) from exc
    if "pageSize" in body and not 1 <= request.page_size <= MAX_PROPERTY_PAGE_SIZE:
        raise RequestValidationError(
            f"--body pageSize must be between 1 and {MAX_PROPERTY_PAGE_SIZE}."
        )
    if request.page_token and request.page_token.strip() != request.page_token:
        raise RequestValidationError(
            "--body pageToken must not have leading or trailing whitespace."
        )
    return reads._list_v1beta(
        request,
        "search_change_history_events",
        SearchChangeHistoryEventsResponse,
        scopes=[reads.ANALYTICS_EDIT_SCOPE],
    )
