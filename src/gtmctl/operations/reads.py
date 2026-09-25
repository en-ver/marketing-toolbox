"""Bounded official Google Tag Manager API v2 read adapters."""

from __future__ import annotations

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


TAG_MANAGER_READONLY_SCOPE = "https://www.googleapis.com/auth/tagmanager.readonly"
TAG_MANAGER_MANAGE_USERS_SCOPE = (
    "https://www.googleapis.com/auth/tagmanager.manage.users"
)
TAG_MANAGER_READ_TIMEOUT_SECONDS = 20


class Request(Protocol):
    def execute(self, *, num_retries: int = 0) -> dict[str, Any]: ...


ServiceFactory = Callable[[Credentials], Resource]


def make_tag_manager_service(credentials: Credentials) -> Resource:
    """Create the official discovery-backed GTM API v2 client."""
    return build("tagmanager", "v2", credentials=credentials, cache_discovery=False)


def execute_read(
    command: str,
    request_factory: Callable[[Resource], Request],
    *,
    scope: str = TAG_MANAGER_READONLY_SCOPE,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Execute exactly one official GTM read request without auto-retry."""
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
    if not isinstance(response, dict):
        raise TypeError(f"{command} returned a non-object API response.")
    return response


def list_accounts(
    *,
    page_token: str | None = None,
    include_google_tags: bool = False,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts list",
        lambda service: service.accounts().list(
            pageToken=page_token, includeGoogleTags=include_google_tags
        ),
        service_factory=service_factory,
    )


def get_account(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts get",
        lambda service: service.accounts().get(path=path),
        service_factory=service_factory,
    )


def _user_permissions(service: Resource) -> Any:
    return service.accounts().user_permissions()


def get_user_permission(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts user-permissions get",
        lambda service: _user_permissions(service).get(path=path),
        scope=TAG_MANAGER_MANAGE_USERS_SCOPE,
        service_factory=service_factory,
    )


def list_user_permissions(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts user-permissions list",
        lambda service: _user_permissions(service).list(
            parent=parent, pageToken=page_token
        ),
        scope=TAG_MANAGER_MANAGE_USERS_SCOPE,
        service_factory=service_factory,
    )


def list_containers(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts containers list",
        lambda service: (
            service.accounts().containers().list(parent=parent, pageToken=page_token)
        ),
        service_factory=service_factory,
    )


def get_container(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers get",
        lambda service: service.accounts().containers().get(path=path),
        service_factory=service_factory,
    )


def get_environment(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers environments get",
        lambda service: service.accounts().containers().environments().get(path=path),
        service_factory=service_factory,
    )


def list_environments(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts containers environments list",
        lambda service: (
            service.accounts()
            .containers()
            .environments()
            .list(parent=parent, pageToken=page_token)
        ),
        service_factory=service_factory,
    )


def get_version(
    path: str,
    *,
    container_version_id: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"path": path}
    if container_version_id is not None:
        kwargs["containerVersionId"] = container_version_id
    return execute_read(
        "accounts containers versions get",
        lambda service: service.accounts().containers().versions().get(**kwargs),
        service_factory=service_factory,
    )


def get_live_version(
    parent: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers versions live",
        lambda service: service.accounts().containers().versions().live(parent=parent),
        service_factory=service_factory,
    )


def lookup_container(
    *,
    destination_id: str | None = None,
    tag_id: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts containers lookup",
        lambda service: (
            service.accounts()
            .containers()
            .lookup(destinationId=destination_id, tagId=tag_id)
        ),
        service_factory=service_factory,
    )


def list_workspaces(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts containers workspaces list",
        lambda service: (
            service.accounts()
            .containers()
            .workspaces()
            .list(parent=parent, pageToken=page_token)
        ),
        service_factory=service_factory,
    )


def get_workspace(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers workspaces get",
        lambda service: service.accounts().containers().workspaces().get(path=path),
        service_factory=service_factory,
    )


def get_container_snippet(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers snippet",
        lambda service: service.accounts().containers().snippet(path=path),
        service_factory=service_factory,
    )


def list_destinations(
    parent: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers destinations list",
        lambda service: (
            service.accounts().containers().destinations().list(parent=parent)
        ),
        service_factory=service_factory,
    )


def list_version_headers(
    parent: str,
    *,
    page_token: str | None = None,
    include_deleted: bool = False,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts containers version-headers list",
        lambda service: (
            service.accounts()
            .containers()
            .version_headers()
            .list(parent=parent, pageToken=page_token, includeDeleted=include_deleted)
        ),
        service_factory=service_factory,
    )


def get_latest_version_header(
    parent: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers version-headers latest",
        lambda service: (
            service.accounts().containers().version_headers().latest(parent=parent)
        ),
        service_factory=service_factory,
    )


def _workspace_entity_resource(service: Resource, entity: str) -> Any:
    """Return one official workspace child resource by its Discovery name."""
    workspace = service.accounts().containers().workspaces()
    return getattr(workspace, entity)()


def _list_workspace_entity(
    entity: str,
    parent: str,
    *,
    service_factory: ServiceFactory | None = None,
    page_token: str | None = None,
) -> dict[str, Any]:
    return execute_read(
        f"accounts containers workspaces {entity} list",
        lambda service: _workspace_entity_resource(service, entity).list(
            parent=parent, pageToken=page_token
        ),
        service_factory=service_factory,
    )


def _get_workspace_entity(
    entity: str, path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        f"accounts containers workspaces {entity} get",
        lambda service: _workspace_entity_resource(service, entity).get(path=path),
        service_factory=service_factory,
    )


def list_tags(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "tags", parent, page_token=page_token, service_factory=service_factory
    )


def get_tag(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("tags", path, service_factory=service_factory)


def list_variables(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "variables", parent, page_token=page_token, service_factory=service_factory
    )


def get_variable(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("variables", path, service_factory=service_factory)


def list_triggers(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "triggers", parent, page_token=page_token, service_factory=service_factory
    )


def get_trigger(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("triggers", path, service_factory=service_factory)


def list_clients(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "clients", parent, page_token=page_token, service_factory=service_factory
    )


def get_client(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("clients", path, service_factory=service_factory)


def list_folders(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "folders", parent, page_token=page_token, service_factory=service_factory
    )


def get_folder(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("folders", path, service_factory=service_factory)


def list_zones(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "zones", parent, page_token=page_token, service_factory=service_factory
    )


def get_zone(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("zones", path, service_factory=service_factory)


def list_transformations(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "transformations",
        parent,
        page_token=page_token,
        service_factory=service_factory,
    )


def get_transformation(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity(
        "transformations", path, service_factory=service_factory
    )


def list_templates(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "templates", parent, page_token=page_token, service_factory=service_factory
    )


def get_template(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("templates", path, service_factory=service_factory)


def list_gtag_configs(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "gtag_config", parent, page_token=page_token, service_factory=service_factory
    )


def get_gtag_config(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return _get_workspace_entity("gtag_config", path, service_factory=service_factory)


def list_built_in_variables(
    parent: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return _list_workspace_entity(
        "built_in_variables",
        parent,
        page_token=page_token,
        service_factory=service_factory,
    )


def list_folder_entities(
    path: str,
    *,
    page_token: str | None = None,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    return execute_read(
        "accounts containers workspaces folders entities",
        lambda service: (
            service.accounts()
            .containers()
            .workspaces()
            .folders()
            .entities(path=path, pageToken=page_token)
        ),
        service_factory=service_factory,
    )


def get_workspace_status(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_read(
        "accounts containers workspaces get-status",
        lambda service: (
            service.accounts().containers().workspaces().getStatus(path=path)
        ),
        service_factory=service_factory,
    )
