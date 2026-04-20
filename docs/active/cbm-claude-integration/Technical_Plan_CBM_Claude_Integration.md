# Technical Plan — CBM × Claude Ecosystem Integration

> **Paired with:** `Strategy_Memo_CBM_Claude_Integration.md`
> **For:** CTO, TechLead, Tester
> **Sprint:** CBM-INT (Integration) · 18 SP · 3 tuần
> **Branch base:** `feat/cbm-claude-integration`
> **Kick-off:** 17/04/2026 (nếu CEO approve hôm nay)

---

## 0. Mục tiêu kỹ thuật

Tích hợp CBM v2.2 vào Claude ecosystem qua 3 lớp distribution phủ mọi loại user:

```
┌──────────────────────────────────────────────────────────────┐
│  Lớp 3: Plugin Marketplace        (1-click install Cowork)   │
├──────────────────────────────────────────────────────────────┤
│  Lớp 2: MCP Server                (auto-invoke tools)        │
├──────────────────────────────────────────────────────────────┤
│  Lớp 1: PyPI + Skill + Commands   (MVP — dev Claude Code)    │
├──────────────────────────────────────────────────────────────┤
│  Base: CBM CLI v2.2               (đã có sẵn)                │
└──────────────────────────────────────────────────────────────┘
```

Nguyên tắc: **Mỗi lớp stand-alone usable**. Nếu Lớp 3 bị plugin schema đổi, Lớp 1 + 2 vẫn chạy.

---

## 1. Phase 1 — PyPI + Skill + Slash Commands (5 SP · Tuần 1)

### 1.1 Task breakdown

| Task | SP | Day | Assignee | Output |
|------|:--:|:---:|---------|--------|
| CBM-INT-101 — Publish `codebase-map` lên PyPI | 1 | D1 | TechLead | Package v2.2.1 trên pypi.org |
| CBM-INT-102 — Viết `SKILL.md` cho Claude | 1 | D2 | TechLead + CTO | `skills/codebase-map/SKILL.md` |
| CBM-INT-103 — Slash command `/cbm-onboard` | 1 | D3 | TechLead | `commands/cbm-onboard.md` |
| CBM-INT-104 — Slash command `/cbm-impact` | 0.5 | D3 | TechLead | `commands/cbm-impact.md` |
| CBM-INT-105 — Slash command `/cbm-diff` | 0.5 | D3 | TechLead | `commands/cbm-diff.md` |
| CBM-INT-106 — Integration test + docs | 1 | D4-5 | Tester + TechLead | Test report + `QUICKSTART.md` |

### 1.2 CBM-INT-101 — PyPI publish

**Bước 1.** Kiểm tra tên trên PyPI:

```bash
pip index versions codebase-map  # nếu trả "ERROR No matching distribution" là name còn trống
# Fallback names: cbm-graph, codebase-map-hc
```

**Bước 2.** Update `pyproject.toml`:

```toml
[project]
name = "codebase-map"
version = "2.2.1"
description = "Function dependency graph generator for Python and TypeScript — works great with Claude Code."
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "Hyper Commerce", email = "hypercdp@gmail.com"}]
keywords = ["codebase", "dependency-graph", "ast", "claude", "ai-coding"]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Documentation",
    "Topic :: Software Development :: Quality Assurance",
]
urls = {Homepage = "https://github.com/hypercommerce-vn/codebase-map", Issues = "https://github.com/hypercommerce-vn/codebase-map/issues"}
```

**Bước 3.** Build + upload:

```bash
pip install --upgrade build twine
python -m build
twine check dist/*
twine upload dist/*  # cần PYPI_API_TOKEN trong env
```

**Bước 4.** Verify:

```bash
pipx install codebase-map
codebase-map --version  # phải ra 2.2.1
```

**DoD:**
- [ ] Package visible tại `https://pypi.org/project/codebase-map/`
- [ ] `pipx install codebase-map` chạy clean trên macOS + Linux + WSL
- [ ] README render đúng trên PyPI page (long_description phải là `text/markdown`)

### 1.3 CBM-INT-102 — SKILL.md file

Tạo tại `integrations/claude-code/skills/codebase-map/SKILL.md`:

```markdown
---
name: codebase-map
description: >
  Use this skill when the user wants to understand a Python or TypeScript
  codebase, find where a function is called from, analyze PR impact, generate
  an API catalog, or compare code snapshots. Triggers: "impact", "callers",
  "dependency graph", "onboard this repo", "what breaks if I change X",
  "API endpoints in this project", "diff vs main".
---

# Codebase Map Skill

You have access to `codebase-map` CLI (v2.2+). It generates a function
dependency graph from Python/TypeScript source and lets you query it.

## Prerequisite check

Before any CBM command, verify install:

    codebase-map --version

If not installed, tell the user:

    pipx install codebase-map

## Workflow for a new repo

1. Check for `codebase-map.yaml` at repo root. If missing, create one:

   ```yaml
   project: "<repo-name>"
   sources:
     - path: "<src-dir>"
       language: python
       base_module: "<src-dir>"
       exclude: ["__pycache__", "migrations", ".venv"]
   output:
     dir: "docs/function-map"
     formats: [json, html]
   ```

2. Generate the graph:

   ```bash
   codebase-map generate -c codebase-map.yaml
   ```

3. Then answer user questions using these commands:

   - `codebase-map summary -f docs/function-map/graph.json` — overview
   - `codebase-map query "<name>" -f <graph>` — function details
   - `codebase-map impact "<name>" -f <graph>` — blast radius
   - `codebase-map search "<keyword>" -f <graph>` — fuzzy search
   - `codebase-map api-catalog -f <graph>` — route list
   - `codebase-map diff <git-ref> -f <graph>` — PR impact

## Dual-snapshot diff (before/after refactor)

    codebase-map generate --label baseline
    # ... make changes ...
    codebase-map generate --label post-dev
    codebase-map snapshot-diff --baseline baseline --current post-dev \
        --format markdown

Paste the markdown output into the PR body.

## Rules

- Always run `codebase-map summary` first when onboarding a repo you haven't
  seen before. Gives node/edge/domain counts in 1 second.
- For impact analysis, default depth is 3. Use `--depth 1` for quick checks,
  `--depth 2` for PR review.
- If graph.json is older than 7 days, re-generate before querying.
- For TypeScript repos, set `language: typescript` in config.

## When not to use

- User just wants to read a single file — use Read tool directly.
- Repo is tiny (< 10 files) — grep is faster than generate.
- User is asking about CBM itself — answer from this skill's knowledge.
```

**DoD:**
- [ ] Skill file pass schema check (frontmatter valid)
- [ ] Trigger phrases test: 10 câu ví dụ anh test trong Claude Code → đúng skill được gọi ít nhất 8/10
- [ ] Skill body < 500 dòng (Claude Code limit)

### 1.4 CBM-INT-103/104/105 — Slash commands

**`commands/cbm-onboard.md`** — 1 lệnh cho workflow onboard repo mới:

```markdown
---
name: cbm-onboard
description: Generate the codebase map for this repo and give me an onboarding summary.
---

Execute these steps:

1. Check if `codebase-map.yaml` exists at repo root.
   - If no, inspect the repo structure (`ls`, detect Python vs TypeScript)
     and create a sensible default config.
2. Run: `codebase-map generate -c codebase-map.yaml`
3. Run: `codebase-map summary -f docs/function-map/graph.json`
4. Run: `codebase-map api-catalog -f docs/function-map/graph.json --format text | head -30`
5. Open `docs/function-map/index.html` in browser if possible, otherwise
   tell the user the path.
6. Give me a 5-bullet onboarding summary:
   - Total nodes / edges / domains
   - Top 3 largest domains by node count
   - How many API routes exist
   - Coverage gaps (if pytest-cov report present)
   - Entry points (main, __main__, route handlers)
```

**`commands/cbm-impact.md`**:

```markdown
---
name: cbm-impact
description: "Usage: /cbm-impact <function-or-class-name> — show blast radius before refactoring."
---

Run: `codebase-map impact "$ARGUMENTS" -f docs/function-map/graph.json --depth 2`

Parse output:
- If impact zone > 50 nodes: warn user this is high-risk refactor, suggest
  splitting into smaller PRs.
- Group affected nodes by layer (service, router, worker) and file.
- List specific test files that should cover the change (from
  `codebase-map query`).
```

**`commands/cbm-diff.md`**:

```markdown
---
name: cbm-diff
description: "Usage: /cbm-diff [git-ref] — generate PR impact report for this branch vs base."
---

Default base: `main`. User can override with argument.

1. Regenerate graph if older than 1 day:
   `codebase-map generate -c codebase-map.yaml --label post-dev`
2. Run snapshot-diff against baseline if exists:
   `codebase-map snapshot-diff --baseline baseline --current post-dev --format markdown`
3. Otherwise fall back to git-diff mode:
   `codebase-map diff ${ARGUMENTS:-main} --json`
4. Format output as a PR body section with:
   - Functions added / removed / modified / renamed
   - Affected callers (grouped by domain)
   - Suggested test plan
5. Copy result to clipboard if `pbcopy` available.
```

**DoD:**
- [ ] 3 slash commands test trên repo HC thực tế → chạy không lỗi
- [ ] `/cbm-onboard` chạy trên repo Django mẫu + Next.js mẫu → đúng kết quả
- [ ] `/cbm-impact` cảnh báo đúng khi impact > 50 nodes

### 1.5 CBM-INT-106 — Integration test + QUICKSTART

Tạo `integrations/claude-code/QUICKSTART.md`:

```markdown
# Quick Start — CBM for Claude Code users

## 30-second install

    pipx install codebase-map
    mkdir -p ~/.claude/skills/codebase-map
    curl -L https://raw.githubusercontent.com/hypercommerce-vn/codebase-map/main/integrations/claude-code/skills/codebase-map/SKILL.md \
        -o ~/.claude/skills/codebase-map/SKILL.md
    mkdir -p ~/.claude/commands
    curl -L https://raw.githubusercontent.com/hypercommerce-vn/codebase-map/main/integrations/claude-code/commands/cbm-onboard.md \
        -o ~/.claude/commands/cbm-onboard.md
    # Repeat for cbm-impact and cbm-diff

## Try it

Open any Python/TypeScript repo in Claude Code, then:

    /cbm-onboard

Claude will generate a dependency graph and give you a 5-bullet summary.

## Next steps

- Add `codebase-map.yaml` to your repo root — commit it for the team.
- Install the GitHub Actions workflows from `.github/workflows/` for PR
  Impact automation.
- Check out the MCP server (Phase 2) for an even more native experience.
```

**Test matrix (Tester):**

| Case | Steps | Expected |
|------|-------|----------|
| Fresh install | `pipx install codebase-map` trên máy mới | Exit 0, version 2.2.1 |
| Skill trigger | "what breaks if I change CustomerService" | Claude dùng skill + chạy `cbm impact` |
| Slash /cbm-onboard | Run trên repo HC | Generate + summary 5 bullet |
| Slash /cbm-impact | `/cbm-impact CustomerService` | List + warn nếu > 50 |
| Slash /cbm-diff | `/cbm-diff main` | Markdown output |

---

## 2. Phase 2 — MCP Server (8 SP · Tuần 2)

### 2.1 Task breakdown

| Task | SP | Day | Output |
|------|:--:|:---:|--------|
| CBM-INT-201 — MCP server scaffold (Python) | 1 | D1 | `mcp_server/` folder |
| CBM-INT-202 — Tool `cbm_query` + `cbm_search` | 1 | D2 | 2 tools implement |
| CBM-INT-203 — Tool `cbm_impact` | 1 | D2 | 1 tool |
| CBM-INT-204 — Tool `cbm_snapshot_diff` | 2 | D3 | 1 tool (phức tạp nhất) |
| CBM-INT-205 — Tool `cbm_api_catalog` | 0.5 | D4 | 1 tool |
| CBM-INT-206 — Graph cache manager | 1 | D4 | Load graph.json 1 lần, cache in-memory |
| CBM-INT-207 — Packaging + NPM/PyPI publish | 1 | D5 | `codebase-map-mcp` trên PyPI |
| CBM-INT-208 — Integration test + config docs | 0.5 | D5 | Config examples |

### 2.2 CBM-INT-201 — Server scaffold

Dùng Python để reuse `codebase_map` package (không cần Node dependency). Chọn library `mcp` (official Anthropic SDK).

**Cấu trúc folder trong repo:**

```
codebase-map/
└── mcp_server/
    ├── __init__.py
    ├── __main__.py              # python -m mcp_server
    ├── server.py                # MCP Server main
    ├── graph_cache.py           # Lazy load + in-memory cache
    ├── tools/
    │   ├── __init__.py
    │   ├── query.py
    │   ├── search.py
    │   ├── impact.py
    │   ├── snapshot_diff.py
    │   └── api_catalog.py
    └── tests/
        └── test_tools.py
```

**`server.py` skeleton:**

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP Server exposing CBM query engine as tools for Claude Code / Cowork."""

from mcp.server import Server
from mcp.server.stdio import stdio_server

from mcp_server.graph_cache import GraphCache
from mcp_server.tools import (
    api_catalog,
    impact,
    query,
    search,
    snapshot_diff,
)

server = Server("codebase-map")
cache = GraphCache(default_path="docs/function-map/graph.json")


@server.list_tools()
async def list_tools():
    return [
        query.TOOL_DEFINITION,
        search.TOOL_DEFINITION,
        impact.TOOL_DEFINITION,
        snapshot_diff.TOOL_DEFINITION,
        api_catalog.TOOL_DEFINITION,
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    handler = {
        "cbm_query": query.handle,
        "cbm_search": search.handle,
        "cbm_impact": impact.handle,
        "cbm_snapshot_diff": snapshot_diff.handle,
        "cbm_api_catalog": api_catalog.handle,
    }.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")
    return await handler(cache, arguments)


def main():
    import asyncio
    asyncio.run(stdio_server(server))


if __name__ == "__main__":
    main()
```

### 2.3 Tool schemas (design)

**`cbm_query`:**

```json
{
  "name": "cbm_query",
  "description": "Get full details of a function/class: file path, layer, dependencies, callers, impact zone.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {"type": "string", "description": "Function or class name"},
      "graph_file": {"type": "string", "default": "docs/function-map/graph.json"},
      "depth": {"type": "integer", "default": 3, "minimum": 1, "maximum": 5}
    },
    "required": ["name"]
  }
}
```

**`cbm_search`:**

```json
{
  "name": "cbm_search",
  "description": "Fuzzy search nodes by keyword across names, IDs, and docstrings.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "keyword": {"type": "string"},
      "graph_file": {"type": "string", "default": "docs/function-map/graph.json"},
      "limit": {"type": "integer", "default": 50, "maximum": 200}
    },
    "required": ["keyword"]
  }
}
```

**`cbm_impact`:**

```json
{
  "name": "cbm_impact",
  "description": "Show all nodes affected (transitively) if this function/class changes. Use before refactor.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "graph_file": {"type": "string", "default": "docs/function-map/graph.json"},
      "depth": {"type": "integer", "default": 3, "minimum": 1, "maximum": 5}
    },
    "required": ["name"]
  }
}
```

**`cbm_snapshot_diff`:**

```json
{
  "name": "cbm_snapshot_diff",
  "description": "Compare two graph snapshots (before/after). Returns added/removed/modified/renamed functions + affected callers.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "baseline": {"type": "string", "description": "Snapshot label or file path"},
      "current": {"type": "string", "description": "Snapshot label or file path"},
      "depth": {"type": "integer", "default": 1, "minimum": 1, "maximum": 3},
      "breaking_only": {"type": "boolean", "default": false},
      "test_plan": {"type": "boolean", "default": false}
    },
    "required": ["baseline", "current"]
  }
}
```

**`cbm_api_catalog`:**

```json
{
  "name": "cbm_api_catalog",
  "description": "List all HTTP API routes in the codebase, optionally filtered by method or domain.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "graph_file": {"type": "string", "default": "docs/function-map/graph.json"},
      "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", ""]},
      "domain": {"type": "string"}
    }
  }
}
```

### 2.4 Graph cache strategy

`graph_cache.py`:

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
"""In-memory graph cache with mtime-based invalidation for MCP server."""

from pathlib import Path
from codebase_map.graph.query import QueryEngine


class GraphCache:
    def __init__(self, default_path: str):
        self._default = default_path
        self._cache: dict[str, tuple[float, QueryEngine]] = {}

    def get(self, path: str | None = None) -> QueryEngine:
        p = Path(path or self._default)
        if not p.exists():
            raise FileNotFoundError(
                f"Graph file not found: {p}. "
                f"Run 'codebase-map generate' first."
            )
        mtime = p.stat().st_mtime
        key = str(p.resolve())
        cached = self._cache.get(key)
        if cached and cached[0] == mtime:
            return cached[1]
        engine = QueryEngine.from_json(p)
        self._cache[key] = (mtime, engine)
        return engine
```

Cache invalidation: mtime-based, tự refresh khi `codebase-map generate` chạy lại.

### 2.5 Deployment config

**`claude_desktop_config.json`** (Claude Code user):

```json
{
  "mcpServers": {
    "codebase-map": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "env": {
        "CBM_DEFAULT_GRAPH": "docs/function-map/graph.json"
      }
    }
  }
}
```

Hoặc đơn giản hơn nếu publish PyPI:

```json
{
  "mcpServers": {
    "codebase-map": {
      "command": "uvx",
      "args": ["--from", "codebase-map-mcp", "cbm-mcp"]
    }
  }
}
```

### 2.6 DoD Phase 2

- [ ] 5 tools pass schema validation (Anthropic MCP Inspector)
- [ ] Graph 10MB load < 500ms, query < 100ms (benchmark)
- [ ] Integration test: Claude Code gọi tool → response đúng cho 20 câu hỏi test
- [ ] Published: `pip install codebase-map-mcp` (entry point `cbm-mcp`)
- [ ] Register vào MCP registry Anthropic (submit PR)
- [ ] Docs: `integrations/mcp/README.md` có config example cho Claude Desktop + Cowork

---

## 3. Phase 3 — Plugin Marketplace (5 SP · Tuần 3)

### 3.1 Task breakdown

| Task | SP | Day | Output |
|------|:--:|:---:|--------|
| CBM-INT-301 — Plugin manifest + bundle | 1 | D1 | `cbm.plugin` file |
| CBM-INT-302 — Post-install hook (install CLI + config MCP) | 1 | D2 | Hook script |
| CBM-INT-303 — Publish to `hypercommerce-vn/claude-plugins` | 1 | D3 | Plugin visible marketplace |
| CBM-INT-304 — Cowork variant (adapt cho non-dev) | 1.5 | D4 | `cbm-cowork.plugin` |
| CBM-INT-305 — Launch blog post + demo video | 0.5 | D5 | Published post + Loom 2min |

### 3.2 Plugin structure

Repo mới: `hypercommerce-vn/claude-plugins` (theo Strategy D6).

```
claude-plugins/
├── README.md                        # Marketplace overview
├── marketplace.json                 # Plugin index
└── plugins/
    └── codebase-map/
        ├── manifest.json            # Plugin metadata
        ├── README.md                # Plugin docs
        ├── skills/
        │   └── codebase-map/
        │       └── SKILL.md         # Từ Phase 1
        ├── commands/
        │   ├── cbm-onboard.md
        │   ├── cbm-impact.md
        │   └── cbm-diff.md
        ├── mcp/
        │   └── config.json          # MCP server entry
        └── hooks/
            ├── post-install.sh      # Install CLI + config MCP
            └── pre-uninstall.sh     # Cleanup
```

### 3.3 Manifest example

`manifest.json`:

```json
{
  "name": "codebase-map",
  "version": "1.0.0",
  "display_name": "Codebase Map",
  "description": "Understand any Python/TypeScript codebase at a glance. Impact analysis, API catalog, PR diff — all powered by AST + D3.js.",
  "author": "Hyper Commerce",
  "homepage": "https://github.com/hypercommerce-vn/codebase-map",
  "license": "MIT",
  "requires": {
    "python": ">=3.10",
    "claude_code": ">=1.0.0"
  },
  "components": {
    "skills": ["skills/codebase-map/SKILL.md"],
    "commands": [
      "commands/cbm-onboard.md",
      "commands/cbm-impact.md",
      "commands/cbm-diff.md"
    ],
    "mcp_servers": ["mcp/config.json"]
  },
  "hooks": {
    "post_install": "hooks/post-install.sh",
    "pre_uninstall": "hooks/pre-uninstall.sh"
  },
  "tags": ["codebase", "ast", "dependency-graph", "pr-review", "onboarding"],
  "screenshots": [
    "https://raw.githubusercontent.com/hypercommerce-vn/codebase-map/main/docs/screenshots/graph-view.png",
    "https://raw.githubusercontent.com/hypercommerce-vn/codebase-map/main/docs/screenshots/pr-diff.png"
  ]
}
```

### 3.4 Post-install hook

`hooks/post-install.sh`:

```bash
#!/usr/bin/env bash
# HC-AI | ticket: FDD-TOOL-CODEMAP
set -euo pipefail

echo "[codebase-map plugin] Installing CLI..."
if ! command -v pipx &> /dev/null; then
    echo "[codebase-map plugin] pipx not found. Installing via pip..."
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath
fi
pipx install codebase-map || pipx upgrade codebase-map

echo "[codebase-map plugin] Installing MCP server..."
pipx inject codebase-map codebase-map-mcp || pipx install codebase-map-mcp

echo "[codebase-map plugin] Done. Try: /cbm-onboard"
```

### 3.5 Cowork variant

Cowork user (PM/PO/CEO) cần UX khác — không gõ lệnh, không đọc JSON. Variant:

- Skill tập trung vào câu hỏi natural language: "Summarize this repo", "Show me the APIs", "What changed in this PR?"
- Slash commands rewrite dùng ngôn ngữ non-technical: `/repo-summary`, `/api-list`, `/pr-impact`
- Auto-generate graph mỗi lần Cowork open folder (hook vào Cowork lifecycle)
- Output: formatted markdown hoặc mini HTML preview trong chat, không dump JSON

File variant: `plugins/codebase-map-cowork/` với skill riêng viết tiếng Việt + English bilingual.

### 3.6 Launch assets

**Blog post outline** (crosspost dev.to + Medium + HC blog):

- Title: "From 'what does this code do?' to 'where does it call?' — meet Codebase Map for Claude"
- 800 từ, 2 GIF demo, 1 code block
- Pin CTA: `/plugin install codebase-map`

**Demo video** (2 phút Loom):

- 0:00-0:15 — Problem: dev mới join team hỏi mãi "where is X called?"
- 0:15-0:45 — Install `/plugin install cbm` + `/cbm-onboard`
- 0:45-1:30 — Ask Claude "what breaks if I change `CustomerService.create`?" → Claude tự gọi MCP tool
- 1:30-2:00 — PR review workflow với `/cbm-diff`

### 3.7 DoD Phase 3

- [ ] Plugin visible trên marketplace, install < 30s
- [ ] Post-install hook pass trên macOS + Linux + Windows WSL
- [ ] Cowork variant test với 1 PM + 1 PO non-technical
- [ ] Blog post published + 100 views trong 48h
- [ ] Demo video 100+ views trong tuần đầu

---

## 4. Cross-cutting concerns

### 4.1 Versioning & release

Sử dụng semver với 3 artifact đồng bộ:

| Artifact | Package name | Registry |
|----------|-------------|----------|
| CLI | `codebase-map` | PyPI |
| MCP server | `codebase-map-mcp` | PyPI |
| Plugin | `codebase-map` | Claude Plugin Marketplace |

Version bump quy tắc:

- PATCH (2.2.1 → 2.2.2): bug fix, skill text tweak
- MINOR (2.2 → 2.3): new MCP tool, new slash command
- MAJOR (2.x → 3.0): breaking change CLI flag hoặc MCP schema

### 4.2 CI/CD changes

Thêm 2 workflow mới:

**`.github/workflows/publish-pypi.yml`** — tag `v*` → auto publish PyPI:

```yaml
name: Publish to PyPI
on:
  push:
    tags: ['v*']
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write  # OIDC, không cần token
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

**`.github/workflows/publish-plugin.yml`** — PR merge vào main của `claude-plugins` → auto sync manifest.

### 4.3 Security review (CTO gate)

| Vector | Mitigation |
|--------|-----------|
| MCP server execute arbitrary path | Validate graph_file path phải trong project_root |
| Snapshot file chứa secrets | Skill cảnh báo check `.gitignore` trước khi publish snapshot |
| Post-install hook chạy as user | Log mọi subprocess, không `curl \| sh`, chỉ pipx install |
| Telegram token trong CBM (staleness) | Bảo đảm MCP server KHÔNG load env var này unless explicitly |

### 4.4 Telemetry (optional — Phase 4)

Opt-in anonymous: `codebase-map telemetry on/off`. Track:
- Command invocation counts (no args, no paths)
- MCP tool call counts
- Graph size buckets (0-100, 100-1k, 1k-10k nodes)

Mục đích: biết feature nào được dùng để prioritize sprint sau.

### 4.5 Documentation updates

- [ ] `README.md` thêm section "Install for Claude Code" ngay sau "Install"
- [ ] `docs/active/ONBOARDING.md` thêm Claude-first workflow
- [ ] `BRIEF.md` cập nhật trạng thái "Integration sprint live"
- [ ] `project/board.html` (SSOT) add section Integration sprint + 3 phase milestones
- [ ] `CLAUDE.md` thêm roadmap row v2.3 — Claude Integration

---

## 5. Acceptance Criteria toàn sprint

| # | AC | Verify |
|---|----|--------|
| AC-1 | `pipx install codebase-map` work trên fresh macOS/Linux/WSL | Smoke test Tester |
| AC-2 | Skill trigger đúng 8/10 câu test | Checklist Tester |
| AC-3 | 3 slash commands pass trên repo HC thật | Manual run |
| AC-4 | MCP server 5 tools pass schema + response correct | MCP Inspector |
| AC-5 | Graph 10MB query latency < 100ms | Benchmark |
| AC-6 | Plugin install < 30s on Claude Code | Manual run |
| AC-7 | Plugin install < 30s on Cowork (non-dev user) | User test |
| AC-8 | Blog + video live, > 100 views tuần đầu | Analytics |
| AC-9 | PyPI + npm + marketplace 3 artifact đồng version v2.3.0 | Version bump audit |
| AC-10 | No regression trên 582 existing tests | `pytest tests/` |

---

## 6. Rollback plan

Nếu Phase X fail:

- **Phase 1 fail:** Không publish PyPI. Fallback: giữ install qua git URL. Ảnh hưởng: zero, chỉ delay.
- **Phase 2 fail:** Không publish MCP server. Phase 1 vẫn chạy. User không có auto-invoke nhưng vẫn có CLI + skill.
- **Phase 3 fail:** Plugin schema đổi. Fallback: giữ Phase 1 + 2 standalone. User manual config MCP + skill vẫn work.

Mỗi phase gate có CEO approve trước khi ship → không fail lan chéo.

---

## 7. Questions cho CTO review

1. MCP server viết Python (reuse `codebase_map` package) hay Node (ecosystem MCP mature hơn)? → Khuyến nghị Python vì reuse code.
2. Plugin repo có nên hosted cùng CBM repo hay tách riêng `claude-plugins`? → Tách riêng để marketplace discovery tốt hơn.
3. Có cần rate limit MCP tool calls không? → Chưa cần Phase 2, xét lại khi > 10k calls/week.
4. Telemetry có ra Phase 4 hay gộp vào Phase 3? → Gộp Phase 4, Phase 3 đã đủ scope.

---

## 8. Kick-off checklist (nếu CEO approve)

- [ ] CEO approve Strategy Memo + Technical Plan (anh sign)
- [ ] Tạo branch `feat/cbm-claude-integration`
- [ ] Tạo project board trên GitHub Projects track 18 SP
- [ ] PyPI account + API token sẵn sàng (anh cung cấp)
- [ ] Tạo repo `hypercommerce-vn/claude-plugins` (private → public khi Phase 3)
- [ ] TechLead đọc Phase 1 task breakdown, ước tính lại nếu cần
- [ ] Update `BRIEF.md` + `project/board.html` (SSOT)

---

*Technical Plan v1.0 · Created 16/04/2026 · For CTO/TechLead/Tester*
*Paired with: `Strategy_Memo_CBM_Claude_Integration.md`*
