# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Configuration loader — reads codebase-map.yaml (or .json) from a project root.

A config file is optional: ``Config.auto_detect`` builds one by looking at the
files in the project. PyYAML is only needed to read YAML config files.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# HC-AI | ticket: FDD-TOOL-CODEMAP
# VIBE-101: PyYAML is optional so the package can run from source on a machine
# where nothing was installed. Only YAML config files need it.
try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised through monkeypatch
    yaml = None  # type: ignore[assignment]

# VIBE-101: Directory names never scanned in auto-detect mode. They are matched
# against whole path segments, so "out" skips ``out/`` but not ``layout/``.
DEFAULT_EXCLUDE_DIRS: tuple[str, ...] = (
    ".git",
    "node_modules",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "dist",
    "build",
    "out",
    "coverage",
    ".venv",
    "venv",
    "__pycache__",
    "site-packages",
    ".codebase-map-cache",
    ".turbo",
    ".vercel",
    ".cache",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
)

# Language -> file extensions used to recognise it during auto-detect.
_LANGUAGE_EXTENSIONS: dict[str, tuple[str, ...]] = {
    "python": (".py",),
    "typescript": (".ts", ".tsx", ".js", ".jsx"),
}

# Generated files that would only add noise to an auto-detected graph.
_AUTO_EXCLUDE: dict[str, tuple[str, ...]] = {
    "python": (),
    "typescript": (".min.js", ".d.ts"),
}


@dataclass
class SourceConfig:
    path: str
    language: str = "python"
    exclude: list[str] = field(default_factory=list)
    base_module: str = ""  # e.g. "app" for Python import resolution
    # VIBE-101: directory names skipped entirely (exact path-segment match).
    exclude_dirs: list[str] = field(default_factory=list)


@dataclass
class OutputConfig:
    dir: str = "docs/function-map"
    formats: list[str] = field(default_factory=lambda: ["json", "html"])


@dataclass
class GraphConfig:
    depth: int = 3
    group_by: str = "module"


@dataclass
class Config:
    project: str = "my-project"
    sources: list[SourceConfig] = field(default_factory=list)
    output: OutputConfig = field(default_factory=OutputConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    project_root: Path = field(default_factory=lambda: Path.cwd())
    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S3-04: Business flows mapping {flow_name: [glob/regex patterns]}
    flows: dict[str, list[str]] = field(default_factory=dict)
    # CM-S4-01: Domain overrides {domain_name: [fnmatch patterns]}, matched on
    # the node's file path or node id.
    # Lets a project define its own business domains instead of relying on the
    # built-in path-segment list in the parsers. First match (insertion order) wins.
    domains: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> Config:
        """Load config from a YAML or JSON file (chosen by the file extension)."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        if config_path.suffix.lower() == ".json":
            with open(config_path, encoding="utf-8") as f:
                raw: dict[str, Any] = json.load(f) or {}
        else:
            if yaml is None:
                raise RuntimeError(
                    f"PyYAML is not installed, so {config_path} cannot be read. "
                    "Install it with `pip install pyyaml`, use a .json config, "
                    "or run without a config file to auto-detect the sources."
                )
            with open(config_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}

        return cls.from_dict(raw, config_path.parent)

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load config from a file. Kept for backwards compatibility."""
        return cls.from_file(path)

    @classmethod
    def from_dict(cls, raw: dict[str, Any], project_root: str | Path) -> Config:
        """Build a config from already-parsed data."""
        sources = [
            SourceConfig(
                path=s["path"],
                language=s.get("language", "python"),
                exclude=s.get("exclude", []),
                base_module=s.get("base_module", ""),
                exclude_dirs=s.get("exclude_dirs", []),
            )
            for s in raw.get("sources", [])
        ]

        output_raw = raw.get("output", {})
        output = OutputConfig(
            dir=output_raw.get("dir", "docs/function-map"),
            formats=output_raw.get("formats", ["json", "html"]),
        )

        graph_raw = raw.get("graph", {})
        graph = GraphConfig(
            depth=graph_raw.get("depth", 3),
            group_by=graph_raw.get("group_by", "module"),
        )

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S3-04: Parse flows section — {name: [patterns]}
        flows = _parse_pattern_map(raw.get("flows"))
        # CM-S4-01: Parse domains section — same shape as flows
        domains = _parse_pattern_map(raw.get("domains"))

        return cls(
            project=raw.get("project", "my-project"),
            sources=sources,
            output=output,
            graph=graph,
            project_root=Path(project_root),
            flows=flows,
            domains=domains,
        )

    @classmethod
    def default(cls, project_root: str | Path = ".") -> Config:
        """Create default config for quick start."""
        root = Path(project_root)
        return cls(
            project=root.name,
            sources=[
                SourceConfig(
                    path=".",
                    language="python",
                    exclude=["__pycache__", ".venv", "migrations"],
                )
            ],
            output=OutputConfig(),
            graph=GraphConfig(),
            project_root=root,
        )

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-101: zero-config mode. Looks at the files under ``project_root`` and
    # returns one source per language found, skipping dependency and build
    # folders. ``sources`` is empty when no supported file exists.
    @classmethod
    def auto_detect(cls, project_root: str | Path = ".") -> Config:
        """Build a config by inspecting the project instead of reading a file."""
        root = Path(project_root)
        sources = [
            SourceConfig(
                path=".",
                language=language,
                exclude=list(_AUTO_EXCLUDE.get(language, ())),
                exclude_dirs=list(DEFAULT_EXCLUDE_DIRS),
            )
            for language in detect_languages(root)
        ]
        return cls(
            project=root.resolve().name,
            sources=sources,
            output=OutputConfig(),
            graph=GraphConfig(),
            project_root=root,
        )


def detect_languages(root: Path) -> list[str]:
    """Return the supported languages that have at least one file under root."""
    found: set[str] = set()
    for _dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]
        for filename in filenames:
            for language, extensions in _LANGUAGE_EXTENSIONS.items():
                if language not in found and filename.endswith(extensions):
                    found.add(language)
        if len(found) == len(_LANGUAGE_EXTENSIONS):
            break
    return [language for language in _LANGUAGE_EXTENSIONS if language in found]


def _parse_pattern_map(raw: Any) -> dict[str, list[str]]:
    """Normalise ``{name: [patterns]}`` / ``{name: "pattern"}`` sections."""
    parsed: dict[str, list[str]] = {}
    for name, patterns in (raw or {}).items():
        if isinstance(patterns, list):
            parsed[str(name)] = [str(p) for p in patterns]
        elif isinstance(patterns, str):
            parsed[str(name)] = [patterns]
    return parsed
