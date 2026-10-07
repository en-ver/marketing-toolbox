"""Contracts for guarded GTM Gallery custom-template imports."""

from __future__ import annotations

import json
import socket
from collections.abc import Callable
from typing import Any

import pytest
import urllib3.connectionpool
from httplib2 import Response
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.operations import mutations, transport
from marketing_common import auth


class FakeRequest:
    def __init__(self) -> None:
        self.retries: list[int] = []
        self.callbacks: list[Callable[[Response], None]] = []

    def add_response_callback(self, callback: Callable[[Response], None]) -> None:
        self.callbacks.append(callback)

    def execute(self, *, num_retries: int = 0) -> dict[str, str]:
        self.retries.append(num_retries)
        for callback in self.callbacks:
            callback(Response({"status": "200"}))
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


def _install_apply_dispatch_barriers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make an accidental Gallery apply dispatch fail before external access."""

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Gallery validation must not use credentials or external services")

    class BlockedSocket(socket.socket):
        def connect(self, address: Any) -> None:
            del address
            pytest.fail("Gallery validation must not open sockets")

        def connect_ex(self, address: Any) -> int:
            del address
            pytest.fail("Gallery validation must not open sockets")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "socket", BlockedSocket)
    monkeypatch.setattr(urllib3.connectionpool.HTTPConnectionPool, "urlopen", forbidden)
    monkeypatch.setattr(
        urllib3.connectionpool.HTTPSConnectionPool, "urlopen", forbidden
    )
    monkeypatch.setattr(auth.google.auth, "default", forbidden)
    monkeypatch.setattr(transport, "credentials_for_access", forbidden)
    monkeypatch.setattr(mutations, "execute_mutation", forbidden)
    monkeypatch.setattr(transport, "make_mutation_service", forbidden)
    monkeypatch.setattr(transport, "build", forbidden)
    monkeypatch.setattr("googleapiclient.discovery.build", forbidden)


def test_gallery_import_descriptor_is_the_exact_query_parameter_envelope() -> None:
    result = CliRunner().invoke(
        app,
        [
            "sdk",
            "schema",
            "--command",
            "accounts containers workspaces templates import-from-gallery",
        ],
    )

    assert result.exit_code == 0, result.output
    body = json.loads(result.stdout)["data"]["request"]["body"]
    assert body["type"] == "official-query-parameter-envelope"
    assert {field["name"] for field in body["fields"]} == {
        "galleryOwner",
        "gallerySha",
        "galleryRepository",
    }
    assert len(body["fields"]) == 3


def test_gallery_import_uses_exact_official_request_and_containers_access_tier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = FakeTemplatesResource()
    accesses: list[str] = []
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
        lambda value: (accesses.append(value), object())[1],
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
    assert accesses == ["containers"]


def test_gallery_import_dry_run_is_deterministic_redacted_and_local(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    monkeypatch.setattr(
        transport,
        "credentials_for_access",
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


def test_gallery_import_apply_rejects_unsupported_body_fields_before_dispatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    _install_apply_dispatch_barriers(monkeypatch)

    result = CliRunner().invoke(
        app,
        _args(
            _body_file(tmp_path, '{"galleryOwner":"owner","unexpected":"value"}'),
            "--acknowledge-template-import-permissions",
            "--apply",
        ),
    )

    assert result.exit_code == 2
    assert result.stdout == ""
    assert json.loads(result.stderr) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "gtmctl accounts containers workspaces templates import-from-gallery",
        "exitCode": 2,
        "category": "invalid_request",
        "message": "--body contains unsupported Gallery import field(s): unexpected.",
    }
