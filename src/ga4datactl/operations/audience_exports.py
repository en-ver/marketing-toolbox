"""Typed GA4 Data audience-export operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from google.analytics.data_v1beta.types import (
    CreateAudienceExportRequest,
    GetAudienceExportRequest,
    ListAudienceExportsRequest,
    QueryAudienceExportRequest,
)
from google.api_core import exceptions
from google.api_core.retry import Retry

from ga4datactl.foundation.errors import (
    is_retryable_google_error,
    normalize_create_audience_export_error,
    normalize_google_error,
)
from ga4datactl.foundation.serialization import parse_request, response_to_json
from ga4datactl.foundation.validation import (
    validate_create_audience_export_request,
    validate_get_audience_export_request,
    validate_list_audience_exports_request,
    validate_query_audience_export_request,
)
from ga4datactl.operations import transport

CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS = 20.0
RUN_REPORT_RETRY = Retry(
    predicate=is_retryable_google_error,
    initial=1.0,
    maximum=5.0,
    multiplier=2.0,
    deadline=20.0,
)


def get_audience_export(property_name: str, name: str) -> dict[str, Any]:
    """Get one audience export after confirming its property scope."""
    validate_get_audience_export_request(property_name, name)
    credentials = transport.credentials_for_access("read")
    request = GetAudienceExportRequest(name=name)
    try:
        response = transport.make_client(credentials).get_audience_export(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def list_audience_exports(
    property_name: str, page_size: int, page_token: str | None
) -> dict[str, Any]:
    """List exactly one audience-export page; callers control pagination."""
    validate_list_audience_exports_request(property_name, page_size, page_token)
    credentials = transport.credentials_for_access("read")
    request = ListAudienceExportsRequest(
        parent=property_name, page_size=page_size, page_token=page_token or ""
    )
    try:
        page = transport.make_client(credentials).list_audience_exports(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return {
        "audienceExports": [
            response_to_json(export) for export in page.audience_exports
        ],
        "nextPageToken": page.next_page_token,
    }


def create_audience_export(
    property_name: str, body: Mapping[str, Any], *, apply: bool = False
) -> dict[str, Any]:
    """Plan or initiate one audience export without polling its operation."""
    validate_create_audience_export_request(property_name, body)
    request_body = {"parent": property_name, "audienceExport": dict(body)}
    if not apply:
        return {"dryRun": True, "request": request_body}
    request = CreateAudienceExportRequest()
    parse_request(request_body, request)
    credentials = transport.credentials_for_access("read")
    try:
        operation = transport.make_client(credentials).create_audience_export(
            request,
            retry=None,
            timeout=CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS,
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_create_audience_export_error(exc) from exc
    return {"operationName": operation.operation.name}


def query_audience_export(
    property_name: str, name: str, limit: int, offset: int = 0
) -> dict[str, Any]:
    """Return exactly one bounded page of sensitive audience-export user rows."""
    validate_query_audience_export_request(property_name, name, limit, offset)
    request = QueryAudienceExportRequest(name=name, limit=limit, offset=offset)
    credentials = transport.credentials_for_access("read")
    try:
        response = transport.make_client(credentials).query_audience_export(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)
