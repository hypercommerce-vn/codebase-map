# HC-AI | ticket: MEM-M1-01
"""Tests for CodebaseVault — vault init, schema, commit, query, snapshot."""

import sqlite3
from pathlib import Path

import pytest

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.vault import CodebaseVault


class TestCodebaseVaultInit:
    """Tests for vault initialization."""

    def test_init_creates_structure(self, tmp_path: Path) -> None:
        """init() creates .knowledge-memory/ with core.db + config.yaml."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        vault_dir = tmp_path / ".knowledge-memory"
        assert vault_dir.exists()
        assert (vault_dir / "core.db").exists()
        assert (vault_dir / "config.yaml").exists()
        assert (vault_dir / "verticals" / "codebase" / "vault.db").exists()

    def test_init_core_db_schema(self, tmp_path: Path) -> None:
        """core.db has _meta, patterns, snapshots, usage_log tables."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        db = tmp_path / ".knowledge-memory" / "core.db"
        with sqlite3.connect(str(db)) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert "_meta" in tables
        assert "patterns" in tables
        assert "snapshots" in tables
        assert "usage_log" in tables

    def test_init_schema_version(self, tmp_path: Path) -> None:
        """core.db _meta has schema_version = 1."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        db = tmp_path / ".knowledge-memory" / "core.db"
        with sqlite3.connect(str(db)) as conn:
            row = conn.execute(
                "SELECT value FROM _meta WHERE key = 'schema_version'"
            ).fetchone()
        assert row is not None
        assert row[0] == "1"

    def test_init_vertical_db_schema(self, tmp_path: Path) -> None:
        """vault.db has cb_nodes, cb_edges, cb_file_ownership tables."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        db = tmp_path / ".knowledge-memory" / "verticals" / "codebase" / "vault.db"
        with sqlite3.connect(str(db)) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            }
        assert "cb_nodes" in tables
        assert "cb_edges" in tables
        assert "cb_file_ownership" in tables

    def test_init_config_yaml(self, tmp_path: Path) -> None:
        """config.yaml contains schema_version and verticals."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        config = (tmp_path / ".knowledge-memory" / "config.yaml").read_text()
        assert "schema_version: 1" in config
        assert "codebase" in config

    def test_init_idempotent_raises(self, tmp_path: Path) -> None:
        """init() twice without force raises FileExistsError."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        with pytest.raises(FileExistsError, match="already exists"):
            vault.init(tmp_path)

    def test_init_force_reinitializes(self, tmp_path: Path) -> None:
        """init() with force=True works on existing vault."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.init(tmp_path, force=True)
        assert (tmp_path / ".knowledge-memory" / "core.db").exists()

    def test_vertical_name(self) -> None:
        """VERTICAL_NAME is 'codebase'."""
        assert CodebaseVault.VERTICAL_NAME == "codebase"


class TestCodebaseVaultOperations:
    """Tests for vault operations: commit, query, snapshot."""

    @pytest.fixture()
    def vault(self, tmp_path: Path) -> CodebaseVault:
        """Create and initialize a vault."""
        v = CodebaseVault()
        v.init(tmp_path)
        return v

    def test_commit_pattern(self, vault: CodebaseVault) -> None:
        """commit_pattern() inserts a pattern into core.db."""
        p = Pattern(
            name="test::pattern",
            category="test",
            confidence=85.0,
            vertical="codebase",
        )
        vault.commit_pattern(p)
        patterns = vault.query_patterns()
        assert len(patterns) == 1
        assert patterns[0].name == "test::pattern"
        assert patterns[0].confidence == 85.0

    def test_query_patterns_by_category(self, vault: CodebaseVault) -> None:
        """query_patterns(category=...) filters correctly."""
        vault.commit_pattern(Pattern(name="a", category="naming", confidence=90.0))
        vault.commit_pattern(Pattern(name="b", category="layer", confidence=80.0))
        naming = vault.query_patterns(category="naming")
        assert len(naming) == 1
        assert naming[0].name == "a"

    def test_query_patterns_ordered_by_confidence(self, vault: CodebaseVault) -> None:
        """Patterns returned in descending confidence order."""
        vault.commit_pattern(Pattern(name="low", category="test", confidence=50.0))
        vault.commit_pattern(Pattern(name="high", category="test", confidence=95.0))
        patterns = vault.query_patterns()
        assert patterns[0].name == "high"
        assert patterns[1].name == "low"

    def test_snapshot_creates_record(self, vault: CodebaseVault) -> None:
        """snapshot() creates a record in snapshots table."""
        result = vault.snapshot()
        assert "id" in result
        assert "created_at" in result
        assert "evidence_count" in result

    def test_snapshot_with_label(self, vault: CodebaseVault) -> None:
        """snapshot(label=...) stores label in result."""
        result = vault.snapshot(label="bootstrap-run-1")
        assert result["label"] == "bootstrap-run-1"

    def test_snapshot_saves_evidence_data(self, vault: CodebaseVault) -> None:
        """snapshot() saves full evidence corpus, restorable via load_snapshot."""
        evs = [
            Evidence(
                source="a.py",
                data={"name": "func_a", "type": "function"},
                line_range=(1, 10),
            ),
            Evidence(
                source="b.py",
                data={"name": "ClassB", "type": "class"},
                line_range=(5, 20),
                metadata={"layer": "service"},
            ),
        ]
        vault.load_evidences(evs)
        result = vault.snapshot(label="test-snap")
        assert result["evidence_count"] == 2

        # Restore from snapshot
        restored = vault.load_snapshot(result["id"])
        assert len(restored) == 2
        assert restored[0].source == "a.py"
        assert restored[0].data["name"] == "func_a"
        assert restored[0].line_range == (1, 10)
        assert restored[1].metadata.get("layer") == "service"

    def test_snapshot_rotation(self, vault: CodebaseVault) -> None:
        """Only 5 snapshots kept after rotation."""
        for _ in range(8):
            vault.snapshot()

        assert vault._core_db is not None
        with sqlite3.connect(str(vault._core_db)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()[0]
        assert count == 5

    def test_snapshot_rotation_keeps_newest(self, vault: CodebaseVault) -> None:
        """Rotation keeps the 5 newest snapshots, not oldest."""
        for i in range(7):
            vault.snapshot(label=f"snap-{i}")

        snapshots = vault.list_snapshots()
        assert len(snapshots) == 5
        # Newest first
        labels = [s["label"] for s in snapshots]
        assert labels[0] == "snap-6"
        assert labels[-1] == "snap-2"

    def test_list_snapshots(self, vault: CodebaseVault) -> None:
        """list_snapshots() returns all snapshots newest first."""
        vault.snapshot(label="first")
        vault.snapshot(label="second")

        snaps = vault.list_snapshots()
        assert len(snaps) == 2
        assert snaps[0]["label"] == "second"
        assert snaps[1]["label"] == "first"
        assert "id" in snaps[0]
        assert "created_at" in snaps[0]
        assert "evidence_count" in snaps[0]

    def test_list_snapshots_empty(self, vault: CodebaseVault) -> None:
        """list_snapshots() returns empty list when no snapshots."""
        assert vault.list_snapshots() == []

    def test_load_snapshot_not_found(self, vault: CodebaseVault) -> None:
        """load_snapshot() raises ValueError for nonexistent ID."""
        with pytest.raises(ValueError, match="not found"):
            vault.load_snapshot(9999)

    def test_load_snapshot_restores_to_memory(self, vault: CodebaseVault) -> None:
        """load_snapshot() also sets _evidences for immediate learner use."""
        evs = [Evidence(source="x.py", data={"name": "x"})]
        vault.load_evidences(evs)
        snap = vault.snapshot()

        # Clear memory
        vault.load_evidences([])
        assert list(vault.get_corpus_iterator()) == []

        # Restore
        vault.load_snapshot(snap["id"])
        result = list(vault.get_corpus_iterator())
        assert len(result) == 1
        assert result[0].data["name"] == "x"

    def test_snapshot_count(self, vault: CodebaseVault) -> None:
        """snapshot_count() returns correct count."""
        assert vault.snapshot_count() == 0
        vault.snapshot()
        vault.snapshot()
        assert vault.snapshot_count() == 2

    def test_corpus_iterator_empty(self, vault: CodebaseVault) -> None:
        """get_corpus_iterator() yields nothing by default."""
        assert list(vault.get_corpus_iterator()) == []

    def test_load_and_iterate_evidences(self, vault: CodebaseVault) -> None:
        """load_evidences() + get_corpus_iterator() round-trips."""
        evs = [
            Evidence(source="a.py", data={"name": "func_a"}),
            Evidence(source="b.py", data={"name": "func_b"}),
        ]
        vault.load_evidences(evs)
        result = list(vault.get_corpus_iterator())
        assert len(result) == 2
        assert result[0].data["name"] == "func_a"

    def test_open_existing_vault(self, tmp_path: Path) -> None:
        """open() works on an existing vault."""
        v1 = CodebaseVault()
        v1.init(tmp_path)
        v1.commit_pattern(Pattern(name="x", category="test", confidence=70.0))

        v2 = CodebaseVault()
        v2.open(tmp_path)
        patterns = v2.query_patterns()
        assert len(patterns) == 1

    def test_open_nonexistent_raises(self, tmp_path: Path) -> None:
        """open() raises FileNotFoundError if no vault."""
        vault = CodebaseVault()
        with pytest.raises(FileNotFoundError, match="No vault found"):
            vault.open(tmp_path / "nonexistent")

    def test_store_nodes(self, vault: CodebaseVault, tmp_path: Path) -> None:
        """store_nodes() inserts into cb_nodes."""
        nodes = [
            {
                "name": "my_func",
                "file_path": "app/service.py",
                "node_type": "function",
                "layer": "service",
                "line_start": 10,
                "line_end": 25,
            }
        ]
        vault.store_nodes(nodes)

        db = tmp_path / ".knowledge-memory" / "verticals" / "codebase" / "vault.db"
        with sqlite3.connect(str(db)) as conn:
            rows = conn.execute("SELECT name, layer FROM cb_nodes").fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "my_func"
        assert rows[0][1] == "service"

    def test_store_edges(self, vault: CodebaseVault, tmp_path: Path) -> None:
        """store_edges() inserts into cb_edges."""
        edges = [
            {
                "source": "func_a",
                "target": "func_b",
                "type": "calls",
                "file_path": "app/main.py",
            }
        ]
        vault.store_edges(edges)

        db = tmp_path / ".knowledge-memory" / "verticals" / "codebase" / "vault.db"
        with sqlite3.connect(str(db)) as conn:
            rows = conn.execute(
                "SELECT source_name, target_name FROM cb_edges"
            ).fetchall()
        assert len(rows) == 1
        assert rows[0] == ("func_a", "func_b")

    # HC-AI | ticket: MEM-M1-04
    def test_schema_has_indices(self, tmp_path: Path) -> None:
        """Extension schema creates performance indices."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        db = tmp_path / ".knowledge-memory" / "verticals" / "codebase" / "vault.db"
        with sqlite3.connect(str(db)) as conn:
            indices = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                ).fetchall()
            }
        assert "idx_cb_nodes_name" in indices
        assert "idx_cb_nodes_layer" in indices
        assert "idx_cb_edges_source" in indices
        assert "idx_cb_edges_target" in indices
        assert "idx_cb_ownership_file" in indices

    # HC-AI | ticket: MEM-M1-04
    def test_query_nodes_all(self, vault: CodebaseVault) -> None:
        """query_nodes() returns all nodes when no filter."""
        vault.store_nodes(
            [
                {"name": "a", "file_path": "x.py", "layer": "service"},
                {"name": "b", "file_path": "y.py", "layer": "model"},
            ]
        )
        result = vault.query_nodes()
        assert len(result) == 2

    # HC-AI | ticket: MEM-M1-04
    def test_query_nodes_filter_layer(self, vault: CodebaseVault) -> None:
        """query_nodes(layer=...) filters correctly."""
        vault.store_nodes(
            [
                {"name": "a", "file_path": "x.py", "layer": "service"},
                {"name": "b", "file_path": "y.py", "layer": "model"},
                {"name": "c", "file_path": "z.py", "layer": "service"},
            ]
        )
        result = vault.query_nodes(layer="service")
        assert len(result) == 2
        assert all(r["layer"] == "service" for r in result)

    # HC-AI | ticket: MEM-M1-04
    def test_query_nodes_filter_type(self, vault: CodebaseVault) -> None:
        """query_nodes(node_type=...) filters correctly."""
        vault.store_nodes(
            [
                {"name": "a", "node_type": "function"},
                {"name": "B", "node_type": "class"},
            ]
        )
        result = vault.query_nodes(node_type="class")
        assert len(result) == 1
        assert result[0]["name"] == "B"

    # HC-AI | ticket: MEM-M1-04
    def test_query_edges_all(self, vault: CodebaseVault) -> None:
        """query_edges() returns all edges."""
        vault.store_edges(
            [
                {"source": "a", "target": "b"},
                {"source": "c", "target": "d"},
            ]
        )
        result = vault.query_edges()
        assert len(result) == 2

    # HC-AI | ticket: MEM-M1-04
    def test_query_edges_filter_source(self, vault: CodebaseVault) -> None:
        """query_edges(source_name=...) filters correctly."""
        vault.store_edges(
            [
                {"source": "a", "target": "b"},
                {"source": "a", "target": "c"},
                {"source": "x", "target": "y"},
            ]
        )
        result = vault.query_edges(source_name="a")
        assert len(result) == 2

    # HC-AI | ticket: MEM-M1-04
    def test_node_count(self, vault: CodebaseVault) -> None:
        """node_count() returns correct count."""
        assert vault.node_count() == 0
        vault.store_nodes([{"name": "a"}, {"name": "b"}])
        assert vault.node_count() == 2

    # HC-AI | ticket: MEM-M1-04
    def test_edge_count(self, vault: CodebaseVault) -> None:
        """edge_count() returns correct count."""
        assert vault.edge_count() == 0
        vault.store_edges([{"source": "a", "target": "b"}])
        assert vault.edge_count() == 1
