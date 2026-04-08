# FDD v2.0 — Codebase Memory (as first vertical of KMP)
> **Project:** Codebase Memory · **Hệ sinh thái:** Knowledge Memory Platform
> **Authors:** @CTO + @BA · **Reviewers:** @PO @PM @TechLead
> **Version:** 2.0 (rewrite from v1.1 sau khi CEO chốt hướng B+ Knowledge OS)
> **Ngày:** 07/04/2026
> **Liên quan:** `kmp-architecture.md`, `memory-cto-feasibility.md`, `memory-po-ba-review.md`

---

## 0. Document Control

| Field | Value |
|-------|-------|
| Status | **Approved by CEO** (07/04/2026, hướng B+) |
| Total SP | **97 SP** (tăng từ 90 do thêm M0 + abstraction discipline) |
| Timeline | **9 tuần** (M0: 1 tuần + M1-M4: 8 tuần) |
| Resource | 1 TechLead full-time + 1 contractor part-time (Tuần 4-9) |
| Predecessor | `memory-fdd.md` v1.1 (deprecated) |

**Thay đổi chính so với v1.1:**
1. Codebase Memory được **redefine** là vertical đầu tiên của KMP, không phải standalone product
2. Package layout đổi sang `knowledge_memory/core/` + `knowledge_memory/verticals/codebase/`
3. Thêm **Sprint M0** (1 tuần, 6 SP) để build KMP Core skeleton + abstraction
4. 4 mitigation R-T1→R-T4 **giữ nguyên 100%**
5. 3 điều chỉnh từ Addendum v1.1 (Quick Win, Multi-LLM, Insights) **giữ nguyên**, chỉ chuyển sang dùng Core abstraction
6. Thêm dependency rule: Core ↛ Vertical, enforce qua import-linter

---

## 1. Executive Summary

Codebase Memory v2.0 là **vertical Codebase đầu tiên của Knowledge Memory Platform** — phục vụ pain "legacy codebase + AI coding adoption" cho SME Việt Nam. Sản phẩm bán theo model:

- **KMP Core:** Free, MIT, OSS — kéo cộng đồng
- **Codebase Memory Free:** Solo tier, không giới hạn project size
- **Codebase Memory Team Legacy:** 990K/tháng — multi-machine, drift dashboard
- **Codebase Memory Business:** 4.9M/tháng — pattern library export, white-label

Sản phẩm được build trên **kiến trúc Knowledge Memory Platform** (xem `kmp-architecture.md`) — đảm bảo khi mở vertical thứ 2 (Legal Memory) chỉ tốn ~75 SP thay vì 90 SP build từ 0.

**Mục tiêu MVP (9 tuần):**
- Vault local-first chạy trên 100K LOC ≤ 5 phút
- AI Ask qua MCP, hỗ trợ 3 LLM provider, recall ≥ 75%
- Onboarding tour sinh tự động cho dev mới
- Drift dashboard + License + Landing
- 5 design partner đầu tiên

---

## 2. Competitor Analysis (giữ nguyên từ v1.1)

Xem v1.1 mục 2. Bổ sung 1 insight sau review:

**Insight mới:** Không có competitor nào hiện tại có **plugin architecture** kiểu KMP. Tất cả đều build single-purpose tool. Đây là moat kiến trúc dài hạn — sau 12 tháng KMP có 3-5 vertical, đối thủ không thể catch-up trong < 18 tháng vì phải refactor toàn bộ codebase.

---

## 3. Functional Requirements (mapped to Core abstraction)

### 3.1 Module M0: KMP Core Skeleton (NEW)

| ID | Mô tả | Acceptance |
|----|------|-----------|
| FR-M0-01 | Package `knowledge_memory.core` với 8 sub-package (vault, learners, parsers, ai, mcp, licensing, cli, telemetry) | Import OK, không có vertical-specific code |
| FR-M0-02 | Abstract base class: `BaseVault`, `BaseLearner`, `BaseParser`, `LLMProvider`, `BaseMCPTool`, `BaseCLI` | Mypy strict pass |
| FR-M0-03 | `LearnerRuntime` orchestrate ≥ 1 mock learner | Unit test pass |
| FR-M0-04 | Import-linter CI rule "Core ↛ Vertical" | CI fail nếu vi phạm |
| FR-M0-05 | Reference vertical "hello" ≤ 50 LOC chạy được end-to-end | `hello-memory init && hello-memory bootstrap` sinh patterns.md |
| FR-M0-06 | KMP Architecture doc (`kmp-architecture.md`) được CTO approve | Sign-off mục 9 |

### 3.2 Module M1: Codebase Vault Foundation + Quick Win

(Thay cho M1 v1.1, refactor để dùng Core abstraction)

| ID | Mô tả | Map to Core |
|----|------|------------|
| FR-M1-01 | `CodebaseVault(BaseVault)` init `.knowledge-memory/verticals/codebase/` | core.vault.BaseVault |
| FR-M1-02 | `PythonASTParser(BaseParser)` parse Python AST → Evidence | core.parsers.BaseParser |
| FR-M1-03 | `NamingLearner`, `LayerLearner`, `GitOwnershipLearner(BaseLearner)` | core.learners.BaseLearner |
| FR-M1-04 | Patterns.md generator dùng `vault.commit_pattern()` | core.vault.commit_pattern |
| FR-M1-05 | Quick Win Mode `bootstrap` ≤ 5 phút (Addendum v1.1 giữ nguyên) | core.cli.BaseCLI.cmd_bootstrap |
| FR-M1-06 | Quick wins generator 10 insight | vertical-specific |
| FR-M1-07 | CLI summary với rich output | core.cli.formatter |

### 3.3 Module M2: Ask + MCP + Multi-LLM

| ID | Mô tả | Map to Core |
|----|------|------------|
| FR-M2-01 | `AnthropicProvider`, `OpenAIProvider`, `GeminiProvider(LLMProvider)` | core.ai.providers |
| FR-M2-02 | RAG: BM25 + AST graph proximity (recall ≥ 75% trên 3 provider) | core.ai.rag |
| FR-M2-03 | Context builder < 200ms | core.ai.context_builder |
| FR-M2-04 | Cost calculator per provider | core.ai.cost |
| FR-M2-05 | `commands/ask.py`, `commands/why.py`, `commands/impact.py` | vertical CLI |
| FR-M2-06 | MCP server bootstrap với registry pattern | core.mcp.server |
| FR-M2-07 | 4 MCP tool: `find_function`, `explain_module`, `pattern_check`, `impact` đăng ký qua `@register_tool` | core.mcp.registry |
| FR-M2-08 | MCP adapter wrap Anthropic SDK (R-T3 mitigation) | core.mcp.adapter |

### 3.4 Module M3: Onboarding + Polish + Insights

| ID | Mô tả | Map to Core |
|----|------|------------|
| FR-M3-01 | `commands/onboard.py` + Jinja2 template | vertical CLI |
| FR-M3-02 | 8-chapter onboarding template | vertical assets |
| FR-M3-03 | 3 learner còn lại: `error_handling`, `dependency_injection`, `test_patterns` | core.learners.BaseLearner |
| FR-M3-04 | `vault/glossary.py` business term extractor | vertical-specific |
| FR-M3-05 | Insights Dashboard `vault/insights.html` (Addendum v1.1) | core.telemetry + vertical exporter |
| FR-M3-06 | Telemetry local-only `usage_log` + `roi_metrics` table | core.telemetry |
| FR-M3-07 | `commands/insights.py` weekly report | vertical CLI |

### 3.5 Module M4: Drift + License + Launch

| ID | Mô tả | Map to Core |
|----|------|------------|
| FR-M4-01 | `commands/drift.py` violation scanner | vertical CLI |
| FR-M4-02 | Drift dashboard HTML | vertical exporter |
| FR-M4-03 | License verify offline (Ed25519) reuse từ Core | core.licensing |
| FR-M4-04 | CLI `activate`, `license info`, `deactivate` | core.cli.BaseCLI |
| FR-M4-05 | Pyarmor obfuscate Pro features (R-T4 matrix test) | tools/build |
| FR-M4-06 | Landing page `codebase.agentwork.vn` | external |
| FR-M4-07 | Email + payment integration | external |
| FR-M4-08 | Documentation + getting started PDF | external |
| FR-M4-09 | Soft launch 5 design partner | external |

---

## 4. Non-Functional Requirements (giữ nguyên v1.1)

Xem v1.1 mục 4. Bổ sung 3 NFR mới cho KMP:

- **NFR-KMP-01:** Core không bao giờ import vertical (enforce CI)
- **NFR-KMP-02:** Vertical mới phải build được trong ≤ 1200 LOC tổng cộng
- **NFR-KMP-03:** Hello vertical phải pass end-to-end test mỗi PR

---

## 5. System Architecture

Xem `kmp-architecture.md` chi tiết. Tóm tắt:

- 6 core service: Vault, Learner Runtime, AI Gateway, MCP Hub, Licensing, CLI Framework
- Codebase = vertical trong `verticals/codebase/`
- Hello = reference vertical trong `verticals/hello/` (50 LOC, ship cùng v1.0 như tutorial)

---

## 6. Build Plan — Sprint M0 → M4

### Sprint M0 — KMP Core Skeleton (Tuần 0, 6 SP)

| Task | SP | Owner |
|------|:--:|------|
| KMP-M0-01: Package skeleton | 1 | TechLead |
| KMP-M0-02: Abstract base classes + dataclass | 2 | TechLead |
| KMP-M0-03: LearnerRuntime | 1 | TechLead |
| KMP-M0-04: Import-linter CI | 0.5 | TechLead |
| KMP-M0-05: Hello vertical 50 LOC | 1 | TechLead |
| KMP-M0-06: CTO sign-off | 0.5 | CTO |
| **Tổng** | **6** | |

### Sprint M1 — Codebase Vault + Quick Win (Tuần 1-2, 26 SP)

| Task | SP | Owner |
|------|:--:|------|
| MEM-M1-01: `CodebaseVault(BaseVault)` | 2 | TechLead |
| MEM-M1-02: `PythonASTParser(BaseParser)` (port từ codebase-map) | 2 | TechLead |
| MEM-M1-03: `vault/snapshots.py` + hook | 2 | TechLead |
| MEM-M1-04: SQLite schema_extension cho codebase | 2 | TechLead |
| MEM-M1-05: `NamingLearner(BaseLearner)` | 2 | TechLead |
| MEM-M1-06: `LayerLearner` | 2 | TechLead |
| MEM-M1-07: `GitOwnershipLearner` | 2 | TechLead |
| MEM-M1-08: `patterns.py` generator | 2 | TechLead |
| MEM-M1-09: `commands/bootstrap.py` orchestrator | 2 | TechLead |
| MEM-M1-10: `quick_wins.py` 10 insight generator | 3 | TechLead |
| MEM-M1-11: CLI summary formatter | 1 | TechLead |
| MEM-M1-12: Spike R-T1 BM25 tiếng Việt validation | 2 | TechLead |
| MEM-M1-13: Unit test (coverage ≥ 80%) | 1 | Tester |
| MEM-M1-14: Dogfood HC + CTO subjective gate | 1 | CTO |
| **Tổng** | **26** | |

(Tăng 1 SP so với v1.1 do thêm spike R-T1)

### Sprint M2 — Ask + MCP + Multi-LLM (Tuần 3-4, 28 SP)

| Task | SP | Owner |
|------|:--:|------|
| MEM-M2-01: `AnthropicProvider` | 1 | TechLead |
| MEM-M2-02: `ai/rag.py` BM25 + graph proximity (R-T1 fix nếu cần) | 5 | TechLead |
| MEM-M2-03: `ai/context_builder.py` | 2 | TechLead |
| MEM-M2-04: `commands/ask.py` | 2 | TechLead |
| MEM-M2-05: `commands/why.py` | 2 | TechLead |
| MEM-M2-06: `commands/impact.py` | 2 | TechLead |
| MEM-M2-07: `mcp/adapter.py` wrap SDK (R-T3) | 1 | TechLead |
| MEM-M2-08: `mcp/server.py` + 4 tool đăng ký registry | 4 | TechLead |
| MEM-M2-09: `OpenAIProvider` | 2 | Contractor |
| MEM-M2-10: `GeminiProvider` | 2 | Contractor |
| MEM-M2-11: Cost calculator + cross-provider test | 1 | Tester |
| MEM-M2-12: E2E test với Cursor + Claude Code | 2 | Tester |
| MEM-M2-13: Pattern threshold tune (R-T2) | 2 | TechLead |
| **Tổng** | **28** | |

(Tăng 1 SP so với v1.1 do RAG under-estimate, dời dogfood sang M3)

### Sprint M3 — Onboarding + Polish + Insights (Tuần 5-6, 21 SP)

| Task | SP | Owner |
|------|:--:|------|
| MEM-M3-01: `commands/onboard.py` + Jinja2 | 3 | TechLead |
| MEM-M3-02: 8-chapter template | 2 | BA + Designer |
| MEM-M3-03: Mermaid integration | 1 | TechLead |
| MEM-M3-04: `error_handling` learner | 2 | TechLead |
| MEM-M3-05: `dependency_injection` learner | 2 | TechLead |
| MEM-M3-06: `test_patterns` learner | 1 | TechLead |
| MEM-M3-07: `glossary.py` extractor | 2 | TechLead |
| MEM-M3-08: `core/telemetry/logger.py` (move từ vertical) | 1 | TechLead |
| MEM-M3-09: `roi_calculator.py` | 1 | Contractor |
| MEM-M3-10: `insights_html.py` dashboard | 2 | Contractor + Designer |
| MEM-M3-11: `commands/insights.py` | 1 | Contractor |
| MEM-M3-12: Dogfood HC + CTO gate (dời từ M2) | 1 | All |
| MEM-M3-13: Tester regression M1 + M2 | 2 | Tester |
| **Tổng** | **21** | |

### Sprint M4 — Drift + License + Launch (Tuần 7-8, 18 SP)

(Giữ nguyên v1.1 — bổ sung pyarmor Python matrix test cho R-T4)

| Task | SP | Owner |
|------|:--:|------|
| MEM-M4-01: `commands/drift.py` | 3 | TechLead |
| MEM-M4-02: `exporters/drift_html.py` | 3 | Designer + TechLead |
| MEM-M4-03: License Core integration | 1 | TechLead |
| MEM-M4-04: CLI activate/info/deactivate | 1 | TechLead |
| MEM-M4-05: pyarmor + Python 3.10-3.13 matrix test (R-T4) | 2 | TechLead |
| MEM-M4-06: Landing codebase.agentwork.vn | 3 | Contractor + Designer |
| MEM-M4-07: Email + payment | 2 | TechLead |
| MEM-M4-08: Docs + getting started PDF | 2 | Contractor + BA |
| MEM-M4-09: Soft launch 5 design partner | 1 | CEO |
| **Tổng** | **18** | |

### Tổng MVP

| Sprint | SP | Tuần |
|--------|:--:|:----:|
| M0 KMP Core Skeleton | 6 | 1 |
| M1 Codebase Vault + Quick Win | 26 | 2 |
| M2 Ask + MCP + Multi-LLM | 28 | 2 |
| M3 Onboarding + Insights | 21 | 2 |
| M4 Drift + License + Launch | 18 | 2 |
| **Tổng** | **99** | **9** |

So với v1.1: 90 SP / 8 tuần → 99 SP / 9 tuần. **Tăng 9 SP / 1 tuần** đầu tư cho abstraction. Khoản đầu tư này tiết kiệm ~25 SP refactor về sau khi build vertical thứ 2.

---

## 7. Risk Register (cập nhật)

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|:----------:|:------:|------------|
| R-T1 | BM25 chưa validate tiếng Việt | Cao | Cao | Spike MEM-M1-12 Tuần 1 |
| R-T2 | Pattern threshold 60% chưa validate | Trung | Cao | MEM-M2-13 tune theo 3 codebase |
| R-T3 | MCP protocol breaking change | Trung | Trung | MEM-M2-07 wrap adapter |
| R-T4 | Pyarmor break Python 3.13+ | Trung | Cao | MEM-M4-05 matrix test |
| R-T5 | Over-engineering abstraction | Trung | Trung | CTO review mỗi PR M0-M1 |
| R-T6 | Hello vertical không pass test | Thấp | Cao | KMP-M0-05 phải xanh trước M1 |
| R-06 | TechLead bottleneck | Cao | Cao | Tuyển contractor Tuần 3 |
| R-08 | Multi-LLM bug surface | Trung | Trung | Cross-provider test suite |
| R-09 | Telemetry hiểu lầm spy | Thấp | Cao | Local-only, blog privacy |
| R-10 | Quick Win sinh insight sai | Trung | Cao | Confidence ≥ 60%, [needs review] flag |

---

## 8. Definition of Done v2.0

Ngoài DoD v1.1, thêm:

- [ ] M0 hoàn thành: Hello vertical chạy end-to-end ≤ 50 LOC
- [ ] Import-linter CI rule pass mọi commit
- [ ] Codebase vertical chỉ implement abstract base, không bypass
- [ ] KMP Core có ≥ 80% test coverage
- [ ] Architecture doc `kmp-architecture.md` được sign-off
- [ ] 5 open decision D-1 → D-5 trong KMP arch doc đã có CEO answer

---

## 9. Sign-off

| Vai trò | Trạng thái | Ghi chú |
|---------|:----------:|---------|
| CTO | ✅ Approve | "Kiến trúc đúng cho 24 tháng tới" |
| BA | ✅ Approve | "User story map sạch sẽ" |
| PO | ✅ Approve | "Không hy sinh time-to-market quá nhiều cho future-proofing" |
| PM | ✅ Approve | "Tuyển contractor Tuần 3 là path khả thi" |
| CEO | ✅ Approved 07/04/2026 | Hướng B+ |

---

*FDD v2.0 — Codebase Memory as KMP Vertical · Co-authored by @CTO + @BA · 07/04/2026*
