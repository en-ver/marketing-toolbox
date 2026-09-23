# CLI specification

This directory indexes the current public interfaces of `ga4datactl`,
`ga4adminctl`, and `gtmctl`. The executable `--help` output remains the
authority for installed command discovery; these documents define the stable
request, response, safety, and provenance contracts.

## v1 contract set

- [v1 overview](v1/README.md)
- [requirements](v1/requirements.md)
- [GA4 Admin catalog](v1/ga4adminctl/catalog.md)
- [GTM catalog](v1/gtmctl/catalog.md)
- [GTM command contracts](v1/gtmctl/command-contracts.md)
- [SDK-backed introspection](v1/sdk-backed-introspection.md)
- [GA4 Data command contracts](v1/ga4datactl/commands/)
- [GA4 Data schemas](v1/ga4datactl/schemas/)
- [GA4 Data fixtures](v1/ga4datactl/fixtures/)

The catalogs and command contracts are derived from the corresponding official
Google API and SDK surfaces. They define the public CLI boundary; implementation
must conform to them without adding arbitrary API dispatch.
