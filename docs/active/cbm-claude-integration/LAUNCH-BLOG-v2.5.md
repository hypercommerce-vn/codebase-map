<!-- HC-AI | ticket: CBM-INT-305 | author: TechLead agent | date: 21/04/2026 -->
<!-- Crosspost-ready: dev.to + Medium + HC blog · target 800 words · 5 min read -->

# From "what does this code do?" to "where does it call?" — meet Codebase Map for Claude

> **TL;DR** — We shipped 3 Claude-integrated products (CLI, MCP server, plugin) in roughly 3 calendar days. Install with `pipx install 'codebase-map[mcp]'`, drop an MCP entry into Claude Desktop, and your assistant suddenly knows your function graph. Open source, MIT, Python 3.10+.

---

## The blind spot

Every new engineer on every team asks the same question 20 times a week: **"Where is this function called from?"** Or its cousin: *"What breaks if I change this?"*

Classic IDEs answer this locally. But the moment you switch to Claude Code, Cursor, or a chat-first workflow, the assistant has no structural view of your repo. It reads files one at a time, pattern-matches imports, and too often guesses. Generic "codebase map" tools exist — but none plug into Claude's natural-language flow without copy-pasting output.

So we built one that does. Meet **Codebase Map (CBM)**.

---

## Three products, one graph

We shipped three layers in roughly 3 calendar days (original internal plan: 6 weeks):

### 1. CBM CLI — `codebase-map` v2.3.0 (on PyPI)

Pure Python + AST. No runtime. Generates a function-level dependency graph from a YAML config pointed at your repo root.

```bash
pipx install codebase-map
codebase-map generate -c codebase-map.yaml
codebase-map impact "UserService" -f graph.json
```

The graph becomes an interactive D3.js HTML (offline, no CDN) plus a JSON source of truth. Supports Python today, TypeScript parser landed in v2.0.

### 2. MCP Server — `cbm-mcp` v2.4.0 (published 20/04/2026)

Wraps the CBM engine in a [Model Context Protocol](https://modelcontextprotocol.io) server. Five tools Claude auto-invokes when the user's question matches:

| Tool | When Claude reaches for it |
|---|---|
| `cbm_query` | "show me node X" |
| `cbm_search` | "find everything named parse*" |
| `cbm_impact` | "what breaks if I change X?" |
| `cbm_snapshot_diff` | "diff this branch vs main" |
| `cbm_api_catalog` | "list our REST endpoints" |

Underneath is a graph cache with mtime invalidation. Measured on CBM's own 201-node graph: **cold load 2.8ms, hot read 0.071ms — 40× speedup**. The target was <100ms; we crushed it.

### 3. Claude Plugin — v2.5.0 plugin bundle (this sprint · PyPI stays v2.4.0)

One-click install via the Cowork marketplace. Plus two **archetype packs**, bilingual EN/VI: one for AI-agent repos, one for SaaS B2B codebases. Each pack adds 3 slash commands and domain-tuned skill triggers — no extra backend, just prompting the shared MCP tools with the right lens.

> 🔍 **Note on versioning:** The plugin bundle is v2.5.0 (marketplace milestone). The underlying PyPI package stays at v2.4.0 — plugins are pure distribution packaging, no runtime changes. Your `pipx install 'codebase-map[mcp]'` still gets v2.4.0 with the 5 MCP tools.

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map@hypercommerce-vn
```

---

## Real demo — three workflows that already work

**1. Impact before refactor.** User: *"What breaks if I change APIRouter?"*
Claude auto-invokes `cbm_impact("APIRouter")`, reads back:

```
Impact: APIRouter (codebase_map/graph/builder.py)
→ 1 node(s) affected · Risk: Low
→ Affected layers: graph (1)
→ Suggested PR split: single commit, no external callers
```

Now the assistant proposes a safe edit plan instead of guessing.

**2. PR body in one turn.** User: *"Generate the PR body for this refactor."*
`cbm_snapshot_diff` with `test_plan: true` returns Markdown ready to paste — added nodes, removed nodes, breaking changes, test-plan bullets.

**3. Onboarding a stranger.** User: *"Onboard me to this Python repo."*
`/cbm-onboard` runs the skill, Claude returns a 5-bullet brief in ~10 seconds: layers, entry points, hotspots, API surface, suggested first read.

---

## Install in 90 seconds

```bash
# 1. Install with the MCP extra
pipx install 'codebase-map[mcp]'

# 2. Wire into Claude Desktop
# ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "codebase-map": { "command": "cbm-mcp" }
  }
}

# 3. In your repo
codebase-map generate -c codebase-map.yaml
```

Then ask Claude anything structural. That's the full setup.

Architecture, simplified:

```
  Claude Desktop / Code
           |
           | stdio (JSON-RPC / MCP)
           v
     cbm-mcp server  <-- 5 tools
           |
           | pure-Python imports
           v
   codebase_map engine
   (parser + graph + cache)
           |
           v
    graph.json  +  D3 HTML
```

---

## By the numbers

- **20 story points** shipped across 5 sprints in ~3 calendar days (plan said 6 weeks)
- **3 PyPI releases:** v2.2.1, v2.3.0, v2.4.0 — all tag-triggered, green CI
- **5 MCP tools** live, all auto-invoke
- **40× cache speedup** hot vs cold (0.071ms vs 2.8ms)
- **158/158 unit tests** green, one-line `pytest` run in 0.28s
- **2 archetype packs** (AI Agent + SaaS B2B), bilingual EN/VI
- **MIT license** — everything open source

---

## Credits

Huge thanks to the Anthropic MCP SDK team — the Python SDK was a pleasure to build against. The marketplace pattern takes direct inspiration from the community work at `buildwithclaude/superpowers-marketplace` and the `cc-marketplace` manifest conventions. And to every engineer who has ever screamed *"where is this called?!"* into a void — this one's for you.

---

**Try it:** https://pypi.org/project/codebase-map/
**Plugin:** https://github.com/hypercommerce-vn/claude-plugins
**Source:** https://github.com/hypercommerce-vn/codebase-map
**Feedback:** hypercdp@gmail.com — or open an issue on the repo.
