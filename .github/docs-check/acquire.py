"""Hosted acquisition specification. Downloads bytes only; never imports package code."""

import base64
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys


def unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError("duplicate JSON key")
        d[k] = v
    return d


lock_path, destination, expected_sha = sys.argv[1:]
raw = pathlib.Path(lock_path).read_bytes()
assert len(raw) <= 2 * 1024 * 1024
assert hashlib.sha256(raw).hexdigest() == expected_sha
lock = json.loads(raw, object_pairs_hook=unique)
assert lock["lockfileVersion"] == 3
entries = {}
for path, item in lock["packages"].items():
    if path == "":
        continue
    assert not item.get("link")
    name = path.rsplit("node_modules/", 1)[1]
    version = item["version"]
    assert re.fullmatch(r"(?:@[a-z0-9._-]+/)?[a-z0-9._-]+", name)
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", version)
    url = f"https://registry.npmjs.org/{name}/-/{name.rsplit('/', 1)[-1]}-{version}.tgz"
    assert item["resolved"] == url
    integrity = item["integrity"]
    assert integrity.startswith("sha512-")
    digest = base64.b64decode(integrity[7:], validate=True)
    assert len(digest) == 64
    assert entries.setdefault(url, (name, version, integrity, digest)) == (
        name,
        version,
        integrity,
        digest,
    )
assert len(entries) == 173
out = pathlib.Path(destination)
out.mkdir(mode=0o700, parents=False, exist_ok=False)
env = {"PATH": "/usr/bin:/bin", "HOME": str(out), "LANG": "C.UTF-8"}
records = []
total = 0
for url, (name, version, integrity, digest) in sorted(entries.items()):
    filename = hashlib.sha256(url.encode("ascii")).hexdigest() + ".tgz"
    p = out / filename
    # curl -q is first: no user curlrc. No -L, no redirects, no proxy environment.
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
            str(8 * 1024 * 1024),
            "--output",
            str(p),
            "--write-out",
            "%{http_code}",
            url,
        ],
        env=env,
        timeout=125,
    )
    assert code == b"200"
    b = p.read_bytes()
    assert 0 < len(b) <= 8 * 1024 * 1024
    total += len(b)
    assert total <= 256 * 1024 * 1024
    assert hashlib.sha512(b).digest() == digest
    os.chmod(p, 0o444)
    records.append(
        {
            "name": name,
            "version": version,
            "url": url,
            "integrity": integrity,
            "sha256": hashlib.sha256(b).hexdigest(),
            "size": len(b),
            "file": filename,
        }
    )
(out / "inventory.json").write_text(json.dumps(records, indent=2) + "\n")
