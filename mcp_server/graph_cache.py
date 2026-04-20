# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Graph cache manager — STUB.

Full implementation lands in CBM-INT-206 (D4). For Day 1 this stub exists so
``mcp_server.server`` can import a stable symbol while the scaffold takes
shape. Any actual use raises :class:`NotImplementedError`.
"""

from __future__ import annotations

from typing import Optional


class GraphCache:
    """Placeholder cache for parsed Codebase Map graph snapshots.

    The real implementation (CBM-INT-206) will load a graph JSON from disk,
    cache it in memory keyed by path + mtime, and expose ``QueryEngine``
    instances to tool handlers.
    """

    def __init__(self, default_path: str) -> None:
        self._default = default_path

    def get(self, path: Optional[str] = None):  # pragma: no cover - stub
        raise NotImplementedError(
            "GraphCache.get() will be implemented in CBM-INT-206 (D4)"
        )
