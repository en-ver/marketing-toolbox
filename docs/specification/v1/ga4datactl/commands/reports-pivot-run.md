# `ga4datactl reports pivot-run` contract

**Contract version:** v1
**Status:** `stable-target`
**Official method:** `analyticsdata.properties.runPivotReport` /
`BetaAnalyticsDataClient.run_pivot_report`

## Invocation

```text
ga4datactl reports pivot-run --property properties/1234 --body <path|->
```

`--property` is the Google property resource name (`properties/<numeric-id>`).
`--body` is an opaque UTF-8 JSON request object from a regular file or `-` for
standard input (maximum 1,048,576 characters). The CLI supplies `property` from
`--property`; the body must not contain it.

The body is an official `RunPivotReportRequest`. The CLI does not publish a
local request schema or field-discovery command. Build the request with the
official API reference or the installed Google Analytics Data SDK's
`RunPivotReportRequest` documentation. Google is authoritative for the request
shape, pivot semantics, and limits, including the product of pivot limits.

## Behavior

This read-only command returns one upstream response and does not auto-page.
Pivot pagination is controlled by the official request's per-pivot offsets.
Successful output preserves the Google `RunPivotReportResponse` in `data`:

```json
{
  "schemaVersion": "marketing-tools/v1",
  "command": "ga4datactl reports pivot-run",
  "data": { "...": "unaltered Google RunPivotReportResponse JSON" }
}
```

The CLI does not flatten or render the pivot response. The command accepts
neither `--apply` nor `--dry-run`; failures write a redacted normalized JSON
diagnostic to stderr.

## Sources

- [Google `properties.runPivotReport` v1beta reference](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runPivotReport)
- [Google `Pivot` reference](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/Pivot)
- [Google Analytics Data API Python SDK](https://cloud.google.com/python/docs/reference/analyticsdata/latest)
