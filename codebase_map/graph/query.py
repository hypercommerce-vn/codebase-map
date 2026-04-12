# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Graph Query Engine — search, impact analysis, dependency lookup."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from codebase_map.graph.models import Graph, Node


@dataclass
class QueryResult:
    node: Node
    dependencies: list[str]
    dependents: list[str]
    impact_zone: list[str]
    test_files: list[str]

    def to_text(self) -> str:
        lines = [
            f"=== {self.node.name} ({self.node.node_type.value}) ===",
            f"  File:   {self.node.file_path}:{self.node.line_start}",
            f"  Layer:  {self.node.layer.value}",
            f"  Domain: {self.node.module_domain}",
        ]
        if self.node.docstring:
            lines.append(f"  Doc:    {self.node.docstring[:100]}")
        if self.node.decorators:
            lines.append(f"  Deco:   {', '.join(self.node.decorators)}")

        if self.dependencies:
            lines.append(f"\n  Dependencies ({len(self.dependencies)}):")
            for dep in self.dependencies:
                lines.append(f"    -> {dep}")

        if self.dependents:
            lines.append(f"\n  Dependents ({len(self.dependents)}):")
            for dep in self.dependents:
                lines.append(f"    <- {dep}")

        if self.impact_zone:
            lines.append(f"\n  Impact Zone ({len(self.impact_zone)}):")
            for imp in self.impact_zone:
                lines.append(f"    !! {imp}")

        if self.test_files:
            lines.append(f"\n  Test Files ({len(self.test_files)}):")
            for tf in self.test_files:
                lines.append(f"    >> {tf}")

        return "\n".join(lines)


class QueryEngine:
    """Query the function graph."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    @classmethod
    def from_json(cls, json_path: str | Path) -> QueryEngine:
        """Load graph from exported JSON file.

        Supports both v1.x (no metadata) and v2.1+ (with metadata) formats
        via ``Graph.from_dict()``.
        """
        with open(json_path) as f:
            data = json.load(f)
        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CBM-P1-01: Delegate to Graph.from_dict for v1.x + v2.1 compat
        graph = Graph.from_dict(data)
        return cls(graph)

    def search(self, query: str) -> list[Node]:
        """Search nodes by name (fuzzy match)."""
        query_lower = query.lower()
        results: list[Node] = []
        for node in self.graph.nodes.values():
            if (
                query_lower in node.name.lower()
                or query_lower in node.id.lower()
                or query_lower in node.docstring.lower()
            ):
                results.append(node)
        return sorted(results, key=lambda n: n.name)

    def query_node(self, query: str, depth: int = 3) -> QueryResult | None:
        """Full query: find node + dependencies + dependents + impact."""
        # Try exact match first
        node = self.graph.get_node(query)
        if not node:
            # Fuzzy search, take first result
            results = self.search(query)
            if not results:
                return None
            node = results[0]

        # Dependencies (what this node calls)
        deps = self.graph.get_dependencies(node.id)
        dep_ids = [e.target for e in deps]

        # Dependents (who calls this node)
        dependents = self.graph.get_dependents(node.id)
        dependent_ids = [e.source for e in dependents]

        # Impact analysis
        impact = self.graph.impact_analysis(node.id, depth=depth)

        # Find related test files
        test_files = self._find_test_files(node)

        return QueryResult(
            node=node,
            dependencies=dep_ids,
            dependents=dependent_ids,
            impact_zone=sorted(impact),
            test_files=test_files,
        )

    def impact(self, query: str, depth: int = 3) -> list[str]:
        """Quick impact analysis — return affected node IDs."""
        node = self.graph.get_node(query)
        if not node:
            results = self.search(query)
            if not results:
                return []
            node = results[0]

        return sorted(self.graph.impact_analysis(node.id, depth=depth))

    def _find_test_files(self, node: Node) -> list[str]:
        """Suggest test files that should cover this node."""
        test_files: set[str] = set()

        # Convention: tests/unit/{domain}/test_{module}.py
        domain = node.module_domain

        # Look for matching test files in the graph
        for other in self.graph.nodes.values():
            if "test" in other.file_path.lower():
                # Check if test file name matches node's module
                if node.name.lower() in other.file_path.lower():
                    test_files.add(other.file_path)
                elif domain in other.file_path.lower():
                    test_files.add(other.file_path)

        return sorted(test_files)

    def summary(self) -> str:
        """Generate a text summary of the graph."""
        stats = self.graph.stats()
        lines = [
            f"=== Codebase Map: {self.graph.project} ===",
            f"Generated: {self.graph.generated_at}",
            f"Total Nodes: {stats['total_nodes']}",
            f"Total Edges: {stats['total_edges']}",
            "",
            "By Type:",
        ]
        for k, v in sorted(stats["by_type"].items()):
            lines.append(f"  {k}: {v}")
        lines.append("\nBy Layer:")
        for k, v in sorted(stats["by_layer"].items()):
            lines.append(f"  {k}: {v}")
        lines.append("\nBy Domain:")
        for k, v in sorted(stats["by_domain"].items()):
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)
