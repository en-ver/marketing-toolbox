"""Normalized GA4 Data API error policy."""

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


def is_retryable_google_error(error: BaseException) -> bool:
    """Return whether a Google API failure is eligible for bounded retry."""
    return isinstance(
        error, (exceptions.InternalServerError, exceptions.ServiceUnavailable)
    )


def _google_status(error: exceptions.GoogleAPICallError) -> int | None:
    return int(error.code) if error.code is not None else None


def normalize_create_audience_export_error(
    error: exceptions.GoogleAPICallError | exceptions.RetryError,
) -> GoogleApiError:
    """Normalize create failures that could follow a successful submission."""
    source: exceptions.GoogleAPICallError | None
    if isinstance(error, exceptions.RetryError):
        cause = error.cause
        source = cause if isinstance(cause, exceptions.GoogleAPICallError) else None
        if source is None:
            return _uncertain_create_error(status=None)
    else:
        source = error

    status = _google_status(source)
    if status in {500, 503, 504}:
        return _uncertain_create_error(status=status)
    return normalize_google_error(error)


def _uncertain_create_error(*, status: int | None) -> GoogleApiError:
    return GoogleApiError(
        exit_code=1,
        category="unexpected",
        message=(
            "Audience export creation may have succeeded. Inspect audience exports "
            "before retrying."
        ),
        status=status,
    )


def normalize_google_error(
    error: exceptions.GoogleAPICallError | exceptions.RetryError,
) -> GoogleApiError:
    """Map SDK failures without exposing upstream diagnostic text."""
    if isinstance(error, exceptions.RetryError):
        cause = error.cause
        if isinstance(cause, exceptions.GoogleAPICallError):
            return normalize_google_error(cause)
        return GoogleApiError(
            exit_code=6,
            category="retryable",
            message="Google Analytics Data API retry failed. Retry with bounded backoff.",
            status=None,
        )

    status = _google_status(error)
    if isinstance(error, exceptions.FailedPrecondition):
        exit_code, category = 5, "failed_precondition"
    elif status == 400:
        exit_code, category = 2, "invalid_request"
    elif status in {401, 403}:
        exit_code, category = 4, "authentication"
    elif status == 404:
        exit_code, category = 3, "not_found"
    elif status in {409, 412}:
        exit_code, category = 5, "conflict"
    elif status in {429, 500, 503}:
        exit_code, category = 6, "retryable"
    else:
        exit_code, category = 1, "unexpected"
    detail = f" with HTTP {status}" if status is not None else ""
    return GoogleApiError(
        exit_code=exit_code,
        category=category,
        message=f"Google Analytics Data API request failed{detail}.",
        status=status,
    )
