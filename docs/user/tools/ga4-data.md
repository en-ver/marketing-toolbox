---
title: GA4 Data
weight: 10
---

# GA4 Data

`ga4datactl` queries the [Google Analytics Data API](https://developers.google.com/analytics/devguides/reporting/data/v1). Its native OAuth tier is `read`; see [authentication](../auth/_index.md) for credential selection and the separate resource-permission requirement.

Start with the installed request descriptor when composing a request. This route is local, credential-free, and network-free:

```bash
ga4datactl sdk schema --command "reports run"
```

The descriptor is a request shape, not a response schema or a complete statement of CLI requiredness and Google semantics. `sdk schema` is available for the six report leaves (`reports run`, `batch-run`, `pivot-run`, `realtime-run`, `batch-pivot-run`, and `compatibility-check`) and for `audience-exports create`.

Each of those six report leaves supports `--schema` in 0.3.1. For example:

```bash
ga4datactl reports run --schema
```

The flag alone prints the CLI structural body JSON Schema; it does not need `--property`, `--body`, stdin, credentials, or network access. It does not run a report. Additional CLI cross-field checks, live property metadata, and Google API semantic validation still apply. On earlier 0.2.0 installations, use the `sdk schema` command above. There is no offline report execution or validate-only command.

`audience-exports create` already supports both schema routes, with different meanings:

```bash
ga4datactl audience-exports create --schema
ga4datactl sdk schema --command "audience-exports create"
```

The first is the CLI structural validator schema; the second is the installed SDK request descriptor. Audience-export reads use their leaf help rather than an SDK body schema.

Audience-export creation requires exactly one of `--dry-run` or `--apply`. A dry run stays local and returns the request plan. An apply submits the create request once, with no automatic retry or operation polling. If apply returns an `unexpected` diagnostic saying creation may have succeeded, inspect existing audience exports before submitting the same request again.

Run a small core report with a property you are allowed to read. The request body must not include `property` because `--property` supplies it:

```bash
cat > report.json <<'JSON'
{
  "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
  "metrics": [{"name": "activeUsers"}],
  "limit": "10"
}
JSON

ga4datactl reports run --property properties/1234 --body report.json
```

The command returns one response page. Use `rowCount` plus the request's `offset` and `limit` to page through a larger report. Property-specific metadata is live Google data, so it requires an authorized property and is separate from local schema discovery. Return to [tool behavior](_index.md) for shared output and safety conventions.
