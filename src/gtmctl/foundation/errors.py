"""Normalized Google Tag Manager API error policy."""

from __future__ import annotations

import ssl

from googleapiclient.errors import HttpError
from httplib2.error import ServerNotFoundError  # type: ignore[import-untyped]


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


def normalize_google_error(error: HttpError) -> GoogleApiError:
    """Map HTTP failures without exposing an upstream diagnostic payload."""
    status = int(error.resp.status)
    if status in {401, 403}:
        exit_code, category = 4, "authentication"
    elif status == 404:
        exit_code, category = 3, "not_found"
    elif status == 400:
        exit_code, category = 2, "invalid_request"
    elif status in {409, 412}:
        exit_code, category = 5, "conflict"
    elif status == 429 or 500 <= status < 600:
        exit_code, category = 6, "retryable"
    else:
        exit_code, category = 1, "unexpected"
    return GoogleApiError(
        exit_code=exit_code,
        category=category,
        message=f"Google Tag Manager API request failed with HTTP {status}.",
        status=status,
    )


def normalize_transport_error(
    error: TimeoutError | ConnectionError | ssl.SSLError | ServerNotFoundError,
) -> GoogleApiError:
    """Normalize known GTM transport failures without exposing their text."""
    return GoogleApiError(
        exit_code=6,
        category="retryable",
        message="Google Tag Manager API network request failed. Retry with bounded backoff.",
    )
