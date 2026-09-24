# `ga4datactl audience-exports create` contract

**Contract version:** v1
**Status:** `stable-target`
**Official method:** `analyticsdata.properties.audienceExports.create` / `BetaAnalyticsDataClient.create_audience_export`
**Upstream:** Google Analytics Data API `v1beta`, Discovery revision `20260722`

## Purpose and safety

Create an asynchronous snapshot of a GA4 audience for later retrieval. This is a Google-side write: each invocation can consume audience-export quota and create a new export.

- Safety class: `mutation`
- Exactly one control is required: `--dry-run` or `--apply`.
- `--dry-run` validates the full request and writes its exact intended official request; it does not load credentials, create a client, or call Google.
- `--apply` is the only mode that calls the SDK and initiates the export. It is an intent guardrail, not authorization.
- OAuth scope: `https://www.googleapis.com/auth/analytics`.

## Invocation

```text
ga4datactl audience-exports create --property properties/1234 --body <path|-> --dry-run
ga4datactl audience-exports create --property properties/1234 --body <path|-> --apply
```

`--property` must match `^properties/[0-9]+$`. `--body` is a UTF-8 JSON object up to 1,048,576 characters, read from a file or standard input, and validates against [`schemas/create-audience-export-body.schema.json`](../schemas/create-audience-export-body.schema.json). The CLI rejects no control, both controls, output-only fields, unknown fields, and source audiences outside `--property` before credential lookup or any SDK call.

## Request body

```json
{
  "audience": "properties/1234/audiences/42",
  "dimensions": [{"dimensionName": "audienceId"}]
}
```

| Field | Required | Contract |
| --- | --- | --- |
| `audience` | yes | Existing source audience matching `properties/<numeric-id>/audiences/<id>` and belonging to `--property`. |
| `dimensions` | yes | Non-empty `AudienceDimension[]`. Each object has only optional `dimensionName`, the GA4 audience-list API dimension name. |

The body is the writable `AudienceExport` subset only. `name`, `audienceDisplayName`, `state`, `beginCreatingTime`, `creationQuotaTokensCharged`, `rowCount`, `errorMessage`, and `percentageCompleted` are output-only and rejected.

## Asynchronous operation handling

The official method returns a long-running operation. On `--apply`, this command initiates exactly one bounded SDK call (20-second RPC deadline, bounded transient retry) and returns its operation name. It never calls `result()`, polls, reloads, or waits for the operation, so it has no implicit or unbounded polling behavior. Later lifecycle inspection and querying are separate explicit commands.

## Successful stdout

Both modes output exactly one normalized JSON document conforming to [`schemas/create-audience-export-success.schema.json`](../schemas/create-audience-export-success.schema.json).

Dry run:

```json
{
  "schemaVersion": "marketing-toolbox/v1",
  "command": "ga4datactl audience-exports create",
  "data": {
    "dryRun": true,
    "request": {
      "parent": "properties/1234",
      "audienceExport": {"audience": "properties/1234/audiences/42", "dimensions": [{"dimensionName": "audienceId"}]}
    }
  }
}
```

Apply:

```json
{
  "schemaVersion": "marketing-toolbox/v1",
  "command": "ga4datactl audience-exports create",
  "data": {"operationName": "operations/audience-export-creation-123"}
}
```

## Failures and retries

Validation errors exit 2; authentication/authorization errors exit 4; missing resources exit 3; conflicts exit 5; 429/500/503 exit 6. Only transient 500/503 SDK failures use bounded exponential retry. The command returns after initiating the operation and does not retry or poll its lifecycle.

## Acceptance fixtures

| Fixture | Expected outcome |
| --- | --- |
| `fixtures/audience-exports-create/valid-basic-request.json` | Valid dry-run intent and official request shape. |
| `fixtures/audience-exports-create/invalid-output-only-field.json` | Reject with exit 2 before SDK invocation. |
| `fixtures/audience-exports-create/invalid-cross-property-audience.json` | Reject with exit 2 before SDK invocation. |

## Sources

- [Google `properties.audienceExports.create` v1beta reference](https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties.audienceExports/create)
- [Google audience-export basics](https://developers.google.com/analytics/devguides/reporting/data/v1/audience-export-basics)
- [Google audience-list API schema](https://developers.google.com/analytics/devguides/reporting/data/v1/audience-list-api-schema)
