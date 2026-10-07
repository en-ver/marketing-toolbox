"""CLI execution helpers shared by GTM command families."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, NoReturn, cast

from gtmctl.foundation.body import body_sha256
from gtmctl.foundation.errors import GoogleApiError
from gtmctl.foundation.validation import RequestValidationError
from marketing_common.auth import CredentialConfigurationError
from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.command import execute_with_diagnostics

DRY_RUN_HELP = (
    "Check local command inputs and print a no-network plan. GTM dry-run does not "
    "validate the body against the Discovery schema, Google API semantics, or any "
    "response schema."
)


def validate_execution_mode(*, dry_run: bool, apply: bool) -> None:
    """Require exactly one mutation execution mode."""
    if dry_run == apply:
        raise RequestValidationError("Specify exactly one of --dry-run or --apply.")


def validate_fingerprint(fingerprint: str | None) -> None:
    """Reject empty or whitespace-padded resource fingerprints."""
    if fingerprint is not None and (
        not fingerprint or fingerprint.strip() != fingerprint
    ):
        raise RequestValidationError(
            "--fingerprint must be a non-empty value without surrounding whitespace."
        )


def build_dry_run_plan(
    *,
    operation: str,
    target: str,
    body: dict[str, Any] | None = None,
    fingerprint: str | None = None,
) -> dict[str, Any]:
    """Produce a deterministic plan without exposing the request body."""
    plan: dict[str, Any] = {
        "applied": False,
        "mode": "dry-run",
        "operation": operation,
        "target": target,
    }
    if fingerprint is not None:
        plan["fingerprint"] = fingerprint
    if body is not None:
        plan["bodySha256"] = body_sha256(body)
    return plan


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
