"""Compatibility exports for the shared CLI JSON presentation contract."""

from __future__ import annotations

from typing import Any, NoReturn

from marketing_common.cli import exit_with_diagnostic as _exit_with_diagnostic
from marketing_common.cli import write_success as _write_success


def write_success(*, command: str, data: Any) -> None:
    """Write the shared success envelope for legacy GTM callers."""
    _write_success(command=command, data=data)


def exit_with_diagnostic(
    *,
    exit_code: int,
    category: str,
    message: str,
    command: str,
    status: int | None = None,
    details: dict[str, Any] | None = None,
) -> NoReturn:
    """Write the shared redacted diagnostic for legacy GTM callers.

    ``details`` remains accepted for compatibility but is intentionally never
    rendered by the public CLI contract.
    """
    del details
    _exit_with_diagnostic(
        exit_code=exit_code,
        category=category,
        message=message,
        command=command,
        status=status,
    )


__all__ = ["exit_with_diagnostic", "write_success"]
