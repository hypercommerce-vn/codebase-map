# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Graph Builder — orchestrates parsers and builds the complete graph."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from codebase_map.config import Config, SourceConfig
from codebase_map.graph.models import Edge, Graph
from codebase_map.parsers.base import BaseParser
from codebase_map.parsers.python_parser import PythonParser


class GraphBuilder:
    """Build a complete function dependency graph from config."""

    PARSERS: dict[str, type[BaseParser]] = {
        "python": PythonParser,
    }

    def __init__(self, config: Config) -> None:
        self.config = config
        self.graph = Graph(
            project=config.project,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def build(self) -> Graph:
        """Parse all sources and build the graph."""
        for source in self.config.sources:
            self._process_source(source)

        self._resolve_self_references()
        self._deduplicate_edges()
        return self.graph

    def _process_source(self, source: SourceConfig) -> None:
        """Process a single source configuration."""
        parser_cls = self.PARSERS.get(source.language)
        if not parser_cls:
            print(f"[WARN] No parser for language: {source.language}")
            return

        parser = parser_cls()
        source_path = self.config.project_root / source.path

        if not source_path.exists():
            print(f"[WARN] Source path not found: {source_path}")
            return

        extensions = parser.supported_extensions()
        files = self._collect_files(source_path, extensions, source.exclude)

        for file_path in sorted(files):
            rel_path = str(file_path.relative_to(self.config.project_root))
            nodes, edges = parser.parse_file(file_path, source.base_module)

            for node in nodes:
                # Override file_path to be relative
                node.file_path = rel_path
                self.graph.add_node(node)

            for edge in edges:
                self.graph.add_edge(edge)

    def _collect_files(
        self, root: Path, extensions: list[str], excludes: list[str]
    ) -> list[Path]:
        """Collect all files matching extensions, respecting excludes."""
        files: list[Path] = []
        for ext in extensions:
            for file_path in root.rglob(f"*{ext}"):
                # Check excludes
                rel = str(file_path.relative_to(root))
                skip = False
                for exc in excludes:
                    if exc in rel:
                        skip = True
                        break
                if not skip:
                    files.append(file_path)
        return files

    def _resolve_self_references(self) -> None:
        """Resolve self.method() calls to actual class method nodes."""
        for edge in self.graph.edges:
            if edge.target.startswith("self."):
                method_name = edge.target.split("self.", 1)[1]
                # Find the caller's parent class
                caller = self.graph.get_node(edge.source)
                if caller and caller.parent_class:
                    resolved = f"{caller.parent_class}.{method_name}"
                    if resolved in self.graph.nodes:
                        edge.target = resolved

    def _deduplicate_edges(self) -> None:
        """Remove duplicate edges."""
        seen: set[tuple[str, str, str]] = set()
        unique: list[Edge] = []
        for edge in self.graph.edges:
            key = (edge.source, edge.target, edge.edge_type.value)
            if key not in seen:
                seen.add(key)
                unique.append(edge)
        self.graph.edges = unique
