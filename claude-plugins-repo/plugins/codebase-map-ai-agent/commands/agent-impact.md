---
name: agent-impact
description: >
  Blast radius for an agent class or tool method before refactor.
  Tác động khi đổi một agent class hay tool method — kiểm tra trước refactor.
---

Show the blast radius of changing `$ARGUMENTS` so the user can size an agent refactor before touching code.

## Steps

1. **Empty arg guard.** If `$ARGUMENTS` is empty or only whitespace, tell the user:

   > "Pass an agent class, tool function, or method name, e.g. `/agent-impact ResearchAgent.search` or `/agent-impact search_tool`. Unsure of the exact name? Run `/agent-overview` first."

   Then stop.

2. **Graph presence check.** If `docs/function-map/graph.json` is missing, tell the user to run `/cbm-onboard` first. Stop.

3. **Run impact at depth 2** (PR-review sweet spot):

   ```
   cbm_impact(name="$ARGUMENTS", depth=2, format="markdown")
   ```

4. **Not-found handling.** If the MCP result contains a "nearest match" / "did you mean" line, surface it verbatim and offer to re-run against the suggested name. Do not silently swap the input — let the user confirm.

5. **Parse + bucket callers by agent role.** Group affected nodes into:

   | Bucket | How to detect |
   |--------|---------------|
   | **Tool** | Name contains `_tool`, decorator `@tool`, or file path has `/tools/` |
   | **Orchestrator** | Name contains `orchestrat`, `dispatch`, `run`, `execute`, `coordinat` |
   | **Agent class** | File path has `/agents/` or name ends in `Agent` |
   | **Route / handler** | Has `@app.`, `@router.`, or name ends in `_handler` |
   | **Test** | File matches `test_*.py` or `*.test.ts` |
   | **Other** | Fallback |

   One line per bucket with count. Skip empty buckets.

6. **Risk signal.** From the affected node count:

   | Zone | Signal | Message |
   |------|--------|---------|
   | ≤ 10 | Low | "Safe local change. One PR fine." |
   | 11–50 | Medium | "Medium blast — keep PR focused, add tool contract tests." |
   | > 50 | **High** | **"High-risk. If this is a tool signature, prompts may break. Add deprecation shim + update system prompts first."** |

7. **Special flag — tool signature change.** If `$ARGUMENTS` matches a tool (bucket Tool above) AND the blast includes orchestrator callers, print an extra warning:

   > "⚠️ Tool signature change detected. LLM JSON schema contract affected. Steps: (1) add new tool alongside old, (2) update agent system prompt, (3) wait for LLM behavior to switch, (4) remove old tool."

## Keep it tight

Don't dump the full impact JSON. Three short sections: node count + risk, buckets, any tool-signature warning. That's it.
