from __future__ import annotations

import importlib
import importlib.metadata
import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[1]
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
        "jsonschema==4.25.1",
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
