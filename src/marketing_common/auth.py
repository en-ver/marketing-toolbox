"""Runtime-only service-account credential loading for Google API clients."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from typing import cast

from google.oauth2 import service_account

SERVICE_ACCOUNT_JSON_ENV = "GOOGLE_SERVICE_ACCOUNT_JSON"
APPLICATION_CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"


class CredentialConfigurationError(ValueError):
    """Raised when the runtime service-account secret is unavailable or invalid."""


def service_account_credentials(
    scopes: Sequence[str], *, env: Mapping[str, str] | None = None
) -> service_account.Credentials:
    """Build scoped service-account credentials from an injected secret or file.

    ``GOOGLE_SERVICE_ACCOUNT_JSON`` takes precedence and is parsed only in
    memory.  Otherwise, ``GOOGLE_APPLICATION_CREDENTIALS`` may name a readable
    service-account JSON file.  Neither credential representation is logged or
    persisted by this loader.
    """
    values = os.environ if env is None else env
    serialized = values.get(SERVICE_ACCOUNT_JSON_ENV)
    credential_file = values.get(APPLICATION_CREDENTIALS_ENV)
    if not serialized and not credential_file:
        raise CredentialConfigurationError(
            "Missing required runtime credential: set GOOGLE_SERVICE_ACCOUNT_JSON "
            "or GOOGLE_APPLICATION_CREDENTIALS."
        )

    if serialized:
        try:
            info = json.loads(serialized)
        except json.JSONDecodeError as exc:
            raise CredentialConfigurationError(
                f"{SERVICE_ACCOUNT_JSON_ENV} must contain a JSON service-account document."
            ) from exc

        if not isinstance(info, dict):
            raise CredentialConfigurationError(
                f"{SERVICE_ACCOUNT_JSON_ENV} must contain a JSON object."
            )

        try:
            return cast(
                service_account.Credentials,
                service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
                    info, scopes=scopes
                ),
            )
        except (TypeError, ValueError) as exc:
            raise CredentialConfigurationError(
                f"{SERVICE_ACCOUNT_JSON_ENV} is not a valid service-account document."
            ) from exc

    try:
        return cast(
            service_account.Credentials,
            service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
                credential_file, scopes=scopes
            ),
        )
    except (OSError, TypeError, ValueError) as exc:
        raise CredentialConfigurationError(
            f"{APPLICATION_CREDENTIALS_ENV} must name a valid readable service-account document."
        ) from exc
