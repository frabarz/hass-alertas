"""Packaging sync: manifest, Nix package, HACS metadata, requirements."""

from __future__ import annotations

import json
import re
from pathlib import Path


def _manifest() -> dict:
    return json.loads(Path("custom_components/alertas_chile/manifest.json").read_text())


def test_manifest_domain_matches_dir() -> None:
    manifest = _manifest()
    assert manifest["domain"] == "alertas_chile"
    assert Path("custom_components/alertas_chile").is_dir()


def test_manifest_push_metadata() -> None:
    """UI-only setup with cloud push metadata and no runtime deps."""
    manifest = _manifest()
    assert manifest["config_flow"] is True
    assert manifest["iot_class"] == "cloud_push"
    assert manifest["integration_type"] == "service"
    assert manifest["requirements"] == []
    assert manifest["codeowners"] == ["@frabarz"]


def test_version_sync_manifest_nix() -> None:
    """Manifest and Nix package versions move together for HACS."""
    manifest = _manifest()
    package = Path("pkgs/alertas-chile-ha/package.nix").read_text()
    assert re.search(rf'domain = "{manifest["domain"]}";', package)
    assert re.search(rf'version = "{manifest["version"]}";', package)
    assert re.match(r"^\d+\.\d+\.\d+$", manifest["version"])


def test_homeassistant_floor_in_hacs() -> None:
    """HACS metadata pins the minimum Home Assistant version."""
    from awesomeversion import AwesomeVersion

    hacs = json.loads(Path("hacs.json").read_text())
    assert AwesomeVersion(hacs["homeassistant"]) >= AwesomeVersion("2026.1.0")
    assert hacs["country"] == "CL"
    assert "homeassistant" not in _manifest()


def test_requirements_mirror_manifest() -> None:
    """Zero runtime requirements stay mirrored in requirements.txt."""
    manifest = _manifest()
    assert manifest["requirements"] == []
    lines = [
        line.strip()
        for line in Path("requirements.txt").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert lines == []
