# v1 public API eligibility requirements

These requirements govern the public command contract for `ga4datactl`, `ga4adminctl`, and `gtmctl`. They are binding for implementation and future maintenance.

## Client integration policy

1. v1 implementations MUST use an official supported Google Python client library/SDK. Hand-written REST/HTTP integrations are out of scope.
2. `google-analytics-data` and `google-analytics-admin` are the approved SDKs for GA4 Data and GA4 Admin. `google-api-python-client` is the approved official discovery-based Python client for GTM v2.
3. The public CLI contract remains independent of a specific internal client. A future direct REST integration requires an explicit design decision, contract-compatibility review, and tests proving equivalent authentication, request, retry, error, and response behavior.

## Upstream API version policy

1. `ga4datactl` public v1 commands MUST map only to Google Analytics Data API `v1beta` methods.
2. `ga4adminctl` public v1 commands MUST map only to Google Analytics Admin API `v1beta` methods.
3. `gtmctl` public v1 commands MUST map only to Google Tag Manager API `v2` methods.
4. Google `v1alpha` methods MUST NOT be exposed through a public v1 command, even if they are present in an installed SDK or the Discovery inventory.
5. A future preview command requires a separately versioned preview contract, explicit approval, a documented upstream lifecycle warning, and no production mutation support by default. It MUST NOT be silently added to the stable public command tree.

Google API versioning guidance permits alpha releases to be shut down at any time. The GA4 Data documentation also explicitly identifies recurring audience lists as an early preview. The GA4 `v1beta` versions remain upstream beta APIs; this project will track their upstream lifecycle and manage its own CLI compatibility separately.

## Deprecation and replacement policy

1. A Google method marked deprecated in the official Discovery document or official reference MUST be `excluded` from the public v1 contract.
2. When Google documents a replacement, the catalog MUST record the deprecated method, its replacement, and the reason for exclusion. Only the replacement may be considered for a public command.
3. A command whose sole upstream implementation becomes deprecated MUST be deprecated in this project before removal, with a migration path and a new CLI major version or explicit deprecation period.
4. Maintainers MUST re-check official lifecycle and deprecation metadata when updating a Google SDK dependency or refreshing the upstream inventory.

## Complete public-target policy

This project intends to specify and implement the complete supported upstream surface, not a small curated subset. Therefore:

1. Every non-deprecated method on an approved upstream version is a `stable-target` for the project's public v1 CLI contract.
2. `stable-target` describes this project's implementation commitment. It does not relabel Google's upstream `v1beta` lifecycle as generally available.
3. `deferred` is not used for the v1 target. A later decision to defer a target requires an explicit requirements change explaining the scope reduction.
4. `preview-target` is not used in the public v1 target. Preview methods remain excluded under the upstream API version policy.

## Catalog enforcement

1. The authoritative inventory is `upstream-inventory.json`; every method has a `publicContractStatus` of `stable-target` or `excluded`.
2. Each `stable-target` MUST receive a public command path and detailed request, response, safety, and test contract before implementation begins.
3. An `excluded` method MUST NOT have a public Typer command, adapter method, fixture, or help entry.
4. The contract test suite MUST reject a public command mapped to an excluded method.

## Official sources

- Google API versioning: <https://cloud.google.com/apis/design/versioning>
- GA4 Data API REST reference: <https://developers.google.com/analytics/devguides/reporting/data/v1/rest>
- GA4 Data API overview, including preview labelling: <https://developers.google.com/analytics/devguides/reporting/data/v1/>
- GA4 Admin API REST reference: <https://developers.google.com/analytics/devguides/config/admin/v1/rest>
- Google Tag Manager API v2: <https://developers.google.com/tag-platform/tag-manager/api/v2>
- Google API Discovery Service: <https://developers.google.com/discovery/>
