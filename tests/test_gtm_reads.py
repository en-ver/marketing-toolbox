"""Core GTM read adapter contracts."""

from __future__ import annotations

from typing import Any

import pytest

from gtmctl.operations import reads


class FakeRequest:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[int] = []

    def execute(self, *, num_retries: int = 0) -> dict[str, Any]:
        self.calls.append(num_retries)
        return self.response


class FakeResource:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __getattr__(self, name: str) -> Any:
        if name in {
            "accounts",
            "containers",
            "workspaces",
            "destinations",
            "environments",
            "versions",
            "version_headers",
        }:
            return lambda: self

        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((name, kwargs))
            return FakeRequest(self.response)

        return request


class WorkspaceFakeResource:
    def __init__(
        self, calls: list[tuple[str, str, dict[str, Any]]], path: str = ""
    ) -> None:
        self.calls = calls
        self.path = path

    def __getattr__(self, name: str) -> Any:
        resources = {
            "accounts",
            "containers",
            "workspaces",
            "tags",
            "variables",
            "triggers",
            "clients",
            "folders",
            "zones",
            "transformations",
            "templates",
            "gtag_config",
            "built_in_variables",
        }
        if name in resources:
            child_path = "/".join(part for part in (self.path, name) if part)
            return lambda: WorkspaceFakeResource(self.calls, child_path)

        def request(**kwargs: Any) -> FakeRequest:
            self.calls.append((self.path, name, kwargs))
            return FakeRequest({"path": self.path})

        return request


@pytest.fixture
def fake_service(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[FakeResource, list[list[str]]]:
    service = FakeResource(
        {"nextPageToken": "next", "account": [{"path": "accounts/1"}]}
    )
    scopes: list[list[str]] = []
    monkeypatch.setattr(
        reads,
        "service_account_credentials",
        lambda requested_scopes: (
            scopes.__iadd__([requested_scopes]),
            object(),
        )[1],
    )
    return service, scopes


def test_account_list_uses_direct_request_preserving_official_pagination(
    fake_service: tuple[FakeResource, list[list[str]]],
) -> None:
    service, scopes = fake_service
    assert (
        reads.list_accounts(
            page_token="next",
            include_google_tags=True,
            service_factory=lambda _: service,
        )
        == service.response
    )
    assert service.calls == [("list", {"pageToken": "next", "includeGoogleTags": True})]
    assert scopes == [[reads.TAG_MANAGER_READONLY_SCOPE]]


def test_lookup_uses_official_camel_case_query_names(
    fake_service: tuple[FakeResource, list[list[str]]],
) -> None:
    service, _ = fake_service
    reads.lookup_container(
        destination_id="AW-123", tag_id="G-ABC", service_factory=lambda _: service
    )
    assert service.calls == [("lookup", {"destinationId": "AW-123", "tagId": "G-ABC"})]


@pytest.mark.parametrize(
    ("operation", "args", "expected"),
    [
        (
            reads.get_environment,
            ("accounts/1/containers/2/environments/3",),
            ("get", {"path": "accounts/1/containers/2/environments/3"}),
        ),
        (
            reads.list_environments,
            ("accounts/1/containers/2",),
            ("list", {"parent": "accounts/1/containers/2", "pageToken": None}),
        ),
        (
            reads.get_version,
            ("accounts/1/containers/2/versions/3",),
            ("get", {"path": "accounts/1/containers/2/versions/3"}),
        ),
        (
            reads.get_live_version,
            ("accounts/1/containers/2",),
            ("live", {"parent": "accounts/1/containers/2"}),
        ),
    ],
)
def test_new_container_reads_map_one_official_request(
    fake_service: tuple[FakeResource, list[list[str]]],
    operation: Any,
    args: tuple[Any, ...],
    expected: tuple[str, dict[str, Any]],
) -> None:
    service, scopes = fake_service
    assert operation(*args, service_factory=lambda _: service) == service.response
    assert service.calls == [expected]
    assert scopes == [[reads.TAG_MANAGER_READONLY_SCOPE]]


def test_workspace_entity_read_uses_explicit_resource_chain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    monkeypatch.setattr(reads, "service_account_credentials", lambda _: object())
    reads.list_tags(
        "accounts/1/containers/2/workspaces/3",
        page_token="next",
        service_factory=lambda _: WorkspaceFakeResource(calls),
    )
    assert calls == [
        (
            "accounts/containers/workspaces/tags",
            "list",
            {"parent": "accounts/1/containers/2/workspaces/3", "pageToken": "next"},
        )
    ]


def test_workspace_folder_entity_read_uses_official_entities_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    monkeypatch.setattr(reads, "service_account_credentials", lambda _: object())
    reads.list_folder_entities(
        "accounts/1/containers/2/workspaces/3/folders/4",
        page_token="next",
        service_factory=lambda _: WorkspaceFakeResource(calls),
    )
    assert calls == [
        (
            "accounts/containers/workspaces/folders",
            "entities",
            {
                "path": "accounts/1/containers/2/workspaces/3/folders/4",
                "pageToken": "next",
            },
        )
    ]
