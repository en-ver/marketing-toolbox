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
