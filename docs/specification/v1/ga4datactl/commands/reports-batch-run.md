# `ga4datactl reports batch-run` contract

**Contract version:** v1
**Status:** `stable-target`
**Official method:** `analyticsdata.properties.batchRunReports` /
`BetaAnalyticsDataClient.batch_run_reports`

## Invocation

```text
ga4datactl reports batch-run --property properties/1234 --body <path|->
```

`--property` is the only property selector and must be
`properties/<numeric-id>`. `--body` is an opaque UTF-8 JSON request object,
read from a regular file or `-` for standard input (maximum 1,048,576
characters). Do not include `property` in the top-level or nested request
objects; all reports use `--property`.

The body is an official `BatchRunReportsRequest`. A batch accepts up to five
report requests, as documented by Google. The CLI intentionally provides no
local request schema, `describe`, or field-discovery surface. Use the official
API reference or the installed Google Analytics Data SDK's
`BatchRunReportsRequest` documentation to construct the request. Google is
authoritative for request fields, semantics, and limits.

## Behavior

This is a read-only operation. It sends one batch RPC and does not auto-page
any individual report. Successful output is the normal envelope, with the
unaltered Google `BatchRunReportsResponse` in `data`. The command accepts
neither `--apply` nor `--dry-run`.

```json
{
  "schemaVersion": "marketing-tools/v1",
  "command": "ga4datactl reports batch-run",
  "data": { "...": "unaltered Google BatchRunReportsResponse JSON" }
}
```

On failure stdout is empty and stderr contains a redacted normalized JSON
diagnostic.

## Sources

- [Google `properties.batchRunReports` v1beta reference](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/batchRunReports)
- [Google Analytics Data API Python SDK](https://cloud.google.com/python/docs/reference/analyticsdata/latest)
- [Google quota guidance](https://developers.google.com/analytics/devguides/reporting/data/v1/quota)
