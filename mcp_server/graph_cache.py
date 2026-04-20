# HC-AI | ticket: FDD-TOOL-CODEMAP
"""In-memory graph cache with mtime-based invalidation for MCP server.

Replaces the Day 1 stub (CBM-INT-201) with the full implementation described
in Technical Plan §2.4. Tool handlers (``cbm_query``, ``cbm_search``,
``cbm_impact``, ``cbm_api_catalog``) obtain a ``QueryEngine`` through the
module-level singleton ``CACHE`` instead of re-parsing ``graph.json`` on
every call.

Invalidation is based on the file's mtime rather than a TTL: when a user
runs ``codebase-map generate`` the file's mtime changes and the next
``get()`` transparently reloads. Access is guarded by a ``Lock`` so
concurrent MCP requests are safe.
"""

from __future__ import annotations

from pathlib import Path
from threading import Lock
from typing import Optional

from codebase_map.graph.query import QueryEngine

DEFAULT_GRAPH_FILE = "docs/function-map/graph.json"


class GraphCache:
    """Cache parsed graph snapshots keyed by absolute path + mtime."""

    def __init__(self, default_path: str = DEFAULT_GRAPH_FILE) -> None:
        self._default = default_path
        self._cache: dict[str, tuple[float, QueryEngine]] = {}
        self._lock = Lock()

    def get(self, path: Optional[str] = None) -> QueryEngine:
        """Return a ``QueryEngine`` for ``path`` (or the default graph).

        Raises ``FileNotFoundError`` with an actionable message if the graph
        file is missing. Reloads whenever the file's mtime has changed since
        the cached entry was stored.
        """
        p = Path(path or self._default)
        if not p.exists():
            raise FileNotFoundError(
                f"Graph file not found: {p}. " f"Run 'codebase-map generate' first."
            )
        key = str(p.resolve())
        mtime = p.stat().st_mtime
        with self._lock:
            cached = self._cache.get(key)
            if cached and cached[0] == mtime:
                return cached[1]
            engine = QueryEngine.from_json(p)
            self._cache[key] = (mtime, engine)
            return engine

    def clear(self) -> None:
        """Clear all cached graphs (useful for tests / reload CLI)."""
        with self._lock:
            self._cache.clear()

    def stats(self) -> dict:
        """Return cache stats for introspection / debugging."""
        with self._lock:
            return {
                "cached_paths": list(self._cache.keys()),
                "entry_count": len(self._cache),
            }


#: Module-level singleton shared across all tool handlers.
CACHE = GraphCache()
