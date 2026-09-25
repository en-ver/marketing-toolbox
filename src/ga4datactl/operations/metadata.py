"""Typed GA4 Data metadata operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import GetMetadataRequest, Metadata
from google.api_core import exceptions
from google.api_core.retry import Retry
from google.auth.credentials import Credentials

from ga4datactl.foundation.errors import (
    is_retryable_google_error,
    normalize_google_error,
)
from ga4datactl.foundation.serialization import response_to_json
from ga4datactl.foundation.validation import _validate_property
from marketing_common.auth import resolve_credentials


def service_account_credentials(scopes: list[str]) -> Credentials:
    """Compatibility injection seam backed by generic credential resolution."""
    return resolve_credentials(scopes, tool="ga4datactl")


ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
RUN_REPORT_RETRY = Retry(
    predicate=is_retryable_google_error,
    initial=1.0,
    maximum=5.0,
    multiplier=2.0,
    deadline=20.0,
)


class GetMetadataClient(Protocol):
    """The narrow official SDK surface used by the `metadata get` adapter."""

    def get_metadata(
        self, request: GetMetadataRequest, *, retry: Retry
    ) -> Metadata: ...


MetadataClientFactory = Callable[[Credentials], GetMetadataClient]


def _default_metadata_client(credentials: Credentials) -> GetMetadataClient:
    return BetaAnalyticsDataClient(credentials=credentials)


def get_metadata(
    property_name: str,
    *,
    client_factory: MetadataClientFactory = _default_metadata_client,
) -> dict[str, object]:
    """Get the live GA4 vocabulary available to one property."""
    _validate_property(property_name)
    credentials = service_account_credentials([ANALYTICS_READONLY_SCOPE])
    request = GetMetadataRequest(name=f"{property_name}/metadata")
    try:
        response = client_factory(credentials).get_metadata(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)
