---
name: agent-refactor-plan
description: >
  Staged refactor plan for an agent system — rank by blast radius, propose rollout.
  Kế hoạch refactor theo giai đoạn cho hệ thống agent — xếp hạng theo blast, đề xuất rollout.
---

Produce a staged refactor plan for the agent system in this repo. Output is a Markdown checklist the user can paste into a PR description or Notion.

## Steps

1. **Graph presence check.** If `docs/function-map/graph.json` is missing, tell the user to run `/cbm-onboard` first. Stop.

2. **Discover targets.** Call MCP `cbm_search` with `agent`, then `tool`:

   ```
   cbm_search(pattern="agent", limit=30)
   cbm_search(pattern="tool", limit=30)
   ```

   Merge. Filter to **public methods only** — names that don't start with `_`. Cap at 20 candidates to keep cost reasonable.

3. **For each candidate, run impact.** Use depth 1 (fast, just direct callers):

   ```
   cbm_impact(name="<candidate>", depth=1, format="json")
   ```

   Extract `affected_count` per candidate.

4. **Sort by blast radius.** Ascending. Small-blast items go in Stage 1 (easy). Large-blast items go in Stage 3 (risky, last).

5. **Group into 3 stages:**

   | Stage | Blast range | Rationale |
   |-------|-------------|-----------|
   | Stage 1 | 0–5 affected | Local cleanup. Rename, dead code, style. Ship in single PR. |
   | Stage 2 | 6–20 affected | Internal API tweaks. Ship in 2–3 PRs with targeted tests. |
   | Stage 3 | > 20 affected | Public contract changes. Ship with deprecation shim + system prompt updates. |

6. **Check for tool-signature items.** Any candidate whose name matches tool patterns (ends `_tool`, has `@tool` decorator, lives under `/tools/`) gets a ⚠️ flag — tool signature changes require prompt updates.

7. **Output format.** Markdown checklist, grouped by stage:

   ```markdown
   # Agent refactor plan

   ## Stage 1 — Low blast (local cleanup)
   - [ ] `<name>` — N affected callers
   - [ ] …

   ## Stage 2 — Medium blast (internal API)
   - [ ] `<name>` — N affected callers
   - [ ] …

   ## Stage 3 — High blast (public contracts) ⚠️
   - [ ] `<name>` — N affected callers — ⚠️ tool signature: update system prompt + add deprecation shim
   - [ ] …

   ## Recommended rollout
   1. Ship Stage 1 together (one PR).
   2. Ship Stage 2 items one PR each.
   3. For each Stage 3 item, use the 4-step tool migration: add-new → prompt-swap → observe → remove-old.
   ```

## Rules

- If fewer than 3 candidates remain after filtering, tell the user "Agent surface is small — a refactor plan isn't necessary. Use `/agent-impact <name>` per change instead."
- Never run `cbm_impact` with depth > 2 for this command — it's a planning pass, not a full audit. Depth 1 is correct.

## Keep it tight

One checklist, three stages, one rollout note. The user pastes this into a PR; extra prose gets deleted.
