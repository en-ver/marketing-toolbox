"""Official Google Tag Manager API v2 workspace mutation adapters."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Protocol

import httplib2  # type: ignore[import-untyped]
from google.auth.credentials import Credentials
from google.auth.exceptions import RefreshError, TransportError
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from requests.exceptions import RequestException

from gtmctl.foundation.errors import (
    normalize_authentication_error,
    normalize_mutation_google_error,
    normalize_mutation_transport_error,
    unreadable_mutation_response_error,
)
from gtmctl.operations import transport
from marketing_common.auth import CredentialConfigurationError


class Request(Protocol):
    def add_response_callback(
        self, callback: Callable[[httplib2.Response], None]
    ) -> None: ...

    def execute(
        self, *, num_retries: int = 0
    ) -> dict[str, Any] | list[Any] | str | bytes | None: ...


ServiceFactory = Callable[[Credentials], Resource]


def _execute_request(
    request: Request,
) -> dict[str, Any] | list[Any] | str | bytes | None:
    """Identify SDK decoding failures only after a successful response receipt."""
    successful_response = False

    def record_response(response: httplib2.Response) -> None:
        nonlocal successful_response
        successful_response = 200 <= response.status < 300

    request.add_response_callback(record_response)
    try:
        return request.execute(num_retries=0)
    except UnicodeDecodeError as exc:
        if successful_response:
            raise unreadable_mutation_response_error() from exc
        raise


def execute_mutation(
    command: str,
    request_factory: Callable[[Resource], Request],
    *,
    access: str = "containers",
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Execute exactly one GTM write request without automatic retry."""
    try:
        credentials = transport.credentials_for_access(access)
        if service_factory is None:
            with transport.make_mutation_service(credentials) as service:
                response = _execute_request(request_factory(service))
        else:
            response = _execute_request(request_factory(service_factory(credentials)))
    except CredentialConfigurationError:
        raise
    except (RefreshError, TransportError) as exc:
        raise normalize_authentication_error(exc) from exc
    except HttpError as exc:
        raise normalize_mutation_google_error(exc) from exc
    except RequestException as exc:
        raise normalize_mutation_transport_error(exc) from exc
    if response is None or response == "" or response == b"":
        return {}
    if isinstance(response, str | bytes):
        try:
            response = json.loads(response)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise unreadable_mutation_response_error() from exc
    if not isinstance(response, dict):
        raise unreadable_mutation_response_error()
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
        access="accounts",
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
        access="users",
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
        access="users",
        service_factory=service_factory,
    )


def delete_user_permission(
    path: str, *, service_factory: ServiceFactory | None = None
) -> dict[str, Any]:
    return execute_mutation(
        "accounts user-permissions delete",
        lambda service: _user_permissions(service).delete(path=path),
        access="users",
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
        access="delete",
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
        access="delete",
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
    """Reauthorize an environment with the catalogued publish access tier."""
    return execute_mutation(
        "accounts containers environments reauthorize",
        lambda service: _environments(service).reauthorize(path=path, body=body),
        access="publish",
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
        access="versions",
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
        access="versions",
        service_factory=service_factory,
    )


def publish_version(
    path: str,
    fingerprint: str | None,
    *,
    service_factory: ServiceFactory | None = None,
) -> dict[str, Any]:
    """Publish one container version using the dedicated publish access tier."""
    return execute_mutation(
        "accounts containers versions publish",
        lambda service: _versions(service).publish(
            **_with_optional_fingerprint(fingerprint, path=path)
        ),
        access="publish",
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
        access="containers",
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
        access="versions",
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
        access="versions",
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
        access="versions",
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
