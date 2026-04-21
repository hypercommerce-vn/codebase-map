---
name: cbm-impact
description: "Usage: /cbm-impact <function-or-class-name> — show blast radius before refactoring."
---

Show the blast radius of changing `$ARGUMENTS` so the user can size the refactor before touching code.

## Steps

1. **Empty arg guard.** If `$ARGUMENTS` is empty or only whitespace, tell the user:

   > "Pass a function or class name, e.g. `/cbm-impact CustomerService.create`. If you aren't sure of the exact name, try `codebase-map search \"<keyword>\" -f docs/function-map/graph.json` first."

   Then stop.

2. **Graph presence check.** If `docs/function-map/graph.json` is missing, tell the user to run `/cbm-onboard` first. Stop.

3. **Run impact at depth 2** (sweet spot for PR-review discussions — `--depth 3` default is too wide, `--depth 1` misses transitive callers):

   ```bash
   codebase-map impact "$ARGUMENTS" -f docs/function-map/graph.json --depth 2
   ```

4. **Not-found handling.** If CBM prints a "nearest match" / "did you mean" line, surface it verbatim and offer to re-run against the suggested name. Do not silently swap the input — let the user confirm.

5. **Parse the output.** Extract the affected node count. Count rules:

   | Zone size | Signal | Message |
   |-----------|--------|---------|
   | ≤ 10 | Low | "Safe local change. One PR is fine." |
   | 11–50 | Medium | "Medium blast radius — keep this PR focused, add targeted tests." |
   | **> 50** | **High** | **"High-risk refactor. Split into smaller PRs: introduce the new API first, migrate callers incrementally, remove the old surface last."** |

   Always print the exact node count alongside the signal.

6. **Group affected nodes by layer** when the output exposes layer info. Bucket into: `route` / `service` / `model` / `util` / `worker` / `other`. One line per bucket with counts. Skip empty buckets.

7. **Suggest test files.** For the top 3 affected service-layer nodes, run:

   ```bash
   codebase-map query "<node-name>" -f docs/function-map/graph.json
   ```

   Pull any `test_*.py` / `*.test.ts` callers from the caller list. Report as a checklist: "Tests to update / add: …". If no tests are found, flag it explicitly — that's a gap to close before merging.

## Keep it tight

Don't dump the full impact JSON. The user wants a decision aid: size, risk, which tests, whether to split. Three short sections is enough.
