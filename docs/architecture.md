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
`marketing_common.oauth.SCOPE_CATALOG` is the sole owner of exact OAuth scope
URLs. Each tool privately owns an `operations/transport.py` module that maps
its access tiers through `scope_for_access()` and constructs its credentials and
SDK client or Discovery service. Leaf operation modules retain request
construction, local validation, dry-run planning, and response serialization.
The Admin transport is the neutral owner of `read`, `list_page`, and `write`
dispatch: it uses `retry=None` with a 20-second timeout, and its explicit
uncertain-create method set selects the post-dispatch ambiguity diagnostic.
`marketing_common.auth.resolve_credentials` selects inline service accounts,
explicit `GOOGLE_APPLICATION_CREDENTIALS`, marked native OAuth, then ambient
ADC, fail-closed at each selected source. Native `auth login|status|forget|revoke`
commands are shared by all tools: users supply their own Desktop client JSON,
records retain only refresh material and the selected scope binding in approved
OS keyrings, with access tokens refreshed only in memory; that local scope
binding is not proof of a remotely granted scope. A non-secret secure marker is
written before keyring mutation and prevents unintended ADC fallback; a marked
missing or invalid secret is recovered with `forget`, not by ADC fallback. All
native lifecycle transactions use one persistent, non-secret lock per OS user
and OAuth service. Its canonical OS-profile path is independent of configurable
marker roots, so tools and tiers coordinate even when their marker roots differ.
An absent selected marker is a safe no-lock, no-keyring result; observed markers
are rechecked under the lock. The shared five-second budget covers only thread
and OS-lock acquisition, not filesystem, keyring, refresh, browser, or network
work. Unsafe or unwritable canonical profiles fail closed rather than falling
back. Ordinary storage failures are best-effort compensated, while interruption
during a replacement can retain either valid record. On POSIX the lock's
app-owned hierarchy is private, non-symlinked, and owner-controlled, and its
persistent file is a single-link mode-0600 regular file; the protected lexical
and resolved ancestor walk accepts platform redirects. Marker writes re-sync
configured-base and application directory entries before marker or keyring
mutation, then syncs marker data and its containing directory; deletion syncs
that directory. Windows rejects reparse points below its OS-profile anchor and
uses inherited profile ACLs plus flushed write-through replacement; its native
ACL and first-use directory semantics require Windows validation and do not
promise universal power-loss durability. The lock is advisory for upgraded
cooperating binaries only. Headless systems without an approved keyring use
externally managed ADC; `forget` is local-only, verifies secret absence before
marker removal, and does not determine remote grant validity, while `revoke`
requires acknowledgement because its grant is project-wide and conditionally
cleans up only an unchanged local record after remote success. Resource access
is still controlled separately by Analytics, Tag Manager, and IAM permissions.

The supported surface is the latest installed CLI: its help output and documented
JSON contracts. `cli.py` composes command groups; commands call their canonical
operation owners directly, and operations use foundation and shared helpers. GTM
intentionally retains distinct read and mutation transport implementations: reads use
Discovery's default `httplib2` transport, while mutations use a GTM-owned Requests
adapter through Discovery's public `http=` seam, with at most one GTM API dispatch, redirects
disabled, and a 60-second connect/read timeout. Credential refresh may make separately
retried pre-API HTTP requests. The adapter preserves the selected credential
for Discovery universe checks and blocks `.netrc` from replacing its Bearer header
without disabling environment proxy or CA settings. Mutation mTLS accepts only
standard-endpoint `auto` or `never`; reads retain Discovery's existing mTLS behavior.
`marketing_common/` holds shared authentication, JSON presentation, command,
Discovery, and introspection facilities. `marketing_common.cli` owns shared CLI
presentation. `ga4datactl/schemas.py` owns the runtime GA4 Data validation schemas.

Four local validation and response boundaries apply:

- GTM resource identifiers reject URI delimiters, percent encodings, backslashes,
  dot segments, whitespace, controls, and lone surrogates before credentials;
  safe opaque identifiers are preserved without rewriting.
- GTM mutation response decoding is uncertain completion only after confirmed
  2xx receipt; unreadable or nonobject returned responses use the same sanitized
  diagnostic. Predispatch failures retain their policy, with no replay or retry.
- Admin change-history `pageSize` and `page_size`, when present, use the parsed
  protobuf value and require 1–200 before credentials. Omission retains default
  zero; null and both-alias input order follow the official parser.
- GA4 Data schema traversal exhaustion is a sanitized invalid request before
  credentials, not a fixed-depth contract. Intake, ordinary schema errors, and
  protobuf conversion retain their existing boundaries.

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
