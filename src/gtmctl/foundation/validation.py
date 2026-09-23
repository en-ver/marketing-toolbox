"""Operational input validation for canonical GTM resource paths."""

from __future__ import annotations

import re


class RequestValidationError(ValueError):
    """Raised when a command input violates its documented contract."""


ACCOUNT_PATTERN = re.compile(r"^accounts/[^/]+$")
CONTAINER_PATTERN = re.compile(r"^accounts/[^/]+/containers/[^/]+$")
WORKSPACE_PATTERN = re.compile(r"^accounts/[^/]+/containers/[^/]+/workspaces/[^/]+$")
ENVIRONMENT_PATTERN = re.compile(
    r"^accounts/[^/]+/containers/[^/]+/environments/[^/]+$"
)
VERSION_PATTERN = re.compile(r"^accounts/[^/]+/containers/[^/]+/versions/[^/]+$")
USER_PERMISSION_PATTERN = re.compile(r"^accounts/[^/]+/user_permissions/[^/]+$")


def _validate(value: str, *, flag: str, pattern: re.Pattern[str]) -> None:
    if not pattern.fullmatch(value):
        raise RequestValidationError(f"{flag} must be a canonical GTM resource path.")


def validate_account_path(path: str) -> None:
    _validate(path, flag="--path", pattern=ACCOUNT_PATTERN)


def validate_account_parent(parent: str) -> None:
    _validate(parent, flag="--parent", pattern=ACCOUNT_PATTERN)


def validate_user_permission_path(path: str) -> None:
    _validate(path, flag="--path", pattern=USER_PERMISSION_PATTERN)


def validate_container_path(path: str) -> None:
    _validate(path, flag="--path", pattern=CONTAINER_PATTERN)


def validate_container_parent(parent: str) -> None:
    _validate(parent, flag="--parent", pattern=CONTAINER_PATTERN)


def validate_workspace_path(path: str) -> None:
    _validate(path, flag="--path", pattern=WORKSPACE_PATTERN)


def validate_workspace_parent(parent: str) -> None:
    _validate(parent, flag="--parent", pattern=CONTAINER_PATTERN)


def validate_environment_path(path: str) -> None:
    _validate(path, flag="--path", pattern=ENVIRONMENT_PATTERN)


def validate_environment_parent(parent: str) -> None:
    _validate(parent, flag="--parent", pattern=CONTAINER_PATTERN)


def validate_version_path(path: str) -> None:
    _validate(path, flag="--path", pattern=VERSION_PATTERN)


def validate_workspace_entity_path(path: str, entity: str) -> None:
    """Validate a canonical child resource path for one workspace collection."""
    pattern = re.compile(
        rf"^accounts/[^/]+/containers/[^/]+/workspaces/[^/]+/{re.escape(entity)}/[^/]+$"
    )
    _validate(path, flag="--path", pattern=pattern)


def validate_workspace_entity_parent(parent: str) -> None:
    _validate(parent, flag="--parent", pattern=WORKSPACE_PATTERN)


def validate_workspace_folder_path(path: str) -> None:
    validate_workspace_entity_path(path, "folders")


def validate_built_in_variables_path(path: str) -> None:
    """Validate the collection path used by built-in variable deletion."""
    pattern = re.compile(
        r"^accounts/[^/]+/containers/[^/]+/workspaces/[^/]+/built_in_variables$"
    )
    _validate(path, flag="--path", pattern=pattern)


def validate_page_token(page_token: str | None) -> None:
    if page_token is not None and page_token.strip() != page_token:
        raise RequestValidationError(
            "--page-token must not have leading or trailing whitespace."
        )
