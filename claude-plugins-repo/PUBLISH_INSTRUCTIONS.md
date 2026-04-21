# CEO Instructions — Publishing `hypercommerce-vn/claude-plugins`

These instructions turn this staging directory (`claude-plugins-repo/`
inside the `codebase-map` repo) into a standalone public repo at
`github.com/hypercommerce-vn/claude-plugins`. Only the CEO / org admin
can run Step 1 (repo creation).

---

## Research summary (Day 2, 21/04/2026)

- **No official Anthropic/MCP plugin registry exists** as of 21/04/2026.
  Anthropic's org hosts SDKs (`anthropic-sdk-*`) but no `claude-plugins`
  or `mcp-servers` repo.
- `modelcontextprotocol/servers` is the closest — but it indexes MCP
  servers, not Claude Code plugins with skills/commands/hooks.
- Community marketplaces (obra/superpowers-marketplace,
  davepoon/buildwithclaude, ananddtyagi/cc-marketplace) use a
  consistent convention: `.claude-plugin/marketplace.json` with
  `$schema: https://anthropic.com/claude-code/marketplace.schema.json`.
- **Conclusion:** self-host the marketplace at
  `hypercommerce-vn/claude-plugins`. Users add it via
  `/plugin marketplace add hypercommerce-vn/claude-plugins`.

## Step 1 — Create the GitHub repo (CEO)

```bash
gh repo create hypercommerce-vn/claude-plugins --public \
    --description "Curated plugins for Claude Code and Cowork" \
    --license MIT
```

Alternative (web UI): https://github.com/organizations/hypercommerce-vn/repositories/new

## Step 2 — Push the staging content to the new repo

From any machine with push rights:

```bash
cd /tmp
cp -r /Users/pro/Projects/codebase-map/claude-plugins-repo claude-plugins
cd claude-plugins
git init
git add .
git commit -m "Initial commit: codebase-map plugin v2.5.0"
git branch -M main
git remote add origin git@github.com:hypercommerce-vn/claude-plugins.git
git push -u origin main
```

## Step 3 — Verify the plugin is discoverable

```bash
gh repo view hypercommerce-vn/claude-plugins
# browse: https://github.com/hypercommerce-vn/claude-plugins
```

Quick manual test in Claude Code:

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map@hypercommerce-vn
```

Confirm the Skill, 3 slash commands, and MCP server register.

## Step 4 (optional) — Submit to community indexes

No official upstream registry exists, but a handful of community
aggregators crawl marketplace repos. Opening a PR there after launch
boosts discoverability:

- `davepoon/buildwithclaude` — browse-only site, accepts submissions
- `ananddtyagi/cc-marketplace` — PR-driven aggregator

Route through whichever lines up with our launch post
(CBM-INT-305, Day 4).

## Expected outcome

Users in Cowork or Claude Code can run:

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map@hypercommerce-vn
```

…and the post-install hook pulls `codebase-map[mcp]>=2.4.0` via pipx.

## Post-publish checklist

- [ ] Repo `hypercommerce-vn/claude-plugins` created public with MIT license
- [ ] Initial content pushed to `main`
- [ ] `marketplace.json` validates against the Claude Code schema
      (automated: the first CI run will confirm)
- [ ] At least one manual test install works end-to-end on macOS
- [ ] Add repo URL to CBM README under "Install via plugin"
      (separate PR in the `codebase-map` repo)
- [ ] Announce on launch day (Day 4-5, CBM-INT-305)

## Questions / risks

- **Cowork marketplace schema may drift.** The `$schema` URL is the
  community convention (confirmed in `davepoon/buildwithclaude`), but
  Anthropic has not published a stable spec yet. If validation fails
  in CI post-launch, expect a small follow-up PR to adjust field
  shapes.
- **If Anthropic ships an official registry during Q2 2026**, submit
  our plugin there and keep the self-hosted marketplace as a mirror.
- **Name collision risk: low.** `codebase-map` is unique across the 4
  community marketplaces surveyed on 21/04/2026.
