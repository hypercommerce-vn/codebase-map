# BRIEF.md — Codebase Map Session Brief
> **Đọc file này ĐẦU TIÊN mỗi session. Cập nhật cuối mỗi session.**
> Version: 4.3 | Cập nhật: 19/04/2026 (CBM-INT-S1 · 2/5 SP DONE in 1 day — PRs #107 #108 merged, Day 3 starting)

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

## 🚀 CBM-INT-S1 · 2/5 SP DONE (40%) · Day 3 STARTING

**Sprint goal:** PyPI + Claude Skill + 3 slash commands (5 SP · 6 tasks) · Gate G1 Sun 26/04

**Progress (19/04 — 1 day in):**
- ✅ Day 0 Pre-flight B1-B4 CLOSED — PRs #104 #105 #106 merged
- ✅ Day 1 CBM-INT-101 PyPI v2.2.1 — PR #107 MERGED (⚠️ tag pending CEO)
- ✅ Day 2 CBM-INT-102 SKILL.md — PR #108 MERGED (parallel Day 1)
- 🔄 Day 3 CBM-INT-103/104/105 slash commands — starting now (2 SP)
- ⏳ Day 4 CBM-INT-106 integration test (Tester = Claude)
- ⏳ Day 5 QUICKSTART.md + v2.3.0 tag dry-run
- 🎯 Gate G1 Sun 26/04 17:00

**Execution pace:** 2 ngày sớm so với schedule gốc (Day 1+Day 2 parallel trong 1 session).

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
