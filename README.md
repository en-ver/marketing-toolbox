# marketing-toolbox

`marketing-toolbox` provides three command-line interfaces for the official Google
APIs:

- `ga4datactl` — Google Analytics Data API v1beta
- `ga4adminctl` — Google Analytics Admin API v1beta
- `gtmctl` — Google Tag Manager API v2

The tools provide explicit commands, structured JSON output, normalized errors,
and safety controls for non-interactive automation. They use the official
Google Python clients for authentication, transport, retries, and API models.

## Quick start

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --all-groups
uv run ga4datactl --help
uv run ga4adminctl --help
uv run gtmctl --help
uv run pytest
uv run ruff check .
```

The installed entry points are `ga4datactl`, `ga4adminctl`, and `gtmctl`.

## Published installation (after the first release)

After the first release has been configured and published to all four PyPI
projects, the three command-specific distributions can be run without a
persistent installation with [`uvx`](https://docs.astral.sh/uv/guides/tools/):

```bash
uvx ga4datactl --help
uvx ga4adminctl --help
uvx gtmctl --help
```

After publication, pin a release when reproducibility matters. The package
named with `--from` is the distribution to resolve, and the following argument
is its executable:

```bash
uvx --from ga4datactl==0.1.0 ga4datactl --help
uvx --from ga4adminctl==0.1.0 ga4adminctl --help
uvx --from gtmctl==0.1.0 gtmctl --help
```

For a published distribution, `uvx` caches its isolated tool environment. An
unpinned invocation can be refreshed to pick up a newer published release; use
`--refresh` when you need to re-resolve and reinstall the tool:

```bash
uvx --refresh ga4datactl --help
```

A version-pinned invocation remains on that version, even when refreshed:

```bash
uvx --refresh --from ga4datactl==0.1.0 ga4datactl --help
```

Each command-specific distribution is a thin launcher distribution. It exposes
one command and pins the corresponding `marketing-toolbox` release; the
`marketing-toolbox` distribution contains the shared implementation and all three
entry points. This gives each CLI a discoverable PyPI name while keeping the
implementation in one distribution.

## Command map

```text
ga4datactl
  reports (run, batch-run, pivot-run, batch-pivot-run, realtime-run, compatibility-check)
  metadata get
  audience-exports (get, list, create, query)
  sdk schema --command "<eligible leaf path>"

ga4adminctl
  account-summaries list
  accounts (...)
  properties (...)
  sdk schema --command "<eligible leaf path>"

gtmctl
  accounts (...)
  sdk schema --command "<eligible body leaf path>"
```

Use `--help` for the executable command set. The complete current target maps
are the [GA4 Admin catalog](docs/specification/v1/ga4adminctl/catalog.md) and
[GTM catalog](docs/specification/v1/gtmctl/catalog.md). The
[GA4 Data command contracts](docs/specification/v1/ga4datactl/commands/) cover
its public request and safety boundaries.

`sdk schema` reads the pinned local SDK or Discovery descriptor. It does not
load credentials or call Google.

## Authentication

Commands that call Google use a service account supplied at process runtime by
one of these environment variables, in precedence order:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
GOOGLE_APPLICATION_CREDENTIALS
```

The first contains the complete service-account JSON document and is parsed in
memory. The second names a service-account JSON file. Credentials are never
accepted as command-line arguments or written to output. Interactive OAuth,
user credentials, and application-default user credentials are not supported.
See [docs/authentication.md](docs/authentication.md).

## Output and safety

Successful commands write one versioned JSON document to stdout. Diagnostics
and warnings go to stderr. Read operations run normally; Google-side writes
require `--apply`, and `--dry-run` validates and plans without making the
mutation request. Command-specific acknowledgements remain required for
high-impact operations and sensitive reads.

`--apply` expresses caller intent; Google IAM, the invoking caller's execution
policy, and any required human approval remain the authorization boundary. See
the [CLI contract](docs/cli-contract.md) for output, errors, exit codes, and
mutation behavior.

## Installation

From a checkout, install the package with:

```bash
uv tool install .
```

This installs all three entry points into uv's managed executable directory.
Ensure that directory is on `PATH`. For repository development, use `uv sync`
and invoke commands with `uv run`.

After the first release has been configured and published, the root
distribution will also be available as a compatibility path. For example, this
runs the root distribution's `ga4datactl` entry point:

```bash
uvx --from marketing-toolbox ga4datactl --help
uvx --from marketing-toolbox ga4adminctl --help
uvx --from marketing-toolbox gtmctl --help
```

The pinned form is `uvx --from marketing-toolbox==0.1.0 ga4datactl --help`, for
example. For new installs from PyPI after publication, prefer the
command-specific paths above.

## Specification

The current public contracts, catalogs, schemas, and deterministic fixtures are
indexed from [docs/specification/README.md](docs/specification/README.md).
[SDK-backed introspection](docs/specification/v1/sdk-backed-introspection.md)
describes the local descriptor command and its current behavior.
