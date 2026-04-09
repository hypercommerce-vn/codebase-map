# CM-MEM-M0 — Sprint M0 Task Board
> **KMP Core Skeleton + Hello Vertical** · Sprint 1/5 của KMP MVP
> Owner: @TechLead · PM: @PM · Created: 08/04/2026 · CEO approved: 08/04/2026

---

## 🎯 SPRINT GOAL

Build KMP Core skeleton (abstract base + runtime + CI gate) + Hello vertical (50 LOC reference) để **chứng minh abstraction stable** trước khi đổ effort vào M1 (Codebase Vault).

**Definition of Success:** Hello vertical chạy end-to-end trong ≤ 50 LOC, sinh `patterns.md`, CI import-linter pass, mypy pass, LICENSE files tồn tại, vault-format-spec.md publish được.

---

## 📅 SPRINT META

| Field | Value |
|-------|-------|
| **Sprint code** | CM-MEM-M0 |
| **Status** | 🔥 **ACTIVE** — Day 1 ✅ MERGED (PR #44) · Day 2 ✅ MERGED (PR #45, 99/100) · Day 3 🟡 IN REVIEW · 6.5/8 SP (81%) · 09/04/2026 |
| **Start date** | 2026-04-09 (Day 1, T4) — pending CEO "Approve Day 1 start" |
| **Target end** | 2026-04-15 (Day 5, T3) — 5 working days, nghỉ T7-CN |
| **Duration** | 1 tuần |
| **Story Points** | 8 SP *(updated từ 6 — CEO bổ sung KMP-M0-07, KMP-M0-08)* |
| **Owner** | @TechLead (1 người) |
| **Reviewer** | @CTO (architecture) + @Tester (acceptance) |
| **Branch base** | `main` |
| **PR strategy** | 1 PR / Day (Daily PR Mandatory) |

---

## ✅ TASK LIST (8 SP)

| # | ID | Task | SP | Day | Status | Acceptance |
|---|----|------|:--:|:---:|:------:|------------|
| 1 | KMP-M0-01 | Tạo package `knowledge_memory/core/` skeleton (mọi `__init__.py`, abstract base files rỗng) | 1 | D1 | ✅ Done (PR #44) | `python -c "import knowledge_memory.core"` pass |
| 2 | KMP-M0-02 | Implement `BaseVault`, `BaseLearner`, `BaseParser`, `Pattern`, `Evidence` dataclass | 2 | D1-2 | ✅ Done (PR #44 + PR #45) | mypy strict pass; type hints đầy đủ |
| 3 | KMP-M0-03 | Implement `core/learners/runtime.py` orchestrator | 1 | D2 | ✅ Done (PR #45, 99/100) | Unit test với mock learner pass (12 new tests) |
| 4 | KMP-M0-04 | Setup import-linter CI rule (Core ↛ Vertical) | 0.5 | D3 | 🟡 In Review | `.importlinter` config + CI step; lint-imports PASS clean, FAIL on deliberate violation |
| 5 | KMP-M0-05 | Build `verticals/hello/` reference ≤ 50 LOC + `verticals/hello/README.md` | 1 | D3-4 | 🟡 In Progress (D3 skeleton) | HelloLearner + HelloParser done; 15 tests green; README + e2e Day 4 |
| 6 | **KMP-M0-07** *(CEO add)* | Viết `docs/vault-format-spec.md` (≤ 5 trang) — public spec | 1 | D4 | ⏳ Todo | Đủ để dev ngoài tự build vault tương thích |
| 7 | **KMP-M0-08** *(CEO add)* | Add `LICENSE` (MIT) root + `LICENSE-PRO` template + CI lint check | 0.5 | D5 | ⏳ Todo | CI fail nếu thiếu LICENSE |
| 8 | KMP-M0-06 | CTO architecture review + sign-off | 0.5 | D5 | ⏳ Todo | Review ≤ 1 ngày, ≥ 15/20 điểm |

**Total: 8 SP**

---

## 🗓️ DAILY PLAN

| Day | Date | Tasks | PR | Reviewer |
|-----|------|-------|----|----|
| **D1** | 09/04 (T4) | KMP-M0-01 + KMP-M0-02 (start) — package skeleton + abstract base | PR #1 | CTO |
| **D2** | 10/04 (T5) | KMP-M0-02 (finish) + KMP-M0-03 — runtime orchestrator | PR #2 | CTO |
| **D3** | 13/04 (T2) | KMP-M0-04 + KMP-M0-05 (start) — import-linter CI + hello vertical | PR #3 | CTO |
| **D4** | 14/04 (T3) | KMP-M0-05 (finish) + KMP-M0-07 — vault-format-spec.md | PR #4 | CTO + Designer (review spec) |
| **D5** | 15/04 (T4) | KMP-M0-08 + KMP-M0-06 — LICENSE + sign-off review-gate | PR #5 + sign-off | CTO + Tester + CEO |

*Nghỉ T7-CN. Review-gate 3 tầng (Tester → CTO → Designer) trước CEO approve.*

---

## 🚪 DEFINITION OF DONE (M0)

- [ ] Hello vertical chạy end-to-end: `knowledge-memory hello bootstrap` → sinh `patterns.md`
- [ ] Hello vertical ≤ 50 LOC (đếm bằng `cloc verticals/hello/`)
- [ ] `verticals/hello/README.md` tồn tại, dev mới đọc 5 phút copy được
- [ ] CI import-linter pass (Core ↛ Vertical enforced)
- [ ] mypy strict pass cho toàn bộ `core/`
- [ ] Pytest cover ≥ 70% cho `core/learners/runtime.py`
- [ ] `LICENSE` (MIT) + `LICENSE-PRO` template tồn tại, CI check pass
- [ ] `docs/vault-format-spec.md` ≤ 5 trang, có ví dụ schema SQLite
- [ ] CTO review ≥ 15/20 điểm
- [ ] CEO approve PR cuối

---

## ⚠️ RISK & MITIGATION

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|:----------:|:------:|------------|
| R-M0-1 | Hello vertical > 50 LOC → abstraction quá nặng | Medium | High | Daily check LOC; nếu vượt 60 LOC → stop, refactor base class |
| R-M0-2 | import-linter false positive với type stub | Low | Medium | Whitelist `typing.TYPE_CHECKING` block |
| R-M0-3 | mypy strict mode khó cho dataclass generics | Medium | Low | Dùng `Protocol` thay vì `Generic` nếu cần |
| R-M0-4 | CTO review chậm → block CEO sign-off | Low | High | CTO commit review SLA ≤ 1 ngày |

---

## 📝 NOTES

- **Branch naming:** `feat/kmp-m0-<id>-<slug>` (vd: `feat/kmp-m0-01-core-skeleton`)
- **Commit:** Conventional Commits + `# HC-AI | ticket: KMP-M0-XX` cho AI-generated code
- **Lint gate:** `black --check . && isort --check . && flake8 && mypy --strict` trước mỗi commit
- **Project board sync:** Mỗi khi update task board → sync `project/board.html`

---

## 🔗 LIÊN QUAN

- Spec gốc: `specs/kmp-architecture.md` (có CEO Sign-off section 9.bis)
- FDD v2.0: `specs/memory-fdd-v2.md`
- User stories: `specs/memory-m0-m1-user-stories.md`
- Session state: `specs/SESSION-STATE.md`

---

*CM-MEM-M0 Task Board · Created 08/04/2026 · @PM*
