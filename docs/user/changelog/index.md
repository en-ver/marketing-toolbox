---
title: Changelog
---

# Changelog

All four distributions share versions (lockstep releases).
`marketing-toolbox` contains the three commands and their shared implementation.
The launcher packages, `ga4datactl`, `ga4adminctl`, and `gtmctl`, do not have separate release histories.
A tool heading identifies that launcher and `marketing-toolbox`. Shared changes affect all three tools unless the text names a smaller set.
`marketing_common` is shared implementation, not a fifth distribution.

These retrospective notes were reconstructed from source, documentation, and test assertions.
Original release notes, PyPI publication dates, and historical test results were not verified.
Tag dates are not publication dates.

## 0.6.0 {#release-0-6-0}

2026-10-07 (tag date, not a verified publication date)

Request validation and GTM response handling changed. This release includes breaking changes.

### Before upgrading

#### ga4datactl

<!-- change-id: 0-6-0-data-nesting -->
- Breaking: Reduce request nesting and handle `invalid_request` instead of an unexpected exception. GA4 Data now reports a schema traversal `RecursionError` as a validation error before authentication. Schema traversal means walking the request's validation rules. No numeric nesting limit is specified.

#### ga4adminctl

<!-- change-id: 0-6-0-admin-page-size -->
- Breaking: For change-history searches, set `pageSize` or `page_size` to 1–200, or omit it to keep the existing default. Invalid values are rejected before authentication.

#### gtmctl

<!-- change-id: 0-6-0-gtm-identifiers -->
- Breaking: Supply canonical, unescaped resource IDs. GTM paths reject dot components, URL delimiters, whitespace, control characters, and surrogates (special Unicode code points). Safe opaque identifiers remain accepted. Do not encode malformed path components to bypass validation.

<!-- change-id: 0-6-0-gtm-responses -->
- Breaking: Inspect GTM state before retrying a mutation (an operation that changes data) with an unreadable response. After evidence of a successful HTTP response, unreadable responses report uncertain completion with exit code `1` and category `unexpected`. Empty responses still become `{}`.

Compatibility of third-party imports from private Python modules is not established. Removal of internal facades does not establish removal of a CLI command.

Historical runtime validation is unverified. An incomplete-validation message at an intermediate commit does not establish the final tag's test results.

[Tag v0.6.0](https://github.com/en-ver/marketing-toolbox/tree/v0.6.0) · [GitHub Release v0.6.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.6.0) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-6-0)

## 0.5.1 {#release-0-5-1}

2026-10-01 (tag date, not a verified publication date)

This release changes OAuth storage and validation messages. Compatibility review is incomplete. Migration impact for existing custom profiles remains uncertain.

### Before upgrading

#### Shared changes

<!-- change-id: 0-5-1-oauth-lock -->
- Potential breaking change: Make sure that your canonical operating-system profile permits a private, writable lock path for native OAuth storage. All three tools share a per-user lock. Cooperating operations share a five-second budget for waiting on that lock, not a deadline for the whole command. Older or noncooperating binaries do not share this protection.

#### ga4datactl

<!-- change-id: 0-5-1-data-diagnostics -->
- Potential breaking change: Use structured error categories and exit codes instead of parsing diagnostic prose or echoed request values. GA4 Data validation uses controlled messages instead of raw schema errors, request-data paths, or custom pivot dimension names.

#### ga4adminctl

<!-- change-id: 0-5-1-admin-diagnostics -->
- Potential breaking change: Use structured error categories and exit codes instead of parsing SDK diagnostic prose. The SDK is the library that calls the API. GA4 Admin sanitizes protobuf parser diagnostics for request bodies, access reports, and change history.

The diagnostic text changed, but a strict public guarantee for that text is not established.

### Other changes

#### Shared changes

<!-- change-id: 0-5-1-oauth-replacement -->
- OAuth revocation preserves a local record replaced during the remote request and reports that review is required.

The final commit changes a Windows test fixture, not shipped OAuth behavior. Native Windows runtime results are unverified.

[Tag v0.5.1](https://github.com/en-ver/marketing-toolbox/tree/v0.5.1) · [GitHub Release v0.5.1](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.5.1) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-5-1)

## 0.5.0 {#release-0-5-0}

2026-10-01 (tag date, not a verified publication date)

This release changes GTM commands and mutation handling. It includes breaking changes.

### Before upgrading

#### gtmctl

<!-- change-id: 0-5-0-removed-commands -->
- Breaking: Stop invoking `accounts containers combine` and `accounts containers move-tag-id`. GTM removes these commands. This CLI provides no replacement.

<!-- change-id: 0-5-0-mtls -->
- Breaking: Use a supported GTM mutation configuration or a separately reviewed alternative. Do not weaken required certificate protections to bypass this restriction. Mutual TLS (mTLS) uses certificates to authenticate both connection ends. GTM mutation transport accepts endpoint modes `auto` and `never`, rejects `always`, and does not discover client certificates automatically. Read transport remains unchanged.

<!-- change-id: 0-5-0-mutation-transport -->
- Breaking: Inspect GTM state before retrying mutation network or HTTP 5xx failures. These failures now report exit code `1` and category `unexpected`. HTTP 429 remains retryable. GTM mutations disable automatic refresh replay, redirects, and request retries. Refresh replay means resending a request after refreshing credentials. Initial credential refresh remains separate. The 60-second connect/read timeout is not a total deadline.

<!-- change-id: 0-5-0-selectors -->
- Breaking: Supply exactly one container selector, `--destination-id` or `--tag-id`, for GTM container lookup. For built-in-variable mutations, supply types from that method's bundled Discovery enum (its list of permitted values). Other types are rejected. Revert still permits an omitted type.

<!-- change-id: 0-5-0-gtag-envelope -->
- Breaking: Match `gtag-config` in GTM mutation envelope command fields, which identify the command in the response wrapper. These fields now match the command path. Retain `gtag_config` for API resource and dry-run operation names.

### Other changes

#### gtmctl

<!-- change-id: 0-5-0-version-warning -->
- GTM `create-version` help explains that the operation deletes the source workspace and sets the new base version. The acknowledgement requirement already existed.

The project documentation records the upstream removal rationale for container commands. Current upstream API availability was not independently verified.

Internal Python namespace removal was reviewed as implementation cleanup, not removal of a supported command.

[Tag v0.5.0](https://github.com/en-ver/marketing-toolbox/tree/v0.5.0) · [GitHub Release v0.5.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.5.0) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-5-0)

## 0.4.0 {#release-0-4-0}

2026-09-30 (tag date, not a verified publication date)

This release changes GA4 Admin safeguards and request handling. It includes breaking changes.

### Before upgrading

#### ga4adminctl

<!-- change-id: 0-4-0-confirm-resource -->
- Breaking: Add `--confirm-resource` with the exact resource name to destructive apply scripts. Nine destructive GA4 Admin commands require it to exactly match `--name` for apply. Any confirmation supplied during dry-run must also match. Keep existing sensitive-secret acknowledgements.

<!-- change-id: 0-4-0-patch-bodies -->
- Breaking: Send only body leaves selected by the update mask. A leaf is a field with no child fields. Name each nested update-mask leaf explicitly. GA4 Admin child patches require body leaves to match normalized update-mask leaves. Help and `sdk schema` list permitted fields for eight patch targets.

<!-- change-id: 0-4-0-firebase-filter -->
- Breaking: Remove `projects/` from Firebase project filter values. GA4 Admin property filters use `firebase_project:<project-id-or-number>` instead of `firebase_project:projects/<project-id>`. Valid account and property forms remain accepted.

<!-- change-id: 0-4-0-secret-alias -->
- Breaking: Omit the output-only secret value and let the server create it. GA4 Admin Measurement Protocol secret creation rejects both `secretValue` and `secret_value` before authentication, in both execution modes. Returned secret values remain redacted.

<!-- change-id: 0-4-0-uncertain-create -->
- Breaking: Inspect current state before retrying uncertain creates. Update scripts that treated these failures as safely retryable. GA4 Admin creates that are not safe to repeat and account-ticket provisioning report HTTP 500/503/504 as uncertain completion. They use exit code `1` and category `unexpected`. Single-call writes already existed.

[Tag v0.4.0](https://github.com/en-ver/marketing-toolbox/tree/v0.4.0) · [GitHub Release v0.4.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.4.0) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-4-0)

## 0.3.1 {#release-0-3-1}

2026-09-30 (tag date, not a verified publication date)

Credential selection and GA4 Data request handling changed. This release includes breaking changes.

### Before upgrading

#### Shared changes

<!-- change-id: 0-3-1-empty-credentials -->
- Breaking: Unset unused `GOOGLE_SERVICE_ACCOUNT_JSON` and `GOOGLE_APPLICATION_CREDENTIALS` variables instead of assigning empty strings. Explicit empty credential environment variables now fail instead of selecting another credential source.

#### ga4datactl

<!-- change-id: 0-3-1-audience-create -->
- Breaking: Inspect existing audience exports before retrying an uncertain create. Handle exit code `1` and category `unexpected` instead of the earlier retryable classification. Audience-export creation disables automatic retries and reports ambiguous server failures as uncertain completion.

<!-- change-id: 0-3-1-report-bounds -->
- Breaking: Supply batch requests and pivot field names. GA4 Data rejects empty batches and unnamed pivot fields. Keep pivot and realtime limit strings within documented bounds, including the existing 250000 ceiling. Audience-export query offsets must be within `0..9223372036854775807`.

### Other changes

#### ga4datactl

<!-- change-id: 0-3-1-request-discovery -->
- Batch SDK request descriptors omit nested property routing fields that request bodies forbid. Report and audience-export requests are constructed before credential lookup.

#### marketing-toolbox

<!-- change-id: 0-3-1-archive-exclusions -->
- The `marketing-toolbox` source archive excludes `dist` and `.release-build-*` output directories.

[Tag v0.3.1](https://github.com/en-ver/marketing-toolbox/tree/v0.3.1) · [GitHub Release v0.3.1](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.3.1) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-3-1)

## 0.3.0 {#release-0-3-0}

2026-09-30 (tag date in its recorded +03:00 offset, not a verified publication date)

This release improves command discovery and documentation. No breaking changes were identified in the reviewed evidence.

The historical user site used Hugo. Later VitePress changes do not belong to this release. Site publication success was not verified.

### Shared changes

<!-- change-id: 0-3-0-guides -->
- User guides cover installation, authentication, the three command families, pagination, output, and dry-run limits.

<!-- change-id: 0-3-0-help -->
- Root and authentication help explain command discovery, credential precedence, JSON streams, and access tiers.

### ga4datactl

<!-- change-id: 0-3-0-data-schema -->
- All six report commands expose standalone `--schema` output without credentials. This structural JSON Schema describes the request shape. It differs from the installed SDK request descriptor.

### ga4adminctl

<!-- change-id: 0-3-0-admin-schema -->
- Property-patch help and `sdk schema` expose the existing four-field update-mask allowlist (the permitted fields) and exact-body constraint.

### gtmctl

<!-- change-id: 0-3-0-gtm-planning-help -->
- GTM help distinguishes offline dry-run planning from API and response validation. This clarifies existing behavior.

### marketing-toolbox

<!-- change-id: 0-3-0-source-archive -->
- The `marketing-toolbox` source archive excludes Hugo and user-site inputs.

[Tag v0.3.0](https://github.com/en-ver/marketing-toolbox/tree/v0.3.0) · [GitHub Release v0.3.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.3.0) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-3-0)

## 0.2.0 {#release-0-2-0}

2026-09-25 (tag date, not a verified publication date)

This release changes authentication and command failure reporting. It includes a confirmed breaking change and a potential identity change.

OAuth and Application Default Credentials (ADC) changes are attributed retrospectively from the chosen pre-OAuth boundary.
The feature commit still declares 0.1.0, before the 0.2.0 version bump.

### Before upgrading

#### Shared changes

<!-- change-id: 0-2-0-process-exit -->
- Breaking: Handle nonzero failure codes in scripts. Do not treat the former zero exit as proof of success. Console entry points now preserve nonzero command exit codes instead of returning an erroneous zero.

<!-- change-id: 0-2-0-credential-fallback -->
- Potential breaking change: Review credential precedence before automation. Use an explicit credential source when a fixed identity is required. A selected invalid source fails instead of switching identity. New ambient ADC fallback can authenticate commands that previously lacked credentials.

### Other changes

#### Shared changes

<!-- change-id: 0-2-0-auth -->
- Native OAuth adds `auth login`, `auth status`, `auth forget`, and `auth revoke`. Credential selection uses inline service accounts, explicit files, matching native records, then ADC.

<!-- change-id: 0-2-0-native-setup -->
- Native OAuth uses a Desktop client, tool-specific access tiers, and approved encrypted operating-system keyring storage. `--no-open-browser` requires `--port`.

<!-- change-id: 0-2-0-auth-lifecycle -->
- `auth forget` removes a local record only. `auth revoke` requires `--apply` and `--acknowledge-project-wide-revocation` because it affects the OAuth project grant.

[Tag v0.2.0](https://github.com/en-ver/marketing-toolbox/tree/v0.2.0) · [GitHub Release v0.2.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.2.0) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-2-0)

## 0.1.0 {#release-0-1-0}

2026-09-23 (initial source commit date, not a verified publication date)

This untagged initial history introduces the tools and includes breaking naming changes.
The interval includes September 24 packaging work through a chosen pre-OAuth boundary.
It does not mean that every change shipped on September 23.
The original distribution was `marketing-tools`. The package names used here follow the later four-package naming convention.

### Before upgrading

#### Shared changes

<!-- change-id: 0-1-0-package-rename -->
- Breaking: For the earliest source, install `marketing-toolbox` or a named launcher. The distribution changes from `marketing-tools` to `marketing-toolbox`. Three thin launcher distributions pin the same core version. The core still installs all three commands. There is no `marketing-toolbox` executable.

<!-- change-id: 0-1-0-schema-identity -->
- Breaking: Update scripts that compare the old `schemaVersion` literal. Update Data schema-URN references to the renamed identifiers. The initial rename changes `schemaVersion` from `marketing-tools/v1` to `marketing-toolbox/v1` and schema URNs to `urn:marketing-toolbox`.

### Other changes

#### Shared changes

<!-- change-id: 0-1-0-commands -->
- `ga4datactl` provides GA4 reports and audience exports. `ga4adminctl` manages GA4 resources. `gtmctl` reads and changes GTM resources.

<!-- change-id: 0-1-0-output -->
- Commands emit a versioned JSON envelope (a response wrapper) on stdout and diagnostics on stderr. Writes use explicit apply or dry-run controls and operation-specific acknowledgements.

<!-- change-id: 0-1-0-service-accounts -->
- Initial authentication supports inline `GOOGLE_SERVICE_ACCOUNT_JSON` before a `GOOGLE_APPLICATION_CREDENTIALS` service-account file. Native OAuth and ambient user ADC are outside this interval and are attributed to 0.2.0.

There is no tag or GitHub Release for this interval.

[Initial source commit](https://github.com/en-ver/marketing-toolbox/commit/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f) · [Historical evidence](https://github.com/en-ver/marketing-toolbox/blob/main/docs/changelog-provenance.md#release-0-1-0)
