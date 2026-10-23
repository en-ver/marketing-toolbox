"""Refresh the locked development graph without invoking npm or package code."""

import json
import os
import subprocess
import sys
from pathlib import Path

lock, output = map(Path, sys.argv[1:])
packages = json.loads(lock.read_text())["packages"]
request: dict[str, list[str]] = {}
for path, item in packages.items():
    if path:
        name = path.rsplit("node_modules/", 1)[1]
        versions = request.setdefault(name, [])
        if item["version"] not in versions:
            versions.append(item["version"])
request_path = output / "audit-request.json"
request_path.write_text(json.dumps(request))
response_path = output / "audit-response.json"
code = subprocess.check_output(
    [
        "/usr/bin/curl",
        "-q",
        "--silent",
        "--show-error",
        "--fail",
        "--proto",
        "=https",
        "--tlsv1.2",
        "--connect-timeout",
        "15",
        "--max-time",
        "120",
        "--max-filesize",
        "2097152",
        "--header",
        "Content-Type: application/json",
        "--data-binary",
        "@" + str(request_path),
        "--output",
        str(response_path),
        "--write-out",
        "%{http_code}",
        "https://registry.npmjs.org/-/npm/v1/security/advisories/bulk",
    ],
    env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": str(output)},
    timeout=125,
)
assert code == b"200"
response = json.loads(response_path.read_bytes())
assert set(response) == {"esbuild", "vite"}
expected = {
    "GHSA-67mh-4wv8-2f99",
    "GHSA-v6wh-96g9-6wx3",
    "GHSA-4w7w-66w2-5vf9",
    "GHSA-fx2h-pf6j-xcff",
    "GHSA-9jrq-w75r-8gcw",
    "GHSA-rq7h-c2jc-7f22",
    "GHSA-698v-4r3x-3vcv",
    "GHSA-r825-w8mm-5pxw",
    "GHSA-587h-7wmj-h5pm",
}
findings = [item for values in response.values() for item in values]
assert len(findings) == 9
assert {item["url"] for item in findings} == {
    "https://github.com/advisories/" + identity for identity in expected
}, "Changed findings require reassessment, not an automatic fix or waiver"
(output / "audit-status.json").write_text(
    json.dumps(
        {
            "passing_audit": False,
            "known_exception": sorted(expected),
            "prior_npm_audit_exit": 1,
            "method": "registry full-graph bulk query, no npm execution",
            "controls": "offline build only; no Vite/esbuild server or editor middleware",
        }
    )
    + "\n"
)
assert not any(key.endswith("TOKEN") for key in os.environ)
