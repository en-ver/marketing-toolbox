"""Single-dispatch transport contracts for GTM mutations."""

from __future__ import annotations

import json
import socket
from collections.abc import Callable
from typing import Any, cast
from urllib.parse import urlsplit

import pytest
import typer
from google.auth.credentials import Credentials
from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.errors import HttpError
from httplib2 import Response as DiscoveryResponse
from requests import Response
from requests.adapters import BaseAdapter
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout
from requests.structures import CaseInsensitiveDict
from typer.testing import CliRunner

from gtmctl.cli import app
from gtmctl.commands._common import run_command
from gtmctl.foundation.errors import GoogleApiError
from gtmctl.operations import mutations, reads, transport
from marketing_common.oauth import SCOPE_CATALOG

_PARENT = "accounts/1/containers/2/workspaces/3"
_REAL_MAKE_MUTATION_SERVICE = transport.make_mutation_service


class ControlledCredentials(Credentials):
    def __init__(
        self, token: str | None = "test-token", failure: Exception | None = None
    ) -> None:
        super().__init__()
        self.token = token
        self.failure = failure
        self.refreshes = 0

    def refresh(self, request: Any) -> None:
        del request
        self.refreshes += 1
        if self.failure is not None:
            raise self.failure
        self.token = "refreshed-token"


class TrackingResponse(Response):
    def __init__(self, status: int, content: bytes, reason: str = "OK") -> None:
        super().__init__()
        self.status_code = status
        self.reason = reason
        self.headers = CaseInsensitiveDict({"content-type": "application/json"})
        self._content = content
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        super().close()


class RecordingAdapter(BaseAdapter):
    def __init__(self, responses: list[TrackingResponse | Exception]) -> None:
        self.responses = responses
        self.requests: list[
            tuple[str, str, bytes | None, dict[str, str], dict[str, Any]]
        ] = []
        self.closed = 0

    def send(self, request: Any, **kwargs: Any) -> Response:
        self.requests.append(
            (
                request.method,
                request.url,
                request.body,
                dict(request.headers),
                kwargs,
            )
        )
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        response.request = request
        response.url = request.url
        return response

    def close(self) -> None:
        self.closed += 1


@pytest.fixture(autouse=True)
def _block_external_transport_and_ambient_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BlockedSocket(socket.socket):
        def connect(self, address: Any) -> None:
            del address
            pytest.fail("external sockets are forbidden")

        def connect_ex(self, address: Any) -> int:
            del address
            pytest.fail("external sockets are forbidden")

    monkeypatch.delenv("GOOGLE_API_USE_MTLS_ENDPOINT", raising=False)
    monkeypatch.delenv("GOOGLE_API_USE_CLIENT_CERTIFICATE", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_UNIVERSE_DOMAIN", raising=False)
    monkeypatch.setattr(
        socket,
        "create_connection",
        lambda *_args, **_kwargs: pytest.fail("external sockets are forbidden"),
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: pytest.fail("external DNS is forbidden"),
    )
    monkeypatch.setattr(socket, "socket", BlockedSocket)
    monkeypatch.setattr(
        transport,
        "resolve_credentials",
        lambda _scopes, *, tool: pytest.fail(
            "ambient credential resolution is forbidden"
        ),
    )


@pytest.mark.parametrize("access", SCOPE_CATALOG["gtmctl"])
def test_credentials_for_access_uses_the_exact_gtm_catalog_entry(
    monkeypatch: pytest.MonkeyPatch, access: str
) -> None:
    scope_calls: list[tuple[str, str]] = []
    resolution_calls: list[tuple[list[str], str]] = []
    credentials = ControlledCredentials()

    def catalog_scope(tool: str, requested_access: str) -> str:
        scope_calls.append((tool, requested_access))
        return SCOPE_CATALOG[tool][requested_access]

    def resolve(scopes: list[str], *, tool: str) -> Credentials:
        resolution_calls.append((scopes, tool))
        return credentials

    monkeypatch.setattr(transport, "scope_for_access", catalog_scope)
    monkeypatch.setattr(transport, "resolve_credentials", resolve)

    assert transport.credentials_for_access(access) is credentials
    assert scope_calls == [("gtmctl", access)]
    assert resolution_calls == [([SCOPE_CATALOG["gtmctl"][access]], "gtmctl")]


def test_make_read_service_uses_the_default_discovery_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = ControlledCredentials()
    service = object()
    calls: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def build(*args: Any, **kwargs: Any) -> object:
        calls.append((args, kwargs))
        return service

    monkeypatch.setattr(transport, "build", build)

    assert transport.make_read_service(credentials) is service
    assert calls == [
        (("tagmanager", "v2"), {"credentials": credentials, "cache_discovery": False})
    ]


@pytest.mark.parametrize(
    ("operation", "args", "expected_access"),
    [
        (reads.list_accounts, (), "read"),
        (reads.get_user_permission, ("accounts/1/user_permissions/2",), "users"),
        (reads.list_user_permissions, ("accounts/1",), "users"),
        (mutations.update_account, ("accounts/1", {}, None), "accounts"),
        (mutations.create_user_permission, ("accounts/1", {}), "users"),
        (
            mutations.update_user_permission,
            ("accounts/1/user_permissions/2", {}),
            "users",
        ),
        (mutations.delete_user_permission, ("accounts/1/user_permissions/2",), "users"),
        (mutations.create_container, ("accounts/1", {}), "containers"),
        (
            mutations.delete_environment,
            ("accounts/1/containers/2/environments/3",),
            "containers",
        ),
        (
            mutations.delete_tag,
            ("accounts/1/containers/2/workspaces/3/tags/4",),
            "containers",
        ),
        (
            mutations.set_latest_version,
            ("accounts/1/containers/2/versions/4",),
            "containers",
        ),
        (mutations.delete_container, ("accounts/1/containers/2",), "delete"),
        (
            mutations.delete_workspace,
            ("accounts/1/containers/2/workspaces/3",),
            "delete",
        ),
        (
            mutations.update_version,
            ("accounts/1/containers/2/versions/4", {}, None),
            "versions",
        ),
        (mutations.delete_version, ("accounts/1/containers/2/versions/4",), "versions"),
        (
            mutations.undelete_version,
            ("accounts/1/containers/2/versions/4",),
            "versions",
        ),
        (
            mutations.quick_preview_workspace,
            ("accounts/1/containers/2/workspaces/3",),
            "versions",
        ),
        (
            mutations.create_workspace_version,
            ("accounts/1/containers/2/workspaces/3", {}),
            "versions",
        ),
        (
            mutations.publish_version,
            ("accounts/1/containers/2/versions/4", None),
            "publish",
        ),
        (
            mutations.reauthorize_environment,
            ("accounts/1/containers/2/environments/3", {}),
            "publish",
        ),
    ],
)
def test_operation_access_tier_matrix(
    monkeypatch: pytest.MonkeyPatch,
    operation: Any,
    args: tuple[Any, ...],
    expected_access: str,
) -> None:
    accesses: list[str] = []

    def capture_read(
        _command: str,
        _request_factory: Any,
        *,
        access: str = "read",
        service_factory: Any = None,
    ) -> dict[str, Any]:
        del service_factory
        accesses.append(access)
        return {}

    def capture_mutation(
        _command: str,
        _request_factory: Any,
        *,
        access: str = "containers",
        service_factory: Any = None,
    ) -> dict[str, Any]:
        del service_factory
        accesses.append(access)
        return {}

    monkeypatch.setattr(reads, "execute_read", capture_read)
    monkeypatch.setattr(mutations, "execute_mutation", capture_mutation)

    assert operation(*args) == {}
    assert accesses == [expected_access]


def _service_with_adapter(credentials: Credentials, adapter: RecordingAdapter) -> Any:
    service = _REAL_MAKE_MUTATION_SERVICE(credentials)
    cast(Any, service)._http._session.mount("https://", adapter)
    return service


def _create_tag(service: Any) -> Any:
    return (
        service.accounts()
        .containers()
        .workspaces()
        .tags()
        .create(
            parent=_PARENT,
            body={"name": "tag"},
        )
    )


def test_real_discovery_transport_preserves_request_and_response_contract() -> None:
    credentials = ControlledCredentials()
    response = TrackingResponse(200, b'{"tagId":"4"}', reason="Created")
    adapter = RecordingAdapter([response])
    service = _service_with_adapter(credentials, adapter)

    try:
        assert _create_tag(service).execute(num_retries=0) == {"tagId": "4"}
    finally:
        service.close()

    assert len(adapter.requests) == 1
    method, url, body, headers, kwargs = adapter.requests[0]
    assert method == "POST"
    assert url.endswith("/accounts/1/containers/2/workspaces/3/tags?alt=json")
    assert body == '{"name": "tag"}'
    assert headers["authorization"] == "Bearer test-token"
    assert kwargs["timeout"] == transport.GTM_MUTATION_TIMEOUT_SECONDS
    assert response.close_calls >= 1
    assert adapter.closed == 1


def test_acknowledged_workspace_delete_preserves_real_prepared_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = ControlledCredentials()
    response = TrackingResponse(204, b"")
    adapter = RecordingAdapter([response])
    accesses: list[str] = []

    def credentials_for_access(access: str) -> Credentials:
        accesses.append(access)
        return credentials

    def factory(resolved: Credentials) -> Any:
        assert resolved is credentials
        return _service_with_adapter(resolved, adapter)

    monkeypatch.setattr(transport, "credentials_for_access", credentials_for_access)
    monkeypatch.setattr(transport, "make_mutation_service", factory)
    arguments = [
        "accounts",
        "containers",
        "workspaces",
        "delete",
        "--path",
        _PARENT,
        "--apply",
    ]

    unacknowledged = CliRunner().invoke(app, arguments)
    assert unacknowledged.exit_code == 2
    assert unacknowledged.stdout == ""
    assert json.loads(unacknowledged.stderr)["message"] == (
        "--acknowledge-workspace-delete is required before deleting a workspace."
    )
    assert accesses == []
    assert adapter.requests == []

    acknowledged = CliRunner().invoke(
        app, [*arguments, "--acknowledge-workspace-delete"]
    )
    assert acknowledged.exit_code == 0
    assert json.loads(acknowledged.stdout) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "gtmctl accounts containers workspaces delete",
        "data": {},
    }
    assert accesses == ["delete"]
    assert len(adapter.requests) == 1
    method, url, body, headers, kwargs = adapter.requests[0]
    prepared = urlsplit(url)
    assert method == "DELETE"
    assert prepared.path == "/tagmanager/v2/accounts/1/containers/2/workspaces/3"
    assert prepared.query == ""
    assert prepared.fragment == ""
    assert body is None
    assert headers["authorization"] == "Bearer test-token"
    assert kwargs["timeout"] == transport.GTM_MUTATION_TIMEOUT_SECONDS
    assert credentials.refreshes == 0
    assert response.close_calls >= 1
    assert adapter.closed == 1


def test_transport_converts_response_headers_status_reason_and_bytes() -> None:
    payload = b"exact bytes"
    adapter = RecordingAdapter([TrackingResponse(201, payload, reason="Created")])
    service = _service_with_adapter(ControlledCredentials(), adapter)

    try:
        response, content = cast(Any, service)._http.request(
            "https://tagmanager.googleapis.com/example",
            method="PATCH",
            body=b"input",
            headers={"x-test": "value"},
        )
    finally:
        service.close()

    assert (response.status, response.reason, content) == (201, "Created", payload)
    assert response["content-type"] == "application/json"
    assert adapter.requests[0][0:3] == (
        "PATCH",
        "https://tagmanager.googleapis.com/example",
        b"input",
    )
    assert adapter.requests[0][3]["x-test"] == "value"


@pytest.mark.parametrize("status", [204, 401, 307, 308, 500])
def test_real_discovery_dispatches_once_and_closes_each_http_response(
    status: int,
) -> None:
    content = b"" if status == 204 else b'{"error":"ignored"}'
    response = TrackingResponse(status, content)
    if status in {307, 308}:
        response.headers["location"] = "https://synthetic.redirect.invalid/replayed"
    adapter = RecordingAdapter([response])
    service = _service_with_adapter(ControlledCredentials(), adapter)

    try:
        request = _create_tag(service)
        if status == 204:
            assert request.execute(num_retries=0) == {}
        else:
            with pytest.raises(HttpError):
                request.execute(num_retries=0)
    finally:
        service.close()

    assert len(adapter.requests) == 1
    assert response.close_calls >= 1


@pytest.mark.parametrize(
    "failure", [RequestsConnectionError("secret"), Timeout("secret")]
)
def test_real_discovery_dispatches_requests_transport_failure_once(
    failure: Exception,
) -> None:
    adapter = RecordingAdapter([failure])
    service = _service_with_adapter(ControlledCredentials(), adapter)

    try:
        with pytest.raises(type(failure)):
            _create_tag(service).execute(num_retries=0)
    finally:
        service.close()

    assert len(adapter.requests) == 1


def test_initial_refresh_precedes_single_api_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = ControlledCredentials(token=None)
    adapter = RecordingAdapter([TrackingResponse(200, b"{}")])

    def factory(resolved: Credentials) -> Any:
        assert resolved is credentials
        return _service_with_adapter(resolved, adapter)

    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)
    monkeypatch.setattr(transport, "make_mutation_service", factory)

    assert mutations.create_tag(_PARENT, {"name": "tag"}) == {}
    assert credentials.refreshes == 1
    assert len(adapter.requests) == 1
    assert adapter.closed == 1


@pytest.mark.parametrize("failure", [RefreshError("secret"), TransportError("secret")])
def test_initial_authentication_failure_never_dispatches_api(
    monkeypatch: pytest.MonkeyPatch, failure: Exception
) -> None:
    credentials = ControlledCredentials(token=None, failure=failure)
    adapter = RecordingAdapter([TrackingResponse(200, b"{}")])

    def factory(resolved: Credentials) -> Any:
        return _service_with_adapter(resolved, adapter)

    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)
    monkeypatch.setattr(transport, "make_mutation_service", factory)

    with pytest.raises(GoogleApiError) as raised:
        mutations.create_tag(_PARENT, {"name": "tag"})

    assert (raised.value.exit_code, raised.value.category) == (4, "authentication")
    assert "secret" not in str(raised.value)
    assert credentials.refreshes == 1
    assert adapter.requests == []
    assert adapter.closed == 1


def test_authorized_session_uses_real_default_zero_retry_adapter() -> None:
    service = transport.make_mutation_service(ControlledCredentials())
    try:
        retries = cast(Any, service)._http._session.get_adapter("https://").max_retries
        assert (retries.total, retries.read) == (0, False)
    finally:
        service.close()


def test_discovery_preserves_matching_and_mismatched_credential_universes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_CLOUD_UNIVERSE_DOMAIN", "example.com")
    matching = ControlledCredentials()
    matching._universe_domain = "example.com"
    adapter = RecordingAdapter([TrackingResponse(200, b"{}")])
    service = _service_with_adapter(matching, adapter)

    try:
        assert _create_tag(service).execute(num_retries=0) == {}
    finally:
        service.close()

    assert adapter.requests[0][1].startswith("https://tagmanager.example.com/")

    mismatched = ControlledCredentials()
    mismatched._universe_domain = "another.example.com"
    mismatch_service = transport.make_mutation_service(mismatched)
    try:
        with pytest.raises(ValueError, match="does not match"):
            _create_tag(mismatch_service)
    finally:
        mismatch_service.close()


def test_session_auth_blocks_netrc_replacement_without_disabling_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "requests.sessions.get_netrc_auth", lambda _url: ("user", "password")
    )
    adapter = RecordingAdapter([TrackingResponse(200, b"{}")])
    service = _service_with_adapter(ControlledCredentials(), adapter)

    try:
        assert _create_tag(service).execute(num_retries=0) == {}
    finally:
        service.close()

    headers = adapter.requests[0][3]
    assert headers["authorization"] == "Bearer test-token"
    assert cast(Any, service)._http._session.trust_env is True


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("GOOGLE_API_USE_MTLS_ENDPOINT", "invalid"),
        ("GOOGLE_API_USE_MTLS_ENDPOINT", "always"),
        ("GOOGLE_API_USE_CLIENT_CERTIFICATE", "invalid"),
    ],
)
def test_mutation_mtls_configuration_is_rejected_without_certificate_lookup(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)
    monkeypatch.setattr(
        "google.auth.transport._mtls_helper.get_client_cert_and_key",
        lambda *_args, **_kwargs: pytest.fail("certificate lookup is forbidden"),
    )

    with pytest.raises(ValueError):
        transport.make_mutation_service(ControlledCredentials())


def test_valid_mutation_client_certificate_setting_never_looks_up_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_USE_CLIENT_CERTIFICATE", "true")
    monkeypatch.setattr(
        "google.auth.transport._mtls_helper.get_client_cert_and_key",
        lambda *_args, **_kwargs: pytest.fail("certificate lookup is forbidden"),
    )

    service = transport.make_mutation_service(ControlledCredentials())
    service.close()


@pytest.mark.parametrize(
    ("status", "failure", "exit_code", "category"),
    [
        (500, None, 1, "unexpected"),
        (307, None, 1, "unexpected"),
        (None, RequestsConnectionError("transport-secret"), 1, "unexpected"),
    ],
)
def test_mutation_cli_boundary_sanitizes_representative_transport_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    status: int | None,
    failure: Exception | None,
    exit_code: int,
    category: str,
) -> None:
    command = "gtmctl accounts containers workspaces tags create"
    response = (
        TrackingResponse(status, b'{"error":"transport-secret"}')
        if status is not None
        else None
    )
    if status == 307:
        assert response is not None
        response.headers["location"] = "https://synthetic.redirect.invalid/replayed"
    transport_result = failure if failure is not None else response
    assert transport_result is not None
    adapter = RecordingAdapter([transport_result])
    credentials = ControlledCredentials()

    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)
    monkeypatch.setattr(
        transport,
        "make_mutation_service",
        lambda resolved: _service_with_adapter(resolved, adapter),
    )

    with pytest.raises(typer.Exit) as raised:
        run_command(
            command=command,
            operation=lambda: mutations.create_tag(_PARENT, {"name": "tag"}),
        )

    diagnostic = json.loads(capsys.readouterr().err)
    assert raised.value.exit_code == exit_code
    assert diagnostic["command"] == command
    assert diagnostic["exitCode"] == exit_code
    assert diagnostic["category"] == category
    assert "transport-secret" not in json.dumps(diagnostic)
    assert len(adapter.requests) == 1
    assert adapter.closed == 1
    if response is not None:
        assert response.close_calls >= 1


def test_default_owned_resource_closes_after_api_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credentials = ControlledCredentials()
    response = TrackingResponse(500, b'{"error":"ignored"}')
    adapter = RecordingAdapter([response])

    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)
    monkeypatch.setattr(
        transport,
        "make_mutation_service",
        lambda resolved: _service_with_adapter(resolved, adapter),
    )

    with pytest.raises(GoogleApiError):
        mutations.create_tag(_PARENT, {"name": "tag"})

    assert len(adapter.requests) == 1
    assert response.close_calls >= 1
    assert adapter.closed == 1


def test_injected_resource_is_caller_owned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class InjectedService:
        closed = 0

        def close(self) -> None:
            self.closed += 1

    class InjectedRequest:
        def __init__(self) -> None:
            self.callbacks: list[Callable[[DiscoveryResponse], None]] = []

        def add_response_callback(
            self, callback: Callable[[DiscoveryResponse], None]
        ) -> None:
            self.callbacks.append(callback)

        def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
            assert num_retries == 0
            for callback in self.callbacks:
                callback(DiscoveryResponse({"status": "200"}))
            return {}

    injected = InjectedService()
    credentials = ControlledCredentials()
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)

    assert (
        mutations.execute_mutation(
            "accounts containers workspaces tags create",
            lambda _service: InjectedRequest(),
            service_factory=lambda _: cast(Any, injected),
        )
        == {}
    )
    assert injected.closed == 0


def test_factory_closes_adapter_when_discovery_build_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[bool] = []

    class FailingHttp:
        def __init__(self, credentials: Credentials) -> None:
            self.credentials = credentials

        def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(transport, "_DiscoveryAuthorizedSessionHttp", FailingHttp)
    monkeypatch.setattr(
        transport,
        "build",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("build failed")),
    )

    with pytest.raises(RuntimeError, match="build failed"):
        transport.make_mutation_service(ControlledCredentials())
    assert closed == [True]


def _install_mutation_adapter(
    monkeypatch: pytest.MonkeyPatch, adapter: RecordingAdapter
) -> None:
    credentials = ControlledCredentials()
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)
    monkeypatch.setattr(
        transport,
        "make_mutation_service",
        lambda resolved: _service_with_adapter(resolved, adapter),
    )


@pytest.mark.parametrize(
    "content", [b'{"secret":"response-secret"', b"notjson", b"[]", b"\xff"]
)
def test_unreadable_success_reports_exact_uncertainty_at_leaf_command(
    monkeypatch: pytest.MonkeyPatch, content: bytes
) -> None:
    response = TrackingResponse(200, content)
    adapter = RecordingAdapter([response])
    _install_mutation_adapter(monkeypatch, adapter)

    result = CliRunner().invoke(
        app,
        [
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "create",
            "--parent",
            _PARENT,
            "--body",
            "-",
            "--apply",
        ],
        input='{"name":"submitted-secret"}',
    )

    assert result.exit_code == 1
    assert result.stdout == ""
    assert json.loads(result.stderr) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "gtmctl accounts containers workspaces tags create",
        "exitCode": 1,
        "category": "unexpected",
        "message": (
            "Google Tag Manager mutation may have completed, but its API response "
            "could not be read. Inspect the current GTM state before retrying."
        ),
    }
    assert "secret" not in result.stderr
    assert len(adapter.requests) == 1
    assert adapter.requests[0][0] == "POST"
    assert adapter.requests[0][4]["timeout"] == transport.GTM_MUTATION_TIMEOUT_SECONDS
    assert response.close_calls >= 1
    assert adapter.closed == 1


@pytest.mark.parametrize(
    ("status", "content", "expected"),
    [
        (
            200,
            b'{"tagId":"4","unknown":["preserved"]}',
            {"tagId": "4", "unknown": ["preserved"]},
        ),
        (200, b"{}", {}),
        (200, b"", {}),
        (204, b"", {}),
    ],
)
@pytest.mark.parametrize("raw_model", [False, True])
def test_real_discovery_preserves_object_empty_and_raw_model_success(
    monkeypatch: pytest.MonkeyPatch,
    status: int,
    content: bytes,
    expected: dict[str, Any],
    raw_model: bool,
) -> None:
    response = TrackingResponse(status, content)
    adapter = RecordingAdapter([response])
    _install_mutation_adapter(monkeypatch, adapter)

    if raw_model:
        result = mutations.delete_tag(f"{_PARENT}/tags/4")
    else:
        result = mutations.create_tag(_PARENT, {"name": "tag"})

    assert result == expected
    assert len(adapter.requests) == 1
    assert adapter.requests[0][0] == ("DELETE" if raw_model else "POST")
    assert response.close_calls >= 1
    assert adapter.closed == 1


@pytest.mark.parametrize(
    ("status", "content", "exit_code", "category"),
    [
        (400, b"notjson", 2, "invalid_request"),
        (403, b"\xff", 4, "authentication"),
        (500, b"\xff", 1, "unexpected"),
    ],
)
def test_unreadable_non_success_preserves_http_policy_and_status(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    status: int,
    content: bytes,
    exit_code: int,
    category: str,
) -> None:
    response = TrackingResponse(status, content)
    adapter = RecordingAdapter([response])
    _install_mutation_adapter(monkeypatch, adapter)
    command = "gtmctl accounts containers workspaces tags create"

    with pytest.raises(typer.Exit) as raised:
        run_command(
            command=command,
            operation=lambda: mutations.create_tag(_PARENT, {"name": "tag"}),
        )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert raised.value.exit_code == exit_code
    assert json.loads(captured.err) == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": command,
        "exitCode": exit_code,
        "category": category,
        "message": (
            "Google Tag Manager mutation may have completed after an HTTP failure. "
            "Inspect the current GTM state before retrying."
            if status == 500
            else f"Google Tag Manager API request failed with HTTP {status}."
        ),
        "googleStatus": status,
    }
    assert len(adapter.requests) == 1
    assert response.close_calls >= 1
    assert adapter.closed == 1


@pytest.mark.parametrize("injected", [False, True])
def test_service_factory_decoding_failure_is_not_post_dispatch_uncertainty(
    monkeypatch: pytest.MonkeyPatch, injected: bool
) -> None:
    adapter = RecordingAdapter([])
    failure = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "factory-secret")
    calls: list[Credentials] = []

    def factory(credentials: Credentials) -> Any:
        calls.append(credentials)
        raise failure

    monkeypatch.setattr(
        transport, "credentials_for_access", lambda _: ControlledCredentials()
    )
    monkeypatch.setattr(transport, "make_mutation_service", factory)

    with pytest.raises(UnicodeDecodeError) as raised:
        mutations.create_tag(
            _PARENT, {"name": "tag"}, service_factory=factory if injected else None
        )

    assert raised.value is failure
    assert len(calls) == 1
    assert adapter.requests == []


def test_real_discovery_serialization_failure_never_dispatches_and_closes_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = RecordingAdapter([])
    _install_mutation_adapter(monkeypatch, adapter)

    with pytest.raises(TypeError, match="not JSON serializable"):
        mutations.create_tag(_PARENT, {"name": object()})

    assert adapter.requests == []
    assert adapter.closed == 1


def test_request_factory_decoding_failure_never_dispatches_and_closes_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = RecordingAdapter([])
    _install_mutation_adapter(monkeypatch, adapter)
    failure = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "serialization-secret")

    def request_factory(_service: Any) -> Any:
        raise failure

    with pytest.raises(UnicodeDecodeError) as raised:
        mutations.execute_mutation(
            "accounts containers workspaces tags create", request_factory
        )

    assert raised.value is failure
    assert adapter.requests == []
    assert adapter.closed == 1


def test_response_close_failure_preserves_existing_execution_failure_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = RuntimeError("response-close-secret")

    class FailingCloseResponse(TrackingResponse):
        def close(self) -> None:
            super().close()
            raise failure

    response = FailingCloseResponse(200, b"\xff")
    adapter = RecordingAdapter([response])
    _install_mutation_adapter(monkeypatch, adapter)

    with pytest.raises(RuntimeError) as raised:
        mutations.create_tag(_PARENT, {"name": "tag"})

    assert raised.value is failure
    assert len(adapter.requests) == 1
    assert response.close_calls >= 1
    assert adapter.closed == 1


@pytest.mark.parametrize("content", [b"{}", b"\xff"])
def test_service_close_failure_is_not_reclassified_as_response_uncertainty(
    monkeypatch: pytest.MonkeyPatch, content: bytes
) -> None:
    failure = RuntimeError("service-close-secret")
    response = TrackingResponse(200, content)
    adapter = RecordingAdapter([response])
    credentials = ControlledCredentials()
    service = _service_with_adapter(credentials, adapter)
    original_close = service.close

    def close() -> None:
        original_close()
        raise failure

    monkeypatch.setattr(service, "close", close)
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)
    monkeypatch.setattr(transport, "make_mutation_service", lambda _: service)

    with pytest.raises(RuntimeError) as raised:
        mutations.create_tag(_PARENT, {"name": "tag"})

    assert raised.value is failure
    assert len(adapter.requests) == 1
    assert response.close_calls >= 1
    assert adapter.closed == 1


@pytest.mark.parametrize("content", [b'{"tagId":"4"}', b"\xff"])
def test_injected_real_service_remains_caller_owned_on_success_and_decode_failure(
    monkeypatch: pytest.MonkeyPatch, content: bytes
) -> None:
    response = TrackingResponse(200, content)
    adapter = RecordingAdapter([response])
    credentials = ControlledCredentials()
    service = _service_with_adapter(credentials, adapter)
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: credentials)

    try:
        if content == b"\xff":
            with pytest.raises(GoogleApiError) as raised:
                mutations.create_tag(
                    _PARENT, {"name": "tag"}, service_factory=lambda _: service
                )
            assert raised.value.status is None
            assert "response could not be read" in str(raised.value)
        else:
            assert mutations.create_tag(
                _PARENT, {"name": "tag"}, service_factory=lambda _: service
            ) == {"tagId": "4"}
        assert len(adapter.requests) == 1
        assert response.close_calls >= 1
        assert adapter.closed == 0
    finally:
        service.close()
    assert adapter.closed == 1
