"""CLI entry point for Google Analytics Data API operations."""

from __future__ import annotations

from typing import Annotated

import typer

from ga4datactl import __version__
from ga4datactl.commands import audience_exports, auth, metadata, reports, sdk
from marketing_common.cli import make_version_callback, root_help, run_typer_application

app = typer.Typer(
    name="ga4datactl",
    help=root_help(
        summary="Query Google Analytics 4 reporting data through the official Data API client.",
        guide_url="https://marketing-toolbox.org/tools/ga4-data/",
        api_url="https://developers.google.com/analytics/devguides/reporting/data/v1",
    ),
    no_args_is_help=True,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)
app.add_typer(reports.app, name="reports")
app.add_typer(metadata.app, name="metadata")
app.add_typer(audience_exports.app, name="audience-exports")
app.add_typer(sdk.app, name="sdk")
app.add_typer(auth.app, name="auth")

_version_callback = make_version_callback("ga4datactl", __version__)


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
    """A CLI façade for the official Google Analytics Data API Python client."""


def main() -> None:
    """Run the installed ga4datactl console command."""
    run_typer_application(app, command="ga4datactl")
