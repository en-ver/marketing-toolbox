"""Scope and credential wiring contracts for GA4 transports."""

from typing import Any

import pytest

from ga4adminctl.operations import transport as admin_transport
from ga4datactl.operations import transport as data_transport
from marketing_common.oauth import SCOPE_CATALOG


@pytest.mark.parametrize(
    ("transport", "tool", "access"),
    [
        pytest.param(data_transport, "ga4datactl", "read", id="data-read"),
        pytest.param(admin_transport, "ga4adminctl", "read", id="admin-read"),
        pytest.param(admin_transport, "ga4adminctl", "edit", id="admin-edit"),
    ],
)
def test_credentials_for_access_resolves_the_catalogued_single_scope(
    monkeypatch: pytest.MonkeyPatch,
    transport: Any,
    tool: str,
    access: str,
) -> None:
    requests: list[tuple[list[str], str]] = []
    credentials = object()

    monkeypatch.setattr(
        transport,
        "resolve_credentials",
        lambda scopes, *, tool: requests.append((scopes, tool)) or credentials,
    )

    assert transport.credentials_for_access(access) is credentials
    assert requests == [([SCOPE_CATALOG[tool][access]], tool)]
