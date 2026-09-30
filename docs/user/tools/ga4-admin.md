---
title: GA4 Admin
weight: 20
---

# GA4 Admin

`ga4adminctl` manages Google Analytics configuration through the [Google Analytics Admin API](https://developers.google.com/analytics/devguides/config/admin/v1). Most read-only commands use the `read` tier and configuration changes use `edit`; the read-only `accounts change-history search` command also requires `edit`. OAuth consent alone does not grant access to a property.

Read one property with an account that has permission for it:

```bash
ga4adminctl properties get --property properties/1234
```

For eligible request bodies, inspect the installed SDK descriptor before composing a request:

```bash
ga4adminctl sdk schema --command "properties patch"
```

Eligibility is curated, not universal: `sdk schema` supports explicitly curated request-body, report, and mutation targets. Reads and bodyless deletes are ineligible and should be discovered with their leaf `--help`. A descriptor is not a response schema and does not express every CLI-required field or Google API semantic rule.

## Patch constraints

Each supported patch leaf has a command-owned update-mask allowlist. Its leaf `--help` shows the allowed fields; `sdk schema --command "<patch leaf>"` exposes the same list as `request.cliConstraints.allowedUpdateMaskFields` and records the exact-body requirement. The official SDK resource descriptor can be broader than this CLI allowlist. That broader shape does not make additional fields patchable through this command.

| Patch leaf | Allowed update-mask fields |
| --- | --- |
| `accounts patch` | `displayName`, `regionCode` |
| `properties patch` | `displayName`, `industryCategory`, `timeZone`, `currencyCode` |
| `properties custom-dimensions patch` | `displayName`, `description`, `disallowAdsPersonalization` |
| `properties custom-metrics patch` | `displayName`, `description`, `measurementUnit`, `restrictedMetricType` |
| `properties data-streams patch` | `displayName`, `webStreamData.defaultUri` |
| `properties google-ads-links patch` | `adsPersonalizationEnabled` |
| `properties key-events patch` | `countingMethod`, `defaultValue.numericValue`, `defaultValue.currencyCode` |
| `properties data-streams measurement-protocol-secrets patch` | `displayName` |

For these leaves, `--update-mask` is a nonempty, trimmed, unique comma-separated list of the listed leaf paths, and `--body` must omit `name`. The supplied body and mask must match exactly at the leaf level after accepted protobuf JSON spellings are normalized: an unmasked body leaf or a masked leaf missing from the body is rejected locally. A nested object does not stand in for its individual leaves. Valid reset values remain valid when the installed descriptor accepts them, including `false`, `0`, empty strings or lists, and scalar `null` where applicable.

## Property lists

`properties list --filter` accepts exactly these five forms:

- `parent:accounts/<numeric-id>`
- `parent:properties/<numeric-id>`
- `ancestor:accounts/<numeric-id>`
- `firebase_project:<project-id>`
- `firebase_project:<project-number>`

The older `firebase_project:projects/<project-id>` spelling is intentionally rejected. Migrate existing scripts by removing `projects/`; the accepted filter is forwarded unchanged.

## Destructive Admin mutations

The following destructive leaves require target confirmation when using `--apply`:

- `accounts delete`
- `properties delete`
- `properties data-streams delete`
- `properties custom-dimensions archive`
- `properties custom-metrics archive`
- `properties firebase-links delete`
- `properties google-ads-links delete`
- `properties key-events delete`
- `properties data-streams measurement-protocol-secrets delete`

Pass `--confirm-resource` with the exact same unmodified string as `--name`. This is an intentional compatibility change: existing apply scripts must add this option, and no prompt is shown. A dry run may omit it, but a supplied value must still exactly match `--name`; including the same value in both modes makes a script migratable between validation and apply.

```bash
name="properties/1234/dataStreams/5678"
mode="--dry-run" # change to --apply only when ready
ga4adminctl properties data-streams delete \
  --name "$name" \
  "$mode" \
  --confirm-resource "$name"
```

`accounts delete` and `properties delete` move the resource to trash rather than immediately hard-deleting it. They can be restored outside this CLI before eventual purge; this CLI has no restore command. Custom-dimension and custom-metric commands archive their resources; this CLI has no restore command for those archives. Measurement Protocol secret deletion also requires its existing `--acknowledge-sensitive-data` flag; acknowledgement is additive to, not a substitute for, target confirmation.

## Secret handling

Measurement Protocol secret values are output-only. Create bodies containing either `secretValue` or `secret_value` are rejected in both dry-run and apply modes; use the server-created value rather than supplying one. Responses continue to redact any server-provided secret values.

## Mutation outcomes

Supported mutations require exactly one of `--dry-run` or `--apply`; dry runs do not call Google. The eight GA4 Admin create leaves and `accounts provision-account-ticket` are non-idempotent: each sends one request with retries disabled and a 20-second timeout. A provisioning ticket does not guarantee that an account was created.

For those creates and provisioning, only a Google status of 500, 503, or 504 is reported as uncertain completion: the CLI exits 1 with category `unexpected`, includes the known `googleStatus`, and emits a sanitized instruction to inspect current state before retrying. It does not expose the server error text. Other errors retain the normal diagnostic mapping.

See [authentication](../auth/_index.md#credential-precedence) for the native OAuth tier-to-scope mapping and [tool behavior](_index.md#output-and-requests) for the shared request and output contract.
