# Hosted documentation checks

This directory contains the finite helpers for the reviewed documentation lane.
It is not a general container runner or a local preview tool. Do not run
`run.py` on a workstation. The workflow uses a standard `ubuntu-24.04` runner
and a 30-minute job ceiling. Runtime success remains a hosted acceptance gate.

## Inputs and commands

`run.py` acquires two immutable Linux amd64 images and four checksummed tool
files. Its `PYTHON`, `BROWSER`, and `DOWNLOADS` constants contain the exact
identities, URLs, sizes, and SHA256 values. The Python image supplies Python
3.13.14. The browser image supplies Chromium revision 1248, version
156.0.8078.4, and matching system libraries. The official Node archive supplies
Node 24.22.1 and npm 11.19.1 in both execution lanes. No setup-node action,
global npm upgrade, browser installer, `apt`, or additional browser download runs.

`acquire.py` accepts only the 173 archives in the reviewed lock, SHA256
`71ddf49f285f1452e5cf3834768f99aac41ec094e8c0f301efcd7ed911182196`.
It derives each exact registry URL from its name and version. It rejects links,
duplicate keys, changed locks, noncanonical URLs, and non-SHA512 integrity.
The trusted runner's configuration-free curl downloads bytes without redirects,
proxy configuration, credentials, or package execution. Limits are 8 MiB per
archive and 256 MiB total. The assessed archives total 128,426,783 bytes.

`audit.py` sends the locked full development graph to the registry's bulk
advisory endpoint. It records the response and the known exception, not a
passing audit. The nine accepted advisory identities concern the omitted
Vite/editor/esbuild server paths. Changed identities stop the lane for assessment.
This query does not replace review of new findings or image/tool advisories.

The clean environment in each execution container includes no tokens or npm
configuration from the runner. The cache-only container runs exact npm's
`cache add` against local archives with `--offline --ignore-scripts`.
`build.sh` first tests `npm ci --offline --ignore-scripts --include=optional`
in a disposable probe directory. It requires the Linux esbuild executable and
GNU/Linux Rollup module and makes sure that esbuild's installer SHA256 is
`97427508f98287d50b8001d36954fa547cdf73705d699c85de9f87c1c5ca909f`.
It discards that tree before the fresh installation and build.

The assessed dependency lifecycle command is esbuild 0.21.5's `node install.js`.
The only product script is `docs:build`, which runs `vitepress build docs/user`.
The installer and build have no network fallback. A cache miss, missing native
dependency, attempted download, or failed probe stops the run.

## Isolation and output

Containers run as UID/GID 10001 with no external network, read-only roots,
dropped capabilities, no-new-privileges, private PID/mount namespaces, and
seccomp. Limits are 2 CPUs, 4 GiB memory, 256 processes, a 512 MiB cache,
a 2 GiB work tree, and 256 MiB temporary storage. The browser also uses private
256 MiB shared memory and a separate 256 MiB evidence mount. No container mounts
the checkout, home, credentials, Docker socket, or host namespaces. Only the
allowlisted eight pages, configuration, and npm inputs enter the build tree.

`probe.py` checks identity, Python version, effective sandbox flags, absent
credential variables/socket/private sentinel, denied root writes, and external
network denial before package execution. Docker inspection records the limits.
Malformed acquisition fixtures must fail before any download directory exists.

After the producer stops, directory-relative no-follow copying rejects links,
hardlinks, special files, excessive entries, oversized files, and unexpected
output paths or types. The ordinary-file copy is hash-checked and read-only.
`check_html.py` permits the eight indexes and normal 404 page. It checks all 33
baseline heading IDs and all local page and fragment links. Each HTML file is
at most 8 MiB. A fresh parser receives exactly one `feed()` call per file.
An unfinished buffer or embedded document/media fails inspection. This avoids
the multi-feed unfinished-construct trigger assessed for CPython issue 153030.

The server runs only the pinned Python command:

```text
/usr/local/bin/python3.13 -I -m http.server 8765 --bind 127.0.0.1 --directory /site
```

Its fresh, non-root container has no network and mounts only the inspected site
and trusted probe helpers. The browser joins only that server's network namespace.
Neither container publishes a port. `smoke.cjs` uses matching Chromium, headless
mode, an isolated profile, blocked service workers, and `chromiumSandbox: true`.
There is no channel, executable override, remote browser, or sandbox-disable flag.

Before site navigation, the host inspects actual renderer user/PID namespaces,
seccomp, no-new-privileges, and capability state. It also proves private-file and
external-network denial in the browser boundary. Failure stops the run without
privileged mode or relaxed flags. The smoke check covers direct requests and
reloads, all headings, three required fragment reloads, clickable sidebar parents,
back/forward navigation, and table/code layout at 1440×1000 and 390×844.

## Evidence and acceptance

The minimal baseline in `tests/data/docs-pages-baseline.yaml` contains public
route and heading identities only. It derives from published HTML at source
revision `3850475b56cf18b54d32dfca642845819ef2a4a3`. The verified original
inventory SHA256 is
`68f7c6a920a06fe98b7082adb6eb54a861c6585bf1ebca30eb9805f209501ff1`.
No fetched HTML, credentials, or runtime handoff is checked in.

The workflow uploads inspected site files through the existing Pages artifact
action. A separate, one-day validation artifact contains run ID/attempt/ref/event,
checkout SHA, runner/image/tool identities, input/output hashes, acquisition and
audit records, probes, logs, and screenshots. Artifact handling stays outside
package execution because GitHub runtime artifact credentials exist on the runner.
Review downloaded data before use. Never execute downloaded site JavaScript locally.

Match evidence to the reviewed published SHA, not the newest run or a green
badge alone. A feature dispatch must show deployment skipped. Only a successful
non-PR `main` build can reach the unchanged separate deployment job. Required
Python CI results for that final SHA include both Linux matrix jobs and the
Windows OAuth job. Local Python tests do not replace those results or hosted
site checks. No feature run approves merge, deployment, settings, or DNS changes.
