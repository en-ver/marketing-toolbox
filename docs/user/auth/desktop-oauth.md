---
title: Desktop OAuth setup
weight: 10
---

# Desktop OAuth setup

Use a Google Cloud **Desktop app** client for native OAuth. The CLI owns its loopback callback; do not create a Web application or enter redirect URIs.

## Configure a Cloud project

1. [Create or select a Cloud project](https://console.cloud.google.com/projectcreate).
2. In the [API Library](https://console.cloud.google.com/apis/library), enable only the APIs you need:
   - [Google Analytics Data API](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com) for `ga4datactl`.
   - [Google Analytics Admin API](https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com) for `ga4adminctl`.
   - [Tag Manager API](https://console.cloud.google.com/apis/library/tagmanager.googleapis.com) for `gtmctl`.
3. In [Google Auth Platform](https://console.developers.google.com/auth/overview), complete **Branding** with an app name, support email, and contact email.
4. Under **Audience**, choose **External** for a personal project or users outside a Google Workspace organization. Choose **Internal** only for eligible organization-only users. For an External app in **Testing**, add each signing-in account as a test user.
5. Under **Data Access**, add only the scope or scopes for the access tiers you will use. The [authentication guide](./_index.md#credential-precedence) lists the exact tiers and scopes.

External Testing refresh tokens can expire after seven days. Personal testing does not require verification or publishing the app to Production.

## Create and protect the client JSON

In [Google Auth Platform Clients](https://console.developers.google.com/auth/clients), choose **Create client**, select **Desktop app**, name it if prompted, and create it. Download the JSON immediately. Do not enter a redirect URI.

Treat the full downloaded client secret as sensitive and effectively one-time: Google may only show its final characters after creation. Store it securely until needed and do not put it in a repository.

## Log in

Start with the smallest tier for one tool:

```bash
ga4datactl auth login \
  --client-secrets ~/Downloads/client_secret.json \
  --access read
ga4datactl auth status --access read
```

The browser opens Google's consent flow. Approve a macOS Keychain prompt only when you initiated the command and recognize the tool. The same Desktop JSON can be used for all three tools, but every tool and access tier needs its own local login record.

After `auth status` succeeds, it is safe to delete the downloaded JSON for that existing record because the keyring retains the refresh material, client ID, client secret, and scope binding. Keep a secure copy, or create a new client secret when necessary, for another tool, tier, machine, reauthentication, or recovery.

## Deletion and revocation are different

- Deleting the local downloaded JSON does not change an existing keyring record or Google grant.
- `auth forget` deletes the selected local record only.
- `auth revoke --apply --acknowledge-project-wide-revocation` revokes the user's grant across the OAuth project, then removes the selected local record only when its serialized value is unchanged. A concurrent replacement is preserved and reported for local cleanup review.
- Deleting the Cloud OAuth client can invalidate records using that client and is not a logout mechanism.

## SSH or another remote browser

Forward a fixed loopback port before logging in on the remote host:

```bash
ssh -L 127.0.0.1:8765:127.0.0.1:8765 -o ExitOnForwardFailure=yes user@server
ga4datactl auth login --client-secrets /secure/client_secret.json --access read \
  --no-open-browser --port 8765
```

The login prints its loopback URL to standard error; it does not use a copy-and-paste authorization code or public listener. If the remote host has no approved keyring, use externally managed ADC instead.

See Google's [OAuth consent guidance](https://developers.google.com/workspace/guides/configure-oauth-consent), [native-app flow](https://developers.google.com/identity/protocols/oauth2/native-app), and [OAuth client management](https://support.google.com/cloud/answer/15549257) for Cloud-side details.
