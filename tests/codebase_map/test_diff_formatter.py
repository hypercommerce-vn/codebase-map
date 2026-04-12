# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CBM-P2-05/06/07/08: Diff output formatters."""

from __future__ import annotations

import json

from codebase_map.graph.diff_formatter import (
    filter_breaking_only,
    format_diff_json,
    format_diff_markdown,
    format_diff_text,
    format_test_plan,
)
from codebase_map.graph.models import Edge, EdgeType, Graph, LayerType, Node, NodeType
from codebase_map.graph.snapshot_diff import SnapshotDiff


def _node(
    nid: str,
    name: str,
    fpath: str = "a.py",
    line: int = 1,
    params: list[str] | None = None,
    layer: LayerType = LayerType.CORE,
    domain: str = "app",
) -> Node:
    return Node(
        id=nid,
        name=name,
        node_type=NodeType.FUNCTION,
        layer=layer,
        module_domain=domain,
        file_path=fpath,
        line_start=line,
        params=params or [],
    )


def _graph(
    nodes: list[Node],
    edges: list[Edge] | None = None,
    label: str = "test",
    branch: str = "main",
    sha: str = "abc1234",
) -> Graph:
    g = Graph(project="test", generated_at="2026-04-12T10:00:00Z")
    g.metadata = {
        "label": label,
        "commit_sha": sha,
        "branch": branch,
        "generated_at": "2026-04-12T10:00:00Z",
    }
    for n in nodes:
        g.add_node(n)
    for e in edges or []:
        g.edges.append(e)
    return g


def _edge(src: str, tgt: str) -> Edge:
    return Edge(source=src, target=tgt, edge_type=EdgeType.CALLS)


def _make_diff_result():
    """Helper: create a DiffResult with mixed changes."""
    baseline = _graph(
        [
            _node("a.keep", "keep"),
            _node("b.remove", "remove"),
            _node("c.modify", "modify", params=["x"]),
            _node("d.caller", "caller"),
        ],
        [_edge("d.caller", "c.modify")],
        label="baseline",
        sha="aaa1111",
    )
    current = _graph(
        [
            _node("a.keep", "keep"),
            _node("c.modify", "modify", params=["x", "y"]),
            _node("e.new_func", "new_func"),
            _node("d.caller", "caller"),
        ],
        [_edge("d.caller", "c.modify")],
        label="post-dev",
        sha="bbb2222",
    )
    return SnapshotDiff(baseline, current).compute(depth=1)


class TestFormatDiffJson:
    """P2-06: JSON output."""

    def test_valid_json(self) -> None:
        result = _make_diff_result()
        output = format_diff_json(result)
        data = json.loads(output)
        assert "summary" in data
        assert "baseline_meta" in data
        assert "current_meta" in data

    def test_summary_counts(self) -> None:
        result = _make_diff_result()
        data = json.loads(format_diff_json(result))
        s = data["summary"]
        assert s["functions_added"] == 1
        assert s["functions_removed"] == 1
        assert s["functions_modified"] == 1

    def test_node_changes_in_json(self) -> None:
        result = _make_diff_result()
        data = json.loads(format_diff_json(result))
        assert len(data["nodes_added"]) == 1
        assert data["nodes_added"][0]["name"] == "new_func"
        assert data["nodes_removed"][0]["name"] == "remove"

    def test_empty_diff_json(self) -> None:
        g = _graph([_node("a.f", "f")])
        result = SnapshotDiff(g, g).compute()
        data = json.loads(format_diff_json(result))
        assert data["summary"]["functions_added"] == 0


class TestFormatDiffMarkdown:
    """P2-05: Markdown output."""

    def test_header_present(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "Impact Analysis" in md

    def test_baseline_info(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "baseline" in md
        assert "post-dev" in md
        assert "aaa1111" in md

    def test_summary_table(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "Functions added" in md
        assert "Functions removed" in md
        assert "Affected callers" in md

    def test_details_tag(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "<details>" in md
        assert "</details>" in md

    def test_added_section(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "Added Functions" in md
        assert "`new_func`" in md

    def test_removed_section(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "Removed Functions" in md
        assert "`remove`" in md

    def test_modified_section(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "Modified Functions" in md
        assert "params_changed" in md

    def test_no_changes_message(self) -> None:
        g = _graph([_node("a.f", "f")])
        result = SnapshotDiff(g, g).compute()
        md = format_diff_markdown(result)
        assert "No structural changes" in md

    def test_affected_callers_section(self) -> None:
        result = _make_diff_result()
        md = format_diff_markdown(result)
        assert "Affected Callers" in md
        assert "`caller`" in md


class TestFormatDiffText:
    """Text output for terminal."""

    def test_basic_output(self) -> None:
        result = _make_diff_result()
        txt = format_diff_text(result)
        assert "Added:" in txt
        assert "Removed:" in txt
        assert "Modified:" in txt

    def test_no_changes_text(self) -> None:
        g = _graph([_node("a.f", "f")])
        result = SnapshotDiff(g, g).compute()
        txt = format_diff_text(result)
        assert "No structural changes" in txt

    def test_baseline_info_text(self) -> None:
        result = _make_diff_result()
        txt = format_diff_text(result)
        assert "Baseline:" in txt
        assert "Current:" in txt


class TestFilterBreakingOnly:
    """P2-07: --breaking-only filter."""

    def test_removes_added_nodes(self) -> None:
        result = _make_diff_result()
        filtered = filter_breaking_only(result)
        assert len(filtered.nodes_added) == 0

    def test_keeps_modified_with_callers(self) -> None:
        result = _make_diff_result()
        filtered = filter_breaking_only(result)
        # modify has caller "d.caller" → should keep
        assert len(filtered.nodes_modified) == 1

    def test_removes_nodes_without_callers(self) -> None:
        """Removed node 'remove' has no callers → filtered out."""
        result = _make_diff_result()
        filtered = filter_breaking_only(result)
        assert len(filtered.nodes_removed) == 0

    def test_preserves_affected_callers(self) -> None:
        result = _make_diff_result()
        filtered = filter_breaking_only(result)
        assert len(filtered.affected_callers) == len(result.affected_callers)


class TestFormatTestPlan:
    """P2-08: --test-plan output."""

    def test_grouped_by_domain(self) -> None:
        result = _make_diff_result()
        plan = format_test_plan(result)
        assert "Suggested Test Plan" in plan
        assert "Domain:" in plan

    def test_no_callers_message(self) -> None:
        g = _graph([_node("a.f", "f")])
        result = SnapshotDiff(g, g).compute()
        plan = format_test_plan(result)
        assert "No affected callers" in plan

    def test_total_count(self) -> None:
        result = _make_diff_result()
        plan = format_test_plan(result)
        assert "Total:" in plan
        assert "functions need testing" in plan

    def test_caller_name_in_plan(self) -> None:
        result = _make_diff_result()
        plan = format_test_plan(result)
        assert "`caller`" in plan
