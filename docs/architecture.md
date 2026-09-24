# Architecture

## Technology

The project targets Python 3.11+. Typer and Click define command trees and
parse options. The GA4 Data and Admin tools use `google-analytics-data` and
`google-analytics-admin` for their v1beta APIs; GTM uses
`google-api-python-client` and its Discovery model for the Tag Manager v2 API.
`google-auth` loads service-account credentials.

`jsonschema` validates selected GA4 Data request bodies. `sdk schema` derives
GA4 schemas from protobuf descriptors and GTM schemas from the bundled
Discovery document. uv manages the workspace and dependencies; Hatchling builds
the distributions. Exact versions belong in `pyproject.toml` and `uv.lock`.

## Component boundaries

Each tool's `src/<tool>/cli.py` assembles its application. Its `commands/`
package declares Typer commands, maps CLI input, and applies intent and
acknowledgement gates. `foundation/` owns local validation, body handling, and
normalized errors; the GA4 tools also keep request serialization there.
`operations/` chooses credential scopes and calls the official Google clients.

`ga4datactl/service.py` and `ga4adminctl/service.py` are compatibility facades
for their existing APIs. GTM has no corresponding service facade.
`marketing_common/` holds shared authentication, JSON presentation, command,
Discovery, and introspection facilities. `marketing_toolbox/cli.py` provides
compatibility exports for shared CLI presentation. `ga4datactl/schemas.py` owns
the runtime GA4 Data validation schemas.

```text
Typer command
  -> local validation and safety gates
  -> operation adapter
  -> official Google client
  -> normalized JSON result/error
```

## Distribution layout

`marketing-toolbox` contains the implementation and exposes all three scripts.
`ga4datactl`, `ga4adminctl`, and `gtmctl` are thin launcher distributions: each
exposes only its matching script and depends on the exactly matching,
synchronized `marketing-toolbox` version. The uv workspace includes
`packaging/*`.

A release builds four wheels and four source distributions. GitHub Actions
publishes through PyPI Trusted Publishing in the protected `pypi` environment.
