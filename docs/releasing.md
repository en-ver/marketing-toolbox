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
