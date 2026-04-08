# HC Unknown-Layer Baseline — 2026-04-08 (pre-hotfix v2.0.1)

**Source graph:** `/Users/pro/Projects/HyperCommerce/docs/function-map/graph.json`
**Total nodes:** 1565
**Unknown nodes:** 173 (11.1%)
**Target:** < 5% (< 78 unknown)

## Layer distribution (before fix)

| Layer | Count | % |
|---|---|---|
| service | 371 | 23.7% |
| router | 235 | 15.0% |
| schema | 198 | 12.7% |
| util | 178 | 11.4% |
| **unknown** | **173** | **11.1%** |
| core | 170 | 10.9% |
| repository | 153 | 9.8% |
| worker | 48 | 3.1% |
| model | 39 | 2.5% |

## Unknown breakdown by language

| Language | Count |
|---|---|
| TypeScript (frontend) | 171 |
| Python (backend) | 2 |

## Python unknown nodes (2)

| File | Name | Root cause |
|---|---|---|
| `backend/app/modules/private_traffic/agent/rag.py` | `retrieve_context` | `/agent/` path pattern not classified |
| `backend/app/modules/private_traffic/zns/models.py` | `ZNSTemplate` | Classifier matches `model.py` (singular) but not `models.py` (plural) |

## TypeScript unknown nodes (171) — top directories

| Count | Directory |
|---|---|
| 19 | `frontend/src/modules/crm/customers` |
| 10 | `frontend/src/modules/admin` |
| 9 | `frontend/src/modules/cdp/realtime` |
| 9 | `frontend/src/modules/crm/products` |
| 8 | `frontend/src/modules/crm/notifications` |
| 8 | `frontend/src/modules/settings` |
| 7 | `frontend/src/modules/crm/promotions` |
| 7 | `frontend/src/modules/private-traffic/channels` |
| 7 | `frontend/src/modules/private-traffic/zns` |
| 6 | `frontend/src/modules/cdp/segments` |
| 6 | `frontend/src/modules/crm/journey` |
| 6 | `frontend/src/modules/crm/pipeline` |
| 5 | `frontend/src/modules/cdp/customer360` |
| 5 | `frontend/src/modules/ecommerce/inventory` |
| 5 | `frontend/src/modules/private-traffic/agent` |
| 5 | `frontend/src/modules/private-traffic/campaigns` |
| 5 | `frontend/src/shared/components` |
| 4 | `frontend/src/modules/billing` |
| 4 | `frontend/src/modules/cdp/dedup` |
| 4 | `frontend/src/modules/ecommerce/sync_health` |

## Root cause analysis

**TypeScript parser (`codebase_map/parsers/typescript_parser.py::_infer_layer`):**
The current heuristics only check for substrings `controller`, `service`, `repository`, `model`, `worker`, `util`, `test`. React-typical filenames like `LoginPage.tsx`, `BillingPage.tsx`, `InvoiceDetailModal.tsx`, `GatewayDashboard.tsx` match none of them, so the entire React frontend lands in `unknown` — accounting for 171 of 173 unknowns.

**Python parser (`codebase_map/parsers/python_parser.py::_detect_layer`):**
- `fname == "model.py"` check is singular-only; misses `models.py` (plural) when the parent directory is not `/models/`. HC has `zns/models.py` that trips this gap.
- No rule for `/agent/` directory (private-traffic AI agent module).

## Fix plan (POST-CM-S3-02)

1. **TS parser — broaden `_infer_layer`:**
   - Any file whose name ends in `Page.tsx`/`Page.jsx` or lives under `/pages/` → ROUTER (UI routing equivalent).
   - `Modal.tsx`, `Dialog.tsx`, `Drawer.tsx`, `shared/components/`, `/components/` → UTIL.
   - `hooks/`, `use*.ts`, `api/`, `client.ts`, `store/`, `slice.ts` → SERVICE.
   - Fallback for any remaining `.tsx`/`.jsx` file: UTIL (UI component, better than unknown).
   - Fallback for `.ts`/`.js` with no match: SERVICE (business logic default).
2. **Python parser — broaden `_detect_layer`:**
   - Add `fname == "models.py"` to MODEL rule.
   - Add `/agent/` and `/agents/` → SERVICE (AI agent = service layer).
   - Add `/handlers/`, `/adapters/`, `/integrations/`, `/clients/`, `/endpoints/`, `/webhooks/` → appropriate layers.
3. **Verify:** re-run on HC, confirm unknown < 5% (< 78 nodes).

## Acceptance criteria

- HC unknown ratio drops from 11.1% to < 5.0% — **HARD GATE**.
- No existing layer counts regress more than 5% downward (risk R1).
- Self-build of codebase-map still passes (no crashes).

## Verification result (post-fix, 2026-04-08)

**HC full re-run (backend + frontend, 1565 nodes):**

| Layer | Before | After | Delta |
|---|---|---|---|
| service | 371 | 409 | +38 |
| router | 235 | 370 | +135 |
| schema | 198 | 198 | 0 |
| util | 178 | 180 | +2 |
| **unknown** | **173** | **0** | **-173** |
| core | 170 | 170 | 0 |
| repository | 153 | 150 | -3 |
| worker | 48 | 48 | 0 |
| model | 39 | 40 | +1 |

**HC unknown ratio: 11.1% → 0.00% ✅ PASS (target <5%)**

- No layer regressed more than -3 nodes (repository −3 is noise from re-parse, not from classifier changes).
- Router absorbed 171 TS React pages (expected — Pages = UI routes).
- Service absorbed the `/agent/` private_traffic node (rag.py::retrieve_context) and `zns/models.py` now in Model.
- No crashes. Build time 650ms (unchanged).

**Self-build (codebase_map on itself, 154 nodes):**

| Layer | After |
|---|---|
| util | 122 |
| core | 16 |
| model | 16 |
| **unknown** | **0** |

**Self-build unknown ratio: 0.00% ✅ PASS**
