# CLAUDE.md — Codebase Map
> **Orchestrator file. Đọc file này đầu tiên mỗi session.**
> Version: 1.0 | Created: 05/04/2026 | Migrated from HC repo

---

## 🧑‍💼 PRODUCT OWNER

- **Tên:** Đoàn Đình Tỉnh — CEO & Founder, Hyper Commerce
- **Email:** hypercdp@gmail.com
- **Cách làm việc:** Trả lời tiếng Việt, ưu tiên business impact, output là file hoàn chỉnh

---

## ⛔ CRITICAL RULES

1. **KHÔNG push thẳng lên `main`** — mọi thay đổi phải qua PR
2. **Comment AI code:** `# HC-AI | ticket: FDD-TOOL-CODEMAP` trên mọi block AI-generated
3. **Lint gate trước mỗi commit:** `black --check . && isort --check . && flake8`
4. **Conventional Commits:** `feat(parser):`, `fix(exporter):`, `chore(ci):`
5. **No Design = No Implementation** — FE component phải có design approved trước
6. **PR Per Day Mandatory** — mỗi Day implement → 1 PR → review-gate → CEO approve
7. **Review Gate 3 tầng:** Tester → CTO → Designer (trước CEO)

---

## 📋 PROJECT OVERVIEW

**Codebase Map** — Standalone function dependency graph generator.
Gắn vào bất kỳ Python/TypeScript project nào qua YAML config.

| Field | Value |
|-------|-------|
| **Repo** | https://github.com/hypercommerce-vn/codebase-map |
| **Parent project** | Hyper Commerce (HC) — nhưng repo độc lập |
| **HC config** | `codebase-map.yaml` trong HC repo root |
| **Tech** | Python 3.10+ · AST · D3.js (bundled) · PyYAML |
| **Install** | `pip install git+https://github.com/hypercommerce-vn/codebase-map.git` |

---

## 📁 REPO STRUCTURE

```
codebase-map/
├── CLAUDE.md                          ← file này
├── BRIEF.md                           ← trạng thái hiện tại (cập nhật mỗi session)
├── .claude/
│   ├── settings.json                  ← security deny/allow rules
│   ├── commands/
│   │   ├── review-gate.md             ← /review-gate — 3 tầng review
│   │   ├── implement.md               ← /implement — 7 bước implement
│   │   ├── review.md                  ← /review — 5D code review
│   │   ├── ci-watch.md                ← /ci-watch — CI auto-fix
│   │   └── security-audit.md          ← /security-audit — 3 tầng security
│   └── specs/
│       └── FDD-TOOL-CODEMAP/          ← spec per ticket
├── agents/
│   ├── README.md                      ← 7 AI agents overview
│   ├── cto/SKILL.md                   ← CTO: code quality, architecture
│   ├── techlead/SKILL.md              ← TechLead: implementation, review
│   ├── project-manager/SKILL.md       ← PM: sprint tracking, risk
│   ├── product-owner/SKILL.md         ← PO: backlog, scope, sign-off
│   ├── business-analyst/SKILL.md      ← BA: spec, business rules
│   ├── designer/SKILL.md              ← Designer: D3.js/HTML review
│   └── tester/SKILL.md               ← Tester: functional, regression
├── codebase_map/
│   ├── __init__.py                    ← version
│   ├── __main__.py                    ← python -m entry
│   ├── cli.py                         ← CLI: generate, query, impact, search, summary
│   ├── config.py                      ← YAML config loader
│   ├── parsers/
│   │   ├── base.py                    ← abstract BaseParser
│   │   └── python_parser.py           ← Python AST parser
│   ├── graph/
│   │   ├── models.py                  ← Node, Edge, Graph, LayerType, NodeType
│   │   ├── builder.py                 ← GraphBuilder orchestrator
│   │   └── query.py                   ← QueryEngine (search, impact, summary)
│   └── exporters/
│       ├── json_exporter.py           ← JSON output
│       ├── html_exporter.py           ← Interactive HTML (D3.js)
│       └── d3.v7.min.js              ← Bundled D3 (offline)
├── design-preview/
│   ├── codebase-map-v2-design.html    ← Design tổng thể v2.0 (CEO approved)
│   └── codebase-map-CM-S1-design.html ← Design chi tiết CM-S1 (CEO approved)
├── specs/
│   └── spec.md                        ← FDD spec đầy đủ (3 sprints, 29 tasks)
├── project/
│   └── CM-S1-TASK-BOARD.md            ← Task board sprint 1
├── .github/workflows/ci.yml           ← CI: lint + self-test
├── pyproject.toml                     ← pip installable
├── setup.cfg                          ← flake8 config
├── codebase-map.example.yaml          ← sample config
├── templates/                         ← HTML templates (future)
└── tests/                             ← unit tests (future)
```

---

## 📚 DOCS MAP

| Khi cần... | Đọc file |
|------------|---------|
| Trạng thái hiện tại | **`BRIEF.md`** |
| FDD spec + sprint breakdown | **`specs/spec.md`** |
| Task board CM-S1 | **`project/CM-S1-TASK-BOARD.md`** |
| Design v2.0 tổng thể | **`design-preview/codebase-map-v2-design.html`** |
| Design CM-S1 chi tiết | **`design-preview/codebase-map-CM-S1-design.html`** |
| AI Agents overview | **`agents/README.md`** |
| Slash commands | **`.claude/commands/`** |

---

## 🤖 AI AGENTS & SLASH COMMANDS

### 7 AI Agents (đọc `agents/README.md` để overview)

| Agent | File | Khi nào dùng |
|-------|------|-------------|
| CTO | `agents/cto/SKILL.md` | Architecture review, quality gate |
| Tech Lead | `agents/techlead/SKILL.md` | Implement, code review |
| PM | `agents/project-manager/SKILL.md` | Sprint tracking, risk |
| PO | `agents/product-owner/SKILL.md` | Scope, user stories, sign-off |
| BA | `agents/business-analyst/SKILL.md` | Spec, business rules, flows |
| Designer | `agents/designer/SKILL.md` | HTML/D3.js design review |
| Tester | `agents/tester/SKILL.md` | Functional test, regression |

### 5 Slash Commands (trong `.claude/commands/`)

| Command | Khi nào dùng |
|---------|-------------|
| `/review-gate` | **BẮT BUỘC** trước CEO review — 3 tầng |
| `/implement` | Bắt đầu implement feature — 7 bước |
| `/review` | Code review nhanh — 5D × 20đ |
| `/ci-watch` | CI fail — auto-fix + re-push |
| `/security-audit` | Security scan — 3 tầng |

---

## 🔁 SESSION START PROTOCOL

```
Bước 1: Đọc CLAUDE.md (file này)
Bước 2: Đọc BRIEF.md (trạng thái hiện tại)
Bước 3: Đọc specs/spec.md nếu implement
Bước 4: Đọc design-preview/ nếu FE work
Bước 5: Bắt đầu làm
Bước cuối: Cập nhật BRIEF.md
```

---

## 🔁 SESSION END PROTOCOL

Cập nhật `BRIEF.md`:
- Trạng thái sprint/tasks
- Quyết định quan trọng
- Vấn đề đang mở
- Next actions

---

## ⚡ ROADMAP

| Version | Sprint | Focus | SP | Status |
|---------|--------|-------|----|--------|
| **v1.0** | — | Core: parser + graph + CLI + HTML | 8 | ✅ Done |
| **v1.1** | CM-S1 | UX: sidebar tree, clusters, minimap, toolbar, D3 bundle | 15 | ✅ Done (06/04/2026) |
| **v1.2** | CM-S2 | Workflow: git diff, coverage, API catalog, /implement | 18 | ⏳ Planned |
| **v2.0** | CM-S3 | Multi-view: Executive, PR Diff, TS parser, responsive | 22 | ⏳ Planned |

---

## 🔧 DEVELOPMENT

```bash
# Setup
git clone https://github.com/hypercommerce-vn/codebase-map.git
cd codebase-map
pip install -e ".[dev]"

# Generate on HC project
codebase-map generate -c /path/to/HyperCommerce/codebase-map.yaml

# CLI commands
codebase-map query "create_customer" -f graph.json
codebase-map impact "CustomerService" -f graph.json
codebase-map search "pipeline" -f graph.json
codebase-map summary -f graph.json

# Lint before commit
black --check codebase_map/ && isort --check codebase_map/ && flake8 codebase_map/
```

---

*CLAUDE.md v1.1 — Codebase Map | Updated 06/04/2026 | Added agents + commands + settings*
