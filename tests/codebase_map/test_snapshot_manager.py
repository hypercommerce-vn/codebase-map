# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CBM-P1-03: SnapshotManager — save/list/clean/load."""

from __future__ import annotations

import json
from pathlib import Path

from codebase_map.graph.models import Edge, EdgeType, Graph, LayerType, Node, NodeType
from codebase_map.snapshot import SnapshotInfo, SnapshotManager, _sanitize_filename


def _make_graph(label: str = "test", sha: str = "abc1234", date: str = "") -> Graph:
    """Helper — create a Graph with v2.1 metadata for testing."""
    g = Graph(project="test-project", generated_at=date or "2026-04-12T10:00:00Z")
    g.metadata = {
        "version": "2.1",
        "generated_at": g.generated_at,
        "commit_sha": sha,
        "branch": "main",
        "label": label,
        "generator_version": "1.0.0",
        "source_paths": ["src/"],
        "stats": {
            "total_functions": 10,
            "total_files": 3,
            "total_edges": 15,
        },
    }
    node = Node(
        id="mod.func",
        name="func",
        node_type=NodeType.FUNCTION,
        layer=LayerType.CORE,
        module_domain="app",
        file_path="mod.py",
        line_start=1,
    )
    g.add_node(node)
    edge = Edge(source="mod.func", target="mod.other", edge_type=EdgeType.CALLS)
    g.add_edge(edge)
    return g


class TestSnapshotManagerSave:
    """CBM-P1-03: SnapshotManager.save()."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """save() creates a JSON file in the cache directory."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="baseline", sha="deadbeef")
        path = mgr.save(g)

        assert path.exists()
        assert path.suffix == ".json"
        assert "baseline" in path.name
        assert "deadbee" in path.name  # short sha (7 chars)

    def test_save_naming_convention(self, tmp_path: Path) -> None:
        """save() follows graph_{label}_{sha}.json convention."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="post-dev", sha="1234567890")
        path = mgr.save(g)

        assert path.name == "graph_post-dev_1234567.json"

    def test_save_content_valid_json(self, tmp_path: Path) -> None:
        """Saved file is valid JSON with metadata."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="test-json")
        path = mgr.save(g)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert "metadata" in data
        assert data["metadata"]["label"] == "test-json"
        assert len(data["nodes"]) == 1
        assert len(data["edges"]) == 1

    def test_save_custom_output_path(self, tmp_path: Path) -> None:
        """save() with output_path writes to custom location."""
        mgr = SnapshotManager(str(tmp_path / "default"))
        custom = tmp_path / "custom" / "my_snapshot.json"
        g = _make_graph(label="custom")
        path = mgr.save(g, output_path=str(custom))

        assert path == custom
        assert custom.exists()

    def test_save_sanitizes_label(self, tmp_path: Path) -> None:
        """save() sanitizes unsafe chars in label for filename."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="feat/my-branch", sha="abc1234")
        path = mgr.save(g)

        assert "/" not in path.name
        assert "feat_my-branch" in path.name

    def test_save_creates_cache_dir(self, tmp_path: Path) -> None:
        """SnapshotManager creates cache dir if it doesn't exist."""
        deep_path = tmp_path / "a" / "b" / "c"
        SnapshotManager(str(deep_path))
        assert deep_path.exists()


class TestSnapshotManagerList:
    """CBM-P1-03: SnapshotManager.list_snapshots()."""

    def test_list_empty_dir(self, tmp_path: Path) -> None:
        """list_snapshots() returns empty list for empty dir."""
        mgr = SnapshotManager(str(tmp_path))
        assert mgr.list_snapshots() == []

    def test_list_returns_snapshot_info(self, tmp_path: Path) -> None:
        """list_snapshots() returns SnapshotInfo objects."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="v1", sha="aaa1111")
        mgr.save(g)

        snaps = mgr.list_snapshots()
        assert len(snaps) == 1
        assert isinstance(snaps[0], SnapshotInfo)
        assert snaps[0].label == "v1"
        assert snaps[0].sha == "aaa1111"
        assert snaps[0].nodes == 10
        assert snaps[0].edges == 15

    def test_list_sorted_by_date_desc(self, tmp_path: Path) -> None:
        """list_snapshots() sorted newest first."""
        mgr = SnapshotManager(str(tmp_path))

        g1 = _make_graph(label="old", sha="aaa0001", date="2026-04-10T08:00:00Z")
        g2 = _make_graph(label="new", sha="bbb0002", date="2026-04-12T08:00:00Z")
        g3 = _make_graph(label="mid", sha="ccc0003", date="2026-04-11T08:00:00Z")

        mgr.save(g1)
        mgr.save(g2)
        mgr.save(g3)

        snaps = mgr.list_snapshots()
        assert len(snaps) == 3
        assert snaps[0].label == "new"
        assert snaps[1].label == "mid"
        assert snaps[2].label == "old"

    def test_list_skips_malformed_files(self, tmp_path: Path) -> None:
        """list_snapshots() skips non-JSON or malformed files."""
        mgr = SnapshotManager(str(tmp_path))

        # Save a valid one
        g = _make_graph(label="valid", sha="good123")
        mgr.save(g)

        # Create a malformed one
        bad = tmp_path / "graph_bad_0000000.json"
        bad.write_text("not valid json {{{", encoding="utf-8")

        snaps = mgr.list_snapshots()
        assert len(snaps) == 1
        assert snaps[0].label == "valid"

    def test_list_nonexistent_dir(self, tmp_path: Path) -> None:
        """list_snapshots() returns empty for dir that was deleted."""
        mgr = SnapshotManager(str(tmp_path / "gone"))
        # Dir created by __init__, remove it
        (tmp_path / "gone").rmdir()
        assert mgr.list_snapshots() == []

    def test_snapshot_info_to_dict(self, tmp_path: Path) -> None:
        """SnapshotInfo.to_dict() returns correct dict."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="dicttest", sha="abc1234")
        mgr.save(g)

        snaps = mgr.list_snapshots()
        d = snaps[0].to_dict()
        assert d["label"] == "dicttest"
        assert d["sha"] == "abc1234"
        assert isinstance(d["size_bytes"], int)


class TestSnapshotManagerClean:
    """CBM-P1-03: SnapshotManager.clean()."""

    def test_clean_no_op_when_few(self, tmp_path: Path) -> None:
        """clean() does nothing when fewer than keep count."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="only", sha="aaa0001")
        mgr.save(g)

        removed, kept = mgr.clean(keep=5)
        assert removed == 0
        assert kept == 1

    def test_clean_removes_oldest(self, tmp_path: Path) -> None:
        """clean(keep=2) removes oldest snapshots."""
        mgr = SnapshotManager(str(tmp_path))

        for i in range(5):
            g = _make_graph(
                label=f"snap{i}",
                sha=f"sha{i:04d}0",
                date=f"2026-04-{10 + i:02d}T08:00:00Z",
            )
            mgr.save(g)

        assert len(mgr.list_snapshots()) == 5

        removed, kept = mgr.clean(keep=2)
        assert removed == 3
        assert kept == 2

        remaining = mgr.list_snapshots()
        assert len(remaining) == 2
        # Newest kept
        labels = {s.label for s in remaining}
        assert "snap4" in labels
        assert "snap3" in labels

    def test_clean_keep_zero(self, tmp_path: Path) -> None:
        """clean(keep=0) removes all snapshots."""
        mgr = SnapshotManager(str(tmp_path))
        for i in range(3):
            g = _make_graph(label=f"s{i}", sha=f"sha{i:04d}0")
            mgr.save(g)

        removed, kept = mgr.clean(keep=0)
        assert removed == 3
        assert kept == 0
        assert len(mgr.list_snapshots()) == 0

    def test_clean_empty_dir(self, tmp_path: Path) -> None:
        """clean() on empty dir returns (0, 0)."""
        mgr = SnapshotManager(str(tmp_path))
        removed, kept = mgr.clean(keep=5)
        assert removed == 0
        assert kept == 0


class TestSnapshotManagerLoad:
    """CBM-P1-03: SnapshotManager.load()."""

    def test_load_by_file_path(self, tmp_path: Path) -> None:
        """load() with a file path loads that file directly."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="loadme", sha="abc1234")
        path = mgr.save(g)

        loaded = mgr.load(str(path))
        assert loaded.project == "test-project"
        assert loaded.metadata["label"] == "loadme"
        assert len(loaded.nodes) == 1

    def test_load_by_label(self, tmp_path: Path) -> None:
        """load() with a label searches snapshots."""
        mgr = SnapshotManager(str(tmp_path))
        g = _make_graph(label="baseline", sha="def5678")
        mgr.save(g)

        loaded = mgr.load("baseline")
        assert loaded.metadata["label"] == "baseline"
        assert loaded.metadata["commit_sha"] == "def5678"

    def test_load_label_newest(self, tmp_path: Path) -> None:
        """load() by label returns the newest matching snapshot."""
        mgr = SnapshotManager(str(tmp_path))

        g1 = _make_graph(label="release", sha="old0001", date="2026-04-10T08:00:00Z")
        g2 = _make_graph(label="release", sha="new0002", date="2026-04-12T08:00:00Z")
        mgr.save(g1)
        mgr.save(g2)

        loaded = mgr.load("release")
        assert loaded.metadata["commit_sha"] == "new0002"

    def test_load_not_found_raises(self, tmp_path: Path) -> None:
        """load() raises FileNotFoundError for unknown label."""
        mgr = SnapshotManager(str(tmp_path))

        try:
            mgr.load("nonexistent")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError as exc:
            assert "nonexistent" in str(exc)
            assert "snapshots list" in str(exc)

    def test_load_roundtrip_preserves_data(self, tmp_path: Path) -> None:
        """save → load roundtrip preserves all graph data."""
        mgr = SnapshotManager(str(tmp_path))
        original = _make_graph(label="roundtrip", sha="rnd1234")
        mgr.save(original)

        loaded = mgr.load("roundtrip")
        assert loaded.project == original.project
        assert loaded.generated_at == original.generated_at
        assert loaded.metadata == original.metadata
        assert len(loaded.nodes) == len(original.nodes)
        assert len(loaded.edges) == len(original.edges)
        assert "mod.func" in loaded.nodes


class TestSanitizeFilename:
    """CBM-P1-03: _sanitize_filename helper."""

    def test_slashes_replaced(self) -> None:
        assert _sanitize_filename("feat/my-branch") == "feat_my-branch"

    def test_spaces_replaced(self) -> None:
        assert _sanitize_filename("my label") == "my_label"

    def test_special_chars_removed(self) -> None:
        result = _sanitize_filename("test@#$%label!")
        assert "@" not in result
        assert "#" not in result

    def test_empty_returns_unknown(self) -> None:
        assert _sanitize_filename("") == "unknown"

    def test_dots_and_dashes_preserved(self) -> None:
        assert _sanitize_filename("v2.1-beta") == "v2.1-beta"
