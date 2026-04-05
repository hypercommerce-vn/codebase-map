# BRIEF.md — Codebase Map Session Brief
> **Đọc file này ĐẦU TIÊN mỗi session. Cập nhật cuối mỗi session.**
> Version: 1.0 | Cập nhật: 05/04/2026

---

## 🎯 TRẠNG THÁI HIỆN TẠI

| Field | Value |
|-------|-------|
| **Version hiện tại** | v1.0 Done + CM-S1 Day 1 Done |
| **Sprint hiện tại** | CM-S1 (v1.1) — **ACTIVE** (Day 1/5 Done, 2/15 SP) |
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

### CM-S1 Day 1 — v1.1 partial
- **CM-S1-03**: Fix unknown layer 444 → 2 nodes (0.1%). Added LayerType.SCHEMA + TEST
- **CM-S1-04**: Bundle D3.js (280KB). HTML offline-capable, no CDN dependency
- Review Gate: Tester PASS + CTO 100/100 SHIPIT

### Repo Migration (CEO Decision 05/04/2026)
- Tách từ `hypercommercesystem/tools/codebase-map/` → repo riêng
- HC repo PR #85 merged (xóa tool code)
- HC repo PR #82 merged (v1.0 original), PR #84 closed (superseded)
- HC repo chỉ giữ `codebase-map.yaml` config

---

## 🔄 ĐANG LÀM — CM-S1 (v1.1) Sprint

| Day | Tasks | SP | Status |
|-----|-------|----|--------|
| Day 1 | CM-S1-03 (fix unknown) + CM-S1-04 (bundle D3) | 2 | ✅ Done |
| Day 2 | CM-S1-01 (sidebar tree) + CM-S1-09 (empty state) + CM-S1-10 (top bar) | 5 | 📋 Todo |
| Day 3 | CM-S1-02 (domain clustering) | 3 | 📋 Todo |
| Day 4 | CM-S1-06 (minimap) + CM-S1-07 (toolbar) + CM-S1-08 (legend) | 4 | 📋 Todo |
| Day 5 | CM-S1-05 (CI auto-generate) | 1 | 📋 Todo |
| **Total** | **10 tasks** | **2/15 SP** | **Day 1 Done** |

---

## 📋 QUYẾT ĐỊNH QUAN TRỌNG

| Ngày | Quyết định | Người |
|------|-----------|-------|
| 05/04/2026 | **Tách repo** — codebase-map là standalone tool, không commit vào HC repo | CEO |
| 05/04/2026 | **Design v2.0 approved** — `codebase-map-v2-design.html` | CEO |
| 05/04/2026 | **Design CM-S1 approved** — `codebase-map-CM-S1-design.html` | CEO |
| 05/04/2026 | **FDD spec approved** — 3 sprints, 29 tasks, 55 SP | CEO |
| 05/04/2026 | **Quy trình Day** — Implement → Lint → PR → CI → /review-gate 3 tầng → CEO | CEO |
| 05/04/2026 | **Retroactive approve Day 1** — CM-S1 Day 1 đã review ở HC repo cũ (PR #82/#84), coi như pass. Exception do migration repo | CEO |
| 06/04/2026 | **AI Infrastructure Migration** — Copy + adapt từ HC: 7 agents, 5 commands, settings, 7 memory files. CEO approved phương án 3 phase | CEO |

---

## 🔥 VẤN ĐỀ ĐANG MỞ

| Vấn đề | Priority |
|--------|----------|
| Day 2-5 CM-S1 chưa implement | 🟡 Next |
| Wiki board ở HC repo cần update link repo mới | 🟢 Low |
| CM-S2 + CM-S3 design chi tiết chưa tạo | 🟢 Future |

---

## 📁 FILES QUAN TRỌNG

| File | Nội dung |
|------|----------|
| `CLAUDE.md` | Rules + structure + development guide |
| `specs/spec.md` | FDD spec đầy đủ 3 sprints |
| `project/CM-S1-TASK-BOARD.md` | Task board sprint 1 |
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

*BRIEF.md v1.0 — Codebase Map | 05/04/2026 | Repo migration complete.*
