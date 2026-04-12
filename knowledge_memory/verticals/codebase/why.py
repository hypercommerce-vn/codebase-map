# HC-AI | ticket: MEM-M2-05
"""Why command — explain dependency relationships between functions/modules.

Design ref: kmp-M2-design.html Screen B (why command).
Uses vault call graph to find all paths between two nodes,
then optionally uses LLM to generate architectural reasoning.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("codebase-memory.why")


@dataclass
class CallPath:
    """A single call path between two nodes."""

    nodes: list[str]
    path_type: str = "direct"  # "direct" | "via shared" | "transitive"


@dataclass
class WhyResult:
    """Result of a why query."""

    source: str
    target: str
    paths: list[CallPath]
    related_patterns: list[str]
    architecture_note: str = ""
    total_ms: float = 0.0
    error: str = ""

    @property
    def connected(self) -> bool:
        """Whether any path exists between source and target."""
        return len(self.paths) > 0


# HC-AI | ticket: MEM-M2-05
class WhyEngine:
    """Analyze dependency relationships using vault call graph.

    Finds all call paths between two functions/modules using BFS
    on the vault's edge data. Max depth 5 to avoid explosion.
    """

    MAX_DEPTH = 5
    MAX_PATHS = 10

    def __init__(self) -> None:
        self._adjacency: dict[str, list[str]] = {}
        self._reverse: dict[str, list[str]] = {}
        self._node_info: dict[str, dict[str, Any]] = {}
        self._patterns: list[str] = []

    def load_graph(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, str]],
        patterns: list[str] | None = None,
    ) -> None:
        """Load call graph from vault data.

        Args:
            nodes: List of node dicts from vault.query_nodes().
            edges: List of edge dicts from vault.query_edges().
            patterns: Pattern names for cross-referencing.
        """
        self._adjacency.clear()
        self._reverse.clear()
        self._node_info.clear()

        for n in nodes:
            name = n.get("name", "")
            if name:
                self._node_info[name] = n
                self._adjacency.setdefault(name, [])
                self._reverse.setdefault(name, [])

        for e in edges:
            src = e.get("source_name", "")
            tgt = e.get("target_name", "")
            if src and tgt:
                self._adjacency.setdefault(src, []).append(tgt)
                self._reverse.setdefault(tgt, []).append(src)

        self._patterns = patterns or []

    def why(self, source: str, target: str) -> WhyResult:
        """Find all call paths from source to target.

        Uses BFS with path tracking, limited to MAX_DEPTH hops
        and MAX_PATHS results. Classifies each path type.
        """
        import time

        start = time.monotonic()

        # Fuzzy match: find best match for source/target names
        src = self._resolve_name(source)
        tgt = self._resolve_name(target)

        if not src:
            return WhyResult(
                source=source,
                target=target,
                paths=[],
                related_patterns=[],
                error=f"Source not found: '{source}'",
            )
        if not tgt:
            return WhyResult(
                source=source,
                target=target,
                paths=[],
                related_patterns=[],
                error=f"Target not found: '{target}'",
            )

        # BFS to find all paths
        paths = self._find_all_paths(src, tgt)

        # Classify paths
        call_paths: list[CallPath] = []
        for path in paths[: self.MAX_PATHS]:
            if len(path) == 2:
                ptype = "direct"
            elif len(path) == 3:
                ptype = "via shared"
            else:
                ptype = "transitive"
            call_paths.append(CallPath(nodes=path, path_type=ptype))

        # Find related patterns
        related = self._find_related_patterns(src, tgt)

        # Architecture note
        arch_note = ""
        if call_paths:
            src_info = self._node_info.get(src, {})
            tgt_info = self._node_info.get(tgt, {})
            src_file = src_info.get("file_path", "")
            tgt_file = tgt_info.get("file_path", "")

            # Detect cross-domain coupling
            if src_file and tgt_file:
                src_domain = src_file.split("/")[0] if "/" in src_file else ""
                tgt_domain = tgt_file.split("/")[0] if "/" in tgt_file else ""
                if src_domain and tgt_domain and src_domain != tgt_domain:
                    arch_note = (
                        f"cross-domain coupling detected: "
                        f"{src_domain} -> {tgt_domain}"
                    )

        elapsed = (time.monotonic() - start) * 1000

        return WhyResult(
            source=src,
            target=tgt,
            paths=call_paths,
            related_patterns=related,
            architecture_note=arch_note,
            total_ms=elapsed,
        )

    def _find_all_paths(self, source: str, target: str) -> list[list[str]]:
        """BFS to find all paths from source to target, max depth."""
        paths: list[list[str]] = []
        queue: deque[list[str]] = deque([[source]])

        while queue and len(paths) < self.MAX_PATHS:
            current_path = queue.popleft()
            current_node = current_path[-1]

            if len(current_path) > self.MAX_DEPTH + 1:
                continue

            if current_node == target and len(current_path) > 1:
                paths.append(current_path)
                continue

            for neighbor in self._adjacency.get(current_node, []):
                if neighbor not in current_path:  # Avoid cycles
                    queue.append(current_path + [neighbor])

        # Sort by path length (shortest first)
        paths.sort(key=len)
        return paths

    def _resolve_name(self, name: str) -> str:
        """Resolve a name to an exact node name (fuzzy match)."""
        # Exact match
        if name in self._node_info:
            return name

        # Partial match (contains)
        lower = name.lower()
        candidates = [n for n in self._node_info if lower in n.lower()]
        if len(candidates) == 1:
            return candidates[0]

        # Try suffix match (e.g., "authenticate" matches "auth.service.authenticate")
        suffix_matches = [n for n in self._node_info if n.lower().endswith(lower)]
        if len(suffix_matches) == 1:
            return suffix_matches[0]

        return candidates[0] if candidates else ""

    def _find_related_patterns(self, source: str, target: str) -> list[str]:
        """Find patterns that mention source or target."""
        related = []
        src_lower = source.lower()
        tgt_lower = target.lower()
        for p in self._patterns:
            p_lower = p.lower()
            if src_lower in p_lower or tgt_lower in p_lower:
                related.append(p)
        return related


def format_why_result(result: WhyResult) -> str:
    """Format WhyResult for terminal output.

    Design ref: kmp-M2-design.html Screen B.
    """
    lines: list[str] = []
    lines.append("Knowledge Memory \u2014 Why")
    lines.append("")

    if result.error:
        lines.append(f"\u2717 {result.error}")
        return "\n".join(lines)

    if not result.connected:
        lines.append(
            f"No dependency path found between "
            f"'{result.source}' and '{result.target}'."
        )
        lines.append("")
        lines.append("Did you mean one of these functions?")
        return "\n".join(lines)

    lines.append(
        f"\u25b6 Analyzing call graph... "
        f"\u2713 Found {len(result.paths)} call path(s)"
    )
    lines.append("")

    for i, path in enumerate(result.paths, 1):
        lines.append(f"Path {i} ({path.path_type})")
        lines.append("  " + " \u2192 ".join(path.nodes))
        lines.append("")

    if result.architecture_note:
        lines.append(f"\u26a0 Architecture note: {result.architecture_note}")

    if result.related_patterns:
        lines.append("")
        lines.append("Related patterns:")
        for p in result.related_patterns:
            lines.append(f"  - {p}")

    return "\n".join(lines)
