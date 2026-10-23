# Changelog provenance

This file is the maintained audit mapping for [the user-facing changelog](user/changelog/index.md).
The same maintainer owns both files. The website page is the sole maintained source of user-facing release prose.
This file preserves the accepted historical words and explains their editorial disposition. It is not a second editorial changelog.
It is outside `docs/user` and does not define a website route or renderer input.

## Agreement and record contract

The eight version sections use explicit repository anchors. Each record uses its accepted stable change ID.
Its website locator consists of the version anchor and the adjacent, non-rendered `change-id` comment.
These comments are not public DOM anchors or runtime data.
There are 40 accepted identities, with release counts 4, 4, 6, 5, 5, 6, 5, 5 in newest-first order.

Historical website equivalence means preservation of facts, actions, affected-tool meaning, breaking strength, and uncertainty.
It does not mean identical wording or inline metadata.
The seven published GitHub bodies remain byte-identical historical witnesses.
Their older wording, categories, and inline audit fields intentionally differ from the rewritten website.
Do not regenerate or overwrite those bodies to match the new page.
The ledger entries below retain their verified identities and decoded-body SHA256 values.
Release flags, assets, tags, and the accepted latest designation `v0.6.0` remain unchanged.
Unexpected remote differences require parent resolution, not automatic repair.

For future unpublished releases, prepare the proposed GitHub body from the canonical human-oriented website section.
Preserve every user-facing fact, warning, action, uncertainty, and affected-tool meaning.
Only heading depth, navigation, and meaning-preserving Markdown adaptation can differ.
Include an appropriate link to repository provenance when audit evidence is separate.
Review the body before separately authorized publication and compare the fetched body afterward.
This document grants no Release, tag, package, or deployment operation.

The original category, exact package list, breaking assessment, action or its absence, and every evidence destination remain in each accepted record.
The `evidence` commit/path/line triples are immutable source locators.
Each also has an explicit repository link below.
The original JSON order, accepted-page order, current website position, and reason for any move are recorded separately.

For every completed record, original phrasing remains audit-only because the website now uses human-oriented prose.
The category and repeated package list remain audit-only because tool headings and the page-wide package explanation carry that meaning once.
Confirmed and potential breaking strength stay explicit in the affected website bullet.
A `none` assessment stays audit-only: absence of an identified break is not a guarantee of compatibility.
An absent action means that the accepted record did not provide a separate action, not that review proved no action necessary.
Evidence links remain audit-only because they support reconstruction rather than upgrade decisions.
Full tag objects, timestamps, commits, comparison boundaries, and Release body hashes are audit-only identity data.
The website retains date bases, descriptive tag/Release links, relevant caveats, and one evidence link per rewritten release.
No user behavior or required action is relocated solely to audit.

## Reconstruction limits

These retrospective notes were reconstructed from source, documentation, and test assertions. Original release notes, PyPI publication dates, and historical test results were not verified. Tag dates are not publication dates.

All versions are retrospective.
Tag dates retain their recorded offsets, not inferred publication dates.
In particular, 0.3.0 uses September 30 from `2026-09-30T00:26:21+03:00`, not September 29 in UTC.
0.1.0 is untagged. Its September 23 date is the initial source commit date, not publication.
Its chosen interval includes September 24 packaging and documentation work.
The original distribution name was `marketing-tools`, before the later four-distribution naming convention.
The eventual package vocabulary does not imply four distributions existed in the initial source.

The 0.1.0 interval runs from root `4147871781c42a9e1539823f6f8e8ad1bd0e4b8f` inclusive through `773c5ffcba3675fad60daf0808e950341cfc15a0` inclusive.
That root's author and committer timestamp is `2026-09-23T16:42:01+03:00`.
OAuth/ADC commit `ebed104a65d1712403bac5b80bf6d0350f89b511` follows that endpoint while its manifest still declares 0.1.0.
Its child `d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb` changes the four versions and launcher pins to 0.2.0.
OAuth/ADC is attributed retrospectively to 0.2.0. This is a feature-history boundary, not a publication chronology.
There is no 0.1.0 tag or hosted Release.

## Immutable baseline and completion state

The accepted pre-editorial page SHA256 is `ad033e176965c8c18de33e3233d1147ef20c3144937daee1c527f337cb73a741`.
The accepted eight-version JSON SHA256 is `6fd3e1f43c4c7aa32829e7c0dfc79a0b3e7adeaff643d8f39cab4791173dd58e`.
The seven-Release ledger SHA256 is `8a00e7f2594851589a967209abdc8efc6a6a468f6d56853e17e6b6e4ab734485`.
These are immutable witnesses, not maintained alternative notes sources.

E1A completed the 19 records for 0.6.0, 0.5.1, 0.5.0, and 0.4.0.
E1B completes the remaining 21 records for 0.3.1, 0.3.0, 0.2.0, and 0.1.0.
All eight sections and 40 records are mapped. This author-checked candidate still needs independent semantic and pre-publication review.
Website links identify the existing release sections, not proof that these rewritten notes are deployed.
The page's main-branch provenance links resolve to this candidate's explicit anchors. They do not establish that the new file exists on main yet.
All eight date bases, section metadata, and seven Release ledger entries are retained.
Each accepted record has a website locator, original/current order, and fact/action disposition for combined review.

<a id="release-0-6-0"></a>

## 0.6.0

Website section: [release 0.6.0](https://marketing-toolbox.org/changelog/#release-0-6-0). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-6-0`.

### Accepted release metadata

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

### Published historical witness

```json
{
  "tag": "v0.6.0",
  "release_id": 421798289,
  "url": "https://github.com/en-ver/marketing-toolbox/releases/tag/v0.6.0",
  "tag_object": "f9bbd58c5272b616042f1312a532729be7911711",
  "target_commit": "b507d2d4c05eca043f3df409fcca82d18f4bc01f",
  "body_sha256": "651f34df8248bf3152221c4b64815101e09482efb1854474e4ed2d774e8cf09d",
  "body_byte_parity": true,
  "draft": false,
  "prerelease": false,
  "assets": 0,
  "operation": "created",
  "create_exit": 0
}
```

The ledger body hash is for decoded UTF-8 body bytes, without newline normalization. It is not a hash of the rewritten website section.

### Editorial mapping

Dates and date bases remain visible. The page-wide retrospective notice replaces repeated per-release status labels.
Both private-import and historical-runtime caveats remain visible below the upgrade bullets.

### Record 1: 0-6-0-gtm-identifiers

Website locator: `release-0-6-0`, adjacent comment `<!-- change-id: 0-6-0-gtm-identifiers -->`.
Original JSON position: 1. Accepted-page position: 3. Current website position: 3 (Before upgrading / gtmctl / bullet 1).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps every rejected component class and acceptance of safe opaque identifiers. It keeps canonical unescaped IDs and the prohibition on encoding malformed components to bypass validation. The Unicode parenthesis explains surrogates without narrowing the rejection. Only marketing-toolbox and gtmctl are affected.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-6-0-gtm-identifiers",
  "category": "Fixed",
  "text": "GTM resource paths reject dot components, URL delimiters, whitespace, control characters, and surrogates. Safe opaque identifiers remain accepted.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Supply canonical unescaped IDs. Do not encode malformed path components to bypass validation.",
  "evidence": [
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "src/gtmctl/foundation/validation.py",
      "lines": "20-100"
    },
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "tests/test_gtm_request_fidelity.py",
      "lines": "510-548"
    }
  ]
}
```

Evidence destinations:

- [`afee9354090c0f09fc222b119952a383cf365db7 src/gtmctl/foundation/validation.py:20-100`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/gtmctl/foundation/validation.py#L20-L100)
- [`afee9354090c0f09fc222b119952a383cf365db7 tests/test_gtm_request_fidelity.py:510-548`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_gtm_request_fidelity.py#L510-L548)

### Record 2: 0-6-0-gtm-responses

Website locator: `release-0-6-0`, adjacent comment `<!-- change-id: 0-6-0-gtm-responses -->`.
Original JSON position: 2. Accepted-page position: 4. Current website position: 4 (Before upgrading / gtmctl / bullet 2).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps successful-HTTP-response evidence as the condition for uncertain completion, unreadable mutation responses, exit 1/unexpected, and empty-response normalization to {}. It puts inspecting state before retry first. It defines mutation without changing its scope.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-6-0-gtm-responses",
  "category": "Fixed",
  "text": "Unreadable GTM mutation responses report uncertain completion with exit 1/unexpected after evidence of a successful HTTP response. Empty responses still become {}.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Inspect GTM state before retrying a mutation with an unreadable response.",
  "evidence": [
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "src/gtmctl/operations/mutations.py",
      "lines": "39-90"
    },
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "tests/test_gtm_errors.py",
      "lines": "250-325"
    }
  ]
}
```

Evidence destinations:

- [`afee9354090c0f09fc222b119952a383cf365db7 src/gtmctl/operations/mutations.py:39-90`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/gtmctl/operations/mutations.py#L39-L90)
- [`afee9354090c0f09fc222b119952a383cf365db7 tests/test_gtm_errors.py:250-325`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_gtm_errors.py#L250-L325)

### Record 3: 0-6-0-admin-page-size

Website locator: `release-0-6-0`, adjacent comment `<!-- change-id: 0-6-0-admin-page-size -->`.
Original JSON position: 3. Accepted-page position: 2. Current website position: 2 (Before upgrading / ga4adminctl / bullet 1).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps change-history search, both pageSize spellings, the explicit 1–200 bound, and rejection before authentication. It keeps both choices: use a valid explicit value or omit the field for the existing default.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-6-0-admin-page-size",
  "category": "Fixed",
  "text": "GA4 Admin change-history search enforces 1..200 for explicitly supplied pageSize and page_size values before authentication.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "confirmed",
  "action": "Use 1..200 for either spelling, or omit the field to use the existing default.",
  "evidence": [
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "src/ga4adminctl/operations/access.py",
      "lines": "65-94"
    },
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "tests/test_ga4_admin_discovery.py",
      "lines": "1397-1403"
    }
  ]
}
```

Evidence destinations:

- [`afee9354090c0f09fc222b119952a383cf365db7 src/ga4adminctl/operations/access.py:65-94`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/ga4adminctl/operations/access.py#L65-L94)
- [`afee9354090c0f09fc222b119952a383cf365db7 tests/test_ga4_admin_discovery.py:1397-1403`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_ga4_admin_discovery.py#L1397-L1403)

### Record 4: 0-6-0-data-nesting

Website locator: `release-0-6-0`, adjacent comment `<!-- change-id: 0-6-0-data-nesting -->`.
Original JSON position: 4. Accepted-page position: 1. Current website position: 1 (Before upgrading / ga4datactl / bullet 1).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps schema traversal, RecursionError, invalid_request, pre-authentication validation, and the absence of a numeric nesting limit. It puts both actions first: reduce nesting and handle validation rather than an unexpected exception. A short definition explains schema traversal.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-6-0-data-nesting",
  "category": "Fixed",
  "text": "GA4 Data reports a schema traversal RecursionError as an invalid_request validation error before authentication. No numeric nesting limit is specified.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl"
  ],
  "breaking": "confirmed",
  "action": "Reduce request nesting. Handle a validation error instead of an unexpected exception.",
  "evidence": [
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "src/ga4datactl/foundation/validation.py",
      "lines": "122-131"
    },
    {
      "commit": "afee9354090c0f09fc222b119952a383cf365db7",
      "path": "tests/test_ga4_data.py",
      "lines": "160-200"
    }
  ]
}
```

Evidence destinations:

- [`afee9354090c0f09fc222b119952a383cf365db7 src/ga4datactl/foundation/validation.py:122-131`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/src/ga4datactl/foundation/validation.py#L122-L131)
- [`afee9354090c0f09fc222b119952a383cf365db7 tests/test_ga4_data.py:160-200`](https://github.com/en-ver/marketing-toolbox/blob/afee9354090c0f09fc222b119952a383cf365db7/tests/test_ga4_data.py#L160-L200)

<a id="release-0-5-1"></a>

## 0.5.1

Website section: [release 0.5.1](https://marketing-toolbox.org/changelog/#release-0-5-1). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-5-1`.

### Accepted release metadata

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

### Published historical witness

```json
{
  "tag": "v0.5.1",
  "release_id": 421798224,
  "url": "https://github.com/en-ver/marketing-toolbox/releases/tag/v0.5.1",
  "tag_object": "64d2b6bc6339f6e1d4e2542fa6c6863871269172",
  "target_commit": "df0f5ca751f731016e664c2378f2c94c83d5b5e0",
  "body_sha256": "b36aba7f1d6fd16f3eeb9ceea617896db9ac2669ec0047dcd6ec5bd67d95714f",
  "body_byte_parity": true,
  "draft": false,
  "prerelease": false,
  "assets": 0,
  "operation": "created",
  "create_exit": 0
}
```

The ledger body hash is for decoded UTF-8 body bytes, without newline normalization. It is not a hash of the rewritten website section.

### Editorial mapping

Dates and date bases remain visible. The page-wide retrospective notice replaces repeated per-release status labels.
Incomplete review and uncertain custom-profile migration remain in the introduction. The diagnostic guarantee caveat remains before Other changes. The final Windows fixture/runtime caveat remains after the ordinary change.

### Record 1: 0-5-1-oauth-lock

Website locator: `release-0-5-1`, adjacent comment `<!-- change-id: 0-5-1-oauth-lock -->`.
Original JSON position: 1. Accepted-page position: 1. Current website position: 1 (Before upgrading / Shared changes / bullet 1).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps native storage, one shared per-user lock across all three tools, the five-second cooperative contention budget, and exclusion of a whole-command deadline. It keeps the canonical OS profile's private writable lock path requirement and exclusion of older/noncooperating binaries. The release introduction keeps incomplete review and uncertain custom-profile migration.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-1-oauth-lock",
  "category": "Fixed",
  "text": "Native OAuth storage uses a shared per-user lock across tools. Cooperating operations share a five-second contention budget, not a whole-command deadline.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "potential",
  "action": "Make sure that the canonical OS profile permits a private, writable lock path. Older or noncooperating binaries do not share this protection.",
  "evidence": [
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "src/marketing_common/oauth.py",
      "lines": "300-486"
    },
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "tests/test_oauth_locking.py",
      "lines": "883-939"
    }
  ]
}
```

Evidence destinations:

- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 src/marketing_common/oauth.py:300-486`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/marketing_common/oauth.py#L300-L486)
- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 tests/test_oauth_locking.py:883-939`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/tests/test_oauth_locking.py#L883-L939)

### Record 2: 0-5-1-oauth-replacement

Website locator: `release-0-5-1`, adjacent comment `<!-- change-id: 0-5-1-oauth-replacement -->`.
Original JSON position: 2. Accepted-page position: 2. Current website position: 4 (Other changes / Shared changes / bullet 1).

Placement: Moved after the potential-breaking bullets so upgrade risks come first.

Fact and action disposition: The ordinary-change bullet keeps remote OAuth revocation, preservation of a local record replaced during that request, and the reported need for review. The accepted record had no separate action. No new action is invented. The original none assessment stays in the witness rather than becoming a compatibility guarantee.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action field is absent and remains absent in this witness.

Accepted record (unchanged values):

```json
{
  "id": "0-5-1-oauth-replacement",
  "category": "Fixed",
  "text": "OAuth revocation preserves a local record replaced during the remote request and reports that review is required.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "src/marketing_common/oauth.py",
      "lines": "879-921"
    },
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "tests/test_oauth.py",
      "lines": "985-1018"
    }
  ]
}
```

Evidence destinations:

- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 src/marketing_common/oauth.py:879-921`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/marketing_common/oauth.py#L879-L921)
- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 tests/test_oauth.py:985-1018`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/tests/test_oauth.py#L985-L1018)

### Record 3: 0-5-1-data-diagnostics

Website locator: `release-0-5-1`, adjacent comment `<!-- change-id: 0-5-1-data-diagnostics -->`.
Original JSON position: 3. Accepted-page position: 3. Current website position: 2 (Before upgrading / ga4datactl / bullet 1).

Placement: Moves ahead of the ordinary OAuth replacement record so potential breaks come first. Tool order remains Data before Admin.

Fact and action disposition: The bullet keeps controlled GA4 Data validation messages and all three replaced sources: raw schema errors, request-data paths, and custom pivot dimension names. It puts using structured categories/exit codes before the behavior. It keeps the prohibition on parsing prose or echoed request values. The nearby release caveat keeps the lack of an established strict public diagnostic-text guarantee.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-1-data-diagnostics",
  "category": "Fixed",
  "text": "GA4 Data validation uses controlled messages instead of raw schema errors, request-data paths, or custom pivot dimension names.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl"
  ],
  "breaking": "potential",
  "action": "Use structured error categories and exit codes instead of parsing diagnostic prose or echoed request values.",
  "evidence": [
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "src/ga4datactl/foundation/validation.py",
      "lines": "56-126"
    },
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "src/ga4datactl/foundation/validation.py",
      "lines": "246-313"
    }
  ]
}
```

Evidence destinations:

- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 src/ga4datactl/foundation/validation.py:56-126`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4datactl/foundation/validation.py#L56-L126)
- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 src/ga4datactl/foundation/validation.py:246-313`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4datactl/foundation/validation.py#L246-L313)

### Record 4: 0-5-1-admin-diagnostics

Website locator: `release-0-5-1`, adjacent comment `<!-- change-id: 0-5-1-admin-diagnostics -->`.
Original JSON position: 4. Accepted-page position: 4. Current website position: 3 (Before upgrading / ga4adminctl / bullet 1).

Placement: Moves ahead of the ordinary OAuth replacement record so potential breaks come first. Tool order remains Data before Admin.

Fact and action disposition: The bullet keeps sanitized protobuf parser diagnostics for request bodies, access reports, and change history. It keeps using structured categories/exit codes rather than parsing SDK diagnostic prose. SDK receives a brief definition. The nearby release caveat keeps the lack of an established strict public diagnostic-text guarantee.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-1-admin-diagnostics",
  "category": "Fixed",
  "text": "GA4 Admin sanitizes protobuf parser diagnostics for request bodies, access reports, and change history.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "potential",
  "action": "Use structured error categories and exit codes instead of parsing SDK diagnostic prose.",
  "evidence": [
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "src/ga4adminctl/foundation/validation.py",
      "lines": "128-138"
    },
    {
      "commit": "9a2053dcb27dfd2b548785acec1c3299bf9067b5",
      "path": "src/ga4adminctl/operations/access.py",
      "lines": "26-88"
    }
  ]
}
```

Evidence destinations:

- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 src/ga4adminctl/foundation/validation.py:128-138`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4adminctl/foundation/validation.py#L128-L138)
- [`9a2053dcb27dfd2b548785acec1c3299bf9067b5 src/ga4adminctl/operations/access.py:26-88`](https://github.com/en-ver/marketing-toolbox/blob/9a2053dcb27dfd2b548785acec1c3299bf9067b5/src/ga4adminctl/operations/access.py#L26-L88)

<a id="release-0-5-0"></a>

## 0.5.0

Website section: [release 0.5.0](https://marketing-toolbox.org/changelog/#release-0-5-0). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-5-0`.

### Accepted release metadata

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

### Published historical witness

```json
{
  "tag": "v0.5.0",
  "release_id": 421798160,
  "url": "https://github.com/en-ver/marketing-toolbox/releases/tag/v0.5.0",
  "tag_object": "655d5f76818484b143bd5027df43eb2e4a3d53c5",
  "target_commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
  "body_sha256": "d1d6c0608ffdd5216768da47cb319a42bfc5bb07bb044a82f8fb66705f4b63c9",
  "body_byte_parity": true,
  "draft": false,
  "prerelease": false,
  "assets": 0,
  "operation": "created",
  "create_exit": 0
}
```

The ledger body hash is for decoded UTF-8 body bytes, without newline normalization. It is not a hash of the rewritten website section.

### Editorial mapping

Dates and date bases remain visible. The page-wide retrospective notice replaces repeated per-release status labels.
Both upstream-availability and internal-namespace caveats remain below the ordinary change.

### Record 1: 0-5-0-removed-commands

Website locator: `release-0-5-0`, adjacent comment `<!-- change-id: 0-5-0-removed-commands -->`.
Original JSON position: 1. Accepted-page position: 1. Current website position: 1 (Before upgrading / gtmctl / bullet 1).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps both full removed command paths and the explicit absence of a CLI replacement. It puts stopping those invocations first. The release caveat retains the documentation-only upstream rationale and unverified current API availability.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-0-removed-commands",
  "category": "Changed",
  "text": "GTM removes accounts containers combine and accounts containers move-tag-id.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Stop invoking these commands. This CLI provides no replacement.",
  "evidence": [
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/commands/accounts.py",
      "lines": "9-50"
    }
  ]
}
```

Evidence destinations:

- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/commands/accounts.py:9-50`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/accounts.py#L9-L50)

### Record 2: 0-5-0-mutation-transport

Website locator: `release-0-5-0`, adjacent comment `<!-- change-id: 0-5-0-mutation-transport -->`.
Original JSON position: 2. Accepted-page position: 4. Current website position: 3 (Before upgrading / gtmctl / bullet 3).

Placement: Moves ahead of the ordinary help record so confirmed breaks come first. Relative order among these Fixed records is preserved.

Fact and action disposition: The bullet keeps disabled automatic refresh replay, redirects, and request retries, separate initial credential refresh, and the 60-second connect/read timeout rather than a total deadline. It keeps network/HTTP 5xx uncertain-retry handling with exit 1/unexpected, inspection before retry, and the HTTP 429 retryable exception. It defines refresh replay.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-0-mutation-transport",
  "category": "Fixed",
  "text": "GTM mutations disable automatic refresh replay, redirects, and request retries. Initial credential refresh remains separate. The 60-second connect/read timeout is not a total deadline.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Inspect GTM state before retrying mutation network or HTTP 5xx failures, which now report exit 1/unexpected. HTTP 429 remains retryable.",
  "evidence": [
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/operations/mutation_transport.py",
      "lines": "20-97"
    },
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/foundation/errors.py",
      "lines": "30-107"
    }
  ]
}
```

Evidence destinations:

- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/operations/mutation_transport.py:20-97`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/operations/mutation_transport.py#L20-L97)
- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/foundation/errors.py:30-107`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/foundation/errors.py#L30-L107)

### Record 3: 0-5-0-mtls

Website locator: `release-0-5-0`, adjacent comment `<!-- change-id: 0-5-0-mtls -->`.
Original JSON position: 3. Accepted-page position: 2. Current website position: 2 (Before upgrading / gtmctl / bullet 2).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps mutation-only transport scope, accepted auto/never modes, rejected always mode, no automatic client-certificate discovery, and unchanged read transport. It puts supported configuration or a separately reviewed alternative first and explicitly prohibits weakening required certificate protections. It defines mutual TLS without promising support beyond the accepted modes.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-0-mtls",
  "category": "Changed",
  "text": "GTM mutation transport accepts mutual TLS (mTLS) endpoint modes auto and never, rejects always, and does not discover client certificates automatically. Read transport remains unchanged.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Use a supported mutation configuration or a separately reviewed alternative. Do not weaken required certificate protections to bypass this restriction.",
  "evidence": [
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/operations/mutation_transport.py",
      "lines": "20-97"
    }
  ]
}
```

Evidence destinations:

- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/operations/mutation_transport.py:20-97`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/operations/mutation_transport.py#L20-L97)

### Record 4: 0-5-0-selectors

Website locator: `release-0-5-0`, adjacent comment `<!-- change-id: 0-5-0-selectors -->`.
Original JSON position: 4. Accepted-page position: 5. Current website position: 4 (Before upgrading / gtmctl / bullet 4).

Placement: Moves ahead of the ordinary help record so confirmed breaks come first. Relative order among these Fixed records is preserved.

Fact and action disposition: The bullet keeps exactly one --destination-id/--tag-id selector for container lookup and per-method bundled Discovery enum validation for built-in-variable mutations. It keeps the action to supply supported types and the omitted-type exception for Revert. The definition of enum replaces jargon, not the method-specific constraint.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-0-selectors",
  "category": "Fixed",
  "text": "GTM container lookup requires exactly one of --destination-id or --tag-id. Built-in-variable mutations reject types outside each method's bundled Discovery enum.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Supply one container selector and method-supported variable types. Revert still permits an omitted type.",
  "evidence": [
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/commands/accounts.py",
      "lines": "349-377"
    },
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/commands/built_in_variable_mutations.py",
      "lines": "17-62"
    }
  ]
}
```

Evidence destinations:

- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/commands/accounts.py:349-377`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/accounts.py#L349-L377)
- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/commands/built_in_variable_mutations.py:17-62`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/built_in_variable_mutations.py#L17-L62)

### Record 5: 0-5-0-gtag-envelope

Website locator: `release-0-5-0`, adjacent comment `<!-- change-id: 0-5-0-gtag-envelope -->`.
Original JSON position: 5. Accepted-page position: 6. Current website position: 5 (Before upgrading / gtmctl / bullet 5).

Placement: Moves ahead of the ordinary help record so confirmed breaks come first. Relative order among these Fixed records is preserved.

Fact and action disposition: The bullet keeps gtag-config in mutation envelope command fields and its agreement with the command path. It keeps gtag_config in API resource and dry-run operation names. The action identifies exactly which fields scripts must match. The response-wrapper explanation defines envelope.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-5-0-gtag-envelope",
  "category": "Fixed",
  "text": "GTM mutation envelopes use gtag-config to match the command path. API resource and dry-run operation names retain gtag_config.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Match gtag-config in envelope command fields. Retain gtag_config where the API or dry-run operation requires it.",
  "evidence": [
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/commands/tag_mutations.py",
      "lines": "84-187"
    }
  ]
}
```

Evidence destinations:

- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/commands/tag_mutations.py:84-187`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/tag_mutations.py#L84-L187)

### Record 6: 0-5-0-version-warning

Website locator: `release-0-5-0`, adjacent comment `<!-- change-id: 0-5-0-version-warning -->`.
Original JSON position: 6. Accepted-page position: 3. Current website position: 6 (Other changes / gtmctl / bullet 1).

Placement: Moved to Other changes after all confirmed breaks.

Fact and action disposition: The ordinary-change bullet keeps the create-version help change, deletion of the source workspace, setting of the new base version, and the already-existing acknowledgement requirement. No separate action existed in the accepted record. The none assessment remains audit-only and is not a safety guarantee.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action field is absent and remains absent in this witness.

Accepted record (unchanged values):

```json
{
  "id": "0-5-0-version-warning",
  "category": "Changed",
  "text": "GTM create-version help explains that the operation deletes the source workspace and sets the new base version. The acknowledgement requirement already existed.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "cd5bc653e405528461bbc1e42dbe6ffe5841af8b",
      "path": "src/gtmctl/commands/workspace_operations.py",
      "lines": "179-190"
    }
  ]
}
```

Evidence destinations:

- [`cd5bc653e405528461bbc1e42dbe6ffe5841af8b src/gtmctl/commands/workspace_operations.py:179-190`](https://github.com/en-ver/marketing-toolbox/blob/cd5bc653e405528461bbc1e42dbe6ffe5841af8b/src/gtmctl/commands/workspace_operations.py#L179-L190)

<a id="release-0-4-0"></a>

## 0.4.0

Website section: [release 0.4.0](https://marketing-toolbox.org/changelog/#release-0-4-0). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-4-0`.

### Accepted release metadata

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

### Published historical witness

```json
{
  "tag": "v0.4.0",
  "release_id": 421798117,
  "url": "https://github.com/en-ver/marketing-toolbox/releases/tag/v0.4.0",
  "tag_object": "5d79540419310b305be813b61194256da2aef34b",
  "target_commit": "d59a8222149ec385dce26652f3246d5f025e7168",
  "body_sha256": "6cd99226bf79873badd3d11b4a76f9a211f85aa62e3596bc0decfb504c230802",
  "body_byte_parity": true,
  "draft": false,
  "prerelease": false,
  "assets": 0,
  "operation": "created",
  "create_exit": 0
}
```

The ledger body hash is for decoded UTF-8 body bytes, without newline normalization. It is not a hash of the rewritten website section.

### Editorial mapping

Dates and date bases remain visible. The page-wide retrospective notice replaces repeated per-release status labels.
The accepted caveat list is empty. No historical runtime or compatibility assurance is added.

### Record 1: 0-4-0-confirm-resource

Website locator: `release-0-4-0`, adjacent comment `<!-- change-id: 0-4-0-confirm-resource -->`.
Original JSON position: 1. Accepted-page position: 1. Current website position: 1 (Before upgrading / ga4adminctl / bullet 1).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps nine destructive Admin commands, exact --confirm-resource/--name equality for apply, and matching any supplied dry-run confirmation. It puts adding the exact resource confirmation first and keeps the existing sensitive-secret acknowledgements.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-4-0-confirm-resource",
  "category": "Changed",
  "text": "Nine destructive GA4 Admin commands require --confirm-resource to exactly match --name for apply. Any confirmation supplied during dry-run must also match.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "confirmed",
  "action": "Add --confirm-resource with the exact resource name to destructive apply scripts. Keep existing sensitive-secret acknowledgements.",
  "evidence": [
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "src/ga4adminctl/commands/_common.py",
      "lines": "75-84"
    },
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "tests/test_ga4_admin_command_tree.py",
      "lines": "159-216"
    }
  ]
}
```

Evidence destinations:

- [`d59a8222149ec385dce26652f3246d5f025e7168 src/ga4adminctl/commands/_common.py:75-84`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/commands/_common.py#L75-L84)
- [`d59a8222149ec385dce26652f3246d5f025e7168 tests/test_ga4_admin_command_tree.py:159-216`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/tests/test_ga4_admin_command_tree.py#L159-L216)

### Record 2: 0-4-0-patch-bodies

Website locator: `release-0-4-0`, adjacent comment `<!-- change-id: 0-4-0-patch-bodies -->`.
Original JSON position: 2. Accepted-page position: 2. Current website position: 2 (Before upgrading / ga4adminctl / bullet 2).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps child-patch body leaves matching normalized update-mask leaves, the mask-selected-body-only action, and explicit naming of every nested mask leaf. It defines leaf. It keeps help and sdk schema allowlists for eight patch targets, expressed as permitted fields.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-4-0-patch-bodies",
  "category": "Fixed",
  "text": "GA4 Admin child patches require body leaves to match normalized update-mask leaves. Help and sdk schema expose allowlists for eight patch targets.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "confirmed",
  "action": "Send only mask-selected body leaves. Name each nested update-mask leaf explicitly.",
  "evidence": [
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "src/ga4adminctl/operations/resources.py",
      "lines": "72-179"
    },
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "src/ga4adminctl/commands/sdk.py",
      "lines": "298-307"
    }
  ]
}
```

Evidence destinations:

- [`d59a8222149ec385dce26652f3246d5f025e7168 src/ga4adminctl/operations/resources.py:72-179`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/operations/resources.py#L72-L179)
- [`d59a8222149ec385dce26652f3246d5f025e7168 src/ga4adminctl/commands/sdk.py:298-307`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/commands/sdk.py#L298-L307)

### Record 3: 0-4-0-firebase-filter

Website locator: `release-0-4-0`, adjacent comment `<!-- change-id: 0-4-0-firebase-filter -->`.
Original JSON position: 3. Accepted-page position: 3. Current website position: 3 (Before upgrading / ga4adminctl / bullet 3).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps both exact filter forms and acceptance of valid account/property forms. It puts removing projects/ from Firebase project values first. No other filter form is removed.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-4-0-firebase-filter",
  "category": "Fixed",
  "text": "GA4 Admin property filters use firebase_project:<project-id-or-number> instead of firebase_project:projects/<project-id>. Valid account and property forms remain accepted.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "confirmed",
  "action": "Remove projects/ from Firebase project filter values.",
  "evidence": [
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "src/ga4adminctl/foundation/validation.py",
      "lines": "29-106"
    }
  ]
}
```

Evidence destinations:

- [`d59a8222149ec385dce26652f3246d5f025e7168 src/ga4adminctl/foundation/validation.py:29-106`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/foundation/validation.py#L29-L106)

### Record 4: 0-4-0-secret-alias

Website locator: `release-0-4-0`, adjacent comment `<!-- change-id: 0-4-0-secret-alias -->`.
Original JSON position: 4. Accepted-page position: 4. Current website position: 4 (Before upgrading / ga4adminctl / bullet 4).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet keeps Measurement Protocol secret creation, rejection of both secretValue and secret_value before authentication in both execution modes, and redaction of returned values. It puts omitting the output-only value and letting the server create it first.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-4-0-secret-alias",
  "category": "Fixed",
  "text": "GA4 Admin Measurement Protocol secret creation rejects both secretValue and secret_value before authentication in both execution modes. Returned secret values remain redacted.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "confirmed",
  "action": "Omit the output-only secret value and let the server create it.",
  "evidence": [
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "src/ga4adminctl/operations/secrets.py",
      "lines": "73-98"
    }
  ]
}
```

Evidence destinations:

- [`d59a8222149ec385dce26652f3246d5f025e7168 src/ga4adminctl/operations/secrets.py:73-98`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/operations/secrets.py#L73-L98)

### Record 5: 0-4-0-uncertain-create

Website locator: `release-0-4-0`, adjacent comment `<!-- change-id: 0-4-0-uncertain-create -->`.
Original JSON position: 5. Accepted-page position: 5. Current website position: 5 (Before upgrading / ga4adminctl / bullet 5).

Placement: Retains accepted-page relative order within its tool and priority set. Category headings are removed.

Fact and action disposition: The bullet explains non-idempotent creates as creates that are not safe to repeat. It keeps account-ticket provisioning, HTTP 500/503/504, uncertain completion, exit 1/unexpected, and the already-existing single-call writes. It puts inspecting state before retry and updating scripts that assumed safe retries first.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-4-0-uncertain-create",
  "category": "Fixed",
  "text": "GA4 Admin non-idempotent creates and account-ticket provisioning report HTTP 500/503/504 as uncertain completion with exit 1/unexpected. Single-call writes already existed.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "confirmed",
  "action": "Inspect current state before retrying uncertain creates. Update scripts that treated these failures as safely retryable.",
  "evidence": [
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "src/ga4adminctl/foundation/errors.py",
      "lines": "20-38"
    },
    {
      "commit": "d59a8222149ec385dce26652f3246d5f025e7168",
      "path": "src/ga4adminctl/operations/mutations.py",
      "lines": "24-62"
    }
  ]
}
```

Evidence destinations:

- [`d59a8222149ec385dce26652f3246d5f025e7168 src/ga4adminctl/foundation/errors.py:20-38`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/foundation/errors.py#L20-L38)
- [`d59a8222149ec385dce26652f3246d5f025e7168 src/ga4adminctl/operations/mutations.py:24-62`](https://github.com/en-ver/marketing-toolbox/blob/d59a8222149ec385dce26652f3246d5f025e7168/src/ga4adminctl/operations/mutations.py#L24-L62)

<a id="release-0-3-1"></a>

## 0.3.1

Website section: [release 0.3.1](https://marketing-toolbox.org/changelog/#release-0-3-1). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-3-1`.

### Accepted release metadata

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

### Published historical witness

```json
{
  "tag": "v0.3.1",
  "release_id": 421798056,
  "url": "https://github.com/en-ver/marketing-toolbox/releases/tag/v0.3.1",
  "tag_object": "84a7e5ad04559154a87937118ee7efaec386f769",
  "target_commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
  "body_sha256": "1e6770625ab26f5f6c0af4d58c07a4fa746e8b650021990a68fd5d4475e3e497",
  "body_byte_parity": true,
  "draft": false,
  "prerelease": false,
  "assets": 0,
  "operation": "created",
  "create_exit": 0
}
```

The ledger body hash is for decoded UTF-8 body bytes, without newline normalization. It is not a hash of the rewritten website section.

### Editorial mapping

The date remains visible with its tag basis. Confirmed-breaking warnings precede ordinary Data and umbrella-only changes. The shared credential warning affects all four packages. The page-wide retrospective notice replaces repeated status labels.

### Record 1: 0-3-1-audience-create

Website locator: `release-0-3-1`, adjacent comment `<!-- change-id: 0-3-1-audience-create -->`.
Original JSON position: 1. Accepted-page position: 2. Current website position: 2 (Before upgrading / ga4datactl).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains audience-export creation, disabled automatic retries, ambiguous server failures, uncertain completion, exit 1/unexpected, and the earlier retryable classification. Inspecting existing exports before retry and handling the changed exit/category are the leading actions.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-3-1-audience-create",
  "category": "Fixed",
  "text": "GA4 Data audience-export creation disables automatic retries and reports ambiguous server failures as uncertain completion with exit 1/unexpected.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl"
  ],
  "breaking": "confirmed",
  "action": "Inspect existing exports before retrying an uncertain create. Handle exit 1 instead of the earlier retryable classification.",
  "evidence": [
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "src/ga4datactl/operations/audience_exports.py",
      "lines": "183-227"
    },
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "src/ga4datactl/foundation/errors.py",
      "lines": "31-59"
    }
  ]
}
```

Evidence destinations:

- [`449a5822fc13a104ac1f8524ff04e9248593f914 src/ga4datactl/operations/audience_exports.py:183-227`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/operations/audience_exports.py#L183-L227)
- [`449a5822fc13a104ac1f8524ff04e9248593f914 src/ga4datactl/foundation/errors.py:31-59`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/foundation/errors.py#L31-L59)

### Record 2: 0-3-1-report-bounds

Website locator: `release-0-3-1`, adjacent comment `<!-- change-id: 0-3-1-report-bounds -->`.
Original JSON position: 2. Accepted-page position: 3. Current website position: 3 (Before upgrading / ga4datactl).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains nonempty batch requests, named pivot fields, bounds on pivot and realtime limit strings, and the exact audience-export query offset range 0..9223372036854775807. Keeps supplying requests/names and using documented limits. The existing 250000 ceiling is explicit, supported by the accepted early-history ledger's report/query-bounds entry. No new limit is inferred.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-3-1-report-bounds",
  "category": "Fixed",
  "text": "GA4 Data rejects empty batches and unnamed pivot fields. It bounds pivot and realtime limit strings and restricts audience-export query offsets to 0..9223372036854775807.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl"
  ],
  "breaking": "confirmed",
  "action": "Supply batch requests and pivot names. Keep limits within documented bounds and offsets within the accepted range.",
  "evidence": [
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "src/ga4datactl/schemas.py",
      "lines": "14-120"
    },
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "src/ga4datactl/foundation/validation.py",
      "lines": "122-130"
    }
  ]
}
```

Evidence destinations:

- [`449a5822fc13a104ac1f8524ff04e9248593f914 src/ga4datactl/schemas.py:14-120`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/schemas.py#L14-L120)
- [`449a5822fc13a104ac1f8524ff04e9248593f914 src/ga4datactl/foundation/validation.py:122-130`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/foundation/validation.py#L122-L130)

### Record 3: 0-3-1-request-discovery

Website locator: `release-0-3-1`, adjacent comment `<!-- change-id: 0-3-1-request-discovery -->`.
Original JSON position: 3. Accepted-page position: 4. Current website position: 4 (Other changes / ga4datactl).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains omission of forbidden nested property routing fields from batch SDK descriptors. Retains request construction before credential lookup for reports and audience exports. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-1-request-discovery",
  "category": "Fixed",
  "text": "GA4 Data batch SDK descriptors omit nested property routing fields that request bodies forbid. Report and audience-export request construction precedes credential lookup.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "src/ga4datactl/commands/sdk.py",
      "lines": "42-72"
    },
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "src/ga4datactl/operations/reports.py",
      "lines": "148-264"
    }
  ]
}
```

Evidence destinations:

- [`449a5822fc13a104ac1f8524ff04e9248593f914 src/ga4datactl/commands/sdk.py:42-72`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/commands/sdk.py#L42-L72)
- [`449a5822fc13a104ac1f8524ff04e9248593f914 src/ga4datactl/operations/reports.py:148-264`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/ga4datactl/operations/reports.py#L148-L264)

### Record 4: 0-3-1-empty-credentials

Website locator: `release-0-3-1`, adjacent comment `<!-- change-id: 0-3-1-empty-credentials -->`.
Original JSON position: 4. Accepted-page position: 1. Current website position: 1 (Before upgrading / Shared changes).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains failure of explicitly empty credential variables rather than fallback to another source. Unsetting both named unused variables leads the warning. Membership remains all four packages, not Data only.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-3-1-empty-credentials",
  "category": "Fixed",
  "text": "Explicit empty credential environment variables fail instead of falling through to another credential source.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Unset unused GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_APPLICATION_CREDENTIALS variables instead of assigning empty strings.",
  "evidence": [
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "src/marketing_common/auth.py",
      "lines": "30-136"
    },
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "tests/test_oauth.py",
      "lines": "179-222"
    }
  ]
}
```

Evidence destinations:

- [`449a5822fc13a104ac1f8524ff04e9248593f914 src/marketing_common/auth.py:30-136`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/src/marketing_common/auth.py#L30-L136)
- [`449a5822fc13a104ac1f8524ff04e9248593f914 tests/test_oauth.py:179-222`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/tests/test_oauth.py#L179-L222)

### Record 5: 0-3-1-archive-exclusions

Website locator: `release-0-3-1`, adjacent comment `<!-- change-id: 0-3-1-archive-exclusions -->`.
Original JSON position: 5. Accepted-page position: 5. Current website position: 5 (Other changes / marketing-toolbox).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains source-archive exclusion of dist and .release-build-* output directories. The umbrella-only bullet makes no claim about launcher archive contents. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-1-archive-exclusions",
  "category": "Fixed",
  "text": "The marketing-toolbox source archive excludes dist and .release-build-* output directories.",
  "packages": [
    "marketing-toolbox"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "449a5822fc13a104ac1f8524ff04e9248593f914",
      "path": "pyproject.toml",
      "lines": "35-36"
    }
  ]
}
```

Evidence destinations:

- [`449a5822fc13a104ac1f8524ff04e9248593f914 pyproject.toml:35-36`](https://github.com/en-ver/marketing-toolbox/blob/449a5822fc13a104ac1f8524ff04e9248593f914/pyproject.toml#L35-L36)

<a id="release-0-3-0"></a>

## 0.3.0

Website section: [release 0.3.0](https://marketing-toolbox.org/changelog/#release-0-3-0). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-3-0`.

### Accepted release metadata

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

### Published historical witness

```json
{
  "tag": "v0.3.0",
  "release_id": 421797996,
  "url": "https://github.com/en-ver/marketing-toolbox/releases/tag/v0.3.0",
  "tag_object": "571f37b6c10d39ffde93598e9a68f6ae23308f93",
  "target_commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
  "body_sha256": "474c02c900aae52c9ef19141bf732f2580edb78896abe7f9f3e76f780d88279f",
  "body_byte_parity": true,
  "draft": false,
  "prerelease": false,
  "assets": 0,
  "operation": "created",
  "create_exit": 0
}
```

The ledger body hash is for decoded UTF-8 body bytes, without newline normalization. It is not a hash of the rewritten website section.

### Editorial mapping

The date remains September 30 in the recorded +03:00 offset. The qualified no-break assessment, Hugo attribution, exclusion of later VitePress changes, and unverified site publication remain visible. The page-wide retrospective notice replaces repeated status labels.

### Record 1: 0-3-0-help

Website locator: `release-0-3-0`, adjacent comment `<!-- change-id: 0-3-0-help -->`.
Original JSON position: 1. Accepted-page position: 2. Current website position: 2 (Shared changes).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains root and authentication help, command discovery, credential precedence, JSON streams, and access tiers. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-0-help",
  "category": "Changed",
  "text": "Root and authentication help explain command discovery, credential precedence, JSON streams, and access tiers.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "src/marketing_common/cli.py",
      "lines": "14-33"
    },
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "src/marketing_common/oauth_cli.py",
      "lines": "24-44"
    }
  ]
}
```

Evidence destinations:

- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a src/marketing_common/cli.py:14-33`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/marketing_common/cli.py#L14-L33)
- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a src/marketing_common/oauth_cli.py:24-44`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/marketing_common/oauth_cli.py#L24-L44)

### Record 2: 0-3-0-gtm-planning-help

Website locator: `release-0-3-0`, adjacent comment `<!-- change-id: 0-3-0-gtm-planning-help -->`.
Original JSON position: 2. Accepted-page position: 5. Current website position: 5 (gtmctl).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains offline dry-run planning as distinct from API/response validation. This remains a clarification of existing behavior, not new enforcement. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-0-gtm-planning-help",
  "category": "Changed",
  "text": "GTM help distinguishes offline dry-run planning from API and response validation. This clarifies existing behavior.",
  "packages": [
    "marketing-toolbox",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "src/gtmctl/commands/_common.py",
      "lines": "14-18"
    }
  ]
}
```

Evidence destinations:

- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a src/gtmctl/commands/_common.py:14-18`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/gtmctl/commands/_common.py#L14-L18)

### Record 3: 0-3-0-data-schema

Website locator: `release-0-3-0`, adjacent comment `<!-- change-id: 0-3-0-data-schema -->`.
Original JSON position: 3. Accepted-page position: 3. Current website position: 3 (ga4datactl).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains all six report commands, standalone --schema output without credentials, and structural JSON Schema distinct from the installed SDK request descriptor. Request shape defines structural schema without claiming full API validation. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-0-data-schema",
  "category": "Added",
  "text": "All six GA4 Data report commands expose standalone --schema output without credentials. This structural JSON Schema differs from the installed SDK request descriptor.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "src/ga4datactl/commands/reports.py",
      "lines": "18-51"
    },
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "tests/test_cli.py",
      "lines": "469-490"
    }
  ]
}
```

Evidence destinations:

- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a src/ga4datactl/commands/reports.py:18-51`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/ga4datactl/commands/reports.py#L18-L51)
- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a tests/test_cli.py:469-490`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/tests/test_cli.py#L469-L490)

### Record 4: 0-3-0-admin-schema

Website locator: `release-0-3-0`, adjacent comment `<!-- change-id: 0-3-0-admin-schema -->`.
Original JSON position: 4. Accepted-page position: 4. Current website position: 4 (ga4adminctl).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains property-patch help and sdk schema, the existing four-field update-mask allowlist, and exact-body constraint. Defines allowlist as permitted fields without claiming a new mask policy. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-0-admin-schema",
  "category": "Changed",
  "text": "GA4 Admin property-patch help and sdk schema expose the existing four-field update-mask allowlist and exact-body constraint.",
  "packages": [
    "marketing-toolbox",
    "ga4adminctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "src/ga4adminctl/operations/properties.py",
      "lines": "40-45"
    },
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "src/ga4adminctl/commands/sdk.py",
      "lines": "269-279"
    }
  ]
}
```

Evidence destinations:

- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a src/ga4adminctl/operations/properties.py:40-45`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/ga4adminctl/operations/properties.py#L40-L45)
- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a src/ga4adminctl/commands/sdk.py:269-279`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/src/ga4adminctl/commands/sdk.py#L269-L279)

### Record 5: 0-3-0-guides

Website locator: `release-0-3-0`, adjacent comment `<!-- change-id: 0-3-0-guides -->`.
Original JSON position: 5. Accepted-page position: 1. Current website position: 1 (Shared changes).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains guides for installation, authentication, three command families, pagination, output, and dry-run limits. The release caveat keeps Hugo, exclusion of later VitePress changes, and unverified site publication visible. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-0-guides",
  "category": "Added",
  "text": "User guides cover installation, authentication, the three command families, pagination, output, and dry-run limits.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "07482bf82c4abd26146b4e6f3b91ca3d4980452f",
      "path": "docs/user/_index.md",
      "lines": "6-18"
    },
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "docs/user/tools/_index.md",
      "lines": "26-38"
    }
  ]
}
```

Evidence destinations:

- [`07482bf82c4abd26146b4e6f3b91ca3d4980452f docs/user/_index.md:6-18`](https://github.com/en-ver/marketing-toolbox/blob/07482bf82c4abd26146b4e6f3b91ca3d4980452f/docs/user/_index.md#L6-L18)
- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a docs/user/tools/_index.md:26-38`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/docs/user/tools/_index.md#L26-L38)

### Record 6: 0-3-0-source-archive

Website locator: `release-0-3-0`, adjacent comment `<!-- change-id: 0-3-0-source-archive -->`.
Original JSON position: 6. Accepted-page position: 6. Current website position: 6 (marketing-toolbox).

Placement: Retains accepted-page position. Category headings are removed.

Fact and action disposition: Retains exclusion of Hugo and user-site inputs from the marketing-toolbox source archive. Does not broaden affected packages or attribute VitePress to this release. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-3-0-source-archive",
  "category": "Changed",
  "text": "The marketing-toolbox source archive excludes Hugo and user-site inputs.",
  "packages": [
    "marketing-toolbox"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "944aa9f0d31bbec8b602eefdce4b7241c45bca5a",
      "path": "pyproject.toml",
      "lines": "35-36"
    }
  ]
}
```

Evidence destinations:

- [`944aa9f0d31bbec8b602eefdce4b7241c45bca5a pyproject.toml:35-36`](https://github.com/en-ver/marketing-toolbox/blob/944aa9f0d31bbec8b602eefdce4b7241c45bca5a/pyproject.toml#L35-L36)

<a id="release-0-2-0"></a>

## 0.2.0

Website section: [release 0.2.0](https://marketing-toolbox.org/changelog/#release-0-2-0). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-2-0`.

### Accepted release metadata

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

### Published historical witness

```json
{
  "tag": "v0.2.0",
  "release_id": 421797935,
  "url": "https://github.com/en-ver/marketing-toolbox/releases/tag/v0.2.0",
  "tag_object": "2890f12a63fa5311fdcc1b8c6db615d4300156c1",
  "target_commit": "d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb",
  "body_sha256": "16e49ab538a4795d9a56d7c643bf6549495e55d7a738ff002e6a2ed3c7119473",
  "body_byte_parity": true,
  "draft": false,
  "prerelease": false,
  "assets": 0,
  "operation": "created",
  "create_exit": 0
}
```

The ledger body hash is for decoded UTF-8 body bytes, without newline normalization. It is not a hash of the rewritten website section.

### Editorial mapping

The date remains visible with its tag basis. The confirmed exit-code warning precedes the potential credential-identity warning and ordinary OAuth additions. Retrospective OAuth/ADC attribution, the 0.1.0 feature manifest, and subsequent 0.2.0 bump remain visible.

### Record 1: 0-2-0-auth

Website locator: `release-0-2-0`, adjacent comment `<!-- change-id: 0-2-0-auth -->`.
Original JSON position: 1. Accepted-page position: 1. Current website position: 3 (Other changes / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains all four native auth commands and exact credential order: inline service accounts, explicit files, matching native records, then ADC. ADC is expanded in the introduction. The release caveat retains retrospective OAuth/ADC attribution across the 0.1.0 feature manifest and 0.2.0 bump. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-2-0-auth",
  "category": "Added",
  "text": "Native OAuth adds auth login, status, forget, and revoke. Credential selection uses inline service accounts, explicit files, matching native records, then Application Default Credentials (ADC).",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "src/marketing_common/auth.py",
      "lines": "81-137"
    },
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "src/marketing_common/oauth_cli.py",
      "lines": "24-162"
    }
  ]
}
```

Evidence destinations:

- [`ebed104a65d1712403bac5b80bf6d0350f89b511 src/marketing_common/auth.py:81-137`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/auth.py#L81-L137)
- [`ebed104a65d1712403bac5b80bf6d0350f89b511 src/marketing_common/oauth_cli.py:24-162`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth_cli.py#L24-L162)

### Record 2: 0-2-0-native-setup

Website locator: `release-0-2-0`, adjacent comment `<!-- change-id: 0-2-0-native-setup -->`.
Original JSON position: 2. Accepted-page position: 2. Current website position: 4 (Other changes / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains Desktop client, tool-specific access tiers, approved encrypted operating-system keyring storage, and the --port requirement with --no-open-browser. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-2-0-native-setup",
  "category": "Added",
  "text": "Native OAuth uses a Desktop client, tool-specific access tiers, and approved encrypted OS keyring storage. --no-open-browser requires --port.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "src/marketing_common/oauth.py",
      "lines": "78-138"
    },
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "src/marketing_common/oauth.py",
      "lines": "626-662"
    }
  ]
}
```

Evidence destinations:

- [`ebed104a65d1712403bac5b80bf6d0350f89b511 src/marketing_common/oauth.py:78-138`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth.py#L78-L138)
- [`ebed104a65d1712403bac5b80bf6d0350f89b511 src/marketing_common/oauth.py:626-662`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth.py#L626-L662)

### Record 3: 0-2-0-auth-lifecycle

Website locator: `release-0-2-0`, adjacent comment `<!-- change-id: 0-2-0-auth-lifecycle -->`.
Original JSON position: 3. Accepted-page position: 3. Current website position: 5 (Other changes / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains local-record-only forget and project-grant scope of revoke, with both required flags. These are limits of added commands, not removed earlier functionality. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-2-0-auth-lifecycle",
  "category": "Added",
  "text": "auth forget removes a local record only. auth revoke requires --apply and --acknowledge-project-wide-revocation because it affects the OAuth project grant.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "src/marketing_common/oauth_cli.py",
      "lines": "105-160"
    }
  ]
}
```

Evidence destinations:

- [`ebed104a65d1712403bac5b80bf6d0350f89b511 src/marketing_common/oauth_cli.py:105-160`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/oauth_cli.py#L105-L160)

### Record 4: 0-2-0-credential-fallback

Website locator: `release-0-2-0`, adjacent comment `<!-- change-id: 0-2-0-credential-fallback -->`.
Original JSON position: 4. Accepted-page position: 4. Current website position: 2 (Before upgrading / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Keeps selected-invalid-source failure separate from ambient ADC fallback. Retains the risk that previously credential-missing commands now authenticate. Reviewing precedence before automation and selecting an explicit source for fixed identity lead the potential-breaking warning. Membership remains all four packages.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-2-0-credential-fallback",
  "category": "Changed",
  "text": "A selected invalid credential source fails instead of switching identity. New ambient ADC fallback can authenticate commands that previously lacked credentials.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "potential",
  "action": "Review credential precedence before automation. Use an explicit credential source when a fixed identity is required.",
  "evidence": [
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "src/marketing_common/auth.py",
      "lines": "81-137"
    },
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "tests/test_oauth.py",
      "lines": "74-118"
    }
  ]
}
```

Evidence destinations:

- [`ebed104a65d1712403bac5b80bf6d0350f89b511 src/marketing_common/auth.py:81-137`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/auth.py#L81-L137)
- [`ebed104a65d1712403bac5b80bf6d0350f89b511 tests/test_oauth.py:74-118`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/tests/test_oauth.py#L74-L118)

### Record 5: 0-2-0-process-exit

Website locator: `release-0-2-0`, adjacent comment `<!-- change-id: 0-2-0-process-exit -->`.
Original JSON position: 5. Accepted-page position: 5. Current website position: 1 (Before upgrading / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains preservation of nonzero command exits by console entry points instead of erroneous zero. Handling nonzero failure codes and not treating the former zero as success lead the confirmed-breaking warning. No specific exit numbers are invented.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-2-0-process-exit",
  "category": "Fixed",
  "text": "Console entry points preserve nonzero command exit codes instead of returning an erroneous zero.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Handle nonzero failure codes in scripts. Do not treat the former zero exit as proof of success.",
  "evidence": [
    {
      "commit": "ebed104a65d1712403bac5b80bf6d0350f89b511",
      "path": "src/marketing_common/cli.py",
      "lines": "114-123"
    },
    {
      "commit": "d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb",
      "path": "tests/test_cli.py",
      "lines": "413-458"
    }
  ]
}
```

Evidence destinations:

- [`ebed104a65d1712403bac5b80bf6d0350f89b511 src/marketing_common/cli.py:114-123`](https://github.com/en-ver/marketing-toolbox/blob/ebed104a65d1712403bac5b80bf6d0350f89b511/src/marketing_common/cli.py#L114-L123)
- [`d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb tests/test_cli.py:413-458`](https://github.com/en-ver/marketing-toolbox/blob/d7db5d1d8f9d4c49d1d0285d50f7f40dc21cf5cb/tests/test_cli.py#L413-L458)

<a id="release-0-1-0"></a>

## 0.1.0

Website section: [release 0.1.0](https://marketing-toolbox.org/changelog/#release-0-1-0). Canonical source: [changelog Markdown](user/changelog/index.md), heading `release-0-1-0`.

### Accepted release metadata

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

No tag or GitHub Release exists for this untagged interval.

### Editorial mapping

The initial-source date remains September 23, not publication. Untagged status, September 24 packaging through the pre-OAuth boundary, original marketing-tools name, later package vocabulary, and 0.2.0 OAuth/ADC attribution remain visible. No tag or Release is invented. The obsolete filtering explanation remains only in accepted metadata as historical wording. Confirmed-breaking naming warnings precede ordinary initial functionality.

### Record 1: 0-1-0-commands

Website locator: `release-0-1-0`, adjacent comment `<!-- change-id: 0-1-0-commands -->`.
Original JSON position: 1. Accepted-page position: 1. Current website position: 3 (Other changes / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains Data reports/audience exports, Admin GA4 resource management, and GTM reads/changes. The introduction preserves original distribution naming and later package vocabulary. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-1-0-commands",
  "category": "Added",
  "text": "ga4datactl provides GA4 reports and audience exports, ga4adminctl manages GA4 resources, and gtmctl reads and changes GTM resources.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "4147871781c42a9e1539823f6f8e8ad1bd0e4b8f",
      "path": "README.md",
      "lines": "3-56"
    }
  ]
}
```

Evidence destinations:

- [`4147871781c42a9e1539823f6f8e8ad1bd0e4b8f README.md:3-56`](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/README.md#L3-L56)

### Record 2: 0-1-0-output

Website locator: `release-0-1-0`, adjacent comment `<!-- change-id: 0-1-0-output -->`.
Original JSON position: 2. Accepted-page position: 2. Current website position: 4 (Other changes / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains versioned JSON envelopes on stdout, diagnostics on stderr, explicit apply/dry-run controls for writes, and operation-specific acknowledgements. Response wrapper defines envelope without claiming full API validation. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-1-0-output",
  "category": "Added",
  "text": "Commands emit a versioned JSON envelope on stdout and diagnostics on stderr. Writes use explicit apply or dry-run controls and operation-specific acknowledgements.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "4147871781c42a9e1539823f6f8e8ad1bd0e4b8f",
      "path": "src/marketing_common/cli.py",
      "lines": "14-73"
    },
    {
      "commit": "4147871781c42a9e1539823f6f8e8ad1bd0e4b8f",
      "path": "src/gtmctl/commands/tag_mutations.py",
      "lines": "58-98"
    }
  ]
}
```

Evidence destinations:

- [`4147871781c42a9e1539823f6f8e8ad1bd0e4b8f src/marketing_common/cli.py:14-73`](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/src/marketing_common/cli.py#L14-L73)
- [`4147871781c42a9e1539823f6f8e8ad1bd0e4b8f src/gtmctl/commands/tag_mutations.py:58-98`](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/src/gtmctl/commands/tag_mutations.py#L58-L98)

### Record 3: 0-1-0-service-accounts

Website locator: `release-0-1-0`, adjacent comment `<!-- change-id: 0-1-0-service-accounts -->`.
Original JSON position: 3. Accepted-page position: 3. Current website position: 5 (Other changes / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains inline GOOGLE_SERVICE_ACCOUNT_JSON before a GOOGLE_APPLICATION_CREDENTIALS service-account file. Excludes native OAuth and ambient user ADC from this interval and points to their retrospective 0.2.0 attribution. No separate action was present.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The accepted record has no separate action field. No action is silently dropped.

Accepted record (unchanged values):

```json
{
  "id": "0-1-0-service-accounts",
  "category": "Added",
  "text": "Initial authentication supports inline GOOGLE_SERVICE_ACCOUNT_JSON before a GOOGLE_APPLICATION_CREDENTIALS service-account file. Native OAuth and ambient user ADC are outside this interval.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "none",
  "evidence": [
    {
      "commit": "4147871781c42a9e1539823f6f8e8ad1bd0e4b8f",
      "path": "src/marketing_common/auth.py",
      "lines": "20-74"
    }
  ]
}
```

Evidence destinations:

- [`4147871781c42a9e1539823f6f8e8ad1bd0e4b8f src/marketing_common/auth.py:20-74`](https://github.com/en-ver/marketing-toolbox/blob/4147871781c42a9e1539823f6f8e8ad1bd0e4b8f/src/marketing_common/auth.py#L20-L74)

### Record 4: 0-1-0-package-rename

Website locator: `release-0-1-0`, adjacent comment `<!-- change-id: 0-1-0-package-rename -->`.
Original JSON position: 4. Accepted-page position: 4. Current website position: 1 (Before upgrading / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains marketing-tools to marketing-toolbox, three thin launchers pinned to the same core version, all three commands from core, and no marketing-toolbox executable. Installing core or a named launcher is an action for earliest source, not a claim about verified published packages.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-1-0-package-rename",
  "category": "Changed",
  "text": "The distribution changes from marketing-tools to marketing-toolbox. Three thin launcher distributions pin the same core version. The core still installs all three commands.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "For the earliest source, install marketing-toolbox or a named launcher. There is no marketing-toolbox executable.",
  "evidence": [
    {
      "commit": "0530eb74b672fc65e29c136f51f7d1aabe1ad014",
      "path": "pyproject.toml",
      "lines": "5-31"
    },
    {
      "commit": "0530eb74b672fc65e29c136f51f7d1aabe1ad014",
      "path": "packaging/ga4datactl/pyproject.toml",
      "lines": "5-22"
    }
  ]
}
```

Evidence destinations:

- [`0530eb74b672fc65e29c136f51f7d1aabe1ad014 pyproject.toml:5-31`](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/pyproject.toml#L5-L31)
- [`0530eb74b672fc65e29c136f51f7d1aabe1ad014 packaging/ga4datactl/pyproject.toml:5-22`](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/packaging/ga4datactl/pyproject.toml#L5-L22)

### Record 5: 0-1-0-schema-identity

Website locator: `release-0-1-0`, adjacent comment `<!-- change-id: 0-1-0-schema-identity -->`.
Original JSON position: 5. Accepted-page position: 5. Current website position: 2 (Before upgrading / Shared changes).

Placement: Moves ahead of or behind upgrade warnings so confirmed breaks precede potential breaks and ordinary additions. Relative order within each priority/tool group is preserved.

Fact and action disposition: Retains schemaVersion marketing-tools/v1 to marketing-toolbox/v1 and schema URNs to urn:marketing-toolbox. Retains updating literal comparisons and Data schema-URN references. The introduction limits this to untagged initial history.

Field disposition: The original text, category, exact package membership, breaking assessment, and evidence remain below under the common audit-only rules. The original action is retained below and its full meaning stays visible in the mapped bullet.

Accepted record (unchanged values):

```json
{
  "id": "0-1-0-schema-identity",
  "category": "Changed",
  "text": "The initial rename changes schemaVersion from marketing-tools/v1 to marketing-toolbox/v1 and changes schema URNs to urn:marketing-toolbox.",
  "packages": [
    "marketing-toolbox",
    "ga4datactl",
    "ga4adminctl",
    "gtmctl"
  ],
  "breaking": "confirmed",
  "action": "Update scripts that compare the old schemaVersion literal. Update Data schema-URN references to the renamed identifiers.",
  "evidence": [
    {
      "commit": "0530eb74b672fc65e29c136f51f7d1aabe1ad014",
      "path": "src/marketing_common/cli.py",
      "lines": "14-40"
    },
    {
      "commit": "0530eb74b672fc65e29c136f51f7d1aabe1ad014",
      "path": "src/ga4datactl/schemas.py",
      "lines": "1-120"
    }
  ]
}
```

Evidence destinations:

- [`0530eb74b672fc65e29c136f51f7d1aabe1ad014 src/marketing_common/cli.py:14-40`](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/src/marketing_common/cli.py#L14-L40)
- [`0530eb74b672fc65e29c136f51f7d1aabe1ad014 src/ga4datactl/schemas.py:1-120`](https://github.com/en-ver/marketing-toolbox/blob/0530eb74b672fc65e29c136f51f7d1aabe1ad014/src/ga4datactl/schemas.py#L1-L120)

