# BRIEF.md — Codebase Map Session Brief
> **Đọc file này ĐẦU TIÊN mỗi session. Cập nhật cuối mỗi session.**
> Version: 1.1 | Cập nhật: 06/04/2026

---

## 🎯 TRẠNG THÁI HIỆN TẠI

| Field | Value |
|-------|-------|
| **Version hiện tại** | v1.1 → v1.2 in progress |
| **Sprint hiện tại** | CM-S2 (v1.2) — **🔄 Day 1** (3/18 SP, 1/11 tasks) |
| **Sprint trước** | CM-S1 (v1.1) — ✅ DONE (15/15 SP, 10/10 tasks) |
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

## 🔄 ĐANG LÀM — CM-S2 (v1.2) Sprint

| Day | Tasks | SP | PR | Status |
|-----|-------|----|-----|--------|
| Day 1 | CM-S2-01 (git diff) | 3 | PR #9 | 🔄 Review (CTO 99/100) |
| Day 2 | CM-S2-02 (incremental cache) | 3 | — | 📋 Todo |
| Day 3 | CM-S2-06 (edge resolution) + CM-S2-03 (coverage) | 4 | — | 📋 Todo |
| Day 4 | CM-S2-07 (API catalog) + CM-S2-04 + CM-S2-05 | 4 | — | 📋 Todo |
| Day 5 | CM-S2-08 + CM-S2-09 + CM-S2-10 + CM-S2-11 | 4 | — | 📋 Todo |
| **Total** | **11 tasks** | **18 SP** | | **🔄 Day 1** |

**Design CM-S2 approved** — `design-preview/codebase-map-CM-S2-design.html` (1820 lines, 11 sections).

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
| 06/04/2026 | **CM-S2 Design approved** — 11 task mockups, PR #8 | CEO |
| 06/04/2026 | **CM-S2 Sprint START** — Day 1: Git diff integration (CM-S2-01) | CEO |

---

## 🔥 VẤN ĐỀ ĐANG MỞ

| Vấn đề | Priority |
|--------|----------|
| PR #8 (CM-S2 design) cần merge vào main | 🟡 Next |
| PR #9 (CM-S2 Day 1) cần CEO approve + merge | 🟡 Active |
| Wiki board ở HC repo cần update link repo mới | 🟢 Low |
| CM-S3 design chi tiết chưa tạo | 🟢 Future |

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

---

*BRIEF.md v1.2 — Codebase Map | 06/04/2026 | CM-S2 Day 1 In Progress 🔄*
