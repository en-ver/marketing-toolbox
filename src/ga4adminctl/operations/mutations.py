"""Shared bounded GA4 Admin SDK write dispatch."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from google.api_core import exceptions

from ga4adminctl.operations import reads
from marketing_common.auth import CredentialConfigurationError

# Reuse the existing Admin client and error boundary without making reads own writes.
ANALYTICS_EDIT_SCOPE = reads.ANALYTICS_EDIT_SCOPE
PROPERTY_READ_TIMEOUT_SECONDS = reads.PROPERTY_READ_TIMEOUT_SECONDS
PropertiesClientFactory = reads.PropertiesClientFactory
_make_properties_client = reads._make_properties_client
_normalize_google_error = reads._normalize_google_error
service_account_credentials = reads.service_account_credentials


def _write_v1beta(
    request: Any,
    method_name: str,
    render: Callable[[Any], dict[str, Any]],
    *,
    client_factory: PropertiesClientFactory | None = None,
) -> dict[str, Any]:
    """Call one validated Admin write with its established bounded policy."""
    try:
        credentials = service_account_credentials([ANALYTICS_EDIT_SCOPE])
        factory = _make_properties_client if client_factory is None else client_factory
        response = getattr(factory(credentials), method_name)(
            request, retry=None, timeout=PROPERTY_READ_TIMEOUT_SECONDS
        )
    except CredentialConfigurationError:
        raise
    except exceptions.GoogleAPICallError as exc:
        raise _normalize_google_error(exc) from exc
    return render(response)
