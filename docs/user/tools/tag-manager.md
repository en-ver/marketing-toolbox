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
| `containers` | Ordinary container, workspace, and entity mutations: creates and updates; variable and other entity deletion; environment deletion; and `versions set-latest` |
| `versions` | Version update, delete, and undelete; workspace `quick-preview` and `create-version` |
| `publish` | Version publish and environment reauthorize |
| `delete` | Only container deletion and workspace deletion |

Thus a user-permission read requires `users`, while a variable or environment delete requires `containers`; only container/workspace deletion uses `delete`. Likewise, `versions set-latest` uses `containers`, while version deletion, workspace quick preview, and workspace version creation use `versions`. See [authentication](../auth/_index.md#credential-precedence) for tier-to-scope mappings and separate tool+tier credential records.

## Removed container commands

`gtmctl accounts containers combine` and `gtmctl accounts containers move-tag-id`
are no longer available because their upstream GTM API methods are unsupported and
scheduled for removal. There is no replacement command.

## Transport and mutation failures

GTM reads retain the Discovery client's default `httplib2` transport behavior.
Mutations instead use one bounded Requests dispatch through the official Discovery
transport hook: a mutation makes at most one GTM API send attempt. An initial
credential refresh can make separate pre-API HTTP requests, but a 401 response is
not refreshed and replayed, and redirects (including 307 and 308) are not followed.

Mutation requests use a 60-second Requests connect/read timeout. It is not a total
wall-clock deadline for the whole operation. HTTP 429 remains retryable. For a
mutation HTTP 5xx response or network failure, completion may be unknown; inspect
the current GTM state before retrying rather than assuming that the mutation failed.

GTM mutation transport supports `GOOGLE_API_USE_MTLS_ENDPOINT=auto` (the default)
or `never`; `always` and invalid mTLS configuration are rejected before a request.
An explicitly set `GOOGLE_API_USE_CLIENT_CERTIFICATE` must be `true` or `false`.
This mutation-only restriction avoids automatic certificate discovery. GTM reads
retain their existing Discovery mTLS behavior.

## Selectors, identities, and version lifecycle

`gtmctl accounts containers lookup` requires exactly one selector: supply either
`--destination-id` or `--tag-id`, never both. The command rejects missing or
combined selectors locally before it resolves credentials.

Built-in-variable `create`, `delete`, and `revert` validate each `--type` against
that official method's bundled Discovery enum. Every permitted value is shown in
that leaf's `--type` help. Invalid values are rejected locally for both `--dry-run`
and `--apply`, before credentials are resolved. Repeated `--type` values remain
supported for create and delete; revert's `--type` remains optional.

The Google-tag configuration entity is named `gtag-config` in CLI paths and JSON
envelope command identities. Its official API resource name and dry-run
`data.operation` retain the required `gtag_config` spelling.

`workspaces create-version` deletes the source workspace and makes the newly
created version the container's base version. Its existing
`--acknowledge-version-create` option explicitly acknowledges both effects.

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
