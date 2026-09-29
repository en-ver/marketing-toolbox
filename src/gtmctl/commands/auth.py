"""Native OAuth commands for GTM access."""

from marketing_common.oauth_cli import make_auth_app

app = make_auth_app(
    "gtmctl",
    access_guidance=(
        "GTM ordinary reads use read; user-permission get/list/create/update/delete "
        "use users; account update uses accounts. Ordinary container/workspace/entity "
        "edits and entity/environment deletion use containers; only container/workspace "
        "deletion use delete. Version update/delete/undelete and workspace quick-preview/"
        "create-version use versions; version set-latest uses containers; version publish "
        "and environment reauthorize use publish."
    ),
)
