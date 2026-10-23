from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parents[1]
HELPERS = ROOT / ".github/docs-check"
BASELINE = ROOT / "tests/data/docs-pages-baseline.yaml"


def test_pages_workflow_preserves_deployment_and_credential_boundaries() -> None:
    workflow = yaml.load(
        (ROOT / ".github/workflows/docs-pages.yml").read_text(), Loader=yaml.BaseLoader
    )
    assert set(workflow["on"]) == {"pull_request", "push", "workflow_dispatch"}
    assert workflow["on"]["push"] == {"branches": ["main"]}
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"] == {
        "group": "docs-pages-${{ github.event_name == 'pull_request' && format('pr-{0}', github.event.pull_request.number) || github.ref }}",
        "cancel-in-progress": "${{ github.event_name == 'pull_request' }}",
    }
    build = workflow["jobs"]["build"]
    assert build["runs-on"] == "ubuntu-24.04"
    assert build["timeout-minutes"] == "30"
    assert build["permissions"] == {"contents": "read"}
    steps = {step["name"]: step for step in build["steps"]}
    checkout = steps["Check out source"]
    assert checkout["uses"] == (
        "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
    )
    assert checkout["with"]["persist-credentials"] == "false"
    assert steps["Build and inspect in offline boundaries"]["run"] == (
        "python3 -I .github/docs-check/run.py"
    )
    assert steps["Verify preserved inputs"]["run"] == (
        "git diff --exit-code -- package.json package-lock.json README.md uv.lock"
    )
    upload = steps["Upload Pages artifact"]
    assert upload["uses"] == (
        "actions/upload-pages-artifact@7b1f4a764d45c48632c6b24a0339c27f5614fb0b"
    )
    assert upload["with"]["path"] == "docs/user/.vitepress/dist/"
    assert upload["with"]["retention-days"] == "1"
    evidence = steps["Upload validation evidence"]
    assert evidence["uses"] == upload["uses"]
    assert evidence["with"]["name"] == (
        "docs-validation-${{ github.run_id }}-${{ github.run_attempt }}"
    )
    assert evidence["if"] == "always()"
    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["steps"][0]["uses"] == (
        "actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e"
    )
    predicate = deploy["if"]
    assert predicate == (
        "github.event_name != 'pull_request' && github.ref == 'refs/heads/main'"
    )
    for event, ref, expected in (
        ("pull_request", "refs/heads/main", False),
        ("workflow_dispatch", "refs/heads/docs/readme-features", False),
        ("push", "refs/heads/main", True),
        ("workflow_dispatch", "refs/heads/main", True),
    ):
        expression = predicate.replace("github.event_name", repr(event)).replace(
            "github.ref", repr(ref)
        )
        assert eval(expression.replace("&&", "and"), {"__builtins__": {}}) is expected
    assert "secrets." not in json.dumps(workflow)


def test_build_only_manifest_routes_and_original_heading_fixture() -> None:
    manifest = json.loads((ROOT / "package.json").read_text())
    assert manifest == {
        "name": "marketing-toolbox-docs",
        "private": True,
        "packageManager": "npm@11.19.1",
        "engines": {"node": "24.22.1", "npm": "11.19.1"},
        "scripts": {"docs:build": "vitepress build docs/user"},
        "devDependencies": {"vitepress": "1.6.4"},
    }
    assert (ROOT / ".node-version").read_text() == "24.22.1\n"
    lock = ROOT / "package-lock.json"
    assert hashlib.sha256(lock.read_bytes()).hexdigest() == (
        "71ddf49f285f1452e5cf3834768f99aac41ec094e8c0f301efcd7ed911182196"
    )
    assert (
        json.loads(lock.read_text())["packages"][""]["engines"] == manifest["engines"]
    )
    baseline = json.loads(BASELINE.read_text())
    assert baseline["inventory_sha256"] == (
        "68f7c6a920a06fe98b7082adb6eb54a861c6585bf1ebca30eb9805f209501ff1"
    )
    pages = baseline["pages"]
    assert len(pages) == 8 and sum(len(page["headings"]) for page in pages) == 33
    site = ROOT / "docs/user"
    assert {p.relative_to(site).as_posix() for p in site.rglob("*.md")} == {
        page["route"].lstrip("/") + "index.md" for page in pages
    }
    for page in pages:
        source = site / page["route"].lstrip("/") / "index.md"
        text = source.read_text()
        assert "weight:" not in text and "_index.md" not in text
        headings = re.findall(r"^(#{1,6}) (.+)$", text, re.MULTILINE)
        assert [(len(level), title) for level, title in headings] == [
            (heading["level"], heading["text"]) for heading in page["headings"]
        ]
        for target in re.findall(r"\]\((/[^)]*)\)", text):
            route, _, fragment = target.partition("#")
            destination = next(item for item in pages if item["route"] == route)
            if fragment:
                assert fragment in {h["id"] for h in destination["headings"]}
    config = (site / ".vitepress/config.mts").read_text()
    assert "base: '/'" in config and "cleanUrls: false" in config
    assert "ignoreDeadLinks" not in config and "rewrites" not in config
    assert "text: 'Authentication', link: '/auth/'" in config
    assert "text: 'Tool behavior', link: '/tools/'" in config


def test_offline_execution_configuration_is_explicit_not_runtime_proof() -> None:
    source = re.sub(r"\s+", " ", (HELPERS / "run.py").read_text())
    for required in (
        '"--user", "10001:10001"',
        '"--network", network',
        'network: str = "none"',
        '"--read-only"',
        '"--cap-drop", "ALL"',
        '"no-new-privileges"',
        '"--memory", "4g"',
        '"--pids-limit", "256"',
        '"--cpus", "2"',
        'mount("cache", "512m")',
        'mount("work", "2g", runner_owned=True)',
        '"--entrypoint", "/usr/bin/env", image, "-i"',
        '"container:" + server',
        "sandbox_probe(browser, sentinel)",
        "os.O_DIRECTORY | os.O_NOFOLLOW",
    ):
        assert required in source
    build = (HELPERS / "build.sh").read_text()
    assert "npm ci --offline --ignore-scripts --include=optional" in build
    assert "npm ci --offline --include=optional" in build
    assert "npm run docs:build" in build
    assert "sha256sum --check /tmp/inputs.sha256" in build
    smoke = (HELPERS / "smoke.cjs").read_text()
    assert "const browserName = 'chromium'" in smoke
    assert "headless: true, chromiumSandbox: true" in smoke
    assert "channel:" not in smoke and "executablePath:" not in smoke


def test_acquisition_rejects_unreviewed_inputs_before_requests(tmp_path: Path) -> None:
    original = json.loads((ROOT / "package-lock.json").read_text())
    for field, value in (
        ("resolved", "https://example.org/package.tgz"),
        ("integrity", "sha1-invalid"),
        ("link", True),
    ):
        lock = json.loads(json.dumps(original))
        next(item for path, item in lock["packages"].items() if path)[field] = value
        path = tmp_path / "lock.json"
        path.write_text(json.dumps(lock))
        destination = tmp_path / "downloads"
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(HELPERS / "acquire.py"),
                str(path),
                str(destination),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0 and not destination.exists()


def test_output_copy_rejects_links_and_preserves_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    spec = importlib.util.spec_from_file_location("docs_check", HELPERS / "run.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text("<html>ordinary bytes</html>")
    hashes = module.copy_site(tmp_path, Path("source"), tmp_path / "copy")
    assert hashes == {
        "index.html": hashlib.sha256((source / "index.html").read_bytes()).hexdigest()
    }
    (source / "secret.html").symlink_to(source / "index.html")
    with pytest.raises(AssertionError):
        module.copy_site(tmp_path, Path("source"), tmp_path / "rejected")


@pytest.mark.parametrize("component", range(4))
def test_output_copy_rejects_each_dist_path_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: int
) -> None:
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    spec = importlib.util.spec_from_file_location("docs_check", HELPERS / "run.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    work = tmp_path / "work"
    relative = Path("docs/user/.vitepress/dist")
    dist = work / relative
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("ordinary output")
    assert module.copy_site(work, relative, tmp_path / "valid") == {
        "index.html": hashlib.sha256(b"ordinary output").hexdigest()
    }
    replaced = work.joinpath(*relative.parts[: component + 1])
    outside = tmp_path / "outside"
    replaced.rename(outside)
    replaced.symlink_to(outside, target_is_directory=True)
    destination = tmp_path / "rejected"
    with pytest.raises(OSError):
        module.copy_site(work, relative, destination)
    assert not list(destination.iterdir())


@pytest.mark.parametrize(
    "rejected",
    [None, "other.css", "nested/vp-icons.css", "private.json", "bad\nname.css"],
)
def test_output_paths_allow_vitepress_icons_but_reject_other_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rejected: str | None
) -> None:
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    spec = importlib.util.spec_from_file_location("docs_check", HELPERS / "run.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected_html = {"index.html", "auth/index.html", "404.html"}
    names = expected_html | {
        "hashmap.json",
        ".nojekyll",
        "vp-icons.css",
        "assets/app.js",
        "assets/style.css",
    }
    hashes = dict.fromkeys(names, "fixture-digest")
    module.validate_site_paths(hashes, expected_html)
    if rejected is not None:
        hashes[rejected] = "fixture-digest"
        with pytest.raises(AssertionError) as error:
            module.validate_site_paths(hashes, expected_html)
        message = str(error.value)
        assert json.dumps(rejected, ensure_ascii=True) in message
        assert "\n" not in message and str(tmp_path) not in message
        assert "fixture-digest" not in message


def test_work_mount_allows_runner_population_before_ownership_transfer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    spec = importlib.util.spec_from_file_location("docs_check", HELPERS / "run.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.RUN = tmp_path
    monkeypatch.setattr(module.os, "getuid", lambda: 1001)
    monkeypatch.setattr(module.os, "getgid", lambda: 1002)
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(module, "command", lambda *args: calls.append(args))
    work = module.mount("work", "2g", runner_owned=True)
    assert "size=2g,uid=1001,gid=1002,mode=0755" in calls[-1]
    (work / "package.json").write_text("runner input")
    module.mount("cache", "512m")
    assert "size=512m,uid=10001,gid=10001,mode=0755" in calls[-1]
    # Configuration coverage only: no mount, sudo, or container runs in this test.
    source = (HELPERS / "run.py").read_text()
    populated = source.index('shutil.copyfile(ROOT / "docs/user/.vitepress/config.mts"')
    transferred = source.index(
        'command("sudo", "chown", "-R", "10001:10001", str(work))'
    )
    assert populated < transferred < source.index("    build = create(")


def test_static_checker_requires_baseline_headings_and_local_fragments(
    tmp_path: Path,
) -> None:
    baseline = json.loads(BASELINE.read_text())["pages"]
    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps(baseline))
    site = tmp_path / "site"
    for page in baseline:
        path = site / page["route"].lstrip("/") / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        headings = "".join(
            f'<h{h["level"]} id="{h["id"]}">{h["text"]}</h{h["level"]}>'
            for h in page["headings"]
        )
        path.write_text(f"<html><body>{headings}</body></html>")
    (site / "404.html").write_text("<html><body>Not found</body></html>")
    args = [
        sys.executable,
        "-I",
        str(HELPERS / "check_html.py"),
        str(site),
        str(baseline_path),
    ]
    valid = subprocess.run(args, capture_output=True, text=True, check=False)
    assert valid.returncode == 0, valid.stderr
    home = site / "index.html"
    original = home.read_text()
    home.write_text(
        original.replace("</body>", '<a href="/auth/#missing">broken</a></body>')
    )
    broken = subprocess.run(args, capture_output=True, text=True, check=False)
    assert broken.returncode != 0
    home.write_text(original.replace('id="marketing-toolbox"', 'id="changed"'))
    missing = subprocess.run(args, capture_output=True, text=True, check=False)
    assert missing.returncode != 0
