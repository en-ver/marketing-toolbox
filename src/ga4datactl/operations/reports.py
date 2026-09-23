"""Typed GA4 Data core reporting operations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol, TypeAlias

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    BatchRunPivotReportsRequest,
    BatchRunPivotReportsResponse,
    BatchRunReportsRequest,
    BatchRunReportsResponse,
    CheckCompatibilityRequest,
    CheckCompatibilityResponse,
    RunPivotReportRequest,
    RunPivotReportResponse,
    RunRealtimeReportRequest,
    RunRealtimeReportResponse,
    RunReportRequest,
    RunReportResponse,
)
from google.api_core import exceptions
from google.api_core.retry import Retry
from google.oauth2.service_account import Credentials

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
from marketing_common.auth import service_account_credentials

ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"

RUN_REPORT_RETRY = Retry(
    predicate=is_retryable_google_error,
    initial=1.0,
    maximum=5.0,
    multiplier=2.0,
    deadline=20.0,
)


class RunReportClient(Protocol):
    """The narrow official SDK surface used by the `reports run` adapter."""

    def run_report(
        self, request: RunReportRequest, *, retry: Retry
    ) -> RunReportResponse: ...


class BatchRunReportsClient(Protocol):
    """The narrow official SDK surface used by the `reports batch-run` adapter."""

    def batch_run_reports(
        self, request: BatchRunReportsRequest, *, retry: Retry
    ) -> BatchRunReportsResponse: ...


class BatchRunPivotReportsClient(Protocol):
    """The official SDK surface used by `reports batch-pivot-run`."""

    def batch_run_pivot_reports(
        self, request: BatchRunPivotReportsRequest, *, retry: Retry
    ) -> BatchRunPivotReportsResponse: ...


class RunPivotReportClient(Protocol):
    """The narrow official SDK surface used by the `reports pivot-run` adapter."""

    def run_pivot_report(
        self, request: RunPivotReportRequest, *, retry: Retry
    ) -> RunPivotReportResponse: ...


class RunRealtimeReportClient(Protocol):
    """The official SDK surface used by `reports realtime-run`."""

    def run_realtime_report(
        self, request: RunRealtimeReportRequest, *, retry: Retry
    ) -> RunRealtimeReportResponse: ...


class CheckCompatibilityClient(Protocol):
    """The official SDK surface used by the compatibility-check adapter."""

    def check_compatibility(
        self, request: CheckCompatibilityRequest, *, retry: Retry
    ) -> CheckCompatibilityResponse: ...


ClientFactory = Callable[[Credentials], RunReportClient]
BatchClientFactory = Callable[[Credentials], BatchRunReportsClient]
BatchPivotClientFactory = Callable[[Credentials], BatchRunPivotReportsClient]
PivotClientFactory = Callable[[Credentials], RunPivotReportClient]
RealtimeClientFactory = Callable[[Credentials], RunRealtimeReportClient]
CompatibilityClientFactory = Callable[[Credentials], CheckCompatibilityClient]
ReportResponse: TypeAlias = (
    RunReportResponse
    | BatchRunReportsResponse
    | BatchRunPivotReportsResponse
    | RunPivotReportResponse
    | RunRealtimeReportResponse
    | CheckCompatibilityResponse
)


def _default_client(credentials: Credentials) -> RunReportClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_batch_client(credentials: Credentials) -> BatchRunReportsClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_batch_pivot_client(credentials: Credentials) -> BatchRunPivotReportsClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_pivot_client(credentials: Credentials) -> RunPivotReportClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_realtime_client(credentials: Credentials) -> RunRealtimeReportClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_compatibility_client(credentials: Credentials) -> CheckCompatibilityClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def run_report(
    property_name: str,
    body: Mapping[str, Any],
    *,
    client_factory: ClientFactory = _default_client,
) -> dict[str, Any]:
    """Call the official SDK and preserve its response JSON field names."""
    validate_run_report_request(property_name, body)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = RunReportRequest()
    parse_request({"property": property_name, **body}, request)
    try:
        response = client_factory(credentials).run_report(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def batch_run_reports(
    property_name: str,
    body: Mapping[str, Any],
    *,
    client_factory: BatchClientFactory = _default_batch_client,
) -> dict[str, Any]:
    """Call the official SDK for up to five reports and preserve response JSON."""
    validate_batch_run_reports_request(property_name, body)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = BatchRunReportsRequest()
    parse_request({"property": property_name, **body}, request)
    try:
        response = client_factory(credentials).batch_run_reports(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def batch_run_pivot_reports(
    property_name: str,
    body: Mapping[str, Any],
    *,
    client_factory: BatchPivotClientFactory = _default_batch_pivot_client,
) -> dict[str, Any]:
    """Call the official SDK for up to five pivot reports."""
    validate_batch_run_pivot_reports_request(property_name, body)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = BatchRunPivotReportsRequest()
    parse_request({"property": property_name, **body}, request)
    try:
        response = client_factory(credentials).batch_run_pivot_reports(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def run_pivot_report(
    property_name: str,
    body: Mapping[str, Any],
    *,
    client_factory: PivotClientFactory = _default_pivot_client,
) -> dict[str, Any]:
    """Call the official SDK for a pivot report and preserve response JSON."""
    validate_run_pivot_report_request(property_name, body)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = RunPivotReportRequest()
    parse_request({"property": property_name, **body}, request)
    try:
        response = client_factory(credentials).run_pivot_report(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def run_realtime_report(
    property_name: str,
    body: Mapping[str, Any],
    *,
    client_factory: RealtimeClientFactory = _default_realtime_client,
) -> dict[str, Any]:
    """Call the official SDK to return one GA4 realtime report."""
    validate_run_realtime_report_request(property_name, body)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = RunRealtimeReportRequest()
    parse_request({"property": property_name, **body}, request)
    try:
        response = client_factory(credentials).run_realtime_report(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def check_compatibility(
    property_name: str,
    body: Mapping[str, Any],
    *,
    client_factory: CompatibilityClientFactory = _default_compatibility_client,
) -> dict[str, Any]:
    """Check a candidate core report using the official Data API SDK."""
    validate_check_compatibility_request(property_name, body)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = CheckCompatibilityRequest()
    parse_request({"property": property_name, **body}, request)
    try:
        response = client_factory(credentials).check_compatibility(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)
