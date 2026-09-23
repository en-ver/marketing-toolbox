# `gtmctl` v1 command-family contracts

This companion document makes the catalog's implementation rules testable. It
contains no API methods beyond the official v2 catalog.

## Command naming and module layout

The future package follows the GA4 CLI structure:

```text
src/gtmctl/
  cli.py                 # small root composition façade
  commands/              # cohesive Typer command-family modules
  operations/            # official googleapiclient request adapters
  foundation/            # auth, bounded JSON intake, names, envelopes, errors
```

Typer command groups mirror official resources: `accounts`, then nested
`containers`, `user-permissions`, `workspaces`, and their child resources.
Names are kebab-case transformations of the official Discovery resource/method
name; an exception needs a documented compatibility reason and a catalog update.

## Read-only baseline

For every `GET` stable target and the readonly-scoped `folders entities` target:

- require all official path/parent parameters and expose only documented query
  parameters;
- construct one `googleapiclient` request and call `.execute()` once;
- return the raw official response, with no synthesized summaries;
- expose `pageToken` exactly where upstream offers it and never auto-follow it;
- use the narrowest scope listed in the catalog, normally
  `tagmanager.readonly`; and
- have fixture/fake tests for request mapping, response envelope, error mapping,
  and no credential/network activity in local validation paths.

## Body-carrying actions

For every catalog row with a request resource:

- require a bounded UTF-8 JSON object through `--body <file|->`;
- inject route identifiers through the official request parameters, never by
  trusting duplicate body identifiers;
- preserve all official writable fields rather than maintaining a CLI-owned
  schema catalog; unknown or unsupported fields are handled by the official API
  response/diagnostics;
- pass `fingerprint` only through the official query parameter for methods that
  define it; and
- make dry-run output deterministic and secret-safe.

## Entity and workspace actions

Tags, triggers, variables, clients, folders, zones, transformations, templates,
and gtag configurations share create/get/list/update/delete/revert lifecycle
patterns but retain resource-specific route building and redaction. Built-in
variables have the upstream `type` query contract; folders' move operation has
only upstream `tagId`, `triggerId`, and `variableId` query inputs. Do not merge
those into an invented generic entity endpoint.

## High-impact actions

- `versions publish` additionally requires `--acknowledge-publish` and must
  emit an explicit dry-run statement that no container version was published.
- Account updates require `--acknowledge-account-update`. Account
  user-permission create/update/delete commands require
  `--acknowledge-permission-change`; delete additionally requires
  `--acknowledge-user-permission-delete`. Permission reads require
  `--acknowledge-sensitive-data`; the CLI must not print access grants in
  diagnostics.
- Delete methods require a resource-specific destructive acknowledgement in
  addition to `--apply`; no delete can be retried automatically.
- `environments reauthorize`, gallery-template import, container move/combine,
  workspace bulk update, workspace create-version, and quick preview are
  action-class operations. They require their catalogued scope, dry-run/apply,
  and an operation-specific acknowledgement. Implemented acknowledgements are
  `--acknowledge-environment-reauthorize`, `--acknowledge-container-combine`,
  `--acknowledge-container-move-tag-id`,
  `--acknowledge-workspace-bulk-update`, `--acknowledge-version-create`,
  `--acknowledge-quick-preview`, and
  `--acknowledge-template-import-permissions`. Gallery import's bounded JSON
  input contains only its official Gallery query fields; dry-run emits its
  SHA-256 digest rather than those field values and never loads credentials.
  Create-version uses its acknowledgement as the required destructive safety
  control. Each action needs individual acceptance fixtures before implementation.

## Acceptance evidence required per increment

Each delivered command family needs: catalog/help parity, official request-path
and query/body mapping tests, dry-run/apply refusal tests where applicable,
response-envelope and normalized-error tests, one-page pagination tests where
available, Ruff, MyPy, compilation, package build, and an explicitly approved
bounded live read before any live mutation.
