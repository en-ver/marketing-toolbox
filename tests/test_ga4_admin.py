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

from ga4adminctl import service as ga4_admin
from ga4adminctl.cli import app
from ga4adminctl.commands import properties as admin_properties
from ga4adminctl.foundation.errors import normalize_create_mutation_error
from ga4adminctl.operations import mutations, reads

_UNCERTAIN_CREATE_METHODS = (
    "create_property",
    "create_custom_dimension",
    "create_custom_metric",
    "create_data_stream",
    "create_firebase_link",
    "create_google_ads_link",
    "create_key_event",
    "create_measurement_protocol_secret",
    "provision_account_ticket",
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
    with pytest.raises(ga4_admin.RequestValidationError, match="valid JSON"):
        ga4_admin.read_json_body("-", stdin=StringIO('{"value": NaN}'))


def test_read_json_body_rejects_non_utf8_file(tmp_path: Path) -> None:
    body = tmp_path / "invalid.json"
    body.write_bytes(b"\xff")

    with pytest.raises(ga4_admin.RequestValidationError, match="readable UTF-8"):
        ga4_admin.read_json_body(str(body), stdin=StringIO())


def test_read_json_body_bounds_file_reads(tmp_path: Path) -> None:
    body = tmp_path / "oversized.json"
    body.write_text("x" * (ga4_admin.MAX_BODY_CHARACTERS + 1), encoding="utf-8")

    with pytest.raises(ga4_admin.RequestValidationError, match="must not exceed"):
        ga4_admin.read_json_body(str(body), stdin=StringIO())


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
    normalized = ga4_admin._normalize_google_error(error)

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
        ga4_admin._normalize_google_error(error).__dict__
    )
    assert str(normalize_create_mutation_error(error)) == str(
        ga4_admin._normalize_google_error(error)
    )


@pytest.mark.parametrize("method_name", _UNCERTAIN_CREATE_METHODS)
def test_create_like_writes_use_uncertain_error_policy_once_without_retry(
    monkeypatch: pytest.MonkeyPatch, method_name: str
) -> None:
    request = object()
    client = FailingWriteClient(
        exceptions.ServiceUnavailable("write-error-sentinel")  # type: ignore[no-untyped-call]
    )
    monkeypatch.setattr(mutations, "service_account_credentials", lambda _: object())

    with pytest.raises(ga4_admin.GoogleApiError) as raised:
        mutations._write_v1beta(
            request,
            method_name,
            lambda _: {},
            client_factory=lambda _: client,
        )

    assert mutations._UNCERTAIN_CREATE_METHODS == frozenset(_UNCERTAIN_CREATE_METHODS)
    assert client.calls == [
        (method_name, request, None, ga4_admin.PROPERTY_READ_TIMEOUT_SECONDS)
    ]
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
    monkeypatch.setattr(mutations, "service_account_credentials", lambda _: object())
    monkeypatch.setattr(reads, "service_account_credentials", lambda _: object())

    with pytest.raises(ga4_admin.GoogleApiError) as write_raised:
        mutations._write_v1beta(
            object(),
            "update_property",
            lambda _: {},
            client_factory=lambda _: write_client,
        )
    with pytest.raises(ga4_admin.GoogleApiError) as read_raised:
        reads._read_v1beta(
            GetPropertyRequest(name="properties/1234"),
            "get_property",
            Property,
            client_factory=lambda _: read_client,
        )

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


def test_get_property_uses_v1beta_readonly_scope_and_raw_sdk_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingPropertiesClient()
    scopes: list[str] = []

    def credentials(value: list[str]) -> object:
        scopes.extend(value)
        return object()

    monkeypatch.setattr(reads, "service_account_credentials", credentials)

    response = ga4_admin.get_property(
        "properties/1234", client_factory=lambda _: client
    )

    assert scopes == [ga4_admin.ANALYTICS_READONLY_SCOPE]
    assert client.get_request == GetPropertyRequest(name="properties/1234")
    assert client.retry is None
    assert client.timeout == ga4_admin.PROPERTY_READ_TIMEOUT_SECONDS
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
    monkeypatch.setattr(reads, "service_account_credentials", lambda _: object())

    response = ga4_admin.list_properties(
        filter_expression,
        page_size=25,
        page_token="prior-page",
        show_deleted=True,
        client_factory=lambda _: client,
    )

    assert client.list_request == ListPropertiesRequest(
        filter=filter_expression,
        page_size=25,
        page_token="prior-page",
        show_deleted=True,
    )
    assert client.retry is None
    assert client.timeout == ga4_admin.PROPERTY_READ_TIMEOUT_SECONDS
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
        reads,
        "service_account_credentials",
        lambda _: pytest.fail("invalid input must not load credentials"),
    )

    with pytest.raises(ga4_admin.RequestValidationError, match="--filter"):
        ga4_admin.list_properties(
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
        reads,
        "service_account_credentials",
        lambda _: pytest.fail("invalid input must not load credentials"),
    )

    if property_name != "properties/1234":
        with pytest.raises(ga4_admin.RequestValidationError):
            ga4_admin.get_property(property_name)
    else:
        with pytest.raises(ga4_admin.RequestValidationError):
            ga4_admin.list_properties(
                filter_expression,
                page_size=page_size,
                page_token="",
                show_deleted=False,
            )
