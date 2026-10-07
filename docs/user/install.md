---
title: Installation
weight: 10
---

# Installation

Marketing Toolbox requires Python 3.11 or later and [uv](https://docs.astral.sh/uv/).

## Run without installing

Use `uvx` for an ephemeral command. This resolves the named package for that invocation:

```bash
uvx ga4datactl --help
uvx ga4adminctl --help
uvx gtmctl --help
```

Pin a release when reproducibility matters:

```bash
uvx --from 'ga4datactl==0.6.0' ga4datactl --version
```

## Install persistently

Install each tool separately when you need only one command:

```bash
uv tool install ga4datactl
uv tool install ga4adminctl
uv tool install gtmctl
```

Or install the combined package to provide all three commands:

```bash
uv tool install marketing-toolbox
```

`marketing-toolbox` provides `ga4datactl`, `ga4adminctl`, and `gtmctl`; it does not provide a `marketing-toolbox` executable. After either installation method, verify the installed command with `--version` and inspect it with `--help`:

```bash
ga4datactl --version
ga4datactl --help
```

Continue with [authentication](auth/_index.md) before running commands that access Google resources.
