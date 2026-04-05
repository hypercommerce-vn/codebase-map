# FDD-TOOL-CODEMAP — Codebase Map: Function Dependency Graph

> **CEO-approved 05/04/2026. Design v2.0 approved: `design-preview/codebase-map-v2-design.html`**
> Standalone module — gắn vào bất kỳ Python project nào.

---

## 1. Feature Overview

| Field | Value |
|-------|-------|
| **Feature ID** | FDD-TOOL-CODEMAP |
| **Module** | Tools (standalone) |
| **Sprints** | CM-S1 (v1.1) → CM-S2 (v1.2) → CM-S3 (v2.0) |
| **Total SP** | 55 SP (15 + 18 + 22) |
| **Priority** | High — CEO strategic decision |
| **Status** | v1.0 Done (PR #82) · v1.1-v2.0 Planning |
| **Design Ref** | `design-preview/codebase-map-v2-design.html` |
| **Assigned** | CTO (parser/graph) · Designer (HTML/UX) · DevOps (CI) |
| **BA Owner** | PO Agent |

**Goal:** Bản đồ tư duy neural network cho toàn bộ functions của dự án — giúp dev hiểu impact trước khi code, QA cover side effects, team mới onboard nhanh.

---

## 2. User Stories

- **US-1:** As a Developer, I want to query function dependencies before coding so that I understand where new code fits and what it affects.
- **US-2:** As a QA/Tester, I want to see impact zone of a changed function so that I can cover all side effects in testing.
- **US-3:** As a CTO, I want to see architecture overview with domain clustering so that I can review structural health at a glance.
- **US-4:** As a CEO/PO, I want an Executive view showing only modules and routes so that I understand the system without technical noise.
- **US-5:** As a TechLead, I want PR diff mode showing changed + impacted nodes so that code review is focused and thorough.
- **US-6:** As a PM, I want auto-generated API catalog from routes so that API documentation stays always up-to-date.
- **US-7:** As a DevOps, I want CI auto-generate the map on each PR so that it is always current without manual effort.

---

## 3. Version Breakdown & Acceptance Criteria

### ═══ v1.0 — Core Foundation ✅ DONE (PR #82)

| # | Feature | Status |
|---|---------|--------|
| v1.0-01 | Python AST Parser (functions, classes, methods, routes, Celery tasks) | ✅ Done |
| v1.0-02 | Graph models (Node, Edge, Graph dataclasses) | ✅ Done |
| v1.0-03 | Graph Builder (orchestrate parsers → build graph) | ✅ Done |
| v1.0-04 | JSON Exporter (structured, Claude-queryable) | ✅ Done |
| v1.0-05 | HTML Exporter (D3.js interactive force graph) | ✅ Done |
| v1.0-06 | CLI: generate, query, impact, search, summary | ✅ Done |
| v1.0-07 | YAML config (standalone, any project) | ✅ Done |
| **Result** | **1,386 nodes · 8,285 edges · 7 domains** | ✅ |

---

### ═══ CM-S1: v1.1 — UX Polish + DevOps Integration (15 SP)

| Task ID | Feature | SP | Owner | Design Ref (element in HTML) | AC |
|---------|---------|----|----|------|-----|
| CM-S1-01 | **Progressive disclosure** — collapse methods, show domain → class tree | 3 | Designer | Sidebar `.domain-tree`, `.class-methods` | Sidebar mặc định hiện domain → class. Click class expand methods. Giảm visible nodes từ 1386 → ~350 |
| CM-S1-02 | **Domain clustering** — D3 forceCluster, background color per domain | 3 | CTO | SVG `.clusters`, `.cluster-bg`, `.cluster-label` | Mỗi domain có vùng riêng trên graph. Label domain hiện rõ. Nodes cùng domain nằm gần nhau |
| CM-S1-03 | **Fix "unknown" layer** — classify 444 nodes (schemas, utils, init) | 1 | CTO | Sidebar filter chips `.chip` counts cập nhật | Nodes layer "unknown" giảm xuống < 50 (< 5%) |
| CM-S1-04 | **Bundle D3.js** — remove CDN, inline vào HTML | 1 | DevOps | HTML `<script>` section | HTML mở được offline, không cần internet |
| CM-S1-05 | **.gitignore output + CI auto-generate** | 1 | DevOps | Topbar `.topbar-meta` timestamp | `docs/function-map/` trong .gitignore. CI job generate on PR |
| CM-S1-06 | **Minimap** — canvas mini ở góc dưới phải | 2 | Designer | `#minimap` element | Minimap hiện toàn cảnh graph + viewport indicator (rect viền xanh) |
| CM-S1-07 | **Toolbar** — zoom, fit, toggle labels/edges/clusters | 1 | Designer | `#toolbar` buttons | 8 buttons hoạt động: zoom in/out, fit, labels, edges, clusters, export, fullscreen |
| CM-S1-08 | **Dual legend** — node type (fill) + edge type (line style) | 1 | Designer | `#legend` with 2 groups | Legend phân 2 nhóm rõ: Type (dot colors) + Edge (line styles) |
| CM-S1-09 | **Accessibility fix** — font min 11px, empty state | 1 | Designer | `.node-text` font + `.empty-state` | Không có font < 11px. Search không kết quả → hiện empty state |
| CM-S1-10 | **Top bar** — logo, stats badges, timestamp | 1 | Designer | `#topbar` full element | Top bar hiện logo "CM v1.1", stats (nodes/edges/domains), generated timestamp |

**Sprint AC tổng:**
- [ ] CM-AC-01: HTML mở offline, không cần CDN
- [ ] CM-AC-02: Sidebar tree collapse/expand hoạt động
- [ ] CM-AC-03: Domain clustering visible trên graph
- [ ] CM-AC-04: CI job generate map chạy thành công trên GitHub Actions
- [ ] CM-AC-05: "unknown" layer < 5% total nodes

---

### ═══ CM-S2: v1.2 — Workflow Integration + Smart Features (18 SP)

| Task ID | Feature | SP | Owner | Design Ref | AC |
|---------|---------|----|----|------|-----|
| CM-S2-01 | **Git diff integration** — `codebase-map diff HEAD~1` | 3 | CTO | `#diff-overlay`, `.diff-badge` | CLI chạy `diff` trả danh sách changed + impacted nodes. JSON output |
| CM-S2-02 | **Incremental update** — cache AST hash, chỉ re-parse changed files | 3 | CTO | (performance, no visual) | Generate time giảm > 50% khi chỉ 1-2 files thay đổi |
| CM-S2-03 | **Test coverage overlay** — map test → source, highlight untested | 2 | CTO | Detail panel `.coverage-bar`, `.coverage-fill` | Detail panel hiện coverage % per function. Bar xanh/vàng/đỏ theo threshold |
| CM-S2-04 | **Tích hợp `/implement`** — Step 2 auto-query impact | 1 | PM | (workflow, no visual) | `/implement` step 2 tự chạy query trước khi dev bắt đầu code |
| CM-S2-05 | **Tích hợp `/review-gate`** — impact graph trong review | 1 | PM | (workflow, no visual) | Review gate hiện impact zone trong report |
| CM-S2-06 | **Edge resolution cải thiện** — resolve self.repo chain từ __init__ | 2 | CTO | (parser accuracy) | `self.repo.list()` resolve chính xác đến `CustomerRepository.list` |
| CM-S2-07 | **API Catalog auto-gen** — extract routes → method, path, params | 2 | CTO+PO | View tab "API Catalog", `.api-catalog`, `.api-endpoint` | Tab "API Catalog" hiện tất cả routes grouped by domain. HTTP method badge + path + auth |
| CM-S2-08 | **FDD Spec linking** — node metadata → FDD ID | 1 | PM | Detail panel `.detail-grid` row "FDD" | Detail panel hiện FDD link nếu có. Click mở spec file |
| CM-S2-09 | **PR impact comment bot** — CI comment impact vào PR | 1 | DevOps | (CI automation) | PR mới → CI comment: "This PR affects X functions, impact zone: Y nodes" |
| CM-S2-10 | **Sprint metric: impact per PR** — track + alert > 50 nodes | 1 | PM | (process) | PR impact > 50 nodes → auto-assign CTO review label |
| CM-S2-11 | **Staleness alert** — graph > 7 days → Telegram notify | 1 | DevOps | Topbar timestamp color change | Timestamp chuyển đỏ nếu > 7 ngày. Telegram alert gửi team |

**Sprint AC tổng:**
- [ ] CM-AC-06: `codebase-map diff HEAD~1` trả output đúng
- [ ] CM-AC-07: Coverage bar hiện trong detail panel
- [ ] CM-AC-08: API Catalog tab hiện tất cả 187 routes đúng
- [ ] CM-AC-09: PR comment bot hoạt động trên GitHub Actions
- [ ] CM-AC-10: `/implement` + `/review-gate` tích hợp hoạt động

---

### ═══ CM-S3: v2.0 — Multi-View + AI Integration (22 SP)

| Task ID | Feature | SP | Owner | Design Ref | AC |
|---------|---------|----|----|------|-----|
| CM-S3-01 | **Multi-view mode** — Executive / Architecture / Developer tabs | 3 | Designer+PO | Topbar `.view-tabs` (Graph/Executive/API/PR Diff) | 4 tabs chuyển đổi smooth. Mỗi view hiện đúng level of detail |
| CM-S3-02 | **Executive view** — chỉ modules + routes + business flows | 3 | PO+Designer | View tab "Executive" | CEO/PO thấy: domain boxes + route counts + flow connections. Không thấy methods/internal |
| CM-S3-03 | **PR Diff view** — changed/impacted nodes highlighted trên graph | 3 | CTO+Designer | View tab "PR Diff", `#diff-overlay` | Nodes xanh (added), vàng (modified), đỏ (removed). Impact zone viền cam |
| CM-S3-04 | **Business Flow Mapping** — tag functions → user journeys | 3 | PO | (new feature in Executive view) | PO tag groups: "Onboarding Flow", "Checkout Flow". Hiện flow path trên graph |
| CM-S3-05 | **Breadcrumb navigation** — zoom domain → sub-module drill-down | 2 | Designer | Topbar `.breadcrumb` | Click domain → zoom + filter. Breadcrumb hiện: All > CRM > Customers |
| CM-S3-06 | **TypeScript parser** — parse React components + hooks | 5 | CTO | (parser extension) | Frontend components, hooks, API calls parsed. Thêm ~500 nodes |
| CM-S3-07 | **Detail panel v2** — visual hierarchy, coverage, FDD, impact | 2 | Designer | `#detail-panel` full redesign | Sections rõ ràng: Info → Dependencies → Dependents → Impact Zone → Coverage |
| CM-S3-08 | **Responsive sidebar** — collapsible, mobile-friendly | 1 | Designer | CSS `@media` rules | Sidebar collapse trên < 768px. Toggle button hiện/ẩn |

**Sprint AC tổng:**
- [ ] CM-AC-11: 4 view tabs hoạt động: Graph / Executive / API Catalog / PR Diff
- [ ] CM-AC-12: Executive view hiện modules + routes, ẩn methods
- [ ] CM-AC-13: TypeScript parser thêm frontend nodes vào graph
- [ ] CM-AC-14: Breadcrumb navigation drill-down hoạt động
- [ ] CM-AC-15: Detail panel hiện coverage + FDD link + impact zone

---

## 4. Design ↔ Sprint Mapping

### Visual Map: Design Element → Task → Sprint

```
┌─────────────────────────────────────────────────────────────────────┐
│  DESIGN: design-preview/codebase-map-v2-design.html                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─── TOP BAR ───────────────────────────────────────────────┐     │
│  │ Logo+Stats ─── CM-S1-10 (v1.1)                            │     │
│  │ View Tabs ──── CM-S3-01 (v2.0)                            │     │
│  │ Breadcrumb ─── CM-S3-05 (v2.0)                            │     │
│  │ Timestamp ──── CM-S1-10 (v1.1) + CM-S2-11 staleness(v1.2)│     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌─── SIDEBAR ──┐  ┌─── GRAPH CANVAS ─────────────────────┐       │
│  │Search         │  │                                       │       │
│  │ CM-S1-09 (1.1)│  │  Domain Clusters ── CM-S1-02 (v1.1) │       │
│  │               │  │  Node Highlight ──── v1.0 ✅          │       │
│  │Layer Filters  │  │  Edge Types ──────── v1.0 ✅          │       │
│  │ CM-S1-01 (1.1)│  │  Dimmed Nodes ────── CM-S1-02 (v1.1) │       │
│  │               │  │  PR Diff Overlay ─── CM-S3-03 (v2.0) │       │
│  │Type Filters   │  │                                       │       │
│  │ CM-S1-01 (1.1)│  │                                       │       │
│  │               │  │  ┌── DETAIL PANEL ──────────┐        │       │
│  │Domain Tree    │  │  │ Type Badge ── CM-S3-07    │        │       │
│  │ CM-S1-01 (1.1)│  │  │ Info Grid ── CM-S1-10     │        │       │
│  │  └ Classes    │  │  │ Coverage ─── CM-S2-03     │        │       │
│  │    └ Methods  │  │  │ FDD Link ─── CM-S2-08     │        │       │
│  │               │  │  │ Dependencies ── v1.0 ✅   │        │       │
│  │Empty State    │  │  │ Dependents ──── v1.0 ✅   │        │       │
│  │ CM-S1-09 (1.1)│  │  │ Impact Zone ── CM-S2-01  │        │       │
│  │               │  │  └──────────────────────────┘        │       │
│  │Responsive     │  │                                       │       │
│  │ CM-S3-08 (2.0)│  │  ┌── MINIMAP ──┐  ┌── TOOLBAR ──┐  │       │
│  │               │  │  │ CM-S1-06     │  │ CM-S1-07    │  │       │
│  └───────────────┘  │  └─────────────┘  └─────────────┘  │       │
│                      │                                       │       │
│                      │  ┌── LEGEND ──────────────────────┐  │       │
│                      │  │ Dual: CM-S1-08 (v1.1)          │  │       │
│                      │  └────────────────────────────────┘  │       │
│                      └───────────────────────────────────────┘       │
│                                                                     │
│  ┌─── VIEWS (v2.0) ────────────────────────────────────────────┐   │
│  │ Executive View ──── CM-S3-02 + CM-S3-04 (Business Flows)    │   │
│  │ API Catalog ──────── CM-S2-07 (v1.2)                         │   │
│  │ PR Diff View ─────── CM-S2-01 (v1.2) + CM-S3-03 (v2.0)     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─── BACKEND / CI (không có visual) ──────────────────────────┐   │
│  │ Fix unknown layer ── CM-S1-03 (v1.1)                         │   │
│  │ Bundle D3 ──────── CM-S1-04 (v1.1)                           │   │
│  │ CI auto-generate ── CM-S1-05 (v1.1)                          │   │
│  │ Incremental update ─ CM-S2-02 (v1.2)                         │   │
│  │ Edge resolution ──── CM-S2-06 (v1.2)                         │   │
│  │ Implement integration CM-S2-04 (v1.2)                        │   │
│  │ Review-gate integ ── CM-S2-05 (v1.2)                         │   │
│  │ PR comment bot ───── CM-S2-09 (v1.2)                         │   │
│  │ Impact metric ────── CM-S2-10 (v1.2)                         │   │
│  │ Staleness alert ──── CM-S2-11 (v1.2)                         │   │
│  │ TypeScript parser ── CM-S3-06 (v2.0)                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Sprint Timeline

```
         CM-S1 (v1.1)        CM-S2 (v1.2)        CM-S3 (v2.0)
         15 SP                18 SP                22 SP
         ───────────          ───────────          ───────────
Focus:   UX + DevOps          Workflow + Smart     Multi-View + AI
Tasks:   10 tasks             11 tasks             8 tasks
Output:  Usable visual tool   Dev workflow tool    Full platform tool

Deps:    v1.0 ✅ ──→ CM-S1 ──→ CM-S2 ──→ CM-S3
                      │         │         │
                      │         │         └─ Needs: CM-S2-01 (diff)
                      │         │                   CM-S2-07 (API)
                      │         │
                      │         └─ Needs: CM-S1-02 (clusters)
                      │                   CM-S1-05 (CI)
                      │
                      └─ Needs: v1.0 parser + graph
```

---

## 6. Files to Create / Modify

### CM-S1 (v1.1)
```
tools/codebase-map/
├── codebase_map/
│   ├── parsers/python_parser.py          (MODIFY — fix unknown layer)
│   ├── graph/builder.py                  (MODIFY — add clustering)
│   ├── exporters/html_exporter.py        (REWRITE — new design v1.1)
│   └── exporters/d3.v7.min.js            (CREATE — bundled D3)
├── templates/
│   └── visualization_v1.1.html           (CREATE — new template)
.github/workflows/codebase-map.yml        (CREATE — CI job)
.gitignore                                 (MODIFY — add function-map/)
```

### CM-S2 (v1.2)
```
tools/codebase-map/
├── codebase_map/
│   ├── graph/query.py                    (MODIFY — diff, coverage)
│   ├── graph/diff.py                     (CREATE — git diff integration)
│   ├── graph/coverage.py                 (CREATE — pytest-cov overlay)
│   ├── parsers/python_parser.py          (MODIFY — edge resolution)
│   ├── exporters/html_exporter.py        (MODIFY — API catalog tab)
│   └── cli.py                            (MODIFY — add diff command)
.claude/commands/implement.md              (MODIFY — add Step 2 query)
.claude/commands/review-gate.md            (MODIFY — add impact report)
.github/workflows/codebase-map.yml        (MODIFY — PR comment bot)
```

### CM-S3 (v2.0)
```
tools/codebase-map/
├── codebase_map/
│   ├── parsers/typescript_parser.py      (CREATE — TS/TSX parser)
│   ├── exporters/html_exporter.py        (REWRITE — multi-view)
│   ├── graph/flows.py                    (CREATE — business flow tags)
│   └── cli.py                            (MODIFY — flow commands)
├── templates/
│   └── visualization_v2.0.html           (CREATE — final template)
```

---

## 7. Definition of Done (DoD) — Per Sprint

### DoD CM-S1 (v1.1)
- [ ] HTML mở offline, D3.js bundled
- [ ] Domain clustering visible trên graph
- [ ] Sidebar tree collapse/expand hoạt động (domain → class → method)
- [ ] Minimap + Toolbar + Dual Legend hoạt động
- [ ] "unknown" layer < 5% total nodes
- [ ] CI job generate map trên GitHub Actions pass
- [ ] Font minimum 11px, empty state hiện khi search không kết quả
- [ ] `black --check && isort --check && flake8` pass
- [ ] PR tạo: `[FDD-TOOL-CODEMAP] feat: codebase-map v1.1`

### DoD CM-S2 (v1.2)
- [ ] `codebase-map diff HEAD~1` output đúng changed + impacted
- [ ] Incremental update: generate time giảm > 50% khi 1-2 files change
- [ ] Coverage bar hiện trong detail panel (xanh/vàng/đỏ)
- [ ] API Catalog tab hiện 187 routes grouped by domain
- [ ] `/implement` step 2 tự query impact
- [ ] `/review-gate` hiện impact zone trong report
- [ ] PR comment bot hoạt động
- [ ] PR tạo: `[FDD-TOOL-CODEMAP] feat: codebase-map v1.2`

### DoD CM-S3 (v2.0)
- [ ] 4 view tabs hoạt động: Graph / Executive / API Catalog / PR Diff
- [ ] Executive view hiện modules + routes only
- [ ] PR Diff view highlight changed (xanh/vàng/đỏ) + impact zone (cam)
- [ ] TypeScript parser parse frontend → thêm ~500 nodes
- [ ] Breadcrumb navigation drill-down hoạt động
- [ ] Business Flow tags hiện trên Executive view
- [ ] Responsive: sidebar collapse < 768px
- [ ] **100% match design**: `design-preview/codebase-map-v2-design.html`
- [ ] PR tạo: `[FDD-TOOL-CODEMAP] feat: codebase-map v2.0`

---

## 8. Risk Register

| ID | Risk | P | I | Score | Mitigation |
|----|------|---|---|-------|------------|
| R1 | D3.js bundled tăng HTML file size > 5MB | 2 | 1 | 2 | Minify D3, lazy load |
| R2 | TypeScript parser phức tạp hơn Python | 3 | 2 | 6 | Start với basic TS, iterate |
| R3 | Graph performance chậm > 2000 nodes | 2 | 3 | 6 | WebGL renderer fallback, viewport culling |
| R4 | Coverage overlay cần pytest-cov format cụ thể | 2 | 2 | 4 | Parse standard .coverage JSON |
| R5 | Business Flow tagging cần PO manual work | 2 | 2 | 4 | Start với convention-based auto-detect |

---

*FDD-TOOL-CODEMAP spec v1.0 | Created: 05/04/2026 by PM Agent | Approved: CEO 05/04/2026*
*Design ref: `design-preview/codebase-map-v2-design.html`*
