"""Harmless probes inside each offline execution boundary, before package code."""

import json
import os
import pathlib
import socket
import sys

assert sys.version_info[:3] == (3, 13, 14)
assert os.getuid() == os.getgid() == 10001
assert not any(
    key.startswith(("GITHUB_", "ACTIONS_", "INPUT_", "NPM_TOKEN", "NODE_AUTH_TOKEN"))
    for key in os.environ
)
for path in ("/var/run/docker.sock", "/github/workspace", sys.argv[1]):
    assert not pathlib.Path(path).exists(), path
try:
    pathlib.Path("/root-write-probe").write_text("denied")
except PermissionError:
    pass
except OSError as error:
    assert error.errno == 30  # Read-only filesystem.
else:
    raise AssertionError("root write succeeded")
for address in ("1.1.1.1", "169.254.169.254"):
    try:
        with socket.create_connection((address, 443), timeout=2):
            pass
    except OSError:
        pass
    else:
        raise AssertionError("external network reachable")
status = pathlib.Path("/proc/self/status").read_text()
assert "NoNewPrivs:\t1" in status and "Seccomp:\t2" in status
assert "CapEff:\t0000000000000000" in status
print(
    json.dumps(
        {
            "python": sys.version,
            "uid": os.getuid(),
            "network_denied": True,
            "status": status,
        }
    )
)
