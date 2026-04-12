# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CBM-P2-01: SnapshotDiff core — node diff, edge diff, affected callers."""

from __future__ import annotations

from codebase_map.graph.models import Edge, EdgeType, Graph, LayerType, Node, NodeType
from codebase_map.graph.snapshot_diff import (
    SnapshotDiff,
    _detect_modifications,
    _signature_match,
)


def _node(
    nid: str,
    name: str,
    fpath: str = "a.py",
    line: int = 1,
    params: list[str] | None = None,
    return_type: str = "",
    decorators: list[str] | None = None,
    parent_class: str = "",
) -> Node:
    """Helper — create a minimal Node."""
    return Node(
        id=nid,
        name=name,
        node_type=NodeType.FUNCTION,
        layer=LayerType.CORE,
        module_domain="app",
        file_path=fpath,
        line_start=line,
        params=params or [],
        return_type=return_type,
        decorators=decorators or [],
        parent_class=parent_class,
    )


def _graph(
    nodes: list[Node],
    edges: list[Edge] | None = None,
    label: str = "test",
) -> Graph:
    """Helper — create a Graph from node/edge lists."""
    g = Graph(project="test", generated_at="2026-04-12T10:00:00Z")
    g.metadata = {"label": label, "commit_sha": "abc1234", "branch": "main"}
    for n in nodes:
        g.add_node(n)
    for e in edges or []:
        g.edges.append(e)
    return g


def _edge(src: str, tgt: str, etype: str = "calls") -> Edge:
    """Helper — create an Edge."""
    return Edge(source=src, target=tgt, edge_type=EdgeType(etype))


class TestSnapshotDiffIdentical:
    """Identical graphs should produce no changes."""

    def test_no_changes(self) -> None:
        nodes = [_node("a.func", "func"), _node("b.bar", "bar")]
        baseline = _graph(nodes, label="baseline")
        current = _graph(nodes, label="current")
        result = SnapshotDiff(baseline, current).compute()
        assert not result.has_changes()
        assert result.summary["functions_added"] == 0
        assert result.summary["functions_removed"] == 0
        assert result.summary["functions_modified"] == 0

    def test_empty_graphs(self) -> None:
        result = SnapshotDiff(_graph([]), _graph([])).compute()
        assert not result.has_changes()


class TestSnapshotDiffNodes:
    """Node addition, removal, modification detection."""

    def test_added_nodes(self) -> None:
        baseline = _graph([_node("a.func", "func")])
        current = _graph(
            [
                _node("a.func", "func"),
                _node("b.bar", "bar"),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_added"] == 1
        assert result.nodes_added[0].node.name == "bar"
        assert result.nodes_added[0].change_type == "added"

    def test_removed_nodes(self) -> None:
        baseline = _graph(
            [
                _node("a.func", "func"),
                _node("b.bar", "bar"),
            ]
        )
        current = _graph([_node("a.func", "func")])
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_removed"] == 1
        assert result.nodes_removed[0].node.name == "bar"

    def test_modified_params(self) -> None:
        baseline = _graph([_node("a.func", "func", params=["x"])])
        current = _graph([_node("a.func", "func", params=["x", "y"])])
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_modified"] == 1
        assert "params_changed" in result.nodes_modified[0].modifications
        assert result.nodes_modified[0].old_node is not None

    def test_modified_return_type(self) -> None:
        baseline = _graph(
            [
                _node("a.func", "func", return_type="str"),
            ]
        )
        current = _graph(
            [
                _node("a.func", "func", return_type="int"),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_modified"] == 1
        assert "return_type_changed" in (result.nodes_modified[0].modifications)

    def test_modified_decorators(self) -> None:
        baseline = _graph([_node("a.func", "func", decorators=[])])
        current = _graph(
            [
                _node("a.func", "func", decorators=["@cache"]),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_modified"] == 1
        assert "decorators_changed" in (result.nodes_modified[0].modifications)

    def test_line_change_only_not_modified(self) -> None:
        """Line shifts alone should NOT count as modification."""
        baseline = _graph([_node("a.func:1", "func", line=1)])
        current = _graph([_node("a.func:5", "func", line=5)])
        result = SnapshotDiff(baseline, current).compute()
        # Fallback match by (name, file) should match them
        assert result.summary["functions_modified"] == 0
        assert result.summary["functions_added"] == 0
        assert result.summary["functions_removed"] == 0

    def test_mixed_changes(self) -> None:
        baseline = _graph(
            [
                _node("a.keep", "keep"),
                _node("b.remove", "remove"),
                _node("c.modify", "modify", params=["x"]),
            ]
        )
        current = _graph(
            [
                _node("a.keep", "keep"),
                _node("c.modify", "modify", params=["x", "y"]),
                _node("d.new", "new_func"),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_added"] == 1
        assert result.summary["functions_removed"] == 1
        assert result.summary["functions_modified"] == 1

    def test_parent_class_changed(self) -> None:
        baseline = _graph(
            [
                _node("a.meth", "meth", parent_class="OldClass"),
            ]
        )
        current = _graph(
            [
                _node("a.meth", "meth", parent_class="NewClass"),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_modified"] == 1
        assert "parent_class_changed" in (result.nodes_modified[0].modifications)


class TestSnapshotDiffEdges:
    """Edge addition and removal detection."""

    def test_added_edges(self) -> None:
        n1, n2 = _node("a.f1", "f1"), _node("b.f2", "f2")
        baseline = _graph([n1, n2])
        current = _graph([n1, n2], [_edge("a.f1", "b.f2")])
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["edges_added"] == 1
        assert result.edges_added[0].edge.source == "a.f1"

    def test_removed_edges(self) -> None:
        n1, n2 = _node("a.f1", "f1"), _node("b.f2", "f2")
        baseline = _graph([n1, n2], [_edge("a.f1", "b.f2")])
        current = _graph([n1, n2])
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["edges_removed"] == 1

    def test_cascade_edge_removed(self) -> None:
        """Edge removed because node was removed should be marked cascade."""
        n1, n2 = _node("a.f1", "f1"), _node("b.f2", "f2")
        baseline = _graph([n1, n2], [_edge("a.f1", "b.f2")])
        current = _graph([n1])  # n2 removed
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["edges_removed"] == 1
        assert result.edges_removed[0].is_cascade is True


class TestRenameDetection:
    """Rename detection via signature matching."""

    def test_rename_same_sig_diff_file(self) -> None:
        """Same name + params + return_type, different file = rename."""
        baseline = _graph(
            [
                _node("old.func", "func", fpath="old.py", params=["x"]),
            ]
        )
        current = _graph(
            [
                _node("new.func", "func", fpath="new.py", params=["x"]),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_renamed"] == 1
        assert result.summary["functions_added"] == 0
        assert result.summary["functions_removed"] == 0
        assert result.nodes_renamed[0].rename_from_file == "old.py"

    def test_no_rename_different_params(self) -> None:
        """Same name but different params = NOT rename."""
        baseline = _graph(
            [
                _node("old.func", "func", fpath="old.py", params=["x"]),
            ]
        )
        current = _graph(
            [
                _node("new.func", "func", fpath="new.py", params=["x", "y"]),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_renamed"] == 0
        assert result.summary["functions_added"] == 1
        assert result.summary["functions_removed"] == 1

    def test_no_rename_same_file(self) -> None:
        """Same name + params but SAME file = not a rename/move."""
        n1 = _node("a.func:1", "func", fpath="a.py", line=1)
        n2 = _node("a.func:10", "func", fpath="a.py", line=10)
        # These should fallback-match, not be rename
        baseline = _graph([n1])
        current = _graph([n2])
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_renamed"] == 0

    def test_rename_disabled(self) -> None:
        """include_renames=False skips rename detection."""
        baseline = _graph(
            [
                _node("old.func", "func", fpath="old.py"),
            ]
        )
        current = _graph(
            [
                _node("new.func", "func", fpath="new.py"),
            ]
        )
        result = SnapshotDiff(baseline, current).compute(include_renames=False)
        assert result.summary["functions_renamed"] == 0
        assert result.summary["functions_added"] == 1
        assert result.summary["functions_removed"] == 1

    def test_first_match_wins(self) -> None:
        """When 1 removed matches multiple added, first match wins."""
        baseline = _graph(
            [
                _node("old.func", "func", fpath="old.py"),
            ]
        )
        current = _graph(
            [
                _node("new1.func", "func", fpath="new1.py"),
                _node("new2.func", "func", fpath="new2.py"),
            ]
        )
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["functions_renamed"] == 1
        assert result.summary["functions_added"] == 1  # second one


class TestAffectedCallers:
    """Affected callers detection via BFS."""

    def test_depth_1_default(self) -> None:
        n1 = _node("a.caller", "caller")
        n2 = _node("b.changed", "changed", params=["x"])
        n2_new = _node("b.changed", "changed", params=["x", "y"])
        baseline = _graph([n1, n2], [_edge("a.caller", "b.changed")])
        current = _graph([n1, n2_new], [_edge("a.caller", "b.changed")])
        result = SnapshotDiff(baseline, current).compute(depth=1)
        assert result.summary["affected_callers"] == 1
        assert result.affected_callers[0].name == "caller"
        assert result.affected_callers[0].depth == 1

    def test_depth_2_transitive(self) -> None:
        n1 = _node("a.top", "top")
        n2 = _node("b.mid", "mid")
        n3 = _node("c.changed", "changed", params=["x"])
        n3_new = _node("c.changed", "changed", params=["x", "y"])
        edges = [
            _edge("a.top", "b.mid"),
            _edge("b.mid", "c.changed"),
        ]
        baseline = _graph([n1, n2, n3], edges)
        current = _graph([n1, n2, n3_new], edges)
        result = SnapshotDiff(baseline, current).compute(depth=2)
        names = {a.name for a in result.affected_callers}
        assert "mid" in names  # depth 1
        assert "top" in names  # depth 2

    def test_depth_capped_at_3(self) -> None:
        """Max depth is 3 even if larger value is passed."""
        nodes = [_node(f"n{i}", f"f{i}") for i in range(5)]
        nodes_new = list(nodes)
        nodes_new[4] = _node("n4", "f4", params=["new"])
        edges = [_edge(f"n{i}", f"n{i+1}") for i in range(4)]
        baseline = _graph(nodes, edges)
        current = _graph(nodes_new, edges)
        result = SnapshotDiff(baseline, current).compute(depth=10)
        max_d = max(a.depth for a in result.affected_callers)
        assert max_d <= 3

    def test_no_callers(self) -> None:
        """Node with no callers has empty affected list."""
        baseline = _graph([_node("a.f", "f", params=["x"])])
        current = _graph([_node("a.f", "f", params=["x", "y"])])
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["affected_callers"] == 0

    def test_dedup_multiple_sources(self) -> None:
        """Caller affected by 2 changed nodes should appear once."""
        caller = _node("a.caller", "caller")
        c1 = _node("b.c1", "c1", params=["x"])
        c2 = _node("c.c2", "c2", params=["a"])
        c1_new = _node("b.c1", "c1", params=["x", "y"])
        c2_new = _node("c.c2", "c2", params=["a", "b"])
        edges = [
            _edge("a.caller", "b.c1"),
            _edge("a.caller", "c.c2"),
        ]
        baseline = _graph([caller, c1, c2], edges)
        current = _graph([caller, c1_new, c2_new], edges)
        result = SnapshotDiff(baseline, current).compute()
        assert result.summary["affected_callers"] == 1
        assert len(result.affected_callers[0].source_changes) == 2


class TestDiffResult:
    """DiffResult properties."""

    def test_summary(self) -> None:
        baseline = _graph([_node("a.f", "f")])
        current = _graph([_node("a.f", "f"), _node("b.g", "g")])
        result = SnapshotDiff(baseline, current).compute()
        s = result.summary
        assert s["functions_added"] == 1
        assert s["functions_removed"] == 0

    def test_has_changes(self) -> None:
        baseline = _graph([_node("a.f", "f")])
        current = _graph([_node("a.f", "f"), _node("b.g", "g")])
        result = SnapshotDiff(baseline, current).compute()
        assert result.has_changes()

    def test_metadata_preserved(self) -> None:
        baseline = _graph([], label="v1")
        current = _graph([], label="v2")
        result = SnapshotDiff(baseline, current).compute()
        assert result.baseline_meta["label"] == "v1"
        assert result.current_meta["label"] == "v2"


class TestHelpers:
    """Helper function tests."""

    def test_detect_modifications_no_change(self) -> None:
        n = _node("a.f", "f", params=["x"], return_type="int")
        assert _detect_modifications(n, n) == []

    def test_detect_modifications_params(self) -> None:
        old = _node("a.f", "f", params=["x"])
        new = _node("a.f", "f", params=["x", "y"])
        mods = _detect_modifications(old, new)
        assert "params_changed" in mods

    def test_signature_match_true(self) -> None:
        a = _node("old.f", "f", fpath="old.py", params=["x"])
        b = _node("new.f", "f", fpath="new.py", params=["x"])
        assert _signature_match(a, b)

    def test_signature_match_same_file(self) -> None:
        a = _node("a.f", "f", fpath="a.py")
        b = _node("a.f2", "f", fpath="a.py")
        assert not _signature_match(a, b)

    def test_signature_match_diff_params(self) -> None:
        a = _node("old.f", "f", fpath="old.py", params=["x"])
        b = _node("new.f", "f", fpath="new.py", params=["y"])
        assert not _signature_match(a, b)
