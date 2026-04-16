# Codebase Map

> **Standalone function dependency graph generator** for Python (and TypeScript) projects.
> Output: interactive HTML + JSON. **100% offline · zero CDN.**
> **License:** MIT · **Version:** 2.2.0

Parse your codebase into a function dependency graph (nodes = functions/classes, edges = call relationships). Foundation for understanding large codebases, PR impact analysis, and dual-snapshot diff.

---

## Install

### From PyPI (future)
```bash
pipx install codebase-map
```

### From GitHub (current)
```bash
pipx install "git+https://github.com/hypercommerce-vn/codebase-map.git"
```

### For development
```bash
git clone git@github.com:hypercommerce-vn/codebase-map.git
cd codebase-map
pip install -e ".[dev]"
```

Verify:
```bash
codebase-map --version  # 2.2.0
```

---

## Quick Start

### 1. Create config at project root

```yaml
# codebase-map.yaml
project: "my-app"
sources:
  - path: "app"
    language: python
    base_module: "app"
    exclude: ["__pycache__", "migrations"]
output:
  dir: "docs/function-map"
  formats: [json, html]
graph:
  depth: 3
  group_by: module
```

### 2. Generate graph

```bash
codebase-map generate -c codebase-map.yaml
```

Output: `docs/function-map/graph.json` + interactive `index.html`.

### 3. Query the graph

```bash
codebase-map summary -f docs/function-map/graph.json
codebase-map query "CustomerService" -f docs/function-map/graph.json
codebase-map impact "AuthService" -f docs/function-map/graph.json
codebase-map search "create" -f docs/function-map/graph.json
```

### 4. Dual-snapshot diff (v2.2)

```bash
# Create baseline
codebase-map generate --label "baseline"

# ... make changes ...

codebase-map generate --label "post-dev"
codebase-map snapshot-diff --baseline baseline --current post-dev --format markdown
```

---

## Commands

| Command | Purpose |
|---------|---------|
| `generate` | Generate function dependency graph |
| `query` | Look up function/class details |
| `impact` | Show impact zone for a node |
| `search` | Search nodes by keyword |
| `summary` | Graph statistics |
| `diff` | Git diff impact analysis |
| `snapshot-diff` | Dual-snapshot structural diff (v2.2) |
| `snapshots` | Manage snapshots (list/clean) |
| `api-catalog` | List API routes |
| `coverage` | Overlay test coverage |
| `check-staleness` | Check graph freshness |

All commands support `--help` for detailed options.

---

## Features

### 🔍 Graph Generation
- Python AST parser (classes, functions, methods, decorators)
- Layer classification (route / service / model / util / schema / test)
- Domain clustering (by module path)
- Call graph edges + import edges
- JSON + interactive HTML output

### 📊 Dual-Snapshot Diff (v2.2)
- Compare two graph snapshots (before/after)
- Added / removed / modified / renamed functions
- Affected callers (transitive, 1-3 levels)
- Rename detection via signature matching
- Output formats: markdown (PR body), JSON (CI), text (terminal)

### 🎨 Interactive HTML
- D3.js force-directed graph (bundled, offline)
- Sidebar tree, minimap, toolbar
- Executive view, PR Diff view, API Catalog
- Multi-view tabs, breadcrumb navigation
- Business Flow mapping

### ⚙️ CI Integration
- `cbm-baseline.yml` — auto-baseline on merge to main
- `cbm-post-merge.yml` — rotate baseline after PR merge
- `cbm-pr-impact.yml` — post PR Impact comment (dual-snapshot)

---

## Architecture

```
Source Code (Python/TS)
    ↓
  [AST Parser]
    ↓
  [Graph Builder]  → Nodes + Edges + Metadata
    ↓
  [Exporters]      → JSON + HTML (D3.js)
    ↓
  [Query Engine]   → summary, impact, search, query
    ↓
  [Snapshot Diff]  → add/remove/modify/rename + affected callers
```

CBM is **stateless**: every command takes graph.json as input. No database, no state.

---

## Use Cases

### Before modifying a function
```bash
codebase-map impact "CustomerService.create" -f graph.json
# Shows all callers — know blast radius before refactoring
```

### In PR description
```bash
codebase-map snapshot-diff --baseline main --current feature-branch --format markdown
# Copy-paste into PR body — reviewers see structural impact
```

### CI auto-comment
Installed workflows post impact analysis on every PR automatically.

### Understand a new codebase
```bash
codebase-map summary -f graph.json       # How big is it?
codebase-map api-catalog -f graph.json    # What APIs exist?
codebase-map query "main" -f graph.json   # Where's the entry point?
```

---

## Sister Project: Knowledge AI Platform

Want AI-powered Q&A on your codebase? Check out [Knowledge AI Platform](https://github.com/hypercommerce-vn/knowledge-AI-platform) — adds multi-LLM RAG, MCP server, and onboarding report generator on top of CBM data.

---

## Development

```bash
# Install
pip install -e ".[dev]"

# Test
pytest tests/ -q

# Lint
black --check codebase_map/ tests/
isort --check codebase_map/ tests/
flake8 codebase_map/ tests/

# Generate on self
codebase-map generate -c codebase-map-self.yaml
```

---

## License

**MIT** — see [LICENSE](LICENSE) file.

---

## Credits

Built by [Hyper Commerce](https://github.com/hypercommerce-vn) for internal use, open-sourced for the community.

---

*Version 2.2.0 · Published 2026-04-16*
