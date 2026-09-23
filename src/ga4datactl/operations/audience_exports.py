"""Typed GA4 Data audience-export operations."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, Protocol

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    AudienceExport,
    CreateAudienceExportRequest,
    GetAudienceExportRequest,
    ListAudienceExportsRequest,
    QueryAudienceExportRequest,
    QueryAudienceExportResponse,
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
    validate_create_audience_export_request,
    validate_get_audience_export_request,
    validate_list_audience_exports_request,
    validate_query_audience_export_request,
)
from marketing_common.auth import service_account_credentials

ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
ANALYTICS_SCOPE = "https://www.googleapis.com/auth/analytics"
CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS = 20.0
RUN_REPORT_RETRY = Retry(
    predicate=is_retryable_google_error,
    initial=1.0,
    maximum=5.0,
    multiplier=2.0,
    deadline=20.0,
)


class GetAudienceExportClient(Protocol):
    """The official SDK surface used by `audience-exports get`."""

    def get_audience_export(
        self, request: GetAudienceExportRequest, *, retry: Retry
    ) -> AudienceExport: ...


class ListAudienceExportsResponse(Protocol):
    """The first page exposed by the official SDK's audience-export pager."""

    @property
    def audience_exports(self) -> list[AudienceExport]: ...

    @property
    def next_page_token(self) -> str: ...


class ListAudienceExportsClient(Protocol):
    """The official SDK surface used by `audience-exports list`."""

    def list_audience_exports(
        self, request: ListAudienceExportsRequest, *, retry: Retry
    ) -> ListAudienceExportsResponse: ...


class CreateAudienceExportOperation(Protocol):
    """The initiated long-running operation returned by the official SDK."""

    @property
    def operation(self) -> Any: ...


class CreateAudienceExportClient(Protocol):
    """The official SDK surface used by `audience-exports create`."""

    def create_audience_export(
        self, request: CreateAudienceExportRequest, *, retry: Retry, timeout: float
    ) -> CreateAudienceExportOperation: ...


class QueryAudienceExportClient(Protocol):
    """The official SDK surface used by `audience-exports query`."""

    def query_audience_export(
        self, request: QueryAudienceExportRequest, *, retry: Retry
    ) -> QueryAudienceExportResponse: ...


AudienceExportClientFactory = Callable[[Credentials], GetAudienceExportClient]
AudienceExportsClientFactory = Callable[[Credentials], ListAudienceExportsClient]
CreateAudienceExportClientFactory = Callable[[Credentials], CreateAudienceExportClient]
QueryAudienceExportClientFactory = Callable[[Credentials], QueryAudienceExportClient]


def _default_audience_export_client(
    credentials: Credentials,
) -> GetAudienceExportClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_audience_exports_client(
    credentials: Credentials,
) -> ListAudienceExportsClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_create_audience_export_client(
    credentials: Credentials,
) -> CreateAudienceExportClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def _default_query_audience_export_client(
    credentials: Credentials,
) -> QueryAudienceExportClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def get_audience_export(
    property_name: str,
    name: str,
    *,
    client_factory: AudienceExportClientFactory = _default_audience_export_client,
) -> dict[str, Any]:
    """Get one audience export after confirming its property scope."""
    validate_get_audience_export_request(property_name, name)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = GetAudienceExportRequest(name=name)
    try:
        response = client_factory(credentials).get_audience_export(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)


def list_audience_exports(
    property_name: str,
    page_size: int,
    page_token: str | None,
    *,
    client_factory: AudienceExportsClientFactory = _default_audience_exports_client,
) -> dict[str, Any]:
    """List exactly one audience-export page; callers control pagination."""
    validate_list_audience_exports_request(property_name, page_size, page_token)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = ListAudienceExportsRequest(
        parent=property_name, page_size=page_size, page_token=page_token or ""
    )
    try:
        page = client_factory(credentials).list_audience_exports(
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
    property_name: str,
    body: Mapping[str, Any],
    *,
    apply: bool = False,
    client_factory: CreateAudienceExportClientFactory = _default_create_audience_export_client,
) -> dict[str, Any]:
    """Plan or initiate one audience export without polling its operation."""
    validate_create_audience_export_request(property_name, body)
    request_body = {"parent": property_name, "audienceExport": dict(body)}
    if not apply:
        return {"dryRun": True, "request": request_body}
    credentials = service_account_credentials([ANALYTICS_SCOPE])
    request = CreateAudienceExportRequest()
    parse_request(request_body, request)
    try:
        operation = client_factory(credentials).create_audience_export(
            request,
            retry=RUN_REPORT_RETRY,
            timeout=CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS,
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return {"operationName": operation.operation.name}


def query_audience_export(
    property_name: str,
    name: str,
    limit: int,
    offset: int = 0,
    *,
    client_factory: QueryAudienceExportClientFactory = _default_query_audience_export_client,
) -> dict[str, Any]:
    """Return exactly one bounded page of sensitive audience-export user rows."""
    validate_query_audience_export_request(property_name, name, limit, offset)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = QueryAudienceExportRequest(name=name, limit=limit, offset=offset)
    try:
        response = client_factory(credentials).query_audience_export(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)
