"""Contracts for guarded GTM Gallery custom-template imports."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations


class FakeRequest:
    def __init__(self) -> None:
        self.retries: list[int] = []

    def execute(self, *, num_retries: int = 0) -> dict[str, str]:
        self.retries.append(num_retries)
        return {"templateId": "4"}


class FakeTemplatesResource:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.requests: list[FakeRequest] = []

    def accounts(self) -> FakeTemplatesResource:
        return self

    def containers(self) -> FakeTemplatesResource:
        return self

    def workspaces(self) -> FakeTemplatesResource:
        return self

    def templates(self) -> FakeTemplatesResource:
        return self

    def import_from_gallery(self, **kwargs: Any) -> FakeRequest:
        self.calls.append(("import_from_gallery", kwargs))
        request = FakeRequest()
        self.requests.append(request)
        return request


def _body_file(
    tmp_path: Any,
    contents: str = '{"galleryOwner":"owner","gallerySha":"sha","galleryRepository":"repository"}',
) -> str:
    path = tmp_path / "gallery.json"
    path.write_text(contents)
    return str(path)


def _args(body: str, *extra: str) -> list[str]:
    return [
        "accounts",
        "containers",
        "workspaces",
        "templates",
        "import-from-gallery",
        "--parent",
        "accounts/1/containers/2/workspaces/3",
        "--body",
        body,
        *extra,
    ]


def test_gallery_import_uses_exact_official_request_and_edit_scope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeTemplatesResource()
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )

    assert mutations.import_template_from_gallery(
        "accounts/1/containers/2/workspaces/3",
        gallery_owner="owner",
        gallery_sha="sha",
        gallery_repository="repository",
        acknowledge_permissions=True,
        service_factory=lambda _: service,
    ) == {"templateId": "4"}
    assert service.calls == [
        (
            "import_from_gallery",
            {
                "parent": "accounts/1/containers/2/workspaces/3",
                "galleryOwner": "owner",
                "gallerySha": "sha",
                "galleryRepository": "repository",
                "acknowledgePermissions": True,
            },
        )
    ]
    assert [request.retries for request in service.requests] == [[0]]
    assert scopes == [[mutations.TAG_MANAGER_EDIT_SCOPE]]


def test_gallery_import_dry_run_is_deterministic_redacted_and_local(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    monkeypatch.setattr(
        mutations,
        "service_account_credentials",
        lambda _: pytest.fail("dry run must not load credentials"),
    )
    body = _body_file(tmp_path)
    args = _args(body, "--acknowledge-template-import-permissions", "--dry-run")

    first = CliRunner().invoke(app, args)
    second = CliRunner().invoke(app, args)

    assert first.exit_code == second.exit_code == 0
    assert first.output == second.output
    data = json.loads(first.output)["data"]
    assert data["operation"] == "templates.import-from-gallery"
    assert data["permissionsAcknowledged"] is True
    assert len(data["bodySha256"]) == 64
    assert "owner" not in first.output
    assert "repository" not in first.output


def test_gallery_import_requires_permission_acknowledgement(tmp_path: Any) -> None:
    result = CliRunner().invoke(app, _args(_body_file(tmp_path), "--apply"))

    assert result.exit_code == 2
    assert "--acknowledge-template-import-permissions" in result.output
