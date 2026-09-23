# Service-account authentication

All three CLIs authenticate as a Google service account. Supply the credential only at process runtime using one of these mechanisms, in precedence order:

```text
GOOGLE_SERVICE_ACCOUNT_JSON
GOOGLE_APPLICATION_CREDENTIALS
```

`GOOGLE_SERVICE_ACCOUNT_JSON` contains the complete service-account JSON document and is parsed in memory. `GOOGLE_APPLICATION_CREDENTIALS` names a readable service-account JSON file managed by the runtime. Neither representation may be committed, printed, passed as a command-line flag, or copied into request/output files.

## Credential loading

The shared `marketing_common.auth.service_account_credentials()` loader prefers the in-memory JSON secret and otherwise loads the declared service-account file, then creates scoped `google-auth` credentials. It does not discover user credentials, start a browser OAuth flow, or fall back to a developer's local Google login.

Missing or invalid credentials return a sanitized configuration error that names only the credential environment-variable key, never any secret content or file contents.

## Per-command-family scopes

Each live command scopes its credentials for its own operation. Help, `--version`, dry-run planning, and `sdk schema` do not load credentials. The following is the runtime selection, not a recommendation to grant every scope to every service account.

| CLI | Command family | Requested OAuth scope |
|---|---|---|
| `ga4datactl` | Reports, metadata, and audience-export `get`, `list`, and sensitive `query` | `https://www.googleapis.com/auth/analytics.readonly` |
| `ga4datactl` | `audience-exports create` | `https://www.googleapis.com/auth/analytics` |
| `ga4adminctl` | Ordinary reads | `https://www.googleapis.com/auth/analytics.readonly` |
| `ga4adminctl` | Mutations, sensitive actions, and account change-history search | `https://www.googleapis.com/auth/analytics.edit` |
| `gtmctl` | Ordinary GTM reads | `https://www.googleapis.com/auth/tagmanager.readonly` |
| `gtmctl` | Account user-permission reads and mutations | `https://www.googleapis.com/auth/tagmanager.manage.users` |
| `gtmctl` | `accounts update` | `https://www.googleapis.com/auth/tagmanager.manage.accounts` |
| `gtmctl` | Ordinary container/workspace/entity mutations | `https://www.googleapis.com/auth/tagmanager.edit.containers` |
| `gtmctl` | Container-version `update`, `delete`, and `undelete`; workspace `create-version` and `quick-preview` | `https://www.googleapis.com/auth/tagmanager.edit.containerversions` |
| `gtmctl` | Container-version `publish` and environment `reauthorize` | `https://www.googleapis.com/auth/tagmanager.publish` |
| `gtmctl` | Container and workspace deletion | `https://www.googleapis.com/auth/tagmanager.delete.containers` |

The [GTM catalog](specification/v1/gtmctl/catalog.md) records the exact scope allowed for each official target; the runtime families above identify the scope this CLI currently requests. Scopes constrain the token request, but Google Analytics and GTM IAM roles remain the ultimate authorization boundary. Configure each service account with only the Google-side permissions required for its intended commands.

## Runtime requirements

- The process launcher must inject `GOOGLE_SERVICE_ACCOUNT_JSON` or securely provide the service-account file named by `GOOGLE_APPLICATION_CREDENTIALS`.
- Local tests and help/version commands do not require credentials.
- SDK-backed API commands fail before making a Google request if neither credential source is available or the supplied credential is invalid.
- Do not use interactive OAuth, application-default user credentials, or `.env` files for these tools.
