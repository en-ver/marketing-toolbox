"""Shared execution and validation helpers for GA4 Admin command modules."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any, NoReturn, cast

from ga4adminctl.foundation.errors import GoogleApiError
from ga4adminctl.foundation.validation import RequestValidationError, read_json_body
from ga4adminctl.operations.access import (
    run_access_report,
    search_change_history_events,
)
from marketing_common.auth import CredentialConfigurationError
from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.command import execute_with_diagnostics


def run_command(*, command: str, operation: Callable[[], dict[str, Any]]) -> None:
    """Write the stable command envelope for one operation."""

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


def require_sensitive_acknowledgement(acknowledged: bool) -> None:
    if not acknowledged:
        raise RequestValidationError(
            "--acknowledge-sensitive-data is required for this sensitive read."
        )


def require_exactly_one_mutation_mode(dry_run: bool, apply: bool) -> None:
    """Enforce the stable mutation-mode diagnostic before reading a body."""
    if dry_run == apply:
        raise RequestValidationError(
            "Specify exactly one of --dry-run or --apply for this mutation."
        )


def run_access_report_command(
    *,
    entity: str,
    body_source: str,
    acknowledge_sensitive_data: bool,
    entity_pattern: Any,
) -> dict[str, Any]:
    """Validate sensitive-read acknowledgement before opening its request body."""
    require_sensitive_acknowledgement(acknowledge_sensitive_data)
    return run_access_report(
        entity,
        read_json_body(body_source, stdin=sys.stdin),
        entity_pattern=entity_pattern,
    )


def search_change_history_command(
    *, account: str, body_source: str, acknowledge_sensitive_data: bool
) -> dict[str, Any]:
    """Validate acknowledgement before loading a sensitive history request."""
    require_sensitive_acknowledgement(acknowledge_sensitive_data)
    return search_change_history_events(
        account, read_json_body(body_source, stdin=sys.stdin)
    )
