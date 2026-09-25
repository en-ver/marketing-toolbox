"""Reusable Typer authentication command family."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer

from .cli import exit_with_diagnostic, write_success
from .oauth import (
    OAuthAuthenticationError,
    OAuthRequestError,
    ToolName,
    forget_native_credentials,
    login_native_credentials,
    native_marker_exists,
    revoke_native_credentials,
    scope_for_access,
    validate_login_request,
    validate_native_record,
)


def make_auth_app(tool: ToolName) -> typer.Typer:
    """Create the explicitly registered native OAuth command group for a tool."""
    app = typer.Typer(
        help="Manage this tool's local native OAuth credentials.", no_args_is_help=True
    )

    def command(name: str) -> str:
        return f"{tool} auth {name}"

    def fail(name: str, exc: OAuthAuthenticationError) -> NoReturn:
        exit_with_diagnostic(
            exit_code=4,
            category="authentication",
            message=str(exc),
            command=command(name),
        )

    def fail_invalid_request(name: str, exc: OAuthRequestError) -> NoReturn:
        exit_with_diagnostic(
            exit_code=2,
            category="invalid_request",
            message=str(exc),
            command=command(name),
        )

    def validate_access(name: str, access: str) -> str:
        try:
            return scope_for_access(tool, access)
        except OAuthRequestError as exc:
            fail_invalid_request(name, exc)

    @app.command("login")
    def login(
        client_secrets: Annotated[
            Path,
            typer.Option(
                "--client-secrets", exists=True, dir_okay=False, readable=True
            ),
        ],
        access: Annotated[
            str, typer.Option("--access", help="Tool-specific OAuth access tier.")
        ],
        open_browser: Annotated[
            bool, typer.Option("--open-browser/--no-open-browser")
        ] = True,
        port: Annotated[int | None, typer.Option("--port", min=1, max=65535)] = None,
    ) -> None:
        """Authorize one least-privilege installed-app OAuth access tier."""
        try:
            validate_login_request(tool, access, open_browser=open_browser, port=port)
        except OAuthRequestError as exc:
            fail_invalid_request("login", exc)
        try:
            login_native_credentials(
                tool, access, client_secrets, open_browser=open_browser, port=port
            )
        except OAuthAuthenticationError as exc:
            fail("login", exc)
        write_success(command=command("login"), data={"stored": True, "access": access})

    @app.command("status")
    def status(
        access: Annotated[
            str, typer.Option("--access", help="Tool-specific OAuth access tier.")
        ],
    ) -> None:
        """Report local native credential state without contacting Google."""
        scope = validate_access("status", access)
        try:
            stored = native_marker_exists(tool, access)
            if stored:
                validate_native_record(tool, access, scope)
        except OAuthAuthenticationError as exc:
            fail("status", exc)
        write_success(
            command=command("status"), data={"stored": stored, "access": access}
        )

    @app.command("forget")
    def forget(
        access: Annotated[
            str, typer.Option("--access", help="Tool-specific OAuth access tier.")
        ],
    ) -> None:
        """Delete local credentials only without attempting remote revocation."""
        validate_access("forget", access)
        try:
            forget_native_credentials(tool, access)
        except OAuthAuthenticationError as exc:
            fail("forget", exc)
        write_success(
            command=command("forget"),
            data={
                "forgotten": True,
                "access": access,
                "remoteRevocationAttempted": False,
            },
        )

    @app.command("revoke")
    def revoke(
        access: Annotated[
            str, typer.Option("--access", help="Tool-specific OAuth access tier.")
        ],
        apply: Annotated[
            bool, typer.Option("--apply", help="Apply remote grant revocation.")
        ] = False,
        acknowledge_project_wide_revocation: Annotated[
            bool,
            typer.Option(
                "--acknowledge-project-wide-revocation",
                help="Acknowledge revocation affects this user across the OAuth project.",
            ),
        ] = False,
    ) -> None:
        """Revoke the project-wide Google grant and then clean up this local tier."""
        validate_access("revoke", access)
        if not apply or not acknowledge_project_wide_revocation:
            exit_with_diagnostic(
                exit_code=2,
                category="invalid_request",
                message="revoke requires --apply and --acknowledge-project-wide-revocation.",
                command=command("revoke"),
            )
        try:
            revoke_native_credentials(tool, access)
        except OAuthAuthenticationError as exc:
            fail("revoke", exc)
        write_success(
            command=command("revoke"),
            data={
                "revoked": True,
                "access": access,
                "warning": "The project-wide grant was revoked; run auth forget for other affected local tiers.",
            },
        )

    return app
