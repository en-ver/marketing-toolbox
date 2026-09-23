"""Narrow execution primitive shared by marketing CLI command adapters."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, NoReturn

DiagnosticHandler = tuple[type[Exception], Callable[[Exception], NoReturn]]


def execute_with_diagnostics(
    operation: Callable[[], Any], *, handlers: Iterable[DiagnosticHandler]
) -> Any:
    """Execute an operation and dispatch only its declared diagnostic errors.

    Unexpected exceptions are deliberately re-raised so each CLI's outer entry
    point preserves its established failure boundary.
    """
    try:
        return operation()
    except Exception as exc:
        for error_type, handler in handlers:
            if isinstance(exc, error_type):
                handler(exc)
        raise
