# KMP-M0 Day 1 — Pre-flight Checklist
> **Sprint:** CM-MEM-M0 · **Day:** 1 · **Date:** 09/04/2026 (T4)
> **PR target:** PR #1 · **Owner:** @TechLead · **Reviewer:** @CTO

---

## ✈️ PRE-FLIGHT (chạy trước khi code)

- [ ] `git status` clean — không file dirty
- [ ] `git checkout main && git pull origin main` — local main = origin/main
- [ ] Branch tạo: `feat/kmp-m0-01-core-skeleton` từ `main`
- [ ] Specs locked & đọc:
  - [ ] `specs/kmp/architecture.md` — 6 core services + vault format
  - [ ] `specs/kmp/fdd-v2.md` — sprint timeline
  - [ ] `specs/kmp/user-stories-m0-m1.md` — US-M0-01, US-M0-02
- [ ] Designs available:
  - [ ] `design-preview/kmp-v2-design.html`
  - [ ] `design-preview/kmp-M0-design.html`
- [ ] Project board sync (BRIEF.md + board.html) ✅ done by PM kickoff PR
- [ ] Lint tools cài: `black`, `isort`, `flake8`, `mypy`
- [ ] CEO đã chấp thuận **"Approve Day 1 start"** 🟢

---

## 🎯 DAY 1 SCOPE — 3 SP (KMP-M0-01 + KMP-M0-02 start)

### KMP-M0-01 — Package skeleton (1 SP)

**Goal:** Tạo package `knowledge_memory/core/` với 8 sub-package + `__init__.py`

**Acceptance Criteria:**
- [ ] Cấu trúc: `knowledge_memory/core/{vault,learners,parsers,ai,mcp,licensing,cli,telemetry}/__init__.py`
- [ ] Mỗi sub-package có docstring 1 dòng giải thích trách nhiệm
- [ ] Tên neutral — không nhắc "code", "python", "ast"
- [ ] `python -c "from knowledge_memory.core import vault, learners, parsers, ai, mcp, licensing, cli, telemetry"` pass
- [ ] `pyproject.toml` cấu hình wheel `knowledge-memory-core==0.1.0`
- [ ] Comment `# HC-AI | ticket: KMP-M0-01` cho mọi block AI-generated

### KMP-M0-02 (start) — Abstract base classes (2 SP, finish D2)

**Goal:** Implement `BaseVault`, `BaseLearner`, `BaseParser`, `Pattern`, `Evidence` dataclass

**Day 1 partial scope:**
- [ ] `Pattern` dataclass (`frozen=True`) + `Evidence` dataclass
- [ ] `BaseVault` abstract với contract `init()`, `commit_pattern()`, `get_patterns()`
- [ ] Mọi abstract method có docstring + type hints rõ ràng
- [ ] Constant `VERTICAL_NAME` placeholder
- [ ] `BaseLearner`, `BaseParser` finish ở D2

---

## 🧪 LOCAL TEST STRATEGY

```bash
# 1. Lint gate (BẮT BUỘC trước commit)
black --check knowledge_memory/
isort --check knowledge_memory/
flake8 knowledge_memory/
mypy --strict knowledge_memory/core/

# 2. Import smoke test
python -c "from knowledge_memory.core import vault, learners, parsers, ai, mcp, licensing, cli, telemetry"

# 3. Unit test (nếu có)
pytest tests/core/ -v

# 4. Pre-flight review-gate (LOCAL)
/review-gate --local
# Block nếu CTO local < 80 hoặc Dim C < 20/25
```

---

## 🚪 REVIEW GATE EXPECTATION

**Mode:** 2-tier (từ CM-S3) → Pre-flight LOCAL trước push, Remote Full sau CI pass.

- **Local (trước push):** `/review-gate --local` ≥ 80/100
- **Remote (sau CI):** Tester PASS → CTO ≥ 90/100 → Designer N/A (D1 không có FE)
- **Final target:** ≥ 90/100 SHIPIT
- **CEO approve:** trước Day 2 kickoff

---

## ⏪ ROLLBACK PLAN

Nếu Day 1 fail (review gate < 80, hoặc CI red, hoặc abstraction sai):
1. **STOP** — không merge nửa vời
2. PM convene retro: TechLead + CTO 30 phút
3. Identify root cause: spec gap? abstraction quá sớm? lint env?
4. Options:
   - **Option A:** Fix in-place trong cùng PR #1 (max 1 ngày extra)
   - **Option B:** Close PR #1, re-plan D1 với scope giảm (chỉ KMP-M0-01)
   - **Option C:** Escalate CEO — cần điều chỉnh sprint goal
5. Update BRIEF.md + board.html với rollback decision

**No-ship rule:** Nếu sau 1 ngày fix vẫn fail → escalate, không kéo qua Day 2.

---

## 📦 DEFINITION OF DONE — DAY 1

- [ ] Branch `feat/kmp-m0-01-core-skeleton` pushed
- [ ] PR #1 opened, base = `main`
- [ ] CI 4 jobs xanh (lint, test, generate, notify)
- [ ] Review gate Mode 2 final ≥ 90/100
- [ ] CEO approve + merge
- [ ] BRIEF.md + board.html sync Day 1 status
- [ ] Day 2 unblocked

---

*KMP-M0 Day 1 Checklist · @PM · 09/04/2026*
