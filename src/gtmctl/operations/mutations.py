"""Official Google Tag Manager API v2 workspace mutation adapters."""

from __future__ import annotations

import json
import ssl
from collections.abc import Callable
from typing import Any, Protocol

from google.auth.credentials import Credentials
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from httplib2.error import ServerNotFoundError  # type: ignore[import-untyped]

from gtmctl.foundation.errors import normalize_google_error, normalize_transport_error
from marketing_common.auth import CredentialConfigurationError, resolve_credentials


def service_account_credentials(scopes: list[str]) -> Credentials:
    """Compatibility injection seam backed by generic credential resolution."""
    return resolve_credentials(scopes, tool="gtmctl")


TAG_MANAGER_EDIT_SCOPE = "https://www.googleapis.com/auth/tagmanager.edit.containers"
TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE = (
    "https://www.googleapis.com/auth/tagmanager.edit.containerversions"
)
TAG_MANAGER_PUBLISH_SCOPE = "https://www.googleapis.com/auth/tagmanager.publish"
TAG_MANAGER_MANAGE_ACCOUNTS_SCOPE = (
    "https://www.googleapis.com/auth/tagmanager.manage.accounts"
)
TAG_MANAGER_MANAGE_USERS_SCOPE = (
    "https://www.googleapis.com/auth/tagmanager.manage.users"
)
TAG_MANAGER_DELETE_CONTAINERS_SCOPE = (
    "https://www.googleapis.com/auth/tagmanager.delete.containers"
)


class Request(Protocol):
    def execute(
        self, *, num_retries: int = 0
    ) -> dict[str, Any] | list[Any] | str | bytes | None: ...


ServiceFactory = Callable[[Credentials], Resource]


def make_tag_manager_service(credentials: Credentials) -> Resource:
    """Create the official Discovery-backed GTM API v2 client."""
    return build("tagmanager", "v2", credentials=credentials, cache_discovery=False)


def execute_mutation(
    command: str,
    request_factory: Callable[[Resource], Request],
    *,
    scope: str = TAG_MANAGER_EDIT_SCOPE,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Execute exactly one GTM write request without automatic retry."""
    try:
        credentials = service_account_credentials([scope])
        service = (
            make_tag_manager_service if service_factory is None else service_factory
        )(credentials)
        response = request_factory(service).execute(num_retries=0)
    except CredentialConfigurationError:
        raise
    except HttpError as exc:
        raise normalize_google_error(exc) from exc
    except (TimeoutError, ConnectionError, ssl.SSLError, ServerNotFoundError) as exc:
        raise normalize_transport_error(exc) from exc
    if response is None or response == "" or response == b"":
        return {}
    if isinstance(response, str | bytes):
        try:
            response = json.loads(response)
        except (TypeError, ValueError) as exc:
            raise TypeError(f"{command} returned an invalid API response.") from exc
    if not isinstance(response, dict):
        raise TypeError(f"{command} returned a non-object API response.")
    return response


def _tags(service: Resource) -> Any:
    return service.accounts().containers().workspaces().tags()


def _variables(service: Resource) -> Any:
    return service.accounts().containers().workspaces().variables()


def _triggers(service: Resource) -> Any:
    return service.accounts().containers().workspaces().triggers()


def _folders(service: Resource) -> Any:
    return service.accounts().containers().workspaces().folders()


def _workspace_entity(service: Resource, entity: str) -> Any:
    """Return one explicitly-selected workspace entity resource."""
    return getattr(service.accounts().containers().workspaces(), entity)()


def _environments(service: Resource) -> Any:
    return service.accounts().containers().environments()


def _versions(service: Resource) -> Any:
    return service.accounts().containers().versions()


def _containers(service: Resource) -> Any:
    return service.accounts().containers()


def _user_permissions(service: Resource) -> Any:
    return service.accounts().user_permissions()


def _with_optional_fingerprint(
    fingerprint: str | None, **kwargs: Any
) -> dict[str, Any]:
    """Add the upstream concurrency token only when the caller supplied it."""
    if fingerprint is not None:
        kwargs["fingerprint"] = fingerprint
    return kwargs


def update_account(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts update",
        lambda service: service.accounts().update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        scope=TAG_MANAGER_MANAGE_ACCOUNTS_SCOPE,
        service_factory=service_factory,
    )


def create_user_permission(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts user-permissions create",
        lambda service: _user_permissions(service).create(parent=parent, body=body),
        scope=TAG_MANAGER_MANAGE_USERS_SCOPE,
        service_factory=service_factory,
    )


def update_user_permission(
    path: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts user-permissions update",
        lambda service: _user_permissions(service).update(path=path, body=body),
        scope=TAG_MANAGER_MANAGE_USERS_SCOPE,
        service_factory=service_factory,
    )


def delete_user_permission(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_mutation(
        "accounts user-permissions delete",
        lambda service: _user_permissions(service).delete(path=path),
        scope=TAG_MANAGER_MANAGE_USERS_SCOPE,
        service_factory=service_factory,
    )


def _workspaces(service: Resource) -> Any:
    return service.accounts().containers().workspaces()


def create_container(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers create",
        lambda service: _containers(service).create(parent=parent, body=body),
        service_factory=service_factory,
    )


def update_container(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers update",
        lambda service: _containers(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def delete_container(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers delete",
        lambda service: _containers(service).delete(path=path),
        scope=TAG_MANAGER_DELETE_CONTAINERS_SCOPE,
        service_factory=service_factory,
    )


def combine_container(
    path: str,
    *,
    container_id: str | None,
    allow_user_permission_feature_update: bool,
    setting_source: str | None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Combine container settings through the official container action."""
    return execute_mutation(
        "accounts containers combine",
        lambda service: _containers(service).combine(
            path=path,
            containerId=container_id,
            allowUserPermissionFeatureUpdate=allow_user_permission_feature_update,
            settingSource=setting_source,
        ),
        service_factory=service_factory,
    )


def move_container_tag_id(
    path: str,
    *,
    copy_settings: bool,
    allow_user_permission_feature_update: bool,
    tag_id: str | None,
    tag_name: str | None,
    copy_users: bool,
    copy_terms_of_service: bool,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Move a Google tag ID through the official container action."""
    return execute_mutation(
        "accounts containers move-tag-id",
        lambda service: _containers(service).move_tag_id(
            path=path,
            copySettings=copy_settings,
            allowUserPermissionFeatureUpdate=allow_user_permission_feature_update,
            tagId=tag_id,
            tagName=tag_name,
            copyUsers=copy_users,
            copyTermsOfService=copy_terms_of_service,
        ),
        service_factory=service_factory,
    )


def create_workspace(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces create",
        lambda service: _workspaces(service).create(parent=parent, body=body),
        service_factory=service_factory,
    )


def update_workspace(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces update",
        lambda service: _workspaces(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def delete_workspace(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces delete",
        lambda service: _workspaces(service).delete(path=path),
        scope=TAG_MANAGER_DELETE_CONTAINERS_SCOPE,
        service_factory=service_factory,
    )


def create_environment(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers environments create",
        lambda service: _environments(service).create(parent=parent, body=body),
        service_factory=service_factory,
    )


def update_environment(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers environments update",
        lambda service: _environments(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def delete_environment(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers environments delete",
        lambda service: _environments(service).delete(path=path),
        service_factory=service_factory,
    )


def reauthorize_environment(
    path: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Reauthorize an environment with the catalogued publish scope."""
    return execute_mutation(
        "accounts containers environments reauthorize",
        lambda service: _environments(service).reauthorize(path=path, body=body),
        scope=TAG_MANAGER_PUBLISH_SCOPE,
        service_factory=service_factory,
    )


def update_version(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers versions update",
        lambda service: _versions(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        scope=TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        service_factory=service_factory,
    )


def delete_version(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers versions delete",
        lambda service: _versions(service).delete(path=path),
        scope=TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        service_factory=service_factory,
    )


def publish_version(
    path: str,
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Publish one container version using the dedicated publish scope."""
    return execute_mutation(
        "accounts containers versions publish",
        lambda service: _versions(service).publish(
            **_with_optional_fingerprint(fingerprint, path=path)
        ),
        scope=TAG_MANAGER_PUBLISH_SCOPE,
        service_factory=service_factory,
    )


def set_latest_version(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers versions set-latest",
        lambda service: _versions(service).set_latest(path=path),
        service_factory=service_factory,
    )


def undelete_version(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers versions undelete",
        lambda service: _versions(service).undelete(path=path),
        scope=TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        service_factory=service_factory,
    )


def create_tag(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces tags create",
        lambda service: _tags(service).create(parent=parent, body=body),
        service_factory=service_factory,
    )


def update_tag(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces tags update",
        lambda service: _tags(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def revert_tag(
    path: str,
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces tags revert",
        lambda service: _tags(service).revert(
            **_with_optional_fingerprint(fingerprint, path=path)
        ),
        service_factory=service_factory,
    )


def delete_tag(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces tags delete",
        lambda service: _tags(service).delete(path=path),
        service_factory=service_factory,
    )


def create_variable(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces variables create",
        lambda service: _variables(service).create(parent=parent, body=body),
        service_factory=service_factory,
    )


def update_variable(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces variables update",
        lambda service: _variables(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def revert_variable(
    path: str,
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces variables revert",
        lambda service: _variables(service).revert(
            **_with_optional_fingerprint(fingerprint, path=path)
        ),
        service_factory=service_factory,
    )


def delete_variable(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces variables delete",
        lambda service: _variables(service).delete(path=path),
        service_factory=service_factory,
    )


def create_trigger(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces triggers create",
        lambda service: _triggers(service).create(parent=parent, body=body),
        service_factory=service_factory,
    )


def update_trigger(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces triggers update",
        lambda service: _triggers(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def revert_trigger(
    path: str,
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces triggers revert",
        lambda service: _triggers(service).revert(
            **_with_optional_fingerprint(fingerprint, path=path)
        ),
        service_factory=service_factory,
    )


def delete_trigger(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces triggers delete",
        lambda service: _triggers(service).delete(path=path),
        service_factory=service_factory,
    )


def create_folder(
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces folders create",
        lambda service: _folders(service).create(parent=parent, body=body),
        service_factory=service_factory,
    )


def update_folder(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces folders update",
        lambda service: _folders(service).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def revert_folder(
    path: str,
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces folders revert",
        lambda service: _folders(service).revert(
            **_with_optional_fingerprint(fingerprint, path=path)
        ),
        service_factory=service_factory,
    )


def delete_folder(
    path: str,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces folders delete",
        lambda service: _folders(service).delete(path=path),
        service_factory=service_factory,
    )


def move_folder_entities_to_folder(
    path: str,
    *,
    body: dict[str, Any] | None = None,
    variable_ids: list[str] | None = None,
    trigger_ids: list[str] | None = None,
    tag_ids: list[str] | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"path": path}
    if body is not None:
        kwargs["body"] = body
    if variable_ids is not None:
        kwargs["variableId"] = variable_ids
    if trigger_ids is not None:
        kwargs["triggerId"] = trigger_ids
    if tag_ids is not None:
        kwargs["tagId"] = tag_ids
    return execute_mutation(
        "accounts containers workspaces folders move_entities_to_folder",
        lambda service: _folders(service).move_entities_to_folder(**kwargs),
        service_factory=service_factory,
    )


def _create_workspace_entity(
    entity: str,
    parent: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None,
) -> dict[str, Any]:
    return execute_mutation(
        f"accounts containers workspaces {entity} create",
        lambda service: _workspace_entity(service, entity).create(
            parent=parent, body=body
        ),
        service_factory=service_factory,
    )


def _update_workspace_entity(
    entity: str,
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None,
) -> dict[str, Any]:
    return execute_mutation(
        f"accounts containers workspaces {entity} update",
        lambda service: _workspace_entity(service, entity).update(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def _revert_workspace_entity(
    entity: str,
    path: str,
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None,
) -> dict[str, Any]:
    return execute_mutation(
        f"accounts containers workspaces {entity} revert",
        lambda service: _workspace_entity(service, entity).revert(
            **_with_optional_fingerprint(fingerprint, path=path)
        ),
        service_factory=service_factory,
    )


def _delete_workspace_entity(
    entity: str, path: str, *, service_factory: ServiceFactory | None
) -> dict[str, Any]:
    return execute_mutation(
        f"accounts containers workspaces {entity} delete",
        lambda service: _workspace_entity(service, entity).delete(path=path),
        service_factory=service_factory,
    )


def create_client(
    parent: str, body: dict[str, Any], *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _create_workspace_entity(
        "clients", parent, body, service_factory=service_factory
    )


def update_client(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _update_workspace_entity(
        "clients", path, body, fingerprint, service_factory=service_factory
    )


def revert_client(
    path: str, fingerprint: str | None, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _revert_workspace_entity(
        "clients", path, fingerprint, service_factory=service_factory
    )


def delete_client(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _delete_workspace_entity("clients", path, service_factory=service_factory)


def create_zone(
    parent: str, body: dict[str, Any], *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _create_workspace_entity(
        "zones", parent, body, service_factory=service_factory
    )


def update_zone(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _update_workspace_entity(
        "zones", path, body, fingerprint, service_factory=service_factory
    )


def revert_zone(
    path: str, fingerprint: str | None, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _revert_workspace_entity(
        "zones", path, fingerprint, service_factory=service_factory
    )


def delete_zone(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _delete_workspace_entity("zones", path, service_factory=service_factory)


def create_transformation(
    parent: str, body: dict[str, Any], *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _create_workspace_entity(
        "transformations", parent, body, service_factory=service_factory
    )


def update_transformation(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _update_workspace_entity(
        "transformations", path, body, fingerprint, service_factory=service_factory
    )


def revert_transformation(
    path: str, fingerprint: str | None, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _revert_workspace_entity(
        "transformations", path, fingerprint, service_factory=service_factory
    )


def delete_transformation(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _delete_workspace_entity(
        "transformations", path, service_factory=service_factory
    )


def create_template(
    parent: str, body: dict[str, Any], *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _create_workspace_entity(
        "templates", parent, body, service_factory=service_factory
    )


def update_template(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _update_workspace_entity(
        "templates", path, body, fingerprint, service_factory=service_factory
    )


def revert_template(
    path: str, fingerprint: str | None, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _revert_workspace_entity(
        "templates", path, fingerprint, service_factory=service_factory
    )


def delete_template(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _delete_workspace_entity("templates", path, service_factory=service_factory)


def create_gtag_config(
    parent: str, body: dict[str, Any], *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _create_workspace_entity(
        "gtag_config", parent, body, service_factory=service_factory
    )


def update_gtag_config(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _update_workspace_entity(
        "gtag_config", path, body, fingerprint, service_factory=service_factory
    )


def delete_gtag_config(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _delete_workspace_entity(
        "gtag_config", path, service_factory=service_factory
    )


def _built_in_variables(service: Resource) -> Any:
    return service.accounts().containers().workspaces().built_in_variables()


def create_built_in_variable(
    parent: str,
    variable_type: list[str] | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces built-in-variables create",
        lambda service: _built_in_variables(service).create(
            **(
                {"parent": parent}
                | ({"type": variable_type} if variable_type is not None else {})
            )
        ),
        service_factory=service_factory,
    )


def delete_built_in_variable(
    path: str,
    variable_type: list[str] | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces built-in-variables delete",
        lambda service: _built_in_variables(service).delete(
            **(
                {"path": path}
                | ({"type": variable_type} if variable_type is not None else {})
            )
        ),
        service_factory=service_factory,
    )


def revert_built_in_variable(
    path: str,
    variable_type: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_mutation(
        "accounts containers workspaces built-in-variables revert",
        lambda service: _built_in_variables(service).revert(
            **(
                {"path": path}
                | ({"type": variable_type} if variable_type is not None else {})
            )
        ),
        service_factory=service_factory,
    )


def sync_workspace(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    """Synchronize one workspace through the official workspace action."""
    return execute_mutation(
        "accounts containers workspaces sync",
        lambda service: _workspaces(service).sync(path=path),
        service_factory=service_factory,
    )


def quick_preview_workspace(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    """Create an official temporary workspace preview."""
    return execute_mutation(
        "accounts containers workspaces quick-preview",
        lambda service: _workspaces(service).quick_preview(path=path),
        scope=TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        service_factory=service_factory,
    )


def resolve_workspace_conflict(
    path: str,
    body: dict[str, Any],
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Resolve one workspace conflict with the supplied official entity."""
    return execute_mutation(
        "accounts containers workspaces resolve-conflict",
        lambda service: _workspaces(service).resolve_conflict(
            **_with_optional_fingerprint(fingerprint, path=path, body=body)
        ),
        service_factory=service_factory,
    )


def bulk_update_workspace(
    path: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Apply an official ProposedChange payload to one workspace."""
    return execute_mutation(
        "accounts containers workspaces bulk-update",
        lambda service: _workspaces(service).bulk_update(path=path, body=body),
        service_factory=service_factory,
    )


def create_workspace_version(
    path: str,
    body: dict[str, Any],
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Create one container version from the specified workspace."""
    return execute_mutation(
        "accounts containers workspaces create-version",
        lambda service: _workspaces(service).create_version(path=path, body=body),
        scope=TAG_MANAGER_EDIT_CONTAINER_VERSIONS_SCOPE,
        service_factory=service_factory,
    )


def import_template_from_gallery(
    parent: str,
    *,
    gallery_owner: str | None,
    gallery_sha: str | None,
    gallery_repository: str | None,
    acknowledge_permissions: bool,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Import a Gallery template through the official permissions-aware endpoint."""
    return execute_mutation(
        "accounts containers workspaces templates import-from-gallery",
        lambda service: _workspace_entity(service, "templates").import_from_gallery(
            parent=parent,
            galleryOwner=gallery_owner,
            gallerySha=gallery_sha,
            galleryRepository=gallery_repository,
            acknowledgePermissions=acknowledge_permissions,
        ),
        service_factory=service_factory,
    )
