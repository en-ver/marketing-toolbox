"""Compatibility facade for GA4 Data operation modules.

New code should import a cohesive module from :mod:`ga4datactl.operations`.
This module preserves the former callable import surface as static re-exports.
"""
# ruff: noqa: F401

from __future__ import annotations

from typing import TypeAlias

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    AudienceExport,
    BatchRunPivotReportsRequest,
    BatchRunPivotReportsResponse,
    BatchRunReportsRequest,
    BatchRunReportsResponse,
    CheckCompatibilityRequest,
    CheckCompatibilityResponse,
    CreateAudienceExportRequest,
    GetAudienceExportRequest,
    GetMetadataRequest,
    ListAudienceExportsRequest,
    Metadata,
    QueryAudienceExportRequest,
    QueryAudienceExportResponse,
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

from ga4datactl.foundation.errors import GoogleApiError as _GoogleApiError
from ga4datactl.foundation.errors import is_retryable_google_error
from ga4datactl.foundation.errors import (
    normalize_google_error as _normalize_google_error,
)
from ga4datactl.foundation.serialization import parse_request as _parse_request
from ga4datactl.foundation.serialization import response_to_json as _response_to_json
from ga4datactl.foundation.validation import (
    MAX_BODY_CHARACTERS,
    _validate_property,
    read_json_body,
    validate_batch_run_pivot_reports_request,
    validate_batch_run_reports_request,
    validate_check_compatibility_request,
    validate_create_audience_export_request,
    validate_get_audience_export_request,
    validate_list_audience_exports_request,
    validate_query_audience_export_request,
    validate_run_pivot_report_request,
    validate_run_realtime_report_request,
    validate_run_report_request,
)
from ga4datactl.foundation.validation import (
    RequestValidationError as _RequestValidationError,
)
from ga4datactl.operations import audience_exports as _audience_exports
from ga4datactl.operations import metadata as _metadata
from ga4datactl.operations import reports as _reports
from ga4datactl.operations.audience_exports import (
    AudienceExportClientFactory,
    AudienceExportsClientFactory,
    CreateAudienceExportClient,
    CreateAudienceExportClientFactory,
    CreateAudienceExportOperation,
    GetAudienceExportClient,
    ListAudienceExportsClient,
    ListAudienceExportsResponse,
    QueryAudienceExportClient,
    QueryAudienceExportClientFactory,
    _default_audience_export_client,
    _default_audience_exports_client,
    _default_create_audience_export_client,
    _default_query_audience_export_client,
    create_audience_export,
    get_audience_export,
    list_audience_exports,
    query_audience_export,
)
from ga4datactl.operations.metadata import (
    GetMetadataClient,
    MetadataClientFactory,
    _default_metadata_client,
    get_metadata,
)
from ga4datactl.operations.reports import (
    BatchClientFactory,
    BatchPivotClientFactory,
    BatchRunPivotReportsClient,
    BatchRunReportsClient,
    CheckCompatibilityClient,
    ClientFactory,
    CompatibilityClientFactory,
    PivotClientFactory,
    RealtimeClientFactory,
    RunPivotReportClient,
    RunRealtimeReportClient,
    RunReportClient,
    _default_batch_client,
    _default_batch_pivot_client,
    _default_client,
    _default_compatibility_client,
    _default_pivot_client,
    _default_realtime_client,
    batch_run_pivot_reports,
    batch_run_reports,
    check_compatibility,
    run_pivot_report,
    run_realtime_report,
    run_report,
)
from marketing_common.auth import service_account_credentials

# These names remain explicit compatibility exports.
__all__ = [
    "MAX_BODY_CHARACTERS",
    "GoogleApiError",
    "RequestValidationError",
    "_normalize_google_error",
    "_parse_request",
    "_response_to_json",
    "batch_run_pivot_reports",
    "batch_run_reports",
    "check_compatibility",
    "create_audience_export",
    "get_audience_export",
    "get_metadata",
    "list_audience_exports",
    "query_audience_export",
    "read_json_body",
    "run_pivot_report",
    "run_realtime_report",
    "run_report",
    "validate_create_audience_export_request",
    "validate_query_audience_export_request",
    "validate_run_report_request",
]

# Explicit aliases preserve the legacy service import surface during migration.
GoogleApiError = _GoogleApiError
RequestValidationError = _RequestValidationError
ANALYTICS_READONLY_SCOPE = _reports.ANALYTICS_READONLY_SCOPE
ANALYTICS_SCOPE = _audience_exports.ANALYTICS_SCOPE
CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS = (
    _audience_exports.CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS
)
RUN_REPORT_RETRY = _reports.RUN_REPORT_RETRY
# This legacy alias spans response types now owned by separate operation modules.
ReportResponse: TypeAlias = (
    RunReportResponse
    | BatchRunReportsResponse
    | BatchRunPivotReportsResponse
    | RunPivotReportResponse
    | RunRealtimeReportResponse
    | CheckCompatibilityResponse
    | Metadata
    | QueryAudienceExportResponse
)
