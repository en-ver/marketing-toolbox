# `ga4datactl reports batch-pivot-run` contract

**Contract version:** v1
**Status:** `stable-target`
**Official method:** `analyticsdata.properties.batchRunPivotReports` /
`BetaAnalyticsDataClient.batch_run_pivot_reports`

## Invocation

```text
ga4datactl reports batch-pivot-run --property properties/1234 --body <path|->
```

`--property` must be `properties/<numeric-id>`. `--body` is an opaque UTF-8
JSON request object read from a regular file or standard input (`-`), up to
1,048,576 characters. The CLI supplies the property from `--property`; do not
include `property` in the batch or nested request objects.

The body is an official `BatchRunPivotReportsRequest`. Google documents a
maximum of five nested pivot report requests per batch. The CLI does not expose
a local request schema, `describe`, or field-discovery command. Construct the
body from the official API reference or the installed Google Analytics Data
SDK's `BatchRunPivotReportsRequest` documentation. Google remains authoritative
for request fields, semantics, and limits.

## Behavior

This is a read-only operation. It returns one unaltered Google
`BatchRunPivotReportsResponse` in the success envelope and does not auto-page
nested reports:

```json
{
  "schemaVersion": "marketing-toolbox/v1",
  "command": "ga4datactl reports batch-pivot-run",
  "data": { "pivotReports": [] }
}
```

The command accepts neither `--apply` nor `--dry-run`. Validation failures
write exit code 2, authentication failures exit 4, not-found failures exit 3,
and 429/500/503 failures exit 6; only transient 500/503 failures are retried.

## Sources

- [Google `properties.batchRunPivotReports` v1beta reference](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/batchRunPivotReports)
- [Google Analytics Data API Python SDK](https://googleapis.dev/python/analyticsdata/latest/)
