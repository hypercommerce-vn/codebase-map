# CM-HOTFIX v2.0.1 — Task Board

**Sprint:** Hotfix v2.0.1
**Created:** 2026-04-08
**Owner:** PM (orchestrator) · Tech Lead (implementer) · Designer (CM-03 visual) · Tester + CTO + Designer (review gate)
**Approver:** CEO
**Source backlog:** `project/POST-CM-S3-HOTFIX-PLAN.md` (issues #32–#35)
**Parent sprint:** CM-S3 v2.0.0 (delivered 07/04/2026)

---

## 1. Sprint Goal

Ship `v2.0.1` hotfix release to address 4 post-delivery polish items surfaced by FullTest and HC customer feedback. Priority focus: **reduce HC "unknown" layer ratio from ~11% (173/1565) to <5%** via POST-CM-S3-02, and **eliminate manual 2-step PR Diff bake** via POST-CM-S3-04.

**Definition of Done:**
- All 4 acceptance criteria (HOTFIX-AC-01..04) pass
- Re-run on HC repo shows unknown-layer ratio <5%
- CI green, Mode 2 Remote Full score ≥95/100
- Tag `v2.0.1` pushed, GitHub release published
- Release notes link sent to HC customer

---

## 2. Scope

| # | ID | Item | SP | Day | Owner |
|---|----|------|----|-----|-------|
| 1 | POST-CM-S3-02 | Fix CM-AC-05 self-build false positive / unknown layer classifier | 0.5 | Day 1 | Tech Lead |
| 2 | POST-CM-S3-03 | API Catalog better empty state (Python-only projects) | 0.5 | Day 1 | Designer + TL |
| 3 | POST-CM-S3-01 | Hook real coverage into Executive health bar | 1 | Day 2 | Tech Lead |
| 4 | POST-CM-S3-04 | Auto-bake `pr_diff.json` via `generate --diff <ref>` flag | 1 | Day 2 | Tech Lead |
| **Total** | | | **3** | | |

**Out of scope:** new features, design changes beyond empty-state copy/visual, TS coverage overlay, customer-facing UI redesign.

---

## 3. Timeline

### Day 1 — Classifier + Empty State → PR #1 — ✅ DONE (2026-04-08)

| Slot | Task | Owner | Output | Status |
|------|------|-------|--------|--------|
| AM 1 | POST-CM-S3-02 — Unknown layer classifier fix | Tech Lead | TS + Py classifiers broadened | ✅ |
| AM 2 | POST-CM-S3-02 — Re-run on HC repo, verify <5% unknown | Tech Lead | HC 173→0 unknown (0.00%) | ✅ |
| PM 1 | POST-CM-S3-03 — API Catalog empty state copy + icon | Designer | Copy + icon + dashed card | ✅ |
| PM 2 | POST-CM-S3-03 — TL implement in HTML exporter | Tech Lead | `renderApiCatalog()` + CSS | ✅ |
| PM 3 | Local Pre-flight lint gate | PM | black/isort/flake8 PASS | ✅ |
| EOD | Push PR #38 → Review gate → CEO approve → merge | PM + CEO | PR #38 merged, Final 90.20 SHIPIT+NOTE | ✅ |

**PR #38:** https://github.com/hypercommerce-vn/codebase-map/pull/38 (MERGED 2026-04-08)
**Review report:** `docs/reviews/ReviewGate_PR38_Round1_2026-04-08.md`
**Polish carried to Day 2:** POLISH-01 (TS hooks precedence) · POLISH-02 (API domain escape) · POLISH-03 (empty-state aria-hidden)

### Day 2 — Coverage Hook + Diff Flag + Polish Bundle → PR #2 → Release — 🟡 ACTIVE (2026-04-08)

| Slot | Task | Owner | Output | Status |
|------|------|-------|--------|--------|
| AM 1 | POLISH-01 — TS hooks `and`/`or` precedence parentheses | Tech Lead | Explicit parens in `typescript_parser.py` | ✅ |
| AM 2 | POLISH-02 — HTML-escape API domain header | Tech Lead | `htmlEscape()` helper + usage | ✅ |
| AM 3 | POLISH-03 — `aria-hidden="true"` on empty-state emoji | Tech Lead | `html_exporter.py` a11y fix | ✅ |
| AM 4 | POST-CM-S3-01 — Real coverage aggregation + Executive health bar | Tech Lead | Prefers `metadata.coverage.percent`, proxy fallback | ✅ |
| PM 1 | POST-CM-S3-04 — `generate --diff <ref>` CLI flag | Tech Lead | `--diff` + `--diff-depth` args | ✅ |
| PM 2 | POST-CM-S3-04 — Auto-bake `pr_diff.json` in output dir | Tech Lead | Unified 1-command flow verified (26 changed on self-build) | ✅ |
| PM 3 | Local Pre-flight lint gate | PM | black/isort/flake8 PASS | ✅ |
| PM 4 | HC regression — no-cache rebuild, verify 1565 nodes/0 unknown | PM | 1565 nodes, 0 unknown confirmed | ✅ |
| EOD | Push PR #39 → review gate Mode 2 → CEO approve → merge | PM + CEO | [PR #39](https://github.com/hypercommerce-vn/codebase-map/pull/39) opened | 🟡 |
| Post | Tag `v2.0.1` + GitHub release + notify HC | CEO | — | ⏳ |

**Slip buffer:** If Day 2 overflows, POST-CM-S3-01 (coverage hook) ships in v2.0.1 and POST-CM-S3-04 defers to v2.0.2. POST-CM-S3-04 has higher user value — re-sequence if risk emerges at Day 2 AM checkpoint.

---

## 4. Acceptance Criteria

### HOTFIX-AC-01 — `generate --diff` unified flag (POST-CM-S3-04)
- `codebase-map generate -c x.yaml --diff main` produces HTML with PR Diff view fully baked in a single command
- No intermediate `codebase-map diff` step required
- Backward compatible — existing 2-step flow still works
- CLI `--help` documents the flag
- Unit test covers flag wiring

### HOTFIX-AC-02 — Executive real coverage (POST-CM-S3-01)
- When `coverage.xml` (or JSON equivalent) exists in `.codebase-map-cache/`, Executive view health bar displays real `covered_lines / total_lines` ratio
- When coverage absent, health bar gracefully falls back to layer-diversity proxy with tooltip "coverage unavailable"
- Coverage source clearly labeled in UI

### HOTFIX-AC-03 — Unknown layer classifier fix (POST-CM-S3-02)
- Self-build of codebase-map repo shows unknown-layer ratio <5% (currently >90% false positive from tool's own tools/ dir)
- Re-run on HC repo reduces unknown from ~11% (173/1565) to **<5%**
- Classifier explicitly handles: `tools/`, `scripts/`, `tests/`, `docs/`, entry-point modules, `__main__.py`
- Regression test on fixture repos (HC-slice + self-build)

### HOTFIX-AC-04 — API Catalog empty state (POST-CM-S3-03)
- Python-only projects without detected routes show informative placeholder (not blank / not broken)
- Copy explains: "No HTTP routes detected in this project" + small help hint
- Visual: icon + muted color per CM-S1 empty-state design pattern
- Matches design preview approved copy

### Global
- All CI jobs green (lint, test 3.10–3.12, generate verify, Telegram notify)
- Mode 2 Remote Full review gate ≥95/100 (Tester PASS · CTO ≥95 · Designer ≥95)
- Lint gate pre-commit: `black + isort + flake8` all clean
- Every AI-generated block tagged `# HC-AI | ticket: CM-HOTFIX-V2.0.1`
- Conventional commits

---

## 5. Review Gate Checklist

Standard 2-tier per Critical Rule #6 (from CM-S3).

**Per PR:**
- [ ] Local Pre-flight `/review-gate --local` — CTO local ≥80, Dim C ≥20/25 before push
- [ ] CI green after push
- [ ] Mode 2 Remote Full `/review-gate PR #XX`
  - [ ] Tester — functional + regression on HC fixture + self-build
  - [ ] CTO — code quality, architecture impact (expected 🟢 Low), Dim scores
  - [ ] Designer — empty state visual (PR #1) + Executive health bar visual (PR #2) via `mcp__Claude_Preview`
  - [ ] Every dimension cites reference docs per Rule #9
- [ ] Final score ≥95/100
- [ ] CEO approve + merge

**Sprint-close (after PR #2 merged):**
- [ ] HC re-run verification: unknown <5% confirmed, API Catalog placeholder visible, Executive health bar shows real coverage %
- [ ] Tag `v2.0.1` annotated
- [ ] GitHub release with bug-fixes notes
- [ ] Notify HC customer via release link
- [ ] Update `BRIEF.md` + `project/board.html`

---

## 6. Risks & Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| R1 | Classifier fix regresses HC layer distribution (over-classifies known-good nodes) | Medium | High | Snapshot current HC scan BEFORE change; diff layer counts after; regression test on HC-slice fixture |
| R2 | Coverage file format varies (pytest-cov JSON vs coverage.xml) | Medium | Medium | Support both formats; graceful fallback to proxy when neither found |
| R3 | `generate --diff` flag clashes with existing `diff` subcommand semantics | Low | Medium | Reuse internal diff engine; document flag vs subcommand relationship in help text |
| R4 | Day 2 scope overflow delays release | Medium | Low | Slip buffer: defer POST-CM-S3-01 if needed; POST-CM-S3-04 is higher priority |
| R5 | HC customer already using v2.0.0 and hits unknown-layer issue again before fix | Low | Medium | PM: send interim workaround note to HC (exclude tools/ in yaml) while hotfix ships |
| R6 | Review gate <95 due to test coverage gap on new classifier | Low | Medium | Write regression tests FIRST (TDD), then implement |

---

## 7. HC Feedback Integration Note

**Critical customer signal:** HC full-repo scan reports unknown layer = 173/1565 nodes (~11%). Target is **<5%** after POST-CM-S3-02.

**Verification plan:**
1. Before Day 1 AM: PM captures baseline — run `codebase-map summary` on HC repo, record layer distribution JSON to `docs/hotfix-baselines/hc_layer_baseline_2026-04-08.json`
2. After POST-CM-S3-02 merge: Tech Lead re-runs on same HC commit, records to `hc_layer_postfix_2026-04-08.json`
3. Tester compares + confirms <5% unknown ratio before closing HOTFIX-AC-03
4. Include before/after layer counts in v2.0.1 release notes for customer transparency

**If <5% target missed:** escalate to CEO before tagging release — do not ship v2.0.1 with partial fix.

---

## 8. References

- `project/POST-CM-S3-HOTFIX-PLAN.md` — original hotfix plan
- `docs/reviews/FullTest_PreDelivery_2026-04-07.md` §8 — deferred items source
- `docs/ONBOARDING.md` — customer onboarding (already shipped)
- `CLAUDE.md` — project rules (no push to main, PR per Day, lint gate, Rule #6 2-tier review)
- Issues: #32 (POST-CM-S3-01) · #33 (POST-CM-S3-02) · #34 (POST-CM-S3-03) · #35 (POST-CM-S3-04)

---

*CM-HOTFIX v2.0.1 Task Board · Created by PM · 2026-04-08 · Awaiting CEO kickoff approval*
