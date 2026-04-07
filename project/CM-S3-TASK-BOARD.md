# Codebase Map Sprint 3 (CM-S3) Task Board — v2.0 Multi-view + TypeScript + Responsive
**Module: Tools (standalone) | Duration: 5 Days | Total: 22 SP**
**FDD: FDD-TOOL-CODEMAP | Design: design-preview/codebase-map-CM-S3-design.html**

---

## Sprint Goal
> Nâng cấp Codebase Map từ v1.2 (workflow tool) lên v2.0 (stakeholder tool):
> 4-view mode (Graph/Executive/API/PR Diff), TypeScript parser, Business Flow tagging,
> Breadcrumb navigation, Detail Panel v2, Responsive sidebar. Serve đủ 4 persona:
> Developer, Product, Executive, Reviewer.

---

## Quy trình mỗi Day — 2-tier Review Gate (CEO Decision 07/04/2026)

```
Implement
    ↓
/review-gate --local  ← BƯỚC 5.5 BẮT BUỘC TỪ CM-S3
    ├── Lint gate (black + isort + flake8)
    ├── Self-test generate
    ├── CTO 5D local scoring (trên git diff main..HEAD)
    ├── Tester edge cases basic
    └── Designer 5D local (nếu có HTML changes)
    ↓
Verdict local:
    ├── < 80  → ❌ BLOCK → fix → re-run
    ├── 80–89 → ⚠️ NOTE  → note vào PR body, cho phép push
    └── ≥ 90  → ✅ GO → tiếp tục
    ↓
Git commit + push branch
    ↓
gh pr create
    ↓
CI Automation (GitHub Actions)
    ├── lint + test (3.10-3.12)
    ├── PR Impact Bot comment (CM-S2-09)
    └── Telegram notify CEO
    ↓
/review-gate PR #XX  ← Mode 2: Remote Full
    ├── Tầng 1: Tester verify
    ├── Tầng 2: CTO 5D review
    └── Tầng 3: Designer 5D review (nếu HTML)
    ↓
CEO review + approve + merge
    ↓
Cập nhật BRIEF.md + CM-S3-TASK-BOARD.md + project/board.html (Rule #8)
    ↓
Day tiếp theo
```

---

## Task Board

| Task ID | Feature | Task | SP | Design Ref | Day | PR | Review Gate | Status |
|---------|---------|------|----|-----------|-----|-----|-------------|--------|
| CM-S3-06 | FDD-TOOL-CODEMAP | BE: TypeScript parser — tree-sitter WASM, .ts/.tsx/.js | 5 | CM-S3-design #cm-s3-06 | Day 1 | — | — | 📋 Todo |
| CM-S3-01 | FDD-TOOL-CODEMAP | FE: Multi-view mode — 4 tab switcher (Graph/Exec/API/Diff) | 3 | CM-S3-design #cm-s3-01 | Day 2 | — | — | 📋 Todo |
| CM-S3-05 | FDD-TOOL-CODEMAP | FE: Breadcrumb navigation — drill-down trail + URL sync | 2 | CM-S3-design #cm-s3-05 | Day 2 | — | — | 📋 Todo |
| CM-S3-02 | FDD-TOOL-CODEMAP | FE: Executive view — domain health grid + metrics | 3 | CM-S3-design #cm-s3-02 | Day 3 | — | — | 📋 Todo |
| CM-S3-07 | FDD-TOOL-CODEMAP | FE: Detail Panel v2 — 5 blocks (Identity/Sig/Rel/Quality/Meta) | 2 | CM-S3-design #cm-s3-07 | Day 3 | — | — | 📋 Todo |
| CM-S3-03 | FDD-TOOL-CODEMAP | FE: PR Diff view — color-coded node highlighting | 3 | CM-S3-design #cm-s3-03 | Day 4 | — | — | 📋 Todo |
| CM-S3-04 | FDD-TOOL-CODEMAP | BE+FE: Business Flow Mapping — YAML tags + flow diagram | 3 | CM-S3-design #cm-s3-04 | Day 4 | — | — | 📋 Todo |
| CM-S3-08 | FDD-TOOL-CODEMAP | FE: Responsive sidebar — mobile/tablet/desktop breakpoints | 1 | CM-S3-design #cm-s3-08 | Day 5 | — | — | 📋 Todo |

---

## Day Plan

| Day | SP | Tasks | Focus | Risk |
|-----|-----|-------|-------|------|
| Day 1 | 5 | CM-S3-06 | TypeScript parser foundation (BE only, no design gate) | 🔴 Largest task — isolate to 1 Day |
| Day 2 | 5 | CM-S3-01, CM-S3-05 | Multi-view tab bar + breadcrumb (navigation layer) | 🟡 FE state mgmt |
| Day 3 | 5 | CM-S3-02, CM-S3-07 | Executive view + Detail Panel v2 (read views) | 🟢 Pure render |
| Day 4 | 6 | CM-S3-03, CM-S3-04 | PR Diff view + Business Flow tagging | 🟡 Depends Day 2 tab infra |
| Day 5 | 1 | CM-S3-08 | Responsive sidebar + sprint polish + DoD | 🟢 Small, buffer day |
| **Total** | **22** | **8 tasks** | | |

**Rationale:**
- Day 1 đặt CM-S3-06 một mình vì là task BE lớn nhất (5 SP) và không cần design gate
- Day 2 ship navigation layer (tab + breadcrumb) trước để Day 3/4 build views lên trên
- Day 3 views đơn giản, pure render
- Day 4 views phức tạp nhất cần tab infra từ Day 2
- Day 5 chỉ có 1 SP để buffer cho DoD checklist + fix carry-over

---

## Acceptance Criteria — Sprint Level

- [ ] CM-AC-11: TypeScript parser extract ≥95% functions/classes từ sample .ts/.tsx project
- [ ] CM-AC-12: 4-tab view switcher hoạt động, state sync URL hash
- [ ] CM-AC-13: Executive view hiện 7 domain boxes với coverage bar
- [ ] CM-AC-14: PR Diff view highlight added/modified/removed/impacted đúng màu
- [ ] CM-AC-15: Business Flow tagging từ YAML config hiện flow diagram
- [ ] CM-AC-16: Breadcrumb trail drill-down + URL sync
- [ ] CM-AC-17: Detail Panel v2 hiện đủ 5 blocks
- [ ] CM-AC-18: Responsive breakpoints hoạt động trên mobile/tablet/desktop

---

## Design References

| Section | File | Anchor |
|---------|------|--------|
| Tổng thể v2.0 | `design-preview/codebase-map-v2-design.html` | — |
| Chi tiết CM-S3 | `design-preview/codebase-map-CM-S3-design.html` | `#cm-s3-01` → `#cm-s3-08` |
| FDD Spec | `specs/spec.md` | Section CM-S3 |

---

## DoD Checklist — Cuối Sprint

- [ ] Tất cả 8 AC passed
- [ ] `black --check && isort --check && flake8` pass toàn bộ module
- [ ] TypeScript parser self-test pass (sample .ts project)
- [ ] 4 views render đúng trên HC project graph
- [ ] Responsive test pass trên Chrome mobile emulator (< 768px, 768–1024px, ≥ 1024px)
- [ ] 5 PRs merged (1 per day, Day 4 có thể 1–2 PRs nếu cần split)
- [ ] Mỗi PR qua **2-tier Review Gate** (local pre-flight + remote full)
- [ ] BRIEF.md + board.html cập nhật sau mỗi Day (Rule #8)
- [ ] Design match: `codebase-map-CM-S3-design.html` 100%

---

*CM-S3 Task Board v1.0 | Created: 07/04/2026 | Sprint planned, awaiting CEO approval 📋*
