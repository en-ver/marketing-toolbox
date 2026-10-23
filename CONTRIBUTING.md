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
Dependency changes require lockfile validation. Ordinary documentation edits do
not change dependencies. The approved site migration also changes site tooling
and source-distribution exclusions.

## User documentation site

The user documentation lives in `docs/user/`. The architecture and release
guides remain repository-only. The site uses the default VitePress 1.6.4 theme,
Node 24.22.1, and bundled npm 11.19.1. Python users do not need Node.

VitePress 1.6.4 includes unsupported Vite 5 and known security findings. This is
an explicit exception for the reviewed lock and isolated builds, not a passing
audit. Development servers, Vite preview, and live reload are omitted. Do not
run package commands on a host that contains personal credentials.

Use the reviewed hosted workflow when local isolation is unavailable. A
maintainer first reviews the source, lock, scripts, and workflow protections.
After separate publication and dispatch approval, the maintainer runs the
workflow at the exact feature branch. A feature dispatch builds and checks the
site but cannot deploy. A successful feature run does not approve a merge.

The workflow acquires reviewed archives without package execution. It seeds a
fresh cache offline, tests an installation without lifecycle scripts, then runs
`npm ci --offline --include=optional --no-audit --no-fund --foreground-scripts`
and `npm run docs:build` in a fresh, credential-free, network-disabled container.
The only dependency install script is esbuild 0.21.5's `node install.js`.
The build command is `vitepress build docs/user`. These commands describe the
container lane, not instructions for execution on your workstation.

The workflow stops the build before it copies and inspects the output. A pinned
Python static server and matching sandboxed Chromium inspect only that copy,
without external network access. The server is not a VitePress preview server.
Read `.github/docs-check/README.md` for exact inputs and limits. Do not relax
isolation or enable network access to recover a failed installation.

Keep `title` YAML metadata and one body H1 in each page. Directory `index.md`
files preserve the eight published trailing-slash routes. Use explicit directory
links such as `/auth/` and retain existing fragments. The production build
rejects dead links. Static and browser checks compare all 33 published heading
identities with `tests/data/docs-pages-baseline.yaml`. Use native `{#old-id}`
heading syntax only when rendered comparison shows a difference.

Treat lock updates as dependency changes. Review the complete graph, archives,
lifecycle scripts, and applicable advisories before installation. Do not use
`npm audit fix`, overrides, a new release, or additional downloads as an automatic
repair. Changed dependencies or newly applicable findings require reassessment.
Normal builds must leave both npm inputs unchanged. Keep site tooling and output
out of all four Python distributions.

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
6. Wait for the certificate and enable HTTPS when GitHub makes it available.
   Make sure that all eight routes and required fragments work on HTTPS. The
   README, CLI help, and package metadata already use the custom-domain URLs.
   Keep those URLs unchanged.

See GitHub's [custom workflow](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages), [domain verification](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages), and [custom-domain DNS](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) documentation for current provider details.
