---
title: Marketing Toolbox
weight: 1
---

# Marketing Toolbox

Marketing Toolbox provides three command-line tools for Google Analytics 4 and Google Tag Manager:

- `ga4datactl` queries the Google Analytics Data API.
- `ga4adminctl` manages the Google Analytics Admin API.
- `gtmctl` manages the Google Tag Manager API.

This guide describes the released 0.2.0 commands. Start with [installation](install.md), then choose an [authentication method](auth/_index.md). The [tool guides](tools/_index.md) show representative, credentialed commands without replacing each command's built-in help.

## Choose a command

Use `ga4datactl` for reporting data, `ga4adminctl` for Analytics account and property configuration, and `gtmctl` for Tag Manager accounts, containers, and workspaces. Run `<tool> --help` to discover the current command tree and `sdk schema` for supported request bodies.
