from io import StringIO
from pathlib import Path

import pytest
from google.analytics.admin_v1beta.types import (
    GetPropertyRequest,
    ListPropertiesRequest,
    ListPropertiesResponse,
    Property,
)
from google.api_core import exceptions
from typer.testing import CliRunner

from ga4adminctl.cli import app
from ga4adminctl.commands import properties as admin_properties
from ga4adminctl.foundation import errors as admin_errors
from ga4adminctl.foundation import validation as admin_validation
from ga4adminctl.foundation.errors import normalize_create_mutation_error
from ga4adminctl.operations import accounts, resources, secrets, transport
from ga4adminctl.operations import (
    properties as property_operations,
)


class FailingWriteClient:
    def __init__(self, error: exceptions.GoogleAPICallError) -> None:
        self.error = error
        self.calls: list[tuple[str, object, None, float]] = []

    def __getattr__(self, method_name: str) -> object:
        def call(request: object, *, retry: None, timeout: float) -> object:
            self.calls.append((method_name, request, retry, timeout))
            raise self.error

        return call


def test_read_json_body_rejects_nonstandard_constants() -> None:
    with pytest.raises(admin_validation.RequestValidationError, match="valid JSON"):
        admin_validation.read_json_body("-", stdin=StringIO('{"value": NaN}'))


def test_read_json_body_rejects_non_utf8_file(tmp_path: Path) -> None:
    body = tmp_path / "invalid.json"
    body.write_bytes(b"\xff")

    with pytest.raises(admin_validation.RequestValidationError, match="readable UTF-8"):
        admin_validation.read_json_body(str(body), stdin=StringIO())


def test_read_json_body_bounds_file_reads(tmp_path: Path) -> None:
    body = tmp_path / "oversized.json"
    body.write_text("x" * (admin_validation.MAX_BODY_CHARACTERS + 1), encoding="utf-8")

    with pytest.raises(
        admin_validation.RequestValidationError, match="must not exceed"
    ):
        admin_validation.read_json_body(str(body), stdin=StringIO())


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (
            exceptions.Unauthenticated("expired"),  # type: ignore[no-untyped-call]
            (4, "authentication", 401),
        ),
        (
            exceptions.PermissionDenied("forbidden"),  # type: ignore[no-untyped-call]
            (4, "authentication", 403),
        ),
        (exceptions.NotFound("missing"), (3, "not_found", 404)),  # type: ignore[no-untyped-call]
        (exceptions.ResourceExhausted("quota exceeded"), (6, "retryable", 429)),  # type: ignore[no-untyped-call]
        (exceptions.BadRequest("invalid request"), (2, "invalid_request", 400)),  # type: ignore[no-untyped-call]
        (
            exceptions.FailedPrecondition("precondition"),
            (5, "failed_precondition", 400),
        ),  # type: ignore[no-untyped-call]
        (exceptions.Aborted("conflict"), (5, "conflict", 409)),  # type: ignore[no-untyped-call]
        (exceptions.InternalServerError("unexpected"), (6, "retryable", 500)),  # type: ignore[no-untyped-call]
        (exceptions.ServiceUnavailable("unavailable"), (6, "retryable", 503)),  # type: ignore[no-untyped-call]
    ],
)
def test_normalize_google_error(
    error: exceptions.GoogleAPICallError, expected: tuple[int, str, int]
) -> None:
    normalized = admin_errors.normalize_google_error(error)

    assert (normalized.exit_code, normalized.category, normalized.status) == expected
    assert str(error) not in str(normalized)


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (exceptions.InternalServerError("create-error-sentinel"), 500),  # type: ignore[no-untyped-call]
        (exceptions.ServiceUnavailable("create-error-sentinel"), 503),  # type: ignore[no-untyped-call]
        (exceptions.DeadlineExceeded("create-error-sentinel"), 504),  # type: ignore[no-untyped-call]
    ],
)
def test_normalize_create_mutation_error_reports_uncertain_completion(
    error: exceptions.GoogleAPICallError, status: int
) -> None:
    normalized = normalize_create_mutation_error(error)

    assert (normalized.exit_code, normalized.category, normalized.status) == (
        1,
        "unexpected",
        status,
    )
    assert str(normalized) == (
        "Google Analytics Admin API mutation may have succeeded "
        f"with HTTP {status}. Inspect current state before retrying."
    )
    assert "create-error-sentinel" not in str(normalized)


@pytest.mark.parametrize(
    "error",
    [
        exceptions.BadRequest("definitive-error-sentinel"),  # type: ignore[no-untyped-call]
        exceptions.Aborted("definitive-error-sentinel"),  # type: ignore[no-untyped-call]
    ],
)
def test_normalize_create_mutation_error_preserves_definitive_errors(
    error: exceptions.GoogleAPICallError,
) -> None:
    assert normalize_create_mutation_error(error).__dict__ == (
        admin_errors.normalize_google_error(error).__dict__
    )
    assert str(normalize_create_mutation_error(error)) == str(
        admin_errors.normalize_google_error(error)
    )


_UNCERTAIN_CREATE_CASES = (
    pytest.param(
        lambda: property_operations.create_property({}, apply=True),
        "create_property",
        id="property",
    ),
    pytest.param(
        lambda: resources.create_custom_dimension("properties/1234", {}, apply=True),
        "create_custom_dimension",
        id="custom-dimension",
    ),
    pytest.param(
        lambda: resources.create_custom_metric("properties/1234", {}, apply=True),
        "create_custom_metric",
        id="custom-metric",
    ),
    pytest.param(
        lambda: resources.create_data_stream("properties/1234", {}, apply=True),
        "create_data_stream",
        id="data-stream",
    ),
    pytest.param(
        lambda: resources.create_firebase_link("properties/1234", {}, apply=True),
        "create_firebase_link",
        id="firebase-link",
    ),
    pytest.param(
        lambda: resources.create_google_ads_link("properties/1234", {}, apply=True),
        "create_google_ads_link",
        id="google-ads-link",
    ),
    pytest.param(
        lambda: resources.create_key_event("properties/1234", {}, apply=True),
        "create_key_event",
        id="key-event",
    ),
    pytest.param(
        lambda: secrets.create_measurement_protocol_secret(
            "properties/1234/dataStreams/stream-1", {}, apply=True
        ),
        "create_measurement_protocol_secret",
        id="measurement-protocol-secret",
    ),
    pytest.param(
        lambda: accounts.provision_account_ticket({}, apply=True),
        "provision_account_ticket",
        id="provision-account-ticket",
    ),
)


@pytest.mark.parametrize(("operation", "method_name"), _UNCERTAIN_CREATE_CASES)
def test_create_like_writes_use_uncertain_error_policy_once_without_retry(
    monkeypatch: pytest.MonkeyPatch,
    operation: object,
    method_name: str,
) -> None:
    client = FailingWriteClient(
        exceptions.ServiceUnavailable("write-error-sentinel")  # type: ignore[no-untyped-call]
    )
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())
    monkeypatch.setattr(transport, "make_client", lambda _: client)

    with pytest.raises(admin_errors.GoogleApiError) as raised:
        operation()

    assert len(client.calls) == 1
    actual_method, _request, retry, timeout = client.calls[0]
    assert actual_method == method_name
    assert retry is None
    assert timeout == transport.ADMIN_RPC_TIMEOUT_SECONDS
    error = raised.value
    assert (error.exit_code, error.category, error.status) == (1, "unexpected", 503)
    assert "write-error-sentinel" not in str(error)


def test_non_create_write_and_read_keep_generic_error_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_client = FailingWriteClient(
        exceptions.ServiceUnavailable("non-create-write-sentinel")  # type: ignore[no-untyped-call]
    )
    read_client = FailingWriteClient(
        exceptions.ServiceUnavailable("read-sentinel")  # type: ignore[no-untyped-call]
    )
    clients = iter((write_client, read_client))
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())
    monkeypatch.setattr(transport, "make_client", lambda _: next(clients))

    with pytest.raises(admin_errors.GoogleApiError) as write_raised:
        property_operations.update_property(
            "properties/1234", {"displayName": "Example"}, "displayName", apply=True
        )
    with pytest.raises(admin_errors.GoogleApiError) as read_raised:
        property_operations.get_property("properties/1234")

    for error, sentinel in (
        (write_raised.value, "non-create-write-sentinel"),
        (read_raised.value, "read-sentinel"),
    ):
        assert (error.exit_code, error.category, error.status) == (6, "retryable", 503)
        assert sentinel not in str(error)


def test_uncertain_create_cli_diagnostic_preserves_status_and_redacts_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = "cli-error-sentinel"

    def fail_create(*_: object, **__: object) -> object:
        raise normalize_create_mutation_error(
            exceptions.ServiceUnavailable(sentinel)  # type: ignore[no-untyped-call]
        )

    monkeypatch.setattr(admin_properties, "create_property", fail_create)
    result = CliRunner().invoke(
        app,
        ["properties", "create", "--body", "-", "--apply"],
        input="{}",
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == (
        '{"schemaVersion": "marketing-toolbox/v1", "command": '
        '"ga4adminctl properties create", "exitCode": 1, '
        '"category": "unexpected", "message": '
        '"Google Analytics Admin API mutation may have succeeded with HTTP 503. '
        'Inspect current state before retrying.", "googleStatus": 503}\n'
    )
    assert sentinel not in result.stderr


class CapturingPropertiesClient:
    def __init__(self) -> None:
        self.get_request: GetPropertyRequest | None = None
        self.list_request: ListPropertiesRequest | None = None
        self.retry: object | None = "unset"
        self.timeout: float | None = None

    def get_property(
        self, request: GetPropertyRequest, *, retry: None, timeout: float
    ) -> Property:
        self.get_request = request
        self.retry = retry
        self.timeout = timeout
        return Property(name=request.name, display_name="Example property")

    def list_properties(
        self, request: ListPropertiesRequest, *, retry: None, timeout: float
    ) -> object:
        self.list_request = request
        self.retry = retry
        self.timeout = timeout
        return type(
            "OnePagePager",
            (),
            {
                "raw_page": ListPropertiesResponse(
                    properties=[
                        Property(
                            name="properties/1234", display_name="Example property"
                        )
                    ],
                    next_page_token="next-page",
                )
            },
        )()


def test_get_property_uses_v1beta_read_access_and_raw_sdk_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingPropertiesClient()
    accesses: list[str] = []

    def credentials(access: str) -> object:
        accesses.append(access)
        return object()

    monkeypatch.setattr(transport, "credentials_for_access", credentials)
    monkeypatch.setattr(transport, "make_client", lambda _: client)

    response = property_operations.get_property("properties/1234")

    assert accesses == ["read"]
    assert client.get_request == GetPropertyRequest(name="properties/1234")
    assert client.retry is None
    assert client.timeout == transport.ADMIN_RPC_TIMEOUT_SECONDS
    assert response == {"name": "properties/1234", "displayName": "Example property"}


@pytest.mark.parametrize(
    "filter_expression",
    [
        "parent:accounts/5678",
        "parent:properties/1234",
        "ancestor:accounts/5678",
        "firebase_project:example-project",
        "firebase_project:123456789012",
    ],
)
def test_list_properties_forwards_documented_filters_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    filter_expression: str,
) -> None:
    client = CapturingPropertiesClient()
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())
    monkeypatch.setattr(transport, "make_client", lambda _: client)

    response = property_operations.list_properties(
        filter_expression,
        page_size=25,
        page_token="prior-page",
        show_deleted=True,
    )

    assert client.list_request == ListPropertiesRequest(
        filter=filter_expression,
        page_size=25,
        page_token="prior-page",
        show_deleted=True,
    )
    assert client.retry is None
    assert client.timeout == transport.ADMIN_RPC_TIMEOUT_SECONDS
    assert response == {
        "properties": [{"name": "properties/1234", "displayName": "Example property"}],
        "nextPageToken": "next-page",
    }


@pytest.mark.parametrize(
    "filter_expression",
    [
        "firebase_project:projects/example-project",
        "firebase_project:example-project-",
    ],
)
def test_invalid_property_filters_fail_before_credential_lookup(
    monkeypatch: pytest.MonkeyPatch,
    filter_expression: str,
) -> None:
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda _: pytest.fail("invalid input must not load credentials"),
    )

    with pytest.raises(admin_validation.RequestValidationError, match="--filter"):
        property_operations.list_properties(
            filter_expression,
            page_size=25,
            page_token="",
            show_deleted=False,
        )


@pytest.mark.parametrize(
    ("property_name", "filter_expression", "page_size"),
    [
        ("properties/not-a-number", "parent:accounts/5678", 1),
        ("properties/1234", "accounts/5678", 1),
        ("properties/1234", "parent:accounts/5678", 201),
    ],
)
def test_property_read_validation_happens_before_credential_lookup(
    monkeypatch: pytest.MonkeyPatch,
    property_name: str,
    filter_expression: str,
    page_size: int,
) -> None:
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda _: pytest.fail("invalid input must not load credentials"),
    )

    if property_name != "properties/1234":
        with pytest.raises(admin_validation.RequestValidationError):
            property_operations.get_property(property_name)
    else:
        with pytest.raises(admin_validation.RequestValidationError):
            property_operations.list_properties(
                filter_expression,
                page_size=page_size,
                page_token="",
                show_deleted=False,
            )
