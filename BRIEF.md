# BRIEF.md — Codebase Map Session Brief
> **Đọc file này ĐẦU TIÊN mỗi session. Cập nhật cuối mỗi session.**
> Version: 1.2 | Cập nhật: 06/04/2026

---

## 🎯 TRẠNG THÁI HIỆN TẠI

| Field | Value |
|-------|-------|
| **Version hiện tại** | v1.2 ✅ → v2.0 in planning |
| **Sprint hiện tại** | CM-S3 (v2.0) — ⏳ Kickoff (design + task board phase) |
| **Sprint trước** | CM-S2 (v1.2) — ✅ DONE (18/18 SP, 11/11 tasks, 5 feature PRs) |
| **Sprint trước nữa** | CM-S1 (v1.1) — ✅ DONE (15/15 SP, 10/10 tasks) |
| **Repo** | https://github.com/hypercommerce-vn/codebase-map |
| **Parent HC repo** | https://github.com/hypercommerce-vn/hypercommercesystem |
| **HC config** | `codebase-map.yaml` trong HC repo root |

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

---

## 🔥 VẤN ĐỀ ĐANG MỞ

| Vấn đề | Priority |
|--------|----------|
| CM-S3 design HTML (8 mockup sections) — Designer drafting | 🔴 Blocker Day 1 |
| CM-S3 task board + Day plan | 🔴 Blocker Day 1 |
| CEO approve CM-S3 design + task board | 🟡 Next |
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

---

## 🚨 CRITICAL RULES (LUÔN NHỚ)

1. **KHÔNG push thẳng main** — PR required
2. **Mỗi Day → 1 PR → /review-gate → CEO approve**
3. **No Design = No Implementation**
4. **Lint gate:** `black + isort + flake8` trước commit
5. **Comment:** `# HC-AI | ticket: FDD-TOOL-CODEMAP`
6. **2-tier Review Gate (từ CM-S3):** `/review-gate --local` TRƯỚC `git push` (Pre-flight) → `/review-gate PR #XX` SAU khi push + CI pass (Remote Full) → CEO review. Local block nếu CTO local < 80 hoặc Dim C < 20/25.

---

*BRIEF.md v1.5 — Codebase Map | 07/04/2026 | CM-S2 Sprint COMPLETE 🎉 · CM-S3 Kickoff ⏳*
