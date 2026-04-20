# MCP Registry Submission — Codebase Map

**Status:** Ready to submit — CEO action post-launch.
**Target registry:** https://github.com/modelcontextprotocol/servers
**Owner for submission:** Đoàn Đình Tỉnh (CEO, Hyper Commerce)

## What the registry is

The official [`modelcontextprotocol/servers`](https://github.com/modelcontextprotocol/servers)
repo on GitHub lists community-built MCP servers. Anthropic surfaces the
list on modelcontextprotocol.io and in Claude Desktop's built-in server
picker. Inclusion is via pull request — fork, add an entry, open the PR.

## Our server metadata

Paste the block below into the registry's README (community servers table)
and open a PR.

```markdown
- **[codebase-map](https://github.com/hypercommerce-vn/codebase-map)**
  — Function dependency graph for Python/TypeScript codebases. 5 tools:
  `cbm_query`, `cbm_search`, `cbm_impact`, `cbm_snapshot_diff`,
  `cbm_api_catalog`. Auto-invokes on refactor / PR-impact / onboarding
  prompts. Install: `pipx install "codebase-map[mcp]"` then run `cbm-mcp`.
  (Hyper Commerce, MIT)
```

If the registry uses a YAML or JSON manifest instead of a Markdown table,
here is the equivalent metadata:

```yaml
name: codebase-map
display_name: Codebase Map
description: >
  Function dependency graph for Python/TypeScript codebases. Auto-invokes
  on impact / refactor / onboarding / PR-diff prompts.
publisher: Hyper Commerce
license: MIT
repo: https://github.com/hypercommerce-vn/codebase-map
docs: https://github.com/hypercommerce-vn/codebase-map/blob/main/integrations/mcp/README.md
install:
  pypi: codebase-map
  extras: [mcp]
  command: cbm-mcp
transport: stdio
tools:
  - cbm_query
  - cbm_search
  - cbm_impact
  - cbm_snapshot_diff
  - cbm_api_catalog
min_mcp_version: 1.27.0
languages_scanned: [python, typescript]
```

## Submission process

1. CEO forks `modelcontextprotocol/servers` into their personal GitHub
   account.
2. Add the entry above to the appropriate section of the registry README
   (community / productivity / code-intelligence — whichever lives on the
   repo's `main` branch at submission time).
3. Commit with message `docs: add codebase-map server`.
4. Open PR titled `Add codebase-map (dependency graph for Python/TS)`.
5. Body: link to [`integrations/mcp/README.md`](README.md),
   [`docs/releases/v2.4.0.md`](../../docs/releases/v2.4.0.md), and a
   screenshot of a working Claude Desktop conversation invoking one of
   the tools.
6. Respond to registry maintainer review comments.
7. Once merged, announce on CBM repo Discussions + Hyper Commerce blog.

## Pre-submission checklist

- [x] PyPI package published as `codebase-map` v2.4.0 with `[mcp]` extra
      (publish workflow fires on tag `v2.4.0` push)
- [x] `cbm-mcp` entry point installed and callable (`pipx install
      "codebase-map[mcp]"` → `cbm-mcp`)
- [x] 5 tools registered and individually smoke-tested (see
      [`CBM-INT-S2-Day5-Test-Report.md`](../../docs/active/cbm-claude-integration/CBM-INT-S2-Day5-Test-Report.md))
- [x] Claude Desktop config documented in
      [`integrations/mcp/README.md`](README.md)
- [x] License confirmed MIT
- [x] README + QUICKSTART updated with MCP section
- [ ] Live Claude Desktop dry-run screenshot (CEO action pre-PR)
- [ ] Fork `modelcontextprotocol/servers` (CEO action)
- [ ] PR filed (CEO action)

## Why post-launch

Registry maintainers prefer servers that are already stable, published,
and documented. Filing the PR *after* `v2.4.0` is live on PyPI (and a
couple of external users have tried it) strengthens the submission and
avoids a "come back when it's published" response.

## Rollback

If the registry rejects the submission for any reason, CBM continues to
work as a standalone MCP server — users install and configure manually
via [`integrations/mcp/README.md`](README.md). No dependency on registry
acceptance for the v2.4.0 launch.
