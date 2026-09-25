"""Shared bounded GA4 Admin SDK read and list dispatches."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from google.analytics.admin_v1beta import (
    AnalyticsAdminServiceClient as V1BetaAnalyticsAdminServiceClient,
)
from google.analytics.admin_v1beta.types import Property
from google.api_core import exceptions
from google.auth.credentials import Credentials

from ga4adminctl.foundation.errors import (
    normalize_google_error as _normalize_google_error,
)
from ga4adminctl.foundation.serialization import (
    message_response as _message_response,
)
from marketing_common.auth import CredentialConfigurationError, resolve_credentials


def service_account_credentials(scopes: list[str]) -> Credentials:
    """Compatibility injection seam backed by generic credential resolution."""
    return resolve_credentials(scopes, tool="ga4adminctl")


ANALYTICS_EDIT_SCOPE = "https://www.googleapis.com/auth/analytics.edit"
ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
PROPERTY_READ_TIMEOUT_SECONDS = 20.0

__all__ = [
    "ANALYTICS_EDIT_SCOPE",
    "ANALYTICS_READONLY_SCOPE",
    "PROPERTY_READ_TIMEOUT_SECONDS",
    "PropertiesClient",
    "PropertiesClientFactory",
    "_list_v1beta",
    "_make_properties_client",
    "_normalize_google_error",
    "_read_v1beta",
    "service_account_credentials",
]


class PropertiesClient(Protocol):
    """The bounded official v1beta SDK surface used by Admin operations."""

    def get_property(
        self, request: Any, *, retry: None, timeout: float
    ) -> Property: ...

    def list_properties(self, request: Any, *, retry: None, timeout: float) -> Any: ...


PropertiesClientFactory = Callable[[Credentials], PropertiesClient]


def _make_properties_client(credentials: Credentials) -> PropertiesClient:
    return V1BetaAnalyticsAdminServiceClient(credentials=credentials)


def _read_v1beta(
    request: Any,
    method_name: str,
    response_type: Any,
    *,
    client_factory: PropertiesClientFactory | None = None,
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Call one non-paginated v1beta read and retain protobuf JSON semantics."""
    try:
        credentials = service_account_credentials(
            [ANALYTICS_READONLY_SCOPE] if scopes is None else scopes
        )
        factory = _make_properties_client if client_factory is None else client_factory
        response = getattr(factory(credentials), method_name)(
            request, retry=None, timeout=PROPERTY_READ_TIMEOUT_SECONDS
        )
    except CredentialConfigurationError:
        raise
    except exceptions.GoogleAPICallError as exc:
        raise _normalize_google_error(exc) from exc
    return _message_response(response_type)(response)


def _list_v1beta(
    request: Any,
    method_name: str,
    response_type: Any,
    *,
    client_factory: PropertiesClientFactory | None = None,
    scopes: list[str] | None = None,
) -> dict[str, Any]:
    """Call one v1beta list operation and return only its pager raw page."""
    try:
        credentials = service_account_credentials(
            [ANALYTICS_READONLY_SCOPE] if scopes is None else scopes
        )
        factory = _make_properties_client if client_factory is None else client_factory
        pager = getattr(factory(credentials), method_name)(
            request, retry=None, timeout=PROPERTY_READ_TIMEOUT_SECONDS
        )
    except CredentialConfigurationError:
        raise
    except exceptions.GoogleAPICallError as exc:
        raise _normalize_google_error(exc) from exc
    return _message_response(response_type)(pager.raw_page)
