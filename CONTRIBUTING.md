# Contributing

## Setup

```bash
git clone https://github.com/en-ver/marketing-toolbox.git
cd marketing-toolbox
uv sync --locked --all-groups --all-packages
```

## Checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy

uv run ga4datactl --help
uv run ga4adminctl --help
uv run gtmctl --help
```

See [the architecture](docs/architecture.md) for source boundaries and
[releasing](docs/releasing.md) for maintainer release procedures. The four
distributions retain synchronized versions, and each launcher must pin the
matching `marketing-toolbox` version.

CLI help and runtime schemas, not prose catalogs, are authoritative. Put test
fixtures in `tests/fixtures/` and machine-readable inventories in `tests/data/`.
Dependency changes require lockfile validation; documentation-only changes
should not modify dependency or packaging metadata.

## User documentation site

The user documentation lives in `docs/user/`; `docs/architecture.md` and
`docs/releasing.md` remain repository-only. The site uses Hugo 0.166.0 and
Hugo Book v0.15.0 (`github.com/alex-shpak/hugo-book`), pinned by the root
`go.mod` and generated `go.sum`. Go 1.25 or later is required to resolve the
theme module.

Use the exact Hugo version to preview or build the site:

```bash
hugo server --disableFastRender
hugo --environment production --cleanDestinationDir --gc --minify --panicOnWarning
```

Author pages with only `title` and `weight` YAML front matter plus one explicit
body H1. Use ordinary relative `.md` links and verify them with the production
build; `BookPortableLinks = "error"` rejects unresolved local page and resource
links. Keep Hugo and theme upgrades deliberate paired changes: update their
pins, regenerate `go.sum`, and review the rendered site.

## GitHub Pages launch

`.github/workflows/docs-pages.yml` builds pull requests without deployment and
deploys only `main`. It does not configure GitHub Pages, domain ownership, or
DNS. Before the first approved deployment, a maintainer must:

1. In repository **Settings → Pages**, set **Build and deployment → Source** to
   **GitHub Actions**. In **Settings → Environments**, create or protect
   `github-pages` so only the `main` branch can deploy.
2. In the `en-ver` account's **Settings → Pages → Verified domains**, verify
   `marketing-toolbox.org` with the exact TXT record GitHub provides and retain
   that record. Do not invent or replace it with a placeholder value.
3. In repository **Settings → Pages**, set `marketing-toolbox.org` as the
   custom domain before directing DNS traffic there, then approve the first
   `main` push or manual run from `main`.
4. At the DNS provider, add all four apex A records (`185.199.108.153`,
   `185.199.109.153`, `185.199.110.153`, and `185.199.111.153`) or the
   provider's ALIAS/ANAME equivalent to `en-ver.github.io`. Optionally point
   `www` to `en-ver.github.io` with a CNAME.
5. Do not use wildcard DNS records (for example, `*.marketing-toolbox.org`)
   for GitHub Pages. Before publishing, remove any existing wildcard records
   that route to Pages; TXT domain verification does not eliminate this
   takeover risk. Preserve unrelated DNS records supporting legitimate services.
6. Wait for the certificate, enable HTTPS when GitHub makes it available, and
   confirm the HTTPS site works. Only then make the held README, launcher, and
   package Documentation URL cutover changes.

See GitHub's [custom workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [domain verification](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages), and [custom-domain DNS](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) documentation for current provider details.
