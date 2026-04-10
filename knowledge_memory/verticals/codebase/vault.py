# HC-AI | ticket: MEM-M1-01
"""CodebaseVault — concrete vault for the Codebase Memory vertical."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.core.vault.base import BaseVault

# HC-AI | ticket: MEM-M1-01
_CORE_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS _meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patterns (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    confidence    REAL    NOT NULL DEFAULT 0.0,
    vertical      TEXT    NOT NULL,
    evidence_json TEXT    NOT NULL DEFAULT '[]',
    metadata_json TEXT    NOT NULL DEFAULT '{}',
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT    NOT NULL,
    data_json  TEXT    NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS usage_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    action     TEXT NOT NULL,
    detail     TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
"""

# HC-AI | ticket: MEM-M1-04 (schema extension — placed here for Day 1 init)
_CODEBASE_EXTENSION_SQL = """\
CREATE TABLE IF NOT EXISTS cb_nodes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    file_path TEXT NOT NULL,
    node_type TEXT NOT NULL DEFAULT 'function',
    layer     TEXT NOT NULL DEFAULT 'unknown',
    line_start INTEGER NOT NULL DEFAULT 0,
    line_end   INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS cb_edges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    target_name TEXT NOT NULL,
    edge_type   TEXT NOT NULL DEFAULT 'calls',
    file_path   TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS cb_file_ownership (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    author    TEXT NOT NULL,
    commits   INTEGER NOT NULL DEFAULT 0,
    pct       REAL    NOT NULL DEFAULT 0.0
);
"""


class CodebaseVault(BaseVault):
    """Concrete vault for the Codebase Memory vertical.

    Manages ``.knowledge-memory/`` directory with SQLite storage
    for patterns, snapshots, and codebase-specific tables (nodes,
    edges, file_ownership).
    """

    VERTICAL_NAME = "codebase"

    def __init__(self) -> None:
        self._root: Optional[Path] = None
        self._vault_dir: Optional[Path] = None
        self._core_db: Optional[Path] = None
        self._vertical_db: Optional[Path] = None
        self._evidences: List[Evidence] = []

    @property
    def vault_dir(self) -> Path:
        """Return the vault directory path."""
        if self._vault_dir is None:
            raise RuntimeError("Vault not initialized. Call init() first.")
        return self._vault_dir

    def init(self, root: Path, force: bool = False) -> None:
        """Create ``.knowledge-memory/`` structure + SQLite databases.

        Idempotent unless force=True. If vault already exists and
        force is False, raises FileExistsError.
        """
        self._root = root
        self._vault_dir = root / ".knowledge-memory"
        self._core_db = self._vault_dir / "core.db"
        vert_dir = self._vault_dir / "verticals" / self.VERTICAL_NAME
        self._vertical_db = vert_dir / "vault.db"

        if self._vault_dir.exists() and not force:
            raise FileExistsError(
                f"Vault already exists at {self._vault_dir}. "
                "Use --force to reinitialize."
            )

        # Create directories
        self._vault_dir.mkdir(parents=True, exist_ok=True)
        vert_dir.mkdir(parents=True, exist_ok=True)

        # Create core.db with core schema
        with sqlite3.connect(str(self._core_db)) as conn:
            conn.executescript(_CORE_SCHEMA_SQL)
            conn.execute(
                "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
                ("schema_version", "1"),
            )
            conn.execute(
                "INSERT OR REPLACE INTO _meta (key, value) VALUES (?, ?)",
                ("created_at", datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

        # Create vertical vault.db with extension schema
        with sqlite3.connect(str(self._vertical_db)) as conn:
            conn.executescript(self.schema_extension_sql())
            conn.commit()

        # Write config.yaml
        config_path = self._vault_dir / "config.yaml"
        config_path.write_text(
            "# Knowledge Memory vault config\n"
            "schema_version: 1\n"
            f"created_at: {datetime.now(timezone.utc).isoformat()}\n"
            "verticals:\n"
            "  - codebase\n"
            "sources:\n"
            "  include:\n"
            '    - "**/*.py"\n'
            "  exclude:\n"
            '    - "**/__pycache__/**"\n'
            '    - "**/test_*"\n'
            '    - "**/.venv/**"\n'
        )

    def _ensure_initialized(self) -> None:
        """Raise RuntimeError if vault not initialized."""
        if self._vault_dir is None or not self._vault_dir.exists():
            raise RuntimeError("Vault not initialized. Call init() first.")

    def open(self, root: Path) -> None:
        """Open an existing vault at root (without creating)."""
        vault_dir = root / ".knowledge-memory"
        if not vault_dir.exists():
            raise FileNotFoundError(f"No vault found at {vault_dir}. Run init() first.")
        self._root = root
        self._vault_dir = vault_dir
        self._core_db = vault_dir / "core.db"
        vert_dir = vault_dir / "verticals" / self.VERTICAL_NAME
        self._vertical_db = vert_dir / "vault.db"

    # HC-AI | ticket: MEM-M1-03
    def snapshot(self, label: Optional[str] = None) -> Dict[str, object]:
        """Save current corpus state as a snapshot with full evidence data.

        Args:
            label: Optional human-readable label (e.g. ``"bootstrap-run-1"``).

        Returns:
            Dict with ``id``, ``created_at``, ``evidence_count``, ``label``.
        """
        self._ensure_initialized()
        assert self._core_db is not None
        ts = datetime.now(timezone.utc).isoformat()

        # Serialize full evidence corpus for reproducibility
        evidence_payload = []
        for ev in self._evidences:
            evidence_payload.append(
                {
                    "source": ev.source,
                    "data": ev.data,
                    "line_range": list(ev.line_range) if ev.line_range else None,
                    "commit_sha": ev.commit_sha,
                    "metadata": ev.metadata,
                }
            )

        data = {
            "evidence_count": len(self._evidences),
            "evidences": evidence_payload,
            "timestamp": ts,
            "label": label or "",
        }

        with sqlite3.connect(str(self._core_db)) as conn:
            cursor = conn.execute(
                "INSERT INTO snapshots (created_at, data_json) VALUES (?, ?)",
                (ts, json.dumps(data)),
            )
            snap_id = cursor.lastrowid

            # Rotation: keep only last 5 snapshots (design decision D-M1-06)
            conn.execute(
                "DELETE FROM snapshots WHERE id NOT IN "
                "(SELECT id FROM snapshots ORDER BY id DESC LIMIT 5)"
            )
            conn.commit()

        return {
            "id": snap_id,
            "created_at": ts,
            "evidence_count": len(self._evidences),
            "label": label or "",
        }

    # HC-AI | ticket: MEM-M1-03
    def list_snapshots(self) -> List[Dict[str, object]]:
        """List all snapshots in the vault, newest first.

        Returns:
            List of dicts with ``id``, ``created_at``, ``evidence_count``,
            ``label``.
        """
        self._ensure_initialized()
        assert self._core_db is not None
        with sqlite3.connect(str(self._core_db)) as conn:
            rows = conn.execute(
                "SELECT id, created_at, data_json " "FROM snapshots ORDER BY id DESC"
            ).fetchall()

        result: List[Dict[str, object]] = []
        for row in rows:
            data = json.loads(row[2])
            result.append(
                {
                    "id": row[0],
                    "created_at": row[1],
                    "evidence_count": data.get("evidence_count", 0),
                    "label": data.get("label", ""),
                }
            )
        return result

    # HC-AI | ticket: MEM-M1-03
    def load_snapshot(self, snapshot_id: int) -> List[Evidence]:
        """Load evidences from a snapshot back into memory.

        Args:
            snapshot_id: The snapshot ID to load.

        Returns:
            List of Evidence objects restored from the snapshot.

        Raises:
            ValueError: If snapshot_id not found.
        """
        self._ensure_initialized()
        assert self._core_db is not None
        with sqlite3.connect(str(self._core_db)) as conn:
            row = conn.execute(
                "SELECT data_json FROM snapshots WHERE id = ?",
                (snapshot_id,),
            ).fetchone()

        if row is None:
            raise ValueError(f"Snapshot {snapshot_id} not found.")

        data = json.loads(row[0])
        evidences: List[Evidence] = []

        for ev_data in data.get("evidences", []):
            lr = ev_data.get("line_range")
            evidences.append(
                Evidence(
                    source=ev_data.get("source", ""),
                    data=ev_data.get("data", {}),
                    line_range=tuple(lr) if lr else None,
                    commit_sha=ev_data.get("commit_sha"),
                    metadata=ev_data.get("metadata", {}),
                )
            )

        # Also load into memory for immediate learner use
        self._evidences = evidences
        return evidences

    # HC-AI | ticket: MEM-M1-03
    def snapshot_count(self) -> int:
        """Return the number of snapshots currently stored."""
        self._ensure_initialized()
        assert self._core_db is not None
        with sqlite3.connect(str(self._core_db)) as conn:
            row = conn.execute("SELECT COUNT(*) FROM snapshots").fetchone()
        return row[0] if row else 0

    def get_corpus_iterator(self) -> Iterator[Evidence]:
        """Yield evidence objects loaded into this vault."""
        yield from self._evidences

    def load_evidences(self, evidences: List[Evidence]) -> None:
        """Load evidence objects into memory for learner consumption."""
        self._evidences = evidences

    def schema_extension_sql(self) -> str:
        """Return codebase-specific SQL tables."""
        return _CODEBASE_EXTENSION_SQL

    def commit_pattern(self, pattern: Pattern) -> None:
        """Persist a pattern to core.db."""
        self._ensure_initialized()
        assert self._core_db is not None
        with sqlite3.connect(str(self._core_db)) as conn:
            conn.execute(
                "INSERT INTO patterns "
                "(name, category, confidence, vertical, "
                "evidence_json, metadata_json, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    pattern.name,
                    pattern.category,
                    pattern.confidence,
                    pattern.vertical or self.VERTICAL_NAME,
                    json.dumps(
                        [
                            e.source if isinstance(e, Evidence) else str(e)
                            for e in pattern.evidence
                        ]
                    ),
                    json.dumps(pattern.metadata),
                    pattern.created_at,
                ),
            )
            conn.commit()

    def query_patterns(self, category: Optional[str] = None) -> List[Pattern]:
        """Query committed patterns from core.db."""
        self._ensure_initialized()
        assert self._core_db is not None
        with sqlite3.connect(str(self._core_db)) as conn:
            if category:
                rows = conn.execute(
                    "SELECT name, category, confidence, vertical, "
                    "evidence_json, metadata_json, created_at "
                    "FROM patterns WHERE category = ? "
                    "ORDER BY confidence DESC",
                    (category,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT name, category, confidence, vertical, "
                    "evidence_json, metadata_json, created_at "
                    "FROM patterns ORDER BY confidence DESC"
                ).fetchall()
        patterns: List[Pattern] = []
        for row in rows:
            patterns.append(
                Pattern(
                    name=row[0],
                    category=row[1],
                    confidence=row[2],
                    evidence=json.loads(row[4]),
                    vertical=row[3],
                    created_at=row[6],
                    metadata=json.loads(row[5]),
                )
            )
        return patterns

    def store_nodes(self, nodes: list) -> None:
        """Batch-insert parsed AST nodes into cb_nodes table."""
        self._ensure_initialized()
        assert self._vertical_db is not None
        with sqlite3.connect(str(self._vertical_db)) as conn:
            conn.executemany(
                "INSERT INTO cb_nodes "
                "(name, file_path, node_type, layer, "
                "line_start, line_end, metadata_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        n.get("name", ""),
                        n.get("file_path", ""),
                        n.get("node_type", "function"),
                        n.get("layer", "unknown"),
                        n.get("line_start", 0),
                        n.get("line_end", 0),
                        json.dumps(n.get("metadata", {})),
                    )
                    for n in nodes
                ],
            )
            conn.commit()

    def store_edges(self, edges: list) -> None:
        """Batch-insert call edges into cb_edges table."""
        self._ensure_initialized()
        assert self._vertical_db is not None
        with sqlite3.connect(str(self._vertical_db)) as conn:
            conn.executemany(
                "INSERT INTO cb_edges "
                "(source_name, target_name, edge_type, file_path) "
                "VALUES (?, ?, ?, ?)",
                [
                    (
                        e.get("source", ""),
                        e.get("target", ""),
                        e.get("type", "calls"),
                        e.get("file_path", ""),
                    )
                    for e in edges
                ],
            )
            conn.commit()
