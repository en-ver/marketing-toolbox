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

## Property patches

`properties patch` accepts exactly four editable body fields: `displayName`, `industryCategory`, `timeZone`, and `currencyCode`. The `--update-mask` must be a nonempty, trimmed, unique comma-separated list drawn only from those fields. The body must omit `name`, and its fields must exactly match the update-mask: every mask field belongs in the body and every body field belongs in the mask.

The official SDK `Property` resource descriptor is broader than this CLI's editable-field allowlist. Its broader shape does not make other Property fields patchable through this command. Use `ga4adminctl properties patch --help` for the exact mode and acknowledgement options before a mutation.

Supported mutations require exactly one of `--dry-run` or `--apply`; dry runs do not call Google. See [authentication](../auth/_index.md#credential-precedence) for the native OAuth tier-to-scope mapping and [tool behavior](_index.md#output-and-requests) for the shared request and output contract.
