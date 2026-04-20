# Review Gate — PR #39 Round 1

- Date: 2026-04-08
- Branch: `hotfix/v2.0.1-day2`
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/39
- Title: fix: hotfix v2.0.1 Day 2 — coverage hook + generate --diff + polish
- Scope: POST-CM-S3-01, POST-CM-S3-04, POLISH-01/02/03
- Files touched: `codebase_map/cli.py`, `codebase_map/exporters/html_exporter.py`, `codebase_map/parsers/typescript_parser.py` (+BRIEF/board docs)
- Diff stat: 6 files, +178 / -46

---

## Tier 1 — TESTER (blocking gates)

| Check | Result |
|---|---|
| `black --check codebase_map/` | PASS (20 files unchanged) |
| `isort --check codebase_map/` | PASS |
| `flake8 codebase_map/` | PASS (0 warnings) |
| Self-build (codebase_map on itself) | PASS — 154 nodes, 778 edges, 0 unknown layer |
| `generate --diff main` | PASS — `pr_diff.json` written (6.9KB), 26 changed / 0 impacted, valid JSON with `ref`, `changed_files`, `changed_nodes` |
| `generate --diff main --diff-depth 2` | PASS |
| `generate --diff nosuchref` (edge) | PASS — prints `[WARN] git diff failed: ...` then continues with 0 changed. No crash. HTML still renders. |
| HC regression (1565 baseline) | PASS — 1565 nodes, 9516 edges, 187 routes, 0 unknown layer. Matches Day 1 baseline exactly. Build 1161ms, 100% cache hit. |
| CLI smoke: summary / search / query / impact | PASS |

Tester verdict: **GREEN** — no blocking issues.

---

## Tier 2 — CTO (5 dimensions, 100 pts)

### A. Code Logic & Correctness — 24/25
- `--diff` branch wraps DiffAnalyzer in `try/except Exception` with `# noqa: BLE001` — appropriate for user-facing CLI, prints warning and continues rather than aborting the full generate. Verified behavior with invalid ref.
- Uses `getattr(args, "diff", "") or ""` defensively — tolerates future refactors where subcommand doesn't set the attr.
- Coverage detection: `nodes.some(n => n.metadata && n.metadata.coverage && typeof n.metadata.coverage.percent === 'number')` — correctly guards against missing `metadata`, missing `coverage`, and wrong type.
- Per-domain aggregation uses running sum/count, rounds with `Math.round` — correct mean.
- Minor nit (-1): when `hasCoverage` is true but a specific domain has `covCount === 0`, the label becomes "Layer diversity (no cov data)" which is informative, but the `healthPct` for that domain falls back to `layerCount * 14` — fine, but users could be slightly confused seeing mixed metrics across cards in one view. Not blocking.

### B. Architecture & Structure — 24/25
- `--diff` / `--diff-depth` placed on `generate` subparser — correct location (unified single-command flow).
- Lazy import `from codebase_map.graph.diff import DiffAnalyzer` inside the `if diff_ref:` block — avoids hard dependency when users don't use the flag. Good.
- `htmlEscape()` helper defined once in the JS bundle and reused across API Catalog + Executive view — DRY.
- Minor (-1): helper is a nested f-string inside Python with `{{ }}` escaping; could eventually move to a templates/ file (already hinted in repo structure), but out-of-scope for hotfix.

### C. Parser Accuracy & Graph Integrity — 25/25 (AUTO-BLOCK gate cleared)
- POLISH-01 only adds explicit parentheses around the `(fname.startswith("use") and (fname.endswith(".ts") or fname.endswith(".tsx")))` clause. **Semantically identical** to v2.0.0 under Python precedence (`and` binds tighter than `or`), but now unambiguous to readers and linters.
- HC regression proves zero graph drift: 1565/9516/187 routes identical to Day 1 baseline.
- No changes to Python parser, builder, or graph models.

### D. Output Quality — 14/15
- `htmlEscape()` covers all 5 required entities: `&`, `<`, `>`, `"`, `'`. Verified by reading source.
- Applied to: API Catalog domain header, route label, Executive card `data-domain`, card title, `<h3>` domain text, dynamic `healthTitle` tooltip. Good coverage of attacker-reachable paths.
- `pr_diff.json` shape validated — includes `ref`, `changed_files`, `changed_nodes` (with full node metadata), impacted set.
- Coverage tooltip copy: "Real coverage from pytest-cov: X/Y nodes covered" is clear. Fallback title "Proxy metric — run `codebase-map coverage` for real test-coverage health" is actionable.
- Minor (-1): Exec card `data-domain` attribute is HTML-escaped (`&#39;` etc.) which means any JS reading `card.dataset.domain` gets the raw name back via DOM decoding — OK, but if downstream code does `querySelector([data-domain="..."])` with the raw name, selector will miss. Not currently an issue (no such selector exists), flag for follow-up.

### E. Production Readiness — 10/10
- Lint gate PASS (black/isort/flake8 all clean).
- Every new block tagged `# HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-01|POST-CM-S3-04|POLISH-01|POLISH-02)` per project rules.
- No dead code, no TODOs left behind, no print-debugging.
- Help strings on new flags are clear and include example (`'main'`).

**CTO total: 97/100**

---

## Tier 3 — DESIGNER (5 dimensions, 100 pts)

Code-review only (preview_start not attempted — hotfix scope, design already approved in PR #38, only 1 aria attr + 1 label tweak).

### A. Visual Consistency — 19/20
- Executive card layout unchanged. Health bar color thresholds preserved (`<40 red`, `<70 amber`, else green).
- New right-label `${healthPct}%` vs `${layerCount} layers` uses same `.health-label` span — consistent.

### B. Accessibility — 20/20
- POLISH-03: `aria-hidden="true"` correctly added to the decorative emoji icon `&#x1f50c;` in API empty state. Screen readers now skip the visual decoration and read the meaningful `es-title` / `es-hint` directly. Textbook fix.
- `role="status"` on the empty-state container preserved.
- Tooltip on exec card (`title=`) supplements visual health bar with text — good for keyboard/SR users.

### C. Layout — 19/20
- No layout shifts: health bar, stats row, h3 all retain exact DOM structure.
- `title` attribute added on card root — invisible until hover, zero layout impact.

### D. Copy — 19/20
- "Test coverage" / "Layer diversity" / "Layer diversity (no cov data)" — three states clearly differentiated.
- Tooltip copy actionable ("run `codebase-map coverage` for real test-coverage health").
- Minor (-1): "(no cov data)" abbreviation could be "(no coverage data)" for clarity, but space-constrained in the label row — acceptable trade-off.

### E. Responsiveness — 19/20
- No viewport-specific changes; exec-grid / api-domain remain as-is. No regressions expected.

**Designer total: 96/100**

---

## Tier 4 — Impact

```
BRIEF.md                                  | 40 ++++++++++++--------
codebase_map/cli.py                       | 45 ++++++++++++++++++++++
codebase_map/exporters/html_exporter.py   | 62 ++++++++++++++++++++++++++-----
codebase_map/parsers/typescript_parser.py | 11 ++++--
project/CM-HOTFIX-V2.0.1-TASK-BOARD.md    | 32 ++++++++++------
project/board.html                        | 34 ++++++++++++++---
```

- Code files: 3 (cli, exporter, ts parser)
- CLI hot path touched (new subcommand flags) + exporter (JS template)
- Parser change is cosmetic-only (parens, no semantic delta)
- HC regression clean (identical to baseline)

**Impact level: MEDIUM** — new CLI surface + JS rendering logic, but no graph/model changes and regression confirmed.

---

## Final Score

```
Final = (CTO * 0.6) + (Designer * 0.4)
      = (97 * 0.6) + (96 * 0.4)
      = 58.2 + 38.4
      = 96.6
```

- CTO dim C = 25 (≥20, no auto-block)
- Tester: GREEN
- Final: **96.6 / 100**
- Threshold: ≥95 → **SHIPIT**

---

## Verdict: SHIPIT

All 5 PR items verified working:
1. POST-CM-S3-01 coverage hook — falls back cleanly, tooltip actionable
2. POST-CM-S3-04 `--diff` / `--diff-depth` — creates valid `pr_diff.json`, handles invalid ref
3. POLISH-01 parser parens — no graph drift (HC 1565 baseline preserved)
4. POLISH-02 `htmlEscape()` — full 5-char coverage on all domain/route headers
5. POLISH-03 `aria-hidden` on decorative icon — correct pattern

## Top 3 Follow-ups (non-blocking)

1. Consider extracting `html_exporter.py` inline JS into `templates/` files — the f-string `{{ }}` escaping is becoming hard to read.
2. Mixed-metric rendering in Executive view when only some domains have coverage — consider hiding proxy fallback entirely once real coverage is baked, or stamping "partial coverage" badge.
3. `data-domain` attribute is HTML-entity-escaped — document that any future `querySelector('[data-domain=...]')` consumers must use the decoded name.

## Recommendation to CEO

**Approve & merge PR #39, then tag `v2.0.1`.** All Day 2 objectives delivered, HC regression clean at the 1565/0-unknown baseline set by Day 1, accessibility and security polish items done cleanly. No blocking issues.
