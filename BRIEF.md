# BRIEF.md — Codebase Map Session Brief
> **Đọc file này ĐẦU TIÊN mỗi session. Cập nhật cuối mỗi session.**
> Version: 5.1 | Cập nhật: 21/04/2026 (🎉 S1+S2 SEALED · 🚀 S3 LIVE Day 1 — Plugin + 2 Packs · FINAL sprint · 20 ngày sớm schedule)

---

## 🎯 TRẠNG THÁI HIỆN TẠI

**Codebase Map v2.2 — Production ready — Public OSS**

Tất cả sprints COMPLETE (85 SP, 582 tests):
- v1.0 — Core graph generator ✅
- v1.1 — CM-S1 UX polish (15 SP) ✅
- v1.2 — CM-S2 Workflow tool (18 SP) ✅
- v2.0 — CM-S3 Multi-view + TypeScript (22 SP) ✅
- v2.0.1 — Hotfix (3 SP) ✅
- v2.1 — CBM-P1 Metadata + Snapshots (7 SP) ✅
- v2.2 — CBM-P2 Dual-Snapshot Diff Engine (12 SP) ✅

**Repo split 16/04/2026:** KMP (Knowledge AI Platform) tách sang repo riêng (private):
- KMP repo: https://github.com/hypercommerce-vn/knowledge-AI-platform
- CBM repo (this): standalone public OSS — free unlimited CI on GitHub Actions

---

## 🏗️ KIẾN TRÚC HIỆN TẠI

```
CBM (public OSS) = stateless data generator
    ↓ subprocess call (no library coupling)
KMP (private) = stateful intelligence layer
    github.com/hypercommerce-vn/knowledge-AI-platform
```

CBM không biết gì về KMP. KMP gọi CBM qua `subprocess.run(["codebase-map", ...])`.

---

## 📦 COMMANDS

```bash
# Install
pip install -e ".[dev]"

# Generate + query
codebase-map generate -c codebase-map.yaml
codebase-map summary -f docs/function-map/graph.json
codebase-map query "ClassName" -f graph.json
codebase-map impact "ServiceName" -f graph.json
codebase-map search "keyword" -f graph.json

# Dual-Snapshot (v2.2)
codebase-map generate --label "baseline"
codebase-map generate --label "post-dev"
codebase-map snapshot-diff --baseline baseline --current post-dev --format markdown

# Git diff impact
codebase-map diff main -f graph.json

# Management
codebase-map snapshots list
codebase-map api-catalog -f graph.json
codebase-map coverage -f graph.json
codebase-map check-staleness -f graph.json
```

---

## 🧪 TEST & LINT

```bash
pytest tests/ -q                                    # 158 tests
black --check codebase_map/ tests/
isort --check codebase_map/ tests/
flake8 codebase_map/ tests/
```

---

## 📁 REPO STRUCTURE

```
codebase-map/
├── codebase_map/                  # Source (48 modules)
├── tests/codebase_map/            # 158 tests
├── specs/spec.md                  # FDD spec
├── docs/
│   ├── cbm-dual-snapshot/         # Phase 1+2 proposals
│   ├── function-map/              # Generated outputs
│   ├── reviews/                   # CBM review reports (15 files)
│   └── releases/                  # Release notes
├── design-preview/
│   └── codebase-map-*.html        # CM-S1/S2/S3/v2 designs
├── project/
│   ├── board.html                 # CBM board (SSOT)
│   └── CM-*.md                    # Task boards
├── agents/                        # 7 AI agents (shared)
├── .claude/                       # Claude Code config
├── .github/workflows/             # 4 CI workflows
├── pyproject.toml                 # CBM only (codebase-map package)
├── README.md                      # Public-facing docs
├── LICENSE                        # MIT
└── CLAUDE.md                      # Project instructions
```

---

## 🔁 WORKFLOW RULES

1. KHÔNG push thẳng main — mọi thay đổi qua PR
2. PR Per Day — 1 PR/day → CEO approve
3. /review-gate 3 tầng (Tester → CTO → Designer) trước CEO
4. Lint gate trước commit: black + isort + flake8
5. Conventional Commits: `feat(...):` `fix(...):` `chore(...):`
6. No Design = No Implementation cho FE changes
7. Board SSOT — mọi thay đổi sync lên `project/board.html`

---

## 🚀 INITIATIVE ĐANG MỞ — CBM Claude Integration (2026-04-16)

**Mục tiêu:** Biến CBM từ tool nội bộ thành OSS dev tool chủ lực, tích hợp vào hệ sinh thái Claude (Claude Code + Cowork + Desktop) qua 3 pha: PyPI+Skill → MCP server → Plugin Marketplace. Làm funnel cho KMP (Open Core model).

**7 tài liệu chiến lược** trong `docs/active/cbm-claude-integration/`:

1. `Strategy_Memo_CBM_Claude_Integration.md` — 4 path phân tích, khuyến nghị Path D (combo 3 phase), risk register
2. `Technical_Plan_CBM_Claude_Integration.md` — Phase 1 PyPI+Skill (5 SP) + Phase 2 MCP (8 SP) + Phase 3 Plugin (5 SP) = **18 SP total**
3. `Language_Coverage_Analysis.md` — CBM Python+TS cover 38% dev; thêm JS+Java = 75% (13 SP)
4. `Project_Archetype_GTM_Strategy.md` — AI Agent + SaaS B2B là Tier 1 (CBM cover 100%, launch ngay)
5. `CBM_UI_Preview_Integration.md` — UI v2.0 tái sử dụng 100% qua multi-view MCP adapter
6. `Open_Source_Publishing_Strategy.md` — **Open Core confirmed**: CBM public + KMP private, ROI 17x
7. `Phase2_MCP_Explainer.md` — Slash Command vs MCP auto-invoke (retention 15% → 50%)

**Expected ROI:** ~$86k ARR năm 1 vs $5k cost (17x).

**CEO decisions (chốt 18/04/2026 — full 7/7):**

- **D1 = MIT** giữ nguyên license
- **D2 = 2 archetype** — AI Agent + SaaS B2B (Python+TS 100% cover)
- **D3 = Song song** — Claude Integration chạy cùng CBM-LANG-P1 (JS+Java)
- **D4 = Java** (implicit từ D3)
- **D5 = Pack bundle** — Ship 2 pack: AI Agent Knowledge Pack + SaaS Onboarding Pack
- **D6 = TechLead lead + CEO review weekly** maintain repo public
- **D7 = 70% coverage** qua Phương án B (JS+Java = 75%)

**Tổng scope:** 33 SP (Claude Integration 20 SP + Language 13 SP), song song 2 track.

**Capacity Option B:** 1 TechLead full-time + AI pair → **5 tuần** (launch Sat 23/05/2026), 0 chi phí thêm.

---

## ✅ CEO KICKOFF APPROVALS — 5/5 (19/04/2026)

| # | Action | Status | Evidence |
|---|--------|:------:|----------|
| A1 | PyPI API token upload | ✅ Done | `PYPI_API_TOKEN` secret trong repo (created 18/04 16:58) |
| A2 | Make repo public | ✅ Done | `visibility: PUBLIC` verified qua `gh repo view` |
| A3 | TechLead full-time 5 tuần | ✅ Confirmed | Option B capacity locked |
| A4 | Tester role | ✅ Claude | AI pair play Tester Day 4-5 |
| A5 | Weekly review cadence | ✅ Sun 17:00 | G1-G5 cố định Sunday |

---

## ✅ SPRINT CBM-INT-S1 SEALED (19-20/04/2026)

- **5/5 SP** shipped trong 1 calendar day (5 ngày sớm schedule)
- **12 PRs merged** (#104-#116) · **0 P0/P1/P2 defects** · **158/158 tests PASS**
- **2 PyPI releases LIVE:** `codebase-map` [v2.2.1](https://pypi.org/project/codebase-map/2.2.1/) + [v2.3.0](https://pypi.org/project/codebase-map/2.3.0/)
- **E2E CEO verification 20/20** (Level 1+2A+2B+2C) → Gate G1 GO ✅
- Deliverables: PyPI package · Claude Skill · 3 slash commands · QUICKSTART · Retrospective · Verification Report

## 🎉 SPRINT CBM-INT-S2 SEALED (20/04/2026)

- **8/8 SP** in 1.5 calendar days (vs 10-day plan — **8.5 days early**)
- **13 PRs merged** (11 feature + 2 status syncs · 3 superseded by v2 rebase)
- **0 P0/P1/P2 defects** · **158/158 tests PASS** · Lint clean
- **v2.4.0 LIVE on PyPI** — workflow 24679777408 SUCCESS 29s
- **5 MCP tools LIVE:** `cbm_query` · `cbm_search` · `cbm_impact` · `cbm_snapshot_diff` · `cbm_api_catalog`
- **Entry point:** `cbm-mcp` (via `pipx install codebase-map[mcp]==2.4.0`)
- **Graph cache 40× speedup** (AC-S2-02 closed: Cold 2.8ms → Hot 0.071ms)
- **E2E Verification: 18/20 PASS** (2 deferred: live Claude Desktop dry-run + MCP registry PR — CEO post-launch action)
- **Docs shipped:** `v2.4.0.md` release notes · `integrations/mcp/README.md` Claude Desktop config · `REGISTRY_SUBMISSION.md` prep · Day 5 test report · Retro + Verify Report

**S2 Retro:** `docs/active/cbm-claude-integration/CBM-INT-S2-Retrospective.md` (10 sections · 4 S2-specific + 6 AI carried from S1)
**S2 Verify:** `docs/active/cbm-claude-integration/CBM-INT-S2-Verification-Report.md` (L1 5/5 + L2A 5/5 + L2B cache bench + L2C 12/12)

---

## 🚀 SPRINT CBM-INT-S3 · LIVE Day 1 Tue 21/04/2026 (FINAL sprint)

**Sprint goal:** Đóng gói CBM thành Claude Plugin 1-click install (Cowork) · 2 Archetype Packs (AI Agent + SaaS per CEO D5) · Launch marketing. **Final sprint của Claude Integration initiative.**

**Timeline (fast-track, 20 ngày sớm original Mon 11/05):**
- Day 1 Tue 21/04 — CBM-INT-301 Plugin manifest + bundle · CBM-INT-302 Post-install hook (2 SP)
- Day 2 Wed 22/04 — CBM-INT-303 Publish marketplace `hypercommerce-vn/claude-plugins` (1 SP)
- Day 3 Thu 23/04 — CBM-INT-304 Cowork variant (AI Agent Knowledge Pack + SaaS Onboarding Pack, bilingual EN/VI) (1.5 SP)
- Day 4 Fri 24/04 — CBM-INT-305 Launch blog 800 words + Loom demo video 2 min (0.5 SP)
- Day 5 Sat 25/04 — 🚀 LAUNCH — HN/Reddit/Viblo/Zalo posts
- Gate G5 Sun 26/04 — CEO review · LAUNCH retro · Initiative complete

**Kickoff brief:** `docs/active/cbm-claude-integration/CBM-INT-S3-KICKOFF.md`

**AC-S3-01→07:** Plugin install < 30s (Claude Code + Cowork) · Post-install hook macOS/Linux/WSL · 2 Packs installable · Blog 100+ views 48h · Demo video 100+ views tuần đầu · Lint + 158/158 no regression

**Rule #S2-1 applied:** Feature PRs skip `project/board.html` progress label. PM ships separate status sync after each feature merge. Addresses S2's 3 recurring conflicts.

## 📋 Pre-S3 Backlog

- [ ] **AI-#1** PyPI OIDC Trusted Publisher (S3 Day 1 recommended)
- [ ] **AI-#7** GitHub Settings (secret scanning · Dependabot · branch protection) — CEO action, not blocking
- [ ] S2-2 Live Claude Desktop dry-run (AC-S2-03 deferred)
- [ ] S2-3 Remove redundant `mcp_server/__init__.py __version__` (S3 Day 1 cleanup)
- [ ] AI-#2 Test `__version__` == pyproject (S3 Day 1)
- [ ] AI-#4 PyPI release runbook doc (S3 Day 2)
- [ ] AI-#5 Linux + WSL pipx smoke tests (S3 Day 4)
- [ ] AI-#9, AI-#10 P3 UX improvements (backlog)

## 🧹 AI-#6 CLEANUP COMPLETE (20/04)

44/44 uncommitted files addressed trong 3 PRs:
- **#118** — 7 strategy foundation docs (CRITICAL recovery)
- **#119** — 34 files Option B refactor (active/reference split)
- **#120** — 3 misc path refs

**Working tree CLEAN** · S2 proceeds without conflict risk.

## 📋 REMAINING ACTION ITEMS (S1 Retro §7)

- [ ] AI-#1 PyPI OIDC Trusted Publisher (S2 D5 during CBM-INT-207)
- [ ] AI-#2 `__version__` == pyproject test (low priority)
- [x] AI-#3 ✅ Live Claude Code skill trigger dry-run (done in E2E 20/04)
- [ ] AI-#4 PyPI release runbook doc (D2)
- [ ] AI-#5 Linux + WSL pipx smoke tests (D5)
- [x] AI-#8 ✅ AC-INT-06 "582+" → "158+" (done in retro v1.1)
- [ ] AI-#9 Config path resolution UX P3 (D3-4)
- [ ] AI-#10 `/cbm-diff` default branch auto-detect P3 (D3-4)

---

## ⚡ NEXT ACTIONS (Sun 19/04 — pre-flight)

**Pre-flight blockers — ALL CLOSED 19/04/2026 ✅:**
- [x] **B1** ✅ `SECURITY.md` (102 dòng) — GHSA private inbox, 48h ACK, scope rõ
- [x] **B2** ✅ Git audit CLEAN — gitleaks v8.30.1 · 168 commits · 0 findings · Report: `docs/active/cbm-claude-integration/CBM-INT-S1-B2-Git-Audit-Report.md`
- [x] **B3** ✅ `CONTRIBUTING.md` (165 dòng) — dev setup + lint gate + PR workflow
- [x] **B4** ✅ `.github/ISSUE_TEMPLATE/` (bug_report + feature_request + config.yml) + `.github/pull_request_template.md`
- [x] **+** GitHub Discussions ENABLED via `gh api`

**CEO actions:**
- [x] ✅ 3 PRs merged (#104 #105 #106) — pre-flight complete
- [x] ✅ CEO decision 19/04: **Skip Telegram — track sprint qua board.html SSOT** + PR history + timeline events

**Post-sprint (sau G1):**
- [ ] Launch day marketing: HN / Reddit / Viblo / Zalo communities
- [ ] Update `docs/HC-DEPLOYMENT-GUIDE.md` trong KMP repo với PyPI install path

---

## 📌 REFERENCES

- **Sprint briefing:** `docs/active/cbm-claude-integration/CBM-INT-S1-KICKOFF.md`
- **Technical Plan:** `docs/active/cbm-claude-integration/Technical_Plan_CBM_Claude_Integration.md` §1
- **Board SSOT:** `project/board.html#cbm-int-s1`
