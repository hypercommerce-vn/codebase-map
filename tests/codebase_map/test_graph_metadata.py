# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CBM-P1-01: Graph metadata + from_dict backward compat."""

from __future__ import annotations

import json
from pathlib import Path

from codebase_map.graph.models import Edge, EdgeType, Graph, LayerType, Node, NodeType

# --- Graph.to_dict metadata ---


class TestGraphMetadata:
    """CBM-P1-01: Graph.to_dict includes metadata block."""

    def test_to_dict_includes_metadata_when_present(self) -> None:
        """to_dict outputs metadata key when graph.metadata is populated."""
        g = Graph(project="test", generated_at="2026-04-12T00:00:00Z")
        g.metadata = {"version": "2.1", "label": "baseline", "commit_sha": "abc123"}
        d = g.to_dict()
        assert "metadata" in d
        assert d["metadata"]["version"] == "2.1"
        assert d["metadata"]["label"] == "baseline"

    def test_to_dict_omits_metadata_when_empty(self) -> None:
        """to_dict does NOT output metadata key when graph.metadata is empty."""
        g = Graph(project="test", generated_at="2026-04-12T00:00:00Z")
        d = g.to_dict()
        assert "metadata" not in d

    def test_to_dict_roundtrip_json(self, tmp_path: Path) -> None:
        """to_dict → JSON → from_dict preserves metadata."""
        g = Graph(project="roundtrip", generated_at="2026-04-12T00:00:00Z")
        g.metadata = {
            "version": "2.1",
            "label": "test",
            "commit_sha": "deadbeef",
            "branch": "main",
            "generator_version": "1.0.0",
        }
        node = Node(
            id="mod.func",
            name="func",
            node_type=NodeType.FUNCTION,
            layer=LayerType.UTIL,
            module_domain="core",
            file_path="mod.py",
            line_start=1,
        )
        g.add_node(node)
        edge = Edge(source="mod.func", target="mod.other", edge_type=EdgeType.CALLS)
        g.add_edge(edge)

        # Serialize
        json_path = tmp_path / "graph.json"
        json_path.write_text(json.dumps(g.to_dict(), indent=2))

        # Deserialize
        data = json.loads(json_path.read_text())
        g2 = Graph.from_dict(data)

        assert g2.project == "roundtrip"
        assert g2.metadata["version"] == "2.1"
        assert g2.metadata["label"] == "test"
        assert g2.metadata["commit_sha"] == "deadbeef"
        assert len(g2.nodes) == 1
        assert len(g2.edges) == 1
        assert "mod.func" in g2.nodes

    def test_metadata_stats_in_to_dict(self) -> None:
        """to_dict always includes stats at top level."""
        g = Graph(project="stats-test")
        node = Node(
            id="a",
            name="a",
            node_type=NodeType.FUNCTION,
            layer=LayerType.CORE,
            module_domain="x",
            file_path="a.py",
            line_start=1,
        )
        g.add_node(node)
        d = g.to_dict()
        assert d["stats"]["total_nodes"] == 1


# --- Graph.from_dict backward compat ---


class TestGraphFromDict:
    """CBM-P1-01 / CBM-P1-06: from_dict handles v1.x and v2.1 formats."""

    def test_from_dict_v21_with_metadata(self) -> None:
        """from_dict loads v2.1 format with metadata block."""
        data = {
            "project": "my-project",
            "generated_at": "2026-04-12T10:00:00Z",
            "metadata": {
                "version": "2.1",
                "label": "baseline",
                "commit_sha": "abc1234",
                "branch": "develop",
                "generator_version": "1.0.0",
            },
            "nodes": [
                {
                    "id": "mod.MyClass",
                    "name": "MyClass",
                    "type": "class",
                    "layer": "model",
                    "domain": "crm",
                    "file": "models/customer.py",
                    "line_start": 10,
                    "line_end": 50,
                    "params": [],
                    "return_type": "",
                }
            ],
            "edges": [
                {"source": "mod.MyClass", "target": "mod.Base", "type": "inherits"}
            ],
        }
        g = Graph.from_dict(data)
        assert g.project == "my-project"
        assert g.metadata["version"] == "2.1"
        assert g.metadata["label"] == "baseline"
        assert len(g.nodes) == 1
        assert g.nodes["mod.MyClass"].layer == LayerType.MODEL
        assert len(g.edges) == 1
        assert g.edges[0].edge_type == EdgeType.INHERITS

    def test_from_dict_v1x_legacy_no_metadata(self) -> None:
        """from_dict handles v1.x format (no metadata key) gracefully."""
        data = {
            "project": "legacy",
            "generated_at": "2026-01-01",
            "nodes": [
                {
                    "id": "app.main",
                    "name": "main",
                    "type": "function",
                    "layer": "core",
                    "domain": "app",
                    "file": "app.py",
                    "line_start": 1,
                }
            ],
            "edges": [],
        }
        g = Graph.from_dict(data)
        assert g.metadata["version"] == "1.x-legacy"
        assert g.metadata["label"] == ""
        assert len(g.nodes) == 1

    def test_from_dict_empty_graph(self) -> None:
        """from_dict handles completely empty data."""
        g = Graph.from_dict({})
        assert g.project == ""
        assert len(g.nodes) == 0
        assert len(g.edges) == 0
        assert g.metadata["version"] == "1.x-legacy"

    def test_from_dict_skips_malformed_nodes(self) -> None:
        """from_dict skips nodes with missing required fields."""
        data = {
            "nodes": [
                {
                    "id": "good",
                    "name": "good",
                    "type": "function",
                    "layer": "core",
                    "domain": "x",
                    "file": "a.py",
                    "line_start": 1,
                },
                {"bad": "missing-id"},  # missing required fields
            ],
            "edges": [],
        }
        g = Graph.from_dict(data)
        assert len(g.nodes) == 1
        assert "good" in g.nodes

    def test_from_dict_skips_malformed_edges(self) -> None:
        """from_dict skips edges with invalid edge type."""
        data = {
            "nodes": [],
            "edges": [
                {"source": "a", "target": "b", "type": "calls"},
                {"source": "c", "target": "d", "type": "INVALID_TYPE"},
            ],
        }
        g = Graph.from_dict(data)
        assert len(g.edges) == 1


# --- git info + auto label helpers ---


class TestGitInfoHelpers:
    """CBM-P1-01: _collect_git_info and _auto_label."""

    def test_collect_git_info_returns_dict(self, tmp_path: Path) -> None:
        """_collect_git_info returns dict with commit_sha and branch keys."""
        from codebase_map.graph.builder import _collect_git_info

        info = _collect_git_info(tmp_path)
        assert "commit_sha" in info
        assert "branch" in info

    def test_collect_git_info_on_real_repo(self) -> None:
        """_collect_git_info returns real values on a git repo."""
        from codebase_map.graph.builder import _collect_git_info

        # This test runs in the codebase-map repo itself
        info = _collect_git_info(Path.cwd())
        # Should have non-empty values (we're in a git repo)
        assert info["commit_sha"] != ""
        assert info["branch"] != ""

    def test_auto_label_format(self) -> None:
        """_auto_label produces branch_sha_timestamp format."""
        from codebase_map.graph.builder import _auto_label

        label = _auto_label({"branch": "main", "commit_sha": "abc1234"})
        assert label.startswith("main_abc1234_")
        assert len(label) > 20  # includes timestamp

    def test_auto_label_sanitizes_branch(self) -> None:
        """_auto_label converts / in branch names to _."""
        from codebase_map.graph.builder import _auto_label

        label = _auto_label({"branch": "feat/my-feature", "commit_sha": "def5678"})
        assert label.startswith("feat_my-feature_def5678_")
        assert "/" not in label

    def test_auto_label_fallback_on_empty(self) -> None:
        """_auto_label handles empty git info gracefully."""
        from codebase_map.graph.builder import _auto_label

        label = _auto_label({"branch": "", "commit_sha": ""})
        assert label.startswith("unknown_unknown_")
