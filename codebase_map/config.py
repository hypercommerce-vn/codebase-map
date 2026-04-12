# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Configuration loader — reads codebase-map.yaml from any project root."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SourceConfig:
    path: str
    language: str = "python"
    exclude: list[str] = field(default_factory=list)
    base_module: str = ""  # e.g. "app" for Python import resolution


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

    @classmethod
    def from_yaml(cls, path: str | Path) -> Config:
        """Load config from a YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path) as f:
            raw: dict[str, Any] = yaml.safe_load(f) or {}

        sources = [
            SourceConfig(
                path=s["path"],
                language=s.get("language", "python"),
                exclude=s.get("exclude", []),
                base_module=s.get("base_module", ""),
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
        flows_raw = raw.get("flows", {}) or {}
        flows: dict[str, list[str]] = {}
        for fname, patterns in flows_raw.items():
            if isinstance(patterns, list):
                flows[str(fname)] = [str(p) for p in patterns]
            elif isinstance(patterns, str):
                flows[str(fname)] = [patterns]

        return cls(
            project=raw.get("project", "my-project"),
            sources=sources,
            output=output,
            graph=graph,
            project_root=config_path.parent,
            flows=flows,
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
