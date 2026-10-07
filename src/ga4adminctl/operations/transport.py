"""Shared GA4 Admin credential and bounded SDK transport."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from google.analytics.admin_v1beta import (
    AnalyticsAdminServiceClient as V1BetaAnalyticsAdminServiceClient,
)
from google.api_core import exceptions
from google.auth.credentials import Credentials

from ga4adminctl.foundation.errors import (
    GoogleApiError,
    normalize_create_mutation_error,
    normalize_google_error,
)
from ga4adminctl.foundation.serialization import message_response
from marketing_common.auth import CredentialConfigurationError, resolve_credentials
from marketing_common.oauth import scope_for_access

ADMIN_RPC_TIMEOUT_SECONDS = 20.0

_UNCERTAIN_CREATE_METHODS = frozenset(
    {
        "create_property",
        "create_custom_dimension",
        "create_custom_metric",
        "create_data_stream",
        "create_firebase_link",
        "create_google_ads_link",
        "create_key_event",
        "create_measurement_protocol_secret",
        "provision_account_ticket",
    }
)


def credentials_for_access(access: str) -> Credentials:
    """Resolve credentials for one GA4 Admin access tier."""
    return resolve_credentials(
        [scope_for_access("ga4adminctl", access)], tool="ga4adminctl"
    )


def make_client(credentials: Credentials) -> V1BetaAnalyticsAdminServiceClient:
    """Construct the official GA4 Admin client with resolved credentials."""
    return V1BetaAnalyticsAdminServiceClient(credentials=credentials)


def _invoke(
    request: Any,
    method_name: str,
    *,
    access: str,
    normalize_error: Callable[[exceptions.GoogleAPICallError], GoogleApiError],
) -> Any:
    """Invoke one Admin RPC with its established bounded transport policy."""
    try:
        credentials = credentials_for_access(access)
        return getattr(make_client(credentials), method_name)(
            request, retry=None, timeout=ADMIN_RPC_TIMEOUT_SECONDS
        )
    except CredentialConfigurationError:
        raise
    except exceptions.GoogleAPICallError as exc:
        raise normalize_error(exc) from exc


def read(
    request: Any,
    method_name: str,
    response_type: Any,
    *,
    access: str = "read",
) -> dict[str, Any]:
    """Run one non-paginated Admin read and preserve protobuf JSON semantics."""
    response = _invoke(
        request,
        method_name,
        access=access,
        normalize_error=normalize_google_error,
    )
    return message_response(response_type)(response)


def list_page(
    request: Any,
    method_name: str,
    response_type: Any,
    *,
    access: str = "read",
) -> dict[str, Any]:
    """Run one Admin list RPC and serialize only its pager raw page."""
    pager = _invoke(
        request,
        method_name,
        access=access,
        normalize_error=normalize_google_error,
    )
    return message_response(response_type)(pager.raw_page)


def write(
    request: Any,
    method_name: str,
    render: Callable[[Any], dict[str, Any]],
) -> dict[str, Any]:
    """Run one Admin write with its established uncertain-create policy."""
    normalize_error = (
        normalize_create_mutation_error
        if method_name in _UNCERTAIN_CREATE_METHODS
        else normalize_google_error
    )
    return render(
        _invoke(
            request,
            method_name,
            access="edit",
            normalize_error=normalize_error,
        )
    )
