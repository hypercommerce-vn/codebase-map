# BRIEF.md — Codebase Map Session Brief
> **Đọc file này ĐẦU TIÊN mỗi session. Cập nhật cuối mỗi session.**
> Version: 2.8 | Cập nhật: 22/04/2026 (Day 9 — BM25 spike + coverage 94%)

---

## 🎯 TRẠNG THÁI HIỆN TẠI

**KMP Sprint M1 ACTIVE · Day 9 · 26/26 SP · M0 COMPLETE (8/8 SP, CTO 20/20) · v2.0.1 shipped**

M1 Day 9 complete: MEM-M1-12 (BM25 Vietnamese spike: 100% recall, target ≥75%) + MEM-M1-13 (coverage: 94%, target ≥80%). 434 tests green. Only MEM-M1-14 (CTO dogfood) remains for D10.

### 🗓️ Session timeline (08-09/04/2026)

**08/04/2026:**
1. HC customer delivery verification — YAML tuning, unknown layer 11.1% → 0%
2. Hotfix v2.0.1 full lifecycle — Day 1 PR #38 + Day 2 PR #39 → tag v2.0.1 → GitHub Release
3. KMP Phase 2 docs PR #40 + designs PR #42 (revised, 82/100 combined) merged
4. KMP Sprint M0 kickoff PR #43 merged
5. KMP M0 Day 1 PR #44 (99/100 SHIPIT) + Day 2 PR #45 (99/100 SHIPIT) merged

**09/04/2026:**
6. KMP M0 Day 3 PR #47 (100/100 SHIPIT) — import-linter + Hello vertical — CEO merged

### 📦 PRs merged (13 PRs across 3 sessions)

| PR | Title / Scope | Score | Status |
|----|---------------|-------|--------|
| #37 | chore: hotfix v2.0.1 kickoff + task board | — | ✅ merged |
| #38 | fix: hotfix v2.0.1 Day 1 — classifier + API empty state | 90.20 | ✅ merged |
| #39 | fix: hotfix v2.0.1 Day 2 — coverage hook + diff + polish | 96.60 | ✅ merged |
| #40 | docs(kmp): Phase 2 specs | — | ✅ merged |
| #41 | chore(hotfix): close v2.0.1 sprint | — | ✅ merged |
| #42 | design(kmp): Phase 2 design mocks (v2 + M0) | 82 | ✅ merged |
| #43 | chore(kmp): kickoff Sprint M0 | — | ✅ merged |
| #44 | feat(kmp): M0 Day 1 — core skeleton + Pattern/Evidence/BaseVault | 99 | ✅ merged |
| #45 | feat(kmp): M0 Day 2 — BaseLearner + BaseParser + LearnerRuntime | 99 | ✅ merged |
| #46 | chore(state): session checkpoint 08/04 | — | 🟡 pending |
| #47 | feat(kmp): M0 Day 3 — import-linter CI + Hello vertical | 100 | ✅ merged |
| #49 | chore(docs): update install URLs + auth guide for private repo | — | ✅ merged |
| #51 | feat(kmp): M0 Day 4 — Hello finish + vault-format-spec | 92 | ✅ merged |
| #52 | chore(project): board separation KMP/CM | — | ✅ merged |
| #53 | feat(kmp): M0 Day 5 — LICENSE dual MIT/PRO + CTO sign-off 20/20 | — | ✅ merged |
| #54 | feat(kmp): M1 Day 1 — CodebaseVault + PythonASTParser + M1 design | 97 | ✅ merged |
| #55 | feat(kmp): M1 Day 2 — PythonASTParser finish + Snapshots enhanced | 98 | ✅ merged |
| #56 | feat(kmp): M1 Day 3 — SQLite extension + NamingLearner start | 95 | ✅ merged |
| #57 | feat(kmp): M1 Day 3.5 — NamingLearner runtime E2E | — | ✅ merged |
| #58 | feat(kmp): M1 Day 4 — NamingLearner vault-query + LayerLearner | 96 | ✅ merged |
| #59 | feat(kmp): M1 Day 5 — GitOwnershipLearner + vault ownership | 97 | ✅ merged |
| #60 | feat(kmp): M1 Day 6 — patterns.md generator + bootstrap orchestrator | 97 | ✅ merged |
| #61 | feat(kmp): M1 Day 7 — Quick Wins generator (10 insights 5+3+2) | 98 | ✅ merged |
| #62 | feat(kmp): M1 Day 8 — CLI summary output with rich colors | 97 | ✅ merged |
| #63 | fix(kmp): 3 P0/P1 bugs — duplicate patterns, git author, path mixing | — | ✅ merged |

### ▶️ Next actions

- **M1 Day 10 next** — MEM-M1-14 (CTO dogfood ≥15/20) → final PR → CEO approve
- M1 Design: `design-preview/kmp-M1-design.html` (CEO approved 10/04/2026)
- M1 Task board: `project/CM-MEM-M1-TASK-BOARD.md`

| Field | Value |
|-------|-------|
| **Version hiện tại** | v2.0.1 ✅ SHIPPED (08/04/2026) — tag `v2.0.1` pushed, GitHub release published |
| **Sprint hiện tại** | 🔥 **KMP CM-MEM-M0** — ACTIVE, Day 1 ready (kickoff plan published 09/04/2026) |
| **KMP Sprint M0** | 8 tasks · 8 SP · 5 Days (D1=09/04 → D5=15/04) · awaiting CEO "Approve Day 1 start" |
| **Sprint vừa xong** | CM-HOTFIX v2.0.1 — ✅ CLOSED · PR #38 + PR #39 merged · tag v2.0.1 pushed |
| **Designs approved** | `design-preview/kmp-v2-design.html` + `kmp-M0-design.html` (PR #42 merged 09/04) |
| **Sprint trước** | CM-S3 (v2.0) — ✅ DELIVERED (22/22 SP, 8/8 tasks, v2.0.0 released) |
| **Sprint trước nữa** | CM-S2 (v1.2) — ✅ DONE (18/18 SP, 11/11 tasks, 5 feature PRs) |
| **Sprint đầu tiên** | CM-S1 (v1.1) — ✅ DONE (15/15 SP, 10/10 tasks) |
| **Repo** | https://github.com/hypercommerce-vn/codebase-map **(PRIVATE)** |
| **Parent HC repo** | https://github.com/hypercommerce-vn/hypercommercesystem |
| **HC config** | `codebase-map.yaml` trong HC repo root |

---

## 🔥 KMP SPRINT M0 — ACTIVE (kickoff 09/04/2026)

**Goal:** Build KMP Core skeleton (abstract base + runtime + CI gate) + Hello vertical (≤50 LOC reference) để chứng minh abstraction stable trước M1 (Codebase Vault).

**Scope:** 8 tasks · 8 SP · 5 Days · 5 PRs (1 PR / Day mandatory)

| Day | Date | Tasks | PR |
|-----|------|-------|-----|
| D1 | 09/04 (T4) | KMP-M0-01 (skeleton) + KMP-M0-02 start (abstract base) | PR #1 |
| D2 | 10/04 (T5) | KMP-M0-02 finish + KMP-M0-03 (runtime orchestrator) | PR #2 |
| D3 | 13/04 (T2) | KMP-M0-04 (import-linter CI) + KMP-M0-05 start (hello vertical) | PR #3 |
| D4 | 14/04 (T3) | KMP-M0-05 finish + KMP-M0-07 (vault-format-spec.md) | PR #4 |
| D5 | 15/04 (T4) | KMP-M0-08 (LICENSE) + KMP-M0-06 (CTO sign-off) | PR #5 |

**Owner:** @TechLead · **Reviewers:** @CTO + @Tester + @Designer (D4 spec) · **Branch base:** `main`
**Task board:** `project/CM-MEM-M0-TASK-BOARD.md`
**Day 1 checklist:** `project/KMP-M0-DAY1-CHECKLIST.md`
**Specs:** `specs/kmp/architecture.md` · `specs/kmp/fdd-v2.md` · `specs/kmp/user-stories-m0-m1.md`
**Designs:** `design-preview/kmp-v2-design.html` · `design-preview/kmp-M0-design.html`

**Dependencies:** ✅ none — v2.0.1 shipped, designs approved, specs locked.
**Day 1 ready state:** ✅ branch base clean · ✅ specs locked · ✅ designs available · ⏳ awaiting CEO "Approve Day 1 start"

---

## ✅ ĐÃ HOÀN THÀNH

### v1.0 — Core Foundation
- Python AST Parser: functions, classes, methods, routes, Celery tasks
- Graph models: Node, Edge, Graph dataclasses
- Graph Builder + Query Engine (search, impact, dependency)
- JSON Exporter + HTML Exporter (D3.js interactive)
- CLI: generate, query, impact, search, summary
- YAML config (standalone, any project)
- **HC scan: 1,386 nodes · 8,285 edges · 7 domains**

### v1.1 — CM-S1 Sprint ✅ COMPLETE (06/04/2026)

| Day | Tasks | SP | PR | Review Gate | Status |
|-----|-------|----|-----|-------------|--------|
| Day 1 | CM-S1-03 (fix unknown) + CM-S1-04 (bundle D3) | 2 | Retroactive | CTO 100/100 SHIPIT | ✅ Done |
| Day 2 | CM-S1-01 (sidebar tree) + CM-S1-09 (empty state) + CM-S1-10 (top bar) | 5 | PR #2 | CTO 93/100 Designer 99/100 → 95.4% SHIPIT | ✅ Done |
| Day 3 | CM-S1-02 (domain clustering) + CI Telegram notify | 3 | PR #3 | CI pass + CEO approved | ✅ Done |
| Day 4 | CM-S1-06 (minimap) + CM-S1-07 (toolbar) + CM-S1-08 (legend) | 4 | PR #4 | CTO 93/100 Designer 99/100 → 95.4% SHIPIT | ✅ Done |
| Day 5 | CM-S1-05 (CI auto-generate + verify HTML) | 1 | PR #5 | CTO 100/100 SHIPIT | ✅ Done |
| **Total** | **10 tasks** | **15/15 SP** | **5 PRs merged** | **All passed** | **✅ Sprint Done** |

**Key deliverables v1.1:**
- Progressive disclosure sidebar — domain → class → method tree
- Domain clustering — D3 forceCluster + background colors
- Minimap — SVG overview + viewport indicator
- Toolbar — 8 buttons (zoom, fit, labels, edges, clusters, export PNG, fullscreen)
- Dual legend — node type (fill) + edge type (line style)
- Top bar — project name, stats badges, timestamp
- Empty state — search no results message
- D3.js bundled — 280KB inline, fully offline
- Unknown layer < 1% (was 32%)
- CI pipeline — 4 jobs: lint → test (3.10-3.12) → generate (JSON+HTML verify) → notify (Telegram)
- Telegram bot — @CodebaseMap_Project_bot notifies CEO on CI pass/fail

### Repo Migration (CEO Decision 05/04/2026)
- Tách từ `hypercommercesystem/tools/codebase-map/` → repo riêng
- HC repo PR #85 merged (xóa tool code)
- HC repo PR #82 merged (v1.0 original), PR #84 closed (superseded)
- HC repo chỉ giữ `codebase-map.yaml` config

---

### v1.2 — CM-S2 Sprint ✅ COMPLETE (07/04/2026)

| Day | Tasks | SP | PR | Review Gate | Status |
|-----|-------|----|-----|-------------|--------|
| Day 1 | CM-S2-01 (git diff) | 3 | PR #9 | CTO 99/100 SHIPIT | ✅ Done |
| Day 2 | CM-S2-02 (incremental cache) | 3 | PR #11 | CTO 100/100 SHIPIT | ✅ Done |
| Day 3 | CM-S2-06 (edge resolution) + CM-S2-03 (coverage) | 4 | PR #13 | CTO 99/100 SHIPIT | ✅ Done |
| Day 4 | CM-S2-07 (API catalog) + CM-S2-04 (/implement) + CM-S2-05 (/review-gate) | 4 | PR #15 | CTO 99/100 SHIPIT | ✅ Done |
| Day 5 | CM-S2-08 (FDD) + CM-S2-09 (PR bot) + CM-S2-10 (metric) + CM-S2-11 (staleness) | 4 | PR #17 | CEO merged | ✅ Done |
| **Total** | **11 tasks** | **18/18 SP** | **5 feature + 4 chore PRs** | **All passed** | **✅ Sprint Done** |

**Key deliverables v1.2:**
- Git diff integration — `codebase-map diff HEAD~1` changed + impacted nodes
- Incremental build cache — SHA-256 per-file, 80%+ faster rebuilds
- Edge resolution — `self.attr.method()` chain via `__init__` type hints
- Test coverage overlay — pytest-cov JSON mapped to node line ranges
- API catalog — route extraction, HTTP method + path + auth detection
- Workflow integration — `/implement` + `/review-gate` auto-query impact
- FDD spec linking — `# FDD: FDD-XXX` comment parsing → `node.metadata.fdd`
- PR Impact Comment Bot — auto-post markdown risk analysis to every PR
- Sprint metric store — `.codebase-map-cache/pr_metrics.json`
- Staleness alert — `check-staleness --notify` + Telegram webhook
- 2-tier Review Gate workflow — local pre-flight + remote full

**Design CM-S2 approved** — `design-preview/codebase-map-CM-S2-design.html` (1820 lines, 11 sections).

---

## ✅ Hotfix Sprint v2.0.1 — CLOSED (08/04/2026)

**Result:** Both PRs merged, tag pushed, GitHub release published, HC verified.

| Day | Tasks | PR | Review Gate | Status |
|-----|-------|----|-------------|--------|
| Day 1 | POST-CM-S3-02 (classifier) + POST-CM-S3-03 (API empty state) | [#38](https://github.com/hypercommerce-vn/codebase-map/pull/38) | 90.20 SHIPIT+NOTE | ✅ MERGED |
| Day 2 | POST-CM-S3-01 (coverage hook) + POST-CM-S3-04 (`generate --diff`) + POLISH-01/02/03 | [#39](https://github.com/hypercommerce-vn/codebase-map/pull/39) | 96.60 SHIPIT | ✅ MERGED |

**Tag:** `v2.0.1` · **Release:** https://github.com/hypercommerce-vn/codebase-map/releases/tag/v2.0.1
**HC verified:** unknown layer 173/1565 (11.1%) → 0/1565 (0.00%) ✅
**Total:** 8 items (4 POST + 3 POLISH + release) · 3 SP · 2 Days · 2 PRs

---

## 🗄️ Hotfix Sprint v2.0.1 — Original scope (archive)

**Goal:** Ship `v2.0.1` hotfix release — fix 4 post-delivery polish items + 3 review-gate polish. Priority: real coverage hook + unified `generate --diff` workflow.

**Scope (3 SP + 3 polish · 2 Days · 2 PRs):**
- **Day 1 → PR #38 ✅ MERGED:** POST-CM-S3-02 (unknown layer classifier, 0.5 SP) + POST-CM-S3-03 (API Catalog empty state, 0.5 SP) — Final 90.20 SHIPIT+NOTE
- **Day 2 → PR #39 🟡 ACTIVE:** POST-CM-S3-01 (Executive real coverage hook, 1 SP) + POST-CM-S3-04 (`generate --diff` flag, 1 SP) + POLISH-01/02/03 bundled → tag v2.0.1 → release

**Task board:** `project/CM-HOTFIX-V2.0.1-TASK-BOARD.md`
**Source backlog:** `project/POST-CM-S3-HOTFIX-PLAN.md` (issues #32–#35)
**Day 1 review:** `docs/reviews/ReviewGate_PR38_Round1_2026-04-08.md` (Final 90.20)

**Day 1 results (2026-04-08) — ✅ DONE:**
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/38 (MERGED)
- HC unknown: 173/1565 (11.1%) → 0/1565 (0.00%) ✅ PASS <5% gate
- Self-build: 154 nodes, 0 unknown ✅
- Files: TS + Py classifier, HTML exporter API catalog, baseline doc
- Review gate Final: 90.20 SHIPIT+NOTE → 3 polish items carried into Day 2

**Day 2 scope (2026-04-08) — 🟡 ACTIVE:**
- POST-CM-S3-01: Real coverage hooked into Executive health bar (aggregates `metadata.coverage.percent` per domain; falls back to layer-diversity proxy when no coverage data)
- POST-CM-S3-04: `generate --diff <ref>` flag bakes `pr_diff.json` in one command
- POLISH-01: TS parser hooks rule — explicit parentheses for `and`/`or` precedence
- POLISH-02: API domain header HTML-escaped via new `htmlEscape()` helper
- POLISH-03: `aria-hidden="true"` on API Catalog empty-state emoji icon
- HC re-verify: 1565 nodes · 0 unknown · no regression
- Lint gate: PASS (black + isort + flake8)
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/39
- Next: review-gate Mode 2 → CEO approve → merge → tag v2.0.1 → release

---

## 🚚 v2.0.0 DELIVERED (07/04/2026)

**Latest:** PR #36 merged (onboarding 1-pager + FullTest report + hotfix plan). CEO đã được hướng dẫn cách dùng tool cho HC repo (8-bước cheatsheet). Hotfix sprint v2.0.1 plan đã sẵn sàng.

**Hotfix backlog (issues #32–#35):** POST-CM-S3-01 coverage hook · -02 self-build fix · -03 API empty state · -04 `generate --diff` flag. Plan: `project/POST-CM-S3-HOTFIX-PLAN.md`.

**Customer doc:** `docs/ONBOARDING.md` (install · YAML · CLI · CI · mobile).
**Release:** https://github.com/hypercommerce-vn/codebase-map/releases/tag/v2.0.0

---

## ✅ CM-S3 (v2.0) Sprint COMPLETE 🎉 — 22/22 SP · 8/8 tasks

| Day | Tasks | SP | PR | Status |
|-----|-------|----|----|--------|
| Day 1 | CM-S3-06 TS parser | 5 | #24 ✅ merged | Done |
| Day 2 | CM-S3-01 Multi-view + CM-S3-05 Breadcrumb | 5 | #25 ✅ merged | Done |
| — | Board refs table (Rule #9) | — | #26 ✅ merged | Done |
| — | Post-CM-S3 Minor Backlog | — | #27 ✅ merged | Done |
| Day 3 | CM-S3-02 Executive view + CM-S3-07 Detail Panel v2 | 5 | #28 ✅ merged | Done (95.6/100) |
| Day 4 | CM-S3-03 PR Diff + CM-S3-04 Business Flow | 6 | #29 ✅ merged | Done (95.0/100) |
| Day 5 | CM-S3-08 Responsive sidebar (sprint close) | 1 | #30 ✅ merged | Done (96.6/100) |

**CM-S3 COMPLETE — v2.0 ships:** TS parser · Multi-view · Executive · Detail Panel v2 · PR Diff · Business Flow · Breadcrumb · Responsive.
**5 feature PRs merged:** #24 #25 #28 #29 #30 (+ chore #26 #27).
**Avg final score:** ~95.7/100.

### Last Review Gate — PR #28 Round 1 (Mode 2 Remote Full)
- Tester ✅ PASS · CTO 96/100 · Designer 95/100 (mcp__Claude_Preview verified)
- Impact 🟢 Low (3 changed → 5 zone)
- Final **95.6/100 → SHIPIT + NOTE**
- Report: `docs/reviews/ReviewGate_PR28_Round1_2026-04-07.md`
- Notes: health bar = layer-diversity proxy (real coverage deferred POST-CM-S3); Detail Panel v2 graceful-degrade missing fields.

---

## 📋 QUYẾT ĐỊNH QUAN TRỌNG

| Ngày | Quyết định | Người |
|------|-----------|-------|
| 05/04/2026 | **Tách repo** — codebase-map là standalone tool, không commit vào HC repo | CEO |
| 05/04/2026 | **Design v2.0 approved** — `codebase-map-v2-design.html` | CEO |
| 05/04/2026 | **Design CM-S1 approved** — `codebase-map-CM-S1-design.html` | CEO |
| 05/04/2026 | **FDD spec approved** — 3 sprints, 29 tasks, 55 SP | CEO |
| 05/04/2026 | **Quy trình Day** — Implement → Lint → PR → CI → /review-gate 3 tầng → CEO | CEO |
| 05/04/2026 | **Retroactive approve Day 1** — CM-S1 Day 1 đã review ở HC repo cũ, coi như pass | CEO |
| 06/04/2026 | **AI Infrastructure Migration** — 7 agents, 5 commands, settings, 7 memory files | CEO |
| 06/04/2026 | **Telegram Bot setup** — @CodebaseMap_Project_bot cho CI notify | CEO |
| 06/04/2026 | **CM-S1 Sprint COMPLETE** — All 5 PRs merged, 15/15 SP, all review gates passed | CEO |
| 06/04/2026 | **Board sync rule** — Rule #8: update board.html khi update BRIEF.md/task board | CEO |
| 06/04/2026 | **CM-S2 Design approved** — 11 task mockups, PR #8 merged | CEO |
| 06/04/2026 | **CM-S2 Sprint START** — Day 1: Git diff integration (CM-S2-01), PR #9 merged | CEO |
| 06/04/2026 | **CM-S2 Day 2 Done** — Incremental cache (CM-S2-02), 80%+ faster builds, PR #11 merged, CTO 100/100 | CEO |
| 06/04/2026 | **CM-S2 Day 3 Done** — Edge resolution (CM-S2-06) + Coverage overlay (CM-S2-03), PR #13 merged, CTO 99/100 | CEO |
| 07/04/2026 | **CM-S2 Day 4 Done** — API Catalog (CM-S2-07) + /implement (CM-S2-04) + /review-gate (CM-S2-05), PR #15 merged, CTO 99/100 | CEO |
| 07/04/2026 | **2-tier Review Gate approved** — `/review-gate --local` Pre-flight TRƯỚC push + Remote Full SAU push. Áp dụng từ CM-S3. Mục tiêu giảm force-push + tiết kiệm CI/CEO review time | CEO |
| 07/04/2026 | **CM-S2 Sprint COMPLETE** 🎉 — 18/18 SP, 11/11 tasks, 5 feature PRs merged (#9, #11, #13, #15, #17) + bot fix #19 + 2-tier workflow #20. v1.2 shipped | CEO |
| 07/04/2026 | **CM-S3 Kickoff** — 3 agents (PM + CTO + Designer) phân công tạo design + task board trước khi code | CEO |
| 07/04/2026 | **CM-S3 Day 1 Done** — CM-S3-06 TS parser, PR #24 merged | CEO |
| 07/04/2026 | **CM-S3 Day 2 Done** — CM-S3-01 Multi-view + CM-S3-05 Breadcrumb, PR #25 merged + PR #26 refs table + PR #27 minor backlog | CEO |
| 07/04/2026 | **Rule #9** — Mọi review report phải cite tài liệu tham chiếu per dimension | CEO |
| 07/04/2026 | **CM-S3 Day 3 Done** — PR #28 merged | CEO |
| 07/04/2026 | **CM-S3 Day 4 Done** — CM-S3-03 PR Diff + CM-S3-04 Business Flow, PR #29 merged, Mode 2: 95.0/100 | CEO |
| 07/04/2026 | **CM-S3 Day 5 Done** — PR #30 merged | CEO |
| 07/04/2026 | **CM-S3 Sprint COMPLETE 🎉** — 22/22 SP · 8/8 tasks · v2.0 shipped | CEO |
| 07/04/2026 | **FullTest Pre-Delivery PASS** — 6 agents (PM/CTO/BA/Tester/Designer/PO), GO FOR DELIVERY, 0 blockers, 4 minor items deferred | PM |
| 07/04/2026 | **v2.0.0 Released** — Tag pushed, GitHub release published, customer onboarding 1-pager `docs/ONBOARDING.md` | CEO |
| 07/04/2026 | **POST-CM-S3 Hotfix Sprint scheduled** — 4 issues #32-#35, ~3 SP, target v2.0.1 | PM |
| 08/04/2026 | **Hotfix v2.0.1 Sprint kickoff plan** — task board `project/CM-HOTFIX-V2.0.1-TASK-BOARD.md` drafted, Day 1/Day 2 split, HC <5% unknown target, awaiting CEO approve Day 1 start | PM |
| 08/04/2026 | **Hotfix Day 1 MERGED** — PR #38 merged, HC unknown 173→0, review Final 90.20 SHIPIT+NOTE. 3 polish items (TS hooks precedence, API domain escape, empty-state aria-hidden) carried into Day 2 | CEO |
| 08/04/2026 | **Hotfix Day 2 KICKOFF** — POST-CM-S3-01 coverage hook + POST-CM-S3-04 `generate --diff` flag + POLISH-01/02/03 bundled, branch `hotfix/v2.0.1-day2`, PR #2 in-progress | PM |
| 08/04/2026 | **Hotfix Day 2 MERGED** — PR #39 merged, review gate Final 96.60 SHIPIT | CEO |
| 08/04/2026 | **v2.0.1 SHIPPED** — tag `v2.0.1` pushed, GitHub release published, KMP M0 unblocked | CEO |
| 08/04/2026 | **KMP Phase 2 designs approved** — PR #42 merged (kmp-v2-design.html + kmp-M0-design.html), combined 82/100 revised v2 | CEO |
| 08/04/2026 | **KMP Sprint M0 kickoff** — PR #43 merged (task board 8 SP, Day 1 checklist, 5-day plan) | CEO |
| 08/04/2026 | **KMP M0 Day 1 MERGED** — PR #44: skeleton + Pattern/Evidence/BaseVault (3 SP, 99/100 SHIPIT) | CEO |
| 08/04/2026 | **KMP M0 Day 2 MERGED** — PR #45: BaseLearner + BaseParser + LearnerRuntime + datetime polish (2 SP, 99/100 SHIPIT). Sprint 5/8 SP (62%) | CEO |
| 09/04/2026 | **KMP M0 Day 3 MERGED** — PR #47: import-linter CI gate + HelloLearner + HelloParser (1.5 SP, 100/100 SHIPIT). Sprint 6.5/8 SP (81%) | CEO |
| 09/04/2026 | **Repo PRIVATE** — chuyển public → private, PR #49 cập nhật SSH URLs + auth guide + ONBOARDING.md | CEO |
| 10/04/2026 | **KMP M0 COMPLETE** — 8/8 SP, 5 PRs, CTO sign-off 20/20 PASS. PR #53 merged | CEO |
| 10/04/2026 | **KMP M1 Design approved** — PO+CTO+Designer 3-way meeting, 7 screens, 8 decisions. `kmp-M1-design.html` | CEO |
| 10/04/2026 | **KMP M1 Sprint kickoff** — 14 tasks, 26 SP, 10 Days (10/04 → 23/04). Day 1: CodebaseVault + PythonASTParser | CEO |
| 10/04/2026 | **CBM Dual-Snapshot APPROVED** — Proposal + CTO Review + CI Integration. 3 modifications: Phase 3→KMP, rename=signature matching, CI=artifact. Scope: 19 SP / 2 phases / 3 tuần | CEO |
| 10/04/2026 | **CI Phương án B chốt** — GitHub Actions Artifact + Auto PR Comment. Zero commit noise. 3-day warn Telegram, 7-day block merge | CEO |
| 10/04/2026 | **CBM ranh giới** — codebase-map = stateless graph tool (free). KMP = stateful knowledge engine (freemium). Lifecycle commands ở KMP M3 | CEO + CTO |
| 11/04/2026 | **CBM Sprint plans + Design + Specs hoàn tất** — 7 files trong `docs/cbm-dual-snapshot/`, sẵn sàng implement khi CEO ra lệnh | PM + CTO |

---

## 🗺️ CBM DUAL-SNAPSHOT — READY (10/04/2026)

**Goal:** Nâng codebase-map từ snapshot tool → lifecycle tool. Before vs After function-level impact analysis.

**Scope:** Phase 1 (v2.1, 7 SP, 1 tuần) + Phase 2 (v2.2, 12 SP, 2 tuần) = **19 SP / 3 tuần**
**Phase 3 (Lifecycle):** DEFERRED sang KMP M3

**Start condition:** KMP M1 done + CEO duyệt plan
**Branch:** `feat/cbm-phase1-metadata` → `feat/cbm-phase2-diff-engine`

**Deliverables (trong `docs/cbm-dual-snapshot/`):**

| File | Nội dung |
|------|---------|
| `Proposal_Dual_Snapshot_CBM.md` | Proposal gốc (v1.1) + CEO decisions section 14 |
| `CTO_Review_Dual_Snapshot.md` | CTO review 48/60, 3 modifications, 15 tasks chi tiết |
| `CTO_CI_Integration_Proposal.md` | CI deep-dive, Phương án B, 3 YAML templates, CEO decisions |
| `CBM-PHASE1-TASK-BOARD.md` | Sprint Phase 1: 7 tasks, 7 SP, daily plan, DoD |
| `CBM-PHASE2-TASK-BOARD.md` | Sprint Phase 2: 8 tasks + CI, 12 SP, daily plan 2 tuần |
| `CBM-Dual-Snapshot-Design.html` | Design preview 6 tabs (PR comment, CLI diff, snapshots, test plan, Telegram, JSON) |
| `CBM-Implementation-Specs.md` | Technical specs: metadata schema, SnapshotManager, SnapshotDiff, formatters, tests |

**CEO Decisions (tóm tắt):**
- Phase 3 → KMP M3 (giữ codebase-map stateless)
- Rename = signature matching (name + params + return_type)
- CI = GitHub Actions artifact + auto PR comment (zero commit)
- PR comment = summary visible + full diff `<details>` collapsible
- Staleness = 3 ngày warn Telegram, 7 ngày block merge
- Pricing = 100% free (paid ở KMP)

---

## 🔥 VẤN ĐỀ ĐANG MỞ

| Vấn đề | Priority |
|--------|----------|
| KMP M1 Day 2 — Parser finish + Snapshots (4 SP) | 🔥 Active |
| CBM Dual-Snapshot — READY, chờ CEO ra lệnh start (sau KMP M1) | 🟡 Ready |
| Wiki board ở HC repo cần update link repo mới | 🟢 Low |

---

## 📁 FILES QUAN TRỌNG

| File | Nội dung |
|------|----------|
| `CLAUDE.md` | Rules + structure + development guide |
| `specs/spec.md` | FDD spec đầy đủ 3 sprints |
| `project/CM-S1-TASK-BOARD.md` | Task board sprint 1 |
| `project/CM-S2-TASK-BOARD.md` | Task board sprint 2 |
| `project/board.html` | Project Board HTML (sync mỗi update) |
| `design-preview/codebase-map-v2-design.html` | Design tổng thể v2.0 |
| `design-preview/codebase-map-CM-S1-design.html` | Design chi tiết CM-S1 |
| `design-preview/codebase-map-CM-S2-design.html` | Design chi tiết CM-S2 |
| `agents/README.md` | 7 AI agents overview |
| `.claude/commands/` | 5 slash commands (review-gate, implement, review, ci-watch, security-audit) |
| `.claude/settings.json` | Security deny/allow rules |
| `docs/cbm-dual-snapshot/Proposal_Dual_Snapshot_CBM.md` | CBM Dual-Snapshot proposal v1.1 + CEO decisions |
| `docs/cbm-dual-snapshot/CTO_Review_Dual_Snapshot.md` | CTO review + effort re-estimate |
| `docs/cbm-dual-snapshot/CTO_CI_Integration_Proposal.md` | CI Phương án B + 3 YAML templates |
| `docs/cbm-dual-snapshot/CBM-PHASE1-TASK-BOARD.md` | Sprint Phase 1 task board (v2.1, 7 SP) |
| `docs/cbm-dual-snapshot/CBM-PHASE2-TASK-BOARD.md` | Sprint Phase 2 task board (v2.2, 12 SP) |
| `docs/cbm-dual-snapshot/CBM-Dual-Snapshot-Design.html` | Design preview interactive (6 tabs) |
| `docs/cbm-dual-snapshot/CBM-Implementation-Specs.md` | Implementation specs kỹ thuật |

---

## 🚨 CRITICAL RULES (LUÔN NHỚ)

1. **KHÔNG push thẳng main** — PR required
2. **Mỗi Day → 1 PR → /review-gate → CEO approve**
3. **No Design = No Implementation**
4. **Lint gate:** `black + isort + flake8` trước commit
5. **Comment:** `# HC-AI | ticket: FDD-TOOL-CODEMAP`
6. **2-tier Review Gate (từ CM-S3):** `/review-gate --local` TRƯỚC `git push` (Pre-flight) → `/review-gate PR #XX` SAU khi push + CI pass (Remote Full) → CEO review. Local block nếu CTO local < 80 hoặc Dim C < 20/25.

---

*BRIEF.md v2.4 — Codebase Map | 11/04/2026 | Repo PRIVATE · KMP M1 ACTIVE · M0 COMPLETE · CBM Dual-Snapshot READY*
