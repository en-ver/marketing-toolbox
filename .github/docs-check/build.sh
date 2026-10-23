#!/bin/sh
# Executed only in the offline, disposable build container.
set -eu
mkdir -p /tmp/home
: > /tmp/user.npmrc
: > /tmp/global.npmrc
node --version | grep -x v24.22.1
npm --version | grep -x 11.19.1
cd /work
# Prove Linux native dependencies and the offline cache without lifecycle scripts.
mkdir /work/probe
cp package.json package-lock.json /work/probe/
cd /work/probe
npm ci --offline --ignore-scripts --include=optional --no-audit --no-fund
test -f node_modules/@esbuild/linux-x64/bin/esbuild
test -f node_modules/@rollup/rollup-linux-x64-gnu/rollup.linux-x64-gnu.node
printf '%s\n' '97427508f98287d50b8001d36954fa547cdf73705d699c85de9f87c1c5ca909f  node_modules/esbuild/install.js' | sha256sum --check
cd /work
rm -rf /work/probe
npm ci --offline --include=optional --no-audit --no-fund --foreground-scripts
npm run docs:build
