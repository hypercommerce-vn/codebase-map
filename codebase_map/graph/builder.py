# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Graph Builder — orchestrates parsers and builds the complete graph."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from codebase_map.config import Config, SourceConfig
from codebase_map.graph.cache import BuildCache, CacheStats
from codebase_map.graph.models import Edge, Graph
from codebase_map.parsers.base import BaseParser
from codebase_map.parsers.python_parser import PythonParser


class GraphBuilder:
    """Build a complete function dependency graph from config."""

    PARSERS: dict[str, type[BaseParser]] = {
        "python": PythonParser,
    }

    def __init__(self, config: Config, use_cache: bool = True) -> None:
        self.config = config
        self.use_cache = use_cache
        self.graph = Graph(
            project=config.project,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S2-02: Incremental cache setup
        self._cache = BuildCache(cache_dir=config.project_root if use_cache else None)
        self._cache_stats = CacheStats()
        self._all_files: set[str] = set()

    @property
    def cache_stats(self) -> CacheStats:
        """Get cache statistics from the last build."""
        return self._cache_stats

    def build(self) -> Graph:
        """Parse all sources and build the graph."""
        start_time = time.monotonic()

        # Load existing cache
        if self.use_cache:
            self._cache.load(project=self.config.project)

        for source in self.config.sources:
            self._process_source(source)

        # Remove stale cache entries (deleted files)
        if self.use_cache:
            removed = self._cache.remove_stale(self._all_files)
            self._cache_stats.removed_files = removed

        self._resolve_self_references()
        self._deduplicate_edges()

        # Save updated cache
        if self.use_cache:
            self._cache.save()

        # Compute cache stats
        total = self._cache_stats.total_files
        if total > 0:
            self._cache_stats.cache_hit_rate = (
                self._cache_stats.cached_files / total * 100
            )

        elapsed = time.monotonic() - start_time
        self.graph.metadata = {
            "build_time_ms": round(elapsed * 1000),
            "cache_stats": {
                "total_files": self._cache_stats.total_files,
                "cached": self._cache_stats.cached_files,
                "parsed": self._cache_stats.parsed_files,
                "removed": self._cache_stats.removed_files,
                "hit_rate": round(self._cache_stats.cache_hit_rate, 1),
            },
        }

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
            self._all_files.add(rel_path)
            self._cache_stats.total_files += 1

            # HC-AI | ticket: FDD-TOOL-CODEMAP
            # CM-S2-02: Check cache before parsing
            if self.use_cache:
                file_hash = BuildCache.hash_file(file_path)
                if not self._cache.is_changed(rel_path, file_hash):
                    # Cache hit — load from cache
                    cached = self._cache.get_cached(rel_path)
                    if cached is not None:
                        cached_nodes, cached_edges = cached
                        for node in cached_nodes:
                            self.graph.add_node(node)
                        for edge in cached_edges:
                            self.graph.add_edge(edge)
                        self._cache_stats.cached_files += 1
                        continue

            # Cache miss or no cache — parse file
            nodes, edges = parser.parse_file(file_path, source.base_module)

            for node in nodes:
                # Override file_path to be relative
                node.file_path = rel_path
                self.graph.add_node(node)

            for edge in edges:
                self.graph.add_edge(edge)

            # Update cache with fresh parse results
            if self.use_cache:
                # Nodes already have rel_path set
                self._cache.update(rel_path, file_hash, nodes, edges)

            self._cache_stats.parsed_files += 1

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
