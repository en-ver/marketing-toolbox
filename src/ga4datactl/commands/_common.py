"""Shared CLI execution helpers for GA4 Data command families."""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping
from typing import Any, NoReturn, cast

from ga4datactl.foundation.errors import GoogleApiError
from ga4datactl.foundation.validation import RequestValidationError, read_json_body
from marketing_common.auth import CredentialConfigurationError
from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.command import execute_with_diagnostics

ReportOperation = Callable[[str, Mapping[str, Any]], dict[str, Any]]
CommandOperation = Callable[[], dict[str, Any]]


def run_command(*, command: str, operation: CommandOperation) -> None:
    """Run one command operation with normalized diagnostics and output."""

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


def run_report_command(
    *, command: str, property_name: str, body_source: str, operation: ReportOperation
) -> None:
    """Run one validated report operation through the common CLI envelope."""

    def operation_with_body() -> dict[str, Any]:
        body = read_json_body(body_source, stdin=sys.stdin)
        return operation(property_name, body)

    run_command(command=command, operation=operation_with_body)
