"""Root composition façade for Google Tag Manager API v2 commands."""

from __future__ import annotations

from typing import Annotated

import typer

from gtmctl import __version__
from gtmctl.commands.accounts import accounts_app
from gtmctl.commands.sdk import register_sdk_commands
from marketing_common.cli import make_version_callback, run_typer_application

_version_callback = make_version_callback("gtmctl", __version__)


app = typer.Typer(
    name="gtmctl",
    help="Manage Google Tag Manager through the official Google API v2 client.",
    no_args_is_help=True,
    invoke_without_command=True,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)
app.add_typer(accounts_app, name="accounts")
register_sdk_commands(app)


@app.callback()
def root_callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            help="Show the installed version.",
            is_eager=True,
        ),
    ] = None,
) -> None:
    """A CLI façade for the official Google Tag Manager API v2 client."""


def main() -> None:
    """Run the installed gtmctl console command."""
    run_typer_application(app, command="gtmctl")
