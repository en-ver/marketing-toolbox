"""Focused contracts for ordinary GTM workspace tag mutations."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[int] = []

    def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
        self.calls.append(num_retries)
        return self.response


class FakeTagResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def accounts(self) -> FakeTagResource:
        return self

    def containers(self) -> FakeTagResource:
        return self

    def workspaces(self) -> FakeTagResource:
        return self

    def tags(self) -> FakeTagResource:
        return self

    def __getattr__(self, name: str) -> Any:
        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            return FakeRequest(self.response)

        return request


@pytest.fixture
def fake_service(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FakeTagResource, list[list[str]]]:
    service = FakeTagResource({"tagId": "4"})
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )
    return service, scopes


@pytest.mark.parametrize(
    ("operation", "args", "expected"),
    [
        (
            mutations.create_tag,
            ("accounts/1/containers/2/workspaces/3", {"name": "tag"}),
            (
                "create",
                {
                    "parent": "accounts/1/containers/2/workspaces/3",
                    "body": {"name": "tag"},
                },
            ),
        ),
        (
            mutations.update_tag,
            ("accounts/1/containers/2/workspaces/3/tags/4", {"name": "tag"}, "abc"),
            (
                "update",
                {
                    "path": "accounts/1/containers/2/workspaces/3/tags/4",
                    "body": {"name": "tag"},
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.revert_tag,
            ("accounts/1/containers/2/workspaces/3/tags/4", "abc"),
            (
                "revert",
                {
                    "path": "accounts/1/containers/2/workspaces/3/tags/4",
                    "fingerprint": "abc",
                },
            ),
        ),
        (
            mutations.delete_tag,
            ("accounts/1/containers/2/workspaces/3/tags/4",),
            ("delete", {"path": "accounts/1/containers/2/workspaces/3/tags/4"}),
        ),
    ],
)
def test_tag_mutations_use_one_official_edit_request(
    fake_service: tuple[FakeTagResource, list[list[str]]],
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service, scopes = fake_service

    response = operation(*args, service_factory=lambda _: service)

    assert response == service.response
    assert service.calls == [expected]
    assert scopes == [[mutations.TAG_MANAGER_EDIT_SCOPE]]


def test_tag_update_omits_an_unsupplied_optional_fingerprint(
    fake_service: tuple[FakeTagResource, list[list[str]]],
) -> None:
    service, _scopes = fake_service

    mutations.update_tag(
        "accounts/1/containers/2/workspaces/3/tags/4",
        {"name": "tag"},
        None,
        service_factory=lambda _: service,
    )

    assert service.calls == [
        (
            "update",
            {
                "path": "accounts/1/containers/2/workspaces/3/tags/4",
                "body": {"name": "tag"},
            },
        )
    ]


def _body_file(tmp_path: Any, content: str = '{"name":"private"}') -> str:
    path = tmp_path / "tag.json"
    path.write_text(content)
    return str(path)


def test_tag_create_dry_run_is_deterministic_and_never_calls_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    monkeypatch.setattr(
        mutations, "create_tag", lambda *_: pytest.fail("dry run must not mutate")
    )
    body = _body_file(tmp_path)
    args = [
        "accounts",
        "containers",
        "workspaces",
        "tags",
        "create",
        "--parent",
        "accounts/1/containers/2/workspaces/3",
        "--body",
        body,
        "--dry-run",
    ]

    first = CliRunner().invoke(app, args)
    second = CliRunner().invoke(app, args)

    assert first.exit_code == second.exit_code == 0
    assert first.output == second.output
    envelope = json.loads(first.output)
    assert envelope["data"] == {
        "applied": False,
        "mode": "dry-run",
        "operation": "tags.create",
        "target": "accounts/1/containers/2/workspaces/3",
        "bodySha256": "d19bde18795e874532c1b0880acf54a7fba0ee482f4a31110c99ea36648a1d78",
    }
    assert "private" not in first.output


@pytest.mark.parametrize(
    "mode_args",
    [[], ["--dry-run", "--apply"]],
)
def test_tag_mutations_require_exactly_one_execution_mode(
    tmp_path: Any, mode_args: list[str]
) -> None:
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "update",
            "--path",
            "accounts/1/containers/2/workspaces/3/tags/4",
            "--body",
            _body_file(tmp_path),
            "--fingerprint",
            "abc",
            *mode_args,
        ],
    )

    assert result.exit_code == 2
    assert "exactly one" in result.output


def test_tag_apply_maps_cli_values_to_mutation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    calls: list[tuple[str, dict[str, Any], str]] = []
    monkeypatch.setattr(
        mutations,
        "update_tag",
        lambda path, body, fingerprint: (
            calls.__iadd__([(path, body, fingerprint)]),
            {"tagId": "4"},
        )[1],
    )

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "update",
            "--path",
            "accounts/1/containers/2/workspaces/3/tags/4",
            "--body",
            _body_file(tmp_path),
            "--fingerprint",
            "abc",
            "--apply",
        ],
    )

    assert result.exit_code == 0
    assert calls == [
        ("accounts/1/containers/2/workspaces/3/tags/4", {"name": "private"}, "abc")
    ]
    assert '"tagId": "4"' in result.output


def test_tag_create_accepts_body_from_standard_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, Any]]] = []
    monkeypatch.setattr(
        mutations,
        "create_tag",
        lambda parent, body: (
            calls.__iadd__([(parent, body)]),
            {"tagId": "4"},
        )[1],
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
            "accounts/1/containers/2/workspaces/3",
            "--body",
            "-",
            "--apply",
        ],
        input='{"name":"stdin tag"}',
    )

    assert result.exit_code == 0
    assert calls == [("accounts/1/containers/2/workspaces/3", {"name": "stdin tag"})]


def test_invalid_tag_route_is_rejected_before_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("credentials must not load before route validation"),
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
            "not-a-workspace",
            "--body",
            _body_file(tmp_path),
            "--apply",
        ],
    )

    assert result.exit_code == 2
    assert "canonical GTM" in result.output


def test_delete_requires_tag_specific_acknowledgement(tmp_path: Any) -> None:
    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "delete",
            "--path",
            "accounts/1/containers/2/workspaces/3/tags/4",
            "--apply",
        ],
    )

    assert result.exit_code == 2
    assert "--acknowledge-tag-delete" in result.output


def test_body_must_be_a_json_object_without_loading_credentials(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("credentials must not load for bad bodies"),
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
            "accounts/1/containers/2/workspaces/3",
            "--body",
            _body_file(tmp_path, "[]"),
            "--apply",
        ],
    )

    assert result.exit_code == 2
    assert "JSON object" in result.output


def test_execute_mutation_normalizes_empty_success_response(monkeypatch: Any) -> None:
    class EmptyRequest:
        def __init__(self, response: list[Any] | str | bytes | None) -> None:
            self.response = response

        def execute(self, *, num_retries: int = 0) -> list[Any] | str | bytes | None:
            assert num_retries == 0
            return self.response

    monkeypatch.setattr(
        mutations, "service_account_credentials", lambda scopes: object()
    )

    assert (
        mutations.execute_mutation(
            "test empty",
            lambda service: EmptyRequest(None),
            service_factory=lambda credentials: object(),
        )
        == {}
    )
    for response in ("", b"", b"{}\n"):
        request = EmptyRequest(response)

        def request_factory(
            _service: Any, request: EmptyRequest = request
        ) -> EmptyRequest:
            return request

        assert (
            mutations.execute_mutation(
                "test empty response",
                request_factory,
                service_factory=lambda credentials: object(),
            )
            == {}
        )
