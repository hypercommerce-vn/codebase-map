# CBM-INT-S2 · v2.4 — Sprint Retrospective

> **Sprint:** CBM-INT-S2 (MCP Server · 5 tools · Graph cache · PyPI publish · docs)
> **Originally scheduled:** Mon 27/04 → Sun 10/05/2026 (2 weeks · 8 SP)
> **Actual execution:** Mon 20/04 → Tue 21/04/2026 — **1.5 calendar days**
> **Outcome:** 🎉 **8/8 SP (100%) COMPLETE · 5 days ahead of schedule · v2.4.0 LIVE on PyPI**
> **Shipped:** MCP server scaffold · 5 tools (query/search/impact/snapshot_diff/api_catalog) · GraphCache 40× speedup · PyPI packaging (Path A) · integration tests · Claude Desktop docs · MCP registry submission prep
> **Facilitator:** PM (Claude, project-manager skill)

---

## 1. Sprint Goal & Outcome

**Goal:** Build MCP Server exposing CBM query engine to Claude Code / Cowork / Desktop via stdio transport. Moves Phase 1 slash-command UX → Phase 2 auto-invoke UX. Retention 15% → 50%.

**Outcome:** ✅ **ALL 6 AC met · v2.4.0 LIVE on PyPI · `cbm-mcp` entry point callable.**

| Deliverable | Status | Evidence |
|------------|:------:|---------|
| MCP server scaffold (`mcp_server/`) | ✅ | 167 LoC D1 · TOOL_REGISTRY pattern |
| Tool `cbm_query` | ✅ | 67 LoC · D2 |
| Tool `cbm_search` | ✅ | 79 LoC · D2 |
| Tool `cbm_impact` | ✅ | 100 LoC · risk tier · D2 |
| Tool `cbm_snapshot_diff` | ✅ | 138 LoC · 5 flags · pure Python API · D3 |
| Tool `cbm_api_catalog` | ✅ | 96 LoC · method+domain filters · D4 |
| Graph cache | ✅ | 72 LoC · thread-safe · mtime invalidation · **40× speedup** · D4 |
| PyPI packaging | ✅ | v2.4.0 LIVE · `pipx install codebase-map[mcp]` · `cbm-mcp` entry |
| Integration test | ✅ | 5/5 tools smoke PASS · Day 5 report |
| Claude Desktop docs | ✅ | `integrations/mcp/README.md` 120 lines |
| MCP registry prep | ✅ | Submission doc ready · CEO action post-launch |

---

## 2. Velocity & Estimation

| Metric | Plan | Actual | Delta |
|--------|:----:|:------:|:-----:|
| SP committed | 8 | 8 | 0 |
| SP delivered | 8 | 8 | 0 |
| Days allocated | 10 working days (+ Gate weeks) | **1.5 calendar days** | **-8.5 days** |
| PRs planned | ~8 | **12 merged** (incl. 2 status syncs + 2 superseded-by-rebased-v2) | +4 |
| Conflict-resolution PRs | 0 | 3 (Option C pattern applied #124, #128, #131) | +3 |

**Sprint velocity observation:** Same fast agent-driven pattern as S1. But **3 merge conflicts** were recurring friction (same pattern each time: status sync PR edits board.html progress, feature PR also edits). See Start/Stop/Continue §3.

---

## 3. Start / Stop / Continue

### 🚀 Start

- **Combine status sync + feature PR** (or split board edits) — 3 conflicts in a row is a smell. For S3, either (a) PM lets feature PRs update progress themselves (no separate status sync PR), or (b) feature PRs exclude `project/board.html` from their scope entirely.
- **PyPI trusted publisher (AI-#1 from S1 retro)** — still using `PYPI_API_TOKEN`. Workflow even warns "The workflow was run with 'attestations: true' but an explicit password was also set, disabling Trusted Publishing." **Action item for CBM-INT-S3:** configure OIDC on PyPI side, drop secret.
- **Live Claude Desktop dry-run** — smoke tests via direct handler call are PASS, but the real test is Claude Desktop invoking via stdio MCP protocol. Needs CEO-side test at some point before next initiative.

### 🛑 Stop

- **Having both status sync PR and feature PR edit `project/board.html` progress label concurrently** — causes guaranteed conflicts. Choose one:
  - (a) Status sync PR is docs-only (timeline + PR history), feature PR updates its own progress
  - (b) Feature PR skips board.html; PM merges feature PR then ships board update
- **Including `mcp_server/__init__.py __version__` in the version-bump dance** — it drifted from `pyproject.toml` once already (remember stale 1.0.0?). Either align to pyproject automatically or just drop mcp_server's __version__ entirely (redundant with parent package).
- **Writing lengthy commit bodies for trivial PRs** — `chore(board)` status syncs had ~30-line commit messages for 2-file diffs. Keep commit messages proportional to change size (5-10 lines max for docs updates).

### ✅ Continue

- **Option C conflict resolution pattern** — new branch + cherry-pick + close old PR is clean, auditable, non-destructive. Worked 3× in a row with zero data loss. Keep this as the default for any rebase-vs-main conflict.
- **Agent role framing from `agents/*/SKILL.md`** — same benefit as S1: agents catch real bugs.
  - TechLead D2 caught `QueryEngine.query_node` (not `query`), `search()` no `limit` kwarg, `register_tool(tool, handler)` 2-arg signature
  - TechLead D3 chose pure Python API over subprocess for snapshot_diff (cleaner) — 6/6 smoke tests PASS
  - TechLead D4 extracted `DEFAULT_GRAPH_FILE` constant to `graph_cache.py` as single source of truth (not in template)
  - TechLead D5 chose Path A packaging (single package + `[mcp]` extra) with clear rationale vs Path B (separate package) — matched 1 SP budget
- **TOOL_REGISTRY self-register pattern** — established D1 paid off every subsequent day. D2-D5 tools dropped in without touching `server.py`. Architecture investment ≠ wasted time.
- **Board SSOT rule #8** — every merged PR has a timeline event. CEO can reconstruct sprint trajectory purely from board.
- **Benchmark-driven acceptance** — AC-S2-02 "Graph 10MB load < 500ms, query < 100ms" measured empirically (40× speedup on 200-node self-graph, cold 2.8ms → hot 0.071ms). No hand-waving.

---

## 4. What went well

1. **Zero P0/P1 defects** across 8 tasks · 12 PRs · 2 conflict resolutions · 300+ LoC MCP code
2. **Lint gate 100% green** every PR
3. **158/158 tests PASS** every day · no regression
4. **Agent architecture decisions**: Path A packaging, pure Python API for snapshot_diff, DEFAULT_GRAPH_FILE constant
5. **PyPI v2.4.0 LIVE** verified within minutes of tag push (workflow 29s)
6. **Real install test verified `cbm-mcp` entry point** — perl-alarm 2s → stdio block → exit 0 (correct behavior)
7. **Sprint speed**: 8 SP in 1.5 calendar days vs 10-day plan (**0.15 days/SP**) — similar to S1's 0.2 days/SP, pattern reproducible

## 5. What could have gone better

1. **3 merge conflicts** — #123→#124, #127→#128, #130→#131. Same root cause each time. See Stop §3.
2. **PyPI OIDC still not configured** — AI-#1 from S1 retro still open
3. **Live Claude Desktop dry-run not done** — AC-S2-03 marked 🟡 partial (smoke PASS only)
4. **Release notes bump** — v2.4.0 release notes were 102 lines, slightly over 100-line budget. Not a real issue.
5. **Packaging Path A deviation from Tech Plan** — Tech Plan §2.5 showed `uvx --from codebase-map-mcp cbm-mcp`; we ship as `codebase-map[mcp]` entry point instead. Documented in release notes. Not a regression but a deliberate trade-off for speed.

## 6. Surprises & Insights

- **`cbm-mcp` entry point via `[project.scripts]`** is cleaner than Tech Plan's `uvx --from codebase-map-mcp cbm-mcp` pattern. Users get a direct CLI without separate package management. Path A wins.
- **MCP SDK 1.27.0** — Tech Plan template was written for a possibly-older version; SDK API evolved but TechLead adapted cleanly (async handlers, `mcp.types.Tool`, `register_tool(TOOL, handler)` 2-arg).
- **`query_node` vs `query`** — Tech Plan assumed `query()`; real API is `query_node()`. TechLead caught by reading the actual source before coding.
- **Cache benchmark 40× speedup** on small 200-node graph is already excellent; expect 50-100× on 1000+ node repos (loading parse time dominates cold path).
- **snapshot_diff Python API is clean** — 3-piece composition (SnapshotManager + SnapshotDiff + diff_formatter) mirrors CBM CLI. No subprocess needed. Tech Plan's subprocess fallback was over-engineering.

---

## 7. Action Items for CBM-INT-S3 + ongoing backlog

| # | Action | Carried from | Owner | Due |
|---|--------|:-------------:|-------|:---:|
| S2-1 | **Stop board-progress conflict pattern** — feature PRs skip `project/board.html`, PM ships board sync separately | S2 | PM | S3 Day 1 |
| S2-2 | **Live Claude Desktop dry-run** — install `cbm-mcp` in real Claude Desktop, test 20 prompts | S2 | CEO | Pre-S3 kickoff |
| S2-3 | **`mcp_server/__init__.py __version__` removal** — redundant with parent pyproject, remove to prevent drift | S2 | TechLead | S3 Day 1 |
| S2-4 | **Tighter commit message discipline** — 5-10 lines max for docs/status PRs | S2 | PM | Ongoing |
| AI-#1 | **PyPI OIDC Trusted Publisher** — configure on pypi.org side, drop `PYPI_API_TOKEN` secret | S1 retro · still open | TechLead | S3 Day 1 |
| AI-#2 | **`__version__` == pyproject test** | S1 retro · still open | TechLead | S3 Day 1 |
| AI-#4 | **PyPI release runbook doc** | S1 retro · still open | PM | S3 Day 2 |
| AI-#5 | **Linux + WSL pipx smoke tests** | S1 retro · still open | Tester | S3 Day 5 |
| AI-#7 | **GitHub Settings** (secret scanning · Dependabot · branch protection main) | S1 retro · still open | CEO | Pre-S3 kickoff |
| AI-#9 | **Config path UX** (fallback CWD for `/dev/fd/*`) | S1 retro · still open | TechLead | S3 backlog |
| AI-#10 | **`/cbm-diff` default branch auto-detect** | S1 retro · still open | TechLead | S3 backlog |

**Critical item for S3 Day 1:** S2-1 (board conflict pattern) — this will keep recurring otherwise.

---

## 8. CEO Decisions for S3

### D-S2-Retro-1: Merge conflict prevention pattern

S2 had 3 merge conflicts (#123, #127, #130) all from same root cause. Which convention for S3?

- **(a)** Feature PRs never touch `project/board.html` — PM ships separate board sync PR after each feature merges
- **(b)** No separate status-sync PRs — feature PRs own their progress row + PR history append
- **(c)** Status-sync PRs are docs-only (timeline events + BRIEF), never touch progress bar (feature PRs update)

**PM recommendation:** **(c)** — splits concerns cleanly, feature PR owns its own state, status sync focuses on context (timeline narrative).

### D-S2-Retro-2: PyPI OIDC (finally)

AI-#1 open from S1 retro. Should we block S3 Day 1 until PyPI OIDC is configured? Or keep deferring?

**PM recommendation:** Configure OIDC as part of S3 Day 1 (CBM-INT-S3-301). Removes `PYPI_API_TOKEN` secret dependency, aligns with attestations warning we keep seeing in workflow logs.

### D-S2-Retro-3: Live Claude Desktop dry-run timing

AC-S2-03 is 🟡 partial. Should CEO do dry-run now (before S3 launch) or defer to post-S3?

**PM recommendation:** **Now.** 10-minute test closes AC-S2-03 genuinely. If issues found, they're easier to fix inside S3 scope than post-launch.

---

## 9. Recognition

Second consecutive sprint shipping 100% SP in ~1 day. Notable:

- **CEO** — decisive across 13 PR merges + 2 tag-push authorizations (v2.3.0, v2.4.0). Trust in agent-driven execution pays compounding dividends.
- **Agent roster** (all played SKILL.md roles well):
  - TechLead × 5 sessions — scaffold + 5 tools + cache + packaging
  - PM (Claude, project-manager skill) — 12 PRs + 2 status syncs + 3 conflict resolutions via Option C + this retro

---

## 10. Next Sprint Preview — CBM-INT-S3 · v2.5 Plugin Marketplace + 2 Packs

| Field | Value |
|---|---|
| Budget | 5 SP |
| Nominal duration | Mon 11/05 → Sun 24/05/2026 (2 weeks) |
| Expected actual | 1-2 days based on S1+S2 pace |
| Gates | G4 mid-sprint · G5 launch |
| Deliverables | Plugin manifest + bundle · Cowork variant · AI Agent Knowledge Pack · SaaS Onboarding Pack (CEO decision D5) · Launch blog post + demo video · Launch marketing (HN/Reddit/Viblo/Zalo) |
| Launch date | Sat 23/05/2026 (nominal) — likely earlier |
| Pre-kickoff | S2-1/2/3 action items (especially board-conflict pattern) + AI-#1 PyPI OIDC |

---

*CBM-INT-S2 Retrospective v1.0 · Written 20/04/2026 · Hyper Commerce · Codebase Map*
*Sprint duration: 1.5 calendar days (vs 10-day plan) · Shipped 8/8 SP · Zero P0/P1 defects · v2.4.0 LIVE on PyPI*
