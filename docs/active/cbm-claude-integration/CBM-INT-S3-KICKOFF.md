# CBM-INT-S3 · v2.5 — Plugin Marketplace + 2 Archetype Packs · Sprint Kickoff

> **From:** PM (Claude)
> **To:** TechLead · CTO · CEO
> **Status:** 🚀 **LIVE — Day 1 Tue 21/04/2026** (fast-track from original Mon 11/05 — **20 days early**)
> **Sprint:** CBM-INT-S3 (Plugin bundle + 2 Packs + Launch marketing) · 5 SP
> **This is the FINAL sprint of the CBM × Claude Integration initiative.**
> **Paired docs:** [Tech Plan §3](./Technical_Plan_CBM_Claude_Integration.md#3-phase-3--plugin-marketplace-5-sp--tuần-3) · [Project Archetype GTM Strategy](./Project_Archetype_GTM_Strategy.md) · [S1 Retro](./CBM-INT-S1-Retrospective.md) · [S2 Retro](./CBM-INT-S2-Retrospective.md)

---

## 1. Sprint Goal

Đóng gói CBM v2.4 (CLI + Skill + 3 slash cmds + MCP server) thành **Claude Plugin** cho 1-click install, kèm **2 archetype packs** (AI Agent Knowledge + SaaS Onboarding) theo CEO D5, và launch marketing cho cộng đồng.

**Business rationale:** Đây là mảnh cuối đóng vòng funnel. Users từ nay install qua `/plugin install cbm` trong Cowork, không cần nhớ pipx + skill + commands riêng. Pack format cho phép monetize hint cho KMP (Open Core model).

**Launch target:** Sat 23/05/2026 nominal. Với pace S1 + S2 (1 day / sprint), **likely launch sớm hơn 30+ ngày**.

---

## 2. Timeline (fast-track)

Original Tech Plan: Mon 11/05 → Sun 24/05/2026 (2 tuần).
**Actual kickoff:** Tue 21/04 (20 days early).

| Day | Date | SP | Tasks |
|:---:|:----:|:--:|-------|
| D1 | Tue 21/04 | 1 | CBM-INT-301 Plugin manifest + bundle · CBM-INT-302 Post-install hook |
| D2 | Wed 22/04 | 1 | CBM-INT-303 Publish to `hypercommerce-vn/claude-plugins` |
| D3 | Thu 23/04 | 1.5 | CBM-INT-304 Cowork variant (AI Agent Pack + SaaS Pack skills + commands) |
| D4 | Fri 24/04 | 0.5 | CBM-INT-305 Launch blog post + demo video (2 min Loom) |
| D5 | Sat 25/04 | — | 🚀 **LAUNCH** — HN / Reddit / Viblo / Zalo posts |
| Buffer | Sun 26/04 | — | Fix G4 blockers nếu có |
| **Gate G5** | Sun 26/04 | — | CEO review · LAUNCH retro · Initiative complete |

**Likely outcome (based on S1 + S2 velocity 0.15-0.2 days/SP):** compress to 1-2 days actual, launch possibly Wed 22/04 or Thu 23/04.

---

## 3. Task Breakdown (5 tasks · 5 SP)

| Task | SP | Day | Owner | Deliverable |
|------|:--:|:---:|-------|-------------|
| CBM-INT-301 Plugin manifest + bundle | 1 | D1 | TechLead | `.plugin` file · manifest.json · Cowork plugin structure |
| CBM-INT-302 Post-install hook | 1 | D1 | TechLead | `hooks/post-install.sh` installs CBM + MCP via pipx · idempotent · cross-platform (macOS/Linux/WSL) |
| CBM-INT-303 Publish to marketplace | 1 | D2 | TechLead + CEO | New repo `hypercommerce-vn/claude-plugins` (or fork existing Anthropic marketplace) · plugin discoverable |
| CBM-INT-304 Cowork variant (2 Archetype Packs) | 1.5 | D3 | TechLead + AI pair | `plugins/codebase-map-cowork/` with AI Agent Knowledge Pack + SaaS Onboarding Pack (bilingual English/Vietnamese per CEO D5) |
| CBM-INT-305 Launch blog + demo video | 0.5 | D4 | AI pair + CEO | 800-word blog (dev.to + Medium + HC blog crosspost) · 2-minute Loom demo video |

Task-level DoD: see [Tech Plan §3](./Technical_Plan_CBM_Claude_Integration.md).

---

## 4. Acceptance Criteria (Sprint-level)

| AC | Tiêu chí | Verify by |
|----|---------|-----------|
| AC-S3-01 | Plugin install < 30s on Claude Code | Manual run |
| AC-S3-02 | Plugin install < 30s on Cowork (non-dev user) | User test (PM/PO) |
| AC-S3-03 | Post-install hook PASS trên macOS + Linux + WSL | Smoke tests |
| AC-S3-04 | 2 Archetype Packs (AI Agent + SaaS) installable + tested | Manual run + CEO sign-off |
| AC-S3-05 | Blog post published · 100+ views 48h | Analytics |
| AC-S3-06 | Demo video 100+ views tuần đầu | YouTube/Loom analytics |
| AC-S3-07 | Lint + 158/158 tests + no regression | `pytest` + lint |

---

## 5. Pre-S3 Backlog (from S1+S2 Retros)

**Must-close BEFORE Day 1 start (or accept risk):**

| # | Item | Severity | Owner | Status |
|---|------|:--------:|-------|:------:|
| S2-1 | **Board-progress conflict pattern** — feature PRs skip `project/board.html` progress label · PM ships separate board sync | 🔴 Critical | PM | **Applied from this kickoff** — feature PR Day 1 tests pattern |
| AI-#7 | Enable GitHub Settings (secret scanning · Dependabot · branch protection main) | 🟡 Medium | CEO | Still open from S1 |
| AI-#1 | PyPI OIDC Trusted Publisher (drop `PYPI_API_TOKEN` secret) | 🟡 Medium | TechLead | S3 Day 1 recommended |

**Nice-to-have during S3:**

| # | Item | Target |
|---|------|:------:|
| S2-2 | Live Claude Desktop dry-run (AC-S2-03) | CEO action post-launch |
| S2-3 | Remove `mcp_server/__init__.py __version__` (redundant) | S3 Day 1 cleanup |
| AI-#2 | Test asserting `__version__` matches pyproject | S3 Day 1 |
| AI-#4 | PyPI release runbook doc | S3 Day 2 |
| AI-#5 | Linux + WSL pipx smoke tests | S3 Day 4 |
| AI-#9 | Config path UX improvement | S3 backlog |
| AI-#10 | `/cbm-diff` default branch auto-detect | S3 backlog |

---

## 6. Risk Register

| # | Risk | P×I | Score | Mitigation |
|---|------|:---:|:-----:|-----------|
| R-S3-1 | Claude Plugin Marketplace schema/API changes (still research preview) | 3×3 | 9 🔴 | Follow Anthropic Cowork changelog weekly · Phase 1 + 2 stand-alone usable if Phase 3 breaks · documented fallback |
| R-S3-2 | Post-install hook fails on Windows/WSL path edge cases | 2×2 | 4 🟡 | Day 4 AI-#5 smoke tests · fallback to manual install instructions in plugin README |
| R-S3-3 | Cowork plugin marketplace rejection (quality bar uncertain) | 2×3 | 6 🟡 | Pre-submit review via CTO checklist · have fallback to self-host via GitHub raw URL |
| R-S3-4 | Launch day PR crashes HN/Reddit | 1×2 | 2 🟢 | Blog post emphasizes quick win (`/plugin install cbm` → 30s onboarding) · demo video visual-first · CEO schedules peak HN time (Tue-Thu 8-10am PT) |
| R-S3-5 | 2 Archetype Pack content quality (bilingual requires care) | 2×2 | 4 🟡 | D3 PM + CEO review before ship · borrow templates from existing Cowork skills (per SKILL.md conventions) |

---

## 7. Key Design Decisions

### Plugin architecture (per Tech Plan §3.2)

```
claude-plugins/
├── README.md                        # Marketplace overview
├── marketplace.json                 # Plugin index
└── plugins/
    └── codebase-map/
        ├── manifest.json
        ├── README.md
        ├── skills/
        │   └── codebase-map/
        │       └── SKILL.md         # Reuse S1 skill
        ├── commands/
        │   ├── cbm-onboard.md       # Reuse S1 commands
        │   ├── cbm-impact.md
        │   └── cbm-diff.md
        ├── mcp/
        │   └── config.json          # Reuse S2 MCP config
        └── hooks/
            ├── post-install.sh      # NEW: install CBM + MCP via pipx
            └── pre-uninstall.sh     # NEW: cleanup
```

### Post-install hook pattern

```bash
#!/usr/bin/env bash
# HC-AI | ticket: FDD-TOOL-CODEMAP
set -euo pipefail
command -v pipx > /dev/null || python3 -m pip install --user pipx
pipx install 'codebase-map[mcp]' || pipx upgrade 'codebase-map[mcp]'
echo "✅ CBM installed. Try: /cbm-onboard"
```

### 2 Archetype Packs (per CEO D5)

**AI Agent Knowledge Pack:**
- Skill: bilingual English/Vietnamese · triggers on "how is this agent structured", "what tools does this agent have", "refactor my agent flow"
- Commands: `/agent-overview`, `/agent-impact`, `/agent-refactor-plan`
- Example scenarios: Claude agent project audit, multi-agent workflow mapping

**SaaS Onboarding Pack:**
- Skill: triggers on "onboard this SaaS codebase", "what APIs do we expose", "what's our pricing tier logic"
- Commands: `/saas-onboard`, `/saas-apis`, `/saas-tier-logic`
- Example scenarios: New dev joining team, refactor payment flow, audit multi-tenant boundaries

---

## 8. Definition of Done (Sprint)

- [ ] 5/5 tasks CBM-INT-301→305 complete
- [ ] 7/7 AC met
- [ ] Plugin installable via `/plugin install cbm` trong Cowork
- [ ] 2 Archetype Packs shipped với content reviewed
- [ ] Blog post + demo video live
- [ ] `/review-gate` 3 tầng PASS
- [ ] CEO approve merge · Tag `v2.5.0` push · GitHub Release published
- [ ] Board SSOT + BRIEF.md updated · Retrospective done
- [ ] Launch day posts (HN/Reddit/Viblo/Zalo) published

---

## 9. Communication (same as S2)

- **Tracking:** `project/board.html` SSOT (no Telegram)
- **Daily standup:** Async via PR descriptions
- **Weekly CEO review:** Sunday 17:00 (Gate G4 Sun 26/04 · Gate G5 launch retro)
- **Escalation:** Same protocol as S1 + S2 retros

## 10. Merge Conflict Prevention (from S2 Retro §3 Stop)

**New rule applied this sprint:** Feature PRs **exclude** `project/board.html` progress label edits. PM owns progress updates via separate status sync PRs AFTER feature merges. Testing this convention on Day 1.

**Rationale:** S2 had 3 recurring conflicts (#123, #127, #130) all from status sync + feature PR both editing progress bar. S3 tests the clean split.

---

## 11. Next Steps After S3 — Initiative Close

After CBM-INT-S3 merges, the **CBM × Claude Integration Initiative is COMPLETE**:
- ✅ Phase 1 S1 — PyPI + Skill + slash commands (v2.3.0)
- ✅ Phase 2 S2 — MCP Server (v2.4.0)
- 🚀 Phase 3 S3 — Plugin + 2 Packs + Launch (v2.5.0)

**Total scope:** 20 SP Claude Integration + 13 SP CBM-LANG-P1 (JS+Java, deferred post-launch).

**Post-launch:**
- Monitor metrics (PyPI downloads, plugin installs, MCP tool calls, HN/Reddit engagement)
- Submit MCP registry PR (AC-S2-05 deferred)
- Schedule CBM-LANG-P1 sprint (JS + Java parsers)
- KMP integration discussion (Open Core funnel)

---

*CBM-INT-S3 Kickoff v1.0 · Created 21/04/2026 · Hyper Commerce · Codebase Map*
*Fast-track from Mon 11/05 → Tue 21/04 (20 days early) · Final sprint of Claude Integration initiative · 5 SP budget*
