"""Root composition facade for the GA4 Admin command line interface."""
# ruff: noqa: F401

from __future__ import annotations

from typing import Annotated

import typer

from ga4adminctl import __version__
from ga4adminctl.commands import sdk
from ga4adminctl.commands.accounts import account_summaries_app, accounts_app
from ga4adminctl.commands.properties import properties_app
from ga4adminctl.operations.access import (
    run_access_report,
    search_change_history_events,
)
from ga4adminctl.operations.accounts import (
    delete_account,
    get_account,
    list_account_summaries,
    list_accounts,
    provision_account_ticket,
    update_account,
)
from ga4adminctl.operations.properties import (
    acknowledge_user_data_collection,
    create_property,
    delete_property,
    get_data_retention_settings,
    get_data_sharing_settings,
    get_property,
    list_properties,
    update_data_retention_settings,
    update_property,
)
from ga4adminctl.operations.resources import (
    archive_custom_dimension,
    archive_custom_metric,
    create_custom_dimension,
    create_custom_metric,
    create_data_stream,
    create_firebase_link,
    create_google_ads_link,
    create_key_event,
    delete_data_stream,
    delete_firebase_link,
    delete_google_ads_link,
    delete_key_event,
    get_custom_dimension,
    get_custom_metric,
    get_data_stream,
    get_key_event,
    list_custom_dimensions,
    list_custom_metrics,
    list_data_streams,
    list_firebase_links,
    list_google_ads_links,
    list_key_events,
    update_custom_dimension,
    update_custom_metric,
    update_data_stream,
    update_google_ads_link,
    update_key_event,
)
from ga4adminctl.operations.secrets import (
    create_measurement_protocol_secret,
    delete_measurement_protocol_secret,
    get_measurement_protocol_secret,
    list_measurement_protocol_secrets,
    update_measurement_protocol_secret,
)
from marketing_common.cli import make_version_callback, run_typer_application

# Static operation re-exports preserve established direct imports from this root.

app = typer.Typer(
    name="ga4adminctl",
    help="Manage GA4 configuration through the official Analytics Admin API client.",
    no_args_is_help=True,
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)
app.add_typer(account_summaries_app, name="account-summaries")
app.add_typer(accounts_app, name="accounts")
app.add_typer(properties_app, name="properties")
app.add_typer(sdk.app, name="sdk")
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
