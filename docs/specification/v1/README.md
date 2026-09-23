# v1 CLI specification

This directory contains the current v1 contracts for the three public CLIs.
The checked-in inventory records the official Google API and Discovery
surfaces used by the pinned dependencies; it is evidence for the catalog, not
an arbitrary API invocation interface.

## Source coverage

| CLI | Official API surface | Pinned client |
| --- | --- | --- |
| `ga4datactl` | Google Analytics Data API v1alpha and v1beta | `google-analytics-data==0.23.0` |
| `ga4adminctl` | Google Analytics Admin API v1alpha and v1beta | `google-analytics-admin==0.30.1` |
| `gtmctl` | Tag Manager API v2 | `google-api-python-client==2.198.0` |

The v1 contract targets non-deprecated methods on the approved API versions.
Alpha-only and deprecated methods are excluded. The
[GA4 Admin catalog](ga4adminctl/catalog.md) and [GTM catalog](gtmctl/catalog.md)
list their current command targets. GA4 Data request contracts are in
[ga4datactl/commands](ga4datactl/commands/), with schemas and fixtures in the
adjacent directories.

The earlier GA4 Admin Audience surface was alpha-only and is excluded from the
public v1 command set. It has no public command path.
