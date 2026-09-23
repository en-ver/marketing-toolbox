"""Measurement Protocol secret Typer commands."""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Annotated, Any

import typer

from ga4adminctl.foundation.validation import read_json_body
from ga4adminctl.operations.secrets import (
    create_measurement_protocol_secret,
    delete_measurement_protocol_secret,
    get_measurement_protocol_secret,
    list_measurement_protocol_secrets,
    update_measurement_protocol_secret,
)

from ._common import (
    require_exactly_one_mutation_mode,
    require_sensitive_acknowledgement,
    run_command,
)

measurement_protocol_secrets_app = typer.Typer(
    help="Manage acknowledged Measurement Protocol secret metadata through stable Admin API v1beta.",
    no_args_is_help=True,
)


@measurement_protocol_secrets_app.command("get")
def measurement_protocol_secrets_get(
    name: Annotated[
        str, typer.Option("--name", help="Measurement Protocol secret resource name.")
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this response identifies Measurement Protocol secret metadata.",
        ),
    ] = False,
) -> None:
    """Get one acknowledged, sensitive Measurement Protocol secret metadata resource."""
    run_command(
        command="ga4adminctl properties data-streams measurement-protocol-secrets get",
        operation=lambda: _sensitive_secret_read(
            acknowledge_sensitive_data,
            lambda: get_measurement_protocol_secret(name),
        ),
    )


@measurement_protocol_secrets_app.command("list")
def measurement_protocol_secrets_list(
    data_stream: Annotated[
        str,
        typer.Option("--data-stream", help="Parent data-stream resource name."),
    ],
    page_size: Annotated[
        int,
        typer.Option("--page-size", help="Maximum secrets in this one page (1-200)."),
    ] = 50,
    page_token: Annotated[
        str,
        typer.Option(
            "--page-token", help="Continuation token from a prior list response."
        ),
    ] = "",
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this response identifies Measurement Protocol secret metadata.",
        ),
    ] = False,
) -> None:
    """Return exactly one acknowledged, sensitive Measurement Protocol secret page."""
    run_command(
        command="ga4adminctl properties data-streams measurement-protocol-secrets list",
        operation=lambda: _sensitive_secret_read(
            acknowledge_sensitive_data,
            lambda: list_measurement_protocol_secrets(
                data_stream, page_size=page_size, page_token=page_token
            ),
        ),
    )


def _sensitive_secret_read(
    acknowledge_sensitive_data: bool, operation: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    """Refuse sensitive secret-metadata reads before opening credentials."""
    require_sensitive_acknowledgement(acknowledge_sensitive_data)
    return operation()


def _sensitive_secret_action(
    acknowledge_sensitive_data: bool,
    dry_run: bool,
    apply: bool,
    operation: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Require acknowledgement and explicit execution mode before secret actions."""
    require_sensitive_acknowledgement(acknowledge_sensitive_data)
    require_exactly_one_mutation_mode(dry_run, apply)
    return operation()


@measurement_protocol_secrets_app.command("create")
def measurement_protocol_secrets_create(
    data_stream: Annotated[
        str, typer.Option("--data-stream", help="Parent data-stream resource name.")
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
            help="Acknowledge this action creates sensitive credential material.",
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
        typer.Option(
            "--apply", help="Explicitly create this Measurement Protocol secret."
        ),
    ] = False,
) -> None:
    """Create secret metadata with acknowledgement and explicit apply control."""
    run_command(
        command="ga4adminctl properties data-streams measurement-protocol-secrets create",
        operation=lambda: _sensitive_secret_action(
            acknowledge_sensitive_data,
            dry_run,
            apply,
            lambda: create_measurement_protocol_secret(
                data_stream, read_json_body(body_source, stdin=sys.stdin), apply=apply
            ),
        ),
    )


@measurement_protocol_secrets_app.command("patch")
def measurement_protocol_secrets_patch(
    name: Annotated[
        str, typer.Option("--name", help="Measurement Protocol secret resource name.")
    ],
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
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this action changes sensitive credential metadata.",
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
        typer.Option(
            "--apply", help="Explicitly apply this Measurement Protocol secret update."
        ),
    ] = False,
) -> None:
    """Update secret metadata with acknowledgement and exact-mask safeguards."""
    run_command(
        command="ga4adminctl properties data-streams measurement-protocol-secrets patch",
        operation=lambda: _sensitive_secret_action(
            acknowledge_sensitive_data,
            dry_run,
            apply,
            lambda: update_measurement_protocol_secret(
                name,
                read_json_body(body_source, stdin=sys.stdin),
                update_mask,
                apply=apply,
            ),
        ),
    )


@measurement_protocol_secrets_app.command("delete")
def measurement_protocol_secrets_delete(
    name: Annotated[
        str,
        typer.Option(
            "--name", help="Measurement Protocol secret resource name to delete."
        ),
    ],
    acknowledge_sensitive_data: Annotated[
        bool,
        typer.Option(
            "--acknowledge-sensitive-data",
            help="Acknowledge this action irreversibly deletes sensitive credential material.",
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
        typer.Option(
            "--apply", help="Explicitly delete this Measurement Protocol secret."
        ),
    ] = False,
) -> None:
    """Irreversibly delete a secret with acknowledgement and explicit apply control."""
    run_command(
        command="ga4adminctl properties data-streams measurement-protocol-secrets delete",
        operation=lambda: _sensitive_secret_action(
            acknowledge_sensitive_data,
            dry_run,
            apply,
            lambda: delete_measurement_protocol_secret(name, apply=apply),
        ),
    )
