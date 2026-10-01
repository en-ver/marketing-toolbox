---
title: Marketing Toolbox
weight: 1
---

# Marketing Toolbox

Marketing Toolbox provides three command-line tools for Google Analytics 4 and Google Tag Manager:

- `ga4datactl` queries the Google Analytics Data API.
- `ga4adminctl` manages the Google Analytics Admin API.
- `gtmctl` manages the Google Tag Manager API.

This guide describes the released 0.5.1 commands. The report-leaf `--schema` flags described in [GA4 Data](tools/ga4-data.md) are available in 0.5.1. Earlier 0.2.0 installations should use the existing `ga4datactl sdk schema --command "reports run"` route instead.

Start with [installation](install.md), then choose an [authentication method](auth/_index.md). A fresh user can discover the installed command tree without a product-specific skill:

```bash
ga4datactl --help
ga4datactl reports --help
ga4datactl reports run --help
```

Use the same root → group → leaf `--help` pattern for `ga4adminctl` and `gtmctl`. Root help also links to authentication and the relevant official API; [tool behavior](tools/_index.md) explains JSON output, schemas, and safety boundaries.

## Choose a command

Use `ga4datactl` for reporting data, `ga4adminctl` for Analytics account and property configuration, and `gtmctl` for Tag Manager accounts, containers, and workspaces. `sdk schema` provides locally installed request descriptors only for eligible leaves; it is not a substitute for leaf help or live resource permissions.

The verified canonical web guides are [project home](https://marketing-toolbox.org/), [authentication](https://marketing-toolbox.org/auth/), [GA4 Data](https://marketing-toolbox.org/tools/ga4-data/), [GA4 Admin](https://marketing-toolbox.org/tools/ga4-admin/), and [Tag Manager](https://marketing-toolbox.org/tools/tag-manager/).
