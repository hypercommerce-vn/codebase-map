# Review Gate — PR #38 (Round 1)

- **Date:** 2026-04-08
- **PR:** https://github.com/hypercommerce-vn/codebase-map/pull/38
- **Title:** fix: hotfix v2.0.1 Day 1 — classifier + API empty state
- **Branch:** `hotfix/v2.0.1-day1`
- **Mode:** Remote Full (Tester → CTO → Designer)

## Tier 1 — TESTER (blocking) — PASS

| Check | Result |
|---|---|
| `black --check codebase_map/` | PASS |
| `isort --check codebase_map/` | PASS |
| `flake8 codebase_map/` | PASS |
| Self-test (`-c codebase-map-self.yaml`) | 154 nodes, 774 edges, layers: core=16, util=122, model=16, **unknown=0** |
| HC regression (`HyperCommerce/codebase-map.yaml`) | **1565 nodes**, 9516 edges, 8 layers (no unknown), 11 domains, **187 routes** |
| CLI smoke: `query GraphBuilder` | OK (4 impacted) |
| CLI smoke: `search parser` | OK |
| CLI smoke: `impact GraphBuilder` | OK |
| CLI smoke: `summary` | OK |

HC unknown 173 → 0 verified. No node count regression.

## Tier 2 — CTO — 91/100

### A. Code Logic & Correctness — 22/25
- Python `_detect_layer` rule order is sound; `models.py` plural added; fallback `.py → UTIL` removes UNKNOWN bucket. Good.
- TS `_infer_layer`: `python_parser.py:140-256` rules well-ordered.
- **Minor risk** — `typescript_parser.py` ~line 410: the hooks branch mixes `and`/`or` without parentheses:
  ```
  or fname.startswith("use") and (fname.endswith(".ts") or fname.endswith(".tsx"))
  ```
  Python precedence makes this `or (startswith("use") and (...))` — works as intended, but is fragile. Recommend wrapping in explicit parens.
- Fallback strategy (.tsx→UTIL, .ts→SERVICE) is opinionated but documented in docstring.

### B. Architecture & Structure — 23/25
- Clean separation, no cross-cutting changes.
- All AI blocks tagged `HC-AI | ticket: CM-HOTFIX-V2.0.1` per CLAUDE.md rule.
- Baseline doc `project/hc-unknown-baseline.md` added for traceability.

### C. Parser Accuracy & Graph Integrity — 24/25 (≥20, no auto-block)
- HC: 1565 nodes (no regression), unknown=0, routes=187 preserved.
- Codebase-map self: unknown=0 with new config.
- No edges lost (9516 retained).

### D. Output Quality — 13/15
- API Catalog renderer escapes route names (`replace(/</g,'&lt;')`).
- Domain header uses untrusted `d` from `r.domain` without escape — controlled values today, low risk but worth tightening.
- CSS uses theme vars correctly.

### E. Production Readiness — 9/10
- BRIEF, board.html, task board all updated.
- Baseline doc shipped.

**CTO subtotal: 91/100**

## Tier 3 — DESIGNER — 89/100

(HTML/CSS review of `codebase_map/exporters/html_exporter.py` API Catalog block; no live preview needed — code review sufficient.)

| Dim | Score | Notes |
|---|---|---|
| A. Visual consistency | 18/20 | Uses `--bg-secondary`, `--border`, `--text-*` theme vars — consistent with rest of exporter. |
| B. Accessibility | 17/20 | `role="status"` on empty state. Icon is decorative emoji; no `aria-hidden`. |
| C. Layout | 18/20 | Flex column centered, dashed border, max-width 480px on hint. Clean. |
| D. Content / copy | 19/20 | Clear "why empty" + concrete tips (FastAPI/NestJS/Express) + onboarding link. Excellent for new users. |
| E. Responsiveness | 17/20 | Padding scales, max-width wrap. No explicit mobile breakpoint but flex handles it. |

**Designer subtotal: 89/100**

## Tier 4 — Impact Analysis

```
BRIEF.md                                  |  50 +++++++--
codebase_map/exporters/html_exporter.py   |  64 +++++++++++-
codebase_map/parsers/python_parser.py     |  67 +++++++++++-
codebase_map/parsers/typescript_parser.py | 114 +++++++++++++++++++--
project/CM-HOTFIX-V2.0.1-TASK-BOARD.md    | 163 ++++++++++++++++++++++++++++++
project/board.html                        |  15 ++-
project/hc-unknown-baseline.md            | 122 ++++++++++++++++++++++
7 files changed, 573 insertions(+), 22 deletions(-)
```

**Impact: MEDIUM** — 3 code files (~245 LOC). Touches classifier (graph integrity hot path) but verified non-regressive on HC (1565 nodes preserved).

## Final Score

| | |
|---|---|
| CTO × 0.6 | 54.60 |
| Designer × 0.4 | 35.60 |
| **Final** | **90.20** |

## Verdict: **SHIPIT + NOTE** (90–94 band)

CTO Dim C = 24 (≥20 threshold, no auto-block).

## Top Issues (non-blocking)

1. **TS hooks rule precedence** — `typescript_parser.py` hooks branch mixes `and`/`or`. Wrap in explicit parens for clarity. (Cosmetic; behavior correct.)
2. **Domain header escaping** — `api-domain .hdr` interpolates `d` (domain key) without HTML escape. Controlled set today; harden in next pass.
3. **Empty-state icon a11y** — Decorative emoji should get `aria-hidden="true"`.

## Recommendation for CEO

**APPROVE & MERGE.** Day 1 hotfix delivers stated outcomes:
- HC unknown layer: 173 → 0 (verified live)
- API Catalog empty state: ships clear, actionable copy
- No regression in node/edge/route counts on HC
- All lint and CLI smoke green

Top 3 issues are cosmetic/hardening — file as Day 2 polish, do not block merge.
