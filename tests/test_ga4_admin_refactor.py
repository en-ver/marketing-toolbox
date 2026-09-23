"""Regression coverage for shared GA4 Admin refactor boundaries."""

from __future__ import annotations

from typing import Any, cast

import pytest
from google.analytics.admin_v1beta import types
from typer.testing import CliRunner

from ga4adminctl import cli, service
from ga4adminctl.cli import app
from ga4adminctl.foundation import serialization
from ga4adminctl.operations import mutations, reads


def _record_credential_request(
    requested_scopes: list[str], calls: list[list[str]]
) -> object:
    calls.append(requested_scopes)
    return object()


class AccountReadClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, None, float]] = []

    def get_account(self, request: Any, *, retry: None, timeout: float) -> Any:
        self.calls.append((request, retry, timeout))
        return types.Account(name=request.name, display_name="Example")


class PropertyWriteClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, None, float]] = []

    def create_property(self, request: Any, *, retry: None, timeout: float) -> Any:
        self.calls.append((request, retry, timeout))
        return types.Property(
            name="properties/1234", display_name=request.property.display_name
        )


class CustomDimensionWriteClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, None, float]] = []

    def create_custom_dimension(
        self, request: Any, *, retry: None, timeout: float
    ) -> Any:
        self.calls.append((request, retry, timeout))
        return types.CustomDimension(
            name="properties/1234/customDimensions/1",
            parameter_name=request.custom_dimension.parameter_name,
            display_name=request.custom_dimension.display_name,
            scope=request.custom_dimension.scope,
        )


def test_static_facades_preserve_operation_imports() -> None:
    """Public facade imports remain direct aliases, not mutable dispatch seams."""
    assert service.get_property is cli.get_property
    assert service.provision_account_ticket is cli.provision_account_ticket
    assert (
        service.acknowledge_user_data_collection is cli.acknowledge_user_data_collection
    )
    assert service._write_v1beta is mutations._write_v1beta
    assert not hasattr(reads, "_write_v1beta")


def test_foundation_secret_serialization_redacts_nested_and_top_level_values() -> None:
    payload = {
        "secretValue": "top-level-secret",
        "measurementProtocolSecrets": [
            {"name": "secret-1", "secretValue": "nested-secret"}
        ],
    }

    assert serialization.remove_secret_values(payload) == {
        "measurementProtocolSecrets": [{"name": "secret-1"}]
    }


class OneSensitiveWriteClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any, None, float]] = []

    def create_measurement_protocol_secret(
        self, request: Any, *, retry: None, timeout: float
    ) -> Any:
        self.calls.append(
            ("create_measurement_protocol_secret", request, retry, timeout)
        )
        return types.MeasurementProtocolSecret(
            name="properties/1234/dataStreams/stream-1/measurementProtocolSecrets/secret-1",
            display_name=request.measurement_protocol_secret.display_name,
            secret_value="must-not-be-emitted",
        )


def test_sensitive_write_keeps_one_call_and_redacts_secret_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = OneSensitiveWriteClient()
    credential_calls: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda scopes: _record_credential_request(scopes, credential_calls),
    )

    result = service.create_measurement_protocol_secret(
        "properties/1234/dataStreams/stream-1",
        {"displayName": "Example secret"},
        apply=True,
        client_factory=lambda _: cast(service.PropertiesClient, client),
    )

    assert result == {
        "name": "properties/1234/dataStreams/stream-1/measurementProtocolSecrets/secret-1",
        "displayName": "Example secret",
    }
    assert credential_calls == [[service.ANALYTICS_EDIT_SCOPE]]
    assert len(client.calls) == 1
    method, request, retry, timeout = client.calls[0]
    assert method == "create_measurement_protocol_secret"
    assert request.parent == "properties/1234/dataStreams/stream-1"
    assert request.measurement_protocol_secret.display_name == "Example secret"
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS


class SensitiveAccessReadClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, None, float]] = []

    def search_change_history_events(
        self, request: Any, *, retry: None, timeout: float
    ) -> Any:
        self.calls.append((request, retry, timeout))
        return types.SearchChangeHistoryEventsResponse()


def test_facade_sensitive_access_keeps_edit_scope_and_no_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SensitiveAccessReadClient()
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        reads,
        "service_account_credentials",
        lambda requested: _record_credential_request(requested, scopes),
    )
    monkeypatch.setattr(reads, "_make_properties_client", lambda _: client)

    assert service.search_change_history_events("accounts/1234", {}) == {}
    assert scopes == [[service.ANALYTICS_EDIT_SCOPE]]
    request, retry, timeout = client.calls[0]
    assert request.account == "accounts/1234"
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS


class SensitiveSecretReadClient:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, None, float]] = []

    def get_measurement_protocol_secret(
        self, request: Any, *, retry: None, timeout: float
    ) -> Any:
        self.calls.append((request, retry, timeout))
        return types.MeasurementProtocolSecret(
            name=request.name,
            display_name="Example secret",
            secret_value="must-not-be-emitted",
        )


def test_facade_secret_read_redacts_value_after_typed_non_retried_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SensitiveSecretReadClient()
    monkeypatch.setattr(reads, "service_account_credentials", lambda _: object())
    monkeypatch.setattr(reads, "_make_properties_client", lambda _: client)
    name = "properties/1234/dataStreams/stream-1/measurementProtocolSecrets/secret-1"

    assert service.get_measurement_protocol_secret(name) == {
        "name": name,
        "displayName": "Example secret",
    }
    request, retry, timeout = client.calls[0]
    assert request.name == name
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS


def test_sensitive_mutation_keeps_acknowledgement_before_mode_and_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ga4adminctl.commands.secrets.create_measurement_protocol_secret",
        lambda *_args, **_kwargs: pytest.fail("operation must not be dispatched"),
    )
    command = [
        "properties",
        "data-streams",
        "measurement-protocol-secrets",
        "create",
        "--data-stream",
        "properties/1234/dataStreams/stream-1",
        "--body",
        "/does/not/exist.json",
    ]

    missing_ack = CliRunner().invoke(app, [*command, "--dry-run"])
    assert missing_ack.exit_code == 2
    assert missing_ack.stdout == ""
    assert (
        "--acknowledge-sensitive-data is required for this sensitive read."
        in missing_ack.stderr
    )

    invalid_mode = CliRunner().invoke(app, [*command, "--acknowledge-sensitive-data"])
    assert invalid_mode.exit_code == 2
    assert invalid_mode.stdout == ""
    assert (
        "Specify exactly one of --dry-run or --apply for this mutation."
        in invalid_mode.stderr
    )
