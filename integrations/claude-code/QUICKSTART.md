# Quick Start — CBM for Claude Code users · 30-second setup

`codebase-map` (CBM) is a dependency graph tool that plugs into Claude Code as
a Skill + 3 slash commands. This guide installs everything in ~30 seconds.

## Prerequisites

- Python 3.10+ (`python3 --version`)
- `pipx` (recommended) or `pip`
- Claude Code CLI installed and logged in

## 1. Install CBM CLI

```bash
pipx install codebase-map
```

If `pipx` is unavailable, `pip install --user codebase-map` works. Verify:

```bash
codebase-map --version
```

## 2. Install Skill + slash commands (one-liner)

Downloads the Claude Code Skill file and all 3 slash commands into your user
config:

```bash
mkdir -p ~/.claude/skills/codebase-map ~/.claude/commands \
  && BASE="https://raw.githubusercontent.com/hypercommerce-vn/codebase-map/main/integrations/claude-code" \
  && curl -fsSL "$BASE/skills/codebase-map/SKILL.md"    -o ~/.claude/skills/codebase-map/SKILL.md \
  && curl -fsSL "$BASE/commands/cbm-onboard.md"         -o ~/.claude/commands/cbm-onboard.md \
  && curl -fsSL "$BASE/commands/cbm-impact.md"          -o ~/.claude/commands/cbm-impact.md \
  && curl -fsSL "$BASE/commands/cbm-diff.md"            -o ~/.claude/commands/cbm-diff.md \
  && echo "CBM installed."
```

Prefer installing per-project? Swap `~/.claude/` for `.claude/` inside the
repo root.

## 3. Try it

Open any Python or TypeScript repo in Claude Code, then run:

```
/cbm-onboard
```

## Expected result

Within ~30 seconds you see a 5-bullet onboarding summary covering:

- Scale (nodes, edges, domains)
- Top 3 domains by size
- API surface (HTTP routes detected)
- Coverage gaps (if `coverage.json` is present)
- Entry points (`main`, CLI handlers, route handlers)

An interactive HTML graph is written to `docs/function-map/index.html`. CBM
does NOT auto-open it — you decide.

## Baseline workflow (for PR review)

The dual-snapshot diff is where CBM shines on pull requests. First-time users
often miss it — run these 3 steps to get the richer before/after view:

```bash
# On the base branch, BEFORE starting your refactor:
codebase-map generate --label baseline

# After finishing your changes on the feature branch:
codebase-map generate --label post-dev
```

Then in Claude Code:

```
/cbm-diff main
```

You get a Markdown PR-body section with added/removed/modified functions,
affected callers grouped by domain, and a suggested test plan. Paste it into
the PR description. (Skipping the `baseline` snapshot falls back to a
shallower git-diff mode — still useful, but lighter.)

## Alternative: MCP server (Claude Desktop / Cowork)

Prefer MCP tool calls over slash commands? CBM v2.4.0+ ships an MCP server
with 5 auto-invoke tools (`cbm_query`, `cbm_search`, `cbm_impact`,
`cbm_snapshot_diff`, `cbm_api_catalog`). Install with the `[mcp]` extra:

```bash
pipx install "codebase-map[mcp]"
```

Then wire `cbm-mcp` into your Claude Desktop config — see
[`integrations/mcp/README.md`](../mcp/README.md) for the full walkthrough.

The MCP path is **complementary** to the slash commands. Use MCP when Claude
invokes tools conversationally; use slash commands for deterministic,
explicit workflows.

## Troubleshooting

**`codebase-map: command not found`** — `pipx` installs into
`~/.local/bin`. Either `pipx ensurepath` then restart your shell, or add
`export PATH="$HOME/.local/bin:$PATH"` to your shell rc file.

**`codebase-map.yaml not found`** — `/cbm-onboard` auto-creates a default
config. For manual setup, copy
[`codebase-map.example.yaml`](https://github.com/hypercommerce-vn/codebase-map/blob/main/codebase-map.example.yaml)
and adjust `path` + `base_module` to match your source layout.

**Claude doesn't auto-invoke the skill** — confirm the file lives at
`~/.claude/skills/codebase-map/SKILL.md` (not one directory deeper). Restart
Claude Code if it was already running when you installed the skill.

## Language support

CBM v2.3.0 ships native parsers for **Python** and **TypeScript**. JavaScript
and Java support is planned for v2.4 (CBM-LANG-P1). Other languages are not
yet supported — `/cbm-onboard` will tell you and stop cleanly.

## Next steps

- Full docs and CLI reference: [README](https://github.com/hypercommerce-vn/codebase-map/blob/main/README.md)
- How to contribute: [CONTRIBUTING](https://github.com/hypercommerce-vn/codebase-map/blob/main/CONTRIBUTING.md)
- Reporting security issues: [SECURITY](https://github.com/hypercommerce-vn/codebase-map/blob/main/SECURITY.md)

For feedback or bugs, open an issue: https://github.com/hypercommerce-vn/codebase-map/issues
