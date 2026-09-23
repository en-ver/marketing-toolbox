"""Guarded GTM container action command registration."""

from __future__ import annotations

from typing import Annotated, Any

import typer

from gtmctl.commands._common import run_command
from gtmctl.commands.tag_mutations import _dry_run, _validate_execution_mode
from gtmctl.foundation.validation import RequestValidationError, validate_container_path
from gtmctl.operations import mutations


def _require_acknowledgement(value: bool, flag: str) -> None:
    if not value:
        raise RequestValidationError(
            f"{flag} is required before this container action."
        )


def _validate_setting_source(setting_source: str | None) -> None:
    if setting_source is not None and setting_source not in {
        "settingSourceUnspecified",
        "current",
        "other",
    }:
        raise RequestValidationError(
            "--setting-source must be one of settingSourceUnspecified, current, or other."
        )


def register_container_action_commands(containers_app: typer.Typer) -> None:
    """Add high-impact official container actions."""

    @containers_app.command("combine")
    def containers_combine(
        path: Annotated[str, typer.Option("--path", help="Target GTM container path.")],
        container_id: Annotated[
            str | None,
            typer.Option("--container-id", help="Official source container ID."),
        ] = None,
        allow_user_permission_feature_update: Annotated[
            bool,
            typer.Option(
                "--allow-user-permission-feature-update",
                help="Pass the official user-permission feature update option.",
            ),
        ] = False,
        setting_source: Annotated[
            str | None,
            typer.Option("--setting-source", help="Official setting source enum."),
        ] = None,
        acknowledge_combine: Annotated[
            bool,
            typer.Option(
                "--acknowledge-container-combine",
                help="Acknowledge that combining containers can change container settings.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Combine official GTM container settings."""

        def operation() -> dict[str, Any]:
            validate_container_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _validate_setting_source(setting_source)
            _require_acknowledgement(
                acknowledge_combine, "--acknowledge-container-combine"
            )
            if dry_run:
                return _dry_run(operation="containers.combine", target=path) | {
                    "containerId": container_id,
                    "allowUserPermissionFeatureUpdate": allow_user_permission_feature_update,
                    "settingSource": setting_source,
                }
            return mutations.combine_container(
                path,
                container_id=container_id,
                allow_user_permission_feature_update=allow_user_permission_feature_update,
                setting_source=setting_source,
            )

        run_command(command="gtmctl accounts containers combine", operation=operation)

    @containers_app.command("move-tag-id")
    def containers_move_tag_id(
        path: Annotated[str, typer.Option("--path", help="Target GTM container path.")],
        copy_settings: Annotated[
            bool,
            typer.Option("--copy-settings", help="Copy official container settings."),
        ] = False,
        allow_user_permission_feature_update: Annotated[
            bool,
            typer.Option(
                "--allow-user-permission-feature-update",
                help="Pass the official user-permission feature update option.",
            ),
        ] = False,
        tag_id: Annotated[
            str | None, typer.Option("--tag-id", help="Official Google tag ID.")
        ] = None,
        tag_name: Annotated[
            str | None, typer.Option("--tag-name", help="Official Google tag name.")
        ] = None,
        copy_users: Annotated[
            bool,
            typer.Option("--copy-users", help="Copy users as requested by upstream."),
        ] = False,
        copy_terms_of_service: Annotated[
            bool,
            typer.Option(
                "--copy-terms-of-service", help="Copy the official terms setting."
            ),
        ] = False,
        acknowledge_move: Annotated[
            bool,
            typer.Option(
                "--acknowledge-container-move-tag-id",
                help="Acknowledge that moving a Google tag can change container settings.",
            ),
        ] = False,
        dry_run: Annotated[
            bool, typer.Option("--dry-run", help="Validate and print a mutation plan.")
        ] = False,
        apply: Annotated[
            bool, typer.Option("--apply", help="Execute the Google API mutation.")
        ] = False,
    ) -> None:
        """Move an official Google tag ID to this container."""

        def operation() -> dict[str, Any]:
            validate_container_path(path)
            _validate_execution_mode(dry_run=dry_run, apply=apply)
            _require_acknowledgement(
                acknowledge_move, "--acknowledge-container-move-tag-id"
            )
            if dry_run:
                return _dry_run(operation="containers.move-tag-id", target=path) | {
                    "copySettings": copy_settings,
                    "allowUserPermissionFeatureUpdate": allow_user_permission_feature_update,
                    "tagId": tag_id,
                    "tagName": tag_name,
                    "copyUsers": copy_users,
                    "copyTermsOfService": copy_terms_of_service,
                }
            return mutations.move_container_tag_id(
                path,
                copy_settings=copy_settings,
                allow_user_permission_feature_update=allow_user_permission_feature_update,
                tag_id=tag_id,
                tag_name=tag_name,
                copy_users=copy_users,
                copy_terms_of_service=copy_terms_of_service,
            )

        run_command(
            command="gtmctl accounts containers move-tag-id", operation=operation
        )
