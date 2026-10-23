# Releasing

The repository publishes four distributions in one lockstep release:

| Distribution | Manifest | Purpose |
| --- | --- | --- |
| `marketing-toolbox` | `pyproject.toml` | Shared implementation and all three entry points |
| `ga4datactl` | `packaging/ga4datactl/pyproject.toml` | GA4 Data launcher |
| `ga4adminctl` | `packaging/ga4adminctl/pyproject.toml` | GA4 Admin launcher |
| `gtmctl` | `packaging/gtmctl/pyproject.toml` | GTM launcher |

All four projects are published on PyPI and bootstrap is complete. Their
`project.version` values must remain identical, and each launcher must pin the
matching `marketing-toolbox` version. Update all four manifests together, run
`uv lock`, and commit the resulting metadata and documentation before tagging.
The project is MIT-licensed; the root `LICENSE` and package metadata are the
licensing sources.

## Validate and build

The release workflow uses the locked workspace and runs:

```bash
uv sync --locked --all-groups --all-packages
uv lock --check
uv run --locked --no-sync pytest
uv run --locked --no-sync ruff check .
uv run --locked --no-sync ruff format --check .
uv run --locked --no-sync mypy
```

Build all four distributions once, then inspect the eight artifacts:

```bash
uv build --all-packages --offline --no-build-isolation --no-python-downloads --clear --out-dir dist
uvx twine check dist/*
```

Do not rebuild between validation and publication. The workflow uploads the
wheel and source distribution for each project from this single build.

## Release notes

`docs/user/changelog/index.md` is the sole maintained source of user-facing
release prose. The same maintainer owns `docs/changelog-provenance.md`, the
maintained audit mapping, not a second editorial changelog or website route.
Update both together. Keep accepted JSON and original words as immutable
historical witnesses, not alternative maintained notes.

Start each release with a version-only H2 heading, newest first. Preserve the
explicit version anchor and each stable, non-rendered `change-id` comment
beside its bullet. These comments are internal identities, not public DOM
anchors or runtime data. Keep plain Markdown without new rendering machinery.
Show a bare ISO date below each heading, then a short non-enumerative summary
and relevant compatibility uncertainty. Keep all eight historical dates unchanged.
After the package explanation, keep one global historical notice and one
`Historical provenance` link to the maintained mapping. The notice states the
reconstruction sources and unverified original notes, PyPI publication dates,
and historical test results. It distinguishes tag dates from publication dates,
retains the 0.3.0 tag's +03:00 offset basis, and explains the untagged 0.1.0
initial-commit date and September 24 packaging interval. Keep release-specific
caveats visible. For future releases, use verified date facts and retain their
basis in provenance. Do not infer publication dates or historical test success
from tag dates or source assertions.

Put complete confirmed-breaking bullets first, potential-breaking bullets
second, and ordinary changes last. Keep inline `Breaking:` and
`Potential breaking change:` labels where warranted. Do not add visible
“Before upgrading” or “Other changes” headings.
State the required action before the risk or changed behavior. Keep every
user-facing fact, number, identifier, affected-tool meaning, warning, and limit
visible. Do not repeat facts or actions in summaries or other bullets.
Do not turn absence of an identified break into a compatibility guarantee.

Use H3 tool headings directly within each release. Within each priority band,
order groups as shared, `ga4datactl`, `ga4adminctl`, `gtmctl`, then
`marketing-toolbox` only. Omit empty groups. Repeat a tool heading only when
needed to preserve priority across bands. Never repeat its bullets or actions.
Explain lockstep membership once: a tool heading means that launcher and the
umbrella implementation. Launchers do not have separate release histories.
Show shared changes once. If only some launchers are affected, name them in
ordinary prose. Keep umbrella-only changes distinct. Preserve relative order
unless upgrade priority requires a move, and record the reason in provenance.
Do not require repeated `Packages:`, `Text:`, `Action:`, or `Evidence:` labels,
or an `Added`/`Changed`/`Fixed` hierarchy in human prose.

In provenance, retain original accepted words, categories, exact package lists,
breaking assessments, actions or their original absence, and every evidence
destination. Retain per-version dates and bases, retrospective notices,
caveats, naming and attribution, tag names/objects/timestamps with offsets,
targets, and exclusive/inclusive comparison boundaries. Retain verified
Release IDs, URLs, and body hashes. Map each record to its website section and
adjacent stable comment. Record original/current order, wording and placement
changes, and the disposition and reason for every audit-only field.
Only original phrasing and audit metadata leave the reading flow, never user
behavior or required actions. Use the global provenance link instead of
per-release provenance links. End each of the seven tagged historical sections
with one link labelled only with its tag, pointing to its verified GitHub Release.
Do not add separate tag-tree links. Keep 0.1.0 explicitly untagged, without a
Release footer or invented tag or Release. Retain its initial-source-commit
destination in provenance. Add a Release URL only after confirming that the
matching Release exists.

Historical website equivalence means factual and action equivalence, not exact
wording, visible metadata, or Markdown bytes. Human semantic review must account
for every accepted fact, action, scope, breaking strength, and uncertainty.
Keep all seven published GitHub bodies byte-identical to approved witnesses.
Their older wording, categories, and inline audit fields intentionally differ
from the rewritten website. Do not regenerate or overwrite them. Preserve
Release identities, flags, assets, latest designation, and tag identities.
Unexpected differences require parent resolution, not automatic repair.
Later published-note corrections require separate reconciliation authority and review.

For future unpublished releases, derive the proposed GitHub body from the
canonical human-oriented website section through a reviewed copy or one-off
temporary projection. Preserve every user-facing fact, warning, action,
uncertainty, and affected-tool meaning. Only heading depth, navigation, and
meaning-preserving Markdown adaptation can differ. Include an appropriate
source-controlled provenance link when evidence is separate. Carry relevant
global historical context into a standalone body through meaning-preserving
navigation adaptation. This does not require a three-link website footer.
Audit fields do not become mandatory inline body labels. Review the proposed
body before any separately authorized publication. Fetch and compare the body afterward.
If a Release already exists, read its tag identity and body first. Stop on an
unexpected difference. Creation permission does not permit an existing-body edit.
Do not add a permanent generator, parser, synchronization service, bundled
script, or release-policy CI gate.
Notes guidance does not grant tagging, publication, or recovery permission.

## Normal release

The `.github/workflows/release.yml` workflow publishes a tag matching
`v*.*.*`. It checks out the tag, verifies that it is exactly `v<version>` for
all four synchronized manifests, runs the locked checks above, builds once,
validates with Twine, and uploads only the eight wheel and source artifacts.

The publish job downloads that one build artifact and publishes all eight files
through PyPI Trusted Publishing in the protected `pypi` environment. It has the
only `id-token: write` permission; the build job has no publish credential. For
pre-tag bootstrap, the later synchronized tag run publishes the full set and
`skip-existing: true` skips matching filenames already published. It neither
reconciles different builds nor permits overwriting a PyPI version.

## Exceptional manual dispatch

Manual dispatch is only for pre-tag bootstrap of an unpublished target/version;
it is not a normal alternative to a synchronized tag release. After an
incomplete tagged release, prefer rerunning the original tagged workflow. Use
manual dispatch for that recovery only when current `main` exactly matches the
intended synchronized release and the selected target/version still has
unpublished artifacts.

In **Actions → Release → Run workflow**, select `main` and supply exactly one
target and its confirmation token:

| `publish_target` | `confirmation` |
| --- | --- |
| `marketing-toolbox` | `BOOTSTRAP-MARKETING-TOOLBOX` |
| `ga4datactl` | `BOOTSTRAP-GA4DATACTL` |
| `ga4adminctl` | `BOOTSTRAP-GA4ADMINCTL` |
| `gtmctl` | `BOOTSTRAP-GTMCTL` |

The workflow rejects other branches, targets, or token pairs. It stages exactly
one wheel and one source distribution for the selected target (using
`marketing_toolbox` as the root artifact stem) and publishes through the same
OIDC `pypi` environment. Only a pre-tag bootstrap is completed by a later
synchronized tag release; an incomplete tagged release is recovered as above.
`skip-existing` skips matching published filenames only: it cannot reconcile
different builds or replace a PyPI version.

## Trusted Publishing

Each of the four PyPI projects must retain a trusted publisher for the
`en-ver/marketing-toolbox` repository, `.github/workflows/release.yml`, and the
`pypi` environment. Keep the environment name exactly `pypi`, with the
repository's required approval rules, because it is part of the trusted
publisher identity. The workflow's pinned publisher action, protected
environment, branch restriction, target/token check, artifact-format checks,
and least-privilege permissions are release safeguards.

## Optional TestPyPI check

TestPyPI is not part of this workflow. If needed, use the already-built `dist/`
artifacts after local validation and configure separate TestPyPI projects and
publisher or upload credentials. Keep that rehearsal separate from production
PyPI and its `pypi` environment.
