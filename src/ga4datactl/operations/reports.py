"""Typed GA4 Data core reporting operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from google.analytics.data_v1beta.types import (
    BatchRunPivotReportsRequest,
    BatchRunReportsRequest,
    CheckCompatibilityRequest,
    RunPivotReportRequest,
    RunRealtimeReportRequest,
    RunReportRequest,
)
from google.api_core import exceptions
from google.api_core.retry import Retry

from ga4datactl.foundation.errors import (
    is_retryable_google_error,
    normalize_google_error,
)
from ga4datactl.foundation.serialization import parse_request, response_to_json
from ga4datactl.foundation.validation import (
    validate_batch_run_pivot_reports_request,
    validate_batch_run_reports_request,
    validate_check_compatibility_request,
    validate_run_pivot_report_request,
    validate_run_realtime_report_request,
    validate_run_report_request,
)
from ga4datactl.operations import transport

RUN_REPORT_RETRY = Retry(
    predicate=is_retryable_google_error,
    initial=1.0,
    maximum=5.0,
    multiplier=2.0,
    deadline=20.0,
)


def run_report(property_name: str, body: Mapping[str, Any]) -> dict[str, Any]:
    """Call the official SDK and preserve its response JSON field names."""
    validate_run_report_request(property_name, body)
    request = RunReportRequest()
    parse_request({"property": property_name, **body}, request)
    credentials = transport.credentials_for_access("read")
    try:
        response = transport.make_client(credentials).run_report(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def batch_run_reports(property_name: str, body: Mapping[str, Any]) -> dict[str, Any]:
    """Call the official SDK for up to five reports and preserve response JSON."""
    validate_batch_run_reports_request(property_name, body)
    request = BatchRunReportsRequest()
    parse_request({"property": property_name, **body}, request)
    credentials = transport.credentials_for_access("read")
    try:
        response = transport.make_client(credentials).batch_run_reports(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def batch_run_pivot_reports(
    property_name: str, body: Mapping[str, Any]
) -> dict[str, Any]:
    """Call the official SDK for up to five pivot reports."""
    validate_batch_run_pivot_reports_request(property_name, body)
    request = BatchRunPivotReportsRequest()
    parse_request({"property": property_name, **body}, request)
    credentials = transport.credentials_for_access("read")
    try:
        response = transport.make_client(credentials).batch_run_pivot_reports(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def run_pivot_report(property_name: str, body: Mapping[str, Any]) -> dict[str, Any]:
    """Call the official SDK for a pivot report and preserve response JSON."""
    validate_run_pivot_report_request(property_name, body)
    request = RunPivotReportRequest()
    parse_request({"property": property_name, **body}, request)
    credentials = transport.credentials_for_access("read")
    try:
        response = transport.make_client(credentials).run_pivot_report(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def run_realtime_report(property_name: str, body: Mapping[str, Any]) -> dict[str, Any]:
    """Call the official SDK to return one GA4 realtime report."""
    validate_run_realtime_report_request(property_name, body)
    request = RunRealtimeReportRequest()
    parse_request({"property": property_name, **body}, request)
    credentials = transport.credentials_for_access("read")
    try:
        response = transport.make_client(credentials).run_realtime_report(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def check_compatibility(property_name: str, body: Mapping[str, Any]) -> dict[str, Any]:
    """Check a candidate core report using the official Data API SDK."""
    validate_check_compatibility_request(property_name, body)
    request = CheckCompatibilityRequest()
    parse_request({"property": property_name, **body}, request)
    credentials = transport.credentials_for_access("read")
    try:
        response = transport.make_client(credentials).check_compatibility(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)
