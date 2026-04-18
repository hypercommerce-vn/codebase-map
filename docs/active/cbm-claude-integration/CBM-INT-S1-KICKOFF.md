# CBM-INT-S1 · v2.3 — Sprint Kickoff Briefing

> **From:** PM (Claude)
> **To:** TechLead · CTO · CEO
> **Status:** 🟢 LIVE — Day 1 Mon 20/04/2026
> **Sprint:** CBM-INT-S1 (PyPI + Claude Skill + Slash Commands) · 5 SP · 1 tuần
> **Paired docs:** [Technical Plan §1](./Technical_Plan_CBM_Claude_Integration.md) · [Strategy Memo](./Strategy_Memo_CBM_Claude_Integration.md)

---

## 1. Sprint Goal

Biến CBM v2.2 thành OSS package cài được qua `pipx install codebase-map` trong 30 giây, có Claude Code Skill trigger tự động khi user hỏi về impact / callers / refactor, kèm 3 slash command (`/cbm-onboard`, `/cbm-impact`, `/cbm-diff`).

**Business rationale:** Đây là Phase 1 của initiative CBM × Claude Integration — funnel CBM (public OSS) → KMP (private paid). Fail G1 → slip toàn bộ launch Sat 23/05/2026.

---

## 2. Timeline

```
Sun 19/04 ─ Day 0: Pre-flight blockers B1-B4 close
Mon 20/04 ─ Day 1: CBM-INT-101 PyPI publish (1 SP)
Tue 21/04 ─ Day 2: CBM-INT-102 SKILL.md (1 SP)
Wed 22/04 ─ Day 3: CBM-INT-103/104/105 slash commands (2 SP)
Thu 23/04 ─ Day 4: CBM-INT-106 integration test (0.5 SP)
Fri 24/04 ─ Day 5: QUICKSTART.md + v2.3.0 tag dry-run (0.5 SP) · Sprint demo 17:00
Sat 25/04 ─ Buffer
Sun 26/04 ─ Gate G1: CEO review 17:00 · Retro 18:00
```

**Capacity:** 5 SP trong 5 working days. Option B: 1 TechLead full-time + Tester=Claude + AI pair.

---

## 3. CEO Approvals Log

### D1-D7 · Strategic decisions (chốt 18/04/2026)

| # | Decision | Approved |
|---|---------|:--------:|
| D1 | MIT license giữ nguyên | ✅ |
| D2 | Launch 2 archetype (AI Agent + SaaS B2B) | ✅ |
| D3 | Song song Claude Integration + CBM-LANG-P1 | ✅ |
| D4 | Add Java parser (bên cạnh JS) | ✅ |
| D5 | Ship 2 pack đồng thời | ✅ |
| D6 | TechLead lead + CEO review weekly | ✅ |
| D7 | Coverage target 70%+ (Phương án B = 75%) | ✅ |

### A1-A5 · Kickoff approvals (chốt 19/04/2026)

| # | Action | Status | Verified |
|---|--------|:------:|----------|
| A1 | PyPI API token upload | ✅ | `gh secret list` → `PYPI_API_TOKEN` 18/04 16:58 |
| A2 | Make repo public | ✅ | `gh repo view` → `visibility: PUBLIC` |
| A3 | TechLead full-time 5 tuần | ✅ | Option B capacity locked |
| A4 | Tester role = Claude | ✅ | AI pair play Tester Day 4-5 |
| A5 | Sunday 17:00 weekly review | ✅ | G1-G5 cadence cố định |

---

## 4. Task Breakdown (6 tasks · 5 SP)

| Task | SP | Day | Owner | Output |
|------|:--:|:---:|-------|--------|
| CBM-INT-101 | 1 | D1 Mon 20/04 | TechLead | Package `codebase-map` v2.2.1 trên pypi.org |
| CBM-INT-102 | 1 | D2 Tue 21/04 | TechLead + CTO review | `integrations/claude-code/skills/codebase-map/SKILL.md` |
| CBM-INT-103 | 1 | D3 Wed 22/04 | TechLead | `commands/cbm-onboard.md` |
| CBM-INT-104 | 0.5 | D3 Wed 22/04 | TechLead | `commands/cbm-impact.md` |
| CBM-INT-105 | 0.5 | D3 Wed 22/04 | TechLead | `commands/cbm-diff.md` |
| CBM-INT-106 | 1 | D4-5 Thu-Fri | Tester (Claude) + TechLead | QUICKSTART.md + test matrix 5/5 pass + v2.3.0 tag dry-run |

Task-level DoD chi tiết: xem [Technical Plan §1](./Technical_Plan_CBM_Claude_Integration.md#1-phase-1--pypi--skill--slash-commands-5-sp--tuần-1).

---

## 5. Acceptance Criteria (Sprint-level)

| AC | Tiêu chí | Verify by |
|----|---------|-----------|
| AC-INT-01 | `pipx install codebase-map` < 30s trên macOS/Linux/WSL · v2.2.1 | Tester smoke test |
| AC-INT-02 | Claude Skill trigger ≥ 8/10 câu test ("what breaks", "impact of", "refactor") | Manual checklist |
| AC-INT-03 | 3 slash commands end-to-end OK trên HC repo | Manual run |
| AC-INT-04 | QUICKSTART.md + integration test 5/5 case pass | Tester report |
| AC-INT-05 | `v2.3.0` tag + GitHub Release + PyPI version đồng bộ | Version audit |
| AC-INT-06 | Lint gate pass · 582+ tests pass · No regression v2.2 | `pytest tests/` |

---

## 6. Pre-flight Blockers (Day 0 — Sun 19/04)

**Tất cả phải close trước Day 1 Mon 20/04 09:00.**

| # | Blocker | Severity | Owner | Action |
|---|---------|:--------:|-------|--------|
| B1 | `SECURITY.md` missing | 🔴 Critical | TechLead | Viết theo template GitHub OSS — vulnerability report inbox: hypercdp@gmail.com |
| B2 | Git history audit (secrets/PII) | 🔴 Critical | TechLead | `gitleaks detect --source . --log-opts="--all"` HOẶC `trufflehog git file://. --only-verified` → report findings |
| B3 | `CONTRIBUTING.md` missing | 🟡 High | TechLead | Viết: setup dev, lint gate, PR workflow, conventional commits |
| B4 | `.github/ISSUE_TEMPLATE/` + `pull_request_template.md` | 🟢 Medium | TechLead | Bug report + Feature request + PR template |

**B2 escalation:** nếu phát hiện secret leaked → STOP, ping CEO ngay. Rotate secret + BFG history cleanup trước khi tiếp tục.

---

## 7. Risk Register

| # | Risk | P×I | Score | Mitigation |
|---|------|:---:|:-----:|-----------|
| R1 | PyPI name `codebase-map` bị chiếm | 3×3 | 9 🔴 | Day 0 check `pip index versions codebase-map` · Fallback `cbm-graph` / `codebase-map-hc` |
| R2 | SECURITY.md + git audit chưa xong khi repo public | 3×3 | 9 🔴 | B2 critical path · TechLead delegated Sun 19/04 · CEO sign-off 19:00 |
| R3 | Claude Skill trigger không fire | 2×3 | 6 🟡 | Day 2 test ≥5 user prompt variants · CTO review trigger rules |
| R4 | AI pair pace slow (docs chậm) | 2×2 | 4 🟡 | Day 4 check-in · Cut AC-INT-05 sang S2 nếu cần |
| R5 | pipx install fail Windows/WSL | 1×2 | 2 🟢 | Day 5 Tester test · Document workaround · Không block |

---

## 8. Communication

| Ceremony | Format | Cadence | Channel |
|----------|--------|---------|---------|
| Daily standup | Async 3-dòng (Yesterday / Today / Blockers) | Mon-Fri 9:00 | Telegram group "CBM-INT-S1 Daily" (CEO tạo 19/04) |
| Mid-week check-in | Quick sync | Wed 17:00 | Telegram |
| Sprint demo | Live demo 3 slash commands end-to-end | Fri 24/04 17:00 | Zoom/Meet |
| CEO review (Gate G1) | Go/No-go + retro | Sun 26/04 17:00 | Zoom/Meet |

---

## 9. Definition of Done (Sprint)

- [ ] 6/6 tasks CBM-INT-101→106 complete với task-level DoD
- [ ] 6/6 Acceptance Criteria pass
- [ ] `/review-gate` 3 tầng (Tester + CTO + Designer) PASS cho tất cả PR
- [ ] CEO approve merge · Tag `v2.3.0` push · GitHub Release published
- [ ] Board SSOT + BRIEF.md updated reflecting completion
- [ ] Retrospective done · Action items carry sang S2

---

## 10. Escalation Protocol

| Scenario | Action |
|----------|--------|
| Sprint trễ ≤ 10% (0.5 SP) | PM tự xử — replan, buffer Sat |
| Sprint trễ 10-25% (1-1.5 SP) | Báo CEO mid-week · Scope cut AC-INT-05 (tag dry-run sang S2) |
| Sprint trễ > 25% | Escalate CEO ngay · Emergency planning · Review gate criteria |
| Secret leak detected (B2) | STOP · Ping CEO · Rotate + BFG cleanup · Không kick D1 until clean |
| PyPI name collision (R1) | PM auto-fallback `cbm-graph` · Update pyproject.toml · Document trong release notes |

---

## 11. Next Sprint Preview

**CBM-INT-S2 · v2.3 — MCP Server** (8 SP · Week 2-3 · Mon 27/04 → Sun 10/05/2026)

- MCP server scaffold (Python, reuse `codebase_map` package)
- 5 tools: `cbm_query`, `cbm_search`, `cbm_impact`, `cbm_snapshot_diff`, `cbm_api_catalog`
- Graph cache + mtime invalidation
- Publish `codebase-map-mcp` PyPI
- Gate G2 mid-sprint (Sun 03/05) · Gate G3 (Sun 10/05)

---

*PM Kickoff Briefing v1.0 · Created 19/04/2026 · Codebase Map · CBM-INT-S1*
