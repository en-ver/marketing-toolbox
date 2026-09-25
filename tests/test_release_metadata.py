from __future__ import annotations

import importlib
import importlib.metadata
import os
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).parents[1]
RELEASE_WORKFLOW = ROOT / ".github/workflows/release.yml"
MANUAL_BOOTSTRAP_TARGETS = {
    "marketing-toolbox": {
        "confirmation": "BOOTSTRAP-MARKETING-TOOLBOX",
        "artifact_stem": "marketing_toolbox",
    },
    "ga4datactl": {
        "confirmation": "BOOTSTRAP-GA4DATACTL",
        "artifact_stem": "ga4datactl",
    },
    "ga4adminctl": {
        "confirmation": "BOOTSTRAP-GA4ADMINCTL",
        "artifact_stem": "ga4adminctl",
    },
    "gtmctl": {
        "confirmation": "BOOTSTRAP-GTMCTL",
        "artifact_stem": "gtmctl",
    },
}

PROJECTS = {
    "marketing-toolbox": {
        "manifest": ROOT / "pyproject.toml",
        "scripts": {
            "ga4datactl": "ga4datactl.cli:main",
            "ga4adminctl": "ga4adminctl.cli:main",
            "gtmctl": "gtmctl.cli:main",
        },
    },
    "ga4datactl": {
        "manifest": ROOT / "packaging/ga4datactl/pyproject.toml",
        "scripts": {"ga4datactl": "ga4datactl.cli:main"},
    },
    "ga4adminctl": {
        "manifest": ROOT / "packaging/ga4adminctl/pyproject.toml",
        "scripts": {"ga4adminctl": "ga4adminctl.cli:main"},
    },
    "gtmctl": {
        "manifest": ROOT / "packaging/gtmctl/pyproject.toml",
        "scripts": {"gtmctl": "gtmctl.cli:main"},
    },
}


def _project_metadata(distribution: str) -> dict[str, object]:
    with PROJECTS[distribution]["manifest"].open("rb") as manifest:
        return tomllib.load(manifest)["project"]


def test_workspace_distributions_have_synchronized_installed_metadata() -> None:
    versions = {
        distribution: _project_metadata(distribution)["version"]
        for distribution in PROJECTS
    }
    assert len(set(versions.values())) == 1

    for distribution, expected in versions.items():
        installed = importlib.metadata.distribution(distribution)
        assert installed.version == expected
        assert installed.metadata.get("License-Expression") == "MIT"


def test_aliases_pin_the_exact_core_version_and_expose_expected_scripts() -> None:
    core_version = _project_metadata("marketing-toolbox")["version"]

    core = importlib.metadata.distribution("marketing-toolbox")
    assert set(core.requires or ()) == {
        "google-analytics-admin==0.30.1",
        "google-analytics-data==0.23.0",
        "google-api-python-client==2.198.0",
        "google-auth==2.56.2",
        "google-auth-oauthlib==1.2.4",
        "jsonschema==4.25.1",
        "keyring==25.6.0",
        "typer==0.27.0",
    }

    for distribution, project in PROJECTS.items():
        installed = importlib.metadata.distribution(distribution)
        expected_scripts = project["scripts"]
        scripts = {
            entry_point.name: entry_point.value
            for entry_point in installed.entry_points
            if entry_point.group == "console_scripts"
        }
        assert scripts == expected_scripts

        if distribution != "marketing-toolbox":
            assert installed.requires == [f"marketing-toolbox=={core_version}"]


def test_cli_versions_match_the_installed_core_distribution() -> None:
    core_version = importlib.metadata.version("marketing-toolbox")
    for module_name in ("ga4datactl", "ga4adminctl", "gtmctl"):
        module = importlib.import_module(module_name)
        assert module.__version__ == core_version


def _release_workflow() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        yaml.load(RELEASE_WORKFLOW.read_text(), Loader=yaml.BaseLoader),
    )


def _workflow_step(
    workflow: dict[str, Any], job_name: str, step_name: str
) -> dict[str, Any]:
    steps = workflow["jobs"][job_name]["steps"]
    return next(step for step in steps if step.get("name") == step_name)


def _run_workflow_script(
    script: str, *, cwd: Path, environment: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-euo", "pipefail", "-c", script],
        cwd=cwd,
        env=os.environ | environment,
        capture_output=True,
        text=True,
        check=False,
    )


def test_release_workflow_has_an_exact_manual_bootstrap_contract() -> None:
    workflow = _release_workflow()
    dispatch = workflow["on"]["workflow_dispatch"]
    inputs = dispatch["inputs"]

    assert set(inputs) == {"publish_target", "confirmation"}
    assert inputs["publish_target"]["required"] == "true"
    assert inputs["publish_target"]["type"] == "choice"
    assert inputs["publish_target"]["options"] == list(MANUAL_BOOTSTRAP_TARGETS)
    assert inputs["publish_target"]["default"] == "marketing-toolbox"
    assert inputs["confirmation"]["required"] == "true"
    assert inputs["confirmation"]["type"] == "string"
    assert "options" not in inputs["confirmation"]

    checkout = _workflow_step(workflow, "build", "Check out release source")
    assert checkout["with"]["ref"] == (
        "${{ github.event_name == 'workflow_dispatch' && 'refs/heads/main' || github.ref }}"
    )

    verify = _workflow_step(workflow, "build", "Verify release mode")
    verify_script = cast(str, verify["run"])
    for target, bootstrap in MANUAL_BOOTSTRAP_TARGETS.items():
        valid = _run_workflow_script(
            verify_script,
            cwd=ROOT,
            environment={
                "EVENT_NAME": "workflow_dispatch",
                "WORKFLOW_REF": "refs/heads/main",
                "PUBLISH_TARGET": target,
                "CONFIRMATION": str(bootstrap["confirmation"]),
            },
        )
        assert valid.returncode == 0, valid.stderr

        wrong_branch = _run_workflow_script(
            verify_script,
            cwd=ROOT,
            environment={
                "EVENT_NAME": "workflow_dispatch",
                "WORKFLOW_REF": "refs/heads/release",
                "PUBLISH_TARGET": target,
                "CONFIRMATION": str(bootstrap["confirmation"]),
            },
        )
        assert wrong_branch.returncode != 0

        for other in MANUAL_BOOTSTRAP_TARGETS.values():
            if other != bootstrap:
                mismatched = _run_workflow_script(
                    verify_script,
                    cwd=ROOT,
                    environment={
                        "EVENT_NAME": "workflow_dispatch",
                        "WORKFLOW_REF": "refs/heads/main",
                        "PUBLISH_TARGET": target,
                        "CONFIRMATION": str(other["confirmation"]),
                    },
                )
                assert mismatched.returncode != 0

    invalid_target = _run_workflow_script(
        verify_script,
        cwd=ROOT,
        environment={
            "EVENT_NAME": "workflow_dispatch",
            "WORKFLOW_REF": "refs/heads/main",
            "PUBLISH_TARGET": "marketing-toolbox,ga4datactl",
            "CONFIRMATION": "BOOTSTRAP-MARKETING-TOOLBOX",
        },
    )
    assert invalid_target.returncode != 0


def test_release_workflow_stages_the_right_artifacts_per_mode(tmp_path: Path) -> None:
    workflow = _release_workflow()
    stage = _workflow_step(workflow, "publish", "Stage distributions for publication")
    assert stage["env"]["PUBLISH_TARGET"] == "${{ inputs.publish_target }}"
    stage_script = cast(str, stage["run"])
    artifacts = {
        "marketing_toolbox-0.2.0-py3-none-any.whl",
        "marketing_toolbox-0.2.0.tar.gz",
        "ga4datactl-0.2.0-py3-none-any.whl",
        "ga4datactl-0.2.0.tar.gz",
        "ga4adminctl-0.2.0-py3-none-any.whl",
        "ga4adminctl-0.2.0.tar.gz",
        "gtmctl-0.2.0-py3-none-any.whl",
        "gtmctl-0.2.0.tar.gz",
    }

    for target, bootstrap in MANUAL_BOOTSTRAP_TARGETS.items():
        stem = str(bootstrap["artifact_stem"])
        wheel = f"{stem}-0.2.0-py3-none-any.whl"
        sdist = f"{stem}-0.2.0.tar.gz"
        manual_artifact_cases = {
            "valid-pair": ({wheel, sdist}, True),
            "missing-wheel": ({sdist}, False),
            "missing-sdist": ({wheel}, False),
            "two-wheels-no-sdist": (
                {wheel, f"{stem}-0.1.1-py3-none-any.whl"},
                False,
            ),
            "two-sdists-no-wheel": ({sdist, f"{stem}-0.1.1.tar.gz"}, False),
            "duplicate-wheel": (
                {wheel, f"{stem}-0.1.1-py3-none-any.whl", sdist},
                False,
            ),
            "duplicate-sdist": ({wheel, sdist, f"{stem}-0.1.1.tar.gz"}, False),
        }
        for case_name, (
            case_artifacts,
            should_succeed,
        ) in manual_artifact_cases.items():
            case_dir = tmp_path / target / case_name
            dist = case_dir / "dist"
            dist.mkdir(parents=True)
            for artifact in case_artifacts:
                (dist / artifact).touch()

            manual = _run_workflow_script(
                stage_script,
                cwd=case_dir,
                environment={
                    "EVENT_NAME": "workflow_dispatch",
                    "PUBLISH_TARGET": target,
                },
            )
            if should_succeed:
                assert manual.returncode == 0, manual.stderr
                assert {
                    path.name for path in (case_dir / "publish-dist").iterdir()
                } == {wheel, sdist}
            else:
                assert manual.returncode != 0
                assert not list((case_dir / "publish-dist").iterdir())

    tagged_dir = tmp_path / "tagged"
    tagged_dist = tagged_dir / "dist"
    tagged_dist.mkdir(parents=True)
    for artifact in artifacts:
        (tagged_dist / artifact).touch()
    tagged = _run_workflow_script(
        stage_script,
        cwd=tagged_dir,
        environment={"EVENT_NAME": "push", "PUBLISH_TARGET": "marketing-toolbox"},
    )
    assert tagged.returncode == 0, tagged.stderr
    assert {path.name for path in (tagged_dir / "publish-dist").iterdir()} == artifacts

    invalid_dir = tmp_path / "invalid"
    invalid_dist = invalid_dir / "dist"
    invalid_dist.mkdir(parents=True)
    for artifact in artifacts:
        (invalid_dist / artifact).touch()
    invalid = _run_workflow_script(
        stage_script,
        cwd=invalid_dir,
        environment={
            "EVENT_NAME": "workflow_dispatch",
            "PUBLISH_TARGET": "marketing-toolbox,ga4datactl",
        },
    )
    assert invalid.returncode != 0

    untagged_all = _run_workflow_script(
        stage_script,
        cwd=invalid_dir,
        environment={
            "EVENT_NAME": "repository_dispatch",
            "PUBLISH_TARGET": "marketing-toolbox",
        },
    )
    assert untagged_all.returncode != 0


def test_release_workflow_validates_tag_versions_and_publishes_once() -> None:
    workflow = _release_workflow()
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["build"].get("permissions", {}).get("id-token") != "write"
    assert [
        job_name
        for job_name, job in workflow["jobs"].items()
        if job.get("permissions", {}).get("id-token") == "write"
    ] == ["publish"]

    verify_tag = _workflow_step(workflow, "build", "Verify tag and package versions")
    assert verify_tag["if"] == "github.event_name == 'push'"
    verify_script = cast(str, verify_tag["run"])

    valid = _run_workflow_script(
        verify_script, cwd=ROOT, environment={"RELEASE_TAG": "v0.2.0"}
    )
    assert valid.returncode == 0, valid.stderr
    for tag in ("0.2.0", "v", "v0.2.1"):
        invalid = _run_workflow_script(
            verify_script, cwd=ROOT, environment={"RELEASE_TAG": tag}
        )
        assert invalid.returncode != 0

    publish = workflow["jobs"]["publish"]
    assert publish["environment"] == {"name": "pypi"}
    assert publish["permissions"] == {"id-token": "write"}
    publisher_steps = [
        step
        for step in publish["steps"]
        if str(step.get("uses", "")).startswith("pypa/gh-action-pypi-publish@")
    ]
    assert len(publisher_steps) == 1
    publisher = publisher_steps[0]
    publisher_sha = cast(str, publisher["uses"]).rsplit("@", 1)[1]
    assert re.fullmatch(r"[0-9a-f]{40}", publisher_sha)
    assert publisher_sha == "dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
    assert publisher["with"] == {
        "packages-dir": "publish-dist/",
        "skip-existing": "true",
    }
