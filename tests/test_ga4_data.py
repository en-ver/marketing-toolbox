import json
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import Any, cast

import pytest
from google.analytics.data_v1beta.types import (
    BatchRunPivotReportsRequest,
    BatchRunPivotReportsResponse,
    BatchRunReportsRequest,
    BatchRunReportsResponse,
    CheckCompatibilityRequest,
    CheckCompatibilityResponse,
    CreateAudienceExportRequest,
    ListAudienceExportsResponse,
    QueryAudienceExportResponse,
    RunPivotReportRequest,
    RunPivotReportResponse,
    RunRealtimeReportRequest,
    RunRealtimeReportResponse,
    RunReportRequest,
    RunReportResponse,
)
from google.api_core import exceptions

from ga4datactl.foundation import errors as data_errors
from ga4datactl.foundation import validation as data_validation
from ga4datactl.operations import audience_exports, reports

TESTS_DIR = Path(__file__).parent
FIXTURES = TESTS_DIR / "fixtures/ga4datactl/reports-run"
AUDIENCE_EXPORT_CREATE_FIXTURES = (
    TESTS_DIR / "fixtures/ga4datactl/audience-exports-create"
)


class CapturingClient:
    def __init__(self, response: RunReportResponse) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def run_report(self, request: Any, *, retry: Any) -> RunReportResponse:
        self.request = request
        self.retry = retry
        return self.response


def load_fixture(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any], json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    )


def test_read_json_body_rejects_nonstandard_json_constants() -> None:
    with pytest.raises(data_validation.RequestValidationError, match="valid JSON"):
        data_validation.read_json_body("-", stdin=StringIO('{"value": NaN}'))


def test_read_json_body_rejects_oversized_stdin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(data_validation, "MAX_BODY_CHARACTERS", 4)

    with pytest.raises(
        data_validation.RequestValidationError, match="must not exceed 4"
    ):
        data_validation.read_json_body("-", stdin=StringIO('{"a": 1}'))


@pytest.mark.parametrize(
    "fixture_name",
    ["invalid-unknown-field.json"],
)
def test_validate_run_report_request_rejects_invalid_fixtures(
    fixture_name: str,
) -> None:
    with pytest.raises(data_validation.RequestValidationError, match="request schema"):
        data_validation.validate_run_report_request(
            "properties/1234", load_fixture(fixture_name)
        )


@pytest.mark.parametrize(
    ("body", "trusted_context", "sentinels"),
    [
        (
            {"returnPropertyQuota": "TYPE_VALUE_SENTINEL"},
            ("returnPropertyQuota", "boolean"),
            ("TYPE_VALUE_SENTINEL",),
        ),
        (
            {"UNKNOWN_FIELD_SENTINEL": "UNKNOWN_VALUE_SENTINEL"},
            ("unsupported field",),
            ("UNKNOWN_FIELD_SENTINEL", "UNKNOWN_VALUE_SENTINEL"),
        ),
        (
            {
                "requests": [
                    {
                        "metrics": [
                            {
                                "name": "eventCount",
                                "NESTED_FIELD_SENTINEL": "NESTED_VALUE_SENTINEL",
                            }
                        ]
                    }
                ]
            },
            ("unsupported field",),
            ("NESTED_FIELD_SENTINEL", "NESTED_VALUE_SENTINEL"),
        ),
    ],
)
def test_schema_validation_discloses_only_controlled_context(
    body: dict[str, Any], trusted_context: tuple[str, ...], sentinels: tuple[str, ...]
) -> None:
    validator = (
        data_validation.BATCH_RUN_REPORTS_BODY_VALIDATOR
        if "requests" in body
        else data_validation.RUN_REPORT_BODY_VALIDATOR
    )

    with pytest.raises(data_validation.RequestValidationError) as raised:
        data_validation._validate_schema(body, validator)

    message = str(raised.value)
    for context in trusted_context:
        assert context in message
    for sentinel in sentinels:
        assert sentinel not in message
    if "requests" in body:
        assert "0" not in message


def test_schema_validation_precedes_credential_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        reports,
        "service_account_credentials",
        lambda _: pytest.fail("schema errors must not load credentials"),
    )

    with pytest.raises(data_validation.RequestValidationError) as raised:
        reports.run_report(
            "properties/1234", {"returnPropertyQuota": "TYPE_VALUE_SENTINEL"}
        )

    assert "TYPE_VALUE_SENTINEL" not in str(raised.value)


def test_pivot_validation_does_not_echo_custom_field_names() -> None:
    undeclared = _pivot_request()
    undeclared["pivots"][0]["fieldNames"] = ["UNDECLARED_PIVOT_SENTINEL"]
    duplicate = _pivot_request(dimension={"name": "DUPLICATE_PIVOT_SENTINEL"})
    duplicate["pivots"] = [
        {"fieldNames": ["DUPLICATE_PIVOT_SENTINEL"], "limit": "1"},
        {"fieldNames": ["DUPLICATE_PIVOT_SENTINEL"], "limit": "1"},
    ]

    with pytest.raises(data_validation.RequestValidationError) as undeclared_error:
        data_validation.validate_run_pivot_report_request("properties/1234", undeclared)
    with pytest.raises(data_validation.RequestValidationError) as duplicate_error:
        data_validation.validate_run_pivot_report_request("properties/1234", duplicate)

    assert "declared dimension or dateRange" in str(undeclared_error.value)
    assert "UNDECLARED_PIVOT_SENTINEL" not in str(undeclared_error.value)
    assert "cannot appear in more than one pivot" in str(duplicate_error.value)
    assert "DUPLICATE_PIVOT_SENTINEL" not in str(duplicate_error.value)


def test_run_report_uses_official_request_shape_and_preserves_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = CapturingClient(
        RunReportResponse(
            {
                "row_count": 1,
                "metadata": {
                    "currency_code": "USD",
                    "time_zone": "America/Los_Angeles",
                },
            }
        )
    )
    monkeypatch.setattr(reports, "service_account_credentials", lambda _: object())

    response = reports.run_report(
        "properties/1234",
        load_fixture("valid-basic-request.json"),
        client_factory=lambda _: captured,
    )

    assert captured.request.property == "properties/1234"
    assert captured.request.metrics[0].name == "eventCount"
    assert response == {
        "rowCount": 1,
        "metadata": {"currencyCode": "USD", "timeZone": "America/Los_Angeles"},
    }


@pytest.mark.parametrize(
    ("error", "exit_code", "category"),
    [
        (exceptions.BadRequest("bad request"), 2, "invalid_request"),  # type: ignore[no-untyped-call]
        (exceptions.PermissionDenied("denied"), 4, "authentication"),  # type: ignore[no-untyped-call]
        (exceptions.ResourceExhausted("quota"), 6, "retryable"),  # type: ignore[no-untyped-call]
        (exceptions.FailedPrecondition("precondition"), 5, "failed_precondition"),  # type: ignore[no-untyped-call]
        (exceptions.Aborted("conflict"), 5, "conflict"),  # type: ignore[no-untyped-call]
        (exceptions.InternalServerError("failure"), 6, "retryable"),  # type: ignore[no-untyped-call]
    ],
)
def test_normalize_google_error(
    error: exceptions.GoogleAPICallError, exit_code: int, category: str
) -> None:
    normalized = data_errors.normalize_google_error(error)

    assert normalized.exit_code == exit_code
    assert normalized.category == category
    assert str(error) not in str(normalized)


class CapturingAudienceExportsClient:
    def __init__(self, response: ListAudienceExportsResponse) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None
        self.calls = 0

    def list_audience_exports(
        self, request: Any, *, retry: Any
    ) -> ListAudienceExportsResponse:
        self.calls += 1
        self.request = request
        self.retry = retry
        return self.response


class CapturingCreateAudienceExportClient:
    def __init__(self) -> None:
        self.request: Any = None
        self.retry: Any = None
        self.timeout: Any = None
        self.calls = 0

    def create_audience_export(self, request: Any, *, retry: Any, timeout: Any) -> Any:
        self.calls += 1
        self.request = request
        self.retry = retry
        self.timeout = timeout
        return type(
            "InitiatedOperation",
            (),
            {"operation": type("RawOperation", (), {"name": "operations/export-1"})()},
        )()


class CapturingQueryAudienceExportClient:
    def __init__(self, response: QueryAudienceExportResponse) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None
        self.calls = 0

    def query_audience_export(
        self, request: Any, *, retry: Any
    ) -> QueryAudienceExportResponse:
        self.calls += 1
        self.request = request
        self.retry = retry
        return self.response


def test_query_audience_export_uses_one_bounded_official_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = CapturingQueryAudienceExportClient(
        QueryAudienceExportResponse(
            {
                "audience_export": {"name": "properties/1234/audienceExports/export-1"},
                "audience_rows": [{"dimension_values": [{"value": "user-1"}]}],
                "row_count": 25,
            }
        )
    )
    monkeypatch.setattr(
        audience_exports, "service_account_credentials", lambda _: object()
    )

    response = audience_exports.query_audience_export(
        "properties/1234",
        "properties/1234/audienceExports/export-1",
        10,
        5,
        client_factory=lambda _: captured,
    )

    assert captured.calls == 1
    assert captured.request.name == "properties/1234/audienceExports/export-1"
    assert captured.request.limit == 10
    assert captured.request.offset == 5
    assert response == {
        "audienceExport": {"name": "properties/1234/audienceExports/export-1"},
        "audienceRows": [{"dimensionValues": [{"value": "user-1"}]}],
        "rowCount": 25,
    }


def test_query_audience_export_constructs_the_official_request_before_auth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ordered_calls: list[tuple[str, object]] = []
    original_request = audience_exports.QueryAudienceExportRequest
    client = CapturingQueryAudienceExportClient(QueryAudienceExportResponse())

    def construct_request(**kwargs: object) -> Any:
        ordered_calls.append(("request", kwargs))
        return original_request(**kwargs)

    monkeypatch.setattr(
        audience_exports, "QueryAudienceExportRequest", construct_request
    )
    monkeypatch.setattr(
        audience_exports,
        "service_account_credentials",
        lambda _: ordered_calls.append(("credentials", None)) or object(),
    )

    audience_exports.query_audience_export(
        "properties/1234",
        "properties/1234/audienceExports/export-1",
        10,
        5,
        client_factory=lambda _: client,
    )

    assert ordered_calls == [
        (
            "request",
            {
                "name": "properties/1234/audienceExports/export-1",
                "limit": 10,
                "offset": 5,
            },
        ),
        ("credentials", None),
    ]


@pytest.mark.parametrize(
    ("name", "limit", "offset", "message"),
    [
        ("properties/5678/audienceExports/export-1", 1, 0, "belong to --property"),
        ("properties/1234/audienceExports/export-1", 0, 0, "--limit"),
        ("properties/1234/audienceExports/export-1", 1_001, 0, "--limit"),
    ],
)
def test_query_audience_export_rejects_unbounded_or_cross_property_requests(
    name: str, limit: int, offset: int, message: str
) -> None:
    with pytest.raises(data_validation.RequestValidationError, match=message):
        data_validation.validate_query_audience_export_request(
            "properties/1234", name, limit, offset
        )


def test_list_audience_exports_uses_one_explicit_page_without_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = CapturingAudienceExportsClient(
        ListAudienceExportsResponse(
            {
                "audience_exports": [
                    {
                        "name": "properties/1234/audienceExports/export-1",
                        "audience_display_name": "Purchasers",
                    }
                ],
                "next_page_token": "next-token",
            }
        )
    )
    monkeypatch.setattr(
        audience_exports, "service_account_credentials", lambda _: object()
    )

    response = audience_exports.list_audience_exports(
        "properties/1234", 25, "prior-token", client_factory=lambda _: captured
    )

    assert captured.calls == 1
    assert captured.request.parent == "properties/1234"
    assert captured.request.page_size == 25
    assert captured.request.page_token == "prior-token"
    assert response == {
        "audienceExports": [
            {
                "name": "properties/1234/audienceExports/export-1",
                "audienceDisplayName": "Purchasers",
            }
        ],
        "nextPageToken": "next-token",
    }


@pytest.mark.parametrize(
    "fixture_name",
    ["invalid-cross-property-audience.json"],
)
def test_create_audience_export_rejects_invalid_fixtures(
    fixture_name: str,
) -> None:
    body = json.loads(
        (AUDIENCE_EXPORT_CREATE_FIXTURES / fixture_name).read_text(encoding="utf-8")
    )

    with pytest.raises(data_validation.RequestValidationError):
        data_validation.validate_create_audience_export_request("properties/1234", body)


def test_create_audience_export_dry_run_never_loads_credentials_or_calls_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.loads(
        (AUDIENCE_EXPORT_CREATE_FIXTURES / "valid-basic-request.json").read_text(
            encoding="utf-8"
        )
    )
    client = CapturingCreateAudienceExportClient()
    monkeypatch.setattr(
        audience_exports,
        "service_account_credentials",
        lambda _: pytest.fail("dry run must not load credentials"),
    )

    response = audience_exports.create_audience_export(
        "properties/1234", body, client_factory=lambda _: client
    )

    assert client.calls == 0
    assert response == {
        "dryRun": True,
        "request": {
            "parent": "properties/1234",
            "audienceExport": body,
        },
    }


def test_create_audience_export_apply_uses_official_request_without_polling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.loads(
        (AUDIENCE_EXPORT_CREATE_FIXTURES / "valid-basic-request.json").read_text(
            encoding="utf-8"
        )
    )
    client = CapturingCreateAudienceExportClient()
    monkeypatch.setattr(
        audience_exports, "service_account_credentials", lambda _: object()
    )

    response = audience_exports.create_audience_export(
        "properties/1234", body, apply=True, client_factory=lambda _: client
    )

    assert client.calls == 1
    assert isinstance(client.request, CreateAudienceExportRequest)
    assert client.request.parent == "properties/1234"
    assert client.request.audience_export.audience == "properties/1234/audiences/42"
    assert client.request.audience_export.dimensions[0].dimension_name == "deviceId"
    assert client.retry is None
    assert client.timeout == audience_exports.CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS
    assert response == {"operationName": "operations/export-1"}


def test_create_audience_export_apply_parses_before_credential_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body = json.loads(
        (AUDIENCE_EXPORT_CREATE_FIXTURES / "valid-basic-request.json").read_text(
            encoding="utf-8"
        )
    )
    monkeypatch.setattr(
        audience_exports,
        "parse_request",
        lambda *_args: (_ for _ in ()).throw(
            data_validation.RequestValidationError("invalid request")
        ),
    )
    monkeypatch.setattr(
        audience_exports,
        "service_account_credentials",
        lambda _: pytest.fail("credentials must not be loaded before parsing"),
    )

    with pytest.raises(data_validation.RequestValidationError, match="invalid request"):
        audience_exports.create_audience_export("properties/1234", body, apply=True)


@pytest.mark.parametrize(
    ("error", "exit_code", "category", "status", "may_have_succeeded"),
    [
        (exceptions.InternalServerError("UPSTREAM-SECRET"), 1, "unexpected", 500, True),  # type: ignore[no-untyped-call]
        (exceptions.ServiceUnavailable("UPSTREAM-SECRET"), 1, "unexpected", 503, True),  # type: ignore[no-untyped-call]
        (exceptions.DeadlineExceeded("UPSTREAM-SECRET"), 1, "unexpected", 504, True),  # type: ignore[no-untyped-call]
        (
            exceptions.RetryError(
                "retry exhausted",
                exceptions.ServiceUnavailable("UPSTREAM-SECRET"),  # type: ignore[no-untyped-call]
            ),
            1,
            "unexpected",
            503,
            True,
        ),
        (exceptions.BadRequest("UPSTREAM-SECRET"), 2, "invalid_request", 400, False),  # type: ignore[no-untyped-call]
    ],
)
def test_create_audience_export_normalizes_failures_without_retries(
    monkeypatch: pytest.MonkeyPatch,
    error: exceptions.GoogleAPICallError | exceptions.RetryError,
    exit_code: int,
    category: str,
    status: int,
    may_have_succeeded: bool,
) -> None:
    body = json.loads(
        (AUDIENCE_EXPORT_CREATE_FIXTURES / "valid-basic-request.json").read_text(
            encoding="utf-8"
        )
    )
    client = CapturingCreateAudienceExportClient()

    def fail_once(*_args: Any, **_kwargs: Any) -> Any:
        client.calls += 1
        raise error

    client.create_audience_export = fail_once
    monkeypatch.setattr(
        audience_exports, "service_account_credentials", lambda _: object()
    )

    with pytest.raises(data_errors.GoogleApiError) as raised:
        audience_exports.create_audience_export(
            "properties/1234", body, apply=True, client_factory=lambda _: client
        )

    normalized = raised.value
    assert client.calls == 1
    assert (normalized.exit_code, normalized.category, normalized.status) == (
        exit_code,
        category,
        status,
    )
    assert "UPSTREAM-SECRET" not in str(normalized)
    assert ("may have succeeded" in str(normalized)) is may_have_succeeded


def _pivot_request(
    *, dimension: dict[str, Any] | None = None, metric: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "dimensions": [dimension if dimension is not None else {"name": "country"}],
        "metrics": [metric if metric is not None else {"name": "eventCount"}],
        "pivots": [{"fieldNames": ["country"], "limit": "1"}],
    }


@pytest.mark.parametrize(
    ("validator", "body"),
    [
        (data_validation.validate_batch_run_reports_request, {}),
        (data_validation.validate_batch_run_reports_request, {"requests": []}),
        (data_validation.validate_batch_run_pivot_reports_request, {}),
        (
            data_validation.validate_batch_run_pivot_reports_request,
            {"requests": []},
        ),
    ],
)
def test_batch_report_requests_are_required_and_nonempty(
    validator: Callable[[str, dict[str, Any]], None], body: dict[str, Any]
) -> None:
    with pytest.raises(data_validation.RequestValidationError, match="request schema"):
        validator("properties/1234", body)


@pytest.mark.parametrize("batch", [False, True])
@pytest.mark.parametrize(
    ("dimension", "metric"),
    [
        ({}, None),
        ({"name": ""}, None),
        (None, {}),
        (None, {"name": ""}),
    ],
)
def test_pivot_reports_require_nonempty_dimension_and_metric_names(
    batch: bool, dimension: dict[str, Any] | None, metric: dict[str, Any] | None
) -> None:
    request = _pivot_request(dimension=dimension, metric=metric)
    body = {"requests": [request]} if batch else request
    validator = (
        data_validation.validate_batch_run_pivot_reports_request
        if batch
        else data_validation.validate_run_pivot_report_request
    )

    with pytest.raises(data_validation.RequestValidationError, match="request schema"):
        validator("properties/1234", body)


@pytest.mark.parametrize(
    ("validator", "body"),
    [
        (
            data_validation.validate_run_pivot_report_request,
            _pivot_request(),
        ),
        (
            data_validation.validate_run_realtime_report_request,
            {"metrics": [{"name": "eventCount"}], "limit": "1"},
        ),
    ],
)
def test_pivot_and_realtime_limits_keep_their_250000_boundary(
    validator: Callable[[str, dict[str, Any]], None], body: dict[str, Any]
) -> None:
    limit = body["pivots"][0] if "pivots" in body else body
    limit["limit"] = "250000"
    validator("properties/1234", body)

    limit["limit"] = "250001"
    with pytest.raises(data_validation.RequestValidationError, match="250000"):
        validator("properties/1234", body)

    limit["limit"] = "9" * 4301
    with pytest.raises(data_validation.RequestValidationError, match="request schema"):
        validator("properties/1234", body)


@pytest.mark.parametrize(
    ("offset", "valid"),
    [
        (-1, False),
        (0, True),
        (2**63 - 1, True),
        (2**63, False),
    ],
)
def test_query_audience_export_offset_stays_in_the_official_int64_range(
    offset: int, valid: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = ("properties/1234", "properties/1234/audienceExports/export-1", 1, offset)
    if valid:
        data_validation.validate_query_audience_export_request(*args)
        return

    monkeypatch.setattr(
        audience_exports,
        "service_account_credentials",
        lambda _: pytest.fail("invalid offsets must not load credentials"),
    )
    with pytest.raises(data_validation.RequestValidationError, match="--offset"):
        audience_exports.query_audience_export(*args)


class CapturingReportAdapterClient:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.calls = 0
        self.request: Any = None
        self.retry: Any = None

    def __getattr__(self, _name: str) -> Callable[..., Any]:
        def invoke(request: Any, *, retry: Any) -> Any:
            self.calls += 1
            self.request = request
            self.retry = retry
            return self.response

        return invoke


@pytest.mark.parametrize(
    ("operation", "request_type", "response", "body"),
    [
        (
            reports.run_report,
            RunReportRequest,
            RunReportResponse(),
            {"metrics": [{"name": "eventCount"}]},
        ),
        (
            reports.batch_run_reports,
            BatchRunReportsRequest,
            BatchRunReportsResponse(),
            {"requests": [{"metrics": [{"name": "eventCount"}]}]},
        ),
        (
            reports.batch_run_pivot_reports,
            BatchRunPivotReportsRequest,
            BatchRunPivotReportsResponse(),
            {"requests": [_pivot_request()]},
        ),
        (
            reports.run_pivot_report,
            RunPivotReportRequest,
            RunPivotReportResponse(),
            _pivot_request(),
        ),
        (
            reports.run_realtime_report,
            RunRealtimeReportRequest,
            RunRealtimeReportResponse(),
            {"metrics": [{"name": "eventCount"}]},
        ),
        (
            reports.check_compatibility,
            CheckCompatibilityRequest,
            CheckCompatibilityResponse(),
            {"metrics": [{"name": "eventCount"}]},
        ),
    ],
)
def test_report_adapters_preserve_valid_requests_responses_and_retry(
    monkeypatch: pytest.MonkeyPatch,
    operation: Callable[..., dict[str, Any]],
    request_type: type[Any],
    response: Any,
    body: dict[str, Any],
) -> None:
    credentials = object()
    client = CapturingReportAdapterClient(response)
    monkeypatch.setattr(reports, "service_account_credentials", lambda _: credentials)

    result = operation(
        "properties/1234",
        body,
        client_factory=lambda supplied: (
            client if supplied is credentials else pytest.fail("wrong credentials")
        ),
    )

    assert client.calls == 1
    assert type(client.request) is request_type
    assert client.request.property == "properties/1234"
    assert client.retry is reports.RUN_REPORT_RETRY
    assert result == {}


@pytest.mark.parametrize(
    ("operation", "validator", "body"),
    [
        (
            reports.run_report,
            data_validation.validate_run_report_request,
            {"metrics": [{"name": "eventCount"}], "limit": "not-an-int"},
        ),
        (
            reports.batch_run_reports,
            data_validation.validate_batch_run_reports_request,
            {
                "requests": [
                    {"metrics": [{"name": "eventCount"}], "limit": "not-an-int"}
                ]
            },
        ),
        (
            reports.batch_run_pivot_reports,
            data_validation.validate_batch_run_pivot_reports_request,
            {
                "requests": [
                    {
                        **_pivot_request(),
                        "pivots": [
                            {
                                "fieldNames": ["country"],
                                "limit": "1",
                                "offset": "not-an-int",
                            }
                        ],
                    }
                ]
            },
        ),
        (
            reports.run_pivot_report,
            data_validation.validate_run_pivot_report_request,
            {
                **_pivot_request(),
                "pivots": [
                    {"fieldNames": ["country"], "limit": "1", "offset": "not-an-int"}
                ],
            },
        ),
        (
            reports.run_realtime_report,
            data_validation.validate_run_realtime_report_request,
            {
                "metrics": [{"name": "eventCount"}],
                "metricFilter": {
                    "filter": {"numericFilter": {"value": {"int64Value": "not-an-int"}}}
                },
            },
        ),
        (
            reports.check_compatibility,
            data_validation.validate_check_compatibility_request,
            {
                "metrics": [{"name": "eventCount"}],
                "metricFilter": {
                    "filter": {"numericFilter": {"value": {"int64Value": "not-an-int"}}}
                },
            },
        ),
    ],
)
def test_report_adapters_parse_protobuf_before_credentials_and_clients(
    monkeypatch: pytest.MonkeyPatch,
    operation: Callable[..., dict[str, Any]],
    validator: Callable[[str, dict[str, Any]], None],
    body: dict[str, Any],
) -> None:
    validator("properties/1234", body)
    monkeypatch.setattr(
        reports,
        "service_account_credentials",
        lambda _: pytest.fail("protobuf errors must not load credentials"),
    )

    with pytest.raises(
        data_validation.RequestValidationError, match="cannot be converted"
    ):
        operation(
            "properties/1234",
            body,
            client_factory=lambda _: pytest.fail(
                "protobuf errors must not create clients"
            ),
        )
