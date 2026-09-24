# Releasing

The repository publishes four distributions from one lockstep release:

| Distribution | Manifest | Purpose |
| --- | --- | --- |
| `marketing-toolbox` | `pyproject.toml` | Shared implementation and all three entry points |
| `ga4datactl` | `packaging/ga4datactl/pyproject.toml` | GA4 Data launcher |
| `ga4adminctl` | `packaging/ga4adminctl/pyproject.toml` | GA4 Admin launcher |
| `gtmctl` | `packaging/gtmctl/pyproject.toml` | GTM launcher |

All four `project.version` values must be identical. The three launcher
projects also pin their dependency on the matching `marketing-toolbox` version.
Update all four manifests together, run `uv lock` so the workspace lockfile
reflects the new versions, and commit the resulting documentation and metadata
changes before tagging. The project is MIT-licensed; the root `LICENSE` file
and the package metadata are the source of that licensing information.

## Local validation and build

The release workflow uses the locked workspace and runs these checks before
building:

```bash
uv sync --locked --all-groups --all-packages
uv lock --check
uv run --locked --no-sync pytest
uv run --locked --no-sync ruff check .
uv run --locked --no-sync ruff format --check .
uv run --locked --no-sync mypy
```

Build all four distributions once, using the same offline/no-isolation mode as
the release workflow, and inspect every artifact:

```bash
uv build --all-packages --offline --no-build-isolation --no-python-downloads --clear --out-dir dist
uvx twine check dist/*
```

The build produces two artifacts per distribution (a wheel and a source
archive). Do not rebuild between validation and publication: the release job
uploads the artifacts from this single build.

## Sequential bootstrap process

PyPI pending publishers permit initial publication one project at a time.
Merge the workflow change to `main`, then repeat the following for each project
in this order: `marketing-toolbox`, `ga4datactl`, `ga4adminctl`, and `gtmctl`.

1. Configure the pending publisher for that exact PyPI project using the
   GitHub publisher values in [Trusted Publishing and GitHub setup](#trusted-publishing-and-github-setup).
2. In **Actions → Release → Run workflow**, select the `main` branch and enter
   the exact target and confirmation pair:

   | `publish_target` | `confirmation` |
   | --- | --- |
   | `marketing-toolbox` | `BOOTSTRAP-MARKETING-TOOLBOX` |
   | `ga4datactl` | `BOOTSTRAP-GA4DATACTL` |
   | `ga4adminctl` | `BOOTSTRAP-GA4ADMINCTL` |
   | `gtmctl` | `BOOTSTRAP-GTMCTL` |

3. Approve the protected `pypi` environment if required, then verify that the
   selected project has its wheel and sdist on PyPI before configuring and
   publishing the next project.

After all four projects are bootstrapped, create and push `v0.1.0` for the
normal all-package release.

The manual dispatch is deliberately constrained: it must run from `main`,
accepts exactly one of the four listed targets, and requires that target's
exact confirmation token. It stages and publishes only that target's one wheel
and one sdist, using the normalized artifact stem (`marketing_toolbox` for
`marketing-toolbox`). There is no manual all-package or untagged production
mode.

## Tag-triggered release

The release workflow is `.github/workflows/release.yml`. Pushing a tag matching
`v*.*.*` starts the normal release. Its build job:

1. checks out the tag;
2. verifies that the tag is exactly `v<version>` for all four manifests and
   that the four versions are synchronized;
3. runs the locked tests, lint, format, type, and lockfile checks;
4. builds all distributions once and runs `uvx twine check dist/*`; and
5. uploads only `dist/*.whl` and `dist/*.tar.gz` as one artifact.

The publish job downloads that single build artifact, stages the selected
artifacts, and invokes `pypa/gh-action-pypi-publish` once. A tag release stages
all eight artifacts (wheel and sdist for all four distributions); a manual
bootstrap stages only the selected project's two artifacts. The publish action
uses `skip-existing: true` so the tag run safely skips all files already
uploaded during bootstrap. Both modes run in the GitHub `pypi` environment and
use OIDC rather than a PyPI token stored in the repository.

## Trusted Publishing and GitHub setup

Configure a trusted publisher for **each** of these PyPI projects. Configure
each one as its pending publisher immediately before its corresponding manual
bootstrap run:

- `marketing-toolbox`
- `ga4datactl`
- `ga4adminctl`
- `gtmctl`

For each project, the GitHub publisher values are the `en-ver/marketing-toolbox`
repository, workflow file `.github/workflows/release.yml`, and environment
name `pypi`. The repository workflow grants `id-token: write` only to the
publish job; the build job has no publish credential.

Create the GitHub environment named `pypi` and protect it with the repository's
required approval rules (for example, required reviewers). The environment
name must remain exactly `pypi`, because it is part of the trusted-publisher
identity. GitHub repository public visibility is optional; the repository does
not need to be made public for this OIDC setup.

PyPI distribution names are globally unique and must match the names above
exactly. If a project does not exist yet, use PyPI's **pending publisher**
configuration for that exact name before the first release. If the name is
already owned or the project already exists, its owner must configure the
trusted publisher in that existing project instead; a pending publisher cannot
claim a conflicting name.

## Optional TestPyPI check

TestPyPI is optional and is not part of the current GitHub workflow. If a
TestPyPI rehearsal is needed, use the already-built `dist/` artifacts after
local validation, configure the corresponding four TestPyPI projects and
publisher or upload credentials, and publish to TestPyPI's index. Keep this
separate from the production `pypi` environment: TestPyPI has its own project
namespace, credentials, and trusted-publisher configuration. The production
workflow still publishes only to PyPI.
