---
title: GA4 Data
weight: 10
---

# GA4 Data

`ga4datactl` queries the Google Analytics Data API. Its native OAuth tier is `read`; see [authentication](../auth/_index.md) for credential selection.

Inspect the installed request descriptor before composing a request:

```bash
ga4datactl sdk schema --command "reports run"
```

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

The command returns one response page. Use `rowCount` plus the request's `offset` and `limit` to page through a larger report. Return to [tool behavior](_index.md) for shared output and safety conventions.
