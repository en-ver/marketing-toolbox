"""Root composition facade for the GA4 Admin command line interface."""

from __future__ import annotations

from typing import Annotated

import typer

from ga4adminctl import __version__
from ga4adminctl.commands import auth, sdk
from ga4adminctl.commands.accounts import account_summaries_app, accounts_app
from ga4adminctl.commands.properties import properties_app
from marketing_common.cli import make_version_callback, root_help, run_typer_application

app = typer.Typer(
    name="ga4adminctl",
    help=root_help(
        summary="Manage GA4 configuration through the official Analytics Admin API client.",
        guide_url="https://marketing-toolbox.org/tools/ga4-admin/",
        api_url="https://developers.google.com/analytics/devguides/config/admin/v1",
    ),
    no_args_is_help=True,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)
app.add_typer(account_summaries_app, name="account-summaries")
app.add_typer(accounts_app, name="accounts")
app.add_typer(properties_app, name="properties")
app.add_typer(sdk.app, name="sdk")
app.add_typer(auth.app, name="auth")
_version_callback = make_version_callback("ga4adminctl", __version__)


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
    """A CLI façade for the official Google Analytics Admin API Python client."""


def main() -> None:
    """Run the installed ga4adminctl console command."""
    run_typer_application(app, command="ga4adminctl")
