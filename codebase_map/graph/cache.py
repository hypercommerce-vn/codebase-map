# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Incremental cache — hash files, skip unchanged, re-parse only diffs.

CM-S2-02: Cache AST parse results per file using content hash.
Only re-parse files whose hash changed since last generate.
Target: > 50% speed improvement when 1-2 files change.

Cache format (JSON):
{
    "version": "1.0",
    "project": "my-project",
    "generated_at": "...",
    "files": {
        "path/to/file.py": {
            "hash": "sha256hex",
            "nodes": [...],
            "edges": [...]
        }
    }
}
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codebase_map.graph.models import Edge, EdgeType, LayerType, Node, NodeType

CACHE_VERSION = "1.0"
CACHE_FILENAME = ".codebase-map-cache.json"


@dataclass
class CacheEntry:
    """Cached parse result for a single file."""

    file_hash: str
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CacheStats:
    """Statistics from an incremental build."""

    total_files: int = 0
    cached_files: int = 0
    parsed_files: int = 0
    removed_files: int = 0
    cache_hit_rate: float = 0.0
    time_saved_pct: float = 0.0

    def to_text(self) -> str:
        """Human-readable summary."""
        lines = [
            "--- Cache Stats ---",
            f"  Total files:    {self.total_files}",
            f"  From cache:     {self.cached_files}",
            f"  Re-parsed:      {self.parsed_files}",
            f"  Removed:        {self.removed_files}",
            f"  Cache hit rate: {self.cache_hit_rate:.1f}%",
        ]
        return "\n".join(lines)


# HC-AI | ticket: FDD-TOOL-CODEMAP
class BuildCache:
    """Manages incremental build cache for codebase-map.

    Stores per-file content hash + parsed nodes/edges.
    On next build, only re-parses files whose hash changed.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir
        self._entries: dict[str, CacheEntry] = {}
        self._project: str = ""
        self._loaded = False

    @property
    def cache_path(self) -> Path | None:
        """Full path to cache file."""
        if self.cache_dir:
            return self.cache_dir / CACHE_FILENAME
        return None

    def load(self, project: str = "") -> bool:
        """Load cache from disk. Returns True if loaded successfully."""
        self._project = project
        cache_path = self.cache_path
        if not cache_path or not cache_path.exists():
            return False

        try:
            with open(cache_path) as f:
                data = json.load(f)

            # Validate cache version and project
            if data.get("version") != CACHE_VERSION:
                print("[CACHE] Version mismatch, rebuilding.")
                return False
            if project and data.get("project") != project:
                print("[CACHE] Project mismatch, rebuilding.")
                return False

            # Load entries
            for file_path, entry_data in data.get("files", {}).items():
                self._entries[file_path] = CacheEntry(
                    file_hash=entry_data["hash"],
                    nodes=entry_data.get("nodes", []),
                    edges=entry_data.get("edges", []),
                )

            self._loaded = True
            return True

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[CACHE] Corrupt cache, rebuilding: {e}")
            self._entries.clear()
            return False

    def save(self) -> bool:
        """Save cache to disk. Returns True if saved successfully."""
        cache_path = self.cache_path
        if not cache_path:
            return False

        data: dict[str, Any] = {
            "version": CACHE_VERSION,
            "project": self._project,
            "files": {},
        }
        for file_path, entry in self._entries.items():
            data["files"][file_path] = {
                "hash": entry.file_hash,
                "nodes": entry.nodes,
                "edges": entry.edges,
            }

        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=None, separators=(",", ":"))
            return True
        except OSError as e:
            print(f"[CACHE] Failed to save: {e}")
            return False

    def is_changed(self, file_path: str, content_hash: str) -> bool:
        """Check if a file has changed since last cache."""
        entry = self._entries.get(file_path)
        if not entry:
            return True
        return entry.file_hash != content_hash

    def get_cached(self, file_path: str) -> tuple[list[Node], list[Edge]] | None:
        """Get cached nodes + edges for a file. Returns None if not cached."""
        entry = self._entries.get(file_path)
        if not entry:
            return None

        # Deserialize nodes
        nodes: list[Node] = []
        for n in entry.nodes:
            node = Node(
                id=n["id"],
                name=n["name"],
                node_type=NodeType(n["type"]),
                layer=LayerType(n["layer"]),
                module_domain=n["domain"],
                file_path=n["file"],
                line_start=n["line_start"],
                line_end=n.get("line_end", 0),
                docstring=n.get("docstring", ""),
                decorators=n.get("decorators", []),
                params=n.get("params", []),
                return_type=n.get("return_type", ""),
                parent_class=n.get("parent_class", ""),
                metadata=n.get("metadata", {}),
            )
            nodes.append(node)

        # Deserialize edges
        edges: list[Edge] = []
        for e in entry.edges:
            edge = Edge(
                source=e["source"],
                target=e["target"],
                edge_type=EdgeType(e["type"]),
                metadata=e.get("metadata", {}),
            )
            edges.append(edge)

        return nodes, edges

    def update(
        self,
        file_path: str,
        content_hash: str,
        nodes: list[Node],
        edges: list[Edge],
    ) -> None:
        """Update cache entry for a file."""
        self._entries[file_path] = CacheEntry(
            file_hash=content_hash,
            nodes=[n.to_dict() for n in nodes],
            edges=[e.to_dict() for e in edges],
        )

    def remove_stale(self, current_files: set[str]) -> int:
        """Remove cache entries for files that no longer exist.

        Returns count of removed entries.
        """
        stale = set(self._entries.keys()) - current_files
        for key in stale:
            del self._entries[key]
        return len(stale)

    @staticmethod
    def hash_file(file_path: Path) -> str:
        """Compute SHA-256 hash of file content."""
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except OSError:
            return ""
