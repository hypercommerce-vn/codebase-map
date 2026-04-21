# Codebase Map — Claude Code Plugin

One-command install of the `codebase-map` toolkit inside Claude Code:
Skill + 3 slash commands + MCP auto-invoke, all wired up by the plugin
post-install hook.

Prefer raw pipx + manual MCP config? See
[`integrations/mcp/README.md`](../../integrations/mcp/README.md) — the two
paths coexist.

## What ships in this plugin

| Component | Origin | Purpose |
|-----------|--------|---------|
| Skill `codebase-map` | S1 (v2.3.0) | Claude auto-triggers CBM on "impact", "who calls", "onboard this repo", "blast radius", "API endpoints", "diff vs main" |
| `/cbm-onboard` | S1 | Generate graph + 5-bullet onboarding summary |
| `/cbm-impact <name>` | S1 | Show blast radius before refactoring |
| `/cbm-diff [base-ref]` | S1 | Markdown PR-body section with impact + test plan |
| MCP server `codebase-map` | S2 (v2.4.0) | 5 auto-invoke tools over MCP stdio |

The post-install hook installs `codebase-map[mcp]>=2.4.0` via pipx, which
brings the `codebase-map` CLI and the `cbm-mcp` MCP server onto `PATH`.

## Install

In Claude Code:

```
/plugin install codebase-map
```

The post-install hook runs automatically. It:

1. Ensures `pipx` is available (installs it via `pip --user` if missing).
2. Runs `pipx install 'codebase-map[mcp]>=2.4.0'` (or upgrades an existing
   install).
3. Verifies `codebase-map` and `cbm-mcp` landed on `PATH`.

Verify the install:

```bash
codebase-map --version     # should print 2.4.0 or later
which cbm-mcp              # should resolve to ~/.local/bin/cbm-mcp
```

## First use

**Prerequisite:** generate the graph once for the target repo:

```bash
cd /path/to/your/repo
codebase-map generate -c codebase-map.yaml
# → writes docs/function-map/graph.json
```

Then in Claude Code:

```
/cbm-onboard
```

Claude will verify the install, check for `codebase-map.yaml`, generate
the graph if needed, and return a 5-bullet onboarding summary.

## Tool reference (MCP auto-invoke)

When you ask Claude a natural-language question, it picks the right tool:

| Tool | Example prompt |
|------|----------------|
| `cbm_query` | "Where is `QueryEngine` defined?" |
| `cbm_search` | "Find everything matching `snapshot`." |
| `cbm_impact` | "What breaks if I change `QueryEngine`?" |
| `cbm_snapshot_diff` | "Compare the `baseline` and `post-dev` snapshots." |
| `cbm_api_catalog` | "List all API endpoints in this project." |

All tools return Markdown-ready text. `cbm_snapshot_diff` defaults to
`format: markdown` (PR-body paste); use `format: json` for programmatic
consumption.

Graph cache is mtime-invalidated (S2 v2.4.0): first call parses + indexes
(~3 ms on a 200-node graph); subsequent calls hit cache in <1 ms.

## Dependencies

This plugin declares one PyPI dependency:

- `codebase-map[mcp]>=2.4.0` — pulls `codebase-map` core + `mcp>=1.27.0`.

The post-install hook is the only path that actually calls pipx. If the
hook fails (no Python, no pipx, offline), the plugin surface is still
installed but commands will error until the hook runs cleanly.

## Troubleshooting

**`cbm-mcp: command not found`** — pipx installs into `~/.local/bin`. Run
`pipx ensurepath` then restart your shell.

**Post-install hook failed** — re-run manually:

```bash
pipx install 'codebase-map[mcp]>=2.4.0'
```

**MCP server doesn't fire** — check
`~/Library/Logs/Claude/mcp-server-codebase-map.log` on macOS. Common cause:
`cbm-mcp` not on Claude's launch `PATH`. Fallback: hardcode an absolute
path in `mcp/config.json`:

```json
{
  "mcpServers": {
    "codebase-map": {
      "command": "/Users/you/.local/bin/cbm-mcp"
    }
  }
}
```

**Tools return "graph.json not found"** — CBM defaults to
`docs/function-map/graph.json` relative to CWD. If Claude Code launches
`cbm-mcp` from `/`, pass `graph_file` as an absolute path in the prompt.

## Uninstall

```
/plugin uninstall codebase-map
```

The pre-uninstall hook removes the CBM CLI via `pipx uninstall
codebase-map`. Leaves `~/.codebase-map-cache.json` and any per-repo
`docs/function-map/` artifacts alone — those are user data.

## Links

- Main repo: https://github.com/hypercommerce-vn/codebase-map
- Release notes: [`docs/releases/v2.4.0.md`](../../docs/releases/v2.4.0.md)
- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
- License: MIT
