"""Keep the GA4 Admin public command tree complete and discoverable."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer import _click as click
from typer.main import get_command
from typer.testing import CliRunner

from ga4adminctl.cli import app
from ga4adminctl.operations import mutations


def _leaf_commands(
    command: click.Command, prefix: tuple[str, ...] = ()
) -> dict[str, click.Command]:
    """Return concrete public commands keyed by their full CLI path."""
    children = getattr(command, "commands", None)
    if children is None:
        return {"ga4adminctl " + " ".join(prefix): command}

    leaves: dict[str, click.Command] = {}
    for name, child in children.items():
        leaves.update(_leaf_commands(child, (*prefix, name)))
    return leaves


def test_ga4_admin_api_command_tree_is_complete_and_excludes_unsupported_paths() -> (
    None
):
    """Detect removed API leaves without maintaining a prose command catalog."""
    leaves = _leaf_commands(get_command(app))
    native_auth_paths = {
        "ga4adminctl auth login",
        "ga4adminctl auth status",
        "ga4adminctl auth forget",
        "ga4adminctl auth revoke",
    }
    api_paths = set(leaves) - {"ga4adminctl sdk schema"} - native_auth_paths

    assert len(api_paths) == 50
    assert native_auth_paths <= set(leaves)
    assert "ga4adminctl sdk schema" in leaves
    assert not api_paths.intersection(
        {
            "ga4adminctl audiences create",
            "ga4adminctl properties conversion-events create",
            "ga4adminctl properties conversion-events delete",
            "ga4adminctl properties conversion-events get",
            "ga4adminctl properties conversion-events list",
            "ga4adminctl properties conversion-events patch",
        }
    )


DESTRUCTIVE_CONFIRMATION_CASES = [
    pytest.param(
        ["accounts", "delete"],
        "accounts/1234",
        "delete_account",
        [],
        id="account-delete",
    ),
    pytest.param(
        ["properties", "delete"],
        "properties/1234",
        "delete_property",
        [],
        id="property-delete",
    ),
    pytest.param(
        ["properties", "data-streams", "delete"],
        "properties/1234/dataStreams/5678",
        "delete_data_stream",
        [],
        id="data-stream-delete",
    ),
    pytest.param(
        ["properties", "custom-dimensions", "archive"],
        "properties/1234/customDimensions/5678",
        "archive_custom_dimension",
        [],
        id="custom-dimension-archive",
    ),
    pytest.param(
        ["properties", "custom-metrics", "archive"],
        "properties/1234/customMetrics/5678",
        "archive_custom_metric",
        [],
        id="custom-metric-archive",
    ),
    pytest.param(
        ["properties", "firebase-links", "delete"],
        "properties/1234/firebaseLinks/5678",
        "delete_firebase_link",
        [],
        id="firebase-link-delete",
    ),
    pytest.param(
        ["properties", "google-ads-links", "delete"],
        "properties/1234/googleAdsLinks/5678",
        "delete_google_ads_link",
        [],
        id="google-ads-link-delete",
    ),
    pytest.param(
        ["properties", "key-events", "delete"],
        "properties/1234/keyEvents/5678",
        "delete_key_event",
        [],
        id="key-event-delete",
    ),
    pytest.param(
        ["properties", "data-streams", "measurement-protocol-secrets", "delete"],
        "properties/1234/dataStreams/5678/measurementProtocolSecrets/9012",
        "delete_measurement_protocol_secret",
        ["--acknowledge-sensitive-data"],
        id="measurement-protocol-secret-delete",
    ),
]


def test_exactly_nine_destructive_leaves_expose_optional_target_confirmation() -> None:
    leaves = _leaf_commands(get_command(app))
    expected_paths = {
        "ga4adminctl accounts delete",
        "ga4adminctl properties delete",
        "ga4adminctl properties data-streams delete",
        "ga4adminctl properties custom-dimensions archive",
        "ga4adminctl properties custom-metrics archive",
        "ga4adminctl properties firebase-links delete",
        "ga4adminctl properties google-ads-links delete",
        "ga4adminctl properties key-events delete",
        "ga4adminctl properties data-streams measurement-protocol-secrets delete",
    }
    actual_paths = {
        path
        for path, command in leaves.items()
        if any(parameter.name == "confirm_resource" for parameter in command.params)
    }

    assert actual_paths == expected_paths
    for path in expected_paths:
        option = next(
            parameter
            for parameter in leaves[path].params
            if parameter.name == "confirm_resource"
        )
        assert option.required is False
        assert "--confirm-resource" in option.opts


@pytest.mark.parametrize(
    ("path", "name", "method", "extra_options"), DESTRUCTIVE_CONFIRMATION_CASES
)
def test_destructive_confirmation_is_required_for_apply_and_exact_in_both_modes(
    monkeypatch: pytest.MonkeyPatch,
    path: list[str],
    name: str,
    method: str,
    extra_options: list[str],
) -> None:
    dispatched: list[str] = []

    def no_network(
        _request: Any, method_name: str, _render: Any, **_kwargs: Any
    ) -> dict[str, Any]:
        dispatched.append(method_name)
        return {}

    monkeypatch.setattr(mutations, "_write_v1beta", no_network)
    runner = CliRunner()
    arguments = [*path, "--name", name, *extra_options]

    dry_run_without_confirmation = runner.invoke(app, [*arguments, "--dry-run"])
    assert dry_run_without_confirmation.exit_code == 0
    assert dispatched == []

    dry_run_with_confirmation = runner.invoke(
        app, [*arguments, "--dry-run", "--confirm-resource", name]
    )
    assert dry_run_with_confirmation.exit_code == 0
    assert dispatched == []

    for mode in ("dry-run", "apply"):
        mismatched = runner.invoke(
            app,
            [
                *arguments,
                f"--{mode}",
                "--confirm-resource",
                "mismatched-confirmation-sentinel",
            ],
        )
        assert mismatched.exit_code == 2
        assert mismatched.stdout == ""
        assert json.loads(mismatched.stderr)["category"] == "invalid_request"
        assert "mismatched-confirmation-sentinel" not in mismatched.stderr
        assert dispatched == []

    missing_apply_confirmation = runner.invoke(app, [*arguments, "--apply"])
    assert missing_apply_confirmation.exit_code == 2
    assert missing_apply_confirmation.stdout == ""
    assert (
        json.loads(missing_apply_confirmation.stderr)["category"] == "invalid_request"
    )
    assert dispatched == []

    exact_apply_confirmation = runner.invoke(
        app, [*arguments, "--apply", "--confirm-resource", name]
    )
    assert exact_apply_confirmation.exit_code == 0
    assert dispatched == [method]


@pytest.mark.parametrize("confirmation", ["accounts/1234 ", "ACCOUNTS/1234"])
def test_destructive_confirmation_is_not_normalized(confirmation: str) -> None:
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "delete",
            "--name",
            "accounts/1234",
            "--apply",
            "--confirm-resource",
            confirmation,
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["category"] == "invalid_request"


def test_confirmation_failure_precedes_name_validation_and_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    name = "accounts/confirmation-name-sentinel/invalid"
    confirmation = "confirmation-value-sentinel"

    def forbid_credentials(_: object) -> object:
        pytest.fail("invalid confirmation must not load credentials")

    def forbid_client_factory(_: object) -> object:
        pytest.fail("invalid confirmation must not create a client or dispatch an RPC")

    monkeypatch.setattr(mutations, "service_account_credentials", forbid_credentials)
    monkeypatch.setattr(mutations, "_make_properties_client", forbid_client_factory)

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "delete",
            "--name",
            name,
            "--apply",
            "--confirm-resource",
            confirmation,
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert name not in result.stderr
    assert confirmation not in result.stderr
    assert json.loads(result.stderr)["category"] == "invalid_request"
    assert "--confirm-resource must exactly match --name" in result.stderr


def test_ordinary_destructive_mode_validation_precedes_confirmation() -> None:
    arguments = [
        "accounts",
        "delete",
        "--name",
        "accounts/1234",
        "--confirm-resource",
        "mismatched-confirmation-sentinel",
    ]

    for modes in ([], ["--dry-run", "--apply"]):
        result = CliRunner().invoke(app, [*arguments, *modes])

        assert result.exit_code == 2
        assert result.stdout == ""
        assert json.loads(result.stderr)["category"] == "invalid_request"
        assert "Specify exactly one of --dry-run or --apply" in result.stderr
        assert "--confirm-resource must exactly match --name" not in result.stderr


def test_secret_delete_keeps_acknowledgement_then_mode_then_confirmation_order() -> (
    None
):
    arguments = [
        "properties",
        "data-streams",
        "measurement-protocol-secrets",
        "delete",
        "--name",
        "properties/1234/dataStreams/5678/measurementProtocolSecrets/9012",
    ]

    missing_ack = CliRunner().invoke(
        app,
        [
            *arguments,
            "--dry-run",
            "--apply",
            "--confirm-resource",
            "mismatched-confirmation-sentinel",
        ],
    )
    assert missing_ack.exit_code == 2
    assert missing_ack.stdout == ""
    assert json.loads(missing_ack.stderr)["category"] == "invalid_request"
    assert "--acknowledge-sensitive-data is required" in missing_ack.stderr
    assert "Specify exactly one of --dry-run or --apply" not in missing_ack.stderr

    invalid_mode = CliRunner().invoke(
        app,
        [
            *arguments,
            "--acknowledge-sensitive-data",
            "--confirm-resource",
            "mismatched-confirmation-sentinel",
        ],
    )
    assert invalid_mode.exit_code == 2
    assert invalid_mode.stdout == ""
    assert json.loads(invalid_mode.stderr)["category"] == "invalid_request"
    assert "Specify exactly one of --dry-run or --apply" in invalid_mode.stderr
    assert "--confirm-resource must exactly match --name" not in invalid_mode.stderr

    mismatched_confirmation = CliRunner().invoke(
        app,
        [
            *arguments,
            "--acknowledge-sensitive-data",
            "--apply",
            "--confirm-resource",
            "mismatch",
        ],
    )
    assert mismatched_confirmation.exit_code == 2
    assert mismatched_confirmation.stdout == ""
    assert json.loads(mismatched_confirmation.stderr)["category"] == "invalid_request"
    assert (
        "--confirm-resource must exactly match --name" in mismatched_confirmation.stderr
    )


def test_exact_confirmation_still_validates_resource_name_before_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbid_credentials(_: object) -> object:
        pytest.fail("invalid names must not load credentials")

    def forbid_client_factory(_: object) -> object:
        pytest.fail("invalid names must not create a client or dispatch an RPC")

    monkeypatch.setattr(mutations, "service_account_credentials", forbid_credentials)
    monkeypatch.setattr(mutations, "_make_properties_client", forbid_client_factory)
    name = "accounts/not/a/canonical/name"

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "delete",
            "--name",
            name,
            "--apply",
            "--confirm-resource",
            name,
        ],
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr)["category"] == "invalid_request"
    assert "--name must be a canonical GA4 resource name" in result.stderr


def test_ga4_admin_leaf_commands_have_descriptions_and_working_help() -> None:
    """Keep every registered API leaf discoverable through generated help."""
    runner = CliRunner()
    for path, command in _leaf_commands(get_command(app)).items():
        assert command.help and command.help.strip(), path
        result = runner.invoke(app, [*path.split()[1:], "--help"])
        assert result.exit_code == 0, f"{path}: {result.output}"
