---
title: Tag Manager
weight: 30
---

# Tag Manager

`gtmctl` works with Tag Manager resource paths. An account path is `accounts/<account-id>`; containers and workspaces extend it as `accounts/<account-id>/containers/<container-id>/workspaces/<workspace-id>`.

Read one account you are authorized to access:

```bash
gtmctl accounts get --path accounts/1
```

The native OAuth tier depends on the operation. `read` covers standard reads, but account user-permission reads and changes use `users`; account updates use `accounts`. Most container and workspace entity edits, including tag deletion, use `containers`; version reads use `read`; `versions set-latest` uses `containers`; version update, delete, and undelete use `versions`; publishing uses `publish`; and deleting a container or workspace uses `delete`. Command help describes supported options and mutation acknowledgements, not the native OAuth tier. Mutations use explicit `--dry-run` or `--apply`, and high-impact changes can require another acknowledgement. See [authentication](../auth/_index.md#credential-precedence) for the tier-to-scope mapping.

For request-body leaves, inspect the local descriptor with `gtmctl sdk schema --command "accounts update"`. See [tool behavior](_index.md) for shared pagination, output, and safety conventions.
