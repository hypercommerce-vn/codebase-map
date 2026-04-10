# KMP Vault Format Specification

> **Version:** 1.0-draft · **Author:** @CTO · **Date:** 10/04/2026
> **Status:** Public spec — any tool can read/write this format
> **Ticket:** KMP-M0-07

---

## 1. Overview

A **vault** is the local storage directory for a Knowledge Memory Platform project. It lives at `.knowledge-memory/` inside any project root and is fully offline — no cloud dependency.

**Design principle:** Open vault, closed engine. The vault format is open so that any tool (IDE plugin, script, CI pipeline) can read or generate compatible data. The learning engine that fills the vault may be proprietary.

---

## 2. Directory Layout

```
<project-root>/
└── .knowledge-memory/
    ├── config.yaml                    # Project configuration
    ├── core.db                        # Core SQLite database
    ├── .gitignore                     # Ignore *.lock, *.tmp
    └── verticals/
        └── <vertical-name>/           # One folder per vertical
            ├── vault.db               # Vertical-specific SQLite data
            ├── snapshots/
            │   └── <timestamp>.json   # Corpus snapshots
            ├── patterns.md            # Human-readable pattern output
            └── quick-wins.md          # Bootstrap insights (optional)
```

### Path conventions

| Path | Required | Description |
|------|:--------:|-------------|
| `.knowledge-memory/` | Yes | Vault root, always in project root |
| `config.yaml` | Yes | LLM provider, project metadata, enabled verticals |
| `core.db` | Yes | SQLite 3.35+ — patterns, metadata, usage log |
| `verticals/<name>/` | Per vertical | Created by `BaseVault.init()` |
| `verticals/<name>/vault.db` | Per vertical | Vertical-specific data (nodes, edges, etc.) |
| `verticals/<name>/snapshots/` | Per vertical | Timestamped corpus snapshots |
| `verticals/<name>/patterns.md` | Per vertical | Human-readable learning output |

### .gitignore

The vault `.gitignore` should contain:

```
*.lock
*.tmp
*.db-journal
*.db-wal
*.db-shm
```

The vault itself (`.knowledge-memory/`) should be **included** in version control. The SQLite databases contain learned patterns that are valuable project knowledge.

---

## 3. Core SQLite Schema (`core.db`)

The core database stores cross-vertical data: patterns, metadata, and usage telemetry.

```sql
-- Table: _meta
-- Key-value store for vault metadata.
CREATE TABLE IF NOT EXISTS _meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- Required _meta keys:
-- "vault_version"  → "1.0"
-- "created_at"     → ISO-8601 timestamp
-- "project_name"   → Human-readable project name

-- Table: patterns
-- All learned patterns from all verticals.
CREATE TABLE IF NOT EXISTS patterns (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vertical      TEXT    NOT NULL,     -- e.g. "codebase", "legal"
    category      TEXT    NOT NULL,     -- e.g. "naming", "architecture", "stats"
    name          TEXT    NOT NULL,     -- e.g. "frequent_word::hello"
    confidence    REAL    NOT NULL,     -- 0.0 to 100.0
    evidence_json TEXT    NOT NULL,     -- JSON array of evidence references
    metadata_json TEXT    DEFAULT '{}', -- Free-form JSON extras
    created_at    TEXT    NOT NULL      -- ISO-8601 timestamp (UTC)
);

CREATE INDEX IF NOT EXISTS idx_patterns_vertical
    ON patterns(vertical, category);

CREATE INDEX IF NOT EXISTS idx_patterns_confidence
    ON patterns(confidence DESC);

-- Table: snapshots
-- Corpus snapshot history per vertical.
CREATE TABLE IF NOT EXISTS snapshots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    vertical     TEXT NOT NULL,
    timestamp    TEXT NOT NULL,         -- ISO-8601 (UTC)
    file_path    TEXT NOT NULL,         -- Relative path to snapshot JSON
    summary_json TEXT                   -- Optional summary stats
);

-- Table: usage_log
-- Telemetry for command execution (opt-in, local only).
CREATE TABLE IF NOT EXISTS usage_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,       -- ISO-8601 (UTC)
    vertical    TEXT    NOT NULL,
    command     TEXT    NOT NULL,       -- e.g. "bootstrap", "ask", "insights"
    duration_ms INTEGER,
    tokens_used INTEGER,
    success     BOOLEAN NOT NULL DEFAULT 1
);
```

### Pattern evidence format

The `evidence_json` column contains a JSON array with up to 20 evidence references:

```json
[
  {
    "source": "src/auth/login.py",
    "line_range": [42, 58],
    "commit_sha": "abc1234",
    "data": {"text": "def login(username, password):"}
  }
]
```

Fields per evidence entry:

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `source` | string | Yes | File path, URL, or document ID |
| `line_range` | [int, int] | No | 1-indexed start and end line |
| `commit_sha` | string | No | Git commit hash for traceability |
| `data` | object | No | Parser-specific payload |

---

## 4. Vertical SQLite Schema (`vault.db`)

Each vertical may define additional tables via `BaseVault.schema_extension_sql()`. These tables live in `verticals/<name>/vault.db`, separate from `core.db`.

### Example: Codebase vertical (M1)

```sql
-- Vertical-specific tables for codebase analysis
CREATE TABLE IF NOT EXISTS nodes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    node_type TEXT NOT NULL,     -- "function", "class", "method"
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end   INTEGER,
    metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS edges (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES nodes(id),
    target_id INTEGER NOT NULL REFERENCES nodes(id),
    edge_type TEXT NOT NULL      -- "calls", "imports", "inherits"
);
```

### Example: Hello vertical (reference)

The Hello vertical has no additional tables — `schema_extension_sql()` returns an empty string. It only uses the core `patterns` table.

---

## 5. Config File (`config.yaml`)

```yaml
# .knowledge-memory/config.yaml
vault_version: "1.0"
project_name: "My Project"

# Enabled verticals (list of installed vertical names)
verticals:
  - codebase
  - hello

# LLM configuration (BYOK — user provides their own key)
llm:
  provider: anthropic       # or "openai", "gemini"
  model: claude-sonnet-4-20250514
  # API key resolved from environment: ANTHROPIC_API_KEY

# Optional: telemetry opt-out
telemetry:
  enabled: false
```

---

## 6. Snapshot Format

Snapshots capture the state of a vertical's corpus at a point in time. Stored as JSON in `verticals/<name>/snapshots/<timestamp>.json`.

```json
{
  "version": "1.0",
  "vertical": "codebase",
  "timestamp": "2026-04-10T12:00:00Z",
  "stats": {
    "total_files": 142,
    "total_evidence": 3850,
    "file_types": {".py": 98, ".ts": 44}
  },
  "files": [
    {
      "path": "src/auth/login.py",
      "sha256": "a1b2c3...",
      "size_bytes": 2048,
      "last_modified": "2026-04-09T10:30:00Z"
    }
  ]
}
```

Snapshots enable incremental learning — only re-process files that changed since the last snapshot.

---

## 7. Patterns Markdown (`patterns.md`)

Human-readable output generated after each learning run. Format:

```markdown
# Patterns — <vertical> · <timestamp>

## Category: naming
### frequent_word::hello (confidence: 85.0%)
- Evidence: 12 occurrences across 5 files
- First seen: src/greet.py:14
- Insight: "hello" is a frequently repeated token

## Category: architecture
### layer_violation::utils→core (confidence: 92.0%)
- Evidence: 3 imports violating layer boundary
- Files: src/utils/helper.py, src/utils/cache.py
- Insight: Utils layer imports Core directly
```

This file is designed to be committed to git and reviewed in PRs.

---

## 8. Compatibility Notes

- **SQLite version:** Requires SQLite 3.35+ (for `RETURNING` clause support in M1)
- **Encoding:** All text is UTF-8
- **Timestamps:** Always ISO-8601 in UTC (e.g. `2026-04-10T12:00:00Z`)
- **File paths:** Always use forward slashes, relative to project root
- **JSON columns:** Valid JSON; parsers should tolerate missing optional fields

### Reading a vault from external tools

Any tool can read the vault by:

1. Opening `.knowledge-memory/core.db` with any SQLite client
2. Querying the `patterns` table for learned knowledge
3. Reading `verticals/<name>/patterns.md` for human-readable output
4. Parsing `config.yaml` for project metadata

No KMP library is required to read vault data.

---

*Vault Format Spec v1.0-draft · KMP · HC-AI | ticket: KMP-M0-07*
