# M0 + M1 — User Stories & Acceptance Criteria
> **Sprint:** KMP Core Skeleton (M0) + Codebase Vault + Quick Win (M1)
> **Author:** @BA · **Reviewers:** @PO @CTO @TechLead
> **Version:** 2.0 · **Ngày:** 07/04/2026
> **Liên quan:** `memory-fdd-v2.md`, `kmp-architecture.md`

## ⚠ Thay đổi v2.0 so với v1.0
1. **Thêm Sprint M0** với 6 user story xây KMP Core skeleton
2. M1 stories cập nhật để **kế thừa từ Core abstract base** (`BaseVault`, `BaseLearner`, `BaseParser`)
3. Package layout đổi sang `knowledge_memory.verticals.codebase.*`
4. Thêm spike R-T1 BM25 tiếng Việt
5. Tổng SP: M0 (6) + M1 (26) = **32 SP** (tăng từ 25 do M0 mới)

---

## 1. Persona

| ID | Persona | Mô tả 1 dòng |
|----|---------|-------------|
| P1 | **CTO Hùng** (HC) | CTO dogfood Memory, gate quality |
| P2 | **Dev mới Linh** (HC) | Junior Python join HC tuần đầu |
| P3 | **Tech Lead Sơn** (khách tiềm năng) | Lead SME muốn pitch cho CEO |
| P4 | **TechLead nội bộ** | Người implement KMP Core + vertical |

---

## 2. Epic

> **EPIC-M0:** Là TechLead, tôi muốn có KMP Core skeleton + abstract base + reference vertical "hello" hoạt động, để mọi vertical sau (Codebase, Legal, Sales) build trên nền tảng sạch, không phải refactor.
>
> **EPIC-M1:** Là dev/CTO codebase Python legacy, tôi muốn cài Codebase Memory một lệnh và có vault sinh pattern + 10 insight ban đầu trong ≤ 5 phút.

---

## 3. Sprint M0 — KMP Core Skeleton (6 SP / 1 tuần)

### US-M0-01 — Package skeleton
**FR:** FR-M0-01 · **Task:** KMP-M0-01 · **SP:** 1 · **Persona:** P4

**Story:** Là TechLead, tôi muốn package `knowledge_memory.core` có 8 sub-package (vault, learners, parsers, ai, mcp, licensing, cli, telemetry) với `__init__.py` đầy đủ, để mọi import sau này hoạt động ngay.

**GIVEN** monorepo `knowledge-memory/` mới khởi tạo
**WHEN** TechLead tạo `knowledge_memory/core/` + 8 sub-package
**THEN** lệnh `python -c "from knowledge_memory.core import vault, learners, parsers, ai, mcp, licensing, cli, telemetry"` chạy không error
**AND** không có file nào trong `core/` import từ `verticals/`
**AND** `pyproject.toml` cấu hình wheel `knowledge-memory-core==0.1.0`

**Edge cases:**
- Sub-package rỗng → vẫn phải có `__init__.py` placeholder
- Circular import → CI fail rõ ràng

**Business Rules:**
1. Mọi sub-package có docstring 1 dòng giải thích trách nhiệm
2. Tên package neutral, không nhắc tới "code", "python", "ast" — đó là vertical-specific

---

### US-M0-02 — Abstract base classes
**FR:** FR-M0-02 · **Task:** KMP-M0-02 · **SP:** 2 · **Persona:** P4

**Story:** Là TechLead, tôi muốn có 6 abstract base class chuẩn (`BaseVault`, `BaseLearner`, `BaseParser`, `LLMProvider`, `BaseMCPTool`, `BaseCLI`) + 2 dataclass (`Pattern`, `Evidence`), để mọi vertical kế thừa nhất quán.

**GIVEN** package skeleton M0-01 đã xong
**WHEN** TechLead implement abstract base + dataclass theo `kmp-architecture.md` mục 4
**THEN** `mypy --strict knowledge_memory/core/` pass 100%
**AND** mọi abstract method có docstring với tham số/return type rõ ràng
**AND** có ≥ 1 unit test cho mỗi abstract class (tạo subclass mock, gọi method)

**Edge cases:**
- Abstract method bị quên override → mypy + runtime đều catch
- Generic type (`BaseLearner[E, C]`) phải hoạt động với type checker

**Business Rules:**
1. Abstract base **không chứa logic cụ thể** — chỉ contract
2. Mọi base class có constant `VERTICAL_NAME` hoặc tương đương để vertical bắt buộc set
3. Pattern dataclass immutable (`frozen=True`)

---

### US-M0-03 — Learner Runtime orchestrator
**FR:** FR-M0-03 · **Task:** KMP-M0-03 · **SP:** 1 · **Persona:** P4

**Story:** Là TechLead, tôi muốn có `LearnerRuntime` orchestrate được nhiều learner song song, gom evidence, tính confidence, commit pattern qua threshold, để vertical chỉ define learner mà không phải tự viết loop.

**GIVEN** abstract base M0-02 đã có
**WHEN** TechLead viết `core/learners/runtime.py`
**THEN** `LearnerRuntime(vault, learners=[mock1, mock2]).run_all()` trả về list pattern
**AND** chỉ pattern có confidence ≥ `MIN_CONFIDENCE` được commit vào vault
**AND** unit test cover: 0 learner, 1 learner trả về 0 pattern, 1 learner trả về 5 pattern, learner raise exception (không crash runtime)

**Edge cases:**
- Learner crash → log error, tiếp tục learner khác
- 0 evidence → skip learner gracefully

**Business Rules:**
1. Runtime **không** biết vertical là gì — chỉ làm việc với BaseLearner
2. Confidence threshold lấy từ thuộc tính `learner.MIN_CONFIDENCE`, có thể override per-learner

---

### US-M0-04 — Import-linter CI rule
**FR:** FR-M0-04 · **Task:** KMP-M0-04 · **SP:** 0.5 · **Persona:** P4

**Story:** Là CTO, tôi muốn CI fail nếu bất kỳ commit nào làm Core import từ Vertical, để đảm bảo dependency rule không bị vi phạm vô tình.

**GIVEN** import-linter cài qua `pip install import-linter`
**WHEN** TechLead viết `.importlinter` với contract `core-purity` (forbidden Core → Vertical)
**THEN** CI workflow chạy `lint-imports` mỗi PR
**AND** test cố ý vi phạm: thêm 1 dòng `from knowledge_memory.verticals.codebase import X` vào file core → CI fail
**AND** test xóa dòng → CI pass

**Business Rules:**
1. Rule này **non-negotiable** — không bao giờ tắt, không bao giờ skip
2. Vi phạm rule = block merge

---

### US-M0-05 — Hello vertical reference 50 LOC
**FR:** FR-M0-05 · **Task:** KMP-M0-05 · **SP:** 1 · **Persona:** P4

**Story:** Là TechLead, tôi muốn build 1 vertical "hello" siêu đơn giản (count word frequency trong file .txt) trong ≤ 50 LOC tổng, để chứng minh Core abstraction đủ tốt cho vertical mới.

**GIVEN** Core skeleton + LearnerRuntime đã xong
**WHEN** TechLead implement `verticals/hello/` với 4 file: `__init__.py`, `parsers.py`, `learners.py`, `cli.py`
**THEN** `wc -l verticals/hello/*.py` ≤ 50
**AND** lệnh `hello-memory init && hello-memory bootstrap` trên thư mục có 3 file `.txt` sinh được `patterns.md` với pattern frequent_word
**AND** không có file nào trong hello vertical re-implement logic đã có ở Core

**Edge cases:**
- Thư mục không có file `.txt` → bootstrap log "no corpus" gracefully
- File `.txt` rỗng → skip, không crash

**Business Rules:**
1. Hello vertical là **tutorial chính thức** ship cùng v1.0
2. Nếu hello quá khó implement < 50 LOC → Core abstraction cần refactor

---

### US-M0-06 — CTO architecture sign-off
**FR:** FR-M0-06 · **Task:** KMP-M0-06 · **SP:** 0.5 · **Persona:** P1

**Story:** Là CTO, tôi muốn review toàn bộ M0 deliverable trước khi M1 bắt đầu, để đảm bảo nền móng đúng.

**GIVEN** US-M0-01 → M0-05 đã pass
**WHEN** CTO review code + chạy hello vertical
**THEN** CTO chấm 5 tiêu chí (scale 1-4):
  - Abstract base có ngôn ngữ neutral
  - Hello vertical thực sự ≤ 50 LOC
  - Import-linter rule pass
  - Mypy strict pass
  - Architecture doc match implementation
**AND** điểm trung bình ≥ 3.0 → approve sprint M1 kickoff

---

## 4. Sprint M1 — Codebase Vault + Quick Win (26 SP / 2 tuần)

### US-M1-01 — CodebaseVault kế thừa BaseVault
**FR:** FR-M1-01 · **Task:** MEM-M1-01 · **SP:** 2 · **Persona:** P3

**Story:** Là Tech Lead Sơn, tôi muốn chạy `codebase-memory init` ở root project, để vault `.knowledge-memory/verticals/codebase/` được tạo với cấu trúc sẵn sàng.

**GIVEN** KMP Core M0 đã xong, project có `pyproject.toml`
**WHEN** dev chạy `codebase-memory init`
**THEN** `CodebaseVault(BaseVault).init()` được gọi, tạo:
  - `.knowledge-memory/config.yaml` (`llm.provider: anthropic`)
  - `.knowledge-memory/core.db` (Core SQLite schema)
  - `.knowledge-memory/verticals/codebase/vault.db` (extension schema)
  - `.knowledge-memory/verticals/codebase/snapshots/`
  - `.knowledge-memory/verticals/codebase/patterns.md`
  - `.knowledge-memory/.gitignore`
**AND** terminal in `Vault initialized. Run 'codebase-memory bootstrap' next.`

**Edge cases:**
- Vault đã tồn tại → cảnh báo, exit 1; `--force` backup cũ rồi tạo mới
- Không có quyền ghi → error rõ ràng

**Business Rules:**
1. CodebaseVault **chỉ override** những method bắt buộc của BaseVault
2. Schema SQL extension load từ `verticals/codebase/schema_extension.sql`

---

### US-M1-02 — PythonASTParser kế thừa BaseParser
**FR:** FR-M1-02 · **Task:** MEM-M1-02 · **SP:** 2 · **Persona:** P4

**Story:** Là TechLead, tôi muốn port logic AST từ codebase-map cũ sang `verticals/codebase/parsers/python_ast.py` kế thừa `BaseParser`, để tái dùng code đã được test.

**GIVEN** BaseParser abstract đã có (M0-02)
**WHEN** TechLead implement `PythonASTParser(BaseParser)`
**THEN** `parse(vault)` yield Evidence với data `{name, file, line, type, layer}`
**AND** unit test với 3 fixture (tiny, medium, HC anonymized) pass
**AND** không import gì từ `codebase_map` package cũ — port logic, không depend

**Edge cases:**
- Syntax error trong file Python → log + skip file, không abort
- File rỗng → skip
- Encoding non-UTF8 → fallback latin-1

---

### US-M1-03 → US-M1-08 (rút gọn)

| ID | Mô tả | SP | Map Core |
|----|-------|:--:|---------|
| US-M1-03 | Snapshot từ Codebase Map subprocess (cleanup giữ 5 mới nhất) | 2 | core.vault.snapshot |
| US-M1-04 | SQLite schema extension cho codebase (bảng nodes, edges, file_ownership) | 2 | core.vault.index |
| US-M1-05 | NamingLearner kế thừa BaseLearner (confidence ≥ 60%, ≥ 5 evidence) | 2 | core.learners.BaseLearner |
| US-M1-06 | LayerLearner (top 5 path prefix, layer violation flag) | 2 | core.learners.BaseLearner |
| US-M1-07 | GitOwnershipLearner (top author qua git blame, cache trong vault.db) | 2 | core.learners.BaseLearner |
| US-M1-08 | patterns.md generator dùng vault.commit_pattern() | 2 | core.vault.commit_pattern |

Mỗi story đầy đủ GIVEN/WHEN/THEN + edge case viết trong file BA detail (rút gọn ở đây để tránh trùng v1.0). Nguyên tắc chung: **mọi vertical class đều phải kế thừa từ Core abstract**, không được tự tạo class mới ngoài hierarchy.

---

### US-M1-09 — Bootstrap orchestrator (Quick Win)
**FR:** FR-M1-05 · **Task:** MEM-M1-09 · **SP:** 2 · **Persona:** P3

**Story:** Là Tech Lead Sơn, tôi muốn `codebase-memory bootstrap` chạy tuần tự (snapshot → 3 learner → patterns.md → quick wins → CLI summary) trong ≤ 5 phút trên codebase ≤ 100K LOC, không gọi LLM.

**GIVEN** vault đã init, codebase ≤ 100K LOC
**WHEN** dev chạy `codebase-memory bootstrap`
**THEN** progress bar hiển thị 5 step
**AND** tổng thời gian ≤ 5 phút (đo trên 3 fixture)
**AND** không có outbound HTTP request nào (test với network sandbox)
**AND** exit 0 khi success, 1 khi step quan trọng fail

**Edge cases:**
- > 100K LOC → cảnh báo "may exceed 5 min, continue? [y/N]"
- 1 learner fail → tiếp tục learner khác
- Ctrl+C → cleanup snapshot dở

---

### US-M1-10 — Quick Wins generator (10 insight)
**FR:** FR-M1-06 · **Task:** MEM-M1-10 · **SP:** 3 · **Persona:** P3

**Story:** Là Tech Lead Sơn, tôi muốn ngay sau bootstrap thấy `quick-wins.md` với đúng 10 insight cụ thể (5 structure + 3 patterns + 2 risks), mỗi insight có evidence path.

**GIVEN** bootstrap chạy xong learner
**WHEN** `quick_wins.py generate()` chạy
**THEN** sinh `verticals/codebase/quick-wins.md` với 10 mục:
  - Top 5 layer · Top 5 hot file · Top 5 most depended · Số entry point · Test coverage path-based
  - Naming pattern confidence cao nhất · 3 layer violation · 3 top contributor
  - Top 5 file dài nhất · File stale > 365 ngày
**AND** ≥ 8/10 insight chính xác theo CTO subjective gate
**AND** insight confidence < 60% gắn `[needs review]`

---

### US-M1-11 — CLI summary với rich
**FR:** FR-M1-07 · **Task:** MEM-M1-11 · **SP:** 1 · **Persona:** P3

**Story:** Là Tech Lead Sơn, tôi muốn sau bootstrap terminal hiển thị summary đẹp ≤ 20 dòng có màu, để biết next step.

**GIVEN** bootstrap success
**WHEN** bước cuối thực thi
**THEN** in 4 section: stats, top 3 insights, files generated, next steps
**AND** màu xanh = success, vàng = warning, đỏ = error
**AND** `NO_COLOR=1` fallback plain text

---

### US-M1-12 — Spike R-T1 BM25 tiếng Việt
**FR:** R-T1 mitigation · **Task:** MEM-M1-12 · **SP:** 2 · **Persona:** P4

**Story:** Là TechLead, tôi muốn spike test BM25 với 50 prompt tiếng Việt trên HC backend, để biết recall có ≥ 75% không, trước khi build RAG ở M2.

**GIVEN** HC backend snapshot có biến tiếng Việt không dấu (`xu_ly_don_hang`, `khach_hang_service`)
**WHEN** TechLead viết script test 50 prompt + chạy BM25 với tokenizer mặc định
**THEN** đo recall@5 trên 50 prompt
**AND** nếu recall < 75% → thử custom tokenizer split `_` + camelCase
**AND** kết quả + recommendation viết vào `specs/spike-rt1-result.md`

**Acceptance:** Có file kết quả + recommendation cho M2, dù recall pass hay fail.

---

### US-M1-13 — Unit test ≥ 80% coverage
**FR:** N/A · **Task:** MEM-M1-13 · **SP:** 1 · **Persona:** Tester

**Story:** Là Tester, tôi muốn `pytest --cov=knowledge_memory.verticals.codebase` đạt ≥ 80% coverage trên 3 fixture.

**Acceptance:** CI pipeline xanh, coverage report attach vào PR M1 cuối cùng.

---

### US-M1-14 — Dogfood HC + CTO subjective gate
**FR:** N/A · **Task:** MEM-M1-14 · **SP:** 1 · **Persona:** P1

**Story:** Là CTO Hùng, tôi muốn chạy bootstrap trên HC backend production snapshot và review patterns + quick-wins, để approve sprint M1.

**Acceptance template (5 tiêu chí × 4 điểm = max 20):**
1. Pattern quality (≥ 5 pattern đúng)
2. Quick wins accuracy (≥ 8/10)
3. Performance (≤ 5 min on 80K LOC)
4. Code quality (linter pass, no shortcut hack)
5. KMP discipline (zero Core ↛ Vertical violation)

**Pass:** Tổng ≥ 15/20.

---

## 5. Tổng kết Sprint M0 + M1

| Sprint | Stories | SP |
|--------|:------:|:--:|
| M0 — Core Skeleton | 6 | 6 |
| M1 — Codebase Vault + Quick Win | 14 | 26 |
| **Tổng** | **20** | **32** |

---

## 6. Hằng số chia sẻ

```python
# knowledge_memory/core/constants.py
MIN_PATTERN_CONFIDENCE = 60       # %
MIN_EVIDENCE_COUNT = 5
MAX_EVIDENCE_PER_PATTERN = 20
MAX_SNAPSHOTS_KEPT = 5
BOOTSTRAP_HARD_TIMEOUT_SEC = 600
QUICK_WIN_TARGET_TIME_SEC = 300
LARGE_CODEBASE_LOC = 100_000
CTO_GATE_PASS_THRESHOLD = 15      # /20
```

---

## 7. Câu hỏi mở cho CEO

1. CTO subjective gate template ở US-M1-14 có chấp nhận không?
2. Hello vertical có ship cùng v1.0 release hay tách riêng?
3. Naming learner có cần tokenizer tiếng Việt riêng không (sẽ biết sau spike R-T1)?

---

*M0 + M1 User Stories v2.0 — KMP-aligned · @BA · 07/04/2026*
