# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Graph data models — Node, Edge, Graph dataclasses."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class NodeType(str, Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    ROUTE = "route"
    MODEL = "model"
    CELERY_TASK = "celery_task"


class EdgeType(str, Enum):
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    INJECTS = "injects"
    DECORATES = "decorates"
    INSTANTIATES = "instantiates"


# HC-AI | ticket: FDD-TOOL-CODEMAP
class LayerType(str, Enum):
    CORE = "core"
    MODEL = "model"
    REPOSITORY = "repository"
    SERVICE = "service"
    ROUTER = "router"
    WORKER = "worker"
    SCHEMA = "schema"
    TEST = "test"
    UTIL = "util"
    UNKNOWN = "unknown"


@dataclass
class Node:
    """A single function, class, method, or module in the codebase."""

    id: str  # fully qualified module path
    name: str  # short name: create
    node_type: NodeType
    layer: LayerType
    module_domain: str  # crm, cdp, ecommerce, private_traffic, core, auth
    file_path: str  # relative path from project root
    line_start: int
    line_end: int = 0
    docstring: str = ""
    decorators: list[str] = field(default_factory=list)
    params: list[str] = field(default_factory=list)
    return_type: str = ""
    parent_class: str = ""  # for methods
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.value,
            "layer": self.layer.value,
            "domain": self.module_domain,
            "file": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "docstring": self.docstring,
            "decorators": self.decorators,
            "params": self.params,
            "return_type": self.return_type,
            "parent_class": self.parent_class,
            "metadata": self.metadata,
        }


@dataclass
class Edge:
    """A relationship between two nodes."""

    source: str  # node id
    target: str  # node id
    edge_type: EdgeType
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.edge_type.value,
            "metadata": self.metadata,
        }


@dataclass
class Graph:
    """Complete function dependency graph."""

    project: str = ""
    generated_at: str = ""
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        self.edges.append(edge)

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def get_dependents(self, node_id: str) -> list[Edge]:
        """Who depends on this node? (incoming edges)."""
        return [e for e in self.edges if e.target == node_id]

    def get_dependencies(self, node_id: str) -> list[Edge]:
        """What does this node depend on? (outgoing edges)."""
        return [e for e in self.edges if e.source == node_id]

    def impact_analysis(self, node_id: str, depth: int = 3) -> set[str]:
        """Find all affected nodes if this one changes."""
        affected: set[str] = set()
        queue = [node_id]
        visited: set[str] = set()
        current_depth = 0

        while queue and current_depth < depth:
            next_queue: list[str] = []
            for nid in queue:
                if nid in visited:
                    continue
                visited.add(nid)
                for edge in self.get_dependents(nid):
                    if edge.source not in visited:
                        affected.add(edge.source)
                        next_queue.append(edge.source)
            queue = next_queue
            current_depth += 1

        return affected

    def stats(self) -> dict[str, Any]:
        type_counts: dict[str, int] = {}
        layer_counts: dict[str, int] = {}
        domain_counts: dict[str, int] = {}
        for node in self.nodes.values():
            type_counts[node.node_type.value] = (
                type_counts.get(node.node_type.value, 0) + 1
            )
            layer_counts[node.layer.value] = layer_counts.get(node.layer.value, 0) + 1
            domain_counts[node.module_domain] = (
                domain_counts.get(node.module_domain, 0) + 1
            )
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "by_type": type_counts,
            "by_layer": layer_counts,
            "by_domain": domain_counts,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "generated_at": self.generated_at,
            "stats": self.stats(),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
        }
