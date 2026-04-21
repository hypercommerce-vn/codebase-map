---
name: saas-tier-logic
description: >
  Find tier/plan gating code and audit feature-gate correctness for this SaaS.
  Tìm code gating theo tier/plan và audit tính đúng đắn của feature-gate cho SaaS này.
---

Find everywhere this SaaS codebase gates features by subscription tier or plan, and audit whether the gating is centralized or scattered.

## Steps

1. **Graph presence check.** If `docs/function-map/graph.json` is missing, tell the user to run `/cbm-onboard` first. Stop.

2. **Scan for tier/plan signals.** Run three targeted searches:

   ```
   cbm_search(pattern="tier", limit=20)
   cbm_search(pattern="plan", limit=20)
   cbm_search(pattern="subscription", limit=20)
   ```

   Merge results. Deduplicate by `(file, name)`. Cap at 30 distinct hits to keep this command fast.

3. **Find a policy entry point.** Look for a single canonical gating function:

   ```
   cbm_search(pattern="is_allowed", limit=5)
   cbm_search(pattern="check_plan", limit=5)
   cbm_search(pattern="has_feature", limit=5)
   cbm_search(pattern="policy", limit=5)
   ```

   If at least one match returns, note it — that's the centralized gate. Call it `CENTRAL_GATE`.

4. **For each tier/plan hit, run impact at depth 1.**

   ```
   cbm_impact(name="<hit>", depth=1, format="json")
   ```

   Capture: caller count, caller file paths.

5. **Classify each hit.** Put it in one of these buckets:

   | Bucket | Rule |
   |--------|------|
   | **Central** | Hit IS the `CENTRAL_GATE` or calls it. Healthy. |
   | **Scattered** | Hit reads `plan`/`tier`/`subscription` directly without going through `CENTRAL_GATE`. Smell. |
   | **Data** | Hit is a model field / enum / constant (not a check). Fine. |
   | **Test** | Hit is in a test file. Fine. |

6. **Output format.** One Markdown block:

   ```markdown
   # Tier / Plan Gating Audit

   ## Centralized gate
   - `<CENTRAL_GATE>` @ `<path>` — N callers

   ## Scattered gating ⚠️
   - `<name>` @ `<path>` — reads `plan` directly. Affected callers: N.
   - …

   ## Data / enums
   - `<name>` @ `<path>`

   ## Tests
   - `<name>` @ `<path>`

   ## Summary
   - Scattered count: **N** · Central count: **M**
   - Recommendation: <see below>
   ```

7. **Recommendation logic:**

   | Scattered count | Recommendation |
   |-----------------|----------------|
   | 0 | "Gating is centralized. Healthy." |
   | 1–3 | "Mostly centralized. Migrate the 1–3 scattered checks into `<CENTRAL_GATE>` opportunistically." |
   | 4–10 | "Gating is drifting. Plan a sprint to consolidate into `<CENTRAL_GATE>`." |
   | > 10 | **"Gating is out of control. This is a multi-tenant SaaS bug risk. Schedule a dedicated refactor sprint."** |

8. **Tenant-isolation cross-check.** For each Scattered item, call:

   ```
   cbm_query(name="<scattered_item>")
   ```

   If the function body text does not contain `tenant` / `org` / `workspace`, flag it with a ⚠️ — checking plan without checking tenant is a classic multi-tenant B2B bug.

## Keep it tight

One Markdown audit block. Bucket counts, scattered list, recommendation. The user is deciding "do I need to refactor" — don't bury the answer in prose.
