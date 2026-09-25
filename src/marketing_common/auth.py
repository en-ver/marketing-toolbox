"""Credential resolution for service accounts, native OAuth, and ADC."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from typing import cast

import google.auth
from google.auth.credentials import Credentials
from google.oauth2 import service_account

from .oauth import (
    OAuthAuthenticationError,
    ToolName,
    access_for_scope,
    load_native_credentials,
    native_marker_exists,
)

SERVICE_ACCOUNT_JSON_ENV = "GOOGLE_SERVICE_ACCOUNT_JSON"
APPLICATION_CREDENTIALS_ENV = "GOOGLE_APPLICATION_CREDENTIALS"


class CredentialConfigurationError(ValueError):
    """Raised when an explicitly selected credential source is invalid."""


def service_account_credentials(
    scopes: Sequence[str], *, env: Mapping[str, str] | None = None
) -> service_account.Credentials:
    """Build only service-account credentials from the two explicit sources.

    This compatibility function deliberately does not select native OAuth or
    ambient ADC; callers needing generic Google credentials use
    :func:`resolve_credentials`.
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
                cast(str, credential_file), scopes=scopes
            ),
        )
    except (OSError, TypeError, ValueError) as exc:
        raise CredentialConfigurationError(
            f"{APPLICATION_CREDENTIALS_ENV} must name a valid readable service-account document."
        ) from exc


def resolve_credentials(
    scopes: Sequence[str], *, tool: ToolName, env: Mapping[str, str] | None = None
) -> Credentials:
    """Resolve explicit credentials, matching native OAuth, then ambient ADC.

    Every configured or marked source is fail-closed: a failure never falls
    through to another identity.
    """
    values = os.environ if env is None else env
    requested = list(scopes)
    serialized = values.get(SERVICE_ACCOUNT_JSON_ENV)
    if serialized:
        try:
            info = json.loads(serialized)
            if not isinstance(info, dict):
                raise TypeError
            return cast(
                Credentials,
                service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
                    info, scopes=requested
                ),
            )
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise CredentialConfigurationError(
                f"{SERVICE_ACCOUNT_JSON_ENV} must contain a JSON service-account document."
            ) from exc
    credential_file = values.get(APPLICATION_CREDENTIALS_ENV)
    if credential_file:
        try:
            loaded = google.auth.load_credentials_from_file(  # type: ignore[no-untyped-call]
                credential_file, scopes=requested
            )
            credentials, _ = cast(tuple[Credentials, str | None], loaded)
            return credentials
        except Exception as exc:  # generic loader supports several credential types
            raise CredentialConfigurationError(
                f"{APPLICATION_CREDENTIALS_ENV} must name a valid readable credential document."
            ) from exc
    access = access_for_scope(tool, requested)
    try:
        native_present = access is not None and native_marker_exists(tool, access)
    except OAuthAuthenticationError as exc:
        raise CredentialConfigurationError(str(exc)) from exc
    if native_present:
        assert access is not None
        try:
            return load_native_credentials(tool, access, requested[0])
        except OAuthAuthenticationError as exc:
            raise CredentialConfigurationError(str(exc)) from exc
    try:
        credentials, _ = google.auth.default(scopes=requested)
        return credentials
    except Exception as exc:
        raise CredentialConfigurationError(
            "No usable ambient Google credentials are available."
        ) from exc
