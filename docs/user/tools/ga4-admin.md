---
title: GA4 Admin
weight: 20
---

# GA4 Admin

`ga4adminctl` manages Google Analytics configuration through the Admin API. Most read-only commands use the `read` tier and configuration changes use `edit`; the read-only `accounts change-history search` command also requires `edit`. OAuth consent alone does not grant access to a property.

Read one property with an account that has permission for it:

```bash
ga4adminctl properties get --property properties/1234
```

Use command-specific help before changing configuration. Supported mutations require exactly one of `--dry-run` or `--apply`; dry runs do not call Google. See [authentication](../auth/_index.md#credential-precedence) for the native OAuth tier-to-scope mapping and [tool behavior](_index.md#output-and-requests) for the shared request and output contract.
