# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Test coverage overlay — import pytest-cov JSON, map to graph nodes.

CM-S2-03: Parse coverage.json from pytest-cov, compute per-function
coverage by mapping covered line ranges to AST node line ranges.
Annotate graph nodes with coverage metadata.

Usage:
    coverage = CoverageOverlay.from_json("coverage.json")
    coverage.apply(graph)
    # Now each node has: node.metadata["coverage"] = {
    #     "pct": 92.0, "lines_covered": 46, "lines_total": 50,
    #     "lines_missing": [42, 48, 49, 50], "branch_pct": 85.7
    # }
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from codebase_map.graph.models import Graph, Node


@dataclass
class FileCoverage:
    """Coverage data for a single source file."""

    file_path: str
    executed_lines: set[int] = field(default_factory=set)
    missing_lines: set[int] = field(default_factory=set)
    excluded_lines: set[int] = field(default_factory=set)
    branches_covered: int = 0
    branches_total: int = 0
    line_rate: float = 0.0


@dataclass
class NodeCoverage:
    """Coverage data for a single graph node (function/method/class)."""

    pct: float = 0.0
    lines_covered: int = 0
    lines_total: int = 0
    lines_missing: list[int] = field(default_factory=list)
    branch_pct: float = 0.0
    status: str = "unknown"  # "high" (>80%), "medium" (50-80%), "low" (<50%)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pct": round(self.pct, 1),
            "lines_covered": self.lines_covered,
            "lines_total": self.lines_total,
            "lines_missing": self.lines_missing,
            "branch_pct": round(self.branch_pct, 1),
            "status": self.status,
        }


# HC-AI | ticket: FDD-TOOL-CODEMAP
class CoverageOverlay:
    """Import coverage data and overlay onto graph nodes.

    Reads pytest-cov JSON output and maps covered lines to
    function/method line ranges from the graph.
    """

    def __init__(self) -> None:
        self._file_coverage: dict[str, FileCoverage] = {}
        self._summary: dict[str, Any] = {}

    @classmethod
    def from_json(cls, coverage_path: str | Path) -> CoverageOverlay:
        """Load coverage from pytest-cov JSON report.

        Expected format (pytest-cov --cov-report=json):
        {
            "meta": {...},
            "files": {
                "path/to/file.py": {
                    "executed_lines": [1, 2, 3, ...],
                    "missing_lines": [42, 48],
                    "excluded_lines": [],
                    "summary": {
                        "covered_lines": 46,
                        "num_statements": 50,
                        "percent_covered": 92.0,
                        "num_branches": 14,
                        "num_partial_branches": 2,
                        "covered_branches": 12
                    }
                }
            },
            "totals": {...}
        }
        """
        overlay = cls()
        path = Path(coverage_path)

        if not path.exists():
            print(f"[COVERAGE] File not found: {path}")
            return overlay

        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[COVERAGE] Failed to load: {e}")
            return overlay

        # Parse file coverage
        for file_path, file_data in data.get("files", {}).items():
            summary = file_data.get("summary", {})
            fc = FileCoverage(
                file_path=file_path,
                executed_lines=set(file_data.get("executed_lines", [])),
                missing_lines=set(file_data.get("missing_lines", [])),
                excluded_lines=set(file_data.get("excluded_lines", [])),
                branches_covered=summary.get("covered_branches", 0),
                branches_total=summary.get("num_branches", 0),
                line_rate=summary.get("percent_covered", 0.0),
            )
            overlay._file_coverage[file_path] = fc

        # Store totals
        overlay._summary = data.get("totals", {})

        return overlay

    @property
    def total_coverage(self) -> float:
        """Overall project coverage percentage."""
        return self._summary.get("percent_covered", 0.0)

    @property
    def file_count(self) -> int:
        """Number of files with coverage data."""
        return len(self._file_coverage)

    def apply(self, graph: Graph) -> dict[str, Any]:
        """Apply coverage data to graph nodes.

        Maps coverage line ranges to node line ranges.
        Returns summary stats.
        """
        stats = {
            "total_nodes": 0,
            "covered_nodes": 0,
            "high_nodes": 0,
            "medium_nodes": 0,
            "low_nodes": 0,
            "no_data_nodes": 0,
            "by_domain": {},
        }

        for node in graph.nodes.values():
            # Skip module-level nodes with no line range
            if node.line_start == 0 and node.line_end == 0:
                continue

            stats["total_nodes"] += 1

            # Find matching file coverage
            fc = self._match_file(node.file_path)
            if not fc:
                stats["no_data_nodes"] += 1
                continue

            # Compute per-node coverage
            nc = self._compute_node_coverage(node, fc)
            node.metadata["coverage"] = nc.to_dict()

            stats["covered_nodes"] += 1
            if nc.status == "high":
                stats["high_nodes"] += 1
            elif nc.status == "medium":
                stats["medium_nodes"] += 1
            else:
                stats["low_nodes"] += 1

            # Track by domain
            domain = node.module_domain
            if domain not in stats["by_domain"]:
                stats["by_domain"][domain] = {
                    "total": 0,
                    "covered": 0,
                    "sum_pct": 0.0,
                }
            stats["by_domain"][domain]["total"] += 1
            stats["by_domain"][domain]["covered"] += 1
            stats["by_domain"][domain]["sum_pct"] += nc.pct

        # Compute domain averages
        for domain_stats in stats["by_domain"].values():
            if domain_stats["covered"] > 0:
                domain_stats["avg_pct"] = round(
                    domain_stats["sum_pct"] / domain_stats["covered"], 1
                )
            else:
                domain_stats["avg_pct"] = 0.0

        # Store overall coverage in graph metadata
        graph.metadata["coverage"] = {
            "total_pct": round(self.total_coverage, 1),
            "files_covered": self.file_count,
            "stats": stats,
        }

        return stats

    def _match_file(self, node_file_path: str) -> FileCoverage | None:
        """Match a graph node's file_path to coverage data.

        Handles path normalization: node stores relative paths,
        coverage.json may store absolute or relative paths.
        """
        # Direct match
        if node_file_path in self._file_coverage:
            return self._file_coverage[node_file_path]

        # Normalize: try matching by suffix
        node_path = Path(node_file_path)
        for cov_path, fc in self._file_coverage.items():
            cov_p = Path(cov_path)
            # Match if one path is suffix of the other
            try:
                if node_path == cov_p:
                    return fc
                if str(node_path) in str(cov_p) or str(cov_p) in str(node_path):
                    return fc
                # Match by filename + parent dir
                if (
                    node_path.name == cov_p.name
                    and node_path.parent.name == cov_p.parent.name
                ):
                    return fc
            except Exception:
                continue

        return None

    def _compute_node_coverage(self, node: Node, fc: FileCoverage) -> NodeCoverage:
        """Compute coverage for a single node by its line range."""
        if node.line_end == 0:
            node_lines = {node.line_start}
        else:
            node_lines = set(range(node.line_start, node.line_end + 1))

        # Filter to actual code lines (executed + missing = all statements)
        all_statement_lines = fc.executed_lines | fc.missing_lines
        relevant_lines = node_lines & all_statement_lines

        if not relevant_lines:
            return NodeCoverage(status="unknown")

        covered = relevant_lines & fc.executed_lines
        missing = sorted(relevant_lines & fc.missing_lines)

        total = len(relevant_lines)
        covered_count = len(covered)
        pct = (covered_count / total * 100) if total > 0 else 0.0

        # Branch coverage for this node (approximate — file-level ratio)
        branch_pct = 0.0
        if fc.branches_total > 0:
            branch_pct = fc.branches_covered / fc.branches_total * 100

        # Status thresholds
        if pct >= 80:
            status = "high"
        elif pct >= 50:
            status = "medium"
        else:
            status = "low"

        return NodeCoverage(
            pct=pct,
            lines_covered=covered_count,
            lines_total=total,
            lines_missing=missing,
            branch_pct=branch_pct,
            status=status,
        )

    def get_uncovered_functions(self, graph: Graph) -> list[tuple[str, str, float]]:
        """Get list of functions with 0% coverage.

        Returns: list of (node_id, file_path, coverage_pct)
        """
        uncovered: list[tuple[str, str, float]] = []
        for node in graph.nodes.values():
            cov = node.metadata.get("coverage", {})
            if cov and cov.get("pct", -1) == 0.0:
                uncovered.append((node.id, node.file_path, 0.0))
        return sorted(uncovered, key=lambda x: x[0])

    def summary_text(self, graph: Graph) -> str:
        """Generate human-readable coverage summary."""
        cov_meta = graph.metadata.get("coverage", {})
        stats = cov_meta.get("stats", {})
        lines = [
            "=== Coverage Summary ===",
            f"  Overall: {cov_meta.get('total_pct', 0)}%",
            f"  Files:   {cov_meta.get('files_covered', 0)}",
            f"  Nodes:   {stats.get('covered_nodes', 0)}"
            f"/{stats.get('total_nodes', 0)} analyzed",
            "",
            "  By status:",
            f"    🟢 High (≥80%):   {stats.get('high_nodes', 0)}",
            f"    🟡 Medium (50-80%): {stats.get('medium_nodes', 0)}",
            f"    🔴 Low (<50%):     {stats.get('low_nodes', 0)}",
            f"    ⚪ No data:        {stats.get('no_data_nodes', 0)}",
        ]

        # By domain
        by_domain = stats.get("by_domain", {})
        if by_domain:
            lines.append("\n  By domain:")
            for domain, ds in sorted(by_domain.items()):
                avg = ds.get("avg_pct", 0)
                dot = "🟢" if avg >= 80 else ("🟡" if avg >= 50 else "🔴")
                lines.append(
                    f"    {dot} {domain:20s} {avg:5.1f}% "
                    f"({ds.get('covered', 0)} nodes)"
                )

        # Uncovered functions
        uncovered = self.get_uncovered_functions(graph)
        if uncovered:
            lines.append(f"\n  Uncovered functions ({len(uncovered)}):")
            for nid, fpath, _ in uncovered[:20]:
                lines.append(f"    ✗ {nid}")
            if len(uncovered) > 20:
                lines.append(f"    ... and {len(uncovered) - 20} more")

        return "\n".join(lines)
