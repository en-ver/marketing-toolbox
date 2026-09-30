"""Normalized GA4 Admin API error policy."""

from __future__ import annotations

from google.api_core import exceptions


class GoogleApiError(RuntimeError):
    """A sanitized error from a Google API call."""

    def __init__(
        self, *, exit_code: int, category: str, message: str, status: int | None
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.category = category
        self.status = status


def normalize_create_mutation_error(
    error: exceptions.GoogleAPICallError,
) -> GoogleApiError:
    """Safely report an uncertain create or provisioning result."""
    status = _google_status(error)
    if status in {500, 503, 504}:
        return GoogleApiError(
            exit_code=1,
            category="unexpected",
            message=(
                "Google Analytics Admin API mutation may have succeeded "
                f"with HTTP {status}. Inspect current state before retrying."
            ),
            status=status,
        )
    return normalize_google_error(error)


def normalize_google_error(error: exceptions.GoogleAPICallError) -> GoogleApiError:
    """Map documented Google API failures without exposing SDK diagnostics."""
    status = _google_status(error)
    if isinstance(error, exceptions.FailedPrecondition):
        exit_code, category = 5, "failed_precondition"
    elif status in {401, 403}:
        exit_code, category = 4, "authentication"
    elif status == 404:
        exit_code, category = 3, "not_found"
    elif status in {409, 412}:
        exit_code, category = 5, "conflict"
    elif status in {429, 500, 503}:
        exit_code, category = 6, "retryable"
    elif status == 400:
        exit_code, category = 2, "invalid_request"
    else:
        exit_code, category = 1, "unexpected"
    detail = f" with HTTP {status}" if status is not None else ""
    return GoogleApiError(
        exit_code=exit_code,
        category=category,
        message=f"Google Analytics Admin API request failed{detail}.",
        status=status,
    )


def _google_status(error: exceptions.GoogleAPICallError) -> int | None:
    return int(error.code) if error.code is not None else None
