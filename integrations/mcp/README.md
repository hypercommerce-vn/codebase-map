# Codebase Map — MCP Server

`codebase-map[mcp]` ships an MCP (Model Context Protocol) server that
exposes 5 auto-invoke tools to MCP-aware clients: Claude Desktop, Claude
Code (via MCP), Cowork, and any other host that speaks the protocol.

Prefer slash commands? See
[`integrations/claude-code/QUICKSTART.md`](../claude-code/QUICKSTART.md) —
the two paths coexist.

## Install

```bash
pipx install "codebase-map[mcp]"
cbm-mcp           # stdio server — blocks silently (this is correct)
```

The `[mcp]` extra pulls in `mcp>=1.27.0` alongside CBM. The `cbm-mcp` entry
point lands on your `PATH`.

Verify the entry point:

```bash
which cbm-mcp
codebase-map --version    # should print 2.4.0 or later
```

## Claude Desktop config

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "codebase-map": {
      "command": "cbm-mcp"
    }
  }
}
```

Restart Claude Desktop. In a chat, ask:

> "What's the blast radius of `QueryEngine` in this repo?"

Claude should invoke `cbm_impact` automatically and paste the impact zone
back into the conversation.

**Prerequisite:** generate the graph once for the target repo:

```bash
cd /path/to/your/repo
codebase-map generate -c codebase-map.yaml
# → writes docs/function-map/graph.json
```

MCP tools default to `docs/function-map/graph.json`. Override per-call via
the `graph_file` argument.

## Tool reference

| Tool | Args | Example prompt |
|------|------|----------------|
| `cbm_query` | `name`, `graph_file` | "Where is `QueryEngine` defined?" |
| `cbm_search` | `keyword`, `graph_file`, `limit` | "Find everything matching `snapshot`." |
| `cbm_impact` | `name`, `graph_file`, `depth` | "What breaks if I change `QueryEngine`?" |
| `cbm_snapshot_diff` | `baseline`, `current`, `depth`, `breaking_only`, `test_plan`, `format` | "Compare the `baseline` and `post-dev` snapshots." |
| `cbm_api_catalog` | `graph_file`, `domain`, `method` | "List all API endpoints in this project." |

All tools return Markdown-ready text. `cbm_snapshot_diff` defaults to
`format: markdown` (PR-body paste); use `format: json` for programmatic
consumption.

## Performance

The server keeps a `GraphCache` singleton with mtime-based invalidation.
First call per graph file parses + indexes (~3 ms on a 200-node graph);
subsequent calls hit the cache in <1 ms. Regenerate `graph.json` → next
call re-reads transparently.

## Troubleshooting

**`cbm-mcp: command not found`** — `pipx` installs into `~/.local/bin`.
Run `pipx ensurepath` then restart your shell.

**Claude Desktop doesn't see the tools** — check
`~/Library/Logs/Claude/mcp-server-codebase-map.log`. Common causes:
`cbm-mcp` not on `PATH` in Desktop's launch env (use absolute path like
`/Users/you/.local/bin/cbm-mcp` in the config), or Python venv isolation
issues with `pipx`. Absolute-path fallback:

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
`docs/function-map/graph.json` relative to the current working directory.
Desktop launches `cbm-mcp` from `/`, so either pass `graph_file` as an
absolute path in the prompt, or set the working directory via `cwd` in the
MCP server config (future SDK feature — not yet widely supported).

## Registry submission

CBM is prepared for submission to the public MCP registry
([`anthropic-mcp` on GitHub](https://github.com/modelcontextprotocol/servers)).
See [`REGISTRY_SUBMISSION.md`](REGISTRY_SUBMISSION.md) for the submission
payload. CEO action to file the PR post-launch.

## Support

- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
- Docs: [main README](../../README.md)
- Release notes: [`docs/releases/v2.4.0.md`](../../docs/releases/v2.4.0.md)
