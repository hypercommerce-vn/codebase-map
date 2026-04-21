---
name: agent-overview
description: >
  Map agent structure — entry points, tool registry, orchestration layers.
  Map cấu trúc agent — entry point, tool registry, lớp orchestration.
---

Map the structure of this agent codebase so the user can answer "what does this agent do" in one pass.

## Steps

1. **Graph presence check.** If `docs/function-map/graph.json` is missing, tell the user to run `/cbm-onboard` first. Stop.

2. **Discover agent classes.** Call MCP `cbm_search` with pattern `agent`:

   ```
   cbm_search(pattern="agent", limit=20)
   ```

   Capture the top hits. Filter by name — look for entries containing `Agent`, `agent_`, `_agent`, or class names ending in `Agent`.

3. **Discover tool functions.** Call `cbm_search` with pattern `tool`:

   ```
   cbm_search(pattern="tool", limit=30)
   ```

   Filter matches. A tool is typically:
   - A function decorated with `@tool` / `@function_tool` / `@register_tool`
   - A method on an `Agent` subclass whose name starts with a verb
   - A function listed in a `tools=[...]` kwarg

4. **Detail top 3 agent classes.** For each top agent hit, call `cbm_query`:

   ```
   cbm_query(name="<AgentClassName>")
   ```

   Extract: file path, public methods, caller count.

5. **Find entry points.** Call `cbm_search` once more with `main`:

   ```
   cbm_search(pattern="main", limit=10)
   ```

   Also look for `run`, `execute`, `__main__`. These are likely entry points.

6. **API surface (optional).** If the agent exposes HTTP endpoints, call `cbm_api_catalog`:

   ```
   cbm_api_catalog(format="text")
   ```

   If zero endpoints, note "CLI-only agent" or "library-only agent".

## Deliverable — 5-bullet agent overview

Output as a clean Markdown block. No JSON dumps.

- **Agent classes:** list top 3 with file paths (e.g., `ResearchAgent @ src/agents/research.py`).
- **Tool count:** total functions matching tool patterns. List the top 5 by name.
- **Entry points:** where execution starts (`main`, route, CLI command).
- **Orchestration layer:** any class/function with `orchestrat`, `dispatch`, `route`, `coordinat` in its name — flag it as hot-path.
- **API surface:** endpoint count (skip this bullet if zero).

Close with a one-line recommendation, e.g. "Multi-agent shape with 4 agents and 12 tools — start refactor reviews with `/agent-impact Orchestrator`."

## Keep it tight

Three short Markdown sections max. The user wants a mental model of the codebase, not a full graph dump.
