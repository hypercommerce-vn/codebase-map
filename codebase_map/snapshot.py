# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Snapshot Manager — save, list, clean, load graph snapshots (CBM-P1-03)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from codebase_map.graph.models import Graph

logger = logging.getLogger(__name__)

DEFAULT_SNAPSHOT_DIR = ".codebase-map-cache/snapshots"
DEFAULT_KEEP = 10


@dataclass
class SnapshotInfo:
    """Metadata summary of a single snapshot file."""

    label: str
    date: str
    branch: str
    sha: str
    nodes: int
    edges: int
    file_path: Path
    file_size: int  # bytes

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "date": self.date,
            "branch": self.branch,
            "sha": self.sha,
            "nodes": self.nodes,
            "edges": self.edges,
            "file": str(self.file_path),
            "size_bytes": self.file_size,
        }


# HC-AI | ticket: FDD-TOOL-CODEMAP
# CBM-P1-03: SnapshotManager — save/list/clean/load
class SnapshotManager:
    """Manage graph snapshot files in .codebase-map-cache/snapshots/."""

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self.cache_dir = Path(cache_dir or DEFAULT_SNAPSHOT_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save(self, graph: Graph, output_path: Optional[str] = None) -> Path:
        """Save graph to snapshot file.

        Naming convention: ``graph_{label}_{short_sha}.json``
        Returns the path of the saved file.
        """
        meta = graph.metadata
        label = meta.get("label", "unknown")
        sha = meta.get("commit_sha", "unknown")[:7]

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # Sanitize label for filesystem safety
        safe_label = _sanitize_filename(label)
        filename = f"graph_{safe_label}_{sha}.json"

        if output_path:
            save_path = Path(output_path)
        else:
            save_path = self.cache_dir / filename

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(graph.to_dict(), f, indent=2, ensure_ascii=False)

        logger.info("Snapshot saved: %s", save_path)
        return save_path

    def list_snapshots(self) -> list[SnapshotInfo]:
        """List all snapshots in cache dir, sorted by date descending."""
        snapshots: list[SnapshotInfo] = []

        if not self.cache_dir.exists():
            return snapshots

        for fp in self.cache_dir.glob("graph_*.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = data.get("metadata", {})
                stats = meta.get("stats", {})
                snapshots.append(
                    SnapshotInfo(
                        label=meta.get("label", "unknown"),
                        date=meta.get("generated_at", "unknown"),
                        branch=meta.get("branch", "unknown"),
                        sha=meta.get("commit_sha", "unknown")[:7],
                        nodes=stats.get("total_functions", 0),
                        edges=stats.get("total_edges", 0),
                        file_path=fp,
                        file_size=fp.stat().st_size,
                    )
                )
            except (json.JSONDecodeError, KeyError, OSError):
                logger.warning("Skipping malformed snapshot: %s", fp)
                continue

        return sorted(snapshots, key=lambda s: s.date or "", reverse=True)

    def clean(self, keep: int = DEFAULT_KEEP) -> tuple[int, int]:
        """Remove old snapshots, keep N newest.

        Returns ``(removed_count, kept_count)``.
        """
        snapshots = self.list_snapshots()
        if len(snapshots) <= keep:
            return 0, len(snapshots)

        to_remove = snapshots[keep:]
        removed = 0
        for s in to_remove:
            try:
                s.file_path.unlink(missing_ok=True)
                removed += 1
                logger.info("Removed snapshot: %s", s.file_path.name)
            except OSError as exc:
                logger.warning("Failed to remove %s: %s", s.file_path, exc)

        return removed, min(keep, len(snapshots))

    def load(self, label_or_path: str) -> Graph:
        """Load graph from a label name or file path.

        If ``label_or_path`` is an existing file, loads directly.
        Otherwise searches snapshots by label (returns newest match).
        """
        path = Path(label_or_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return Graph.from_dict(json.load(f))

        # Search by label
        for s in self.list_snapshots():
            if s.label == label_or_path:
                with open(s.file_path, "r", encoding="utf-8") as f:
                    return Graph.from_dict(json.load(f))

        raise FileNotFoundError(
            f"Snapshot '{label_or_path}' not found. "
            f"Run 'codebase-map snapshots list' to see available snapshots."
        )


def _sanitize_filename(name: str) -> str:
    """Replace unsafe filesystem characters in snapshot label."""
    safe = name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    # Remove other problematic chars
    safe = "".join(c for c in safe if c.isalnum() or c in "-_.")
    return safe or "unknown"
