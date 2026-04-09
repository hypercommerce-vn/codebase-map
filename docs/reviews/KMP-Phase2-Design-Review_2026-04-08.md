# KMP Phase 2 Design Review — 08/04/2026

**Files reviewed**
- `design-preview/kmp-v2-design.html` (1199 lines) — Phase 2 platform shell
- `design-preview/kmp-M0-design.html` (753 lines) — Sprint M0 detail page

**Reviewers (composite)**: PO + CTO + BA agents
**Reference**: `specs/kmp/architecture.md`, `specs/kmp/user-stories-m0-m1.md`, `project/CM-MEM-M0-TASK-BOARD.md`

---

## TL;DR

- **Combined score: 82/100** — APPROVE WITH MINOR REVISION
- **Verdict**: Both designs are coherent, on-spec, and visually consistent with the existing codebase-map v2 token system. M0 page is the stronger of the two. v2 page over-promises features that won't exist until M1–M4.
- **3 critical issues**:
  1. **Roadmap math inconsistent** — v2 footer says "116 SP / 11 weeks" (`kmp-v2-design.html:1064`) but the timeline sums to 8+27+36+25+20 = **116 SP** ✓ — however user stories doc says M0=6 SP and M1=26 SP (32 total), while design shows M0=8 SP and M1=27 SP. SP source-of-truth drift between specs and design.
  2. **Phase-2 page shows live data the user cannot have at sprint kickoff** — KPI cards "1,384 memories", "42.8 MB vault", service dots "all OK", FTS5 "12ms p95" (`kmp-v2-design.html:671-765`) imply a working M1+ system. This is a *vision mock*, not a Sprint-M0 deliverable. Risk: CEO mistakes it for current state.
  3. **Story coverage gap** — v2 stories panel lists US-M0-01..05+07 (`:1108-1137`) but **omits US-M0-06 (CTO sign-off) and US-M0-08 (LICENSE/CI)**. M1 panel renumbers stories (US-M1-01..14) that don't match the IDs in `user-stories-m0-m1.md` (e.g. US-M1-09 in spec = "Bootstrap orchestrator", in design = "Quick Win — 10 initial patterns"). **Traceability is broken.**
- **Recommendation**: Approve M0 page as-is for kickoff. Request 1 revision pass on v2 page to (a) label as "vision mock", (b) realign story IDs/SP with the spec, (c) add US-M0-06/08 to coverage table.

---

## PO Review — 78/100

| Dimension | Score | Notes |
|---|---:|---|
| Scope alignment | 16/20 | M0 page maps 1:1 to CM-MEM-M0 task board. v2 page oversteps Phase 2 by showing M2 (MCP Hub registered, 3 tools — `:754`) and M4 (NotebookLM export — `:1095`) as if scaffolded. |
| User value | 18/20 | Sidebar with 6 verticals + ghost "Coming soon" labels (`:619-643`) tells the dual story (current = codebase only, future = platform). Strong for CEO pitch. |
| MVP discipline | 14/20 | Settings page exposes 6 cards including BYOK token inputs, Merkle refresh schedule, embeddings provider (`:983-1058`) — none of these are M0 deliverables. Cuts MVP focus. |
| Story coverage | 15/20 | M0: 6/8 stories shown (missing US-M0-06, US-M0-08). M1: 14 rows but IDs/labels don't match `user-stories-m0-m1.md`. **No story-traceability link** to the spec file. |
| Verdict (PO) | **63/100 raw → 78 weighted** | Story coverage panel needs an audit pass. |

**M0 stories covered (v2 design)**: M0-01, M0-02, M0-03, M0-04, M0-05, M0-07
**M0 stories missing (v2 design)**: M0-06 (CTO sign-off), M0-08 (LICENSE+CI)
**M0 stories covered (M0 design)**: All 8 (01–08) via task list `:653-717` ✓

---

## CTO Review — 86/100

| Dimension | Score | Notes |
|---|---:|---|
| Architecture fidelity | 22/25 | 6 core services match `architecture.md` exactly: VaultService, LearnerRuntime, AI Gateway, MCP Hub, Licensing, CLI Framework. Both files reflect them (`v2:736-765`, `M0:494-553`). Vertical model implied by sidebar (codebase active, 5 ghosts). Vault format viewer (`M0:411-455`) directly visualizes the spec dir tree. |
| Feasibility | 22/25 | M0 LOC estimates (180+120+80+60+90+140 = 670 LOC core) realistic. Hello vertical 50 LOC constraint preserved. **However**, v2 design implies LearnerRuntime "idle" + 1,384 memories — not feasible end of M0. |
| Visual consistency | 20/25 | Inherits codebase-map v2 design tokens (`--bg-canvas: #0d1117`, `--hc-primary: #6366f1`, Inter font, 13px base — `v2:14-39`, `M0:9-26`). Topbar height/sidebar width identical. Card radius, color semantics (ok/warn/err) consistent. **Drift**: M0 page omits sidebar entirely (single-column main), v2 has sidebar. Acceptable as different layouts but worth noting. |
| Code quality | 22/25 | Clean CSS, BEM-ish class naming, single `<style>` block per file (~570 LOC v2, ~360 LOC M0). Responsive: only 1 media query each (`v2:251`, `M0:189`). **ARIA gaps**: no `role`, no `aria-label`, no skip-link, theme toggle button has only `title=`. Tab nav uses `<a href="#">` + JS click but no `role="tablist"`/`aria-selected`. Search inputs have no `<label>`. Checkbox approval has `<label for>` ✓. Dark-mode-only — no light theme despite 🌙 toggle button (`v2:600`). |
| Verdict (CTO) | **86/100** | Architecturally faithful. Polish ARIA + add a "Mock data" disclaimer banner. |

---

## BA Review — 81/100

| Dimension | Score | Notes |
|---|---:|---|
| Requirements traceability | 16/25 | M0 design has acceptance hints embedded in each task row (`:657-716`) — strong. v2 design's stories panel decouples from FR/Task IDs in spec. SP totals drift: spec says M0=6 SP, board says 8 SP, v2 design says 8 SP ✓ for M0; spec says M1=26 SP, v2 says **27 SP** (`:712, 1075`). 1 SP unaccounted. |
| Business rules (dual-license) | 22/25 | Excellent. M0 design dedicates section C (`:565-635`) to dual-license with bullet rules ("CI fail nếu file LICENSE bị xoá", "Per-seat hoặc per-org", "Template ship trong M0, enforce trong M4"). Matches CEO Round 2 directive. v2 design surfaces same in Settings card (`:1033-1043`). Business-rule consistency across both files = good. |
| IA + edge states | 20/25 | v2 design shows search empty state (`:971-975`), sidebar ghost states, service-warn dot for Licensing dev key. M0 design shows blocked-banner pattern + CI fail row (`:614`). **Missing edge states**: vault init failure, license signature invalid, no-corpus hello, BYOK token missing. |
| VN/EN copy consistency | 23/25 | Both files mix Vietnamese microcopy ("Tìm kiếm memory…", "Trạng thái nền tảng KMP", "Sprint chưa start") with English labels ("Overview", "Vault Browser", "READY"). Consistent style. Minor: M0 page has "blocked-banner" with `✓` icon and `var(--ok)` styling but text says "Blocked by: none" (`:720-726`) — semantically a *cleared* banner; consider renaming for clarity. |
| Verdict (BA) | **81/100** | Story-ID realignment is the main fix. |

---

## Top recommendations

### Critical (must fix before approval)
1. **Realign story IDs and SP totals across spec ↔ board ↔ design**. Either update `user-stories-m0-m1.md` to M0=8 SP / M1=27 SP, or update designs back to 6/26. Pick one source of truth. (`v2:712, 1075, 1106-1158`)
2. **Add US-M0-06 (CTO sign-off) and US-M0-08 (LICENSE/CI) rows** to v2 design Stories panel. (`v2:1108-1137`)
3. **Add a "vision mock — not yet built" disclaimer** to the v2 design header so CEO does not interpret KPI cards / service health as live state. (`v2:664-689, 734-766`)

### Important (next iteration)
4. Add minimal ARIA: `role="tablist"`, `aria-selected`, `<label>` for search inputs, skip-link. Codebase-map v2 design already does this — drift here.
5. Make the M0 "blocked-banner" semantically green-cleared or rename CSS class to `status-banner` (`M0:336-346, 720`).
6. Wire the v2 design Roadmap panel `:1064` to actually link to `project/board.html` so CEO can drill down.

### Nice-to-have
7. Light-theme palette (theme toggle is decorative right now — `v2:600`).
8. Add a tiny legend to the vault tree (`M0:410-428`) explaining the 📁/📄 icons (BA improvement).
9. Show a "story → component" hover map in v2 stories panel instead of static text in `.cover` column.

---

## Combined verdict

**APPROVE WITH MINOR REVISION** — combined score **82/100**.

- M0 design (`kmp-M0-design.html`): **APPROVE AS-IS** for Sprint M0 kickoff. It is accurate, scoped, and immediately useful as a one-pager for daily standup.
- v2 design (`kmp-v2-design.html`): **REVISE** — 1 pass to fix story coverage, SP drift, and add a vision-mock disclaimer.

**Effort estimate for revision**: ~2 hours (Designer + BA pair)
- 30 min — disclaimer banner + copy
- 45 min — story coverage table audit (compare with `user-stories-m0-m1.md`)
- 30 min — SP arithmetic reconciliation (decide source of truth, update other files)
- 15 min — ARIA pass on tablist + search labels

After revision → CEO can approve in next session without re-review gate.

---
*Review composed by PO + CTO + BA agents · 08/04/2026 · No design files modified · No PR opened*
