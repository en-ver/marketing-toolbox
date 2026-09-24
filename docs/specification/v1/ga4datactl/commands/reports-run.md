# `ga4datactl reports run` contract

**Contract version:** v1
**Status:** `stable-target`
**Official method:** `analyticsdata.properties.runReport` / `BetaAnalyticsDataClient.run_report`

## Invocation

```text
ga4datactl reports run --property properties/1234 --body <path|->
```

`--property` is the Google property resource name (`properties/<numeric-id>`).
`--body` is an opaque UTF-8 JSON request object read from a regular file or `-`
for standard input (maximum 1,048,576 characters). Do not put `property` in the
body: the CLI supplies it from `--property`.

The CLI does not publish a local request schema or field-discovery command.
Construct the body from the official API reference or the installed Google
Analytics Data SDK's `RunReportRequest` documentation. The CLI may reject an
invalid body before dispatch; Google remains authoritative for request fields,
semantics, and limits.

## Behavior

This is a read-only operation that returns exactly one upstream response page;
it never auto-pages. Use the official request's pagination fields and the
response `rowCount` when fetching later pages. The CLI preserves the upstream
response in the repository-wide success envelope:

```json
{
  "schemaVersion": "marketing-toolbox/v1",
  "command": "ga4datactl reports run",
  "data": { "...": "unaltered Google RunReportResponse JSON" }
}
```

On failure stdout is empty and stderr contains a redacted normalized JSON
diagnostic. The command accepts neither `--apply` nor `--dry-run`.

## Sources

- [Google `properties.runReport` v1beta reference](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport)
- [Google Analytics Data API Python SDK](https://googleapis.dev/python/analyticsdata/latest/)
- [Google report basics](https://developers.google.com/analytics/devguides/reporting/data/v1/basics)
- [Google quota guidance](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas)
