"""Ordinary GA4 Admin account operations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from google.analytics.admin_v1beta.types import (
    Account,
    DeleteAccountRequest,
    GetAccountRequest,
    ListAccountsRequest,
    ListAccountsResponse,
    ListAccountSummariesRequest,
    ListAccountSummariesResponse,
    ProvisionAccountTicketRequest,
    ProvisionAccountTicketResponse,
    UpdateAccountRequest,
)

from ga4adminctl.foundation.serialization import message_response as _message_response
from ga4adminctl.foundation.validation import (
    ACCOUNT_PATTERN,
    RequestValidationError,
    parse_sdk_message,
    reject_route_fields,
    validate_page_request,
    validate_resource_name,
)
from ga4adminctl.operations import mutations, reads

PropertiesClientFactory = reads.PropertiesClientFactory


def list_account_summaries(*, page_size: int, page_token: str) -> dict[str, Any]:
    validate_page_request(page_size, page_token)
    return reads._list_v1beta(
        ListAccountSummariesRequest(page_size=page_size, page_token=page_token),
        "list_account_summaries",
        ListAccountSummariesResponse,
    )


def get_account(name: str) -> dict[str, Any]:
    validate_resource_name(name, flag="--account", pattern=ACCOUNT_PATTERN)
    return reads._read_v1beta(GetAccountRequest(name=name), "get_account", Account)


def update_account(
    name: str,
    body: Mapping[str, Any],
    update_mask: str,
    *,
    apply: bool = False,
    client_factory: PropertiesClientFactory | None = None,
) -> dict[str, Any]:
    """Plan or apply one bounded, non-retried Account update."""
    validate_resource_name(name, flag="--account", pattern=ACCOUNT_PATTERN)
    reject_route_fields(body, "name")
    account = parse_sdk_message(body, Account)
    account.name = name
    mutable_fields = {"displayName", "regionCode"}
    mask_fields = update_mask.split(",") if update_mask else []
    if (
        not mask_fields
        or any(not field or field.strip() != field for field in mask_fields)
        or len(set(mask_fields)) != len(mask_fields)
        or not set(mask_fields).issubset(mutable_fields)
    ):
        raise RequestValidationError(
            "--update-mask must be a nonempty, comma-separated set of mutable body fields."
        )
    if set(mask_fields) != set(body):
        raise RequestValidationError(
            "--update-mask fields must match --body fields exactly."
        )
    if not apply:
        return {
            "dryRun": True,
            "request": {
                "account": {"name": name, **dict(body)},
                "updateMask": update_mask,
            },
        }
    request = UpdateAccountRequest(account=account, update_mask=update_mask)
    return mutations._write_v1beta(
        request,
        "update_account",
        _message_response(Account),
        client_factory=client_factory,
    )


def provision_account_ticket(
    body: Mapping[str, Any],
    *,
    apply: bool = False,
    client_factory: PropertiesClientFactory | None = None,
) -> dict[str, Any]:
    """Plan or request one sensitive account-provisioning ticket once."""
    request = parse_sdk_message(body, ProvisionAccountTicketRequest)
    if not apply:
        return {"dryRun": True, "request": dict(body)}
    return mutations._write_v1beta(
        request,
        "provision_account_ticket",
        _message_response(ProvisionAccountTicketResponse),
        client_factory=client_factory,
    )


def delete_account(
    name: str,
    *,
    apply: bool = False,
    client_factory: PropertiesClientFactory | None = None,
) -> dict[str, Any]:
    """Plan or soft-delete one Account without live validation or retry."""
    validate_resource_name(name, flag="--name", pattern=ACCOUNT_PATTERN)
    if not apply:
        return {"dryRun": True, "request": {"name": name}}
    return mutations._write_v1beta(
        DeleteAccountRequest(name=name),
        "delete_account",
        lambda _: {},
        client_factory=client_factory,
    )


def list_accounts(
    *, page_size: int, page_token: str, show_deleted: bool = False
) -> dict[str, Any]:
    validate_page_request(page_size, page_token)
    return reads._list_v1beta(
        ListAccountsRequest(
            page_size=page_size, page_token=page_token, show_deleted=show_deleted
        ),
        "list_accounts",
        ListAccountsResponse,
    )
