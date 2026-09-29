---
title: Tag Manager
weight: 30
---

# Tag Manager

`gtmctl` works with [Google Tag Manager API v2](https://developers.google.com/tag-platform/tag-manager/api/v2) resource paths. An account path is `accounts/<account-id>`; containers and workspaces extend it as `accounts/<account-id>/containers/<container-id>/workspaces/<workspace-id>`.

Read one account you are authorized to access:

```bash
gtmctl accounts get --path accounts/1
```

## Native OAuth tiers

The native OAuth tier is specific to the operation, not merely whether it reads, writes, or deletes:

| Tier | Reviewed operation family |
| --- | --- |
| `read` | Ordinary reads, including version reads |
| `users` | Account user-permission get, list, create, update, and delete |
| `accounts` | Account update |
| `containers` | Ordinary container, workspace, and entity mutations: creates and updates; variable and other entity deletion; environment deletion; container actions; and `versions set-latest` |
| `versions` | Version update, delete, and undelete; workspace `quick-preview` and `create-version` |
| `publish` | Version publish and environment reauthorize |
| `delete` | Only container deletion and workspace deletion |

Thus a user-permission read requires `users`, while a variable or environment delete requires `containers`; only container/workspace deletion uses `delete`. Likewise, `versions set-latest` uses `containers`, while version deletion, workspace quick preview, and workspace version creation use `versions`. See [authentication](../auth/_index.md#credential-precedence) for tier-to-scope mappings and separate tool+tier credential records.

## Body descriptors and dry runs

For an eligible body leaf, inspect the bundled official Discovery request descriptor locally:

```bash
gtmctl sdk schema --command "accounts containers workspaces variables create"
```

A GTM leaf is eligible only when it accepts `--body` and has a matching bundled official Discovery method descriptor. Reads and bodyless deletes use leaf help instead. The descriptor is not a response schema or full validation contract.

`--dry-run` checks local inputs and prints a no-network plan. It does not validate a body against the Discovery schema, Google API semantics, or any response schema. Local checks can still reject bad route syntax, execution mode, acknowledgements, fingerprints, option constraints, or a non-object/oversized JSON body. The plan's `data.mode` is `"dry-run"` and `data.applied` is `false`; `data.bodySha256` appears only when a body was supplied. Treat that hash as an input fingerprint, not API acceptance.

Here is a synthetic Constant-variable body and a safe no-network plan. The IDs and name are placeholders only:

```bash
cat > constant.json <<'JSON'
{
  "name": "Example constant",
  "type": "c",
  "parameter": [
    {"type": "template", "key": "value", "value": "example"}
  ]
}
JSON

gtmctl accounts containers workspaces variables create \
  --parent accounts/123/containers/456/workspaces/789 \
  --body constant.json \
  --dry-run
```

For the resource shape, see the official [Variables reference](https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/accounts.containers.workspaces.variables) and [Parameter reference](https://developers.google.com/tag-platform/tag-manager/api/reference/rest/v2/Parameter). This guide does not claim a separate official Constant-specific page; use the leaf help, bundled descriptor, and these references together.

Mutations use explicit `--dry-run` or `--apply`, and high-impact changes can require another acknowledgement. Command help describes the installed options and acknowledgements. See [tool behavior](_index.md) for shared pagination, output, and safety conventions.
