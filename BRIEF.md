# BRIEF.md — Codebase Map Session Brief
> **Đọc file này ĐẦU TIÊN mỗi session. Cập nhật cuối mỗi session.**
> Version: 4.0 | Cập nhật: 16/04/2026 (Repo split — CBM standalone public OSS)

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

## ⚡ NEXT ACTIONS

- [ ] Make repo public (unlimited free CI)
- [ ] Update `docs/HC-DEPLOYMENT-GUIDE.md` in KMP repo với PyPI install path
- [ ] Publish to PyPI (future): `pipx install codebase-map`
- [ ] Community release notes
