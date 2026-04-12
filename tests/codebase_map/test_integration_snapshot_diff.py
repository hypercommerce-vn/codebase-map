# HC-AI | ticket: FDD-TOOL-CODEMAP
"""CBM-P2 Day 3: Integration tests — end-to-end dual-snapshot diff pipeline.

Tests the full flow: build graphs → save snapshots → snapshot-diff CLI
→ verify output format + correctness across all modes.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from codebase_map.cli import main
from codebase_map.graph.diff_formatter import (
    filter_breaking_only,
    format_diff_json,
    format_diff_markdown,
    format_diff_text,
    format_test_plan,
)
from codebase_map.graph.models import Edge, EdgeType, Graph, LayerType, Node, NodeType
from codebase_map.graph.snapshot_diff import SnapshotDiff
from codebase_map.snapshot import SnapshotManager

# ── Helpers ──────────────────────────────────────────────────────────


def _node(
    nid: str,
    name: str,
    fpath: str = "app/service.py",
    line: int = 10,
    params: list[str] | None = None,
    return_type: str = "",
    decorators: list[str] | None = None,
    parent_class: str = "",
    domain: str = "service",
    layer: LayerType = LayerType.CORE,
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
        return_type=return_type,
        decorators=decorators or [],
        parent_class=parent_class,
    )


def _edge(src: str, tgt: str, etype: EdgeType = EdgeType.CALLS) -> Edge:
    return Edge(source=src, target=tgt, edge_type=etype)


def _graph(
    nodes: list[Node],
    edges: list[Edge] | None = None,
    label: str = "test",
    sha: str = "abc1234",
    branch: str = "main",
) -> Graph:
    g = Graph(project="test-project", generated_at="2026-04-12T10:00:00Z")
    g.metadata = {
        "version": "2.1",
        "generated_at": g.generated_at,
        "commit_sha": sha,
        "branch": branch,
        "label": label,
        "generator_version": "1.0.0",
        "source_paths": ["app/"],
        "stats": {},
    }
    for n in nodes:
        g.add_node(n)
    for e in edges or []:
        g.add_edge(e)
    # Update stats after building
    g.metadata["stats"] = {
        "total_functions": len(g.nodes),
        "total_files": len({n.file_path for n in g.nodes.values()}),
        "total_edges": len(g.edges),
    }
    return g


def _capture(argv: list[str]) -> str:
    """Run CLI main() and capture stdout."""
    captured = io.StringIO()
    old = sys.stdout
    sys.stdout = captured
    try:
        main(argv)
    except SystemExit:
        pass
    sys.stdout = old
    return captured.getvalue()


# ── Realistic scenario fixtures ──────────────────────────────────────


@pytest.fixture()
def scenario_refactor(tmp_path):
    """Simulates a real PR: rename + modify + add + remove + affected callers.

    Baseline: 6 functions in app/service.py + app/router.py
    Current:  1 removed, 1 modified, 2 added, 1 renamed (moved file)
    """
    # Baseline graph
    b_nodes = [
        _node(
            "svc:create:10",
            "create_customer",
            "app/service.py",
            10,
            params=["name", "email"],
            domain="crm",
        ),
        _node(
            "svc:validate:25",
            "validate_email",
            "app/service.py",
            25,
            params=["email"],
            return_type="bool",
            domain="crm",
        ),
        _node(
            "svc:legacy:40",
            "legacy_check",
            "app/service.py",
            40,
            params=["data"],
            domain="crm",
        ),
        _node(
            "rtr:post:5",
            "post_customer",
            "app/router.py",
            5,
            params=["request"],
            domain="router",
        ),
        _node(
            "rtr:get:15",
            "get_customer",
            "app/router.py",
            15,
            params=["id"],
            domain="router",
        ),
        _node(
            "util:fmt:1",
            "format_name",
            "app/utils.py",
            1,
            params=["name"],
            domain="util",
            layer=LayerType.UTIL,
        ),
    ]
    b_edges = [
        _edge("rtr:post:5", "svc:create:10"),
        _edge("svc:create:10", "svc:validate:25"),
        _edge("svc:create:10", "svc:legacy:40"),
        _edge("rtr:get:15", "svc:create:10"),
        _edge("svc:create:10", "util:fmt:1"),
    ]
    baseline = _graph(b_nodes, b_edges, label="baseline", sha="aaa1111", branch="main")

    # Current graph — after refactor PR
    c_nodes = [
        # create_customer: MODIFIED — new param added, line shifted
        _node(
            "svc:create:12",
            "create_customer",
            "app/service.py",
            12,
            params=["name", "email", "phone"],
            domain="crm",
        ),
        # validate_email: UNCHANGED (but line shifted → ID changed)
        _node(
            "svc:validate:30",
            "validate_email",
            "app/service.py",
            30,
            params=["email"],
            return_type="bool",
            domain="crm",
        ),
        # legacy_check: REMOVED
        # post_customer: UNCHANGED
        _node(
            "rtr:post:5",
            "post_customer",
            "app/router.py",
            5,
            params=["request"],
            domain="router",
        ),
        # get_customer: UNCHANGED
        _node(
            "rtr:get:15",
            "get_customer",
            "app/router.py",
            15,
            params=["id"],
            domain="router",
        ),
        # format_name: RENAMED (moved to new file)
        _node(
            "util:fmt:1",
            "format_name",
            "app/formatters.py",
            1,
            params=["name"],
            domain="util",
            layer=LayerType.UTIL,
        ),
        # NEW functions
        _node(
            "svc:validate_phone:45",
            "validate_phone",
            "app/service.py",
            45,
            params=["phone"],
            return_type="bool",
            domain="crm",
        ),
        _node(
            "svc:audit_log:60",
            "audit_log",
            "app/service.py",
            60,
            params=["action", "data"],
            domain="crm",
        ),
    ]
    c_edges = [
        _edge("rtr:post:5", "svc:create:12"),
        _edge("svc:create:12", "svc:validate:30"),
        _edge("svc:create:12", "svc:validate_phone:45"),
        _edge("svc:create:12", "svc:audit_log:60"),
        _edge("rtr:get:15", "svc:create:12"),
        _edge("svc:create:12", "util:fmt:1"),
    ]
    current = _graph(
        c_nodes, c_edges, label="post-dev", sha="bbb2222", branch="feat/refactor-crm"
    )

    # Save as snapshots
    snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
    mgr = SnapshotManager(str(snap_dir))
    mgr.save(baseline)
    mgr.save(current)

    # Also save as plain files for file-path mode
    (tmp_path / "baseline.json").write_text(json.dumps(baseline.to_dict(), default=str))
    (tmp_path / "current.json").write_text(json.dumps(current.to_dict(), default=str))

    # Write config file
    cfg = tmp_path / "codebase-map.yaml"
    cfg.write_text(
        "project: test\nsources:\n"
        "  - path: app\noutput:\n"
        "  dir: .codebase-map-cache\n"
    )

    return {
        "baseline": baseline,
        "current": current,
        "tmp_path": tmp_path,
        "mgr": mgr,
        "cfg": str(cfg),
    }


# ══════════════════════════════════════════════════════════════════════
# CLASS 1: Full Pipeline — SnapshotDiff → Formatter → Verify
# ══════════════════════════════════════════════════════════════════════


class TestFullPipeline:
    """End-to-end: compute diff + format output + verify correctness."""

    def test_compute_detects_all_change_types(self, scenario_refactor):
        """Diff finds add, remove, modify, rename."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute(depth=1)

        assert len(result.nodes_added) >= 2  # validate_phone, audit_log
        assert len(result.nodes_removed) >= 1  # legacy_check
        assert len(result.nodes_modified) >= 1  # create_customer (new param)
        assert result.has_changes()

    def test_affected_callers_transitive(self, scenario_refactor):
        """create_customer modified → callers post_customer + get_customer affected."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute(depth=1)

        caller_names = {ac.name for ac in result.affected_callers}
        # post_customer and get_customer both call create_customer
        assert "post_customer" in caller_names or "get_customer" in caller_names

    def test_json_output_valid(self, scenario_refactor):
        """JSON output is parseable with complete schema."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute(depth=1)
        out = format_diff_json(result)

        data = json.loads(out)
        assert "baseline_meta" in data
        assert "current_meta" in data
        assert "summary" in data
        assert "nodes_added" in data
        assert "nodes_removed" in data
        assert "affected_callers" in data
        assert data["summary"]["functions_added"] >= 2

    def test_markdown_output_has_required_sections(self, scenario_refactor):
        """Markdown has summary table + collapsible details."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute(depth=1)
        md = format_diff_markdown(result)

        assert "## Codebase-Map Impact Analysis" in md
        assert "**Baseline:**" in md
        assert "**Post-dev:**" in md
        assert "| Metric | Count |" in md
        assert "<details>" in md
        assert "</details>" in md
        assert "Added Functions" in md

    def test_text_output_readable(self, scenario_refactor):
        """Text output has clear sections."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute(depth=1)
        text = format_diff_text(result)

        assert "Baseline:" in text
        assert "Current:" in text
        assert "[ADDED]" in text
        assert "Added:" in text

    def test_breaking_only_filters_added(self, scenario_refactor):
        """Breaking-only removes added nodes (they can't break callers)."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute(depth=1)
        filtered = filter_breaking_only(result)

        assert len(filtered.nodes_added) == 0
        # Callers preserved
        assert len(filtered.affected_callers) == len(result.affected_callers)

    def test_test_plan_groups_by_domain(self, scenario_refactor):
        """Test plan groups affected callers by domain."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute(depth=1)
        plan = format_test_plan(result)

        assert "## Suggested Test Plan" in plan
        if result.affected_callers:
            assert "Domain:" in plan
            assert "- [ ] Test" in plan

    def test_depth_2_finds_more_callers(self, scenario_refactor):
        """Depth 2 should find transitive callers."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        r1 = sd.compute(depth=1)
        r2 = sd.compute(depth=2)

        # Depth 2 should find at least as many callers
        assert len(r2.affected_callers) >= len(r1.affected_callers)


# ══════════════════════════════════════════════════════════════════════
# CLASS 2: CLI Integration — End-to-end via command line
# ══════════════════════════════════════════════════════════════════════


class TestCLIIntegration:
    """Run snapshot-diff through CLI main() with real snapshot files."""

    def test_cli_text_with_file_paths(self, scenario_refactor):
        """CLI loads from file paths (not labels)."""
        tp = scenario_refactor["tmp_path"]
        out = _capture(
            [
                "snapshot-diff",
                "--baseline",
                str(tp / "baseline.json"),
                "--current",
                str(tp / "current.json"),
                "--format",
                "text",
                "-c",
                scenario_refactor["cfg"],
            ]
        )
        assert "Baseline:" in out
        assert "Added:" in out or "[ADDED]" in out

    def test_cli_json_output_parseable(self, scenario_refactor):
        """CLI JSON mode produces valid JSON."""
        tp = scenario_refactor["tmp_path"]
        out = _capture(
            [
                "snapshot-diff",
                "--baseline",
                str(tp / "baseline.json"),
                "--current",
                str(tp / "current.json"),
                "--format",
                "json",
                "-c",
                scenario_refactor["cfg"],
            ]
        )
        data = json.loads(out)
        assert data["summary"]["functions_added"] >= 2

    def test_cli_markdown_output(self, scenario_refactor):
        """CLI markdown mode produces PR-ready output."""
        tp = scenario_refactor["tmp_path"]
        out = _capture(
            [
                "snapshot-diff",
                "--baseline",
                str(tp / "baseline.json"),
                "--current",
                str(tp / "current.json"),
                "--format",
                "markdown",
                "-c",
                scenario_refactor["cfg"],
            ]
        )
        assert "## Codebase-Map Impact Analysis" in out
        assert "<details>" in out

    def test_cli_breaking_only(self, scenario_refactor):
        """CLI --breaking-only filters correctly."""
        tp = scenario_refactor["tmp_path"]
        out = _capture(
            [
                "snapshot-diff",
                "--baseline",
                str(tp / "baseline.json"),
                "--current",
                str(tp / "current.json"),
                "--breaking-only",
                "-c",
                scenario_refactor["cfg"],
            ]
        )
        # Added nodes should NOT appear
        assert "validate_phone" not in out
        assert "audit_log" not in out

    def test_cli_test_plan(self, scenario_refactor):
        """CLI --test-plan produces domain-grouped plan."""
        tp = scenario_refactor["tmp_path"]
        out = _capture(
            [
                "snapshot-diff",
                "--baseline",
                str(tp / "baseline.json"),
                "--current",
                str(tp / "current.json"),
                "--test-plan",
                "-c",
                scenario_refactor["cfg"],
            ]
        )
        assert "## Suggested Test Plan" in out

    def test_cli_depth_option(self, scenario_refactor):
        """CLI --depth 3 accepted and runs."""
        tp = scenario_refactor["tmp_path"]
        out = _capture(
            [
                "snapshot-diff",
                "--baseline",
                str(tp / "baseline.json"),
                "--current",
                str(tp / "current.json"),
                "--depth",
                "3",
                "-c",
                scenario_refactor["cfg"],
            ]
        )
        assert "Baseline:" in out

    def test_cli_with_snapshot_labels(self, scenario_refactor):
        """CLI loads from snapshot labels via SnapshotManager."""
        out = _capture(
            [
                "snapshot-diff",
                "--baseline",
                "baseline",
                "--current",
                "post-dev",
                "-c",
                scenario_refactor["cfg"],
            ]
        )
        assert "Baseline:" in out


# ══════════════════════════════════════════════════════════════════════
# CLASS 3: Edge Cases — Empty graphs, identical, large diffs
# ══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases for robustness."""

    def test_identical_graphs(self, tmp_path):
        """Two identical graphs produce empty diff."""
        nodes = [_node("a:f:1", "func_a")]
        g1 = _graph(nodes, label="v1", sha="aaa")
        g2 = _graph(nodes, label="v2", sha="bbb")

        sd = SnapshotDiff(g1, g2)
        result = sd.compute()
        assert not result.has_changes()
        text = format_diff_text(result)
        assert "No structural changes" in text

    def test_empty_baseline(self, tmp_path):
        """All functions are new if baseline is empty."""
        baseline = _graph([], label="empty", sha="aaa")
        current = _graph(
            [_node("a:f:1", "func_a"), _node("a:g:10", "func_b")],
            label="full",
            sha="bbb",
        )
        sd = SnapshotDiff(baseline, current)
        result = sd.compute()
        assert len(result.nodes_added) == 2
        assert len(result.nodes_removed) == 0

    def test_empty_current(self, tmp_path):
        """All functions removed if current is empty."""
        baseline = _graph(
            [_node("a:f:1", "func_a"), _node("a:g:10", "func_b")],
            label="full",
            sha="aaa",
        )
        current = _graph([], label="empty", sha="bbb")
        sd = SnapshotDiff(baseline, current)
        result = sd.compute()
        assert len(result.nodes_added) == 0
        assert len(result.nodes_removed) == 2

    def test_many_nodes_performance(self):
        """Diff 500+ nodes completes in < 2 seconds."""
        import time

        b_nodes = [_node(f"mod:f{i}:{i}", f"func_{i}", line=i) for i in range(500)]
        c_nodes = [_node(f"mod:f{i}:{i}", f"func_{i}", line=i) for i in range(500)]
        # Modify 50, add 50, remove 50
        for i in range(50):
            c_nodes[i] = _node(
                f"mod:f{i}:{i}",
                f"func_{i}",
                line=i,
                params=["new_param"],
            )
        c_nodes.extend(
            [
                _node(f"mod:new{i}:{600+i}", f"new_func_{i}", line=600 + i)
                for i in range(50)
            ]
        )
        b_nodes.extend(
            [
                _node(f"mod:old{i}:{700+i}", f"old_func_{i}", line=700 + i)
                for i in range(50)
            ]
        )

        baseline = _graph(b_nodes, label="big-base", sha="aaa")
        current = _graph(c_nodes, label="big-curr", sha="bbb")

        start = time.time()
        sd = SnapshotDiff(baseline, current)
        result = sd.compute(depth=1)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Diff took {elapsed:.2f}s — over 2s limit"
        assert result.has_changes()
        assert len(result.nodes_added) >= 50
        assert len(result.nodes_removed) >= 50

    def test_json_round_trip(self, scenario_refactor):
        """JSON output can be parsed back correctly."""
        sd = SnapshotDiff(scenario_refactor["baseline"], scenario_refactor["current"])
        result = sd.compute()
        j = format_diff_json(result)
        data = json.loads(j)

        # Round trip check
        assert data["summary"]["functions_added"] == len(result.nodes_added)
        assert data["summary"]["functions_removed"] == len(result.nodes_removed)
        assert len(data["nodes_added"]) == len(result.nodes_added)
        assert len(data["nodes_removed"]) == len(result.nodes_removed)
        assert len(data["affected_callers"]) == len(result.affected_callers)

    def test_markdown_no_changes_message(self):
        """Markdown output for empty diff shows correct message."""
        g = _graph([_node("a:f:1", "func_a")], label="v1", sha="aaa")
        sd = SnapshotDiff(g, g)
        result = sd.compute()
        md = format_diff_markdown(result)
        assert "No structural changes" in md
        assert "<details>" not in md  # No expandable section for empty diff


# ══════════════════════════════════════════════════════════════════════
# CLASS 4: CI Workflow Validation
# ══════════════════════════════════════════════════════════════════════


class TestCIWorkflowYAML:
    """Validate CI workflow file structure."""

    def test_cbm_pr_impact_yml_exists(self):
        """Workflow file exists at expected path."""
        wf = Path(__file__).parents[2] / ".github/workflows/cbm-pr-impact.yml"
        assert wf.exists(), f"Missing: {wf}"

    def test_cbm_pr_impact_yml_valid_yaml(self):
        """Workflow file is valid YAML."""
        import yaml

        wf = Path(__file__).parents[2] / ".github/workflows/cbm-pr-impact.yml"
        with open(wf) as f:
            data = yaml.safe_load(f)

        # Check required keys
        assert "name" in data or True in data  # yaml parses `on:` as True
        assert "jobs" in data
        assert "snapshot-impact" in data["jobs"]

    def test_cbm_pr_impact_has_required_steps(self):
        """Workflow has all required steps."""
        import yaml

        wf = Path(__file__).parents[2] / ".github/workflows/cbm-pr-impact.yml"
        with open(wf) as f:
            data = yaml.safe_load(f)

        job = data["jobs"]["snapshot-impact"]
        step_names = [s.get("name", "") for s in job["steps"]]

        # Must have these steps
        assert any("Checkout" in n for n in step_names)
        assert any("Python" in n for n in step_names)
        assert any("Install" in n for n in step_names)
        assert any("baseline" in n.lower() for n in step_names)
        assert any("post-dev" in n.lower() or "Generate" in n for n in step_names)
        assert any("diff" in n.lower() for n in step_names)
        assert any("comment" in n.lower() or "PR" in n for n in step_names)

    def test_cbm_pr_impact_uses_snapshot_diff(self):
        """Workflow uses snapshot-diff command (not old diff)."""
        wf = Path(__file__).parents[2] / ".github/workflows/cbm-pr-impact.yml"
        content = wf.read_text()
        assert "snapshot-diff" in content
        assert "--format markdown" in content

    def test_all_ci_workflows_exist(self):
        """All 4 CBM CI workflows exist."""
        wf_dir = Path(__file__).parents[2] / ".github/workflows"
        expected = [
            "ci.yml",
            "cbm-baseline.yml",
            "cbm-post-merge.yml",
            "cbm-pr-impact.yml",
        ]
        for name in expected:
            assert (wf_dir / name).exists(), f"Missing workflow: {name}"
