---
title: Changelog
---

# Changelog

All four distributions share version tags (lockstep versions).
The `marketing-toolbox` umbrella distribution contains all three commands and their shared implementation.
The launcher packages are `ga4datactl`, `ga4adminctl`, and `gtmctl`.
A launcher heading identifies affected behavior, not an independently released version.
`marketing_common` is shared implementation, not another distribution.

The following notice applies to all eight entries.

These retrospective notes were reconstructed from source, documentation, and test assertions. Original release notes, PyPI publication dates, and historical test results were not verified. Tag dates are not publication dates.

## 0.6.0 {#release-0-6-0}

2026-10-07 (Tag date)

Retrospective reconstruction: yes.

Compatibility: Breaking changes identified

Caveat: Compatibility of third-party imports from private Python modules was not established. Removed internal facades do not establish a CLI command removal.

Caveat: Historical runtime validation was not verified. An incomplete-validation message at an intermediate commit does not establish the final tag's test results.

Tag: [Tag v0.6.0](https://github.com/en-ver/marketing-toolbox/tree/v0.6.0)

GitHub Release: [Release v0.6.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.6.0)

Tag object: [f9bbd58c5272b616042f1312a532729be7911711](https://api.github.com/repos/en-ver/marketing-toolbox/git/tags/f9bbd58c5272b616042f1312a532729be7911711)

Annotated tag timestamp: 2026-10-07T07:59:30+03:00

Target commit: [b507d2d4c05eca043f3df409fcca82d18f4bc01f](https://github.com/en-ver/marketing-toolbox/commit/b507d2d4c05eca043f3df409fcca82d18f4bc01f)

Comparison base (exclusive): [df0f5ca751f731016e664c2378f2c94c83d5b5e0](https://github.com/en-ver/marketing-toolbox/commit/df0f5ca751f731016e664c2378f2c94c83d5b5e0)

Comparison target (inclusive): [b507d2d4c05eca043f3df409fcca82d18f4bc01f](https://github.com/en-ver/marketing-toolbox/commit/b507d2d4c05eca043f3df409fcca82d18f4bc01f)

### ga4datactl

#### Fixed

<!-- change-id: 0-6-0-data-nesting -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4datactl
  Text: GA4 Data reports a schema traversal RecursionError as an invalid\_request validation error before authentication. No numeric nesting limit is specified.
  Action: Reduce request nesting. Handle a validation error instead of an unexpected exception.
  Evidence: [afee935 src/ga4datactl/foundation/validation.py:122-131](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/ga4datactl/foundation/validation.py#L122-L131) | [afee935 tests/test\_ga4\_data.py:160-200](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_ga4_data.py#L160-L200)

### ga4adminctl

#### Fixed

<!-- change-id: 0-6-0-admin-page-size -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4adminctl
  Text: GA4 Admin change-history search enforces 1..200 for explicitly supplied pageSize and page\_size values before authentication.
  Action: Use 1..200 for either spelling, or omit the field to use the existing default.
  Evidence: [afee935 src/ga4adminctl/operations/access.py:65-94](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/ga4adminctl/operations/access.py#L65-L94) | [afee935 tests/test\_ga4\_admin\_discovery.py:1397-1403](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_ga4_admin_discovery.py#L1397-L1403)

### gtmctl

#### Fixed

<!-- change-id: 0-6-0-gtm-identifiers -->
- Fixed | Breaking change | Packages: marketing-toolbox, gtmctl
  Text: GTM resource paths reject dot components, URL delimiters, whitespace, control characters, and surrogates. Safe opaque identifiers remain accepted.
  Action: Supply canonical unescaped IDs. Do not encode malformed path components to bypass validation.
  Evidence: [afee935 src/gtmctl/foundation/validation.py:20-100](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/gtmctl/foundation/validation.py#L20-L100) | [afee935 tests/test\_gtm\_request\_fidelity.py:510-548](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_gtm_request_fidelity.py#L510-L548)

<!-- change-id: 0-6-0-gtm-responses -->
- Fixed | Breaking change | Packages: marketing-toolbox, gtmctl
  Text: Unreadable GTM mutation responses report uncertain completion with exit 1/unexpected after evidence of a successful HTTP response. Empty responses still become {}.
  Action: Inspect GTM state before retrying a mutation with an unreadable response.
  Evidence: [afee935 src/gtmctl/operations/mutations.py:39-90](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/gtmctl/operations/mutations.py#L39-L90) | [afee935 tests/test\_gtm\_errors.py:250-325](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_gtm_errors.py#L250-L325)

## 0.5.1 {#release-0-5-1}

2026-10-01 (Tag date)

Retrospective reconstruction: yes.

Compatibility: Compatibility review incomplete

Caveat: The migration impact of native OAuth lock and profile requirements remains uncertain for existing custom profiles.

Caveat: Diagnostic text changes are confirmed, but a strict public guarantee for that text was not established.

Caveat: The final commit changes a Windows test fixture, not shipped OAuth behavior. Native Windows runtime results were not verified.

Tag: [Tag v0.5.1](https://github.com/en-ver/marketing-toolbox/tree/v0.5.1)

GitHub Release: [Release v0.5.1](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.5.1)

Tag object: [64d2b6bc6339f6e1d4e2542fa6c6863871269172](https://api.github.com/repos/en-ver/marketing-toolbox/git/tags/64d2b6bc6339f6e1d4e2542fa6c6863871269172)

Annotated tag timestamp: 2026-10-01T19:04:20+03:00

Target commit: [df0f5ca751f731016e664c2378f2c94c83d5b5e0](https://github.com/en-ver/marketing-toolbox/commit/df0f5ca751f731016e664c2378f2c94c83d5b5e0)

Comparison base (exclusive): [cd5bc653e405528461bbc1e42dbe6ffe5841af8b](https://github.com/en-ver/marketing-toolbox/commit/cd5bc653e405528461bbc1e42dbe6ffe5841af8b)

Comparison target (inclusive): [df0f5ca751f731016e664c2378f2c94c83d5b5e0](https://github.com/en-ver/marketing-toolbox/commit/df0f5ca751f731016e664c2378f2c94c83d5b5e0)

### Shared changes

#### Fixed

<!-- change-id: 0-5-1-oauth-lock -->
- Fixed | Potential breaking change | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Native OAuth storage uses a shared per-user lock across tools. Cooperating operations share a five-second contention budget, not a whole-command deadline.
  Action: Make sure that the canonical OS profile permits a private, writable lock path. Older or noncooperating binaries do not share this protection.
  Evidence: [9a2053d src/marketing\_common/oauth.py:300-486](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/marketing_common/oauth.py#L300-L486) | [9a2053d tests/test\_oauth\_locking.py:883-939](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/tests/test_oauth_locking.py#L883-L939)

<!-- change-id: 0-5-1-oauth-replacement -->
- Fixed | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: OAuth revocation preserves a local record replaced during the remote request and reports that review is required.
  Evidence: [9a2053d src/marketing\_common/oauth.py:879-921](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/marketing_common/oauth.py#L879-L921) | [9a2053d tests/test\_oauth.py:985-1018](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/tests/test_oauth.py#L985-L1018)

### ga4datactl

#### Fixed

<!-- change-id: 0-5-1-data-diagnostics -->
- Fixed | Potential breaking change | Packages: marketing-toolbox, ga4datactl
  Text: GA4 Data validation uses controlled messages instead of raw schema errors, request-data paths, or custom pivot dimension names.
  Action: Use structured error categories and exit codes instead of parsing diagnostic prose or echoed request values.
  Evidence: [9a2053d src/ga4datactl/foundation/validation.py:56-126](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4datactl/foundation/validation.py#L56-L126) | [9a2053d src/ga4datactl/foundation/validation.py:246-313](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4datactl/foundation/validation.py#L246-L313)

### ga4adminctl

#### Fixed

<!-- change-id: 0-5-1-admin-diagnostics -->
- Fixed | Potential breaking change | Packages: marketing-toolbox, ga4adminctl
  Text: GA4 Admin sanitizes protobuf parser diagnostics for request bodies, access reports, and change history.
  Action: Use structured error categories and exit codes instead of parsing SDK diagnostic prose.
  Evidence: [9a2053d src/ga4adminctl/foundation/validation.py:128-138](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4adminctl/foundation/validation.py#L128-L138) | [9a2053d src/ga4adminctl/operations/access.py:26-88](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4adminctl/operations/access.py#L26-L88)

## 0.5.0 {#release-0-5-0}

2026-10-01 (Tag date)

Retrospective reconstruction: yes.

Compatibility: Breaking changes identified

Caveat: The project documentation records the upstream removal rationale for container commands. Current upstream API availability was not independently verified.

Caveat: Internal Python namespace removal was reviewed as implementation cleanup, not removal of a supported command.

Tag: [Tag v0.5.0](https://github.com/en-ver/marketing-toolbox/tree/v0.5.0)

GitHub Release: [Release v0.5.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.5.0)

Tag object: [655d5f76818484b143bd5027df43eb2e4a3d53c5](https://api.github.com/repos/en-ver/marketing-toolbox/git/tags/655d5f76818484b143bd5027df43eb2e4a3d53c5)

Annotated tag timestamp: 2026-10-01T10:02:49+03:00

Target commit: [cd5bc653e405528461bbc1e42dbe6ffe5841af8b](https://github.com/en-ver/marketing-toolbox/commit/cd5bc653e405528461bbc1e42dbe6ffe5841af8b)

Comparison base (exclusive): [d59a8222149ec385dce26652f3246d5f025e7168](https://github.com/en-ver/marketing-toolbox/commit/d59a8222149ec385dce26652f3246d5f025e7168)

Comparison target (inclusive): [cd5bc653e405528461bbc1e42dbe6ffe5841af8b](https://github.com/en-ver/marketing-toolbox/commit/cd5bc653e405528461bbc1e42dbe6ffe5841af8b)

### gtmctl

#### Changed

<!-- change-id: 0-5-0-removed-commands -->
- Changed | Breaking change | Packages: marketing-toolbox, gtmctl
  Text: GTM removes accounts containers combine and accounts containers move-tag-id.
  Action: Stop invoking these commands. This CLI provides no replacement.
  Evidence: [cd5bc65 src/gtmctl/commands/accounts.py:9-50](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/accounts.py#L9-L50)

<!-- change-id: 0-5-0-mtls -->
- Changed | Breaking change | Packages: marketing-toolbox, gtmctl
  Text: GTM mutation transport accepts mutual TLS (mTLS) endpoint modes auto and never, rejects always, and does not discover client certificates automatically. Read transport remains unchanged.
  Action: Use a supported mutation configuration or a separately reviewed alternative. Do not weaken required certificate protections to bypass this restriction.
  Evidence: [cd5bc65 src/gtmctl/operations/mutation\_transport.py:20-97](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/operations/mutation_transport.py#L20-L97)

<!-- change-id: 0-5-0-version-warning -->
- Changed | No breaking change identified | Packages: marketing-toolbox, gtmctl
  Text: GTM create-version help explains that the operation deletes the source workspace and sets the new base version. The acknowledgement requirement already existed.
  Evidence: [cd5bc65 src/gtmctl/commands/workspace\_operations.py:179-190](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/workspace_operations.py#L179-L190)

#### Fixed

<!-- change-id: 0-5-0-mutation-transport -->
- Fixed | Breaking change | Packages: marketing-toolbox, gtmctl
  Text: GTM mutations disable automatic refresh replay, redirects, and request retries. Initial credential refresh remains separate. The 60-second connect/read timeout is not a total deadline.
  Action: Inspect GTM state before retrying mutation network or HTTP 5xx failures, which now report exit 1/unexpected. HTTP 429 remains retryable.
  Evidence: [cd5bc65 src/gtmctl/operations/mutation\_transport.py:20-97](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/operations/mutation_transport.py#L20-L97) | [cd5bc65 src/gtmctl/foundation/errors.py:30-107](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/foundation/errors.py#L30-L107)

<!-- change-id: 0-5-0-selectors -->
- Fixed | Breaking change | Packages: marketing-toolbox, gtmctl
  Text: GTM container lookup requires exactly one of --destination-id or --tag-id. Built-in-variable mutations reject types outside each method's bundled Discovery enum.
  Action: Supply one container selector and method-supported variable types. Revert still permits an omitted type.
  Evidence: [cd5bc65 src/gtmctl/commands/accounts.py:349-377](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/accounts.py#L349-L377) | [cd5bc65 src/gtmctl/commands/built\_in\_variable\_mutations.py:17-62](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/built_in_variable_mutations.py#L17-L62)

<!-- change-id: 0-5-0-gtag-envelope -->
- Fixed | Breaking change | Packages: marketing-toolbox, gtmctl
  Text: GTM mutation envelopes use gtag-config to match the command path. API resource and dry-run operation names retain gtag\_config.
  Action: Match gtag-config in envelope command fields. Retain gtag\_config where the API or dry-run operation requires it.
  Evidence: [cd5bc65 src/gtmctl/commands/tag\_mutations.py:84-187](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/tag_mutations.py#L84-L187)

## 0.4.0 {#release-0-4-0}

2026-09-30 (Tag date)

Retrospective reconstruction: yes.

Compatibility: Breaking changes identified

Tag: [Tag v0.4.0](https://github.com/en-ver/marketing-toolbox/tree/v0.4.0)

GitHub Release: [Release v0.4.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.4.0)

Tag object: [5d79540419310b305be813b61194256da2aef34b](https://api.github.com/repos/en-ver/marketing-toolbox/git/tags/5d79540419310b305be813b61194256da2aef34b)

Annotated tag timestamp: 2026-09-30T22:42:31+03:00

Target commit: [d59a8222149ec385dce26652f3246d5f025e7168](https://github.com/en-ver/marketing-toolbox/commit/d59a8222149ec385dce26652f3246d5f025e7168)

Comparison base (exclusive): [449a5822fc13a104ac1f8524ff04e9248593f914](https://github.com/en-ver/marketing-toolbox/commit/449a5822fc13a104ac1f8524ff04e9248593f914)

Comparison target (inclusive): [d59a8222149ec385dce26652f3246d5f025e7168](https://github.com/en-ver/marketing-toolbox/commit/d59a8222149ec385dce26652f3246d5f025e7168)

### ga4adminctl

#### Changed

<!-- change-id: 0-4-0-confirm-resource -->
- Changed | Breaking change | Packages: marketing-toolbox, ga4adminctl
  Text: Nine destructive GA4 Admin commands require --confirm-resource to exactly match --name for apply. Any confirmation supplied during dry-run must also match.
  Action: Add --confirm-resource with the exact resource name to destructive apply scripts. Keep existing sensitive-secret acknowledgements.
  Evidence: [d59a822 src/ga4adminctl/commands/\_common.py:75-84](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/commands/_common.py#L75-L84) | [d59a822 tests/test\_ga4\_admin\_command\_tree.py:159-216](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/tests/test_ga4_admin_command_tree.py#L159-L216)

#### Fixed

<!-- change-id: 0-4-0-patch-bodies -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4adminctl
  Text: GA4 Admin child patches require body leaves to match normalized update-mask leaves. Help and sdk schema expose allowlists for eight patch targets.
  Action: Send only mask-selected body leaves. Name each nested update-mask leaf explicitly.
  Evidence: [d59a822 src/ga4adminctl/operations/resources.py:72-179](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/operations/resources.py#L72-L179) | [d59a822 src/ga4adminctl/commands/sdk.py:298-307](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/commands/sdk.py#L298-L307)

<!-- change-id: 0-4-0-firebase-filter -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4adminctl
  Text: GA4 Admin property filters use firebase\_project:\<project-id-or-number\> instead of firebase\_project:projects/\<project-id\>. Valid account and property forms remain accepted.
  Action: Remove projects/ from Firebase project filter values.
  Evidence: [d59a822 src/ga4adminctl/foundation/validation.py:29-106](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/foundation/validation.py#L29-L106)

<!-- change-id: 0-4-0-secret-alias -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4adminctl
  Text: GA4 Admin Measurement Protocol secret creation rejects both secretValue and secret\_value before authentication in both execution modes. Returned secret values remain redacted.
  Action: Omit the output-only secret value and let the server create it.
  Evidence: [d59a822 src/ga4adminctl/operations/secrets.py:73-98](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/operations/secrets.py#L73-L98)

<!-- change-id: 0-4-0-uncertain-create -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4adminctl
  Text: GA4 Admin non-idempotent creates and account-ticket provisioning report HTTP 500/503/504 as uncertain completion with exit 1/unexpected. Single-call writes already existed.
  Action: Inspect current state before retrying uncertain creates. Update scripts that treated these failures as safely retryable.
  Evidence: [d59a822 src/ga4adminctl/foundation/errors.py:20-38](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/foundation/errors.py#L20-L38) | [d59a822 src/ga4adminctl/operations/mutations.py:24-62](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/operations/mutations.py#L24-L62)

## 0.3.1 {#release-0-3-1}

2026-09-30 (Tag date)

Retrospective reconstruction: yes.

Compatibility: Breaking changes identified

Tag: [Tag v0.3.1](https://github.com/en-ver/marketing-toolbox/tree/v0.3.1)

GitHub Release: [Release v0.3.1](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.3.1)

Tag object: [84a7e5ad04559154a87937118ee7efaec386f769](https://api.github.com/repos/en-ver/marketing-toolbox/git/tags/84a7e5ad04559154a87937118ee7efaec386f769)

Annotated tag timestamp: 2026-09-30T17:20:42+03:00

Target commit: [449a5822fc13a104ac1f8524ff04e9248593f914](https://github.com/en-ver/marketing-toolbox/commit/449a5822fc13a104ac1f8524ff04e9248593f914)

Comparison base (exclusive): [944aa9f0d31bbec8b602eefdce4b7241c45bca5a](https://github.com/en-ver/marketing-toolbox/commit/944aa9f0d31bbec8b602eefdce4b7241c45bca5a)

Comparison target (inclusive): [449a5822fc13a104ac1f8524ff04e9248593f914](https://github.com/en-ver/marketing-toolbox/commit/449a5822fc13a104ac1f8524ff04e9248593f914)

### Shared changes

#### Fixed

<!-- change-id: 0-3-1-empty-credentials -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Explicit empty credential environment variables fail instead of falling through to another credential source.
  Action: Unset unused GOOGLE\_SERVICE\_ACCOUNT\_JSON and GOOGLE\_APPLICATION\_CREDENTIALS variables instead of assigning empty strings.
  Evidence: [449a582 src/marketing\_common/auth.py:30-136](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/marketing_common/auth.py#L30-L136) | [449a582 tests/test\_oauth.py:179-222](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/tests/test_oauth.py#L179-L222)

### ga4datactl

#### Fixed

<!-- change-id: 0-3-1-audience-create -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4datactl
  Text: GA4 Data audience-export creation disables automatic retries and reports ambiguous server failures as uncertain completion with exit 1/unexpected.
  Action: Inspect existing exports before retrying an uncertain create. Handle exit 1 instead of the earlier retryable classification.
  Evidence: [449a582 src/ga4datactl/operations/audience\_exports.py:183-227](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/operations/audience_exports.py#L183-L227) | [449a582 src/ga4datactl/foundation/errors.py:31-59](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/foundation/errors.py#L31-L59)

<!-- change-id: 0-3-1-report-bounds -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4datactl
  Text: GA4 Data rejects empty batches and unnamed pivot fields. It bounds pivot and realtime limit strings and restricts audience-export query offsets to 0..9223372036854775807.
  Action: Supply batch requests and pivot names. Keep limits within documented bounds and offsets within the accepted range.
  Evidence: [449a582 src/ga4datactl/schemas.py:14-120](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/schemas.py#L14-L120) | [449a582 src/ga4datactl/foundation/validation.py:122-130](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/foundation/validation.py#L122-L130)

<!-- change-id: 0-3-1-request-discovery -->
- Fixed | No breaking change identified | Packages: marketing-toolbox, ga4datactl
  Text: GA4 Data batch SDK descriptors omit nested property routing fields that request bodies forbid. Report and audience-export request construction precedes credential lookup.
  Evidence: [449a582 src/ga4datactl/commands/sdk.py:42-72](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/commands/sdk.py#L42-L72) | [449a582 src/ga4datactl/operations/reports.py:148-264](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/operations/reports.py#L148-L264)

### marketing-toolbox

#### Fixed

<!-- change-id: 0-3-1-archive-exclusions -->
- Fixed | No breaking change identified | Packages: marketing-toolbox
  Text: The marketing-toolbox source archive excludes dist and .release-build-\* output directories.
  Evidence: [449a582 pyproject.toml:35-36](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/pyproject.toml#L35-L36)

## 0.3.0 {#release-0-3-0}

2026-09-30 (Tag date)

Retrospective reconstruction: yes.

Compatibility: No breaking changes identified in reviewed evidence

Caveat: The historical user site used Hugo. Later VitePress changes do not belong to this entry. Site publication success was not verified.

Tag: [Tag v0.3.0](https://github.com/en-ver/marketing-toolbox/tree/v0.3.0)

GitHub Release: [Release v0.3.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.3.0)

Tag object: [571f37b6c10d39ffde93598e9a68f6ae23308f93](https://api.github.com/repos/en-ver/marketing-toolbox/git/tags/571f37b6c10d39ffde93598e9a68f6ae23308f93)

Annotated tag timestamp: 2026-09-30T00:26:21+03:00

Target commit: [944aa9f0d31bbec8b602eefdce4b7241c45bca5a](https://github.com/en-ver/marketing-toolbox/commit/944aa9f0d31bbec8b602eefdce4b7241c45bca5a)

Comparison base (exclusive): [d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb](https://github.com/en-ver/marketing-toolbox/commit/d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb)

Comparison target (inclusive): [944aa9f0d31bbec8b602eefdce4b7241c45bca5a](https://github.com/en-ver/marketing-toolbox/commit/944aa9f0d31bbec8b602eefdce4b7241c45bca5a)

### Shared changes

#### Added

<!-- change-id: 0-3-0-guides -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: User guides cover installation, authentication, the three command families, pagination, output, and dry-run limits.
  Evidence: [07482bf docs/user/\_index.md:6-18](https://github.com/en-ver/marketing-toolbox/blob/07482bf82c4abd26146b4e6f3b91ca3d4980452f/docs/user/_index.md#L6-L18) | [944aa9f docs/user/tools/\_index.md:26-38](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/docs/user/tools/_index.md#L26-L38)

#### Changed

<!-- change-id: 0-3-0-help -->
- Changed | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Root and authentication help explain command discovery, credential precedence, JSON streams, and access tiers.
  Evidence: [944aa9f src/marketing\_common/cli.py:14-33](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/marketing_common/cli.py#L14-L33) | [944aa9f src/marketing\_common/oauth\_cli.py:24-44](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/marketing_common/oauth_cli.py#L24-L44)

### ga4datactl

#### Added

<!-- change-id: 0-3-0-data-schema -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl
  Text: All six GA4 Data report commands expose standalone --schema output without credentials. This structural JSON Schema differs from the installed SDK request descriptor.
  Evidence: [944aa9f src/ga4datactl/commands/reports.py:18-51](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/ga4datactl/commands/reports.py#L18-L51) | [944aa9f tests/test\_cli.py:469-490](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/tests/test_cli.py#L469-L490)

### ga4adminctl

#### Changed

<!-- change-id: 0-3-0-admin-schema -->
- Changed | No breaking change identified | Packages: marketing-toolbox, ga4adminctl
  Text: GA4 Admin property-patch help and sdk schema expose the existing four-field update-mask allowlist and exact-body constraint.
  Evidence: [944aa9f src/ga4adminctl/operations/properties.py:40-45](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/ga4adminctl/operations/properties.py#L40-L45) | [944aa9f src/ga4adminctl/commands/sdk.py:269-279](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/ga4adminctl/commands/sdk.py#L269-L279)

### gtmctl

#### Changed

<!-- change-id: 0-3-0-gtm-planning-help -->
- Changed | No breaking change identified | Packages: marketing-toolbox, gtmctl
  Text: GTM help distinguishes offline dry-run planning from API and response validation. This clarifies existing behavior.
  Evidence: [944aa9f src/gtmctl/commands/\_common.py:14-18](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/gtmctl/commands/_common.py#L14-L18)

### marketing-toolbox

#### Changed

<!-- change-id: 0-3-0-source-archive -->
- Changed | No breaking change identified | Packages: marketing-toolbox
  Text: The marketing-toolbox source archive excludes Hugo and user-site inputs.
  Evidence: [944aa9f pyproject.toml:35-36](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/pyproject.toml#L35-L36)

## 0.2.0 {#release-0-2-0}

2026-09-25 (Tag date)

Retrospective reconstruction: yes.

Compatibility: Breaking changes identified

Caveat: OAuth and ADC changes are attributed retrospectively from the chosen pre-OAuth boundary. The feature commit still declares 0.1.0, before the 0.2.0 version bump.

Tag: [Tag v0.2.0](https://github.com/en-ver/marketing-toolbox/tree/v0.2.0)

GitHub Release: [Release v0.2.0](https://github.com/en-ver/marketing-toolbox/releases/tag/v0.2.0)

Tag object: [2890f12a63fa5311fdcc1b8c6db615d4300156c1](https://api.github.com/repos/en-ver/marketing-toolbox/git/tags/2890f12a63fa5311fdcc1b8c6db615d4300156c1)

Annotated tag timestamp: 2026-09-25T12:59:51+03:00

Target commit: [d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb](https://github.com/en-ver/marketing-toolbox/commit/d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb)

Comparison base (exclusive): [773c5ffcba3675fad60daf0808e950341cfc15a0](https://github.com/en-ver/marketing-toolbox/commit/773c5ffcba3675fad60daf0808e950341cfc15a0)

Comparison target (inclusive): [d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb](https://github.com/en-ver/marketing-toolbox/commit/d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb)

### Shared changes

#### Added

<!-- change-id: 0-2-0-auth -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Native OAuth adds auth login, status, forget, and revoke. Credential selection uses inline service accounts, explicit files, matching native records, then Application Default Credentials (ADC).
  Evidence: [ebed104 src/marketing\_common/auth.py:81-137](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/auth.py#L81-L137) | [ebed104 src/marketing\_common/oauth\_cli.py:24-162](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth_cli.py#L24-L162)

<!-- change-id: 0-2-0-native-setup -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Native OAuth uses a Desktop client, tool-specific access tiers, and approved encrypted OS keyring storage. --no-open-browser requires --port.
  Evidence: [ebed104 src/marketing\_common/oauth.py:78-138](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth.py#L78-L138) | [ebed104 src/marketing\_common/oauth.py:626-662](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth.py#L626-L662)

<!-- change-id: 0-2-0-auth-lifecycle -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: auth forget removes a local record only. auth revoke requires --apply and --acknowledge-project-wide-revocation because it affects the OAuth project grant.
  Evidence: [ebed104 src/marketing\_common/oauth\_cli.py:105-160](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth_cli.py#L105-L160)

#### Changed

<!-- change-id: 0-2-0-credential-fallback -->
- Changed | Potential breaking change | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: A selected invalid credential source fails instead of switching identity. New ambient ADC fallback can authenticate commands that previously lacked credentials.
  Action: Review credential precedence before automation. Use an explicit credential source when a fixed identity is required.
  Evidence: [ebed104 src/marketing\_common/auth.py:81-137](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/auth.py#L81-L137) | [ebed104 tests/test\_oauth.py:74-118](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/tests/test_oauth.py#L74-L118)

#### Fixed

<!-- change-id: 0-2-0-process-exit -->
- Fixed | Breaking change | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Console entry points preserve nonzero command exit codes instead of returning an erroneous zero.
  Action: Handle nonzero failure codes in scripts. Do not treat the former zero exit as proof of success.
  Evidence: [ebed104 src/marketing\_common/cli.py:114-123](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/cli.py#L114-L123) | [d7db5d1 tests/test\_cli.py:413-458](https://github.com/en-ver/marketing-toolbox/blob/d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb/tests/test_cli.py#L413-L458)

## 0.1.0 {#release-0-1-0}

2026-09-23 (Initial source commit date)

Retrospective reconstruction: yes.

Compatibility: Breaking changes identified

Caveat: Untagged initial history. September 23 is the initial source commit date, not a verified publication date.

Caveat: This interval includes September 24 packaging work through a chosen pre-OAuth boundary. It does not claim that every change shipped on September 23.

Caveat: The original distribution name was marketing-tools. Package labels use the later four-package names to support consistent filtering.

Tag: Untagged initial history

Initial source commit: [4147871781c42a9e1539823f6f8e8ad1bd0e4b8f](https://github.com/en-ver/marketing-toolbox/commit/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f)

Initial source timestamp: 2026-09-23T16:42:01+03:00

Target commit: [773c5ffcba3675fad60daf0808e950341cfc15a0](https://github.com/en-ver/marketing-toolbox/commit/773c5ffcba3675fad60daf0808e950341cfc15a0)

Comparison base (exclusive): None (initial history).

Comparison target (inclusive): [773c5ffcba3675fad60daf0808e950341cfc15a0](https://github.com/en-ver/marketing-toolbox/commit/773c5ffcba3675fad60daf0808e950341cfc15a0)

### Shared changes

#### Added

<!-- change-id: 0-1-0-commands -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: ga4datactl provides GA4 reports and audience exports, ga4adminctl manages GA4 resources, and gtmctl reads and changes GTM resources.
  Evidence: [4147871 README.md:3-56](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/README.md#L3-L56)

<!-- change-id: 0-1-0-output -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Commands emit a versioned JSON envelope on stdout and diagnostics on stderr. Writes use explicit apply or dry-run controls and operation-specific acknowledgements.
  Evidence: [4147871 src/marketing\_common/cli.py:14-73](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/src/marketing_common/cli.py#L14-L73) | [4147871 src/gtmctl/commands/tag\_mutations.py:58-98](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/src/gtmctl/commands/tag_mutations.py#L58-L98)

<!-- change-id: 0-1-0-service-accounts -->
- Added | No breaking change identified | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: Initial authentication supports inline GOOGLE\_SERVICE\_ACCOUNT\_JSON before a GOOGLE\_APPLICATION\_CREDENTIALS service-account file. Native OAuth and ambient user ADC are outside this interval.
  Evidence: [4147871 src/marketing\_common/auth.py:20-74](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/src/marketing_common/auth.py#L20-L74)

#### Changed

<!-- change-id: 0-1-0-package-rename -->
- Changed | Breaking change | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: The distribution changes from marketing-tools to marketing-toolbox. Three thin launcher distributions pin the same core version. The core still installs all three commands.
  Action: For the earliest source, install marketing-toolbox or a named launcher. There is no marketing-toolbox executable.
  Evidence: [0530eb7 pyproject.toml:5-31](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/pyproject.toml#L5-L31) | [0530eb7 packaging/ga4datactl/pyproject.toml:5-22](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/packaging/ga4datactl/pyproject.toml#L5-L22)

<!-- change-id: 0-1-0-schema-identity -->
- Changed | Breaking change | Packages: marketing-toolbox, ga4datactl, ga4adminctl, gtmctl
  Text: The initial rename changes schemaVersion from marketing-tools/v1 to marketing-toolbox/v1 and changes schema URNs to urn:marketing-toolbox.
  Action: Update scripts that compare the old schemaVersion literal. Update Data schema-URN references to the renamed identifiers.
  Evidence: [0530eb7 src/marketing\_common/cli.py:14-40](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/src/marketing_common/cli.py#L14-L40) | [0530eb7 src/ga4datactl/schemas.py:1-120](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/src/ga4datactl/schemas.py#L1-L120)
