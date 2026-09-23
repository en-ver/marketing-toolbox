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

from ga4adminctl import service as ga4_admin
from ga4adminctl.operations import reads


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


def test_list_properties_returns_only_the_sdk_pager_raw_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = CapturingPropertiesClient()
    monkeypatch.setattr(reads, "service_account_credentials", lambda _: object())

    response = ga4_admin.list_properties(
        "parent:accounts/5678",
        page_size=25,
        page_token="prior-page",
        show_deleted=True,
        client_factory=lambda _: client,
    )

    assert client.list_request == ListPropertiesRequest(
        filter="parent:accounts/5678",
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
