import pytest
from google.oauth2 import service_account

from marketing_common.auth import (
    CredentialConfigurationError,
    service_account_credentials,
)


def test_missing_service_account_secret_is_sanitized() -> None:
    with pytest.raises(
        CredentialConfigurationError, match="GOOGLE_SERVICE_ACCOUNT_JSON"
    ):
        service_account_credentials(
            ["https://www.googleapis.com/auth/analytics.readonly"], env={}
        )


def test_application_credentials_file_is_used_when_inline_secret_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = object()
    captured: dict[str, object] = {}

    def from_file(path: str, *, scopes: list[str]) -> object:
        captured.update(path=path, scopes=scopes)
        return expected

    monkeypatch.setattr(
        service_account.Credentials, "from_service_account_file", from_file
    )

    result = service_account_credentials(
        ["https://www.googleapis.com/auth/analytics.readonly"],
        env={"GOOGLE_APPLICATION_CREDENTIALS": "/runtime/credential.json"},
    )

    assert result is expected
    assert captured == {
        "path": "/runtime/credential.json",
        "scopes": ["https://www.googleapis.com/auth/analytics.readonly"],
    }


def test_malformed_service_account_secret_is_sanitized() -> None:
    with pytest.raises(
        CredentialConfigurationError,
        match="must contain a JSON service-account document",
    ):
        service_account_credentials(
            ["https://www.googleapis.com/auth/analytics.readonly"],
            env={"GOOGLE_SERVICE_ACCOUNT_JSON": "not-json"},
        )


def test_inline_service_account_secret_takes_precedence_over_application_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = object()
    captured: dict[str, object] = {}

    def from_info(info: dict[str, object], *, scopes: list[str]) -> object:
        captured.update(info=info, scopes=scopes)
        return expected

    monkeypatch.setattr(
        service_account.Credentials, "from_service_account_info", from_info
    )
    monkeypatch.setattr(
        service_account.Credentials,
        "from_service_account_file",
        lambda *_args, **_kwargs: pytest.fail("file credentials must not be used"),
    )

    result = service_account_credentials(
        ["https://www.googleapis.com/auth/analytics.readonly"],
        env={
            "GOOGLE_SERVICE_ACCOUNT_JSON": '{"type": "service_account"}',
            "GOOGLE_APPLICATION_CREDENTIALS": "/runtime/credential.json",
        },
    )

    assert result is expected
    assert captured == {
        "info": {"type": "service_account"},
        "scopes": ["https://www.googleapis.com/auth/analytics.readonly"],
    }
