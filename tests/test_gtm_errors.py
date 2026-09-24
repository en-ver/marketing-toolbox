"""Regression tests for Google Tag Manager API diagnostics."""

from __future__ import annotations

import json
import ssl

import pytest
import typer
from googleapiclient.errors import HttpError
from httplib2 import Response
from httplib2.error import ServerNotFoundError

from gtmctl.commands._common import run_command
from gtmctl.foundation.errors import (
    GoogleApiError,
    normalize_google_error,
)
from gtmctl.operations import reads

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
        (409, 5, "conflict"),
        (412, 5, "conflict"),
        (429, 6, "retryable"),
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
    monkeypatch.setattr(reads, "service_account_credentials", lambda _: object())
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
