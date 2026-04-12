# HC-AI | ticket: FDD-TOOL-CODEMAP
"""CBM-P2-01: Snapshot diff engine — compare two graph snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from codebase_map.graph.models import Edge, Graph, Node


@dataclass
class NodeChange:
    """Represents a single node change between two snapshots."""

    change_type: str  # "added" | "removed" | "modified" | "renamed"
    node: Node
    old_node: Optional[Node] = None
    modifications: list[str] = field(default_factory=list)
    rename_from_file: Optional[str] = None


@dataclass
class EdgeChange:
    """Represents a single edge change between two snapshots."""

    change_type: str  # "added" | "removed"
    edge: Edge
    is_cascade: bool = False


@dataclass
class AffectedCaller:
    """A caller node affected by changes in its dependencies."""

    name: str
    file_path: str
    domain: str
    reason: str
    depth: int
    source_changes: list[str] = field(default_factory=list)


@dataclass
class DiffResult:
    """Complete diff result between two graph snapshots."""

    baseline_meta: dict
    current_meta: dict
    nodes_added: list[NodeChange] = field(default_factory=list)
    nodes_removed: list[NodeChange] = field(default_factory=list)
    nodes_modified: list[NodeChange] = field(default_factory=list)
    nodes_renamed: list[NodeChange] = field(default_factory=list)
    edges_added: list[EdgeChange] = field(default_factory=list)
    edges_removed: list[EdgeChange] = field(default_factory=list)
    affected_callers: list[AffectedCaller] = field(default_factory=list)

    @property
    def summary(self) -> dict:
        """Summary counts for all change types."""
        return {
            "functions_added": len(self.nodes_added),
            "functions_removed": len(self.nodes_removed),
            "functions_modified": len(self.nodes_modified),
            "functions_renamed": len(self.nodes_renamed),
            "edges_added": len(self.edges_added),
            "edges_removed": len(self.edges_removed),
            "affected_callers": len(self.affected_callers),
        }

    def has_changes(self) -> bool:
        """True if any changes were detected."""
        return any(v > 0 for v in self.summary.values())


class SnapshotDiff:
    """Compare two graph snapshots and compute structural diff.

    Handles node ID instability (line changes) via fallback matching
    by (name, file_path). Detects renames via signature matching.
    """

    def __init__(self, baseline: Graph, current: Graph):
        self.baseline = baseline
        self.current = current
        # Primary lookup: by node.id — Graph.nodes is dict[str, Node]
        self._b_by_id = baseline.nodes
        self._c_by_id = current.nodes
        # Fallback lookup: by (name, file_path) — handles line shifts
        self._b_by_name_file: dict[tuple[str, str], Node] = {}
        for n in baseline.nodes.values():
            self._b_by_name_file[(n.name, n.file_path)] = n
        self._c_by_name_file: dict[tuple[str, str], Node] = {}
        for n in current.nodes.values():
            self._c_by_name_file[(n.name, n.file_path)] = n

    def compute(self, depth: int = 1, include_renames: bool = True) -> DiffResult:
        """Run full diff: nodes, edges, renames, affected callers."""
        result = DiffResult(
            baseline_meta=self.baseline.metadata,
            current_meta=self.current.metadata,
        )

        # Step 1: Node diff
        added_ids, removed_ids, modified = self._diff_nodes()
        result.nodes_added = [NodeChange("added", self._c_by_id[i]) for i in added_ids]
        result.nodes_removed = [
            NodeChange("removed", self._b_by_id[i]) for i in removed_ids
        ]
        result.nodes_modified = modified

        # Step 2: Rename detection (reduces false removed+added pairs)
        if include_renames:
            renames = self._detect_renames(
                [c.node for c in result.nodes_removed],
                [c.node for c in result.nodes_added],
            )
            rename_removed_ids = {r.old_node.id for r in renames}
            rename_added_ids = {r.node.id for r in renames}
            result.nodes_removed = [
                c for c in result.nodes_removed if c.node.id not in rename_removed_ids
            ]
            result.nodes_added = [
                c for c in result.nodes_added if c.node.id not in rename_added_ids
            ]
            result.nodes_renamed = renames

        # Step 3: Edge diff
        result.edges_added, result.edges_removed = self._diff_edges()

        # Step 4: Affected callers (transitive BFS)
        changed_node_ids = {c.node.id for c in result.nodes_modified} | {
            c.node.id for c in result.nodes_removed
        }
        result.affected_callers = self._find_affected_callers(changed_node_ids, depth)

        return result

    def _diff_nodes(
        self,
    ) -> tuple[set[str], set[str], list[NodeChange]]:
        """Compare nodes: returns (added_ids, removed_ids, modified)."""
        # Step 1: Match by ID (exact)
        matched_by_id = self._b_by_id.keys() & self._c_by_id.keys()
        unmatched_b = set(self._b_by_id.keys()) - matched_by_id
        unmatched_c = set(self._c_by_id.keys()) - matched_by_id

        # Step 2: Fallback match by (name, file) for unmatched
        # Handles line shifts where ID changes but function is same
        fallback_matched: set[tuple[str, str]] = set()
        for b_id in list(unmatched_b):
            b_node = self._b_by_id[b_id]
            key = (b_node.name, b_node.file_path)
            if key in self._c_by_name_file:
                c_node = self._c_by_name_file[key]
                if c_node.id in unmatched_c:
                    fallback_matched.add((b_id, c_node.id))
                    unmatched_b.discard(b_id)
                    unmatched_c.discard(c_node.id)

        added_ids = unmatched_c
        removed_ids = unmatched_b

        # Check modifications in ID-matched nodes
        modified: list[NodeChange] = []
        for b_id in matched_by_id:
            b_node = self._b_by_id[b_id]
            c_node = self._c_by_id[b_id]
            mods = _detect_modifications(b_node, c_node)
            if mods:
                modified.append(NodeChange("modified", c_node, b_node, mods))

        # Check modifications in fallback-matched nodes
        for b_id, c_id in fallback_matched:
            b_node = self._b_by_id[b_id]
            c_node = self._c_by_id[c_id]
            mods = _detect_modifications(b_node, c_node)
            if mods:
                modified.append(NodeChange("modified", c_node, b_node, mods))

        return added_ids, removed_ids, modified

    def _diff_edges(
        self,
    ) -> tuple[list[EdgeChange], list[EdgeChange]]:
        """Compare edges between two graphs."""
        b_edges = {(e.source, e.target, e.edge_type.value) for e in self.baseline.edges}
        c_edges = {(e.source, e.target, e.edge_type.value) for e in self.current.edges}

        # Build edge lookup for EdgeChange objects
        b_edge_map = {
            (e.source, e.target, e.edge_type.value): e for e in self.baseline.edges
        }
        c_edge_map = {
            (e.source, e.target, e.edge_type.value): e for e in self.current.edges
        }

        added_keys = c_edges - b_edges
        removed_keys = b_edges - c_edges

        # Detect cascade: edge removed because node was removed
        removed_node_ids = self._b_by_id.keys() - self._c_by_id.keys()

        added = [EdgeChange("added", c_edge_map[k]) for k in added_keys]
        removed = [
            EdgeChange(
                "removed",
                b_edge_map[k],
                is_cascade=(k[0] in removed_node_ids or k[1] in removed_node_ids),
            )
            for k in removed_keys
        ]

        return added, removed

    def _detect_renames(
        self, removed: list[Node], added: list[Node]
    ) -> list[NodeChange]:
        """Detect renamed/moved functions via signature matching.

        CEO + CTO decision: match by name + params + return_type,
        NOT body matching.
        """
        renames: list[NodeChange] = []
        used_added: set[str] = set()

        for r_node in removed:
            for a_node in added:
                if a_node.id in used_added:
                    continue
                if _signature_match(r_node, a_node):
                    renames.append(
                        NodeChange(
                            change_type="renamed",
                            node=a_node,
                            old_node=r_node,
                            modifications=["file_moved"],
                            rename_from_file=r_node.file_path,
                        )
                    )
                    used_added.add(a_node.id)
                    break  # 1 removed → 1 added match

        return renames

    def _find_affected_callers(
        self, changed_ids: set[str], max_depth: int
    ) -> list[AffectedCaller]:
        """Find callers affected by changed nodes (BFS, max depth 3)."""
        max_depth = min(max_depth, 3)

        # Build reverse edge map: target_id -> [source_ids]
        callers_of: dict[str, list[str]] = {}
        for edge in self.current.edges:
            if edge.edge_type.value in ("calls", "imports"):
                callers_of.setdefault(edge.target, []).append(edge.source)
        # Also check baseline edges for removed nodes
        for edge in self.baseline.edges:
            if edge.edge_type.value in ("calls", "imports"):
                callers_of.setdefault(edge.target, []).append(edge.source)

        affected: dict[str, AffectedCaller] = {}
        frontier: list[tuple[str, int]] = [(nid, 1) for nid in changed_ids]
        visited: set[str] = set(changed_ids)

        while frontier:
            target_id, depth = frontier.pop(0)
            if depth > max_depth:
                continue

            for caller_id in callers_of.get(target_id, []):
                if caller_id in changed_ids:
                    continue

                target_node = self._c_by_id.get(target_id) or self._b_by_id.get(
                    target_id
                )
                target_name = target_node.name if target_node else target_id

                # Dedup: if already seen, just append source_change
                if caller_id in affected:
                    if target_name not in (affected[caller_id].source_changes):
                        affected[caller_id].source_changes.append(target_name)
                    continue

                if caller_id in visited:
                    continue
                visited.add(caller_id)

                caller_node = self._c_by_id.get(caller_id) or self._b_by_id.get(
                    caller_id
                )
                if not caller_node:
                    continue

                affected[caller_id] = AffectedCaller(
                    name=caller_node.name,
                    file_path=caller_node.file_path,
                    domain=(
                        caller_node.layer.value
                        if caller_node.layer
                        else caller_node.module_domain or "unknown"
                    ),
                    reason=f"calls {target_name} (changed)",
                    depth=depth,
                    source_changes=[target_name],
                )

                if depth + 1 <= max_depth:
                    frontier.append((caller_id, depth + 1))

        return sorted(
            affected.values(),
            key=lambda a: (a.depth, a.domain, a.name),
        )


def _detect_modifications(old: Node, new: Node) -> list[str]:
    """Compare two matched nodes to detect modifications."""
    mods: list[str] = []
    if old.params != new.params:
        mods.append("params_changed")
    if old.return_type != new.return_type:
        mods.append("return_type_changed")
    if old.decorators != new.decorators:
        mods.append("decorators_changed")
    if old.parent_class != new.parent_class:
        mods.append("parent_class_changed")
    # Line changes alone are NOT considered modifications
    # (common due to adding/removing lines above)
    return mods


def _signature_match(a: Node, b: Node) -> bool:
    """Match two nodes by signature: same name+params+return_type, different file."""
    return (
        a.name == b.name
        and a.params == b.params
        and a.return_type == b.return_type
        and a.file_path != b.file_path
    )
