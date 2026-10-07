import json
import re
import sys
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import Any

import pytest
import typer
from google.analytics.data_v1beta.types import (
    BatchRunReportsRequest,
    RunPivotReportRequest,
    RunReportRequest,
)
from google.api_core import exceptions
from typer.main import get_command
from typer.testing import CliRunner

from ga4adminctl.cli import app as ga4_admin_app
from ga4adminctl.cli import main as ga4_admin_main
from ga4adminctl.commands import properties as admin_properties
from ga4adminctl.commands.sdk import (
    _SCHEMA_TARGET_DECLARATIONS as admin_schema_target_declarations,
)
from ga4adminctl.commands.sdk import _SCHEMA_TARGETS as admin_schema_targets
from ga4adminctl.foundation.validation import (
    RequestValidationError as AdminRequestValidationError,
)
from ga4adminctl.operations import transport as admin_transport
from ga4adminctl.operations.accounts import ACCOUNT_PATCH_WRITABLE_FIELDS
from ga4adminctl.operations.properties import PROPERTY_PATCH_WRITABLE_FIELDS
from ga4adminctl.operations.resources import (
    CUSTOM_DIMENSION_PATCH_WRITABLE_FIELDS,
    CUSTOM_METRIC_PATCH_WRITABLE_FIELDS,
    DATA_STREAM_PATCH_WRITABLE_FIELDS,
    GOOGLE_ADS_LINK_PATCH_WRITABLE_FIELDS,
    KEY_EVENT_PATCH_WRITABLE_FIELDS,
)
from ga4adminctl.operations.secrets import (
    MEASUREMENT_PROTOCOL_SECRET_PATCH_WRITABLE_FIELDS,
)
from ga4datactl.cli import app as ga4_data_app
from ga4datactl.cli import main as ga4_data_main
from ga4datactl.commands import audience_exports, metadata, reports
from ga4datactl.commands.sdk import (
    _SCHEMA_TARGET_DECLARATIONS as data_schema_target_declarations,
)
from ga4datactl.commands.sdk import _SCHEMA_TARGETS as data_schema_targets
from ga4datactl.foundation import validation as data_validation
from ga4datactl.foundation.validation import (
    RequestValidationError as DataRequestValidationError,
)
from ga4datactl.operations import audience_exports as audience_export_operations
from ga4datactl.operations import transport as data_transport
from ga4datactl.schemas import (
    BATCH_RUN_PIVOT_REPORTS_BODY_SCHEMA,
    BATCH_RUN_REPORTS_BODY_SCHEMA,
    CHECK_COMPATIBILITY_BODY_SCHEMA,
    RUN_PIVOT_REPORT_BODY_SCHEMA,
    RUN_REALTIME_REPORT_BODY_SCHEMA,
    RUN_REPORT_BODY_SCHEMA,
)
from gtmctl.cli import app as gtm_app
from gtmctl.cli import main as gtm_main
from gtmctl.commands.sdk import _registered_body_options, _target_for_path
from marketing_common.auth import (
    CredentialConfigurationError as AdminCredentialConfigurationError,
)
from marketing_common.cli import exit_with_diagnostic, write_success
from marketing_common.discovery import (
    discovery_method_parameters,
    load_local_discovery_document,
)
from marketing_common.introspection import protobuf_body_schema
from marketing_common.oauth import OAuthAuthenticationError

runner = CliRunner()


@pytest.mark.parametrize(
    ("app", "guide_url", "api_url"),
    [
        (
            ga4_data_app,
            "https://marketing-toolbox.org/tools/ga4-data/",
            "https://developers.google.com/analytics/devguides/reporting/data/v1",
        ),
        (
            ga4_admin_app,
            "https://marketing-toolbox.org/tools/ga4-admin/",
            "https://developers.google.com/analytics/devguides/config/admin/v1",
        ),
        (
            gtm_app,
            "https://marketing-toolbox.org/tools/tag-manager/",
            "https://developers.google.com/tag-platform/tag-manager/api/v2",
        ),
    ],
)
def test_root_help_explains_discovery_json_diagnostics_and_exit_contract(
    app: typer.Typer, guide_url: str, api_url: str
) -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    normalized = " ".join(re.sub(r"-\s+", "-", result.stdout).split())
    for text in (
        "auth --help",
        "sdk schema --help",
        "schemaVersion, command, data",
        "googleStatus",
        "Explicit --help is plain stdout/0",
        "no-argument help is plain stderr/2",
        "0 success; 1 unexpected or unexpected_failure",
        "6 retryable",
        "https://marketing-toolbox.org/",
        "https://marketing-toolbox.org/auth/",
        guide_url,
        api_url,
    ):
        assert text in normalized
    assert result.stderr == ""


@pytest.mark.parametrize(
    ("module_app", "path", "help_text"),
    [
        (reports.app, ["reports"], "Run GA4 reporting operations."),
        (metadata.app, ["metadata"], "Discover live GA4 property metadata."),
        (
            audience_exports.app,
            ["audience-exports"],
            "Discover existing GA4 audience-export metadata.",
        ),
    ],
)
def test_ga4_data_root_composes_the_exported_command_family_apps(
    module_app: typer.Typer, path: list[str], help_text: str
) -> None:
    """Keep public command-family apps composed at their established paths."""
    assert module_app.info.no_args_is_help is True

    result = runner.invoke(ga4_data_app, [*path, "--help"])

    assert result.exit_code == 0
    assert help_text in result.stdout


def test_json_envelope_primitives_preserve_stdout_stderr_and_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_success(command="ga4datactl reports run", data={"rows": []})

    with pytest.raises(typer.Exit) as exit_info:
        exit_with_diagnostic(
            exit_code=6,
            category="retryable",
            message="Try again.",
            command="ga4adminctl properties list",
            status=429,
        )

    captured = capsys.readouterr()
    assert exit_info.value.exit_code == 6
    assert captured.out == (
        '{"schemaVersion": "marketing-toolbox/v1", "command": '
        '"ga4datactl reports run", "data": {"rows": []}}\n'
    )
    assert captured.err == (
        '{"schemaVersion": "marketing-toolbox/v1", "command": '
        '"ga4adminctl properties list", "exitCode": 6, '
        '"category": "retryable", "message": "Try again.", '
        '"googleStatus": 429}\n'
    )


def test_ga4_admin_credential_configuration_error_is_an_authentication_diagnostic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        admin_properties,
        "get_property",
        lambda _: (_ for _ in ()).throw(AdminCredentialConfigurationError("missing")),
    )

    result = runner.invoke(
        ga4_admin_app, ["properties", "get", "--property", "properties/1234"]
    )

    assert result.exit_code == 4
    assert json.loads(result.stderr) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "ga4adminctl properties get",
        "exitCode": 4,
        "category": "authentication",
        "message": "missing",
    }


def test_audience_export_query_requires_sensitive_data_acknowledgement() -> None:
    result = runner.invoke(
        ga4_data_app,
        [
            "audience-exports",
            "query",
            "--property",
            "properties/1234",
            "--name",
            "properties/1234/audienceExports/export-1",
            "--limit",
            "10",
        ],
    )

    assert result.exit_code == 2
    assert "Missing option '--acknowledge-sensitive-data'" in result.stderr


def test_audience_export_query_writes_unmodified_one_page_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, object] = {}

    def query(*args: object) -> dict[str, object]:
        called["args"] = args
        return {"audienceRows": [{"dimensionValues": [{"value": "user-1"}]}]}

    monkeypatch.setattr(audience_exports, "query_audience_export", query)
    result = runner.invoke(
        ga4_data_app,
        [
            "audience-exports",
            "query",
            "--property",
            "properties/1234",
            "--name",
            "properties/1234/audienceExports/export-1",
            "--limit",
            "10",
            "--offset",
            "5",
            "--acknowledge-sensitive-data",
        ],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert called["args"] == (
        "properties/1234",
        "properties/1234/audienceExports/export-1",
        10,
        5,
    )
    assert json.loads(result.stdout) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "ga4datactl audience-exports query",
        "data": {"audienceRows": [{"dimensionValues": [{"value": "user-1"}]}]},
    }
    assert result.stdout == (
        '{"schemaVersion": "marketing-toolbox/v1", "command": '
        '"ga4datactl audience-exports query", "data": {"audienceRows": '
        '[{"dimensionValues": [{"value": "user-1"}]}]}}\n'
    )


def test_ga4_clis_keep_request_error_exit_and_diagnostic_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def admin_failure(_: str) -> dict[str, object]:
        raise AdminRequestValidationError("Bad admin request.")

    def data_failure(*_: object) -> dict[str, object]:
        raise DataRequestValidationError("Bad data request.")

    monkeypatch.setattr(admin_properties, "get_property", admin_failure)
    monkeypatch.setattr(audience_exports, "query_audience_export", data_failure)

    admin_result = runner.invoke(
        ga4_admin_app, ["properties", "get", "--property", "properties/1234"]
    )
    data_result = runner.invoke(
        ga4_data_app,
        [
            "audience-exports",
            "query",
            "--property",
            "properties/1234",
            "--name",
            "properties/1234/audienceExports/export-1",
            "--limit",
            "10",
            "--acknowledge-sensitive-data",
        ],
    )

    assert (admin_result.exit_code, admin_result.stdout, admin_result.stderr) == (
        2,
        "",
        (
            '{"schemaVersion": "marketing-toolbox/v1", "command": '
            '"ga4adminctl properties get", "exitCode": 2, '
            '"category": "invalid_request", "message": "Bad admin request."}\n'
        ),
    )
    assert (data_result.exit_code, data_result.stdout, data_result.stderr) == (
        2,
        "",
        (
            '{"schemaVersion": "marketing-toolbox/v1", "command": '
            '"ga4datactl audience-exports query", "exitCode": 2, '
            '"category": "invalid_request", "message": "Bad data request."}\n'
        ),
    )


def _registered_body_leaf_paths(app: typer.Typer) -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()

    def visit(command: object, path: tuple[str, ...]) -> None:
        children = getattr(command, "commands", None)
        if children:
            for name, child in children.items():
                visit(child, (*path, name))
            return
        if any(
            "--body" in getattr(parameter, "opts", ())
            for parameter in getattr(command, "params", ())
        ):
            paths.add(path)

    visit(get_command(app), ())
    return paths


def test_sdk_schema_maps_every_registered_body_leaf() -> None:
    assert len(data_schema_targets) == 7
    assert len(admin_schema_targets) == 22
    assert tuple(data_schema_targets) == tuple(
        target.cli_path for target in data_schema_target_declarations
    )
    assert tuple(admin_schema_targets) == tuple(
        target.cli_path for target in admin_schema_target_declarations
    )
    assert set(data_schema_targets) == _registered_body_leaf_paths(ga4_data_app)
    assert set(admin_schema_targets) == _registered_body_leaf_paths(ga4_admin_app)
    assert set(_registered_body_options(gtm_app)) == _registered_body_leaf_paths(
        gtm_app
    )


def _discovery_references(value: object) -> set[str]:
    if isinstance(value, dict):
        references = {value["$ref"]} if isinstance(value.get("$ref"), str) else set()
        for nested in value.values():
            references.update(_discovery_references(nested))
        return references
    if isinstance(value, list):
        return set().union(*(_discovery_references(nested) for nested in value))
    return set()


def _bundled_gtm_request_properties(method_id: str) -> dict[str, Any] | None:
    """Read root request properties directly from the bundled official document."""
    document = load_local_discovery_document("tagmanager", "v2")

    def methods(node: dict[str, Any]) -> list[dict[str, Any]]:
        found = list(node.get("methods", {}).values())
        for resource in node.get("resources", {}).values():
            found.extend(methods(resource))
        return found

    for method in methods(document):
        if method.get("id") != method_id:
            continue
        request_ref = method.get("request", {}).get("$ref")
        if request_ref is None:
            return None
        return document["schemas"][request_ref].get("properties", {})
    raise AssertionError(f"Missing bundled GTM Discovery method: {method_id}")


def test_every_sdk_schema_target_resolves_with_complete_provenance_and_references() -> (
    None
):
    for app, targets, expected_kind in (
        (ga4_data_app, data_schema_targets, "installed-sdk-descriptor"),
        (ga4_admin_app, admin_schema_targets, "installed-sdk-descriptor"),
    ):
        for path, target in targets.items():
            result = runner.invoke(app, ["sdk", "schema", "--command", " ".join(path)])
            assert result.exit_code == 0, result.output
            payload = json.loads(result.stdout)["data"]
            assert payload["cliPath"] == list(path)
            assert payload["officialMethod"] == target.official_method
            assert payload["source"]["kind"] == expected_kind
            fields = {field["name"] for field in payload["request"]["body"]["fields"]}
            assert not fields.intersection(target.body_forbidden_fields)

    body_options = _registered_body_options(gtm_app)
    resource_body_targets = 0
    gallery_envelope_targets = 0
    root_field_overlap_targets = 0
    for path, options in body_options.items():
        result = runner.invoke(gtm_app, ["sdk", "schema", "--command", " ".join(path)])
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)["data"]
        discovery_target = _target_for_path(path=path, option_names=options)
        assert payload["cliPath"] == list(path)
        assert payload["officialMethod"] == discovery_target.official_method
        assert payload["source"]["kind"] == "installed-discovery-document"
        request = payload["request"]
        assert set(request) == {
            "type",
            "pathOrQueryFields",
            "bodyForbiddenFields",
            "body",
            "officialParameters",
        }
        assert request["pathOrQueryFields"] == list(
            discovery_target.path_or_query_fields
        )
        assert request["bodyForbiddenFields"] == list(
            discovery_target.body_forbidden_fields
        )
        assert request["officialParameters"] == discovery_method_parameters(
            api="tagmanager",
            api_version="v2",
            method_id=discovery_target.official_method,
        )
        body = request["body"]
        assert _discovery_references(body).issubset(body["definitions"])
        official_properties = _bundled_gtm_request_properties(
            discovery_target.official_method
        )
        if official_properties is None:
            gallery_envelope_targets += 1
            continue

        resource_body_targets += 1
        assert body["properties"] == official_properties
        official_overlap = set(official_properties).intersection(
            request["bodyForbiddenFields"]
        )
        assert (
            set(body["properties"]).intersection(request["bodyForbiddenFields"])
            == official_overlap
        )
        if official_overlap:
            root_field_overlap_targets += 1

    assert len(body_options) == 34
    assert resource_body_targets == 33
    assert gallery_envelope_targets == 1
    assert root_field_overlap_targets == 17


@pytest.mark.parametrize(
    ("command", "nested_request_type"),
    [
        ("batch-run", RunReportRequest),
        ("batch-pivot-run", RunPivotReportRequest),
    ],
)
def test_sdk_schema_batch_reports_exclude_only_nested_request_properties(
    monkeypatch: pytest.MonkeyPatch, command: str, nested_request_type: type[object]
) -> None:
    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError(
            "static schema lookup must not authenticate or call Google"
        )

    monkeypatch.setattr("google.auth.default", forbidden)
    monkeypatch.setattr("googleapiclient.discovery.build", forbidden)

    result = runner.invoke(
        ga4_data_app, ["sdk", "schema", "--command", f"reports {command}"]
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)["data"]
    assert set(payload) == {"cliPath", "officialMethod", "source", "request"}
    assert payload["source"]["kind"] == "installed-sdk-descriptor"
    assert set(payload["request"]) == {
        "type",
        "pathOrQueryFields",
        "bodyForbiddenFields",
        "body",
    }
    assert payload["request"]["bodyForbiddenFields"] == ["property"]
    body = payload["request"]["body"]
    assert "property" not in {field["name"] for field in body["fields"]}
    nested = body["definitions"][nested_request_type.pb().DESCRIPTOR.full_name]
    assert "property" not in {field["name"] for field in nested["fields"]}


def test_protobuf_body_schema_descriptor_exclusions_do_not_filter_root_fields() -> None:
    body = protobuf_body_schema(
        BatchRunReportsRequest,
        descriptor_field_exclusions={
            RunReportRequest.pb().DESCRIPTOR.full_name: frozenset({"property"})
        },
    )

    assert "property" in {field["name"] for field in body["fields"]}
    nested = body["definitions"][RunReportRequest.pb().DESCRIPTOR.full_name]
    assert "property" not in {field["name"] for field in nested["fields"]}


def test_property_patch_help_runtime_policy_and_sdk_constraints_share_allowlist() -> (
    None
):
    help_result = runner.invoke(ga4_admin_app, ["properties", "patch", "--help"])
    schema_result = runner.invoke(
        ga4_admin_app, ["sdk", "schema", "--command", "properties patch"]
    )

    assert help_result.exit_code == schema_result.exit_code == 0
    assert all(field in help_result.stdout for field in PROPERTY_PATCH_WRITABLE_FIELDS)
    payload = json.loads(schema_result.stdout)["data"]
    assert payload["request"]["cliConstraints"] == {
        "allowedUpdateMaskFields": list(PROPERTY_PATCH_WRITABLE_FIELDS),
        "bodyFieldsMustExactlyMatchUpdateMask": True,
    }
    assert payload["request"]["body"]["type"].endswith(".Property")
    assert "name" not in {
        field["name"] for field in payload["request"]["body"]["fields"]
    }


@pytest.mark.parametrize(
    ("path", "owner_fields", "expected_fields"),
    [
        pytest.param(
            ("accounts", "patch"),
            ACCOUNT_PATCH_WRITABLE_FIELDS,
            ("displayName", "regionCode"),
            id="account",
        ),
        pytest.param(
            ("properties", "patch"),
            PROPERTY_PATCH_WRITABLE_FIELDS,
            ("displayName", "industryCategory", "timeZone", "currencyCode"),
            id="property",
        ),
        pytest.param(
            ("properties", "custom-dimensions", "patch"),
            CUSTOM_DIMENSION_PATCH_WRITABLE_FIELDS,
            ("displayName", "description", "disallowAdsPersonalization"),
            id="custom-dimension",
        ),
        pytest.param(
            ("properties", "custom-metrics", "patch"),
            CUSTOM_METRIC_PATCH_WRITABLE_FIELDS,
            ("displayName", "description", "measurementUnit", "restrictedMetricType"),
            id="custom-metric",
        ),
        pytest.param(
            ("properties", "data-streams", "patch"),
            DATA_STREAM_PATCH_WRITABLE_FIELDS,
            ("displayName", "webStreamData.defaultUri"),
            id="data-stream",
        ),
        pytest.param(
            ("properties", "google-ads-links", "patch"),
            GOOGLE_ADS_LINK_PATCH_WRITABLE_FIELDS,
            ("adsPersonalizationEnabled",),
            id="google-ads-link",
        ),
        pytest.param(
            ("properties", "key-events", "patch"),
            KEY_EVENT_PATCH_WRITABLE_FIELDS,
            (
                "countingMethod",
                "defaultValue.numericValue",
                "defaultValue.currencyCode",
            ),
            id="key-event",
        ),
        pytest.param(
            ("properties", "data-streams", "measurement-protocol-secrets", "patch"),
            MEASUREMENT_PROTOCOL_SECRET_PATCH_WRITABLE_FIELDS,
            ("displayName",),
            id="measurement-protocol-secret",
        ),
    ],
)
def test_admin_patch_help_and_sdk_constraints_match_owner_allowlists(
    path: tuple[str, ...],
    owner_fields: tuple[str, ...],
    expected_fields: tuple[str, ...],
) -> None:
    help_result = runner.invoke(ga4_admin_app, [*path, "--help"])
    schema_result = runner.invoke(
        ga4_admin_app, ["sdk", "schema", "--command", " ".join(path)]
    )

    assert help_result.exit_code == schema_result.exit_code == 0
    assert owner_fields == expected_fields
    assert admin_schema_targets[path].request_cli_constraints == {
        "allowedUpdateMaskFields": list(expected_fields),
        "bodyFieldsMustExactlyMatchUpdateMask": True,
    }
    assert all(field in help_result.stdout for field in expected_fields)
    payload = json.loads(schema_result.stdout)["data"]
    assert payload["request"]["cliConstraints"] == {
        "allowedUpdateMaskFields": list(expected_fields),
        "bodyFieldsMustExactlyMatchUpdateMask": True,
    }


def test_sdk_schema_commands_derive_official_local_descriptors_without_auth_or_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError(
            "static schema lookup must not authenticate or call Google"
        )

    monkeypatch.setattr("google.auth.default", forbidden)
    monkeypatch.setattr("googleapiclient.discovery.build", forbidden)

    data_result = runner.invoke(
        ga4_data_app, ["sdk", "schema", "--command", "reports run"]
    )
    admin_result = runner.invoke(
        ga4_admin_app, ["sdk", "schema", "--command", "properties create"]
    )
    gtm_result = runner.invoke(
        gtm_app, ["sdk", "schema", "--command", "accounts update"]
    )

    assert (data_result.exit_code, admin_result.exit_code, gtm_result.exit_code) == (
        0,
        0,
        0,
    )
    data = json.loads(data_result.stdout)["data"]
    admin = json.loads(admin_result.stdout)["data"]
    gtm = json.loads(gtm_result.stdout)["data"]
    assert data["source"]["kind"] == "installed-sdk-descriptor"
    assert data["officialMethod"] == "analyticsdata.properties.runReport"
    assert "property" not in {
        field["name"] for field in data["request"]["body"]["fields"]
    }
    assert admin["request"]["type"].endswith("CreatePropertyRequest")
    assert admin["request"]["body"]["type"].endswith("Property")
    assert gtm["source"]["kind"] == "installed-discovery-document"
    assert gtm["request"]["type"] == "Account"


@pytest.mark.parametrize(
    ("app", "path"),
    [
        (ga4_data_app, ["sdk", "schema", "--command", "reports"]),
        (ga4_admin_app, ["sdk", "schema", "--command", "properties get"]),
        (gtm_app, ["sdk", "schema", "--command", "accounts get"]),
    ],
)
def test_sdk_schema_rejects_non_body_or_group_paths(
    app: typer.Typer, path: list[str]
) -> None:
    result = runner.invoke(app, path)

    assert result.exit_code == 2
    assert result.stdout == ""
    diagnostic = json.loads(result.stderr)
    assert diagnostic.get("category", diagnostic.get("error", {}).get("category")) == (
        "invalid_arguments"
    )


@pytest.mark.parametrize(
    ("command", "expected_schema"),
    [
        ("run", RUN_REPORT_BODY_SCHEMA),
        ("batch-run", BATCH_RUN_REPORTS_BODY_SCHEMA),
        ("pivot-run", RUN_PIVOT_REPORT_BODY_SCHEMA),
        ("realtime-run", RUN_REALTIME_REPORT_BODY_SCHEMA),
        ("batch-pivot-run", BATCH_RUN_PIVOT_REPORTS_BODY_SCHEMA),
        ("compatibility-check", CHECK_COMPATIBILITY_BODY_SCHEMA),
    ],
)
def test_report_schema_is_standalone_structural_cli_validation(
    monkeypatch: pytest.MonkeyPatch, command: str, expected_schema: dict[str, object]
) -> None:
    def forbidden(*_: object, **__: object) -> None:
        raise AssertionError("--schema must not construct a client or authenticate")

    monkeypatch.setattr(reports, "run_report_command", forbidden)
    monkeypatch.setattr("google.auth.default", forbidden)

    help_result = runner.invoke(ga4_data_app, ["reports", command, "--help"])
    schema_result = runner.invoke(ga4_data_app, ["reports", command, "--schema"])

    assert help_result.exit_code == 0
    assert "--schema" in help_result.stdout
    assert "Additional CLI cross-field checks" in help_result.stdout
    assert schema_result.exit_code == 0
    assert schema_result.stderr == ""
    assert json.loads(schema_result.stdout) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": f"ga4datactl reports {command}",
        "data": {"bodySchema": expected_schema},
    }


def test_pivot_schema_overrides_do_not_tighten_ordinary_report_definitions() -> None:
    for command in ("pivot-run", "batch-pivot-run"):
        result = runner.invoke(ga4_data_app, ["reports", command, "--schema"])

        assert result.exit_code == 0
        definitions = json.loads(result.stdout)["data"]["bodySchema"]["$defs"]
        for definition in ("Dimension", "Metric"):
            assert "name" in definitions[definition]["required"]
            assert definitions[definition]["properties"]["name"]["minLength"] == 1
        assert definitions["Pivot"]["properties"]["limit"]["maxLength"] == 6

    ordinary = json.loads(
        runner.invoke(ga4_data_app, ["reports", "run", "--schema"]).stdout
    )["data"]["bodySchema"]["$defs"]
    for definition in ("Dimension", "Metric"):
        assert "required" not in ordinary[definition]
        assert "minLength" not in ordinary[definition]["properties"]["name"]


def test_report_body_schema_and_sdk_descriptor_remain_distinct_contracts() -> None:
    body_schema = json.loads(
        runner.invoke(ga4_data_app, ["reports", "run", "--schema"]).stdout
    )["data"]
    sdk_descriptor = json.loads(
        runner.invoke(
            ga4_data_app, ["sdk", "schema", "--command", "reports run"]
        ).stdout
    )["data"]

    assert set(body_schema) == {"bodySchema"}
    assert sdk_descriptor["source"]["kind"] == "installed-sdk-descriptor"
    assert "response" not in sdk_descriptor


@pytest.mark.parametrize(
    ("entrypoint", "program"),
    [
        (ga4_data_main, "ga4datactl"),
        (ga4_admin_main, "ga4adminctl"),
        (gtm_main, "gtmctl"),
    ],
)
def test_oauth_entrypoints_propagate_request_exit_codes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    program: str,
) -> None:
    monkeypatch.setattr(
        sys, "argv", [program, "auth", "status", "--access", "unsupported"]
    )

    with pytest.raises(SystemExit) as exit_info:
        entrypoint()

    assert exit_info.value.code == 2
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["category"] == "invalid_request"


@pytest.mark.parametrize(
    ("entrypoint", "program"),
    [
        (ga4_data_main, "ga4datactl"),
        (ga4_admin_main, "ga4adminctl"),
        (gtm_main, "gtmctl"),
    ],
)
def test_oauth_entrypoints_propagate_authentication_exit_codes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    program: str,
) -> None:
    def offline_storage(*_args: object) -> bool:
        raise OAuthAuthenticationError("Secure local credential storage is offline.")

    monkeypatch.setattr(
        "marketing_common.oauth_cli.native_record_status", offline_storage
    )
    monkeypatch.setattr(sys, "argv", [program, "auth", "status", "--access", "read"])

    with pytest.raises(SystemExit) as exit_info:
        entrypoint()

    assert exit_info.value.code == 4
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["category"] == "authentication"


@pytest.mark.parametrize(
    ("entrypoint", "program"),
    [
        (ga4_data_main, "ga4datactl"),
        (ga4_admin_main, "ga4adminctl"),
        (gtm_main, "gtmctl"),
    ],
)
def test_oauth_entrypoints_return_successfully_for_local_status(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    program: str,
) -> None:
    monkeypatch.setattr(
        "marketing_common.oauth_cli.native_record_status", lambda *_args: False
    )
    monkeypatch.setattr(sys, "argv", [program, "auth", "status", "--access", "read"])

    entrypoint()

    captured = capsys.readouterr()
    assert json.loads(captured.out)["data"] == {"stored": False, "access": "read"}
    assert captured.err == ""


@pytest.mark.parametrize(
    ("entrypoint", "program"),
    [
        (ga4_data_main, "ga4datactl"),
        (ga4_admin_main, "ga4adminctl"),
        (gtm_main, "gtmctl"),
    ],
)
def test_oauth_entrypoints_return_successfully_for_help(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    program: str,
) -> None:
    monkeypatch.setattr(sys, "argv", [program, "auth", "--help"])

    entrypoint()

    captured = capsys.readouterr()
    assert captured.out.startswith(f"Usage: {program} auth")
    assert captured.err == ""


def test_typos_and_missing_required_options_write_json_diagnostics(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys, "argv", ["ga4datactl", "reports", "run", "--body", "body.json"]
    )

    with pytest.raises(SystemExit) as exit_info:
        ga4_data_main()

    captured = capsys.readouterr()
    assert exit_info.value.code == 2
    assert captured.out == ""
    diagnostic = json.loads(captured.err)
    assert diagnostic["schemaVersion"] == "marketing-toolbox/v1"
    assert diagnostic["command"] == "ga4datactl"
    assert diagnostic["exitCode"] == 2
    assert diagnostic["category"] == "invalid_arguments"


@pytest.mark.parametrize(
    ("entrypoint", "argv", "usage"),
    [
        (ga4_data_main, ["ga4datactl"], "Usage: ga4datactl [OPTIONS] COMMAND"),
        (
            ga4_data_main,
            ["ga4datactl", "reports"],
            "Usage: ga4datactl reports [OPTIONS] COMMAND",
        ),
        (ga4_admin_main, ["ga4adminctl"], "Usage: ga4adminctl [OPTIONS] COMMAND"),
        (
            ga4_admin_main,
            ["ga4adminctl", "properties"],
            "Usage: ga4adminctl properties [OPTIONS] COMMAND",
        ),
        (gtm_main, ["gtmctl"], "Usage: gtmctl [OPTIONS] COMMAND"),
        (
            gtm_main,
            ["gtmctl", "accounts"],
            "Usage: gtmctl accounts [OPTIONS] COMMAND",
        ),
    ],
)
def test_entrypoints_preserve_typer_no_argument_help(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    argv: list[str],
    usage: str,
) -> None:
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as exit_info:
        entrypoint()

    captured = capsys.readouterr()
    assert exit_info.value.code == 2
    assert captured.out == ""
    assert captured.err.startswith(usage)
    assert "Show this message and exit." in captured.err
    assert not captured.err.startswith("{")


@pytest.mark.parametrize(
    ("entrypoint", "argv", "usage"),
    [
        (ga4_data_main, ["ga4datactl", "--help"], "Usage: ga4datactl"),
        (
            ga4_data_main,
            ["ga4datactl", "reports", "--help"],
            "Usage: ga4datactl reports",
        ),
        (ga4_admin_main, ["ga4adminctl", "--help"], "Usage: ga4adminctl"),
        (
            ga4_admin_main,
            ["ga4adminctl", "properties", "--help"],
            "Usage: ga4adminctl properties",
        ),
    ],
)
def test_ga4_entrypoint_help_remains_plain_typer_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    argv: list[str],
    usage: str,
) -> None:
    monkeypatch.setattr(sys, "argv", argv)

    entrypoint()

    captured = capsys.readouterr()
    assert captured.out.startswith(usage)
    assert "Show this message and exit." in captured.out
    assert captured.err == ""


@pytest.mark.parametrize(
    ("entrypoint", "argv", "command"),
    [
        (ga4_data_main, ["ga4datactl", "--version"], "ga4datactl"),
        (ga4_admin_main, ["ga4adminctl", "--version"], "ga4adminctl"),
    ],
)
def test_ga4_entrypoint_version_remains_an_eager_json_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    argv: list[str],
    command: str,
) -> None:
    monkeypatch.setattr(sys, "argv", argv)

    entrypoint()

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": command,
        "data": {"version": "0.5.1"},
    }
    assert captured.err == ""


@pytest.mark.parametrize(
    ("entrypoint", "argv", "command", "message"),
    [
        (
            ga4_data_main,
            ["ga4datactl", "reports", "run", "--body", "body.json"],
            "ga4datactl",
            "Missing parameter: property_name",
        ),
        (
            ga4_admin_main,
            ["ga4adminctl", "properties", "get"],
            "ga4adminctl",
            "Missing parameter: property_name",
        ),
    ],
)
def test_ga4_entrypoint_parse_errors_remain_json_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    entrypoint: Callable[[], None],
    argv: list[str],
    command: str,
    message: str,
) -> None:
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as exit_info:
        entrypoint()

    captured = capsys.readouterr()
    assert exit_info.value.code == 2
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": command,
        "exitCode": 2,
        "category": "invalid_arguments",
        "message": message,
    }


@pytest.mark.parametrize(
    ("argv", "expected_exit_code", "expected_stdout", "expected_message"),
    [
        (
            ["ga4datactl", "--version"],
            0,
            {"version": "0.5.1"},
            None,
        ),
        (
            ["ga4datactl", "unknown-command"],
            2,
            None,
            "No such command 'unknown-command'.",
        ),
        (
            [
                "ga4datactl",
                "audience-exports",
                "list",
                "--property",
                "properties/1234",
                "--page-size",
                "not-a-number",
            ],
            2,
            None,
            "not-a-number' is not a valid int.",
        ),
    ],
)
def test_entrypoint_normalizes_eager_and_parse_paths(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    expected_exit_code: int,
    expected_stdout: object | None,
    expected_message: str | None,
) -> None:
    monkeypatch.setattr(sys, "argv", argv)

    if expected_exit_code == 0:
        ga4_data_main()
    else:
        with pytest.raises(SystemExit) as exit_info:
            ga4_data_main()
        assert exit_info.value.code == expected_exit_code

    captured = capsys.readouterr()
    if expected_stdout is not None:
        envelope = json.loads(captured.out)
        assert envelope["schemaVersion"] == "marketing-toolbox/v1"
        assert envelope["command"] == "ga4datactl"
        assert envelope["data"] == expected_stdout
        assert captured.err == ""
    else:
        assert captured.out == ""
        diagnostic = json.loads(captured.err)
        assert diagnostic["category"] == "invalid_arguments"
        assert expected_message is not None
        assert expected_message in diagnostic["message"]


def test_reports_run_rejects_nonstandard_json_before_credential_lookup(
    tmp_path: Path,
) -> None:
    body = tmp_path / "nonstandard.json"
    body.write_text(
        '{"metrics": [{"name": "sessions"}], "limit": NaN}', encoding="utf-8"
    )

    result = runner.invoke(
        ga4_data_app,
        ["reports", "run", "--property", "properties/1234", "--body", str(body)],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["category"] == "invalid_request"


def test_audience_exports_create_requires_exactly_one_mutation_control(
    tmp_path: Path,
) -> None:
    body = tmp_path / "create.json"
    body.write_text(
        '{"audience": "properties/1234/audiences/42", '
        '"dimensions": [{"dimensionName": "audienceId"}]}',
        encoding="utf-8",
    )

    for controls in ([], ["--dry-run", "--apply"]):
        result = runner.invoke(
            ga4_data_app,
            [
                "audience-exports",
                "create",
                "--property",
                "properties/1234",
                "--body",
                str(body),
                *controls,
            ],
        )
        assert result.exit_code == 2
        assert result.stdout == ""
        assert json.loads(result.stderr)["message"] == (
            "Specify exactly one of --dry-run or --apply for this mutation."
        )


def test_audience_exports_create_dry_run_writes_intent_without_calling_google(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = tmp_path / "create.json"
    body.write_text(
        '{"audience": "properties/1234/audiences/42", '
        '"dimensions": [{"dimensionName": "audienceId"}]}',
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def create(*args: object, **kwargs: object) -> dict[str, object]:
        called["args"] = args
        called["kwargs"] = kwargs
        return {
            "dryRun": True,
            "request": {
                "parent": "properties/1234",
                "audienceExport": {
                    "audience": "properties/1234/audiences/42",
                    "dimensions": [{"dimensionName": "audienceId"}],
                },
            },
        }

    monkeypatch.setattr(audience_exports, "create_audience_export", create)
    result = runner.invoke(
        ga4_data_app,
        [
            "audience-exports",
            "create",
            "--property",
            "properties/1234",
            "--body",
            str(body),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert called["args"] == (
        "properties/1234",
        {
            "audience": "properties/1234/audiences/42",
            "dimensions": [{"dimensionName": "audienceId"}],
        },
    )
    assert called["kwargs"] == {"apply": False}
    assert json.loads(result.stdout)["data"]["dryRun"] is True


def test_audience_exports_create_apply_calls_adapter_with_apply(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = tmp_path / "create.json"
    body.write_text(
        '{"audience": "properties/1234/audiences/42", '
        '"dimensions": [{"dimensionName": "audienceId"}]}',
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def create(*args: object, **kwargs: object) -> dict[str, object]:
        called["args"] = args
        called["kwargs"] = kwargs
        return {"operationName": "operations/export-1"}

    monkeypatch.setattr(audience_exports, "create_audience_export", create)
    result = runner.invoke(
        ga4_data_app,
        [
            "audience-exports",
            "create",
            "--property",
            "properties/1234",
            "--body",
            str(body),
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert called["kwargs"] == {"apply": True}
    assert json.loads(result.stdout)["data"] == {"operationName": "operations/export-1"}


def test_audience_exports_create_ambiguous_failure_is_sanitized_and_not_retryable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = tmp_path / "create.json"
    body.write_text(
        '{"audience": "properties/1234/audiences/42", '
        '"dimensions": [{"dimensionName": "audienceId"}]}',
        encoding="utf-8",
    )
    sentinel = "UPSTREAM-SECRET-MARKER"
    calls = 0

    class FailingCreateClient:
        def create_audience_export(self, *_args: object, **kwargs: object) -> object:
            nonlocal calls
            calls += 1
            assert kwargs["retry"] is None
            assert (
                kwargs["timeout"]
                == audience_export_operations.CREATE_AUDIENCE_EXPORT_TIMEOUT_SECONDS
            )
            raise exceptions.ServiceUnavailable(sentinel)  # type: ignore[no-untyped-call]

    monkeypatch.setattr(data_transport, "credentials_for_access", lambda _: object())
    monkeypatch.setattr(data_transport, "make_client", lambda _: FailingCreateClient())
    monkeypatch.setattr(
        audience_exports,
        "create_audience_export",
        lambda *args, **kwargs: audience_export_operations.create_audience_export(
            *args, **kwargs
        ),
    )

    result = runner.invoke(
        ga4_data_app,
        [
            "audience-exports",
            "create",
            "--property",
            "properties/1234",
            "--body",
            str(body),
            "--apply",
        ],
    )

    assert calls == 1
    assert result.exit_code == 1
    assert result.stdout == ""
    diagnostic = json.loads(result.stderr)
    assert diagnostic == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "ga4datactl audience-exports create",
        "exitCode": 1,
        "category": "unexpected",
        "message": (
            "Audience export creation may have succeeded. Inspect audience exports "
            "before retrying."
        ),
        "googleStatus": 503,
    }
    assert sentinel not in result.stderr


@pytest.mark.parametrize(
    ("command", "body"),
    [
        ("batch-run", "{}"),
        (
            "pivot-run",
            (
                '{"dimensions": [{"name": ""}], "metrics": [{"name": "eventCount"}], '
                '"pivots": [{"fieldNames": ["country"], "limit": "1"}]}'
            ),
        ),
        (
            "realtime-run",
            '{"metrics": [{"name": "eventCount"}], "limit": "' + "9" * 4301 + '"}',
        ),
    ],
)
def test_report_cli_rejects_local_validation_errors_without_authentication(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, command: str, body: str
) -> None:
    request_body = tmp_path / f"{command}.json"
    request_body.write_text(body, encoding="utf-8")
    monkeypatch.setattr(
        data_transport,
        "credentials_for_access",
        lambda _: pytest.fail("local request errors must not load credentials"),
    )

    result = runner.invoke(
        ga4_data_app,
        [
            "reports",
            command,
            "--property",
            "properties/1234",
            "--body",
            str(request_body),
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["category"] == "invalid_request"


def test_audience_export_query_rejects_out_of_range_offset_without_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        data_transport,
        "credentials_for_access",
        lambda _: pytest.fail("invalid offsets must not load credentials"),
    )

    result = runner.invoke(
        ga4_data_app,
        [
            "audience-exports",
            "query",
            "--property",
            "properties/1234",
            "--name",
            "properties/1234/audienceExports/export-1",
            "--limit",
            "1",
            "--offset",
            str(2**63),
            "--acknowledge-sensitive-data",
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["category"] == "invalid_request"


def test_reports_run_rejects_invalid_body_before_credential_lookup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = tmp_path / "invalid.json"
    body.write_text(
        '{"UNKNOWN_FIELD_SENTINEL": "UNKNOWN_VALUE_SENTINEL"}', encoding="utf-8"
    )
    monkeypatch.setattr(
        data_transport,
        "credentials_for_access",
        lambda _: pytest.fail("invalid request must not load credentials"),
    )

    result = runner.invoke(
        ga4_data_app,
        ["reports", "run", "--property", "properties/1234", "--body", str(body)],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    diagnostic = json.loads(result.stderr)
    assert diagnostic["category"] == "invalid_request"
    assert diagnostic["command"] == "ga4datactl reports run"
    assert "unsupported field" in diagnostic["message"]
    assert "SENTINEL" not in result.stderr


@pytest.mark.parametrize(
    ("path", "command", "request_type"),
    [
        (
            [
                "accounts",
                "access-reports",
                "run",
                "--entity",
                "accounts/1234",
            ],
            "ga4adminctl accounts access-reports run",
            "RunAccessReportRequest",
        ),
        (
            [
                "accounts",
                "change-history",
                "search",
                "--account",
                "accounts/1234",
            ],
            "ga4adminctl accounts change-history search",
            "SearchChangeHistoryEventsRequest",
        ),
    ],
)
def test_admin_access_commands_sanitize_invalid_bodies_before_authentication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    path: list[str],
    command: str,
    request_type: str,
) -> None:
    body = tmp_path / "invalid-access.json"
    body.write_text(
        '{"ACCESS_FIELD_SENTINEL": "ACCESS_VALUE_SENTINEL"}', encoding="utf-8"
    )
    monkeypatch.setattr(
        admin_transport,
        "credentials_for_access",
        lambda _: pytest.fail("invalid request must not load credentials"),
    )

    result = runner.invoke(
        ga4_admin_app,
        [
            *path,
            "--body",
            str(body),
            "--acknowledge-sensitive-data",
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    diagnostic = json.loads(result.stderr)
    assert diagnostic["category"] == "invalid_request"
    assert diagnostic["command"] == command
    assert request_type in diagnostic["message"]
    assert "SENTINEL" not in result.stderr


@pytest.mark.parametrize("alias", ["pageSize", "page_size"])
def test_admin_history_stdin_page_size_rejection_is_sanitized_before_authentication(
    monkeypatch: pytest.MonkeyPatch, alias: str
) -> None:
    monkeypatch.setattr(
        admin_transport,
        "credentials_for_access",
        lambda _: pytest.fail("invalid history page size must not load credentials"),
    )
    monkeypatch.setattr(
        admin_transport,
        "make_client",
        lambda _: pytest.fail("invalid history page size must not construct a client"),
    )

    result = runner.invoke(
        ga4_admin_app,
        [
            "accounts",
            "change-history",
            "search",
            "--account",
            "accounts/1234",
            "--body",
            "-",
            "--acknowledge-sensitive-data",
        ],
        input=json.dumps({alias: -1, "actorEmail": ["HISTORY_ACTOR_SECRET_SENTINEL"]}),
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "ga4adminctl accounts change-history search",
        "exitCode": 2,
        "category": "invalid_request",
        "message": "--body pageSize must be between 1 and 200.",
    }
    assert "HISTORY_ACTOR_SECRET_SENTINEL" not in result.stderr


def test_reports_run_deep_filter_stdin_exhaustion_is_sanitized_before_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        data_transport,
        "credentials_for_access",
        lambda _: pytest.fail("schema exhaustion must not load credentials"),
    )
    monkeypatch.setattr(
        data_transport,
        "make_client",
        lambda _: pytest.fail("schema exhaustion must not construct a client"),
    )

    # Use the installed validator at the unchanged runtime limit, not a universal
    # depth claim. String construction avoids a recursive JSON encoder.
    raw: str | None = None
    recursion_limit = sys.getrecursionlimit()
    for depth in range(32, min(512, recursion_limit // 2) + 1, 32):
        candidate = (
            '{"metrics":[{"name":"eventCount"}],"dimensionFilter":'
            + '{"notExpression":' * depth
            + '{"filter":{"fieldName":"country","stringFilter":'
            '{"value":"FILTER_SECRET_SENTINEL"}}}' + "}" * depth + "}"
        )
        body = data_validation.read_json_body("-", stdin=StringIO(candidate))
        try:
            error = next(
                data_validation.RUN_REPORT_BODY_VALIDATOR.iter_errors(body), None
            )
        except RecursionError:
            raw = candidate
            break
        assert error is None, "deep-filter fixture must otherwise satisfy the schema"
    if raw is None:
        pytest.fail(
            f"No schema exhaustion reproduced within bounded depths at recursion limit {recursion_limit}."
        )

    result = runner.invoke(
        ga4_data_app,
        ["reports", "run", "--property", "properties/1234", "--body", "-"],
        input=raw,
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "ga4datactl reports run",
        "exitCode": 2,
        "category": "invalid_request",
        "message": "--body exceeds the supported request nesting depth.",
    }
    assert "FILTER_SECRET_SENTINEL" not in result.stderr
    assert "RecursionError" not in result.stderr
    assert "maximum recursion" not in result.stderr
    assert sys.getrecursionlimit() == recursion_limit


def test_ga4_admin_properties_get_writes_standard_raw_response_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, object] = {}

    def get(property_name: str) -> dict[str, object]:
        called["property"] = property_name
        return {"name": property_name, "displayName": "Example property"}

    monkeypatch.setattr(admin_properties, "get_property", get)
    result = runner.invoke(
        ga4_admin_app, ["properties", "get", "--property", "properties/1234"]
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert called == {"property": "properties/1234"}
    assert json.loads(result.stdout) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "ga4adminctl properties get",
        "data": {"name": "properties/1234", "displayName": "Example property"},
    }
    assert result.stdout == (
        '{"schemaVersion": "marketing-toolbox/v1", "command": '
        '"ga4adminctl properties get", "data": {"name": "properties/1234", '
        '"displayName": "Example property"}}\n'
    )


def test_ga4_admin_properties_list_exposes_one_page_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, object] = {}

    def list_properties(*args: object, **kwargs: object) -> dict[str, object]:
        called["args"] = args
        called["kwargs"] = kwargs
        return {"properties": [], "nextPageToken": "next-page"}

    monkeypatch.setattr(admin_properties, "list_properties", list_properties)
    result = runner.invoke(
        ga4_admin_app,
        [
            "properties",
            "list",
            "--filter",
            "ancestor:accounts/5678",
            "--page-size",
            "25",
            "--page-token",
            "prior-page",
            "--show-deleted",
        ],
    )

    assert result.exit_code == 0
    assert result.stderr == ""
    assert called == {
        "args": ("ancestor:accounts/5678",),
        "kwargs": {
            "page_size": 25,
            "page_token": "prior-page",
            "show_deleted": True,
        },
    }
    assert json.loads(result.stdout)["data"] == {
        "properties": [],
        "nextPageToken": "next-page",
    }


def test_ga4_admin_properties_list_requires_the_documented_filter(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["ga4adminctl", "properties", "list"])

    with pytest.raises(SystemExit) as exit_info:
        ga4_admin_main()

    captured = capsys.readouterr()
    assert exit_info.value.code == 2
    assert captured.out == ""
    diagnostic = json.loads(captured.err)
    assert diagnostic["category"] == "invalid_arguments"
    assert "filter" in diagnostic["message"]


def test_ga4_entrypoint_normalizes_non_finite_success_data_as_unexpected_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Strict JSON serialization failures stay inside the console boundary."""
    monkeypatch.setattr(metadata, "get_metadata", lambda _: {"ratio": float("nan")})
    monkeypatch.setattr(
        sys, "argv", ["ga4datactl", "metadata", "get", "--property", "properties/1234"]
    )

    with pytest.raises(SystemExit) as exit_info:
        ga4_data_main()

    captured = capsys.readouterr()
    assert exit_info.value.code == 1
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "ga4datactl",
        "exitCode": 1,
        "category": "unexpected_failure",
        "message": "Unexpected CLI failure. Inspect local diagnostics.",
    }
    assert "NaN" not in captured.err


def test_gtm_entrypoint_version_is_eager_and_uses_shared_json_success_envelope(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["gtmctl", "--version"])

    gtm_main()

    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "gtmctl",
        "data": {"version": "0.5.1"},
    }
    assert captured.err == ""


@pytest.mark.parametrize(
    "argv",
    [
        ["gtmctl", "unknown-command"],
        ["gtmctl", "accounts", "get"],
    ],
)
def test_gtm_entrypoint_parse_errors_are_json_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(SystemExit) as exit_info:
        gtm_main()

    captured = capsys.readouterr()
    assert exit_info.value.code == 2
    assert captured.out == ""
    diagnostic = json.loads(captured.err)
    assert diagnostic["schemaVersion"] == "marketing-toolbox/v1"
    assert diagnostic["command"] == "gtmctl"
    assert diagnostic["exitCode"] == 2
    assert diagnostic["category"] == "invalid_arguments"


def test_api_error_paths_keep_shared_safe_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Representative command paths never render synthetic upstream diagnostics."""
    sentinel = "UPSTREAM-SECRET-MARKER"

    def raise_error(error: BaseException) -> object:
        raise error

    from googleapiclient.errors import HttpError
    from httplib2 import Response

    from ga4adminctl.foundation.errors import normalize_google_error as admin_error
    from ga4datactl.operations import metadata as metadata_operations
    from gtmctl.foundation.errors import normalize_google_error as gtm_error

    monkeypatch.setattr(
        admin_properties,
        "get_property",
        lambda _: raise_error(admin_error(exceptions.PermissionDenied(sentinel))),
    )
    monkeypatch.setattr(data_transport, "credentials_for_access", lambda _: object())
    monkeypatch.setattr(
        data_transport,
        "make_client",
        lambda _: type(
            "RetryingMetadataClient",
            (),
            {
                "get_metadata": lambda *_args, **_kwargs: raise_error(
                    exceptions.RetryError(
                        "retry exhausted", exceptions.ServiceUnavailable(sentinel)
                    )
                )
            },
        )(),
    )
    monkeypatch.setattr(
        metadata,
        "get_metadata",
        lambda property_name: metadata_operations.get_metadata(property_name),
    )
    monkeypatch.setattr(
        "gtmctl.commands.accounts.reads.get_account",
        lambda _: raise_error(
            gtm_error(
                HttpError(
                    Response({"status": "409"}),
                    f'{{"error": {{"message": "{sentinel}"}}}}'.encode(),
                )
            )
        ),
    )

    admin_result = runner.invoke(
        ga4_admin_app, ["properties", "get", "--property", "properties/1234"]
    )
    data_result = runner.invoke(
        ga4_data_app, ["metadata", "get", "--property", "properties/1234"]
    )
    gtm_result = runner.invoke(gtm_app, ["accounts", "get", "--path", "accounts/1"])

    for result, category, status in (
        (admin_result, "authentication", 403),
        (data_result, "retryable", 503),
        (gtm_result, "conflict", 409),
    ):
        diagnostic = json.loads(result.stderr)
        assert result.exit_code == diagnostic["exitCode"]
        assert diagnostic["schemaVersion"] == "marketing-toolbox/v1"
        assert diagnostic["category"] == category
        assert diagnostic["googleStatus"] == status
        assert sentinel not in result.stderr
        assert result.stdout == ""


def test_typer_compatibility_adapter_matches_the_pinned_typer_layout() -> None:
    """Make the Typer 0.27 vendored exception dependency explicit and checked."""
    from marketing_common.typer_compat import NoArgsIsHelpError, UsageError

    assert issubclass(NoArgsIsHelpError, UsageError)
