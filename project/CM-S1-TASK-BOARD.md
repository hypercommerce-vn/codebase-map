# Codebase Map Sprint 1 (CM-S1) Task Board — v1.1 UX Polish + DevOps
**Module: Tools (standalone) | Duration: TBD | Total: 15 SP**
**FDD: FDD-TOOL-CODEMAP | Design: design-preview/codebase-map-CM-S1-design.html**

---

## Sprint Goal
> Nâng cấp Codebase Map từ v1.0 (raw graph) lên v1.1 (usable visual tool): progressive disclosure sidebar, domain clustering, minimap, toolbar, legend, CI auto-generate. Tất cả offline-capable.

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
Cập nhật BRIEF.md + task board này
    ↓
Tiếp Day sau
```

---

## Task Board

| Task ID | Feature | Task | SP | Design Ref | Day | PR | Review Gate | Status |
|---------|---------|------|----|-----------|-----|-----|-------------|--------|
| CM-S1-03 | FDD-TOOL-CODEMAP | BE: Fix "unknown" layer — classify schemas, utils, tests (444 → 2) | 1 | CM-S1-design #cm-s1-03 | Day 1 | Retroactive | CTO 100/100 | ✅ Done |
| CM-S1-04 | FDD-TOOL-CODEMAP | DevOps: Bundle D3.js — remove CDN, inline vào HTML (280KB) | 1 | CM-S1-design #cm-s1-04 | Day 1 | Retroactive | CTO 100/100 | ✅ Done |
| CM-S1-01 | FDD-TOOL-CODEMAP | FE: Progressive disclosure sidebar — domain → class → method tree | 3 | CM-S1-design #cm-s1-01 | Day 2 | PR #2 | 95.4% SHIPIT | ✅ Done |
| CM-S1-09 | FDD-TOOL-CODEMAP | FE: Accessibility fix — font min 11px + empty state | 1 | CM-S1-design #cm-s1-09 | Day 2 | PR #2 | 95.4% SHIPIT | ✅ Done |
| CM-S1-10 | FDD-TOOL-CODEMAP | FE: Top bar — logo, stats badges, generated timestamp | 1 | CM-S1-design #cm-s1-10 | Day 2 | PR #2 | 95.4% SHIPIT | ✅ Done |
| CM-S1-02 | FDD-TOOL-CODEMAP | FE+BE: Domain clustering — D3 forceCluster + background colors | 3 | CM-S1-design #cm-s1-02 | Day 3 | PR #3 | CI pass + CEO approved | ✅ Done |
| CM-S1-06 | FDD-TOOL-CODEMAP | FE: Minimap — canvas overview + viewport indicator | 2 | CM-S1-design #cm-s1-06 | Day 4 | PR #4 | 95.4% SHIPIT | ✅ Done |
| CM-S1-07 | FDD-TOOL-CODEMAP | FE: Toolbar — zoom, fit, toggle labels/edges/clusters, export | 1 | CM-S1-design #cm-s1-07 | Day 4 | PR #4 | 95.4% SHIPIT | ✅ Done |
| CM-S1-08 | FDD-TOOL-CODEMAP | FE: Dual legend — node type (fill) + edge type (line style) | 1 | CM-S1-design #cm-s1-08 | Day 4 | PR #4 | 95.4% SHIPIT | ✅ Done |
| CM-S1-05 | FDD-TOOL-CODEMAP | DevOps: CI auto-generate on PR + verify HTML + artifact upload | 1 | CM-S1-design timestamp | Day 5 | PR #5 | CTO 100/100 | ✅ Done |

---

## Progress Summary

| Day | SP | Tasks | PR | Review Gate | Status |
|-----|-----|-------|-----|-------------|--------|
| Day 1 | 2 | CM-S1-03, CM-S1-04 | Retroactive | CTO 100/100 SHIPIT | ✅ Done |
| Day 2 | 5 | CM-S1-01, CM-S1-09, CM-S1-10 | PR #2 | CTO 93 + Designer 99 → 95.4% SHIPIT | ✅ Done |
| Day 3 | 3 | CM-S1-02 + CI Telegram | PR #3 | CI pass + CEO approved | ✅ Done |
| Day 4 | 4 | CM-S1-06, CM-S1-07, CM-S1-08 | PR #4 | CTO 93 + Designer 99 → 95.4% SHIPIT | ✅ Done |
| Day 5 | 1 | CM-S1-05 | PR #5 | CTO 100/100 SHIPIT | ✅ Done |
| **Total** | **15** | **10 tasks** | **5 PRs merged** | **All passed** | **✅ 10/10 Done (15/15 SP)** |

---

## Acceptance Criteria — Sprint Level

- [x] CM-AC-01: HTML mở offline, không cần CDN (D3.js bundled 280KB) ✅ Day 1
- [x] CM-AC-02: Sidebar tree collapse/expand hoạt động (domain → class → method) ✅ Day 2
- [x] CM-AC-03: Domain clustering visible trên graph (forceCluster + background colors) ✅ Day 3
- [x] CM-AC-04: CI job generate map chạy thành công trên GitHub Actions ✅ Day 5
- [x] CM-AC-05: "unknown" layer < 5% total nodes (< 1% achieved) ✅ Day 1
- [x] CM-AC-06: Minimap hiện toàn cảnh + viewport indicator ✅ Day 4
- [x] CM-AC-07: Toolbar 8 buttons hoạt động (zoom/fit/labels/edges/clusters/export/fullscreen) ✅ Day 4
- [x] CM-AC-08: Dual legend phân biệt rõ: Type (dot) + Edge (line) ✅ Day 4
- [x] CM-AC-09: Font minimum 11px trên toàn bộ UI ✅ Day 2
- [x] CM-AC-10: Search không kết quả → hiện empty state ✅ Day 2

---

## Design References

| Section | File | Anchor |
|---------|------|--------|
| Tổng thể v2.0 | `design-preview/codebase-map-v2-design.html` | — |
| Chi tiết CM-S1 | `design-preview/codebase-map-CM-S1-design.html` | `#cm-s1-01` → `#full-layout` |
| FDD Spec | `.claude/specs/FDD-TOOL-CODEMAP/spec.md` | Section CM-S1 |

---

## DoD Checklist — Cuối Sprint

- [x] Tất cả 10 AC passed ✅
- [x] `black --check && isort --check && flake8` pass toàn bộ module ✅
- [x] HTML render đúng trên Chrome, Firefox, Safari ✅
- [x] Generate chạy trên self-test: 65 nodes, 313 edges ✅
- [x] 5 PRs merged (1 per day) ✅ Retroactive + PR #2 + PR #3 + PR #4 + PR #5
- [x] Mỗi PR qua review-gate ✅ (Tester + CTO + Designer where applicable)
- [x] BRIEF.md cập nhật ✅
- [x] Design match: `codebase-map-CM-S1-design.html` ✅

---

## 🎉 SPRINT CM-S1 COMPLETE — 06/04/2026

**Velocity:** 15/15 SP (100%)
**Quality:** All review gates passed (avg score 97.7%)
**Timeline:** 5 Days, on schedule
**CI:** 4-job pipeline with Telegram notifications

---

*CM-S1 Task Board v1.1 | Updated: 06/04/2026 | Sprint COMPLETE ✅*
