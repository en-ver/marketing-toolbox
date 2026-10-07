"""GTM credential and Discovery transport."""

from __future__ import annotations

import os
from collections.abc import Mapping
from contextlib import ExitStack
from typing import Any

import httplib2  # type: ignore[import-untyped]
from google.auth.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import Resource, build
from requests.auth import AuthBase
from requests.models import PreparedRequest

from marketing_common.auth import CredentialConfigurationError, resolve_credentials
from marketing_common.oauth import scope_for_access

GTM_MUTATION_TIMEOUT_SECONDS = 60


def credentials_for_access(access: str) -> Credentials:
    """Resolve credentials for one GTM access tier."""
    return resolve_credentials([scope_for_access("gtmctl", access)], tool="gtmctl")


def make_read_service(credentials: Credentials) -> Resource:
    """Create the official Discovery-backed GTM read service."""
    return build("tagmanager", "v2", credentials=credentials, cache_discovery=False)


class _PreserveAuthorization(AuthBase):
    """Prevent netrc replacement without disabling proxy or CA environment support."""

    def __call__(self, request: PreparedRequest) -> PreparedRequest:
        return request


class _DiscoveryAuthorizedSessionHttp:
    """Adapt ``AuthorizedSession`` to Discovery's public httplib2-shaped seam."""

    def __init__(self, credentials: Credentials) -> None:
        self.credentials = credentials
        self._session: Any = AuthorizedSession(  # type: ignore[no-untyped-call]
            credentials, max_refresh_attempts=0
        )
        self._session.auth = _PreserveAuthorization()

    def request(
        self,
        uri: str,
        method: str = "GET",
        body: bytes | str | None = None,
        headers: Mapping[str, str] | None = None,
        redirections: int = 5,
        connection_type: Any = None,
    ) -> tuple[httplib2.Response, bytes]:
        """Make one Discovery request without redirects or transport retries."""
        del redirections, connection_type
        with self._session.request(
            method,
            uri,
            data=body,
            headers=dict(headers) if headers is not None else None,
            timeout=GTM_MUTATION_TIMEOUT_SECONDS,
            allow_redirects=False,
        ) as response:
            content = response.content
            result = httplib2.Response(
                {**dict(response.headers), "status": str(response.status_code)}
            )
            result.reason = "" if response.reason is None else str(response.reason)
        return result, content

    def close(self) -> None:
        """Close API and credential-refresh sessions owned by this adapter."""
        self._session.close()


def _validate_mutation_mtls_environment() -> None:
    """Reject mutation mTLS settings the custom Discovery transport cannot honor."""
    endpoint = os.environ.get("GOOGLE_API_USE_MTLS_ENDPOINT", "auto")
    if endpoint not in {"auto", "never", "always"}:
        raise CredentialConfigurationError(
            "GTM mutation mTLS endpoint configuration is invalid."
        )
    if endpoint == "always":
        raise CredentialConfigurationError(
            "GTM mutations do not support an always-on mTLS endpoint."
        )

    client_certificate = os.environ.get("GOOGLE_API_USE_CLIENT_CERTIFICATE")
    if client_certificate is not None and client_certificate not in {"true", "false"}:
        raise CredentialConfigurationError(
            "GTM mutation client-certificate configuration is invalid."
        )


def make_mutation_service(credentials: Credentials) -> Resource:
    """Build the mutation-only Discovery resource with the bounded adapter."""
    _validate_mutation_mtls_environment()
    http = _DiscoveryAuthorizedSessionHttp(credentials)
    with ExitStack() as cleanup:
        cleanup.callback(http.close)
        service = build("tagmanager", "v2", http=http, cache_discovery=False)
        cleanup.pop_all()
    return service
