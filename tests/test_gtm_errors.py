"""Regression tests for Google Tag Manager API diagnostics."""

from __future__ import annotations

import json
import ssl
from collections.abc import Callable
from typing import Any

import pytest
import typer
from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.errors import HttpError
from httplib2 import Response
from httplib2.error import ServerNotFoundError

from gtmctl.commands._common import run_command
from gtmctl.foundation.errors import GoogleApiError, normalize_google_error
from gtmctl.operations import mutations, reads, transport

_SENTINEL = "UPSTREAM-SECRET-MARKER"


def _http_error(status: int) -> HttpError:
    return HttpError(
        Response({"status": str(status)}),
        (
            f'{{"error":{{"code":{status},"message":"{_SENTINEL}",'
            '"errors":[{"reason":"invalid"}]}}}'
        ).encode(),
    )


@pytest.mark.parametrize(
    ("status", "exit_code", "category"),
    [
        (400, 2, "invalid_request"),
        (401, 4, "authentication"),
        (403, 4, "authentication"),
        (404, 3, "not_found"),
        (409, 5, "conflict"),
        (412, 5, "conflict"),
        (429, 6, "retryable"),
        (500, 6, "retryable"),
    ],
)
def test_normalize_google_error_uses_status_without_upstream_diagnostics(
    status: int, exit_code: int, category: str
) -> None:
    error = normalize_google_error(_http_error(status))

    assert (error.exit_code, error.category, error.status) == (
        exit_code,
        category,
        status,
    )
    assert _SENTINEL not in str(error)


@pytest.mark.parametrize(
    ("status", "exit_code", "category"),
    [
        (400, 2, "invalid_request"),
        (401, 4, "authentication"),
        (403, 4, "authentication"),
        (404, 3, "not_found"),
        (409, 5, "conflict"),
        (412, 5, "conflict"),
        (429, 6, "retryable"),
        (500, 1, "unexpected"),
        (503, 1, "unexpected"),
        (307, 1, "unexpected"),
    ],
)
def test_mutation_execution_boundary_applies_http_error_policy(
    monkeypatch: pytest.MonkeyPatch, status: int, exit_code: int, category: str
) -> None:
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())

    class FailingRequest:
        def __init__(self) -> None:
            self.callbacks: list[Callable[[Response], None]] = []

        def add_response_callback(self, callback: Callable[[Response], None]) -> None:
            self.callbacks.append(callback)

        def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
            assert num_retries == 0
            error = _http_error(status)
            for callback in self.callbacks:
                callback(error.resp)
            raise error

    request = FailingRequest()

    with pytest.raises(GoogleApiError) as raised:
        mutations.execute_mutation(
            "accounts containers workspaces tags create",
            lambda _: request,
            service_factory=lambda _: object(),  # type: ignore[return-value]
        )

    error = raised.value
    assert (error.exit_code, error.category, error.status) == (
        exit_code,
        category,
        status,
    )
    assert _SENTINEL not in str(error)
    if status >= 500:
        assert "may have completed" in str(error)


def test_mutation_mtls_factory_configuration_is_an_authentication_diagnostic(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())
    monkeypatch.setenv("GOOGLE_API_USE_MTLS_ENDPOINT", "always")

    with pytest.raises(typer.Exit) as raised:
        run_command(
            command="gtmctl accounts containers workspaces tags create",
            operation=lambda: mutations.execute_mutation(
                "accounts containers workspaces tags create",
                lambda _: pytest.fail("request must not be created"),
            ),
        )

    assert raised.value.exit_code == 4
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic["category"] == "authentication"
    assert (
        diagnostic["message"]
        == "GTM mutations do not support an always-on mTLS endpoint."
    )


def test_gtm_diagnostic_envelope_is_shared_and_redacts_google_payload(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(typer.Exit) as raised:
        run_command(
            command="gtmctl accounts containers workspaces triggers create",
            operation=lambda: (_ for _ in ()).throw(
                normalize_google_error(_http_error(400))
            ),
        )

    assert raised.value.exit_code == 2
    diagnostic = json.loads(capsys.readouterr().err)
    assert diagnostic == {
        "schemaVersion": "marketing-toolbox/v1",
        "command": "gtmctl accounts containers workspaces triggers create",
        "exitCode": 2,
        "category": "invalid_request",
        "message": "Google Tag Manager API request failed with HTTP 400.",
        "googleStatus": 400,
    }
    assert _SENTINEL not in json.dumps(diagnostic)


@pytest.mark.parametrize(
    "auth_error", [RefreshError(_SENTINEL), TransportError(_SENTINEL)]
)
def test_read_execution_boundary_normalizes_request_time_authentication_errors(
    monkeypatch: pytest.MonkeyPatch, auth_error: Exception
) -> None:
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())
    request = type(
        "FailingRequest",
        (),
        {"execute": lambda *_args, **_kwargs: (_ for _ in ()).throw(auth_error)},
    )()

    with pytest.raises(GoogleApiError) as raised:
        reads.execute_read(
            "accounts list",
            lambda _: request,
            service_factory=lambda _: object(),  # type: ignore[return-value]
        )

    assert (raised.value.exit_code, raised.value.category) == (4, "authentication")
    assert _SENTINEL not in str(raised.value)


@pytest.mark.parametrize(
    "auth_error", [RefreshError(_SENTINEL), TransportError(_SENTINEL)]
)
def test_mutation_execution_boundary_normalizes_request_time_authentication_errors(
    monkeypatch: pytest.MonkeyPatch, auth_error: Exception
) -> None:
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())

    class FailingRequest:
        def __init__(self) -> None:
            self.callbacks: list[Callable[[Response], None]] = []

        def add_response_callback(self, callback: Callable[[Response], None]) -> None:
            self.callbacks.append(callback)

        def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
            assert num_retries == 0
            raise auth_error

    request = FailingRequest()

    with pytest.raises(GoogleApiError) as raised:
        mutations.execute_mutation(
            "accounts containers workspaces tags create",
            lambda _: request,
            service_factory=lambda _: object(),  # type: ignore[return-value]
        )

    assert (raised.value.exit_code, raised.value.category) == (4, "authentication")
    assert _SENTINEL not in str(raised.value)


@pytest.mark.parametrize(
    "transport_error",
    [
        TimeoutError(_SENTINEL),
        ConnectionError(_SENTINEL),
        ssl.SSLError(_SENTINEL),
        ServerNotFoundError(_SENTINEL),
    ],
)
def test_gtm_execution_boundary_normalizes_known_transport_errors(
    monkeypatch: pytest.MonkeyPatch, transport_error: Exception
) -> None:
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())
    request = type(
        "FailingRequest",
        (),
        {"execute": lambda *_args, **_kwargs: (_ for _ in ()).throw(transport_error)},
    )()

    with pytest.raises(GoogleApiError) as raised:
        reads.execute_read(
            "accounts list",
            lambda _: request,
            service_factory=lambda _: object(),  # type: ignore[return-value]
        )

    error = raised.value
    assert (error.exit_code, error.category, error.status) == (6, "retryable", None)
    assert _SENTINEL not in str(error)


@pytest.mark.parametrize("status", [None, 199, 200, 299, 400])
def test_sdk_decode_error_requires_successful_response_evidence(
    monkeypatch: pytest.MonkeyPatch, status: int | None
) -> None:
    failure = UnicodeDecodeError("utf-8", b"\xff", 0, 1, _SENTINEL)

    class DecodeRequest:
        def __init__(self) -> None:
            self.callbacks: list[Callable[[Response], None]] = []
            self.calls: list[int] = []

        def add_response_callback(self, callback: Callable[[Response], None]) -> None:
            self.callbacks.append(callback)

        def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
            self.calls.append(num_retries)
            assert len(self.callbacks) == 1
            if status is not None:
                for callback in self.callbacks:
                    callback(Response({"status": str(status)}))
            raise failure

    request = DecodeRequest()
    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())

    with pytest.raises(
        GoogleApiError if status in {200, 299} else UnicodeDecodeError
    ) as raised:
        mutations.execute_mutation(
            "accounts containers workspaces tags create",
            lambda _: request,
            service_factory=lambda _: object(),  # type: ignore[return-value]
        )

    assert request.calls == [0]
    if status in {200, 299}:
        error = raised.value
        assert (error.exit_code, error.category, error.status) == (
            1,
            "unexpected",
            None,
        )
        assert str(error) == (
            "Google Tag Manager mutation may have completed, but its API response "
            "could not be read. Inspect the current GTM state before retrying."
        )
        assert _SENTINEL not in str(error)
    else:
        assert raised.value is failure


def test_unrelated_execution_error_after_success_is_not_response_uncertainty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failure = TypeError(_SENTINEL)

    class FailingRequest:
        def __init__(self) -> None:
            self.callbacks: list[Callable[[Response], None]] = []

        def add_response_callback(self, callback: Callable[[Response], None]) -> None:
            self.callbacks.append(callback)

        def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
            assert num_retries == 0
            for callback in self.callbacks:
                callback(Response({"status": "200"}))
            raise failure

    monkeypatch.setattr(transport, "credentials_for_access", lambda _: object())
    with pytest.raises(TypeError) as raised:
        mutations.execute_mutation(
            "accounts containers workspaces tags create",
            lambda _: FailingRequest(),
            service_factory=lambda _: object(),  # type: ignore[return-value]
        )
    assert raised.value is failure
