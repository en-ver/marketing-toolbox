# Agent-oriented CLI contract

Applies to `ga4datactl`, `ga4adminctl`, and `gtmctl`.

## Scope

The commands are intended for non-interactive agent automation. Each CLI wraps one official Google Python client surface; it does not reimplement Google authentication, transports, retries, or resource schemas.

## Commands

- Commands are explicit. The v1 public target covers every non-deprecated method on an approved upstream API version; alpha and deprecated methods are excluded as defined in `docs/specification/v1/requirements.md`.
- A generic arbitrary-method invocation command is out of scope.
- Plugin loading and dynamically generated commands are out of scope.
- Every command must offer deterministic `--help` output.

## Input and output

- Successful commands write one JSON document to stdout with `schemaVersion` set to `marketing-tools/v1`, plus `command` and `data`.
- Diagnostics, warnings, retry notices, and debug output go only to stderr.
- Errors, including CLI parsing errors generated before a command handler runs, write one JSON diagnostic document to stderr. The diagnostic has `schemaVersion` set to `marketing-tools/v1`, plus `command`, `exitCode`, `category`, and a safe human-readable `message`; it includes `googleStatus` only when an API HTTP status is available. Upstream diagnostic text and payloads are not public CLI output.
- `--raw` may return one documented scalar for composition; it must not be the default.
- Commands that stream or enumerate a large collection may offer `--format jsonl`; every line must be a complete JSON object.
- Complex request bodies are accepted through a JSON file argument or stdin rather than an expanding set of opaque flags.

## Exit status

| Code | Meaning | Retry guidance |
|---:|---|---|
| 0 | success | not applicable |
| 2 | invalid arguments or request body | do not retry unchanged |
| 3 | resource not found | do not retry unchanged |
| 4 | authentication or authorization failure | obtain valid authorization |
| 5 | conflict or failed state assertion | refresh state and re-plan |
| 6 | retryable Google API or network failure | retry with bounded backoff |
| 1 | unexpected failure | inspect structured error and diagnostics |

## Mutation controls

- Read operations execute without a confirmation flag.
- Every Google-side write requires an explicit `--apply` flag. It is a command-level intent guardrail, not authorization.
- `--dry-run` plans and validates the request without calling the Google mutation endpoint.
- Destructive and publication operations retain their explicit acknowledgements. Optional upstream resource/version fingerprints are validated and forwarded only when supplied; they are not local safety gates.
- High-impact GTM actions require their documented operation-specific acknowledgement in addition to `--apply`; the acknowledgement is checked locally before credentials are loaded.
- Real authorization remains outside the CLI: Google IAM plus the invoking caller's execution policy and explicit human approval before production changes.

A bare `--apply` is intentionally not described as a user-confirmation system: an autonomous agent can supply it. If stronger approval is needed later, add an upstream approval service that issues a short-lived, signed token bound to the exact operation, target, and payload fingerprint.

## Sensitive user-row reads

Commands that return user-row data require an explicit command-specific acknowledgement flag. They return only the one bounded page requested by the caller and do not paginate, log, persist, redact, or transform the returned data.
