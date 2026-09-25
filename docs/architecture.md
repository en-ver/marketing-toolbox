# Architecture

## Technology

The project targets Python 3.11+. Typer and Click define command trees and
parse options. The GA4 Data and Admin tools use `google-analytics-data` and
`google-analytics-admin` for their v1beta APIs; GTM uses
`google-api-python-client` and its Discovery model for the Tag Manager v2 API.
`google-auth` provides the common Google credential interfaces.

`jsonschema` validates selected GA4 Data request bodies. `sdk schema` derives
GA4 schemas from protobuf descriptors and GTM schemas from the bundled
Discovery document. `google-auth` resolves service accounts, native user OAuth,
and ADC; `google-auth-oauthlib` implements the native Desktop loopback flow.
uv manages the workspace and dependencies; Hatchling builds the distributions.
Exact versions belong in `pyproject.toml` and `uv.lock`.

## Component boundaries

Each tool's `src/<tool>/cli.py` assembles its application. Its `commands/`
package declares Typer commands, maps CLI input, and applies intent and
acknowledgement gates. `foundation/` owns local validation, body handling, and
normalized errors; the GA4 tools also keep request serialization there.
`operations/` chooses credential scopes and calls the official Google clients.
`marketing_common.auth.resolve_credentials` selects inline service accounts,
explicit `GOOGLE_APPLICATION_CREDENTIALS`, marked native OAuth, then ambient
ADC, fail-closed at each selected source. Native `auth login|status|forget|revoke`
commands are shared by all tools: users supply their own Desktop client JSON,
records retain only refresh material and the selected scope binding in approved
OS keyrings, with access tokens refreshed only in memory; that local scope
binding is not proof of a remotely granted scope. A non-secret secure marker is
written before keyring mutation and prevents unintended ADC fallback; a marked
missing or invalid secret is recovered with `forget`, not by ADC fallback.
Ordinary storage failures are best-effort compensated, while interruption during
a replacement can retain either valid record. On POSIX the marker path's
app-owned directories are non-symlinked, user-owned, and non-group/other-writable;
marker writes re-sync configured-base and application directory entries before
marker or keyring mutation, then syncs marker data and its containing directory;
deletion syncs that directory. The ancestor walk accepts protected platform
redirects but does not claim protection from hostile filesystems or extended
ACLs. Windows rejects reparse points below the application base and uses
inherited profile ACLs plus flushed write-through replacement; its native ACL and first-use directory
semantics require Windows validation and do not promise universal power-loss
durability. Headless systems without an approved keyring use externally managed
ADC; `forget` is local-only, verifies secret absence before marker removal, and
does not determine remote grant validity, while `revoke` requires acknowledgement
because its grant is project-wide. Resource access is still controlled separately
by Analytics, Tag Manager, and IAM permissions.

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
