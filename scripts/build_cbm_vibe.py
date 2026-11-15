#!/usr/bin/env python3
# HC-AI | ticket: FDD-TOOL-CODEMAP
"""VIBE-104: build the distributable cbm-vibe plugin.

The plugin folder in the repository holds only its own files. This script
adds a copy of the ``codebase_map`` package, so the skill runs on a machine
where nothing is installed, and packs the result:

    <out>/cbm-vibe/               the complete plugin
    <out>/cbm-vibe-plugin.zip     for Customize > Plugins > Add > Upload plugin
    <out>/cbm-vibe-skill.zip      the skill alone, for Customize > Skills

Usage:  python3 scripts/build_cbm_vibe.py [--out dist]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_NAME = "cbm-vibe"
SKILL_NAME = "cbm-vibe"
PLUGIN_SOURCE = REPO_ROOT / "plugins" / PLUGIN_NAME
PACKAGE_SOURCE = REPO_ROOT / "codebase_map"
SKILL_PATH = Path("skills") / SKILL_NAME
VENDOR_PATH = SKILL_PATH / "scripts" / "vendor"

_IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


def build(out_dir: Path) -> dict[str, Path]:
    """Build the plugin under ``out_dir``; return the paths that were made."""
    plugin_dir = out_dir / PLUGIN_NAME
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(PLUGIN_SOURCE, plugin_dir, ignore=_IGNORED)
    shutil.copytree(
        PACKAGE_SOURCE, plugin_dir / VENDOR_PATH / "codebase_map", ignore=_IGNORED
    )
    license_file = REPO_ROOT / "LICENSE"
    if license_file.exists():
        shutil.copy(license_file, plugin_dir / "LICENSE")
        shutil.copy(license_file, plugin_dir / SKILL_PATH / "LICENSE")
    (plugin_dir / VENDOR_PATH / "VERSION").write_text(_version_note(), encoding="utf-8")

    plugin_zip = out_dir / f"{PLUGIN_NAME}-plugin.zip"
    skill_zip = out_dir / f"{SKILL_NAME}-skill.zip"
    # Both archives hold one top-level folder, as the upload dialogs expect.
    _zip_folder(plugin_dir, plugin_zip, PLUGIN_NAME)
    _zip_folder(plugin_dir / SKILL_PATH, skill_zip, SKILL_NAME)
    return {"plugin": plugin_dir, "plugin_zip": plugin_zip, "skill_zip": skill_zip}


def _version_note() -> str:
    manifest = json.loads(
        (PLUGIN_SOURCE / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    package_version = "unknown"
    for line in (PACKAGE_SOURCE / "__init__.py").read_text("utf-8").splitlines():
        if line.startswith("__version__"):
            package_version = line.split("=", 1)[1].strip().strip("\"'")
    return f"plugin {manifest['version']}\ncodebase_map {package_version}\n"


def _zip_folder(folder: Path, archive: Path, top_level: str) -> None:
    """Zip ``folder`` so that every entry sits under ``top_level/``."""
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                name = Path(top_level) / path.relative_to(folder)
                bundle.write(path, name.as_posix())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(REPO_ROOT / "dist"), help="Output folder")
    args = parser.parse_args(argv)

    made = build(Path(args.out))
    files = sum(1 for path in made["plugin"].rglob("*") if path.is_file())
    print(f"[OK] {made['plugin']}  ({files} files)")
    for key in ("plugin_zip", "skill_zip"):
        size_kb = made[key].stat().st_size // 1024
        print(f"[OK] {made[key]}  ({size_kb} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
