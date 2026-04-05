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
| CM-S1-03 | FDD-TOOL-CODEMAP | BE: Fix "unknown" layer — classify schemas, utils, tests (444 → <50) | 1 | CM-S1-design #cm-s1-03 | Day 1 | — | — | 📋 Todo |
| CM-S1-04 | FDD-TOOL-CODEMAP | DevOps: Bundle D3.js — remove CDN, inline vào HTML | 1 | CM-S1-design #cm-s1-04 | Day 1 | — | — | 📋 Todo |
| CM-S1-01 | FDD-TOOL-CODEMAP | FE: Progressive disclosure sidebar — domain → class → method tree | 3 | CM-S1-design #cm-s1-01 | Day 2 | — | — | 📋 Todo |
| CM-S1-09 | FDD-TOOL-CODEMAP | FE: Accessibility fix — font min 11px + empty state | 1 | CM-S1-design #cm-s1-09 | Day 2 | — | — | 📋 Todo |
| CM-S1-10 | FDD-TOOL-CODEMAP | FE: Top bar — logo, stats badges, generated timestamp | 1 | CM-S1-design #cm-s1-10 | Day 2 | — | — | 📋 Todo |
| CM-S1-02 | FDD-TOOL-CODEMAP | FE+BE: Domain clustering — D3 forceCluster + background colors | 3 | CM-S1-design #cm-s1-02 | Day 3 | — | — | 📋 Todo |
| CM-S1-06 | FDD-TOOL-CODEMAP | FE: Minimap — canvas overview + viewport indicator | 2 | CM-S1-design #cm-s1-06 | Day 4 | — | — | 📋 Todo |
| CM-S1-07 | FDD-TOOL-CODEMAP | FE: Toolbar — zoom, fit, toggle labels/edges/clusters, export | 1 | CM-S1-design #cm-s1-07 | Day 4 | — | — | 📋 Todo |
| CM-S1-08 | FDD-TOOL-CODEMAP | FE: Dual legend — node type (fill) + edge type (line style) | 1 | CM-S1-design #cm-s1-08 | Day 4 | — | — | 📋 Todo |
| CM-S1-05 | FDD-TOOL-CODEMAP | DevOps: .gitignore output + CI auto-generate on PR | 1 | CM-S1-design timestamp | Day 5 | — | — | 📋 Todo |

---

## Progress Summary

| Day | SP | Tasks | PR | Review Gate | Status |
|-----|-----|-------|-----|-------------|--------|
| Day 1 | 2 | CM-S1-03, CM-S1-04 | — | — | 📋 Todo |
| Day 2 | 5 | CM-S1-01, CM-S1-09, CM-S1-10 | — | — | 📋 Todo |
| Day 3 | 3 | CM-S1-02 | — | — | 📋 Todo |
| Day 4 | 4 | CM-S1-06, CM-S1-07, CM-S1-08 | — | — | 📋 Todo |
| Day 5 | 1 | CM-S1-05 | — | — | 📋 Todo |
| **Total** | **15** | **10 tasks** | | | **0/10 Done (0/15 SP)** |

---

## Acceptance Criteria — Sprint Level

- [ ] CM-AC-01: HTML mở offline, không cần CDN (D3.js bundled)
- [ ] CM-AC-02: Sidebar tree collapse/expand hoạt động (domain → class → method)
- [ ] CM-AC-03: Domain clustering visible trên graph (7 domains, mỗi domain có vùng riêng)
- [ ] CM-AC-04: CI job generate map chạy thành công trên GitHub Actions
- [ ] CM-AC-05: "unknown" layer < 5% total nodes (< 70 nodes)
- [ ] CM-AC-06: Minimap hiện toàn cảnh + viewport indicator
- [ ] CM-AC-07: Toolbar 8 buttons hoạt động (zoom/fit/labels/edges/clusters/export/fullscreen)
- [ ] CM-AC-08: Dual legend phân biệt rõ: Type (dot) + Edge (line)
- [ ] CM-AC-09: Font minimum 11px trên toàn bộ UI
- [ ] CM-AC-10: Search không kết quả → hiện empty state

---

## Design References

| Section | File | Anchor |
|---------|------|--------|
| Tổng thể v2.0 | `design-preview/codebase-map-v2-design.html` | — |
| Chi tiết CM-S1 | `design-preview/codebase-map-CM-S1-design.html` | `#cm-s1-01` → `#full-layout` |
| FDD Spec | `.claude/specs/FDD-TOOL-CODEMAP/spec.md` | Section CM-S1 |

---

## DoD Checklist — Cuối Sprint

- [ ] Tất cả 10 AC passed
- [ ] `black --check && isort --check && flake8` pass toàn bộ module
- [ ] HTML render đúng trên Chrome, Firefox, Safari
- [ ] Generate chạy trên HC backend: nodes > 1300, "unknown" < 5%
- [ ] 5 PRs merged (1 per day)
- [ ] Mỗi PR qua 3-tầng review-gate
- [ ] BRIEF.md cập nhật
- [ ] 100% match design: `codebase-map-CM-S1-design.html` #full-layout

---

*CM-S1 Task Board v1.0 | Created: 05/04/2026 by PM Agent*
