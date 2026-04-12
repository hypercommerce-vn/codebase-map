# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CBM-P1-04/05: CLI snapshots list + clean commands."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from codebase_map.cli import main
from codebase_map.graph.models import Graph, LayerType, Node, NodeType
from codebase_map.snapshot import SnapshotManager


def _make_graph(label: str, sha: str, date: str = "") -> Graph:
    """Helper — create a Graph with metadata for CLI tests."""
    g = Graph(project="test", generated_at=date or "2026-04-12T10:00:00Z")
    g.metadata = {
        "version": "2.1",
        "generated_at": g.generated_at,
        "commit_sha": sha,
        "branch": "main",
        "label": label,
        "generator_version": "1.0.0",
        "source_paths": ["src/"],
        "stats": {"total_functions": 50, "total_files": 10, "total_edges": 80},
    }
    node = Node(
        id="a.func",
        name="func",
        node_type=NodeType.FUNCTION,
        layer=LayerType.CORE,
        module_domain="app",
        file_path="a.py",
        line_start=1,
    )
    g.add_node(node)
    return g


def _capture_output(argv: list[str]) -> str:
    """Run CLI main() and capture stdout."""
    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        main(argv)
    except SystemExit:
        pass
    sys.stdout = old_stdout
    return captured.getvalue()


_YAML = (
    "project: test\nsources:\n"
    "  - path: src\noutput:\n"
    "  dir: out\n  formats: [json]\n"
)


class TestSnapshotsList:
    """CBM-P1-04: snapshots list command."""

    def test_list_empty(self, tmp_path: Path) -> None:
        """snapshots list with no snapshots shows empty message."""
        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)
        output = _capture_output(["snapshots", "list", "-c", str(config)])
        assert "No snapshots found" in output

    def test_list_shows_snapshots(self, tmp_path: Path) -> None:
        """snapshots list displays table with snapshot info."""
        # Setup: create snapshots
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("baseline", "aaa1111", "2026-04-10T08:00:00Z"))
        mgr.save(_make_graph("post-dev", "bbb2222", "2026-04-12T10:00:00Z"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture_output(["snapshots", "list", "-c", str(config)])
        assert "SNAPSHOTS (2 found)" in output
        assert "baseline" in output
        assert "post-dev" in output
        assert "aaa1111" in output
        assert "bbb2222" in output

    def test_list_json_output(self, tmp_path: Path) -> None:
        """snapshots list --json outputs valid JSON array."""
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("test-json", "ccc3333"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture_output(["snapshots", "list", "-c", str(config), "--json"])
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["label"] == "test-json"
        assert data[0]["sha"] == "ccc3333"

    def test_list_sorted_newest_first(self, tmp_path: Path) -> None:
        """snapshots list shows newest first."""
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("old", "old0001", "2026-04-01T08:00:00Z"))
        mgr.save(_make_graph("new", "new0002", "2026-04-12T08:00:00Z"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture_output(["snapshots", "list", "-c", str(config)])
        # "new" should appear before "old" in output
        new_pos = output.index("new")
        old_pos = output.index("old")
        assert new_pos < old_pos

    def test_list_help_text(self) -> None:
        """snapshots appears in main help."""
        output = _capture_output(["--help"])
        assert "snapshots" in output


class TestSnapshotsClean:
    """CBM-P1-05: snapshots clean command."""

    def test_clean_empty(self, tmp_path: Path) -> None:
        """snapshots clean with no snapshots shows message."""
        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)
        output = _capture_output(["snapshots", "clean", "-c", str(config)])
        assert "No snapshots to clean" in output

    def test_clean_removes_old(self, tmp_path: Path) -> None:
        """snapshots clean --keep 2 removes oldest."""
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        for i in range(5):
            mgr.save(
                _make_graph(
                    f"snap{i}",
                    f"sha{i:04d}0",
                    f"2026-04-{10 + i:02d}T08:00:00Z",
                )
            )

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture_output(
            ["snapshots", "clean", "--keep", "2", "-c", str(config)]
        )
        assert "Removed 3" in output
        assert "kept 2" in output

        # Verify only 2 remain
        remaining = mgr.list_snapshots()
        assert len(remaining) == 2

    def test_clean_default_keep_10(self, tmp_path: Path) -> None:
        """snapshots clean default keeps 10."""
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        for i in range(12):
            mgr.save(
                _make_graph(
                    f"s{i}",
                    f"sha{i:04d}0",
                    f"2026-04-{1 + i:02d}T08:00:00Z",
                )
            )

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture_output(["snapshots", "clean", "-c", str(config)])
        assert "Removed 2" in output
        assert "kept 10" in output

    def test_clean_no_op_when_below_keep(self, tmp_path: Path) -> None:
        """snapshots clean does nothing when count <= keep."""
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        mgr = SnapshotManager(str(snap_dir))
        mgr.save(_make_graph("only", "sha0001"))

        config = tmp_path / "codebase-map.yaml"
        config.write_text(_YAML)

        output = _capture_output(
            ["snapshots", "clean", "--keep", "5", "-c", str(config)]
        )
        assert "Removed 0" in output
        assert "kept 1" in output
