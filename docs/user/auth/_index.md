---
title: Authentication
weight: 20
---

# Authentication

Commands select credentials in this order:

1. `GOOGLE_SERVICE_ACCOUNT_JSON`, containing a service-account JSON document.
2. An explicitly set `GOOGLE_APPLICATION_CREDENTIALS` file.
3. A matching local native OAuth record for the current tool and access tier.
4. Ambient [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/application-default-credentials).

The explicit file and ambient ADC can represent any Google-supported credential type, including service accounts, user credentials, workload identity, or an attached identity. A configured environment source or marked native record fails closed if it is invalid; the command does not silently choose a different identity. To skip an environment source, leave its variable unset: an explicitly set empty value is invalid at that source and does not fall through to a lower-priority identity.

## Credential precedence

Choose native OAuth for an interactive desktop user, or use operator-managed service accounts and ADC for automation. Native OAuth records are separate records for each **tool + access-tier** pair: a `gtmctl` `containers` record is not a `gtmctl` `versions` record, nor a record for either GA4 tool.

OAuth consent and credential selection only determine which identity and OAuth scope the CLI presents. They do not grant access to Analytics properties or Tag Manager resources. Grant that authenticated principal the required Google Analytics, Tag Manager, and IAM resource permissions separately.

The legal native OAuth tiers and their scopes are:

| Tool | Access tier | Scope |
| --- | --- | --- |
| `ga4datactl` | `read` | `https://www.googleapis.com/auth/analytics.readonly` |
| `ga4adminctl` | `read` | `https://www.googleapis.com/auth/analytics.readonly` |
| `ga4adminctl` | `edit` | `https://www.googleapis.com/auth/analytics.edit` |
| `gtmctl` | `read` | `https://www.googleapis.com/auth/tagmanager.readonly` |
| `gtmctl` | `users` | `https://www.googleapis.com/auth/tagmanager.manage.users` |
| `gtmctl` | `accounts` | `https://www.googleapis.com/auth/tagmanager.manage.accounts` |
| `gtmctl` | `containers` | `https://www.googleapis.com/auth/tagmanager.edit.containers` |
| `gtmctl` | `versions` | `https://www.googleapis.com/auth/tagmanager.edit.containerversions` |
| `gtmctl` | `publish` | `https://www.googleapis.com/auth/tagmanager.publish` |
| `gtmctl` | `delete` | `https://www.googleapis.com/auth/tagmanager.delete.containers` |

Use `<tool> auth --help` to see the installed tool's legal `--access` values. Choose a tier from the operation mapping in the relevant [tool guide](../tools/_index.md), not from a simple read/write/delete assumption.

## Native OAuth storage

Native OAuth stores refresh material, client ID, client secret, and the selected scope binding only in an approved encrypted OS keyring: macOS Keychain, Windows Credential Locker, or Linux Secret Service. There is no plaintext fallback. Access tokens are refreshed only in memory, and the stored scope is not proof of a scope Google still grants.

Headless Linux commonly has no approved keyring; use externally managed ADC there. ADC files, including gcloud-managed credentials, are outside the CLI's native encrypted-keyring guarantee and must be secured by the operator. On Windows, a native record is limited by Credential Locker's 2,560-byte UTF-16LE value limit.

Before changing a native record, the CLI writes a non-secret local marker. A missing or invalid marked record does not fall through to ADC. Recover incomplete or interrupted local storage with `auth forget`, then log in again.

All native marker/keyring lifecycle operations coordinate through one persistent,
non-secret lock per OS user and shared OAuth service. The lock uses the canonical
OS profile location, while marker roots remain configurable; changing a marker
root does not create a different lock. Lock acquisition waits at most five
seconds for thread or cross-process contention only, not for profile lookup,
filesystem work, keyring calls, refresh, browser interaction, or network work.
A safely absent selected marker returns absent without creating the lock file or
looking up a keyring secret. An unsafe or unwritable canonical profile fails
closed instead of falling back to environment-selected profile paths. The lock
is cooperative: older or noncooperating binaries are not coordinated.

## Record lifecycle

Use the selected tool and tier for each command:

```bash
ga4datactl auth status --access read
ga4datactl auth forget --access read
ga4datactl auth revoke --access read --apply --acknowledge-project-wide-revocation
```

`auth status` checks the selected local record without contacting Google; a
present record can create the persistent non-secret coordination file on first
use. `auth forget` deletes only that local record; it does not revoke Google
access. `auth revoke` revokes the user's grant across the OAuth project and then
removes the selected local record only when it is unchanged. If another process
replaces it while remote revocation is in flight, the replacement is retained
and the command reports that local cleanup needs review. It is not a tier-local
remote logout. Alternatively, revoke the grant in Google Account permissions and
run `auth forget` locally.

For an interactive login, follow [Desktop OAuth setup](desktop-oauth.md).
