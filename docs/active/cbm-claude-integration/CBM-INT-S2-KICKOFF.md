# CBM-INT-S2 · v2.4 — MCP Server (Core Moat) · Sprint Kickoff Briefing

> **From:** PM (Claude)
> **To:** TechLead · CTO · CEO
> **Status:** 🚀 **LIVE — Day 1 Mon 20/04/2026** (fast-track from original Mon 27/04 — 7 days early)
> **Sprint:** CBM-INT-S2 (MCP Server scaffold + 5 tools + graph cache + PyPI `codebase-map-mcp`)
> **Budget:** 8 SP · 2 tuần nominal (likely compress based on S1 pace)
> **Paired docs:** [Tech Plan §2](./Technical_Plan_CBM_Claude_Integration.md#2-phase-2--mcp-server-8-sp--tuần-2) · [Phase 2 Explainer](./Phase2_MCP_Explainer.md) · [S1 Retrospective](./CBM-INT-S1-Retrospective.md) · [S1 Verification Report](./CBM-INT-S1-Verification-Report.md)

---

## 1. Sprint Goal

Build **MCP Server** (Model Context Protocol) cho CBM — exposing 5 query tools to Claude Code / Cowork / Desktop via stdio transport. Moves from Phase 1 slash-command UX (user gõ `/cbm-impact X`) to Phase 2 auto-invoke UX (Claude tự chọn tool khi user hỏi natural language).

**Business rationale:** Đây là core moat vs competitors (repomix, serena). MCP = UX cao nhất trong Claude ecosystem. Retention target 15% → 50% per [Phase2 Explainer](./Phase2_MCP_Explainer.md).

**Output:** `codebase-map-mcp` PyPI package · 5 MCP tools · graph cache · integration docs.

---

## 2. Timeline (fast-track)

Original Tech Plan: Mon 27/04 → Sun 10/05 (2 tuần).
**Actual kickoff:** Mon 20/04 (7 days early, given S1 finished in Day 0).

| Day | Date | SP | Tasks |
|:---:|:----:|:--:|-------|
| D1 | Mon 20/04 | 1 | CBM-INT-201 MCP server scaffold |
| D2 | Tue 21/04 | 2 | CBM-INT-202 `cbm_query` + `cbm_search` · CBM-INT-203 `cbm_impact` |
| D3 | Wed 22/04 | 2 | CBM-INT-204 `cbm_snapshot_diff` (complex) |
| D4 | Thu 23/04 | 1.5 | CBM-INT-205 `cbm_api_catalog` · CBM-INT-206 graph cache manager |
| D5 | Fri 24/04 | 1.5 | CBM-INT-207 PyPI publish `codebase-map-mcp` · CBM-INT-208 integration test + docs |
| Buffer | Sat 25/04 | — | Fix G2 blockers nếu có |
| **Gate G2** | **Sun 26/04 17:00** | — | Mid-sprint CEO review: MCP scaffold + 3/5 tools working |
| Gate G3 nominal | Sun 03/05 17:00 | — | Full 5 tools + PyPI live (if pace slips to plan) |

**Likely outcome (based on S1 velocity):** compress to 2-3 days actual, making G2/G3 merge into 1 final ceremony.

---

## 3. Task Breakdown (8 tasks · 8 SP)

| Task | SP | Day | Owner | Deliverable |
|------|:--:|:---:|-------|-------------|
| CBM-INT-201 MCP server scaffold | 1 | D1 | TechLead | `mcp_server/` folder · `server.py` · stdio entrypoint · `python -m mcp_server` works |
| CBM-INT-202 `cbm_query` + `cbm_search` | 1 | D2 | TechLead | 2 tools in `mcp_server/tools/` · JSON schema valid per MCP Inspector |
| CBM-INT-203 `cbm_impact` | 1 | D2 | TechLead | Tool with depth param · blast radius response |
| CBM-INT-204 `cbm_snapshot_diff` | 2 | D3 | TechLead | Most complex — baseline/current labels, markdown/json output, depth, breaking_only, test_plan flags |
| CBM-INT-205 `cbm_api_catalog` | 0.5 | D4 | TechLead | Tool with method + domain filters |
| CBM-INT-206 Graph cache manager | 1 | D4 | TechLead | `graph_cache.py` · mtime-based invalidation · 10MB graph load < 500ms target |
| CBM-INT-207 Packaging + PyPI publish | 1 | D5 | TechLead | `codebase-map-mcp` PyPI · entry point `cbm-mcp` |
| CBM-INT-208 Integration test + docs | 0.5 | D5 | Tester (Claude) | MCP Inspector tests · Claude Desktop config example · registry submission |

Task-level DoD: see [Tech Plan §2](./Technical_Plan_CBM_Claude_Integration.md).

---

## 4. Acceptance Criteria (Sprint-level)

| AC | Tiêu chí | Verify by |
|----|---------|-----------|
| AC-S2-01 | 5 tools pass schema validation (Anthropic MCP Inspector) | Tester |
| AC-S2-02 | Graph 10MB load < 500ms · query < 100ms | Benchmark |
| AC-S2-03 | Claude Code auto-invoke 5 tools correctly for 20 test questions | Manual dry-run |
| AC-S2-04 | `pipx install codebase-map-mcp` → `cbm-mcp` entry point works | Smoke test |
| AC-S2-05 | MCP registry submission (PR to anthropic-mcp) opened | Checklist |
| AC-S2-06 | Lint + 158/158 tests + no regression trên existing CBM | `pytest` + lint |

---

## 5. Pre-kickoff Blockers & Backlog (from S1 Retro §7)

**Must-close BEFORE Day 1 start (or accept risk):**

| # | Item | Severity | Owner | Status |
|---|------|:--------:|-------|:------:|
| AI-#6 | Clean up 44 uncommitted working-tree files (S1 docs cleanup Option B) | 🟡 Medium | PM | ⏳ **Pending** |
| AI-#7 | Enable GitHub Settings (secret scanning, Dependabot, branch protection) | 🟡 Medium | CEO | ⏳ Pending |

**Nice-to-have during S2 (parallel track):**

| # | Item | Severity | Owner | Target day |
|---|------|:--------:|-------|:---------:|
| AI-#1 | PyPI OIDC Trusted Publisher config | 🟢 Low | TechLead | D1 |
| AI-#2 | Add `__version__` == pyproject.toml test | 🟢 Low | TechLead | D1 |
| AI-#3 | Live Claude Code skill trigger dry-run | ✅ DONE | — | Verified in E2E 20/04 |
| AI-#4 | Document PyPI release runbook | 🟢 Low | PM | D2 |
| AI-#5 | Linux + WSL pipx smoke tests | 🟢 Low | Tester | D5 |
| AI-#8 | Update AC-INT-06 "582+" → "158+" tests | ✅ DONE | — | In retro v1.1 |
| AI-#9 | Config path resolution UX improvement | 🟢 Low P3 | TechLead | D3-4 |
| AI-#10 | `/cbm-diff` default branch auto-detect | 🟢 Low P3 | TechLead | D3-4 |

---

## 6. Risk Register

| # | Risk | P×I | Score | Mitigation |
|---|------|:---:|:-----:|-----------|
| R-S2-1 | MCP protocol schema changes (Anthropic side) | 2×3 | 6 🟡 | Pin `mcp>=X` version · semver-strict · follow Anthropic changelog weekly |
| R-S2-2 | Graph 10MB+ load perf regression | 2×2 | 4 🟡 | D4 benchmark · lazy load · mtime cache; fallback to stream response |
| R-S2-3 | `cbm_snapshot_diff` complexity underscoped | 2×3 | 6 🟡 | 2 SP budget · TechLead prioritize D3 full day · fall back to mvp tool (just labels, no test-plan flag) if slips |
| R-S2-4 | PyPI name `codebase-map-mcp` taken | 1×2 | 2 🟢 | Check D1 first; fallback `cbm-mcp` or `cbm-mcp-server` |
| R-S2-5 | 44 uncommitted S1 files drift cause merge conflicts | 2×2 | 4 🟡 | AI-#6 priority clean before D1 OR isolate S2 branches strictly |

---

## 7. Architecture Reference

Per [Tech Plan §2.2](./Technical_Plan_CBM_Claude_Integration.md):

```
codebase-map/
└── mcp_server/                    # NEW folder (this sprint)
    ├── __init__.py
    ├── __main__.py                # python -m mcp_server
    ├── server.py                  # MCP Server main
    ├── graph_cache.py             # Lazy load + in-memory cache
    └── tools/
        ├── __init__.py
        ├── query.py               # cbm_query
        ├── search.py              # cbm_search
        ├── impact.py              # cbm_impact
        ├── snapshot_diff.py       # cbm_snapshot_diff
        └── api_catalog.py         # cbm_api_catalog
```

**Tech choice:** Python (reuse `codebase_map` package) — no Node rewrite. Uses official Anthropic `mcp` SDK (stdio transport).

**Deployment config example** (Claude Desktop):

```json
{
  "mcpServers": {
    "codebase-map": {
      "command": "uvx",
      "args": ["--from", "codebase-map-mcp", "cbm-mcp"]
    }
  }
}
```

---

## 8. Definition of Done (Sprint)

- [ ] 8/8 tasks CBM-INT-201→208 complete
- [ ] 6/6 AC met
- [ ] `pipx install codebase-map-mcp` LIVE on PyPI
- [ ] MCP Inspector validates all 5 tool schemas
- [ ] Claude Desktop config example tested
- [ ] Benchmark: graph 10MB load < 500ms, query < 100ms
- [ ] `/review-gate` 3 tầng PASS
- [ ] CEO approve merge · Tag `v2.4.0` push · GitHub Release published
- [ ] Board SSOT + BRIEF.md updated
- [ ] Retrospective done
- [ ] Registry submission opened (Anthropic MCP registry)

---

## 9. Communication (same as S1)

- **Tracking:** `project/board.html` SSOT (no Telegram per CEO decision 19/04)
- **Daily standup:** Async via PR descriptions
- **Weekly CEO review:** Sunday 17:00 (Gate G2 Sun 26/04, G3 Sun 03/05 nominal — likely compresses)
- **Escalation:** Same protocol as S1 retro §10

---

## 10. Next Sprint Preview — CBM-INT-S3 · v2.4 Plugin + 2 Packs

(Paused pending S2 completion)

- Plugin manifest + bundle → Claude Plugin Marketplace
- AI Agent Knowledge Pack + SaaS Onboarding Pack (CEO decision D5)
- Launch blog + demo video
- Budget: 5 SP · Week 4-5 nominal
- Gates G4/G5

Also parallel: CBM-LANG-P1 (JS + Java parsers, 13 SP, Q2 target post-launch).

---

*CBM-INT-S2 Kickoff v1.0 · Created 20/04/2026 · Hyper Commerce · Codebase Map*
*Fast-track from Mon 27/04 → Mon 20/04 (7 days early) · Based on S1 velocity · 8 SP budget*
