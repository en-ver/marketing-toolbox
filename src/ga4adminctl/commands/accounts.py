"""Account-side GA4 Admin Typer command families."""

from __future__ import annotations

import sys
from typing import Annotated, Any

import typer

from ga4adminctl.foundation.validation import (
    ACCOUNT_PATTERN,
    RequestValidationError,
    read_json_body,
)
from ga4adminctl.operations.accounts import (
    delete_account,
    get_account,
    list_account_summaries,
    list_accounts,
    provision_account_ticket,
    update_account,
)
from ga4adminctl.operations.properties import get_data_sharing_settings

from ._common import (
    require_exactly_one_mutation_mode,
    run_access_report_command,
    run_command,
    search_change_history_command,
)

account_summaries_app = typer.Typer(
    help="Read GA4 account summaries through stable Admin API v1beta.",
    no_args_is_help=True,
)
accounts_app = typer.Typer(
    help="Manage GA4 accounts through stable Admin API v1beta.", no_args_is_help=True
)
account_data_sharing_settings_app = typer.Typer(
    help="Read account data-sharing settings through stable Admin API v1beta.",
    no_args_is_help=True,
)
account_access_reports_app = typer.Typer(
    help="Run acknowledged, sensitive account access reports through stable Admin API v1beta.",
    no_args_is_help=True,
)
account_change_history_app = typer.Typer(
    help="Search acknowledged, sensitive account change history through stable Admin API v1beta.",
    no_args_is_help=True,
)
accounts_app.add_typer(account_data_sharing_settings_app, name="data-sharing-settings")
accounts_app.add_typer(account_access_reports_app, name="access-reports")
accounts_app.add_typer(account_change_history_app, name="change-history")


@account_summaries_app.command("list")
def account_summaries_list(
    page_size: Annotated[
        int,
        typer.Option("--page-size", help="Maximum summaries in this one page (1-200)."),
    ] = 50,
    page_token: Annotated[
        str,
        typer.Option(
            "--page-token", help="Continuation token from a prior list response."
        ),
    ] = "",
) -> None:
    """Return exactly one account-summary page; never auto-paginate."""
    run_command(
        command="ga4adminctl account-summaries list",
        operation=lambda: list_account_summaries(
            page_size=page_size, page_token=page_token
        ),
    )


@accounts_app.command("get")
def accounts_get(
    name: Annotated[
        str, typer.Option("--account", help="Account resource name: accounts/<id>.")
    ],
) -> None:
    """Get one GA4 account through stable Admin API v1beta."""
    run_command(
        command="ga4adminctl accounts get",
        operation=lambda: get_account(name),
    )


@accounts_app.command("list")
def accounts_list(
    page_size: Annotated[
        int,
        typer.Option("--page-size", help="Maximum accounts in this one page (1-200)."),
    ] = 50,
    page_token: Annotated[
        str,
        typer.Option(
            "--page-token", help="Continuation token from a prior list response."
        ),
    ] = "",
    show_deleted: Annotated[
        bool, typer.Option("--show-deleted", help="Include soft-deleted accounts.")
    ] = False,
) -> None:
    """Return exactly one account page; never auto-paginate."""
    run_command(
        command="ga4adminctl accounts list",
        operation=lambda: list_accounts(
            page_size=page_size, page_token=page_token, show_deleted=show_deleted
        ),
    )


@accounts_app.command("delete")
def accounts_delete(
    name: Annotated[
        str, typer.Option("--name", help="Account resource name to delete.")
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly delete this Account.")
    ] = False,
) -> None:
    """Soft-delete one Account with explicit apply control; this is irreversible."""

    def operation() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        return delete_account(name, apply=apply)

    run_command(command="ga4adminctl accounts delete", operation=operation)


@accounts_app.command("provision-account-ticket")
def accounts_provision_account_ticket(
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this creates an account-provisioning ticket.",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option("--apply", help="Explicitly request this provisioning ticket."),
    ] = False,
) -> None:
    """Request a sensitive Account provisioning ticket with explicit controls."""

    def operation() -> dict[str, Any]:
        if not acknowledge_sensitive_data:
            raise RequestValidationError(
                "--acknowledge-sensitive-data is required for this sensitive read."
            )
        require_exactly_one_mutation_mode(dry_run, apply)
        return provision_account_ticket(
            read_json_body(body_source, stdin=sys.stdin), apply=apply
        )

    run_command(
        command="ga4adminctl accounts provision-account-ticket", operation=operation
    )


@accounts_app.command("patch")
def accounts_patch(
    account: Annotated[str, typer.Option("--account", help="Account resource name.")],
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    update_mask: Annotated[
        str,
        typer.Option(
            "--update-mask", help="Comma-separated mutable body fields to update."
        ),
    ],
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Validate and print the request without calling Google."
        ),
    ] = False,
    apply: Annotated[
        bool, typer.Option("--apply", help="Explicitly apply this account update.")
    ] = False,
) -> None:
    """Update bounded Account fields with explicit apply control."""

    def operation() -> dict[str, Any]:
        require_exactly_one_mutation_mode(dry_run, apply)
        return update_account(
            account,
            read_json_body(body_source, stdin=sys.stdin),
            update_mask,
            apply=apply,
        )

    run_command(command="ga4adminctl accounts patch", operation=operation)


@account_data_sharing_settings_app.command("get")
def accounts_data_sharing_settings_get(
    name: Annotated[
        str, typer.Option("--name", help="Data-sharing settings resource name.")
    ],
) -> None:
    """Get one account data-sharing settings resource."""
    run_command(
        command="ga4adminctl accounts data-sharing-settings get",
        operation=lambda: get_data_sharing_settings(name),
    )


@account_access_reports_app.command("run")
def accounts_access_reports_run(
    entity: Annotated[
        str, typer.Option("--entity", help="Account resource name: accounts/<id>.")
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this response can contain access and audit data.",
        ),
    ] = False,
) -> None:
    """Run one sensitive, read-only account access report."""
    run_command(
        command="ga4adminctl accounts access-reports run",
        operation=lambda: run_access_report_command(
            entity=entity,
            body_source=body_source,
            acknowledge_sensitive_data=acknowledge_sensitive_data,
            entity_pattern=ACCOUNT_PATTERN,
        ),
    )


@account_change_history_app.command("search")
def accounts_change_history_search(
    account: Annotated[
        str, typer.Option("--account", help="Account resource name: accounts/<id>.")
    ],
    body_source: Annotated[
        str,
        typer.Option(
            "--body", help="UTF-8 JSON request file, or - for standard input."
        ),
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this response can contain access and audit data.",
        ),
    ] = False,
) -> None:
    """Search sensitive, read-only account change-history events."""
    run_command(
        command="ga4adminctl accounts change-history search",
        operation=lambda: search_change_history_command(
            account=account,
            body_source=body_source,
            acknowledge_sensitive_data=acknowledge_sensitive_data,
        ),
    )
