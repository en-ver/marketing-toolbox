---
title: Tool behavior
weight: 30
---

# Tool behavior

Each command's `--help` output is the authoritative command and option reference. Where available, `sdk schema --command "<leaf path>"` prints a locally derived request schema without loading credentials or calling Google.

## Output and requests

Successful API, schema, and version results use structured JSON on standard output. Diagnostics use standard error; `--help` uses normal help text. Request bodies are ordinary JSON files or standard input where a command documents `--body`.

Read commands execute normally. Mutations require an explicit `--dry-run` or `--apply` when supported; a dry run validates and prints the intended request without calling a mutation endpoint. Sensitive or high-impact commands can require an additional acknowledgement. Use placeholder resource identifiers in examples until you replace them with resources you are authorized to access.

## Pagination

List and report commands return one bounded page where applicable. Use the returned continuation token, or the documented request offset and limit, to request another page; commands do not silently collect every page.

## Guides

- [GA4 Data](ga4-data.md) covers a small reporting request.
- [GA4 Admin](ga4-admin.md) covers reading a property and choosing its tier.
- [Tag Manager](tag-manager.md) covers account paths and mutation tiers.
