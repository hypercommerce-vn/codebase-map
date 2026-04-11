# @CTO Review — Proposal Dual-Snapshot Lifecycle (CBM-01 / CBM-02)
> **Reviewer:** @CTO · **Date:** 10/04/2026 · **Document reviewed:** `Proposal_Dual_Snapshot_CBM.md`
> **Verdict:** ✅ **APPROVE with modifications** — feature xứng đáng, cần điều chỉnh triển khai

---

## 1. ĐÁNH GIÁ TỔNG (Scorecard)

| Tiêu chí | Score | Comment |
|----------|:-----:|---------|
| Business value | **9/10** | CEO insight từ thực tế 4 PRs — giải quyết pain point rõ ràng |
| Technical feasibility | **8/10** | Phần lớn dựa trên code có sẵn (graph models + diff engine). Rename detection là phần khó nhất |
| Architecture fit | **8/10** | Tương thích tốt với codebase-map v2.0.1 hiện tại. Metadata đáng lẽ nên có từ đầu |
| Spec quality | **9/10** | BA + CTO draft rất chi tiết: FR/NFR/BR, process flow, edge cases, competitive analysis — ít proposal nào đầy đủ thế này |
| Effort estimate | **7/10** | 24 SP hơi optimistic cho rename detection + lifecycle commands. Em estimate lại bên dưới |
| KMP interaction | **7/10** | Cần clarify ranh giới giữa CBM (standalone) vs KMP Codebase Vault (M1). Xem section 4 |

**Tổng: 48/60 (80%)** — Proposal solid, insight hay, chỉ cần điều chỉnh scope + timeline.

---

## 2. PHÂN TÍCH KỸ THUẬT

### 2.1 Điểm mạnh — Những cái proposal đã đúng

**A. Graph metadata (FR-001)** — Đây đáng lẽ phải có từ v1.0. Hiện tại `graph.json` chỉ chứa `nodes` + `edges`, không có timestamp, commit SHA, branch. Thêm metadata là **zero-risk, high-reward**.

**B. Code sẵn có để tận dụng:**
- `codebase_map/graph/diff.py` — DiffAnalyzer đã tồn tại (CM-S2-01), so sánh git diff + impacted nodes. Mở rộng để so sánh 2 graph files là natural extension.
- `graph.to_dict()` / `export_json()` — cấu trúc rõ ràng, thêm metadata header chỉ cần modify 2 chỗ.
- `cli.py` đã có `_cmd_diff()` — extend thêm flags (`--baseline`, `--breaking-only`, `--format markdown`) không khó.

**C. Competitive whitespace thật:**
- Proposal đúng: không tool nào (Madge, pydeps, Sourcegraph) cung cấp function-level dual-snapshot diff.
- Kết hợp với KMP competitor research (Cursor, Aider): chúng chỉ có retrieval/chat, không có lifecycle diff. **Đây là moat thêm cho codebase-map.**

**D. NFR-006 (Language agnostic diff)** — Critical insight. Diff engine so sánh graph structure (nodes + edges), không parse source code → hỗ trợ Python + TypeScript + future languages ngay.

### 2.2 Điểm cần điều chỉnh

**A. Rename detection (FR-018) — phức tạp hơn proposal mô tả:**

Proposal nói: "cùng function name + ≥80% body match + khác file path = rename". Nhưng:
- Cần tính body similarity → phải lưu body hash/content trong graph. Hiện `Node` dataclass **không có body field**.
- Thêm body content vào graph sẽ **tăng file size đáng kể** (vi phạm NFR-003: <5MB cho 10K functions).
- **Đề xuất CTO:** Dùng **signature-based matching** (function name + params + return type) thay vì body matching cho v2.x. Body matching (AST) để cho v3.0 khi có KMP Codebase Vault (lưu evidence trong SQLite, không bị file size constraint).

**B. Lifecycle commands (FR-020→024) — over-engineering cho v2.x:**

`lifecycle start --task "P2-S5-05"` yêu cầu:
- State management (biết task nào đang active)
- Workspace concept (baseline linked to task)
- Clean up logic

Đây chính xác là scope của **KMP Codebase Vault** (M1-M2). Nếu build trong codebase-map standalone → sẽ phải duplicate khi migrate sang KMP.

**Đề xuất CTO:** Phase 3 (lifecycle commands) **KHÔNG build trong codebase-map**. Dời sang KMP M2-M3 sau khi Vault infrastructure sẵn sàng. Giữ codebase-map lean.

**C. CI integration (FR-030→033) — scope nên thu hẹp:**

CI auto-commit graph file vào repo (FR-031) có side effect: mỗi merge tạo thêm 1 commit → commit history dài. Ở HC team nhỏ OK, nhưng teams lớn sẽ complain.

**Đề xuất CTO:** CI generate graph → **save as GitHub Actions artifact** (default), option `--commit-to-repo` cho team muốn git-tracked. Staleness check (FR-033) giữ nguyên — hay.

### 2.3 Effort re-estimate (CTO adjusted)

| Phase | Proposal SP | CTO estimate | Delta | Lý do |
|-------|:----------:|:------------:|:-----:|------|
| Phase 1: Metadata + Snapshot Save | 6 | **7** | +1 | Thêm backward compat migration cho graph v1.x → v2.0 |
| Phase 2: Dual-Snapshot Diff | 10 | **12** | +2 | Rename detection phức tạp hơn + edge case parallel PRs |
| Phase 3: Lifecycle | 8 | **0** (dời sang KMP) | -8 | Tránh duplicate effort |
| **Total** | **24** | **19** | **-5** | Lean hơn, focus vào core value |

---

## 3. TRẢ LỜI 6 OPEN QUESTIONS

| # | Question | @CTO Answer | Rationale |
|---|---------|-------------|-----------|
| **1** | Snapshot storage: repo hay external? | **GitHub Actions artifact (default)** + option `--commit-to-repo` | Artifact không bloat repo, auto-expire 90 ngày. Team nhỏ muốn git-tracked thì opt-in |
| **2** | Rename detection: AST hay text similarity? | **Signature matching (name + params + return_type)** cho v2.x. AST body match cho v3.0/KMP | Không cần lưu body trong graph → giữ file size nhỏ |
| **3** | Transitive caller depth: 1 hay configurable? | **Default 1, flag `--depth N` max 3** | ≥4 cấp quá nhiều noise. Proposal nói đúng: 1 cấp là sweet spot |
| **4** | Graph format: JSON hay SQLite? | **JSON cho codebase-map v2.x** (git-friendly, simple). SQLite sẽ dùng trong KMP Codebase Vault | Codebase-map là CLI tool nhẹ. SQLite cho KMP engine |
| **5** | CI: GitHub Actions only hay GitLab CI? | **GitHub Actions Phase 1**, GitLab CI **community contribution** | Team mình dùng GitHub. GitLab CI = Dockerfile mẫu, community tự adapt |
| **6** | Pricing: free hay paid? | **100% free** — dual-snapshot là core differentiator, phải open để grow adoption. Paid features nằm trong KMP (pattern learner, insights, drift detection) | Codebase-map = free OSS → kéo user → upsell KMP Memory |

---

## 4. TƯƠNG TÁC VỚI KMP PHASE 2

Đây là câu hỏi quan trọng nhất: **build ở đâu?**

### 4.1 Ranh giới rõ ràng

```
CODEBASE-MAP (standalone, free, OSS)        KMP (platform, freemium)
─────────────────────────────────────       ─────────────────────────
✅ Graph generate (AST parse → nodes/edges)  ✅ Vault (SQLite + Markdown)
✅ Graph metadata + versioning  (NEW)         ✅ Pattern Learner + Confidence
✅ Dual-snapshot diff (NEW)                   ✅ Ask + MCP + Multi-LLM
✅ CLI query/impact/search/api-catalog        ✅ Drift detection
✅ HTML interactive viewer                    ✅ Insights dashboard
✅ CI integration                             ✅ Lifecycle commands (state mgmt)
✅ Markdown PR impact block (NEW)             ✅ Export formats
                                              ✅ Licensing + Pro features
```

**Nguyên tắc:** Codebase-map = **stateless graph tool** (generate, diff, query). KMP = **stateful knowledge engine** (vault, patterns, learning). **Lifecycle commands (FR-020→024) thuộc về KMP**, không build trong codebase-map.

### 4.2 Cầu nối CBM → KMP

Sau khi launch dual-snapshot trong codebase-map:
- KMP Codebase Vault (M1) sẽ **import graph file** từ codebase-map làm input cho parser
- KMP dùng snapshot metadata (commit SHA, timestamp) để track vault history
- KMP `lifecycle` commands gọi `codebase-map generate` internally → tạo snapshot → so sánh trong vault context

**→ Codebase-map là "data generator", KMP là "intelligence layer".**

### 4.3 Timing recommendation

```
Timeline:
─────────────────────────────────────────────────────────────────
NOW          KMP M1 active (Vault + Parser)
             │
Week 3       KMP M1 done → CBM Dual-Snapshot Phase 1 start
             │                    (7 SP, 1 week — metadata + save)
Week 4       CBM Phase 1 done → Phase 2 start
             │                    (12 SP, 2 weeks — diff engine)
             │
             KMP M2 start (Ask + MCP) — parallel track
             │
Week 6       CBM Phase 2 done → shipped as codebase-map v2.1
             │
             KMP M2 continues...
Week 9       KMP M3 (lifecycle commands dùng CBM diff engine)
─────────────────────────────────────────────────────────────────
```

**Không block KMP M1.** CBM Dual-Snapshot Phase 1+2 chạy **parallel hoặc sequentially** sau M1 xong, trước M2 kết thúc.

---

## 5. PHƯƠNG ÁN TRIỂN KHAI (CTO RECOMMENDED)

### 5.1 Scope adjusted: 2 phases (not 3)

**Phase 1 — Graph Metadata + Snapshot Versioning (7 SP, 1 tuần)**

| Task ID | Task | SP | Notes |
|---------|------|----|-------|
| CBM-P1-01 | Add `metadata` dict to `Graph` dataclass + `to_dict()` | 1 | `generated_at`, `commit_sha`, `branch`, `label`, `stats` |
| CBM-P1-02 | `generate --label <name>` CLI flag | 1 | Default: `auto` (branch_shortsha_timestamp) |
| CBM-P1-03 | Snapshot naming: `graph_{label}_{short_sha}.json` | 1 | Store in `.codebase-map-cache/snapshots/` |
| CBM-P1-04 | `snapshots list` command | 1 | Table: label, date, branch, sha, nodes/edges count |
| CBM-P1-05 | `snapshots clean --keep N` | 0.5 | Default keep 10 |
| CBM-P1-06 | Backward compat: read graph v1.x (no metadata) → inject empty metadata | 1 | NFR-004 critical |
| CBM-P1-07 | CI workflow: auto-generate baseline after merge + artifact upload | 1.5 | GitHub Actions reusable workflow |
| **Total** | | **7** | |

**Phase 2 — Dual-Snapshot Diff Engine (12 SP, 2 tuần)**

| Task ID | Task | SP | Notes |
|---------|------|----|-------|
| CBM-P2-01 | `SnapshotDiff` class: load 2 graphs → compute node diff (added/removed/modified) | 3 | Core engine |
| CBM-P2-02 | Edge diff: new/removed caller relationships | 2 | Cross-reference node diff |
| CBM-P2-03 | Affected callers: transitive 1-level (default), `--depth N` max 3 | 2 | Key Tester value |
| CBM-P2-04 | Rename detection: signature matching (name + params + return_type, same content → rename) | 2 | V2.x approach, AST body match defer to v3/KMP |
| CBM-P2-05 | `--format markdown` output (PR Impact block) | 1 | Paste-ready cho PR body |
| CBM-P2-06 | `--format json` output | 0.5 | Machine-readable |
| CBM-P2-07 | `--breaking-only` filter (functions bị remove/modify có callers) | 0.5 | CTO review focus |
| CBM-P2-08 | `--test-plan` output (affected callers grouped by domain) | 1 | Tester value-add |
| **Total** | | **12** | |

**Phase 3 (lifecycle commands) → DEFERRED to KMP M3** — không build trong codebase-map.

### 5.2 Versioning

- Phase 1 ship = **codebase-map v2.1.0**
- Phase 2 ship = **codebase-map v2.2.0**
- Lifecycle commands = **KMP Codebase Memory M3** (không phải codebase-map release)

### 5.3 Risk assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|:----------:|-----------|
| Rename detection false positive | Medium | Medium | Signature matching conservative (exact name + params). Nếu ambiguous → report as "possible rename" thay vì tự quyết |
| Graph v1.x backward compat break | High | Low | CBM-P1-06 xử lý explicitly, có test suite cho old format |
| Diff performance trên large graph | Medium | Low | NFR-002 target <5s cho 10K functions. Dict lookup O(1), không cần optimize sớm |
| Scope creep vào lifecycle commands | Medium | Medium | **Hard boundary:** codebase-map = stateless. Nếu cần state → đó là KMP scope |

---

## 6. TÓM TẮT QUYẾT ĐỊNH CẦN CEO

| # | Question | @CTO Recommendation |
|---|---------|-------------------|
| **1** | Approve proposal? | ✅ **Yes, with 3 modifications:** (a) Phase 3 defer to KMP, (b) rename detection = signature matching (not body), (c) CI artifact default thay vì commit-to-repo |
| **2** | Timeline? | Phase 1 (7 SP, 1w) + Phase 2 (12 SP, 2w) = **19 SP / 3 tuần** · Start sau KMP M1 done hoặc parallel |
| **3** | Pricing? | **100% free** — dual-snapshot là core differentiator của codebase-map OSS |
| **4** | Ai implement? | TechLead (cùng người đang làm KMP) — vì cần hiểu cả 2 codebase |
| **5** | Release as? | codebase-map **v2.1** (Phase 1) + **v2.2** (Phase 2) |
| **6** | KMP interaction? | Codebase-map = data generator (stateless). KMP = intelligence layer (stateful). Lifecycle commands ở KMP M3 |

---

*CTO Review — Dual-Snapshot Proposal · 10/04/2026 · @CTO*
