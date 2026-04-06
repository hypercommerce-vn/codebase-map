# Codebase Map Sprint 2 (CM-S2) Task Board — v1.2 Workflow + Smart
**Module: Tools (standalone) | Duration: TBD | Total: 18 SP**
**FDD: FDD-TOOL-CODEMAP | Design: design-preview/codebase-map-CM-S2-design.html**

---

## Sprint Goal
> Nâng cấp Codebase Map từ v1.1 (usable visual tool) lên v1.2 (workflow tool): git diff integration, incremental cache, test coverage overlay, API catalog, /implement + /review-gate integration, PR impact bot, staleness alert. Tất cả offline-capable.

## Quy trình mỗi Day — KHÔNG CÓ NGOẠI LỆ

```
Implement
    ↓
Local Lint Gate (black + isort + flake8 + bandit) → PASS
    ↓
Git commit + push branch
    ↓
Tạo PR
    ↓
CI Automation (GitHub Actions)
    ├── CI fail → Telegram notify dev → fix → re-push
    └── CI pass → Telegram notify CEO + label ready-for-review
    ↓
/review-gate PR #XX — 3 Tầng
    ├── Tầng 1: Tester verify
    ├── Tầng 2: CTO 5D review
    └── Tầng 3: Designer 5D review
    ↓
CEO review + approve + merge
    ↓
Cập nhật BRIEF.md + task board này + project/board.html
    ↓
Tiếp Day sau
```

---

## Task Board

| Task ID | Feature | Task | SP | Design Ref | Day | PR | Review Gate | Status |
|---------|---------|------|----|-----------|-----|-----|-------------|--------|
| CM-S2-01 | FDD-TOOL-CODEMAP | BE: Git diff integration — `codebase-map diff HEAD~1` changed + impacted nodes | 3 | CM-S2-design #cm-s2-01 | Day 1 | PR #9 | CTO 99/100 SHIPIT | ✅ Done |
| CM-S2-02 | FDD-TOOL-CODEMAP | BE: Incremental update — cache AST hash, re-parse only changed files | 3 | CM-S2-design #cm-s2-02 | Day 2 | PR #11 | CTO 100/100 SHIPIT | ✅ Done |
| CM-S2-06 | FDD-TOOL-CODEMAP | BE: Edge resolution — resolve self.repo chain từ __init__ | 2 | CM-S2-design #cm-s2-06 | Day 3 | — | — | 📋 Todo |
| CM-S2-03 | FDD-TOOL-CODEMAP | BE+FE: Test coverage overlay — map test → source, coverage bar | 2 | CM-S2-design #cm-s2-03 | Day 3 | — | — | 📋 Todo |
| CM-S2-07 | FDD-TOOL-CODEMAP | BE+FE: API Catalog auto-gen — extract routes → tab view | 2 | CM-S2-design #cm-s2-07 | Day 4 | — | — | 📋 Todo |
| CM-S2-04 | FDD-TOOL-CODEMAP | Workflow: Tích hợp /implement — Step 2 auto-query impact | 1 | CM-S2-design #cm-s2-04 | Day 4 | — | — | 📋 Todo |
| CM-S2-05 | FDD-TOOL-CODEMAP | Workflow: Tích hợp /review-gate — impact graph trong review | 1 | CM-S2-design #cm-s2-05 | Day 4 | — | — | 📋 Todo |
| CM-S2-08 | FDD-TOOL-CODEMAP | Metadata: FDD Spec linking — node → FDD ID in detail panel | 1 | CM-S2-design #cm-s2-08 | Day 5 | — | — | 📋 Todo |
| CM-S2-09 | FDD-TOOL-CODEMAP | DevOps: PR impact comment bot — CI comment impact vào PR | 1 | CM-S2-design #cm-s2-09 | Day 5 | — | — | 📋 Todo |
| CM-S2-10 | FDD-TOOL-CODEMAP | Process: Sprint metric — track impact per PR, alert > 50 nodes | 1 | CM-S2-design #cm-s2-10 | Day 5 | — | — | 📋 Todo |
| CM-S2-11 | FDD-TOOL-CODEMAP | DevOps: Staleness alert — graph > 7 days → Telegram notify | 1 | CM-S2-design #cm-s2-11 | Day 5 | — | — | 📋 Todo |

---

## Day Plan

| Day | SP | Tasks | Focus |
|-----|-----|-------|-------|
| Day 1 | 3 | CM-S2-01 | Git diff integration — foundation for impact bot + PR diff |
| Day 2 | 3 | CM-S2-02 | Incremental cache — performance optimization |
| Day 3 | 4 | CM-S2-06, CM-S2-03 | Parser accuracy + coverage overlay |
| Day 4 | 4 | CM-S2-07, CM-S2-04, CM-S2-05 | API catalog + workflow integrations |
| Day 5 | 4 | CM-S2-08, CM-S2-09, CM-S2-10, CM-S2-11 | Metadata + DevOps + process |
| **Total** | **18** | **11 tasks** | |

---

## Progress Summary

| Day | SP | Tasks | PR | Review Gate | Status |
|-----|-----|-------|-----|-------------|--------|
| Day 1 | 3 | CM-S2-01 | PR #9 | CTO 99/100 SHIPIT | ✅ Done |
| Day 2 | 3 | CM-S2-02 | PR #11 | CTO 100/100 SHIPIT | ✅ Done |
| Day 3 | 4 | CM-S2-06, CM-S2-03 | — | — | 📋 Todo |
| Day 4 | 4 | CM-S2-07, CM-S2-04, CM-S2-05 | — | — | 📋 Todo |
| Day 5 | 4 | CM-S2-08, CM-S2-09, CM-S2-10, CM-S2-11 | — | — | 📋 Todo |
| **Total** | **18** | **11 tasks** | **2 PRs merged** | | **🔄 2/11 Done (6/18 SP)** |

---

## Acceptance Criteria — Sprint Level

- [ ] CM-AC-06: `codebase-map diff HEAD~1` trả output đúng changed + impacted nodes
- [ ] CM-AC-07: Coverage bar hiện trong detail panel (xanh/vàng/đỏ)
- [ ] CM-AC-08: API Catalog tab hiện tất cả routes grouped by domain
- [ ] CM-AC-09: PR comment bot hoạt động trên GitHub Actions
- [ ] CM-AC-10: `/implement` + `/review-gate` tích hợp hoạt động

---

## Design References

| Section | File | Anchor |
|---------|------|--------|
| Tổng thể v2.0 | `design-preview/codebase-map-v2-design.html` | — |
| Chi tiết CM-S2 | `design-preview/codebase-map-CM-S2-design.html` | `#cm-s2-01` → `#cm-s2-11` |
| FDD Spec | `specs/spec.md` | Section CM-S2 |

---

## DoD Checklist — Cuối Sprint

- [ ] Tất cả 5 AC passed
- [ ] `black --check && isort --check && flake8` pass toàn bộ module
- [ ] `codebase-map diff HEAD~1` output đúng
- [ ] Incremental generate time giảm > 50%
- [ ] Coverage bar hiện trong detail panel
- [ ] API Catalog tab hoạt động
- [ ] PR comment bot hoạt động trên CI
- [ ] 5 PRs merged (1 per day)
- [ ] Mỗi PR qua review-gate
- [ ] BRIEF.md + board.html cập nhật
- [ ] Design match: `codebase-map-CM-S2-design.html`

---

*CM-S2 Task Board v1.0 | Created: 06/04/2026 | Sprint IN PROGRESS 🔄*
