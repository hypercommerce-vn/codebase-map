---
name: saas-onboard
description: >
  Comprehensive onboarding summary for a SaaS codebase — modules, domains, APIs, data, entry points.
  Tóm tắt onboarding đầy đủ cho codebase SaaS — module, domain, API, dữ liệu, entry point.
---

Onboard a new engineer to this SaaS codebase in one pass. Output is a 7-bullet brief they can read in two minutes.

## Steps

1. **Graph presence check.** If `docs/function-map/graph.json` is missing, tell the user to run `/cbm-onboard` first. Stop.

2. **Domain scan.** Run `cbm_search` once per domain keyword group. Keep each call limited to 10 hits to stay fast:

   ```
   cbm_search(pattern="customer", limit=10)
   cbm_search(pattern="order", limit=10)
   cbm_search(pattern="subscription", limit=10)
   cbm_search(pattern="tenant", limit=10)
   cbm_search(pattern="auth", limit=10)
   cbm_search(pattern="webhook", limit=10)
   ```

   For each group, capture the match count. This gives a rough signal of domain density.

3. **API catalog.** Full count + top 5 routes by domain:

   ```
   cbm_api_catalog(format="text")
   ```

   Extract total endpoint count and the domain with the most routes.

4. **Data models.** Search for common data model signals:

   ```
   cbm_search(pattern="Model", limit=15)
   cbm_search(pattern="Schema", limit=15)
   ```

   Capture top 5 model names.

5. **Entry points.** Standard main / app / server signals:

   ```
   cbm_search(pattern="main", limit=5)
   cbm_search(pattern="app", limit=5)
   ```

   Filter to actual entry functions (`main`, `create_app`, `app.run`, etc.).

6. **Tier / subscription module.** One targeted probe:

   ```
   cbm_search(pattern="tier", limit=5)
   cbm_search(pattern="plan", limit=5)
   ```

   Note which file(s) house plan/tier logic.

7. **Integrations.** Look for common B2B SaaS integrations:

   ```
   cbm_search(pattern="stripe", limit=5)
   cbm_search(pattern="zalo", limit=5)
   cbm_search(pattern="shopify", limit=5)
   cbm_search(pattern="facebook", limit=5)
   ```

   Report which integrations are present.

## Deliverable — 7-bullet SaaS onboarding brief

Output as clean Markdown. No JSON dumps.

- **Scale:** total nodes / edges / domains (from `cbm_api_catalog` preamble or earlier `/cbm-onboard`).
- **Domain density:** top 3 domains by match count (e.g., `Customer: 24 · Order: 18 · Billing: 12`).
- **API surface:** total endpoint count · top domain · HTTP methods seen (`GET`, `POST`, etc.).
- **Data models:** top 5 model names with file paths.
- **Entry points:** `main` / `create_app` / route registration site.
- **Tier / subscription logic:** file(s) that house plan-gating. Flag if gating is scattered across 3+ files — that's a smell.
- **Integrations:** list of external systems integrated (Stripe, Zalo, Shopify, Facebook, Shopify, etc.), or "none detected".

Close with one-line next step, e.g. "Use `/saas-apis` to see the full API surface, or `/saas-tier-logic` to audit the subscription gating."

## Keep it tight

Seven bullets max. The user is a new engineer — too much information and they disengage. Don't dump JSON. Don't dump the full search results.
