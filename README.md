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

Commands resolve credentials in this order: `GOOGLE_SERVICE_ACCOUNT_JSON`, an
explicit `GOOGLE_APPLICATION_CREDENTIALS` file, a matching local native OAuth
record, then ambient [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials).
The explicit file and ambient ADC may be service-account, user, workload, or
other Google-supported credential types. This preserves service-account
compatibility and supports externally managed ADC on servers and CI (for
example, attached identity, workload identity, or a provisioned ADC file).
Credentials are never command-line arguments or output.

### Native user OAuth

Follow Google's guidance to [create a Cloud project](https://developers.google.com/workspace/guides/create-project),
[enable APIs](https://developers.google.com/workspace/guides/enable-apis),
[configure OAuth consent and test users](https://developers.google.com/workspace/guides/configure-oauth-consent),
and [create a Desktop OAuth client and download its JSON](https://support.google.com/cloud/answer/15549257).
For an External project in **Testing**,
add the signing-in user as a test user when applicable. Each native record
requests exactly one access tier:

| Tool | Access tiers |
| --- | --- |
| `ga4datactl` | `read` |
| `ga4adminctl` | `read`, `edit` |
| `gtmctl` | `read`, `users`, `accounts`, `containers`, `versions`, `publish`, `delete` |

For a desktop login, run (replace the tool and tier as needed):

```bash
ga4datactl auth login --client-secrets ~/Downloads/client_secret.json --access read
```

The same command family manages the record:

```bash
ga4datactl auth status --access read
ga4datactl auth forget --access read
ga4datactl auth revoke --access read --apply --acknowledge-project-wide-revocation
```

`forget` deletes only that local record. It does not attempt remote revocation
and cannot determine whether the Google grant remains valid. It verifies secure
storage deletion before removing its recovery marker; if cleanup is incomplete,
rerun `forget` after fixing local storage. `revoke` revokes the user's grant
across the OAuth project, then removes the selected local record; it is not a
per-tier remote logout. You can instead revoke access in Google Account
permissions and run `forget`.

Native records retain only the refresh material and the selected access-tier
scope binding in an approved encrypted OS keyring (macOS Keychain, Windows
Credential Locker, or Linux Secret Service); access tokens are refreshed only
in memory. The stored scope is not proof of the scope Google granted. Native
records are unavailable when that secure keyring is unavailable—common on headless
Linux—so use externally managed ADC instead; this tool never falls back to
plaintext files. On Windows, a native record is limited to Credential Locker's
2,560-byte UTF-16LE value limit. Externally managed ADC (including
gcloud-managed files) is outside this native encrypted-keyring guarantee and
must be secured by the operator. An external consent screen left in **Testing**
can issue refresh tokens that expire after seven days.

Before changing a native record, the tool durably writes a non-secret marker in
its private application directory. An interrupted login can therefore leave a
marked missing or invalid secret; it will fail closed rather than select ADC.
Run `auth forget` to recover, then log in again. Ordinary storage failures are
best-effort compensated, but abrupt interruption during a replacement can leave
either the previous or new valid secret. On POSIX, each storage attempt
re-syncs configured-base and application directory entries before marker or
keyring mutation, then syncs marker data and its containing directory. Windows
uses flushed temporary data and a
write-through replacement under the OS profile's inherited ACLs; neither
platform promise covers every filesystem, redirect, storage device, or power
loss scenario.

For a remote browser over SSH, forward one fixed loopback port before logging
in on the server:

```bash
ssh -L 127.0.0.1:8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes user@server
ga4datactl auth login --client-secrets /secure/client_secret.json --access read \
  --no-open-browser --port 8765
```

The login prints its loopback URL to stderr; no copy/paste authorization-code
or public listener is used. If native secure storage is unavailable, bootstrap
ADC with your owned client instead:

```bash
gcloud auth application-default login --client-id-file=/secure/client_secret.json \
  --scopes="https://www.googleapis.com/auth/analytics.readonly" --no-browser
```

Shared ADC must include the union of scopes required by every tool and access
tier it serves. Consent and credential selection do not grant access to
Analytics or Tag Manager resources. Grant the authenticated principal the
required Google Analytics, Tag Manager, and IAM resource permissions separately.

## Discover commands and schemas

Use `<tool> --help` for the current commands and options. `sdk schema --command
"<eligible leaf path>"` prints the locally derived request schema without
loading credentials or calling Google.

Reads execute normally. Writes require `--apply`; supported dry runs do not
call mutation endpoints. Sensitive or high-impact commands can require an
additional acknowledgement. API, schema, and version results use structured
JSON on stdout; diagnostics use stderr, while `--help` uses normal help text.
