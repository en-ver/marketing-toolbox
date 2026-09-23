# marketing-tools

`marketing-tools` provides three command-line interfaces for the official Google
APIs:

- `ga4datactl` — Google Analytics Data API v1
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

## Specification

The current public contracts, catalogs, schemas, and deterministic fixtures are
indexed from [docs/specification/README.md](docs/specification/README.md).
[SDK-backed introspection](docs/specification/v1/sdk-backed-introspection.md)
describes the local descriptor command and its current behavior.
