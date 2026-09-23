"""CLI execution helpers shared by GTM command families."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NoReturn, cast

from gtmctl.foundation.errors import GoogleApiError
from gtmctl.foundation.validation import RequestValidationError
from marketing_common.auth import CredentialConfigurationError
from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.command import execute_with_diagnostics


def run_command(*, command: str, operation: Callable[[], dict[str, Any]]) -> None:
    """Run one operation and write the repository-standard JSON envelope."""

    def invalid_request(exc: Exception) -> NoReturn:
        exit_with_diagnostic(
            exit_code=2,
            category="invalid_request",
            message=str(exc),
            command=command,
        )

    def authentication(exc: Exception) -> NoReturn:
        exit_with_diagnostic(
            exit_code=4,
            category="authentication",
            message=str(exc),
            command=command,
        )

    def google_api_error(exc: Exception) -> NoReturn:
        error = cast(GoogleApiError, exc)
        exit_with_diagnostic(
            exit_code=error.exit_code,
            category=error.category,
            message=str(error),
            status=error.status,
            command=command,
        )

    data = execute_with_diagnostics(
        operation,
        handlers=(
            (RequestValidationError, invalid_request),
            (CredentialConfigurationError, authentication),
            (GoogleApiError, google_api_error),
        ),
    )
    write_success(command=command, data=data)
