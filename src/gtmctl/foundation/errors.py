"""Normalized Google Tag Manager API error policy."""

from __future__ import annotations

import ssl

from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.errors import HttpError
from httplib2.error import ServerNotFoundError  # type: ignore[import-untyped]
from requests.exceptions import RequestException


class GoogleApiError(RuntimeError):
    """A sanitized error from one official Google API request."""

    def __init__(
        self,
        *,
        exit_code: int,
        category: str,
        message: str,
        status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.category = category
        self.status = status


def _status_category(status: int, *, mutation: bool) -> tuple[int, str]:
    if status in {401, 403}:
        return 4, "authentication"
    if status == 404:
        return 3, "not_found"
    if status == 400:
        return 2, "invalid_request"
    if status in {409, 412}:
        return 5, "conflict"
    if status == 429:
        return 6, "retryable"
    if not mutation and 500 <= status < 600:
        return 6, "retryable"
    return 1, "unexpected"


def normalize_google_error(error: HttpError) -> GoogleApiError:
    """Map GTM read HTTP failures without exposing upstream diagnostics."""
    status = int(error.resp.status)
    exit_code, category = _status_category(status, mutation=False)
    return GoogleApiError(
        exit_code=exit_code,
        category=category,
        message=f"Google Tag Manager API request failed with HTTP {status}.",
        status=status,
    )


def normalize_mutation_google_error(error: HttpError) -> GoogleApiError:
    """Map mutation HTTP failures without implying failed writes are safe to retry."""
    status = int(error.resp.status)
    exit_code, category = _status_category(status, mutation=True)
    message = f"Google Tag Manager API request failed with HTTP {status}."
    if 500 <= status < 600:
        message = (
            "Google Tag Manager mutation may have completed after an HTTP failure. "
            "Inspect the current GTM state before retrying."
        )
    return GoogleApiError(
        exit_code=exit_code,
        category=category,
        message=message,
        status=status,
    )


def unreadable_mutation_response_error() -> GoogleApiError:
    """Report unreadable mutation completion without exposing response details."""
    return GoogleApiError(
        exit_code=1,
        category="unexpected",
        message=(
            "Google Tag Manager mutation may have completed, but its API response "
            "could not be read. Inspect the current GTM state before retrying."
        ),
    )


def normalize_authentication_error(
    error: RefreshError | TransportError,
) -> GoogleApiError:
    """Normalize request-time credential failures without exposing error details."""
    return GoogleApiError(
        exit_code=4,
        category="authentication",
        message="Google Tag Manager API authentication failed.",
    )


def normalize_transport_error(
    error: TimeoutError | ConnectionError | ssl.SSLError | ServerNotFoundError,
) -> GoogleApiError:
    """Normalize known GTM read transport failures without exposing their text."""
    return GoogleApiError(
        exit_code=6,
        category="retryable",
        message="Google Tag Manager API network request failed. Retry with bounded backoff.",
    )


def normalize_mutation_transport_error(error: RequestException) -> GoogleApiError:
    """Report uncertain mutation completion without exposing transport details."""
    return GoogleApiError(
        exit_code=1,
        category="unexpected",
        message=(
            "Google Tag Manager mutation may have completed after a network failure. "
            "Inspect the current GTM state before retrying."
        ),
    )
