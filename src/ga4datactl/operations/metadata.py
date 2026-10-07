"""Typed GA4 Data metadata operations."""

from __future__ import annotations

from google.analytics.data_v1beta.types import GetMetadataRequest
from google.api_core import exceptions
from google.api_core.retry import Retry

from ga4datactl.foundation.errors import (
    is_retryable_google_error,
    normalize_google_error,
)
from ga4datactl.foundation.serialization import response_to_json
from ga4datactl.foundation.validation import _validate_property
from ga4datactl.operations import transport

RUN_REPORT_RETRY = Retry(
    predicate=is_retryable_google_error,
    initial=1.0,
    maximum=5.0,
    multiplier=2.0,
    deadline=20.0,
)


def get_metadata(property_name: str) -> dict[str, object]:
    """Get the live GA4 vocabulary available to one property."""
    _validate_property(property_name)
    credentials = transport.credentials_for_access("read")
    request = GetMetadataRequest(name=f"{property_name}/metadata")
    try:
        response = transport.make_client(credentials).get_metadata(
            request, retry=RUN_REPORT_RETRY
        )
    except (exceptions.GoogleAPICallError, exceptions.RetryError) as exc:
        raise normalize_google_error(exc) from exc
    return response_to_json(response)
