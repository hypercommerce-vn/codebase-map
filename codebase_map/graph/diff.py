# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Git diff integration — detect changed files and compute impact zone.

Usage:
    codebase-map diff HEAD~1
    codebase-map diff HEAD~3 --depth 2
    codebase-map diff abc1234..def5678
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codebase_map.graph.models import Graph, Node


@dataclass
class DiffResult:
    """Result of a git diff analysis on the codebase graph."""

    ref: str
    changed_files: list[str] = field(default_factory=list)
    changed_nodes: list[Node] = field(default_factory=list)
    impacted_nodes: list[Node] = field(default_factory=list)
    stats: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        return {
            "ref": self.ref,
            "changed_files": self.changed_files,
            "changed_nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.value,
                    "layer": n.layer.value,
                    "domain": n.module_domain,
                    "file": n.file_path,
                    "line_start": n.line_start,
                }
                for n in self.changed_nodes
            ],
            "impacted_nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.node_type.value,
                    "layer": n.layer.value,
                    "domain": n.module_domain,
                    "file": n.file_path,
                    "line_start": n.line_start,
                }
                for n in self.impacted_nodes
            ],
            "stats": self.stats,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def to_text(self) -> str:
        """Human-readable text output for CLI."""
        lines: list[str] = []
        lines.append(f"=== Git Diff Analysis: {self.ref} ===")
        lines.append("")

        # Changed files
        lines.append(f"Changed Files ({len(self.changed_files)}):")
        for f in self.changed_files:
            lines.append(f"  M {f}")
        lines.append("")

        # Changed nodes
        lines.append(f"Changed Nodes ({len(self.changed_nodes)}):")
        for node in self.changed_nodes:
            ntype = node.node_type.value
            layer = node.layer.value
            lines.append(
                f"  * {node.name:30s} {ntype:12s} {layer:12s} {node.file_path}"
            )
        lines.append("")

        # Impact zone
        lines.append(f"Impact Zone ({len(self.impacted_nodes)} " f"affected nodes):")
        for node in self.impacted_nodes:
            ntype = node.node_type.value
            domain = node.module_domain
            lines.append(
                f"  !! {node.name:30s} {ntype:12s} {domain:15s} {node.file_path}"
            )
        lines.append("")

        # Summary
        total = len(self.changed_nodes) + len(self.impacted_nodes)
        lines.append("--- Summary ---")
        lines.append(f"  Files changed:  {len(self.changed_files)}")
        lines.append(f"  Nodes changed:  {len(self.changed_nodes)}")
        lines.append(f"  Nodes impacted: {len(self.impacted_nodes)}")
        lines.append(f"  Total affected: {total}")

        if self.stats:
            lines.append("")
            lines.append("  By domain:")
            for domain, count in sorted(self.stats.items()):
                lines.append(f"    {domain}: {count}")

        return "\n".join(lines)


# HC-AI | ticket: FDD-TOOL-CODEMAP
class DiffAnalyzer:
    """Analyze git diff and map changed files to graph nodes + impact zone."""

    def __init__(self, graph: Graph, project_root: Path | None = None) -> None:
        self.graph = graph
        self.project_root = project_root or Path.cwd()

    def analyze(self, ref: str = "HEAD~1", depth: int = 3) -> DiffResult:
        """Run full diff analysis: git diff → changed nodes → impact zone.

        Args:
            ref: Git ref to diff against (e.g. HEAD~1, abc..def, main)
            depth: How deep to trace impact (default 3 hops)

        Returns:
            DiffResult with changed files, nodes, and impacted nodes
        """
        # Step 1: Get changed files from git
        changed_files = self._git_changed_files(ref)

        # Step 2: Map changed files → graph nodes
        changed_nodes = self._map_files_to_nodes(changed_files)

        # Step 3: Compute impact zone for all changed nodes
        impacted_nodes = self._compute_impact(changed_nodes, depth)

        # Step 4: Compute stats by domain
        stats = self._compute_domain_stats(changed_nodes, impacted_nodes)

        return DiffResult(
            ref=ref,
            changed_files=changed_files,
            changed_nodes=changed_nodes,
            impacted_nodes=impacted_nodes,
            stats=stats,
        )

    def _git_changed_files(self, ref: str) -> list[str]:
        """Get list of changed Python files from git diff.

        Supports formats:
            - HEAD~1 (compare with N commits ago)
            - abc1234..def5678 (compare two commits)
            - main (compare with branch)
            - HEAD~1 --staged (compare staged changes)
        """
        try:
            cmd = [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMR",
                ref,
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.project_root),
                timeout=30,
            )
            if result.returncode != 0:
                # Try as a range (e.g., main..HEAD)
                if ".." not in ref:
                    cmd_alt = [
                        "git",
                        "diff",
                        "--name-only",
                        "--diff-filter=ACMR",
                        f"{ref}..HEAD",
                    ]
                    result = subprocess.run(
                        cmd_alt,
                        capture_output=True,
                        text=True,
                        cwd=str(self.project_root),
                        timeout=30,
                    )
                if result.returncode != 0:
                    print(f"[WARN] git diff failed: {result.stderr.strip()}")
                    return []

            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

            # Filter to only source files (Python for now)
            source_files = [f for f in files if f.endswith(".py")]
            return sorted(source_files)

        except FileNotFoundError:
            print("[ERROR] git not found in PATH")
            return []
        except subprocess.TimeoutExpired:
            print("[ERROR] git diff timed out")
            return []

    def _map_files_to_nodes(self, changed_files: list[str]) -> list[Node]:
        """Map changed file paths to graph nodes in those files."""
        changed_nodes: list[Node] = []
        for node in self.graph.nodes.values():
            for changed_file in changed_files:
                # Normalize paths for comparison
                if self._paths_match(node.file_path, changed_file):
                    changed_nodes.append(node)
                    break
        return sorted(changed_nodes, key=lambda n: (n.file_path, n.line_start))

    def _paths_match(self, node_path: str, diff_path: str) -> bool:
        """Check if a node's file_path matches a git diff path.

        Handles cases where paths might have different prefixes.
        """
        # Exact match
        if node_path == diff_path:
            return True
        # One ends with the other
        if node_path.endswith(diff_path) or diff_path.endswith(node_path):
            return True
        # Strip common prefixes and compare filenames
        node_parts = Path(node_path).parts
        diff_parts = Path(diff_path).parts
        # Compare from the end (at least filename + parent dir)
        min_parts = min(len(node_parts), len(diff_parts), 2)
        if min_parts > 0:
            return node_parts[-min_parts:] == diff_parts[-min_parts:]
        return False

    def _compute_impact(self, changed_nodes: list[Node], depth: int) -> list[Node]:
        """Compute impact zone: all nodes affected by changes.

        Uses the graph's built-in impact_analysis (BFS on dependents).
        Excludes the changed nodes themselves from the result.
        """
        changed_ids = {n.id for n in changed_nodes}
        impacted_ids: set[str] = set()

        for node in changed_nodes:
            affected = self.graph.impact_analysis(node.id, depth=depth)
            impacted_ids.update(affected)

        # Remove changed nodes from impact (they are already "changed")
        impacted_ids -= changed_ids

        # Resolve IDs to Node objects
        impacted_nodes: list[Node] = []
        for nid in impacted_ids:
            node = self.graph.get_node(nid)
            if node:
                impacted_nodes.append(node)

        return sorted(impacted_nodes, key=lambda n: (n.module_domain, n.name))

    def _compute_domain_stats(
        self,
        changed_nodes: list[Node],
        impacted_nodes: list[Node],
    ) -> dict[str, int]:
        """Count affected nodes per domain."""
        domain_counts: dict[str, int] = {}
        all_nodes = changed_nodes + impacted_nodes
        for node in all_nodes:
            domain = node.module_domain
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        return domain_counts
