"""GA4 metadata command family."""

from __future__ import annotations

from typing import Annotated

import typer

from ga4datactl.commands._common import run_command
from ga4datactl.operations.metadata import get_metadata

app = typer.Typer(help="Discover live GA4 property metadata.", no_args_is_help=True)


@app.command("get")
def metadata_get(
    property_name: Annotated[
        str,
        typer.Option("--property", help="GA4 property resource name: properties/<id>."),
    ],
) -> None:
    """Return Google’s current dimensions, metrics, and comparisons for a property."""
    run_command(
        command="ga4datactl metadata get",
        operation=lambda: get_metadata(property_name),
    )
