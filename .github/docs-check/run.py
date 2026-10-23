"""Finite hosted-only lane. Never run on a workstation. No package code on runner."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

PYTHON = "docker.io/library/python@sha256:69e18bd8d831d88e0ef70239dc7771ab7c28bc296ae78ac75cde71e60aa4434f"
BROWSER = "mcr.microsoft.com/playwright@sha256:d65108d1a8095d8b0c4a5e32bf1807a40a5ce90ff0c78473e1116b1c243235e8"
LOCK = "71ddf49f285f1452e5cf3834768f99aac41ec094e8c0f301efcd7ed911182196"
DOWNLOADS = (
    (
        "https://nodejs.org/dist/v24.22.1/node-v24.22.1-linux-x64.tar.xz",
        "6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6",
        32026916,
    ),
    (
        "https://registry.npmjs.org/playwright/-/playwright-1.64.1.tgz",
        "36ba838d2d55c44fafcff89f919b5d7bc829209318076578ee2bc7cb5687fd57",
        905535,
    ),
    (
        "https://registry.npmjs.org/playwright-core/-/playwright-core-1.64.1.tgz",
        "3af03703c967c95037454f2283f709d53ce804a4776d4219d319f5bbcc2a0185",
        3172161,
    ),
    (
        "https://raw.githubusercontent.com/microsoft/playwright/v1.64.1/utils/docker/seccomp_profile.json",
        "cc3e61cabda6bbc1e53e54d27ba4d55a9d3be829b6dd1a596f4a7b31b1cc7849",
        12997,
    ),
)
ROOT = Path(__file__).resolve().parents[2]
HELPERS = ROOT / ".github/docs-check"
RUN = Path(os.environ["RUNNER_TEMP"]) / "docs-validation"
EVIDENCE = RUN / "evidence"
ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
containers: list[str] = []
mounts: list[Path] = []


def command(*args: str, timeout: int = 1800) -> str:
    print("+", *args, flush=True)
    return subprocess.check_output(args, env=ENV, text=True, timeout=timeout)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name: str, value: object) -> None:
    (EVIDENCE / name).write_text(json.dumps(value, indent=2) + "\n")


def mount(name: str, size: str, *, runner_owned: bool = False) -> Path:
    uid, gid = (os.getuid(), os.getgid()) if runner_owned else (10001, 10001)
    path = RUN / name
    path.mkdir()
    command(
        "sudo",
        "mount",
        "-t",
        "tmpfs",
        "-o",
        f"size={size},uid={uid},gid={gid},mode=0755",
        "tmpfs",
        str(path),
    )
    mounts.append(path)
    return path


def bind(source: Path, target: str, readonly: bool = True) -> list[str]:
    return [
        "--mount",
        f"type=bind,src={source},dst={target}" + (",readonly" if readonly else ""),
    ]


def create(
    image: str,
    args: list[str],
    volumes: list[str],
    network: str = "none",
    browser: bool = False,
) -> str:
    security = ["--security-opt", "no-new-privileges"]
    if browser:
        security += ["--security-opt", "seccomp=" + str(RUN / "seccomp_profile.json")]
    dns = (
        []
        if network.startswith("container:")
        else ["--dns", "127.0.0.1", "--dns-search", "."]
    )
    result = command(
        "docker",
        "create",
        "--platform",
        "linux/amd64",
        "--user",
        "10001:10001",
        "--network",
        network,
        "--read-only",
        "--cap-drop",
        "ALL",
        *security,
        "--cpus",
        "2",
        "--memory",
        "4g",
        "--memory-swap",
        "4g",
        "--pids-limit",
        "256",
        "--shm-size",
        "256m",
        *dns,
        "--tmpfs",
        "/tmp:rw,nosuid,size=268435456,uid=10001,gid=10001",
        *volumes,
        "--entrypoint",
        "/usr/bin/env",
        image,
        "-i",
        "PATH=/opt/node/bin:/usr/local/bin:/usr/bin:/bin",
        "HOME=/tmp/home",
        "LANG=C.UTF-8",
        "NPM_CONFIG_USERCONFIG=/tmp/user.npmrc",
        "NPM_CONFIG_GLOBALCONFIG=/tmp/global.npmrc",
        "NPM_CONFIG_CACHE=/cache",
        "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright",
        *args,
    ).strip()
    containers.append(result)
    inspection = json.loads(command("docker", "inspect", result))[0]
    config = inspection["HostConfig"]
    assert config["Memory"] == 4 * 1024**3 and config["NanoCpus"] == 2_000_000_000
    assert config["PidsLimit"] == 256 and config["ReadonlyRootfs"]
    assert config["CapDrop"] == ["ALL"] and not config["Privileged"]
    assert not config["PortBindings"] and not config["PidMode"]
    save(f"container-{len(containers)}.json", inspection)
    return result


def execute(cid: str, name: str) -> None:
    # Logs are data. Never source or evaluate them.
    command("docker", "start", cid)
    try:
        code = command("docker", "wait", cid).strip()
    finally:
        (EVIDENCE / f"{name}.log").write_text(command("docker", "logs", cid))
    assert code == "0", (name, code)
    state = json.loads(command("docker", "inspect", cid))[0]["State"]
    assert not state["Running"] and state["ExitCode"] == 0


def copy_site(
    trusted_root: Path, relative_source: Path, destination: Path
) -> dict[str, str]:
    """Walk from a trusted mount root without following any output-path symlink."""
    assert not relative_source.is_absolute() and ".." not in relative_source.parts
    destination.mkdir()
    hashes: dict[str, str] = {}
    total = 0
    entries = 0

    def visit(fd: int, relative: Path) -> None:
        nonlocal total, entries
        for name in os.listdir(fd):
            entries += 1
            assert entries <= 8192
            rel = relative / name
            assert len(str(rel)) <= 512
            assert not name.startswith(".") or str(rel) == ".nojekyll"
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            out = destination / rel
            if stat.S_ISDIR(info.st_mode):
                out.mkdir()
                child = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
                )
                try:
                    visit(child, rel)
                finally:
                    os.close(child)
                out.chmod(0o555)
            else:
                assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                assert info.st_size <= 8 * 1024**2 and len(hashes) < 4096
                assert (
                    rel.suffix
                    in {
                        ".html",
                        ".js",
                        ".css",
                        ".json",
                        ".woff",
                        ".woff2",
                        ".ttf",
                        ".svg",
                        ".png",
                        ".ico",
                        ".txt",
                    }
                    or str(rel) == ".nojekyll"
                )
                total += info.st_size
                assert total <= 256 * 1024**2
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
                with os.fdopen(child, "rb") as stream:
                    assert os.fstat(stream.fileno()) == info
                    data = stream.read(8 * 1024**2 + 1)
                assert len(data) == info.st_size
                with out.open("xb") as stream:
                    stream.write(data)
                hashes[str(rel)] = hashlib.sha256(data).hexdigest()
                assert digest(out) == hashes[str(rel)]
                out.chmod(0o444)

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(trusted_root, flags)
    try:
        for component in relative_source.parts:
            child = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        visit(fd, Path())
    finally:
        os.close(fd)
    destination.chmod(0o555)
    return hashes


def sandbox_probe(cid: str, sentinel: str) -> None:
    """Inspect actual renderer namespaces and kernel sandbox, not launch success."""
    records = []
    for line in command("docker", "top", cid, "-eo", "pid,args").splitlines()[1:]:
        pid, args = line.strip().split(None, 1)
        if "chrome" not in args:
            continue
        assert not any(
            flag in args
            for flag in (
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-namespace-sandbox",
                "--disable-seccomp-filter-sandbox",
            )
        )
        status = command("sudo", "readlink", f"/proc/{pid}/ns/user").strip()
        kernel = command("sudo", "head", "-c", "16384", f"/proc/{pid}/status")
        assert "Seccomp:\t2" in kernel and "NoNewPrivs:\t1" in kernel
        records.append(
            {"pid": pid, "args": args, "user_namespace": status, "status": kernel}
        )
    renderers = [r for r in records if "--type=renderer" in r["args"]]
    parents = [r for r in records if "--type=" not in r["args"]]
    assert renderers and parents
    for renderer in renderers:
        assert renderer["user_namespace"] != parents[0]["user_namespace"]
        assert "CapEff:\t0000000000000000" in renderer["status"]

        def filters(status: str) -> int:
            return int(
                next(
                    line
                    for line in status.splitlines()
                    if line.startswith("Seccomp_filters:")
                ).split()[1]
            )

        assert filters(renderer["status"]) > filters(parents[0]["status"])
        assert (
            len(
                next(
                    line
                    for line in renderer["status"].splitlines()
                    if line.startswith("NSpid:")
                ).split()
            )
            >= 3
        )
    # The exact Node tool probes browser namespace egress and private-file denial.
    result = command(
        "docker",
        "exec",
        cid,
        "/opt/node/bin/node",
        "-e",
        (
            "const fs=require('fs'),net=require('net'),assert=require('assert');"
            f"assert(!fs.existsSync({json.dumps(sentinel)}));"
            "assert(!fs.existsSync('/var/run/docker.sock'));"
            "const s=net.connect({host:'1.1.1.1',port:443});"
            "s.setTimeout(2000);s.on('connect',()=>process.exit(1));"
            "s.on('error',()=>process.exit(0));s.on('timeout',()=>{s.destroy();process.exit(0)});"
        ),
    )
    save("sandbox.json", {"processes": records, "network_private_probe": result})


def main() -> None:
    assert (
        os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("RUNNER_OS") == "Linux"
    )
    assert os.environ.get("RUNNER_ARCH") == "X64"
    RUN.mkdir(mode=0o755)
    EVIDENCE.mkdir()
    actual_sha = command("git", "-C", str(ROOT), "rev-parse", "HEAD").strip()
    assert actual_sha == os.environ["GITHUB_SHA"]
    assert digest(ROOT / "package-lock.json") == LOCK
    manifest = json.loads((ROOT / "package.json").read_text())
    assert manifest["scripts"] == {"docs:build": "vitepress build docs/user"}
    assert manifest["devDependencies"] == {"vitepress": "1.6.4"}
    assert manifest["private"] is True and manifest["packageManager"] == "npm@11.19.1"
    assert manifest["engines"] == {"node": "24.22.1", "npm": "11.19.1"}
    inputs = {
        str(p.relative_to(ROOT)): digest(p)
        for p in [
            ROOT / "package.json",
            ROOT / "package-lock.json",
            ROOT / "README.md",
            ROOT / "uv.lock",
        ]
    }
    save(
        "identity.json",
        {
            "sha": actual_sha,
            "run_id": os.environ["GITHUB_RUN_ID"],
            "attempt": os.environ["GITHUB_RUN_ATTEMPT"],
            "ref": os.environ["GITHUB_REF"],
            "event": os.environ["GITHUB_EVENT_NAME"],
            "workflow_ref": os.environ["GITHUB_WORKFLOW_REF"],
            "workflow_sha": os.environ["GITHUB_WORKFLOW_SHA"],
            "runner_image": os.environ.get("ImageOS"),
            "runner_version": os.environ.get("ImageVersion"),
            "docker": command("docker", "version"),
            "inputs": inputs,
        },
    )
    # Acquisition is separate from all package execution. Reject bad locks first.
    for field, value in (
        ("resolved", "https://example.org/x.tgz"),
        ("integrity", "sha1-invalid"),
        ("link", True),
    ):
        lock = json.loads((ROOT / "package-lock.json").read_text())
        next(v for k, v in lock["packages"].items() if k)[field] = value
        bad = RUN / "bad-lock.json"
        bad.write_text(json.dumps(lock))
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(HELPERS / "acquire.py"),
                str(bad),
                str(RUN / "rejected"),
                digest(bad),
            ],
            env=ENV,
            capture_output=True,
            check=False,
        )
        assert result.returncode != 0 and not (RUN / "rejected").exists()
    command(
        sys.executable,
        "-I",
        str(HELPERS / "audit.py"),
        str(ROOT / "package-lock.json"),
        str(EVIDENCE),
    )
    command(
        sys.executable,
        "-I",
        str(HELPERS / "acquire.py"),
        str(ROOT / "package-lock.json"),
        str(RUN / "archives"),
        LOCK,
    )
    (RUN / "archives").chmod(0o755)
    shutil.copyfile(RUN / "archives/inventory.json", EVIDENCE / "acquisition.json")
    for url, expected, size in DOWNLOADS:
        path = RUN / url.rsplit("/", 1)[1]
        code = command(
            "curl",
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
            "180",
            "--max-filesize",
            str(size),
            "--output",
            str(path),
            "--write-out",
            "%{http_code}",
            url,
            timeout=190,
        )
        assert (
            code == "200" and path.stat().st_size == size and digest(path) == expected
        )
    for image in (PYTHON, BROWSER):
        command("docker", "pull", "--platform", "linux/amd64", image)
    node = RUN / "node"
    node.mkdir()
    command(
        "tar",
        "-xJf",
        str(RUN / "node-v24.22.1-linux-x64.tar.xz"),
        "--strip-components=1",
        "-C",
        str(node),
    )
    tools = RUN / "tools"
    tools.mkdir()
    for package in ("playwright", "playwright-core"):
        path = tools / "node_modules" / package
        path.mkdir(parents=True)
        command(
            "tar",
            "-xzf",
            str(RUN / f"{package}-1.64.1.tgz"),
            "--strip-components=1",
            "-C",
            str(path),
        )
    shutil.copyfile(HELPERS / "smoke.cjs", tools / "smoke.cjs")
    baseline = json.loads((ROOT / "tests/data/docs-pages-baseline.yaml").read_text())[
        "pages"
    ]
    assert len(baseline) == 8 and sum(len(page["headings"]) for page in baseline) == 33
    assert all(re.fullmatch(r"/(?:[a-z0-9-]+/)*", page["route"]) for page in baseline)
    expected_html = {page["route"].lstrip("/") + "index.html" for page in baseline} | {
        "404.html"
    }
    (tools / "baseline.json").write_text(json.dumps(baseline))
    sentinel = str(RUN / "runner-private-sentinel")
    Path(sentinel).write_text("must remain outside containers")
    cache = mount("cache", "512m")
    # The runner populates inputs; ownership passes to UID 10001 before execution.
    work = mount("work", "2g", runner_owned=True)
    browser_evidence = mount("browser-evidence", "256m")
    common = bind(node, "/opt/node") + bind(HELPERS, "/checks")
    probe = f"/usr/local/bin/python3.13 -I /checks/probe.py {sentinel}"
    seed = create(
        PYTHON,
        [
            "/bin/sh",
            "-ec",
            probe
            + '; mkdir -p /tmp/home; touch /tmp/user.npmrc /tmp/global.npmrc; node --version | grep -x v24.22.1; npm --version | grep -x 11.19.1; for archive in /archives/*.tgz; do npm cache add "$archive" --offline --ignore-scripts --no-audit --no-fund; done',
        ],
        common + bind(cache, "/cache", False) + bind(RUN / "archives", "/archives"),
    )
    execute(seed, "cache")
    for filename in ("package.json", "package-lock.json"):
        assert (ROOT / filename).resolve() == ROOT / filename
        shutil.copyfile(ROOT / filename, work / filename)
    for old in baseline:
        relative = Path("docs/user") / old["route"].lstrip("/") / "index.md"
        target = work / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        assert (ROOT / relative).resolve() == ROOT / relative
        shutil.copyfile(ROOT / relative, target)
    config = work / "docs/user/.vitepress"
    config.mkdir()
    assert (
        ROOT / "docs/user/.vitepress/config.mts"
    ).resolve() == ROOT / "docs/user/.vitepress/config.mts"
    shutil.copyfile(ROOT / "docs/user/.vitepress/config.mts", config / "config.mts")
    command("sudo", "chown", "-R", "10001:10001", str(work))
    build = create(
        PYTHON,
        ["/bin/sh", "-ec", probe + "; exec /bin/sh /checks/build.sh"],
        common + bind(cache, "/cache", False) + bind(work, "/work", False),
    )
    execute(build, "build")
    for filename in ("package.json", "package-lock.json"):
        assert digest(work / filename) == inputs[filename]
    # A stopped container cannot race this directory-relative output copy.
    site = RUN / "site"
    hashes = copy_site(work, Path("docs/user/.vitepress/dist"), site)
    assert all(
        name in expected_html | {"hashmap.json", ".nojekyll"}
        or name.startswith("assets/")
        for name in hashes
    )
    save("site-sha256.json", hashes)
    static = create(
        PYTHON,
        [
            "/usr/local/bin/python3.13",
            "-I",
            "/checks/check_html.py",
            "/site",
            "/tools/baseline.json",
        ],
        bind(HELPERS, "/checks") + bind(site, "/site") + bind(tools, "/tools"),
    )
    execute(static, "static")
    server = create(
        PYTHON,
        [
            "/bin/sh",
            "-ec",
            probe
            + "; /usr/local/bin/python3.13 -I -c 'import sys; assert sys.version_info[:3] == (3,13,14)'; exec /usr/local/bin/python3.13 -I -m http.server 8765 --bind 127.0.0.1 --directory /site",
        ],
        bind(HELPERS, "/checks") + bind(site, "/site"),
    )
    command("docker", "start", server)
    command(
        "docker",
        "exec",
        server,
        "/usr/local/bin/python3.13",
        "-I",
        "-c",
        "import socket,time\nfor _ in range(30):\n try:\n  socket.create_connection(('127.0.0.1',8765),1).close(); break\n except OSError: time.sleep(0.5)\nelse: raise RuntimeError('static server not ready')",
    )
    browser = create(
        BROWSER,
        ["/opt/node/bin/node", "/tools/smoke.cjs"],
        bind(node, "/opt/node")
        + bind(tools, "/tools")
        + bind(browser_evidence, "/evidence", False),
        "container:" + server,
        True,
    )
    command("docker", "start", browser)
    for _ in range(120):
        if "sandbox-probe-ready" in command("docker", "logs", browser):
            break
        assert json.loads(command("docker", "inspect", browser))[0]["State"]["Running"]
        time.sleep(1)
    else:
        raise AssertionError("browser probe timeout")
    sandbox_probe(browser, sentinel)
    command("sudo", "touch", str(browser_evidence / "sandbox-ok"))
    assert command("docker", "wait", browser).strip() == "0"
    (EVIDENCE / "browser.log").write_text(command("docker", "logs", browser))
    command("docker", "stop", server)
    (EVIDENCE / "server.log").write_text(command("docker", "logs", server))
    command("sudo", "rm", str(browser_evidence / "sandbox-ok"))
    browser_hashes = copy_site(browser_evidence, Path(), EVIDENCE / "browser")
    assert set(browser_hashes) == {
        "browser-result.json",
        "auth-1440.png",
        "auth-390.png",
    }
    save("browser-sha256.json", browser_hashes)
    # Only the inspected ordinary-file copy enters artifact handling.
    destination = ROOT / "docs/user/.vitepress/dist"
    shutil.copytree(site, destination)
    assert all(digest(ROOT / p) == value for p, value in inputs.items())
    save(
        "success.json",
        {
            "sha": actual_sha,
            "site_files": len(list(site.rglob("*"))),
            "deploy_boundary": "non-PR/main only",
        },
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        for cid in reversed(containers):
            subprocess.run(["docker", "rm", "--force", cid], env=ENV, check=False)
        for path in reversed(mounts):
            subprocess.run(["sudo", "umount", str(path)], env=ENV, check=False)
