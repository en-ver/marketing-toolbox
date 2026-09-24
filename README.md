# marketing-toolbox

Command-line tools for the official Google APIs:

- `ga4datactl` — Google Analytics Data API v1beta
- `ga4adminctl` — Google Analytics Admin API v1beta
- `gtmctl` — Google Tag Manager API v2

They require Python 3.11+ and [uv](https://docs.astral.sh/uv/).

## Install and run

Run a tool without installing it persistently:

```bash
uvx ga4datactl --help
uvx ga4adminctl --help
uvx gtmctl --help
```

Or install individual tools:

```bash
uv tool install ga4datactl
uv tool install ga4adminctl
uv tool install gtmctl
```

To install all three commands together:

```bash
uv tool install marketing-toolbox
```

`marketing-toolbox` provides `ga4datactl`, `ga4adminctl`, and `gtmctl`; it does
not provide a `marketing-toolbox` executable.

## Authentication

Commands that call Google support service accounts only. Provide credentials at
runtime in this precedence order:

1. `GOOGLE_SERVICE_ACCOUNT_JSON` — the complete service-account JSON document.
2. `GOOGLE_APPLICATION_CREDENTIALS` — a path to a service-account JSON file.

Credentials are never accepted as command-line flags or emitted in output.
Google IAM remains the authorization boundary. Interactive OAuth, user
credentials, and application-default user credentials are unsupported.

## Discover commands and schemas

Use `<tool> --help` for the current commands and options. `sdk schema --command
"<eligible leaf path>"` prints the locally derived request schema without
loading credentials or calling Google.

Reads execute normally. Writes require `--apply`; supported dry runs do not
call mutation endpoints. Sensitive or high-impact commands can require an
additional acknowledgement. API, schema, and version results use structured
JSON on stdout; diagnostics use stderr, while `--help` uses normal help text.
