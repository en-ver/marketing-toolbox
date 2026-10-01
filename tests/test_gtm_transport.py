"""Single-dispatch transport contracts for GTM mutations."""

from __future__ import annotations

import json
import socket
from typing import Any, cast

import pytest
import typer
from google.auth.credentials import Credentials
from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.errors import HttpError
from requests import Response
from requests.adapters import BaseAdapter
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout
from requests.structures import CaseInsensitiveDict

from gtmctl.commands._common import run_command
from gtmctl.foundation.errors import GoogleApiError
from gtmctl.operations import mutation_transport, mutations

_PARENT = "accounts/1/containers/2/workspaces/3"


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
        mutations,
        "service_account_credentials",
        lambda _scopes: pytest.fail("ambient credential resolution is forbidden"),
    )


def _service_with_adapter(credentials: Credentials, adapter: RecordingAdapter) -> Any:
    service = mutation_transport.make_tag_manager_mutation_service(credentials)
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
    assert kwargs["timeout"] == mutation_transport.GTM_MUTATION_TIMEOUT_SECONDS
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

    monkeypatch.setattr(mutations, "service_account_credentials", lambda _: credentials)
    monkeypatch.setattr(mutations, "make_tag_manager_mutation_service", factory)

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

    monkeypatch.setattr(mutations, "service_account_credentials", lambda _: credentials)
    monkeypatch.setattr(mutations, "make_tag_manager_mutation_service", factory)

    with pytest.raises(GoogleApiError) as raised:
        mutations.create_tag(_PARENT, {"name": "tag"})

    assert (raised.value.exit_code, raised.value.category) == (4, "authentication")
    assert "secret" not in str(raised.value)
    assert credentials.refreshes == 1
    assert adapter.requests == []
    assert adapter.closed == 1


def test_authorized_session_uses_real_default_zero_retry_adapter() -> None:
    service = mutation_transport.make_tag_manager_mutation_service(
        ControlledCredentials()
    )
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
    mismatch_service = mutation_transport.make_tag_manager_mutation_service(mismatched)
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
        mutation_transport.make_tag_manager_mutation_service(ControlledCredentials())


def test_valid_mutation_client_certificate_setting_never_looks_up_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOOGLE_API_USE_CLIENT_CERTIFICATE", "true")
    monkeypatch.setattr(
        "google.auth.transport._mtls_helper.get_client_cert_and_key",
        lambda *_args, **_kwargs: pytest.fail("certificate lookup is forbidden"),
    )

    service = mutation_transport.make_tag_manager_mutation_service(
        ControlledCredentials()
    )
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

    monkeypatch.setattr(mutations, "service_account_credentials", lambda _: credentials)
    monkeypatch.setattr(
        mutations,
        "make_tag_manager_mutation_service",
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

    monkeypatch.setattr(mutations, "service_account_credentials", lambda _: credentials)
    monkeypatch.setattr(
        mutations,
        "make_tag_manager_mutation_service",
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

    injected = InjectedService()
    credentials = ControlledCredentials()
    monkeypatch.setattr(mutations, "service_account_credentials", lambda _: credentials)

    assert (
        mutations.execute_mutation(
            "accounts containers workspaces tags create",
            lambda _service: type(
                "Request", (), {"execute": lambda *_args, **_kwargs: {}}
            )(),
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

    monkeypatch.setattr(
        mutation_transport, "_DiscoveryAuthorizedSessionHttp", FailingHttp
    )
    monkeypatch.setattr(
        mutation_transport,
        "build",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("build failed")),
    )

    with pytest.raises(RuntimeError, match="build failed"):
        mutation_transport.make_tag_manager_mutation_service(ControlledCredentials())
    assert closed == [True]
