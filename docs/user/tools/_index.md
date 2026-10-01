---
title: Tool behavior
weight: 30
---

# Tool behavior

Each command's `--help` output is the authoritative command and option reference. Discover a command recursively with `<tool> --help`, then `<tool> <group> --help`, then the leaf's `--help`. Where available, `sdk schema --command "<leaf path>"` prints a locally derived request descriptor without loading credentials or calling Google.

## Output and requests

A successful non-help command writes one JSON envelope to standard output with `schemaVersion`, `command`, and `data`. JSON diagnostics write to standard error with `schemaVersion`, `command`, `exitCode`, `category`, and `message`; an API diagnostic can also include `googleStatus`.

Help is deliberately different: explicit `--help` writes plain text to stdout and exits 0, while no-argument help writes plain text to stderr and exits 2. Interactive OAuth may also print an authorization URL or progress text to stderr, so stderr is not always a single JSON document.

| Exit code | Categories |
| --- | --- |
| 0 | `success` |
| 1 | `unexpected` for an unmapped API failure, or `unexpected_failure` for an uncaught CLI-boundary failure |
| 2 | `invalid_arguments` for parsing or an ineligible schema path, or `invalid_request` for local or API request validation |
| 3 | `not_found` |
| 4 | `authentication` |
| 5 | `conflict` or `failed_precondition` |
| 6 | `retryable` |

Request bodies are ordinary JSON files or standard input where a leaf documents `--body`. Use placeholder resource identifiers in examples until you replace them with resources you are authorized to access.

## Request discovery and validation boundaries

`<tool> sdk schema --command "<leaf path>"` returns an installed official SDK or Discovery **request descriptor**, not a response schema or complete CLI contract. It may describe field shapes, types, and enums, but does not universally express CLI requiredness or Google semantic validation.

Eligibility is intentionally per tool:

- `ga4datactl`: the six report leaves and `audience-exports create` are eligible. The existing `audience-exports create --schema` route prints the CLI structural body schema; its `sdk schema` route prints the installed SDK request descriptor. Audience-export reads and other non-body leaves use leaf help.
- `ga4adminctl`: explicitly curated request-body, report, and mutation targets are eligible. Patch descriptors additionally expose the command-owned update-mask constraints; reads and bodyless deletes use leaf help.
- `gtmctl`: a registered leaf with `--body` is eligible only when it also has a bundled official Discovery request descriptor. Reads and bodyless deletes use leaf help.

In 0.5.0, the six GA4 report leaves also offer `--schema`, which prints the structural JSON Schema used by the CLI body validator. It is not a response schema: additional CLI cross-field checks, live property metadata, and Google API semantic validation still apply. On earlier 0.2.0 installations, use the existing `ga4datactl sdk schema` route. Report execution has no offline execution or validate-only command; a report leaf executes against Google after its normal validation.

Supported mutations require the documented explicit `--dry-run` or `--apply` mode, and some require an acknowledgement. A GA4 dry run performs that command's documented local validation and returns its plan without calling a mutation endpoint. The nine destructive GA4 Admin leaves documented in [GA4 Admin](ga4-admin.md#destructive-admin-mutations) also accept `--confirm-resource`; it may be omitted for a dry run, but when supplied it must exactly match `--name`, and it is required with `--apply`. See that guide for the intentional script-migration behavior, patch constraints, secret handling, and the narrow uncertain-completion policy for non-idempotent Admin creates and provisioning. GA4 audience-export creation submits an apply request once; it does not retry or poll the operation. A GTM dry run is narrower: it checks command-local inputs and emits a no-network plan, but does not validate a body against the Discovery schema, Google API semantics, or any response schema. It can still enforce route syntax, execution mode, acknowledgements, fingerprints, option constraints, and bounded JSON-object parsing. A GTM plan includes `bodySha256` only when the command has a body.

## Pagination

List and report commands return one bounded page where applicable. Use the returned continuation token, or the documented request offset and limit, to request another page; commands do not silently collect every page.

## Guides

- [GA4 Data](ga4-data.md) covers a small reporting request and its schema routes.
- [GA4 Admin](ga4-admin.md) covers reading and patching a property.
- [Tag Manager](tag-manager.md) covers account paths, mutation tiers, and a safe Constant-variable dry run.
