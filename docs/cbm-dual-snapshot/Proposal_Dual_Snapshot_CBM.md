# Proposal + FDD: Dual-Snapshot Lifecycle (CBM-01 / CBM-02)

> **Product:** Codebase-Map — Function Dependency Graph Generator
> **Authors:** CTO + BA — Hyper Commerce
> **Date:** 2026-04-10
> **Status:** Draft — Pending dev team review
> **Origin:** CEO insight từ thực tế sử dụng tại HC Sprint 5

---

## 1. EXECUTIVE SUMMARY

### Vấn đề hiện tại

Codebase-map hiện tại chỉ tạo **1 snapshot duy nhất** (`graph.json`) tại một thời điểm. Trong thực tế phát triển phần mềm, mỗi PR/task cần **2 snapshot khác nhau** ở 2 giai đoạn:

| Giai đoạn | Snapshot | Ai dùng | Mục đích |
|-----------|----------|---------|----------|
| **Planning** | CBM-01 (Baseline) | Dev / TechLead | Hiểu architecture hiện tại → lập chiến lược implement |
| **Review & Test** | CBM-02 (Post-dev) | CTO / Tester | Đánh giá impact thực tế → review + test chính xác |

### Tại sao quan trọng

Insight này đến từ CEO sau 4 PRs thực tế (PR #96–#99) tại Hyper Commerce:

- **PR #98:** Dev dùng CBM-01 query `AlertDispatcher` → biết chỉ có 2 channels → quyết định extend (không tạo mới). Sau khi dev xong, Tester dùng CBM-02 → phát hiện `alerting.py` modified → chạy test cũ → **catch regression** (`len(AlertChannel) == 2` → phải là 3).
- **Nếu chỉ có CBM-01:** Tester không biết `alerting.py` bị modify → miss regression.
- **Nếu chỉ có CBM-02:** Dev không biết architecture hiện tại → có thể duplicate code.

### Giá trị đề xuất

Codebase-map trở thành **công cụ lifecycle** thay vì chỉ là **snapshot tool**:

```
Snapshot tool:      "Codebase trông như thế nào?"
Lifecycle tool:     "Codebase đã thay đổi gì, ảnh hưởng gì, so với trước?"
```

---

## 2. PROBLEM ANALYSIS (BA)

### 2.1 Current State — Quy trình hiện tại (AS-IS)

```
                    ┌──────────────────────────────────┐
                    │        codebase-map generate      │
                    │      Tạo 1 file graph.json        │
                    │    (snapshot tại thời điểm chạy)   │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │   Developer/CTO dùng graph.json   │
                    │   query / impact / api-catalog    │
                    │   KHÔNG BIẾT graph là version nào  │
                    └──────────────────────────────────┘
```

**Gaps:**
1. Không phân biệt graph "trước khi dev" vs "sau khi dev"
2. Không so sánh 2 versions → không biết code thay đổi gì
3. `codebase-map diff` hiện chỉ so sánh git diff, không so sánh 2 graph files
4. Không có metadata (timestamp, branch, commit SHA) gắn vào graph
5. Khi graph bị overwrite, mất baseline → không rollback được

### 2.2 Desired State — Quy trình mong muốn (TO-BE)

```
PR (N-1) merged ──► CI generate ──► CBM-01 (baseline)
                                        │
                                        ▼
                              ┌─── PLANNING ───┐
                              │ Dev đọc CBM-01  │
                              │ • query callers │
                              │ • understand    │
                              │   architecture  │
                              │ • plan strategy │
                              └────────┬────────┘
                                       │
                                 Dev implement
                                 Fix CI, iterate
                                 ...hoàn tất...
                                       │
                                       ▼
                              ┌─── REVIEW ─────┐
                              │ Generate CBM-02 │
                              │ (post-dev)      │
                              │                 │
                              │ • diff CBM-01   │
                              │   vs CBM-02     │
                              │ • blast radius  │
                              │ • new callers   │
                              │ • removed funcs │
                              │                 │
                              │ CTO: review     │
                              │ Tester: test    │
                              └────────┬────────┘
                                       │
                              CEO approve → Merge
                                       │
                                       ▼
                              CBM-02 ──► becomes CBM-01
                              cho PR tiếp theo
```

### 2.3 User Personas & Use Cases

#### Persona 1: Developer / TechLead (Planning phase)

**Goal:** Hiểu architecture hiện tại trước khi code

| Use Case | Input | Output | Value |
|----------|-------|--------|-------|
| UC-01: Khám phá module | `cbm query "AlertDispatcher" --snapshot baseline` | Callers, dependencies, call chain | Biết extend hay tạo mới |
| UC-02: Tìm API endpoints | `cbm api-catalog --snapshot baseline` | Danh sách routes hiện tại | Biết API nào đã có |
| UC-03: Check shared modules | `cbm query "channelApi" --snapshot baseline` | Tất cả files import channelApi | Biết sửa file nào sẽ ảnh hưởng ai |

#### Persona 2: CTO (Review phase)

**Goal:** Đánh giá chất lượng + blast radius của code mới

| Use Case | Input | Output | Value |
|----------|-------|--------|-------|
| UC-04: So sánh impact | `cbm diff --baseline CBM-01 --current CBM-02` | Added/removed/modified functions + callers | Blast radius thực tế |
| UC-05: Detect breaking changes | `cbm diff --breaking-only` | Functions bị xóa/đổi signature mà có callers | Catch regressions |
| UC-06: Generate PR Impact block | `cbm impact --format markdown --diff CBM-01 CBM-02` | Markdown table cho PR body | Standardized PR quality |

#### Persona 3: Tester / QA (Test phase)

**Goal:** Biết chính xác test scope từ code changes

| Use Case | Input | Output | Value |
|----------|-------|--------|-------|
| UC-07: Test plan từ diff | `cbm diff --test-plan` | Affected callers + downstream flows | Impact-driven test plan |
| UC-08: Regression scope | `cbm diff --callers-affected` | List functions bị ảnh hưởng gián tiếp | Biết test gì để tránh regression |

---

## 3. FUNCTIONAL REQUIREMENTS (BA + CTO)

### 3.1 Feature: Snapshot Versioning

> Graph file phải có metadata để phân biệt versions.

| FR-ID | Requirement | Priority | Notes |
|-------|------------|----------|-------|
| FR-001 | Graph file chứa metadata: `generated_at` (ISO 8601), `commit_sha`, `branch`, `version_label` | Must | Thêm vào `graph.json` header |
| FR-002 | Command `generate` accept `--label` flag để gắn nhãn (VD: `--label baseline`, `--label post-dev`) | Must | Default: auto-generate từ branch + timestamp |
| FR-003 | Graph files lưu với naming convention: `graph_{label}_{short_sha}.json` | Should | Tránh overwrite, giữ history |
| FR-004 | Command `snapshots list` liệt kê tất cả snapshots có sẵn | Should | Cho dev chọn đúng baseline |
| FR-005 | Config `max_snapshots` giới hạn số lượng snapshots lưu (default: 10) | Could | Tránh disk bloat |

**Data schema — Graph metadata:**

```json
{
  "metadata": {
    "version": "2.0",
    "generated_at": "2026-04-10T14:30:00+07:00",
    "commit_sha": "a7bd55e",
    "branch": "develop",
    "label": "baseline",
    "generator_version": "1.2.0",
    "source_paths": ["backend/app/", "frontend/src/"],
    "stats": {
      "total_functions": 847,
      "total_files": 234,
      "total_edges": 1523
    }
  },
  "nodes": [...],
  "edges": [...]
}
```

### 3.2 Feature: Dual-Snapshot Diff

> So sánh 2 graph snapshots → output thay đổi có ý nghĩa.

| FR-ID | Requirement | Priority | Notes |
|-------|------------|----------|-------|
| FR-010 | Command `diff <baseline> <current>` so sánh 2 graph files | Must | Core feature |
| FR-011 | Diff output gồm: functions added, removed, modified (signature change) | Must | |
| FR-012 | Diff output gồm: edges added, removed (caller relationships thay đổi) | Must | |
| FR-013 | Diff output gồm: affected callers (functions gọi đến function bị modify) | Must | Key value cho Tester |
| FR-014 | Flag `--breaking-only` chỉ hiện changes có callers bị ảnh hưởng | Should | CTO review focus |
| FR-015 | Flag `--format markdown` output markdown table cho PR body | Must | Integration với Rule #9 |
| FR-016 | Flag `--format json` output machine-readable diff | Should | CI/automation integration |
| FR-017 | Flag `--test-plan` output suggested test scope dựa trên affected callers | Could | Tester automation |
| FR-018 | Diff phải handle rename detection (function di chuyển file nhưng cùng signature) | Should | Tránh false positive "removed + added" |

**Output format — Diff report:**

```markdown
## Codebase-Map Diff: baseline → post-dev

**Baseline:** graph_baseline_a7bd55e.json (2026-04-10 10:00)
**Current:**  graph_post-dev_1207b8d.json (2026-04-10 14:30)

### Summary
| Metric | Count |
|--------|-------|
| Functions added | 12 |
| Functions removed | 3 |
| Functions modified | 5 |
| Edges added | 18 |
| Edges removed | 4 |
| Affected callers | 7 |

### Added Functions
| Function | File | Called by |
|----------|------|----------|
| `StepSelectChannel` | ChannelWizard/StepSelectChannel.tsx | ChannelWizard/index.tsx |
| `StepConfigure` | ChannelWizard/StepConfigure.tsx | ChannelWizard/index.tsx |
| ... | ... | ... |

### Removed Functions
| Function | File | Was called by (IMPACT) |
|----------|------|----------------------|
| `ConnectChannelModal` | channels/ChannelMgmtPage.tsx | ChannelMgmtPage (internal) |

### Modified Functions
| Function | File | Change | Affected callers |
|----------|------|--------|-----------------|
| `ChannelMgmtPage` | channels/ChannelMgmtPage.tsx | Removed ConnectChannelModal, added ChannelWizard | router.tsx (1 caller) |

### Affected Callers (Tester Focus)
| Caller | File | Reason |
|--------|------|--------|
| `router.tsx` | app/router.tsx | Imports ChannelMgmtPage (modified) |
```

### 3.3 Feature: Lifecycle Commands

> Convenience commands cho workflow Planning → Dev → Review.

| FR-ID | Requirement | Priority | Notes |
|-------|------------|----------|-------|
| FR-020 | `cbm snapshot save --label baseline` = generate + save với label | Should | Shortcut cho CI |
| FR-021 | `cbm snapshot save --label post-dev` = generate + save từ current code | Should | Dev gọi khi xong |
| FR-022 | `cbm lifecycle start --task "P2-S5-05"` = save baseline + tạo workspace | Could | Full lifecycle tracking |
| FR-023 | `cbm lifecycle review` = generate post-dev + auto diff vs baseline + output Impact block | Could | One-command review prep |
| FR-024 | `cbm snapshot clean --keep 5` = xóa snapshots cũ, giữ N mới nhất | Could | Maintenance |

### 3.4 Feature: CI Integration

> Auto-generate baseline sau mỗi merge.

| FR-ID | Requirement | Priority | Notes |
|-------|------------|----------|-------|
| FR-030 | CI workflow `generate --label baseline` chạy sau merge vào main/develop | Must | CBM-01 auto |
| FR-031 | CI commit graph file vào repo (hoặc artifact store) | Must | Dev có thể pull |
| FR-032 | CI skip nếu commit message chứa `[cbm skip]` | Must | Tránh loop |
| FR-033 | Staleness check: warn nếu baseline > 3 ngày, alert nếu > 7 ngày | Should | Governance |

---

## 4. BUSINESS RULES (BA)

| BR-ID | Rule | Rationale |
|-------|------|-----------|
| BR-001 | CBM-01 (baseline) chỉ được tạo từ code đã merge vào develop/main — KHÔNG từ feature branch | Source of truth phải là code chuẩn |
| BR-002 | CBM-02 (post-dev) được tạo từ feature branch khi dev báo "done" | Phản ánh code sẽ merge |
| BR-003 | Diff chỉ có ý nghĩa khi CBM-01 và CBM-02 cùng project config (`codebase-map.yaml`) | Tránh so sánh 2 projects khác nhau |
| BR-004 | "Affected callers" = functions gọi đến function bị modify/remove, tính transitive 1 cấp | 2+ cấp quá nhiều noise |
| BR-005 | Rename detection: cùng function name + ≥80% body match + khác file path = rename, không phải remove+add | Giảm false positive |
| BR-006 | Snapshot label phải unique trong project scope | Tránh overwrite nhầm |
| BR-007 | CBM-02 tự động trở thành CBM-01 của task tiếp theo sau khi PR merge | Lifecycle liên tục |

---

## 5. PROCESS FLOW (BA)

### 5.1 Full PR Lifecycle với Dual-Snapshot

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PR LIFECYCLE — DUAL SNAPSHOT                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐     CI auto-generate                              │
│  │ PR (N-1)     │────────────────────► CBM-01 saved                 │
│  │ merged       │                      (label: baseline)            │
│  └──────────────┘                      (branch: develop)            │
│                                        (sha: abc123)                │
│         │                                     │                     │
│         │                                     ▼                     │
│         │                           ┌──────────────────┐            │
│         │                           │  PLANNING PHASE  │            │
│         │                           │                  │            │
│         │                           │  Dev reads CBM-01│            │
│         │                           │  • query callers │            │
│         │                           │  • find deps     │            │
│         │                           │  • plan strategy │            │
│         │                           └────────┬─────────┘            │
│         │                                    │                      │
│         │                              Dev implements               │
│         │                              (feature branch)             │
│         │                              Fix CI, iterate              │
│         │                                    │                      │
│         │                                    ▼                      │
│         │                           ┌──────────────────┐            │
│         │                           │  DEV DONE        │            │
│         │                           │                  │            │
│         │                           │  cbm snapshot    │            │
│         │                           │  save --label    │            │
│         │                           │  post-dev        │            │
│         │                           │  → CBM-02 saved  │            │
│         │                           └────────┬─────────┘            │
│         │                                    │                      │
│         │                                    ▼                      │
│         │                           ┌──────────────────┐            │
│         │                           │  REVIEW PHASE    │            │
│         │                           │                  │            │
│         │                           │  cbm diff        │            │
│         │                           │  CBM-01 CBM-02   │            │
│         │                           │  --format md     │            │
│         │                           │                  │            │
│         │                           │  → Impact block  │            │
│         │                           │  → Test plan     │            │
│         │                           │  → PR body       │            │
│         │                           └────────┬─────────┘            │
│         │                                    │                      │
│         │                           CTO review + Tester verify      │
│         │                           CEO approve                     │
│         │                                    │                      │
│         │                                    ▼                      │
│         │                           ┌──────────────────┐            │
│         │                           │  MERGE           │            │
│         │                           │                  │            │
│         │                           │  CBM-02 ──►      │            │
│         │                           │  becomes CBM-01  │            │
│         │                           │  for next PR     │            │
│         │                           └──────────────────┘            │
│         │                                    │                      │
│         └────────────────────────────────────┘                      │
│                        (cycle repeats)                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Decision Flowchart — Khi nào cần diff?

```
Start: Dev nhận task mới
  │
  ▼
CBM-01 (baseline) có sẵn?
  │
  ├── NO → Chạy `cbm generate --label baseline` trên develop → Tiếp tục
  │
  ├── YES → CBM-01 stale (> 3 ngày)?
  │           │
  │           ├── YES → Regenerate CBM-01 trên develop mới nhất
  │           │
  │           └── NO → Dùng CBM-01 hiện tại
  │
  ▼
Dev implement xong, chạy `cbm snapshot save --label post-dev`
  │
  ▼
Task type?
  │
  ├── New feature (0 callers) → Diff value: THẤP → Generate CBM-02 for record only
  │
  ├── Modify shared module → Diff value: CAO → `cbm diff CBM-01 CBM-02 --format md`
  │
  ├── Refactor / rename → Diff value: CAO → `cbm diff CBM-01 CBM-02 --breaking-only`
  │
  └── Docs / config only → Diff value: KHÔNG CẦN → Skip CBM-02
```

---

## 6. EDGE CASES & EXCEPTIONS (BA)

| Scenario | Expected Behavior | Priority |
|----------|------------------|----------|
| CBM-01 không tồn tại khi dev bắt đầu task | Warning + auto-generate từ current branch | P1 |
| CBM-01 stale > 7 ngày | Alert + suggest regenerate | P2 |
| CBM-02 generate trên branch có merge conflicts | Error message rõ ràng: "Resolve conflicts first" | P1 |
| Function rename (cùng tên, khác file) | Detect as rename, không phải remove+add | P2 |
| Function overload (cùng tên, khác signature) | Detect as modify, list cả old + new signature | P2 |
| Diff giữa 2 projects khác config | Error: "Config mismatch — cannot compare" | P1 |
| Graph quá lớn (>10K functions) | Diff chỉ hiện top 50 changes + summary | P3 |
| Cùng function sửa ở 2 PRs song song | Mỗi PR có CBM-02 riêng, diff riêng — merge conflict ở graph level | P2 |
| CI fail → dev fix → push lại nhiều lần | CBM-02 chỉ generate khi dev báo "done", không mỗi push | P1 |

---

## 7. NON-FUNCTIONAL REQUIREMENTS (CTO)

| NFR-ID | Requirement | Target | Rationale |
|--------|-------------|--------|-----------|
| NFR-001 | `generate` performance | < 30s cho project 10K functions | Dev không muốn chờ lâu |
| NFR-002 | `diff` performance | < 5s cho 2 graphs × 10K functions | Review workflow cần nhanh |
| NFR-003 | Graph file size | < 5MB cho 10K functions | Git-friendly, không bloat repo |
| NFR-004 | Backward compatible | graph.json v1.x vẫn đọc được bởi v2.0 | Không break existing users |
| NFR-005 | Zero external dependencies | Diff hoạt động offline, chỉ cần 2 files | Chạy local, không cần network |
| NFR-006 | Language agnostic diff | Diff so sánh graph structure, không parse source code | Hỗ trợ Python + TypeScript + future languages |

---

## 8. COMPETITIVE ANALYSIS (CTO)

### 8.1 Existing Tools & Gaps

| Tool | What it does | CBM-01/02 support? | Gap |
|------|-------------|--------------------|----|
| **Madge** (JS) | Module dependency graph | No versioning | Single snapshot only |
| **pydeps** (Python) | Package dependency | No versioning | Single snapshot only |
| **Sourcegraph** | Code search + navigation | Has history but enterprise-only | $150/user/month, overkill for small teams |
| **GitHub Dependency Graph** | Package-level deps | No function-level | Too coarse for blast radius |
| **codebase-map (current)** | Function-level graph | No — single snapshot | This proposal fixes it |

### 8.2 Unique Value Proposition

```
"Codebase-map is the only tool that gives you Before vs After 
function-level impact analysis — so you know exactly what changed, 
what broke, and what to test."
```

Không tool nào hiện tại cung cấp:
1. Function-level (không chỉ package/module)
2. Dual-snapshot (baseline vs post-dev)
3. Affected callers (transitive impact)
4. PR-integrated (markdown output cho PR body)
5. Offline + zero-dependency

---

## 9. IMPLEMENTATION ROADMAP (CTO)

### Phase 1 — Graph Metadata + Snapshot Save (1 sprint)

**Scope:** FR-001, FR-002, FR-003, FR-004, FR-030, FR-031, FR-032

| Task | SP | Description |
|------|----|-------------|
| Add metadata to graph.json | 2 | `generated_at`, `commit_sha`, `branch`, `label`, `stats` |
| `--label` flag cho `generate` | 1 | CLI argument, default auto-label |
| Snapshot naming convention | 1 | `graph_{label}_{short_sha}.json` |
| `snapshots list` command | 1 | List saved snapshots with metadata |
| CI workflow update | 1 | Auto-generate baseline after merge |
| **Total** | **6** | |

### Phase 2 — Dual-Snapshot Diff (1 sprint)

**Scope:** FR-010 → FR-018

| Task | SP | Description |
|------|----|-------------|
| Diff engine: compare 2 graphs | 3 | Node + edge comparison, added/removed/modified |
| Affected callers detection | 2 | Transitive 1-level caller lookup |
| Rename detection | 2 | Same name + ≥80% body match |
| `--format markdown` output | 1 | PR body ready |
| `--format json` output | 1 | Machine-readable |
| `--breaking-only` filter | 1 | CTO review focus |
| **Total** | **10** | |

### Phase 3 — Lifecycle Commands (1 sprint)

**Scope:** FR-020 → FR-024, FR-017, FR-033

| Task | SP | Description |
|------|----|-------------|
| `snapshot save` shortcut | 1 | Generate + save + label |
| `lifecycle start/review` | 3 | Full lifecycle automation |
| `--test-plan` output | 2 | Suggested test scope |
| `snapshot clean` | 1 | Maintenance |
| Staleness warning system | 1 | 3-day warn, 7-day alert |
| **Total** | **8** | |

### Total: 3 sprints, 24 SP

---

## 10. SUCCESS METRICS (BA + CTO)

| Metric | Current (v1.x) | Target (v2.0) | How to measure |
|--------|---------------|---------------|----------------|
| Regressions caught pre-merge | 2 / 4 PRs (manual) | ≥ 80% of PRs with shared module changes | Diff report → affected callers → test run |
| Time to understand blast radius | 5-10 min (manual query) | < 30 sec (`cbm diff` one command) | Tester feedback |
| PR Impact block quality | Manual, inconsistent | Auto-generated, standardized | PR body format check |
| Test plan accuracy | Guess-based + Impact read | Impact-driven from diff output | Tester survey: "Did diff help scope?" |
| Developer planning time | 10-15 min exploring architecture | 2-3 min reading labeled baseline | Dev feedback |

---

## 11. MARKETING ANGLES (CEO Input)

Từ thực tế 4 PRs tại Hyper Commerce:

### Headline Options
1. **"Before & After: Know exactly what your code change broke"**
2. **"From 'I think it's safe' to 'I know it's safe' — function-level impact analysis"**
3. **"The missing piece in code review: baseline vs post-dev diff"**

### Case Study Data (HC Sprint 5)
- 4 PRs tracked, 2 regressions caught pre-merge
- `query` usage: 9 times (architecture discovery)
- `impact` usage: 5 times (blast radius)
- Average time saved: ~5x faster than manual grep
- New with dual-snapshot: safe deletion confidence, impact-driven test plans

### Target Audience
- **Primary:** Dev teams using PR-based workflow (GitHub/GitLab)
- **Secondary:** QA teams needing impact-driven test plans
- **Tertiary:** CTOs/TechLeads reviewing PRs for blast radius

### Differentiator
```
Other tools:  "Here's your dependency graph" (static, one-time)
Codebase-map: "Here's what changed, who's affected, and what to test" (lifecycle, actionable)
```

---

## 12. OPEN QUESTIONS FOR DEV TEAM

| # | Question | Impact | Proposed Answer |
|---|----------|--------|----------------|
| 1 | Snapshot storage: files trong repo hay external store? | Repo size vs accessibility | Repo (git-tracked) cho teams < 50 devs, external store cho enterprise |
| 2 | Rename detection algorithm: AST-based hay text similarity? | Accuracy vs complexity | Text similarity (≥80% body match) cho v2.0, AST cho v3.0 |
| 3 | Transitive caller depth: 1 cấp hay configurable? | Noise vs completeness | Default 1, flag `--depth N` cho power users |
| 4 | Graph format: giữ JSON hay migrate sang SQLite? | Query performance cho large projects | JSON cho v2.0 (simple, git-friendly), SQLite option cho v3.0 |
| 5 | CI integration: GitHub Actions only hay support GitLab CI? | Market size | GitHub Actions first, GitLab CI Phase 3 |
| 6 | Pricing: dual-snapshot là free hay paid feature? | Revenue vs adoption | Free cho core diff, paid cho lifecycle automation + CI integration |

---

## 13. GLOSSARY

| Term | Definition |
|------|-----------|
| **CBM-01 (Baseline)** | Graph snapshot từ code đã merge (develop/main) — đại diện architecture chuẩn hiện tại |
| **CBM-02 (Post-dev)** | Graph snapshot từ feature branch sau khi dev hoàn tất — đại diện code sẽ merge |
| **Blast radius** | Số lượng callers bị ảnh hưởng bởi thay đổi code |
| **Affected caller** | Function gọi đến function bị modify/remove (transitive) |
| **Snapshot** | Graph file + metadata tại một thời điểm cụ thể |
| **Lifecycle** | Chuỗi: Baseline → Planning → Dev → Post-dev → Review → Merge → New Baseline |
| **Impact block** | Markdown section trong PR body mô tả blast radius + affected callers |

---

---

## 14. CTO REVIEW + CEO DECISIONS (10/04/2026)

> **Review file chi tiết:** `CTO_Review_Dual_Snapshot.md` + `CTO_CI_Integration_Proposal.md` (cùng thư mục)

### 14.1 CTO Review — Verdict: ✅ APPROVE with 3 modifications

**Score: 48/60 (80%)** — Proposal solid, spec quality 9/10.

**3 điều chỉnh:**

| # | Modification | Lý do |
|---|-------------|------|
| 1 | **Phase 3 (Lifecycle commands) → DEFER sang KMP M3** | `lifecycle start/review` cần state management = scope KMP Vault, không build trong codebase-map standalone (giữ stateless) |
| 2 | **Rename detection: signature matching** (name + params + return_type) thay vì body matching | Body matching cần lưu content trong graph → phình file size. AST body match defer sang v3.0/KMP |
| 3 | **CI: GitHub Actions artifact (default)** thay vì commit-to-repo | Zero commit noise. PR comment auto-post Impact Analysis |

**Scope adjusted:** 2 phases, **19 SP**, 3 tuần (giảm từ 24 SP / 3 phases):
- Phase 1: Metadata + Snapshot Save = **7 SP / 1 tuần** → ship **codebase-map v2.1**
- Phase 2: Dual-Snapshot Diff = **12 SP / 2 tuần** → ship **codebase-map v2.2**
- ~~Phase 3: Lifecycle = defer KMP M3~~

**6 Open Questions answered:**
1. Storage → GitHub Actions artifact (default) + opt-in commit-to-repo
2. Rename → Signature matching (v2.x), AST body (v3.0/KMP)
3. Depth → Default 1, `--depth N` max 3
4. Format → JSON (codebase-map), SQLite (KMP Vault)
5. CI → GitHub Actions first, GitLab = community
6. Pricing → **100% free** (paid features ở KMP)

### 14.2 CEO Decisions (10/04/2026)

| # | Decision | CEO Answer |
|---|---------|-----------|
| 1 | Approve CTO 3 modifications | ✅ Approved |
| 2 | CI Phương án | ✅ **Phương án B** (Artifact + Auto PR Comment) — zero commit noise |
| 3 | PR comment format | ✅ Summary table visible + full diff collapsible `<details>` |
| 4 | Staleness threshold | ✅ 3 ngày warn Telegram, 7 ngày block merge |
| 5 | Timeline start Phase 1 | ✅ **Sau KMP M1 done + CEO duyệt plan** |
| 6 | CI workflows draft vào HC repo | ❌ Không cần ngay — **templates lưu trong proposal** (section 5 của `CTO_CI_Integration_Proposal.md`), triển khai khi cần |

### 14.3 Ranh giới CBM vs KMP (CEO + CTO đồng thuận)

```
CODEBASE-MAP (standalone, free, stateless)     KMP (platform, freemium, stateful)
──────────────────────────────────────────     ──────────────────────────────────
✅ Graph generate (AST → nodes/edges)           ✅ Vault (SQLite + Markdown)
✅ Graph metadata + versioning (v2.1)            ✅ Pattern Learner + Confidence
✅ Dual-snapshot diff (v2.2)                     ✅ Ask + MCP + Multi-LLM
✅ CLI query/impact/search                       ✅ Drift detection
✅ CI artifact + PR comment                      ✅ Lifecycle commands (state mgmt)
✅ HTML interactive viewer                       ✅ Insights dashboard
```

### 14.4 Timeline tổng

```
NOW          KMP M1 active (Vault + Parser, 26 SP, 2 tuần)
    ↓
M1 done      CEO review + duyệt CBM Phase 1 plan
    ↓
Phase 1      CBM v2.1: Metadata + Snapshot (7 SP, 1 tuần)
    ↓
Phase 2      CBM v2.2: Dual-Snapshot Diff (12 SP, 2 tuần)
    ↓         ↑ parallel KMP M2
CI enable    3 workflow files → HC repo → 6/9 bước automated
    ↓
KMP M3       Lifecycle commands (dùng CBM diff engine)
```

---

*Proposal v1.1 | CTO + BA — Hyper Commerce | 2026-04-10*
*Origin: CEO insight from HC Sprint 5 (PRs #96-#99)*
*CTO Review + CEO Decisions: 10/04/2026*
*Status: ✅ APPROVED — Pending KMP M1 completion → Phase 1 kickoff*
