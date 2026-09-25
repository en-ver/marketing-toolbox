"""Shared presentation helpers for the agent-oriented command-line interfaces."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any, NoReturn

import typer

from .typer_compat import NoArgsIsHelpError, UsageError


def success_envelope(*, command: str, data: Any) -> dict[str, Any]:
    """Build the stable JSON success envelope shared by all three CLIs."""
    return {
        "schemaVersion": "marketing-toolbox/v1",
        "command": command,
        "data": data,
    }


def diagnostic_envelope(
    *,
    exit_code: int,
    category: str,
    message: str,
    command: str,
    status: int | None = None,
) -> dict[str, Any]:
    """Build the stable JSON diagnostic envelope shared by all three CLIs."""
    payload: dict[str, Any] = {
        "schemaVersion": "marketing-toolbox/v1",
        "command": command,
        "exitCode": exit_code,
        "category": category,
        "message": message,
    }
    if status is not None:
        payload["googleStatus"] = status
    return payload


def write_success(*, command: str, data: Any) -> None:
    """Write one stable JSON success envelope to standard output."""
    typer.echo(
        json.dumps(success_envelope(command=command, data=data), allow_nan=False)
    )


def exit_with_diagnostic(
    *,
    exit_code: int,
    category: str,
    message: str,
    command: str,
    status: int | None = None,
) -> NoReturn:
    """Write one stable JSON diagnostic to standard error and exit."""
    typer.echo(
        json.dumps(
            diagnostic_envelope(
                exit_code=exit_code,
                category=category,
                message=message,
                command=command,
                status=status,
            ),
            allow_nan=False,
        ),
        err=True,
    )
    raise typer.Exit(code=exit_code)


def exit_not_implemented(command: str) -> None:
    """Write a standard unsupported-command diagnostic and exit with code 2."""
    exit_with_diagnostic(
        exit_code=2,
        category="invalid_request",
        message="SDK-backed implementation is not available yet.",
        command=command,
    )


def make_version_callback(
    command: str, version: str
) -> Callable[[bool | None], bool | None]:
    """Create an eager callback that writes a version success envelope and exits."""

    def version_callback(value: bool | None) -> bool | None:
        if value:
            write_success(command=command, data={"version": version})
            raise typer.Exit()
        return value

    return version_callback


def make_schema_callback(
    command: str, body_schema: Mapping[str, Any]
) -> Callable[[bool | None], bool | None]:
    """Create an eager callback that writes a code-bundled request schema."""

    def schema_callback(value: bool | None) -> bool | None:
        if value:
            write_success(command=command, data={"bodySchema": body_schema})
            raise typer.Exit()
        return value

    return schema_callback


def run_typer_application(app: typer.Typer, *, command: str) -> None:
    """Run a Typer app with its help and JSON diagnostic contracts intact."""
    try:
        exit_code = app(standalone_mode=False, prog_name=command)
        # With standalone mode disabled, Click converts typer.Exit into its code
        # instead of raising it. Propagate nonzero command exits to the console.
        if isinstance(exit_code, int) and exit_code != 0:
            raise SystemExit(exit_code)
    except NoArgsIsHelpError as exc:
        # Typer uses this distinct UsageError subclass for no_args_is_help=True.
        # Preserve its native help rendering instead of converting it to our
        # machine-readable diagnostic used by actual argument parse failures.
        exc.show()
        raise SystemExit(exc.exit_code) from None
    except UsageError as exc:
        typer.echo(
            json.dumps(
                diagnostic_envelope(
                    exit_code=2,
                    category="invalid_arguments",
                    message=str(exc),
                    command=command,
                )
            ),
            err=True,
        )
        raise SystemExit(2) from None
    except typer.Exit as exc:
        raise SystemExit(exc.exit_code) from None
    except Exception:  # noqa: BLE001 - the console boundary normalizes all failures.
        typer.echo(
            json.dumps(
                diagnostic_envelope(
                    exit_code=1,
                    category="unexpected_failure",
                    message="Unexpected CLI failure. Inspect local diagnostics.",
                    command=command,
                )
            ),
            err=True,
        )
        raise SystemExit(1) from None
