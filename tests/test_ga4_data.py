import json
from io import StringIO
from pathlib import Path
from typing import Any, cast

import pytest
from google.analytics.data_v1beta.types import (
    AudienceExport,
    BatchRunPivotReportsResponse,
    BatchRunReportsResponse,
    CheckCompatibilityResponse,
    CreateAudienceExportRequest,
    ListAudienceExportsResponse,
    Metadata,
    QueryAudienceExportResponse,
    RunRealtimeReportResponse,
    RunReportResponse,
)
from google.api_core import exceptions

from ga4datactl import service as ga4_data
from ga4datactl.foundation import errors as data_errors
from ga4datactl.foundation import serialization as data_serialization
from ga4datactl.foundation import validation as data_validation
from ga4datactl.operations import audience_exports, metadata, reports


def test_service_facade_preserves_foundation_and_operation_identities() -> None:
    """Legacy imports share the extracted implementations, rather than wrappers."""
    assert ga4_data.RequestValidationError is data_validation.RequestValidationError
    assert (
        ga4_data.validate_run_report_request
        is data_validation.validate_run_report_request
    )
    assert ga4_data.GoogleApiError is data_errors.GoogleApiError
    assert ga4_data._normalize_google_error is data_errors.normalize_google_error
    assert ga4_data._parse_request is data_serialization.parse_request
    assert ga4_data._response_to_json is data_serialization.response_to_json

    assert ga4_data.run_report is reports.run_report
    assert ga4_data.batch_run_reports is reports.batch_run_reports
    assert ga4_data.check_compatibility is reports.check_compatibility
    assert ga4_data.get_metadata is metadata.get_metadata
    assert ga4_data.get_audience_export is audience_exports.get_audience_export
    assert ga4_data.create_audience_export is audience_exports.create_audience_export


def test_service_facade_calls_owning_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy callable imports invoke their static owning-operation aliases."""
    captured = CapturingClient(RunReportResponse({"row_count": 1}))
    credentials = object()
    monkeypatch.setattr(reports, "service_account_credentials", lambda _: credentials)

    response = ga4_data.run_report(
        "properties/1234",
        {
            "metrics": [{"name": "eventCount"}],
            "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
        },
        client_factory=lambda supplied: (
            captured if supplied is credentials else pytest.fail("wrong credentials")
        ),
    )

    assert captured.request.property == "properties/1234"
    assert response == {"rowCount": 1}


FIXTURES = Path("docs/specification/v1/ga4datactl/fixtures/reports-run")
AUDIENCE_EXPORT_CREATE_FIXTURES = Path(
    "docs/specification/v1/ga4datactl/fixtures/audience-exports-create"
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
    with pytest.raises(ga4_data.RequestValidationError, match="valid JSON"):
        ga4_data.read_json_body("-", stdin=StringIO('{"value": NaN}'))


def test_read_json_body_rejects_oversized_stdin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(data_validation, "MAX_BODY_CHARACTERS", 4)

    with pytest.raises(ga4_data.RequestValidationError, match="must not exceed 4"):
        ga4_data.read_json_body("-", stdin=StringIO('{"a": 1}'))


@pytest.mark.parametrize(
    "fixture_name",
    ["invalid-unknown-field.json"],
)
def test_validate_run_report_request_rejects_invalid_fixtures(
    fixture_name: str,
) -> None:
    with pytest.raises(ga4_data.RequestValidationError, match="request schema"):
        ga4_data.validate_run_report_request(
            "properties/1234", load_fixture(fixture_name)
        )


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

    response = ga4_data.run_report(
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
    normalized = ga4_data._normalize_google_error(error)

    assert normalized.exit_code == exit_code
    assert normalized.category == category
    assert str(error) not in str(normalized)


class CapturingAudienceExportClient:
    def __init__(self, response: AudienceExport) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def get_audience_export(self, request: Any, *, retry: Any) -> AudienceExport:
        self.request = request
        self.retry = retry
        return self.response


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

    response = ga4_data.query_audience_export(
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
    with pytest.raises(ga4_data.RequestValidationError, match=message):
        ga4_data.validate_query_audience_export_request(
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

    response = ga4_data.list_audience_exports(
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

    with pytest.raises(ga4_data.RequestValidationError):
        ga4_data.validate_create_audience_export_request("properties/1234", body)


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

    response = ga4_data.create_audience_export(
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

    response = ga4_data.create_audience_export(
        "properties/1234", body, apply=True, client_factory=lambda _: client
    )

    assert client.calls == 1
    assert isinstance(client.request, CreateAudienceExportRequest)
    assert client.request.parent == "properties/1234"
    assert client.request.audience_export.audience == "properties/1234/audiences/42"
    assert client.request.audience_export.dimensions[0].dimension_name == "deviceId"
    assert client.timeout == ga4_data.CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS
    assert response == {"operationName": "operations/export-1"}


class CapturingBatchClient:
    def __init__(self, response: BatchRunReportsResponse) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def batch_run_reports(self, request: Any, *, retry: Any) -> BatchRunReportsResponse:
        self.request = request
        self.retry = retry
        return self.response


class CapturingBatchPivotClient:
    def __init__(self, response: BatchRunPivotReportsResponse) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def batch_run_pivot_reports(
        self, request: Any, *, retry: Any
    ) -> BatchRunPivotReportsResponse:
        self.request = request
        self.retry = retry
        return self.response


class CapturingMetadataClient:
    def __init__(self, response: Metadata) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def get_metadata(self, request: Any, *, retry: Any) -> Metadata:
        self.request = request
        self.retry = retry
        return self.response


class CapturingPivotClient:
    def __init__(self, response: Any) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def run_pivot_report(self, request: Any, *, retry: Any) -> Any:
        self.request = request
        self.retry = retry
        return self.response


class CapturingRealtimeClient:
    def __init__(self, response: RunRealtimeReportResponse) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def run_realtime_report(
        self, request: Any, *, retry: Any
    ) -> RunRealtimeReportResponse:
        self.request = request
        self.retry = retry
        return self.response


class CapturingCompatibilityClient:
    def __init__(self, response: CheckCompatibilityResponse) -> None:
        self.response = response
        self.request: Any = None
        self.retry: Any = None

    def check_compatibility(
        self, request: Any, *, retry: Any
    ) -> CheckCompatibilityResponse:
        self.request = request
        self.retry = retry
        return self.response
