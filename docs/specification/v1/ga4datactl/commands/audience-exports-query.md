# `ga4datactl audience-exports query` contract

**Contract version:** v1
**Status:** `stable-target`
**Official method:** `analyticsdata.properties.audienceExports.query` / `BetaAnalyticsDataClient.query_audience_export`
**Upstream:** Google Analytics Data API `v1beta`, Discovery revision `20260722`

## Purpose and safety

Return a caller-selected page of audience-export user rows. These rows are sensitive data.

- Safety class: `sensitive-read`.
- `--acknowledge-sensitive-data` is required on every invocation. It is an explicit intent guardrail, not authorization.
- OAuth scope: `https://www.googleapis.com/auth/analytics.readonly`.
- The command performs one SDK call only. It does not implicitly paginate, log, persist, redact, or transform the returned user-row data.

## Invocation

```text
ga4datactl audience-exports query \
  --property properties/1234 \
  --name properties/1234/audienceExports/export-1 \
  --limit 100 \
  --offset 0 \
  --acknowledge-sensitive-data
```

`--property` must match `properties/<numeric-id>`. `--name` must match `properties/<numeric-id>/audienceExports/<id>` and belong to `--property`. `--limit` is required and must be 1 through 1000. `--offset` is optional, defaults to 0, and must be zero or greater. Offset is the only pagination input; there is no page token or implicit follow-up request.

## Successful stdout

The command writes exactly one standard envelope. Its `data` is the official SDK response in protobuf JSON field names, including `audienceExport`, `audienceRows`, and `rowCount` when returned by Google.

```json
{
  "schemaVersion": "marketing-tools/v1",
  "command": "ga4datactl audience-exports query",
  "data": {
    "audienceRows": [{"dimensionValues": [{"value": "user-1"}]}],
    "rowCount": 25
  }
}
```

## Failures and retries

Invalid input exits 2; authentication/authorization failures exit 4; missing resources exit 3; conflicts exit 5; and 429/500/503 failures exit 6. Only transient 500/503 SDK failures use the standard bounded retry policy. No live query is used for tests or documentation.

## Sources

- [Google `properties.audienceExports.query` v1beta reference](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties.audienceExports/query)
- [Google audience-export basics](https://developers.google.com/analytics/devguides/reporting/data/v1/audience-export-basics)
