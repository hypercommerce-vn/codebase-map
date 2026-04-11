# CM-MEM-M1 — Sprint M1 Task Board
# HC-AI | ticket: KMP-M1
> **Codebase Memory Vertical + Quick Wins** · Sprint 2/5 của KMP MVP
> Owner: @TechLead · PM: @PM · Created: 10/04/2026 · CEO approved design: 10/04/2026

---

## 🎯 SPRINT GOAL

Build first product vertical: PythonAST parser + 3 learners (Naming, Layer, GitOwnership) + bootstrap CLI + Quick Wins output. Prove KMP Core abstraction works end-to-end on real codebase (HC project).

**Definition of Success:** `codebase-memory bootstrap` chạy trên HC project ≤5 min, sinh `patterns.md` (≥20 patterns) + `quick-wins.md` (10 insights: 5+3+2), CTO dogfood ≥15/20.

---

## 📅 SPRINT META

| Field | Value |
|-------|-------|
| **Sprint code** | CM-MEM-M1 |
| **Status** | 🔥 **ACTIVE** — Day 4 · 14/04/2026 · 14/26 SP |
| **Start date** | 2026-04-10 (T5) — CEO approved M1 design |
| **Target end** | 2026-04-24 (T5) — 10 working days, nghỉ T7-CN |
| **Duration** | 2 tuần |
| **Story Points** | 26 SP |
| **Owner** | @TechLead (1 người) |
| **Reviewer** | @CTO (architecture) + @Tester (acceptance) + @Designer (CLI UX) |
| **Branch base** | `main` |
| **PR strategy** | 1 PR / Day (Daily PR Mandatory) |
| **Design** | `design-preview/kmp-M1-design.html` (CEO approved 10/04/2026) |
| **Prerequisite** | M0 COMPLETE (8/8 SP, CTO 20/20, PR #53 merged) |

---

## ✅ TASK LIST (26 SP)

| # | ID | Task | SP | Day | Status | Acceptance |
|---|----|------|:--:|:---:|:------:|------------|
| 1 | MEM-M1-01 | `CodebaseVault(BaseVault)` — init vault structure, SQLite core.db | 2 | D1 | ✅ Done | `codebase-memory init` creates `.knowledge-memory/`, idempotent, schema_version: 1 |
| 2 | MEM-M1-02 | `PythonASTParser(BaseParser)` — port AST parsing + directory scan | 2 | D1-2 | ✅ Done | parse_directory + scan_stats, include/exclude, 29 parser tests |
| 3 | MEM-M1-03 | Snapshots + rotation (keep 5 recent) | 2 | D2 | ✅ Done | Full corpus save, list/load/restore, rotation keep 5, labels, 31 vault tests |
| 4 | MEM-M1-04 | SQLite extension schema + indices + query methods | 2 | D3 | ✅ Done | 8 indices, query_nodes/edges, node_count/edge_count, 8 new tests |
| 5 | MEM-M1-05 | `NamingLearner(BaseLearner)` — naming conventions | 2 | D3-4 | ✅ Done | snake_case/PascalCase detection, CRUD prefix, violations, vault-query, 29 tests, E2E pass |
| 6 | MEM-M1-06 | `LayerLearner` — path hierarchy patterns | 2 | D4 | ✅ Done | 10 layer types, 5 cluster patterns, domain grouping, depth analysis, 50 tests, E2E pass |
| 7 | MEM-M1-07 | `GitOwnershipLearner` — author attribution | 2 | D5 | ⏳ Todo | Parse git log, detect single-owner risk (bus factor), ≥3 patterns |
| 8 | MEM-M1-08 | `patterns.md` generator via `vault.commit_pattern()` | 2 | D6 | ⏳ Todo | Human-readable Markdown, grouped by learner, confidence + evidence |
| 9 | MEM-M1-09 | `bootstrap` orchestrator (Parse→Snapshot→Learn→Commit→Summary) | 2 | D6-7 | ⏳ Todo | ≤5 min for 100K LOC, 5-step progress, graceful Ctrl+C |
| 10 | MEM-M1-10 | Quick Wins generator (10 insights: 5+3+2) | 3 | D7-8 | ⏳ Todo | 5 structure + 3 patterns + 2 risks, each with evidence + confidence |
| 11 | MEM-M1-11 | CLI summary output with rich colors | 1 | D8 | ⏳ Todo | `rich` library, progress bars, NO_COLOR=1 fallback, ≤20 lines |
| 12 | MEM-M1-12 | Spike: BM25 Vietnamese language validation (recall ≥75%) | 2 | D9 | ⏳ Todo | Report on BM25 + tiếng Việt tokenization, recall benchmark |
| 13 | MEM-M1-13 | Unit tests ≥80% coverage | 1 | D9-10 | ⏳ Todo | pytest coverage report, all learners + vault + parser covered |
| 14 | MEM-M1-14 | CTO dogfood + subjective gate (≥15/20) | 1 | D10 | ⏳ Todo | CTO runs on HC codebase, scores ≥15/20 |

**Total: 26 SP**

---

## 🗓️ DAILY PLAN

| Day | Date | Tasks | PR | Reviewer |
|-----|------|-------|----|----|
| **D1** | 10/04 (T5) | MEM-M1-01 (CodebaseVault) + MEM-M1-02 start (PythonASTParser) | PR #1 | CTO |
| **D2** | 11/04 (T6) | MEM-M1-02 finish + MEM-M1-03 (Snapshots) | PR #2 | CTO |
| **D3** | 14/04 (T2) | MEM-M1-04 (SQLite schema) + MEM-M1-05 start (NamingLearner) | PR #3 | CTO |
| **D4** | 15/04 (T3) | MEM-M1-05 finish + MEM-M1-06 (LayerLearner) | PR #4 | CTO |
| **D5** | 16/04 (T4) | MEM-M1-07 (GitOwnershipLearner) | PR #5 | CTO |
| **D6** | 17/04 (T5) | MEM-M1-08 (patterns.md) + MEM-M1-09 start (bootstrap) | PR #6 | CTO |
| **D7** | 18/04 (T6) | MEM-M1-09 finish + MEM-M1-10 start (Quick Wins) | PR #7 | CTO |
| **D8** | 21/04 (T2) | MEM-M1-10 finish + MEM-M1-11 (CLI rich) | PR #8 | CTO + Designer |
| **D9** | 22/04 (T3) | MEM-M1-12 (BM25 spike) + MEM-M1-13 start (tests) | PR #9 | CTO |
| **D10** | 23/04 (T4) | MEM-M1-13 finish + MEM-M1-14 (CTO dogfood) | PR #10 | CTO + Tester + CEO |

*Nghỉ T7-CN (12-13/04, 19-20/04). Review-gate 3 tầng trước CEO approve.*

---

## 🚪 DEFINITION OF DONE (M1)

- [ ] `codebase-memory init` tạo vault structure idempotent
- [ ] `codebase-memory bootstrap` chạy ≤5 min trên HC (1,386 nodes)
- [ ] 3 learners (Naming, Layer, GitOwnership) sinh ≥20 patterns
- [ ] `patterns.md` human-readable, grouped by learner
- [ ] `quick-wins.md` có 10 insights (5+3+2), evidence + confidence
- [ ] CLI output ≤20 lines, rich colors, NO_COLOR=1 fallback
- [ ] Ctrl+C saves partial state, --resume continues
- [ ] Learner crash → log + continue (isolation)
- [ ] Confidence threshold 60% (configurable)
- [ ] Snapshot rotation keep 5
- [ ] Unit tests ≥80% coverage
- [ ] CTO dogfood ≥15/20
- [ ] CEO approve final PR

---

## ⚠️ RISK & MITIGATION

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|:----------:|:------:|------------|
| R-M1-1 | AST parser port from codebase-map takes longer than 2 SP | Medium | High | Reuse existing python_parser.py, adapt to BaseParser interface |
| R-M1-2 | GitOwnershipLearner slow on large git history | Medium | Medium | Limit to last 1000 commits, configurable depth |
| R-M1-3 | Quick Wins insights not actionable enough | Low | High | PO review D8, iterate wording before D10 |
| R-M1-4 | BM25 Vietnamese recall <75% | Medium | Low | Spike only — results inform M2, not blocking M1 |
| R-M1-5 | 26 SP in 10 days too aggressive | Medium | High | D1-D2 are port work (not greenfield), buffer in D9-10 |

---

## 📝 DESIGN DECISIONS (locked 10/04/2026)

| # | Decision | Owner |
|---|----------|-------|
| D-M1-01 | CLI-first, no HTML in M1 | PO |
| D-M1-02 | 10 Quick Wins fixed ratio: 5+3+2 | PO + CTO |
| D-M1-03 | Rich CLI via `rich` library | Designer |
| D-M1-04 | Confidence threshold: 60% default | CTO |
| D-M1-05 | Learner isolation: crash one, continue rest | CTO |
| D-M1-06 | Snapshot rotation: keep 5 | CTO |
| D-M1-07 | Ctrl+C saves partial state + --resume | CTO + Designer |
| D-M1-08 | Output = standard Markdown | PO |

---

## 🔗 LIÊN QUAN

- M0 task board (done): `project/CM-MEM-M0-TASK-BOARD.md`
- FDD v2.0: `specs/kmp/fdd-v2.md`
- Architecture: `specs/kmp/architecture.md`
- M1 Design: `design-preview/kmp-M1-design.html` (CEO approved 10/04/2026)
- M0 Design: `design-preview/kmp-M0-design.html`
- KMP v2 Design: `design-preview/kmp-v2-design.html`

---

*CM-MEM-M1 Task Board · Created 10/04/2026 · @PM*
