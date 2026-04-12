# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CBM-P2: CLI snapshot-diff command."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from codebase_map.cli import main
from codebase_map.graph.models import Graph, LayerType, Node, NodeType
from codebase_map.snapshot import SnapshotManager


def _make_graph(label: str, sha: str, nodes_extra: list | None = None) -> Graph:
    """Helper — create a Graph with metadata."""
    g = Graph(project="test", generated_at="2026-04-12T10:00:00Z")
    g.metadata = {
        "version": "2.1",
        "generated_at": g.generated_at,
        "commit_sha": sha,
        "branch": "main",
        "label": label,
        "generator_version": "1.0.0",
        "source_paths": ["src/"],
        "stats": {"total_functions": 10, "total_files": 2, "total_edges": 5},
    }
    # Base nodes
    base = Node(
        id="a.func",
        name="func",
        node_type=NodeType.FUNCTION,
        layer=LayerType.CORE,
        module_domain="app",
        file_path="a.py",
        line_start=1,
        params=["x"],
    )
    g.add_node(base)
    for n in nodes_extra or []:
        g.add_node(n)
    return g


def _capture(argv: list[str]) -> str:
    captured = io.StringIO()
    old = sys.stdout
    sys.stdout = captured
    try:
        main(argv)
    except SystemExit:
        pass
    sys.stdout = old
    return captured.getvalue()


_YAML = (
    "project: test\nsources:\n"
    "  - path: src\noutput:\n"
    "  dir: out\n  formats: [json]\n"
)


class TestSnapshotDiffCLI:
    """CLI snapshot-diff command integration tests."""

    def test_text_output(self, tmp_path: Path) -> None:
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("baseline", "aaa1111"))
        new_node = Node(
            id="b.bar",
            name="bar",
            node_type=NodeType.FUNCTION,
            layer=LayerType.UTIL,
            module_domain="app",
            file_path="b.py",
            line_start=1,
        )
        mgr.save(_make_graph("postdev", "bbb2222", [new_node]))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture(
            [
                "snapshot-diff",
                "--baseline",
                "baseline",
                "--current",
                "postdev",
                "-c",
                str(config),
            ]
        )
        assert "Added:" in output
        assert "bar" in output

    def test_json_output(self, tmp_path: Path) -> None:
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("v1", "aaa1111"))
        mgr.save(_make_graph("v2", "bbb2222"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture(
            [
                "snapshot-diff",
                "--baseline",
                "v1",
                "--current",
                "v2",
                "--format",
                "json",
                "-c",
                str(config),
            ]
        )
        data = json.loads(output)
        assert "summary" in data
        assert "baseline_meta" in data

    def test_markdown_output(self, tmp_path: Path) -> None:
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("baseline", "aaa1111"))
        mgr.save(_make_graph("postdev", "bbb2222"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture(
            [
                "snapshot-diff",
                "--baseline",
                "baseline",
                "--current",
                "postdev",
                "--format",
                "markdown",
                "-c",
                str(config),
            ]
        )
        assert "Impact Analysis" in output

    def test_test_plan_output(self, tmp_path: Path) -> None:
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("baseline", "aaa1111"))
        mgr.save(_make_graph("postdev", "bbb2222"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture(
            [
                "snapshot-diff",
                "--baseline",
                "baseline",
                "--current",
                "postdev",
                "--test-plan",
                "-c",
                str(config),
            ]
        )
        assert "Test Plan" in output

    def test_baseline_not_found(self, tmp_path: Path) -> None:
        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture(
            [
                "snapshot-diff",
                "--baseline",
                "nonexistent",
                "--current",
                "also-missing",
                "-c",
                str(config),
            ]
        )
        assert "ERROR" in output

    def test_help_shows_snapshot_diff(self) -> None:
        output = _capture(["--help"])
        assert "snapshot-diff" in output

    def test_by_file_path(self, tmp_path: Path) -> None:
        """Can pass direct file paths instead of labels."""
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        p1 = mgr.save(_make_graph("v1", "aaa1111"))
        p2 = mgr.save(_make_graph("v2", "bbb2222"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture(
            [
                "snapshot-diff",
                "--baseline",
                str(p1),
                "--current",
                str(p2),
                "--format",
                "json",
                "-c",
                str(config),
            ]
        )
        data = json.loads(output)
        assert "summary" in data
