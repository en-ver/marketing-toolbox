"""Focused v1beta discovery adapter and command-discovery tests."""

from __future__ import annotations

from typing import Any

import pytest
from google.analytics.admin_v1beta import types
from google.protobuf.empty_pb2 import Empty
from typer.testing import CliRunner

from ga4adminctl import service
from ga4adminctl.cli import app
from ga4adminctl.operations import mutations, reads


def _record_scopes(requested_scopes: list[str], scopes: list[str]) -> object:
    scopes.extend(requested_scopes)
    return object()


class OnePagePager:
    def __init__(self, raw_page: Any) -> None:
        self.raw_page = raw_page

    def __iter__(self) -> Any:
        pytest.fail("discovery list commands must never iterate a pager")


class CapturingDiscoveryClient:
    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, Any, None, float]] = []

    def __getattr__(self, method: str) -> Any:
        def call(request: Any, *, retry: None, timeout: float) -> Any:
            self.calls.append((method, request, retry, timeout))
            response = self.responses[method]
            return OnePagePager(response) if method.startswith("list_") else response

        return call


class CredentialRecorder:
    def __init__(self) -> None:
        self.scopes: list[str] = []

    def __call__(self, scopes: list[str]) -> object:
        self.scopes.extend(scopes)
        return object()


@pytest.fixture
def capturing_client(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Install a client and record the scope used to create it."""

    def install(
        responses: dict[str, Any],
    ) -> tuple[CapturingDiscoveryClient, CredentialRecorder]:
        client = CapturingDiscoveryClient(responses)
        credentials = CredentialRecorder()
        monkeypatch.setattr(reads, "service_account_credentials", credentials)
        monkeypatch.setattr(reads, "_make_properties_client", lambda _: client)
        monkeypatch.setattr(mutations, "service_account_credentials", credentials)
        monkeypatch.setattr(mutations, "_make_properties_client", lambda _: client)
        return client, credentials

    return install


@pytest.fixture
def forbid_credentials(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Fail a test if validation or dry-run code reaches credential lookup."""

    def forbid(message: str) -> None:
        for owner in (reads, mutations):
            monkeypatch.setattr(
                owner,
                "service_account_credentials",
                lambda _: pytest.fail(message),
            )

    return forbid


@pytest.mark.parametrize(
    ("operation", "args", "kwargs"),
    [
        # Resource-name validation, including the nested secret resource shape.
        (service.delete_property, ("properties/not-a-number",), {}),
        (
            service.delete_measurement_protocol_secret,
            ("properties/1234/dataStreams/5678/measurementProtocolSecrets/a/b",),
            {},
        ),
        # The official SDK parser rejects fields outside its protobuf messages.
        (service.create_property, ({"notAnOfficialField": True},), {}),
        (
            service.update_custom_dimension,
            ("properties/1234/customDimensions/5678", {"scope": "EVENT"}, "scope"),
            {},
        ),
        (
            service.update_custom_metric,
            (
                "properties/1234/customMetrics/5678",
                {"parameterName": "immutable"},
                "parameterName",
            ),
            {},
        ),
        (service.provision_account_ticket, ({"notAnOfficialField": True},), {}),
        (
            service.create_measurement_protocol_secret,
            ("properties/1234/dataStreams/5678", {"secretValue": "never-accept"}),
            {},
        ),
        (
            service.acknowledge_user_data_collection,
            ("properties/1234", {"property": "properties/999"}),
            {},
        ),
        # Update-mask exactness and nested body schema are separate mechanisms.
        (
            service.update_data_retention_settings,
            (
                "properties/1234/dataRetentionSettings",
                {"eventDataRetention": "TWO_MONTHS"},
                "name",
            ),
            {},
        ),
        (
            service.update_property,
            ("properties/1234", {"displayName": "Example"}, "displayName,timeZone"),
            {},
        ),
        (
            service.update_data_stream,
            (
                "properties/1234/dataStreams/5678",
                {"webStreamData": {"notAnOfficialField": "bad"}},
                "webStreamData.defaultUri",
            ),
            {},
        ),
        (
            service.update_google_ads_link,
            (
                "properties/1234/googleAdsLinks/5678",
                {"adsPersonalizationEnabled": True},
                "customerId",
            ),
            {},
        ),
        (
            service.update_account,
            ("accounts/1234", {"displayName": "Example"}, "displayName,regionCode"),
            {},
        ),
        (
            service.update_key_event,
            (
                "properties/1234/keyEvents/5678",
                {"countingMethod": "ONCE_PER_EVENT"},
                "defaultValue.numericValue",
            ),
            {},
        ),
        (
            service.update_measurement_protocol_secret,
            (
                "properties/1234/dataStreams/5678/measurementProtocolSecrets/9012",
                {"displayName": "Example"},
                "displayName,secretValue",
            ),
            {},
        ),
        # Read/list validation: bounded pages and request-body routing/schema.
        (service.list_account_summaries, (), {"page_size": 201, "page_token": ""}),
        (
            service.run_access_report,
            ("accounts/123", {"entity": "properties/999"}),
            {"entity_pattern": service.ACCOUNT_PATTERN},
        ),
        (
            service.search_change_history_events,
            ("accounts/123", {"pageToken": " token "}),
            {},
        ),
    ],
)
def test_representative_validation_precedes_credential_lookup(
    forbid_credentials: Any,
    operation: Any,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    forbid_credentials("invalid input must not load credentials")
    with pytest.raises(service.RequestValidationError):
        operation(*args, **kwargs)


@pytest.mark.parametrize(
    ("operation", "args", "method", "request_type", "response"),
    [
        (
            service.list_account_summaries,
            (),
            "list_account_summaries",
            types.ListAccountSummariesRequest,
            types.ListAccountSummariesResponse(next_page_token="next"),
        ),
        (
            service.list_accounts,
            (),
            "list_accounts",
            types.ListAccountsRequest,
            types.ListAccountsResponse(next_page_token="next"),
        ),
        (
            service.get_account,
            ("accounts/1234",),
            "get_account",
            types.GetAccountRequest,
            types.Account(name="accounts/1234"),
        ),
        (
            service.get_data_sharing_settings,
            ("accounts/1234/dataSharingSettings",),
            "get_data_sharing_settings",
            types.GetDataSharingSettingsRequest,
            types.DataSharingSettings(name="accounts/1234/dataSharingSettings"),
        ),
        (
            service.get_data_retention_settings,
            ("properties/1234/dataRetentionSettings",),
            "get_data_retention_settings",
            types.GetDataRetentionSettingsRequest,
            types.DataRetentionSettings(name="properties/1234/dataRetentionSettings"),
        ),
        (
            service.get_data_stream,
            ("properties/1234/dataStreams/5678",),
            "get_data_stream",
            types.GetDataStreamRequest,
            types.DataStream(name="properties/1234/dataStreams/5678"),
        ),
        (
            service.list_data_streams,
            ("properties/1234",),
            "list_data_streams",
            types.ListDataStreamsRequest,
            types.ListDataStreamsResponse(next_page_token="next"),
        ),
        (
            service.get_custom_dimension,
            ("properties/1234/customDimensions/5678",),
            "get_custom_dimension",
            types.GetCustomDimensionRequest,
            types.CustomDimension(name="properties/1234/customDimensions/5678"),
        ),
        (
            service.list_custom_dimensions,
            ("properties/1234",),
            "list_custom_dimensions",
            types.ListCustomDimensionsRequest,
            types.ListCustomDimensionsResponse(next_page_token="next"),
        ),
        (
            service.get_custom_metric,
            ("properties/1234/customMetrics/5678",),
            "get_custom_metric",
            types.GetCustomMetricRequest,
            types.CustomMetric(name="properties/1234/customMetrics/5678"),
        ),
        (
            service.list_custom_metrics,
            ("properties/1234",),
            "list_custom_metrics",
            types.ListCustomMetricsRequest,
            types.ListCustomMetricsResponse(next_page_token="next"),
        ),
        (
            service.list_firebase_links,
            ("properties/1234",),
            "list_firebase_links",
            types.ListFirebaseLinksRequest,
            types.ListFirebaseLinksResponse(next_page_token="next"),
        ),
        (
            service.list_google_ads_links,
            ("properties/1234",),
            "list_google_ads_links",
            types.ListGoogleAdsLinksRequest,
            types.ListGoogleAdsLinksResponse(next_page_token="next"),
        ),
        (
            service.get_key_event,
            ("properties/1234/keyEvents/5678",),
            "get_key_event",
            types.GetKeyEventRequest,
            types.KeyEvent(name="properties/1234/keyEvents/5678"),
        ),
        (
            service.list_key_events,
            ("properties/1234",),
            "list_key_events",
            types.ListKeyEventsRequest,
            types.ListKeyEventsResponse(next_page_token="next"),
        ),
        (
            service.get_measurement_protocol_secret,
            ("properties/1234/dataStreams/5678/measurementProtocolSecrets/9012",),
            "get_measurement_protocol_secret",
            types.GetMeasurementProtocolSecretRequest,
            types.MeasurementProtocolSecret(
                name="properties/1234/dataStreams/5678/measurementProtocolSecrets/9012"
            ),
        ),
        (
            service.list_measurement_protocol_secrets,
            ("properties/1234/dataStreams/5678",),
            "list_measurement_protocol_secrets",
            types.ListMeasurementProtocolSecretsRequest,
            types.ListMeasurementProtocolSecretsResponse(next_page_token="next"),
        ),
    ],
)
def test_v1beta_discovery_operations_use_one_readonly_sdk_call_and_raw_page(
    capturing_client: Any,
    operation: Any,
    args: tuple[str, ...],
    method: str,
    request_type: type[Any],
    response: Any,
) -> None:
    client, credentials = capturing_client({method: response})

    result = (
        operation(*args, page_size=25, page_token="prior")
        if method.startswith("list_")
        else operation(*args)
    )

    assert credentials.scopes == [service.ANALYTICS_READONLY_SCOPE]
    assert len(client.calls) == 1
    actual_method, request, retry, timeout = client.calls[0]
    assert actual_method == method
    assert isinstance(request, request_type)
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS
    assert result.get("nextPageToken", "next") == "next"


def test_list_accounts_passes_show_deleted_and_bounded_page_options(
    capturing_client: Any,
) -> None:
    client, _ = capturing_client({"list_accounts": types.ListAccountsResponse()})

    service.list_accounts(page_size=25, page_token="prior", show_deleted=True)

    request = client.calls[0][1]
    assert request == types.ListAccountsRequest(
        page_size=25, page_token="prior", show_deleted=True
    )


PROPERTY_CREATE_BODY = {
    "parent": "accounts/1234",
    "displayName": "Temporary property",
    "industryCategory": "TECHNOLOGY",
    "timeZone": "America/Los_Angeles",
    "currencyCode": "USD",
}


def test_property_create_and_delete_dry_runs_need_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry runs must not load credentials"),
    )

    assert service.create_property(PROPERTY_CREATE_BODY) == {
        "dryRun": True,
        "request": {"property": PROPERTY_CREATE_BODY},
    }
    assert service.delete_property("properties/5678") == {
        "dryRun": True,
        "request": {"name": "properties/5678"},
    }


def test_property_create_and_delete_apply_once_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingDiscoveryClient(
        {
            "create_property": types.Property(
                name="properties/5678",
                parent="accounts/1234",
                display_name="Temporary property",
                industry_category="TECHNOLOGY",
                time_zone="America/Los_Angeles",
                currency_code="USD",
            ),
            "delete_property": types.Property(name="properties/5678"),
        }
    )
    scopes: list[str] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(mutations, "_make_properties_client", lambda _: client)

    assert service.create_property(PROPERTY_CREATE_BODY, apply=True)["name"] == (
        "properties/5678"
    )
    assert service.delete_property("properties/5678", apply=True) == {
        "name": "properties/5678"
    }
    assert scopes == [service.ANALYTICS_EDIT_SCOPE, service.ANALYTICS_EDIT_SCOPE]
    assert [call[0] for call in client.calls] == [
        "create_property",
        "delete_property",
    ]
    assert client.calls[0][1] == types.CreatePropertyRequest(
        property=types.Property(
            parent="accounts/1234",
            display_name="Temporary property",
            industry_category="TECHNOLOGY",
            time_zone="America/Los_Angeles",
            currency_code="USD",
        )
    )
    assert client.calls[1][1] == types.DeletePropertyRequest(name="properties/5678")
    assert all(call[2] is None for call in client.calls)


CREATE_DELETE_LIFECYCLES = [
    pytest.param(
        service.create_data_stream,
        (
            "properties/1234",
            {
                "displayName": "Temporary stream",
                "webStreamData": {"defaultUri": "https://example.test"},
            },
        ),
        (
            "properties/1234",
            {
                "displayName": "Temporary stream",
                "webStreamData": {"defaultUri": "https://example.test"},
            },
        ),
        service.delete_data_stream,
        "properties/1234/dataStreams/5678",
        {
            "parent": "properties/1234",
            "dataStream": {
                "displayName": "Temporary stream",
                "webStreamData": {"defaultUri": "https://example.test"},
            },
        },
        {
            "create_data_stream": types.DataStream(display_name="Temporary stream"),
            "delete_data_stream": Empty(),
        },
        types.CreateDataStreamRequest(
            parent="properties/1234",
            data_stream=types.DataStream(
                display_name="Temporary stream",
                web_stream_data=types.DataStream.WebStreamData(
                    default_uri="https://example.test"
                ),
            ),
        ),
        types.DeleteDataStreamRequest(name="properties/1234/dataStreams/5678"),
        None,
        id="data-stream",
    ),
    pytest.param(
        service.create_firebase_link,
        ("properties/1234", {"project": "projects/example-project"}),
        ("properties/1234", {"project": "projects/example-project"}),
        service.delete_firebase_link,
        "properties/1234/firebaseLinks/5678",
        {
            "parent": "properties/1234",
            "firebaseLink": {"project": "projects/example-project"},
        },
        {
            "create_firebase_link": types.FirebaseLink(
                project="projects/example-project"
            ),
            "delete_firebase_link": Empty(),
        },
        types.CreateFirebaseLinkRequest(
            parent="properties/1234",
            firebase_link=types.FirebaseLink(project="projects/example-project"),
        ),
        types.DeleteFirebaseLinkRequest(name="properties/1234/firebaseLinks/5678"),
        None,
        id="firebase-link",
    ),
    pytest.param(
        service.create_google_ads_link,
        (
            "properties/1234",
            {"customerId": "1234567890", "adsPersonalizationEnabled": True},
        ),
        ("properties/1234", {"customerId": "1234567890"}),
        service.delete_google_ads_link,
        "properties/1234/googleAdsLinks/5678",
        {
            "parent": "properties/1234",
            "googleAdsLink": {
                "customerId": "1234567890",
                "adsPersonalizationEnabled": True,
            },
        },
        {
            "create_google_ads_link": types.GoogleAdsLink(customer_id="1234567890"),
            "delete_google_ads_link": Empty(),
        },
        types.CreateGoogleAdsLinkRequest(
            parent="properties/1234",
            google_ads_link=types.GoogleAdsLink(customer_id="1234567890"),
        ),
        types.DeleteGoogleAdsLinkRequest(name="properties/1234/googleAdsLinks/5678"),
        None,
        id="google-ads-link",
    ),
    pytest.param(
        service.create_key_event,
        (
            "properties/1234",
            {"eventName": "purchase", "countingMethod": "ONCE_PER_EVENT"},
        ),
        (
            "properties/1234",
            {"eventName": "purchase", "countingMethod": "ONCE_PER_EVENT"},
        ),
        service.delete_key_event,
        "properties/1234/keyEvents/5678",
        {
            "parent": "properties/1234",
            "keyEvent": {"eventName": "purchase", "countingMethod": "ONCE_PER_EVENT"},
        },
        {
            "create_key_event": types.KeyEvent(
                name="properties/1234/keyEvents/5678",
                event_name="purchase",
                counting_method="ONCE_PER_EVENT",
            ),
            "delete_key_event": Empty(),
        },
        types.CreateKeyEventRequest(
            parent="properties/1234",
            key_event=types.KeyEvent(
                event_name="purchase", counting_method="ONCE_PER_EVENT"
            ),
        ),
        types.DeleteKeyEventRequest(name="properties/1234/keyEvents/5678"),
        {
            "name": "properties/1234/keyEvents/5678",
            "eventName": "purchase",
            "countingMethod": "ONCE_PER_EVENT",
        },
        id="key-event",
    ),
]


def test_update_property_dry_run_needs_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry runs must not load credentials"),
    )

    result = service.update_property(
        "properties/1234", {"displayName": "Example"}, "displayName"
    )

    assert result == {
        "dryRun": True,
        "request": {
            "property": {"name": "properties/1234", "displayName": "Example"},
            "updateMask": "displayName",
        },
    }


def test_update_property_uses_one_edit_scoped_non_retried_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingDiscoveryClient(
        {
            "update_property": types.Property(
                name="properties/1234", display_name="Example"
            )
        }
    )
    scopes: list[str] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(mutations, "_make_properties_client", lambda _: client)

    result = service.update_property(
        "properties/1234", {"displayName": "Example"}, "displayName", apply=True
    )

    assert result == {"name": "properties/1234", "displayName": "Example"}
    assert scopes == [service.ANALYTICS_EDIT_SCOPE]
    method, request, retry, timeout = client.calls[0]
    assert method == "update_property"
    assert request == types.UpdatePropertyRequest(
        property=types.Property(name="properties/1234", display_name="Example"),
        update_mask="displayName",
    )
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS


@pytest.mark.parametrize(
    ("entity", "entity_pattern"),
    [
        ("accounts/1234", service.ACCOUNT_PATTERN),
        ("properties/1234", service.PROPERTY_PATTERN),
    ],
)
def test_access_reports_use_one_readonly_sdk_call_and_route_entity(
    monkeypatch: pytest.MonkeyPatch,
    entity: str,
    entity_pattern: Any,
) -> None:
    client = CapturingDiscoveryClient(
        {"run_access_report": types.RunAccessReportResponse()}
    )
    scopes: list[str] = []
    monkeypatch.setattr(
        reads,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(reads, "_make_properties_client", lambda _: client)

    result = service.run_access_report(
        entity,
        {"dimensions": [{"dimensionName": "userEmail"}]},
        entity_pattern=entity_pattern,
    )

    assert result == {}
    assert scopes == [service.ANALYTICS_READONLY_SCOPE]
    assert len(client.calls) == 1
    method, request, retry, timeout = client.calls[0]
    assert method == "run_access_report"
    assert request == types.RunAccessReportRequest(
        entity=entity,
        dimensions=[types.AccessDimension(dimension_name="userEmail")],
    )
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS


def test_change_history_search_uses_one_edit_scoped_sdk_call_and_route_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingDiscoveryClient(
        {
            "search_change_history_events": OnePagePager(
                types.SearchChangeHistoryEventsResponse(next_page_token="next")
            )
        }
    )
    scopes: list[str] = []
    monkeypatch.setattr(
        reads,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(reads, "_make_properties_client", lambda _: client)

    result = service.search_change_history_events(
        "accounts/1234", {"pageSize": 25, "actorEmail": ["user@example.com"]}
    )

    assert result == {"nextPageToken": "next"}
    assert scopes == [service.ANALYTICS_EDIT_SCOPE]
    assert len(client.calls) == 1
    method, request, retry, timeout = client.calls[0]
    assert method == "search_change_history_events"
    assert request == types.SearchChangeHistoryEventsRequest(
        account="accounts/1234", page_size=25, actor_email=["user@example.com"]
    )
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS


def test_change_history_search_command_is_exposed_in_help() -> None:
    result = CliRunner().invoke(app, ["accounts", "change-history", "search", "--help"])
    assert result.exit_code == 0, result.output


@pytest.mark.parametrize(
    "path",
    [
        [
            "accounts",
            "access-reports",
            "run",
            "--entity",
            "accounts/123",
            "--body",
            "missing.json",
        ],
        [
            "properties",
            "access-reports",
            "run",
            "--entity",
            "properties/123",
            "--body",
            "missing.json",
        ],
    ],
)
def test_access_report_commands_require_sensitive_acknowledgement(
    path: list[str],
) -> None:
    result = CliRunner().invoke(app, path)
    assert result.exit_code == 2
    assert "--acknowledge-sensitive-data is required" in result.output


def test_change_history_search_requires_sensitive_acknowledgement() -> None:
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "change-history",
            "search",
            "--account",
            "accounts/123",
            "--body",
            "missing.json",
        ],
    )
    assert result.exit_code == 2
    assert "--acknowledge-sensitive-data is required" in result.output


@pytest.mark.parametrize(
    "path",
    [
        [
            "properties",
            "data-streams",
            "measurement-protocol-secrets",
            "get",
            "--name",
            "properties/123/dataStreams/456/measurementProtocolSecrets/789",
        ],
        [
            "properties",
            "data-streams",
            "measurement-protocol-secrets",
            "list",
            "--data-stream",
            "properties/123/dataStreams/456",
        ],
        [
            "properties",
            "data-streams",
            "measurement-protocol-secrets",
            "create",
            "--data-stream",
            "properties/123/dataStreams/456",
            "--body",
            "-",
            "--dry-run",
        ],
        [
            "properties",
            "data-streams",
            "measurement-protocol-secrets",
            "patch",
            "--name",
            "properties/123/dataStreams/456/measurementProtocolSecrets/789",
            "--body",
            "-",
            "--update-mask",
            "displayName",
            "--dry-run",
        ],
        [
            "properties",
            "data-streams",
            "measurement-protocol-secrets",
            "delete",
            "--name",
            "properties/123/dataStreams/456/measurementProtocolSecrets/789",
            "--dry-run",
        ],
    ],
)
def test_measurement_protocol_secret_commands_require_sensitive_acknowledgement(
    path: list[str],
) -> None:
    result = CliRunner().invoke(app, path, input='{"displayName":"Example"}')
    assert result.exit_code == 2
    assert "--acknowledge-sensitive-data is required" in result.output


def test_measurement_protocol_secret_create_dry_run_is_offline_and_secret_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry runs must not load credentials"),
    )
    assert service.create_measurement_protocol_secret(
        "properties/1234/dataStreams/5678", {"displayName": "Example"}
    ) == {
        "dryRun": True,
        "request": {
            "parent": "properties/1234/dataStreams/5678",
            "measurementProtocolSecret": {"displayName": "Example"},
        },
    }


@pytest.mark.parametrize(
    ("operation", "args", "method", "expected_request"),
    [
        (
            service.create_measurement_protocol_secret,
            ("properties/1234/dataStreams/5678", {"displayName": "Example"}),
            "create_measurement_protocol_secret",
            types.CreateMeasurementProtocolSecretRequest(
                parent="properties/1234/dataStreams/5678",
                measurement_protocol_secret=types.MeasurementProtocolSecret(
                    display_name="Example"
                ),
            ),
        ),
        (
            service.update_measurement_protocol_secret,
            (
                "properties/1234/dataStreams/5678/measurementProtocolSecrets/9012",
                {"displayName": "Example"},
                "displayName",
            ),
            "update_measurement_protocol_secret",
            types.UpdateMeasurementProtocolSecretRequest(
                measurement_protocol_secret=types.MeasurementProtocolSecret(
                    name="properties/1234/dataStreams/5678/measurementProtocolSecrets/9012",
                    display_name="Example",
                ),
                update_mask="displayName",
            ),
        ),
        (
            service.delete_measurement_protocol_secret,
            ("properties/1234/dataStreams/5678/measurementProtocolSecrets/9012",),
            "delete_measurement_protocol_secret",
            types.DeleteMeasurementProtocolSecretRequest(
                name="properties/1234/dataStreams/5678/measurementProtocolSecrets/9012"
            ),
        ),
    ],
)
def test_measurement_protocol_secret_actions_use_one_edit_scoped_non_retried_call(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    method: str,
    expected_request: Any,
) -> None:
    response: Any = (
        Empty()
        if method == "delete_measurement_protocol_secret"
        else types.MeasurementProtocolSecret(display_name="Example")
    )
    client = CapturingDiscoveryClient({method: response})
    scopes: list[str] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(mutations, "_make_properties_client", lambda _: client)

    operation(*args, apply=True)

    assert scopes == [service.ANALYTICS_EDIT_SCOPE]
    assert len(client.calls) == 1
    actual_method, actual_request, retry, timeout = client.calls[0]
    assert actual_method == method
    assert actual_request == expected_request
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS


PROVISION_ACCOUNT_TICKET_BODY = {
    "account": {"displayName": "Example account", "regionCode": "US"},
    "redirectUri": "https://example.test/analytics/tos",
}

USER_DATA_COLLECTION_ACKNOWLEDGEMENT = (
    "I acknowledge that I have the necessary privacy disclosures and rights from "
    "my end users for the collection and processing of their data, including the "
    "association of such data with the visitation information Google Analytics "
    "collects from my site and/or app property."
)
ACKNOWLEDGE_USER_DATA_COLLECTION_BODY = {
    "acknowledgement": USER_DATA_COLLECTION_ACKNOWLEDGEMENT
}


def test_account_delete_and_provision_ticket_dry_runs_need_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry runs must not load credentials"),
    )

    assert service.delete_account("accounts/1234") == {
        "dryRun": True,
        "request": {"name": "accounts/1234"},
    }
    assert service.provision_account_ticket(PROVISION_ACCOUNT_TICKET_BODY) == {
        "dryRun": True,
        "request": PROVISION_ACCOUNT_TICKET_BODY,
    }


def test_account_delete_and_provision_ticket_apply_once_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingDiscoveryClient(
        {
            "delete_account": Empty(),
            "provision_account_ticket": types.ProvisionAccountTicketResponse(
                account_ticket_id="ticket-123"
            ),
        }
    )
    scopes: list[str] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(mutations, "_make_properties_client", lambda _: client)

    assert service.delete_account("accounts/1234", apply=True) == {}
    assert service.provision_account_ticket(
        PROVISION_ACCOUNT_TICKET_BODY, apply=True
    ) == {"accountTicketId": "ticket-123"}
    assert scopes == [service.ANALYTICS_EDIT_SCOPE, service.ANALYTICS_EDIT_SCOPE]
    assert client.calls[0][0] == "delete_account"
    assert client.calls[0][1] == types.DeleteAccountRequest(name="accounts/1234")
    assert client.calls[1][0] == "provision_account_ticket"
    assert client.calls[1][1] == types.ProvisionAccountTicketRequest(
        account=types.Account(display_name="Example account", region_code="US"),
        redirect_uri="https://example.test/analytics/tos",
    )
    assert all(call[2] is None for call in client.calls)


def test_provision_account_ticket_requires_sensitive_acknowledgement(
    tmp_path: Any,
) -> None:
    body = tmp_path / "ticket.json"
    body.write_text('{"not":"loaded without acknowledgement"}', encoding="utf-8")
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "provision-account-ticket",
            "--body",
            str(body),
            "--dry-run",
        ],
    )
    assert result.exit_code == 2
    assert "--acknowledge-sensitive-data is required" in result.output


def test_acknowledge_user_data_collection_dry_run_needs_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry runs must not load credentials"),
    )
    assert service.acknowledge_user_data_collection(
        "properties/1234", ACKNOWLEDGE_USER_DATA_COLLECTION_BODY
    ) == {
        "dryRun": True,
        "request": {
            "property": "properties/1234",
            **ACKNOWLEDGE_USER_DATA_COLLECTION_BODY,
        },
    }


def test_acknowledge_user_data_collection_apply_once_without_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingDiscoveryClient(
        {
            "acknowledge_user_data_collection": (
                types.AcknowledgeUserDataCollectionResponse()
            )
        }
    )
    scopes: list[str] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(mutations, "_make_properties_client", lambda _: client)

    assert (
        service.acknowledge_user_data_collection(
            "properties/1234", ACKNOWLEDGE_USER_DATA_COLLECTION_BODY, apply=True
        )
        == {}
    )
    assert scopes == [service.ANALYTICS_EDIT_SCOPE]
    assert client.calls == [
        (
            "acknowledge_user_data_collection",
            types.AcknowledgeUserDataCollectionRequest(
                property="properties/1234",
                acknowledgement=USER_DATA_COLLECTION_ACKNOWLEDGEMENT,
            ),
            None,
            service.PROPERTY_READ_TIMEOUT_SECONDS,
        )
    ]


def test_acknowledge_user_data_collection_requires_sensitive_acknowledgement(
    tmp_path: Any,
) -> None:
    body = tmp_path / "acknowledgement.json"
    body.write_text('{"not":"opened without acknowledgement"}', encoding="utf-8")
    result = CliRunner().invoke(
        app,
        [
            "properties",
            "acknowledge-user-data-collection",
            "--property",
            "properties/1234",
            "--body",
            str(body),
            "--dry-run",
        ],
    )
    assert result.exit_code == 2
    assert "--acknowledge-sensitive-data is required" in result.output


def test_update_account_dry_run_needs_no_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry runs must not load credentials"),
    )
    assert service.update_account(
        "accounts/1234", {"displayName": "Example"}, "displayName"
    ) == {
        "dryRun": True,
        "request": {
            "account": {"name": "accounts/1234", "displayName": "Example"},
            "updateMask": "displayName",
        },
    }


def test_update_account_uses_one_edit_scoped_non_retried_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingDiscoveryClient(
        {"update_account": types.Account(name="accounts/1234", display_name="Example")}
    )
    scopes: list[str] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda value: _record_scopes(value, scopes),
    )
    monkeypatch.setattr(mutations, "_make_properties_client", lambda _: client)

    result = service.update_account(
        "accounts/1234", {"displayName": "Example"}, "displayName", apply=True
    )

    assert result == {"name": "accounts/1234", "displayName": "Example"}
    assert scopes == [service.ANALYTICS_EDIT_SCOPE]
    method, request, retry, timeout = client.calls[0]
    assert method == "update_account"
    assert request == types.UpdateAccountRequest(
        account=types.Account(name="accounts/1234", display_name="Example"),
        update_mask="displayName",
    )
    assert retry is None
    assert timeout == service.PROPERTY_READ_TIMEOUT_SECONDS
