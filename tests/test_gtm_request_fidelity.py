"""Request-fidelity contracts for guarded GTM mutations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.foundation.body import body_sha256, read_json_object
from gtmctl.foundation.validation import RequestValidationError
from gtmctl.operations import mutations

PATH = "accounts/1/containers/2"
WORKSPACE = f"{PATH}/workspaces/3"
FOLDER = f"{WORKSPACE}/folders/4"


def _data(result: Any) -> dict[str, Any]:
    return json.loads(result.output)["data"]


def _body_file(tmp_path: Path, contents: str = '{"name":"folder"}') -> str:
    body = tmp_path / "body.json"
    body.write_text(contents)
    return str(body)


def test_folder_move_plan_and_apply_keep_optional_body_and_all_entity_lists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = {"folderId": "destination"}
    body_path = _body_file(tmp_path, json.dumps(body))
    arguments = [
        "accounts",
        "containers",
        "workspaces",
        "folders",
        "move-entities-to-folder",
        "--path",
        FOLDER,
        "--body",
        body_path,
        "--variable-id",
        "1",
        "--variable-id",
        "2",
        "--trigger-id",
        "3",
        "--tag-id",
        "4",
    ]

    dry_run = CliRunner().invoke(app, [*arguments, "--dry-run"])

    assert dry_run.exit_code == 0
    assert _data(dry_run) == {
        "applied": False,
        "mode": "dry-run",
        "operation": "folders.move-entities-to-folder",
        "target": FOLDER,
        "bodySha256": body_sha256(body),
        "variableId": ["1", "2"],
        "triggerId": ["3"],
        "tagId": ["4"],
    }

    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(
        mutations,
        "move_folder_entities_to_folder",
        lambda path, **kwargs: (calls.append((path, kwargs)), {})[1],
    )
    applied = CliRunner().invoke(app, [*arguments, "--apply"])

    assert applied.exit_code == 0
    assert calls == [
        (
            FOLDER,
            {
                "body": body,
                "variable_ids": ["1", "2"],
                "trigger_ids": ["3"],
                "tag_ids": ["4"],
            },
        )
    ]


@pytest.mark.parametrize(
    ("command", "path_option", "acknowledgement"),
    [
        ("create", "--parent", None),
        ("delete", "--path", "--acknowledge-built-in-variable-delete"),
    ],
)
def test_built_in_variable_types_remain_repeated_from_cli_to_adapter(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
    path_option: str,
    acknowledgement: str | None,
) -> None:
    calls: list[tuple[str, list[str] | None]] = []
    operation = (
        "create_built_in_variable"
        if command == "create"
        else "delete_built_in_variable"
    )
    monkeypatch.setattr(
        mutations,
        operation,
        lambda path, variable_types: (
            calls.append((path, variable_types)),
            {},
        )[1],
    )
    target = WORKSPACE if command == "create" else f"{WORKSPACE}/built_in_variables"
    arguments = [
        "accounts",
        "containers",
        "workspaces",
        "built-in-variables",
        command,
        path_option,
        target,
        "--type",
        "pageUrl",
        "--type",
        "clickId",
    ]
    if acknowledgement is not None:
        arguments.append(acknowledgement)

    result = CliRunner().invoke(app, [*arguments, "--apply"])

    assert result.exit_code == 0
    assert calls == [(target, ["pageUrl", "clickId"])]


def test_gtm_dry_run_help_is_local_plan_not_google_schema_validation() -> None:
    result = CliRunner().invoke(
        app,
        ["accounts", "containers", "workspaces", "variables", "create", "--help"],
    )

    assert result.exit_code == 0
    normalized = " ".join(result.stdout.split())
    assert "Check local command inputs and print a no-network plan." in normalized
    assert "does not validate the body against the Discovery schema" in normalized
    assert "Validate and print" not in normalized


def test_constant_variable_body_dry_run_and_apply_preserve_exact_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body = {
        "name": "Example constant",
        "type": "c",
        "parameter": [{"type": "template", "key": "value", "value": "example"}],
    }
    body_path = _body_file(tmp_path, json.dumps(body))
    arguments = [
        "accounts",
        "containers",
        "workspaces",
        "variables",
        "create",
        "--parent",
        WORKSPACE,
        "--body",
        body_path,
    ]

    dry_run = CliRunner().invoke(app, [*arguments, "--dry-run"])

    assert dry_run.exit_code == 0
    assert _data(dry_run) == {
        "applied": False,
        "mode": "dry-run",
        "operation": "variables.create",
        "target": WORKSPACE,
        "bodySha256": body_sha256(body),
    }

    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(
        mutations,
        "create_variable",
        lambda parent, request_body: (calls.append((parent, request_body)), {})[1],
    )
    applied = CliRunner().invoke(app, [*arguments, "--apply"])

    assert applied.exit_code == 0
    assert calls == [(WORKSPACE, body)]


def test_optional_fingerprint_is_omitted_or_forwarded_and_publish_stays_guarded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    body_path = _body_file(tmp_path, '{"name":"tag"}')
    calls: list[tuple[str, dict[str, Any], str | None]] = []
    monkeypatch.setattr(
        mutations,
        "update_tag",
        lambda path, body, fingerprint: (calls.append((path, body, fingerprint)), {})[
            1
        ],
    )
    tag_path = f"{WORKSPACE}/tags/4"

    omitted = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "update",
            "--path",
            tag_path,
            "--body",
            body_path,
            "--apply",
        ],
    )
    malformed = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "update",
            "--path",
            tag_path,
            "--body",
            body_path,
            "--fingerprint",
            " ",
            "--dry-run",
        ],
    )

    assert omitted.exit_code == 0
    assert calls == [(tag_path, {"name": "tag"}, None)]
    assert malformed.exit_code == 2
    assert "must be a non-empty" in malformed.output

    publish_path = f"{PATH}/versions/4"
    publish = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "versions",
            "publish",
            "--path",
            publish_path,
            "--acknowledge-publish",
            "--dry-run",
        ],
    )
    missing_acknowledgement = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "versions",
            "publish",
            "--path",
            publish_path,
            "--apply",
        ],
    )

    assert publish.exit_code == 0
    assert "fingerprint" not in _data(publish)
    assert missing_acknowledgement.exit_code == 2
    assert "--acknowledge-publish" in missing_acknowledgement.output


@pytest.mark.parametrize(
    "contents",
    [
        "NaN",
        "[]",
        '{"value":NaN}',
        '{"value":Infinity}',
        '{"value":-Infinity}',
        '{"value":1e999}',
        '{"nested":{"value":-1e999}}',
    ],
)
def test_gtm_body_intake_rejects_non_objects_and_nonfinite_numbers(
    tmp_path: Path, contents: str
) -> None:
    with pytest.raises(RequestValidationError, match="valid JSON|JSON object"):
        read_json_object(_body_file(tmp_path, contents))


@pytest.mark.parametrize("mode", ["--dry-run", "--apply"])
def test_numeric_json_overflow_fails_before_dry_run_or_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: str
) -> None:
    calls: list[tuple[Any, ...]] = []
    monkeypatch.setattr(
        mutations,
        "create_tag",
        lambda *args: (calls.append(args), {})[1],
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "create",
            "--parent",
            WORKSPACE,
            "--body",
            _body_file(tmp_path, '{"value":1e999}'),
            mode,
        ],
    )

    assert result.exit_code == 2
    assert json.loads(result.output)["category"] == "invalid_request"
    assert "valid JSON" in result.output
    assert "dry-run" not in result.output
    assert calls == []
