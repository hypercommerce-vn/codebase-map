# Strategy Memo — Tích hợp Codebase Map vào Claude Ecosystem

> **From:** Claude (CEO Advisor)
> **To:** Đoàn Đình Tỉnh — CEO & Founder, Hyper Commerce
> **Date:** 16/04/2026
> **Status:** Draft for CEO review
> **Scope:** Distribution strategy đưa CBM v2.2 vào Claude Code + Claude Cowork

---

## 1. Executive Summary

CBM v2.2 đã production-ready và public OSS, nhưng hiện tại user Claude Code / Cowork **chưa có path chính thống** để install và dùng CBM trong workflow. Nếu không có lớp tích hợp này, CBM chỉ là một CLI tool bình thường, thất thế trước các competitor có MCP native (ví dụ `repomix`, `serena`, `code2prompt`).

**Khuyến nghị:** Triển khai **3-phase combo** trong 3 tuần (Apr 17 → May 8), ngân sách nội bộ, không cần fund.

| Phase | Tuần | Output | Value |
|-------|------|--------|-------|
| **Phase 1 — MVP** | Tuần 1 | PyPI + Skill + Slash commands | Dev Claude Code dùng được sau 2 phút setup |
| **Phase 2 — UX cao** | Tuần 2 | MCP server | Claude tự gọi tools không cần user gõ lệnh |
| **Phase 3 — Distribution** | Tuần 3 | Plugin Marketplace | One-click install qua `/plugin install cbm` |

**Business impact:** CBM trở thành "default codebase intelligence" cho cộng đồng Claude Code, tạo funnel dẫn về **KMP** (Knowledge AI Platform — private layer) — đây mới là monetize path dài hạn của Hyper Commerce.

---

## 2. Bối cảnh

### 2.1 CBM hiện tại (16/04/2026)

- v2.2.0 production-ready, 85 SP completed, 582 tests, MIT license
- Repo public: `github.com/hypercommerce-vn/codebase-map`
- Install hiện tại: `pipx install "git+https://github.com/hypercommerce-vn/codebase-map.git"` — chưa publish PyPI
- Chưa có lớp tích hợp native với Claude Code / Cowork
- Sister project KMP (private) cần CBM làm data layer

### 2.2 Claude ecosystem (Apr 2026)

Claude Code + Cowork hỗ trợ 4 cơ chế distribution:

| Cơ chế | Mức độ trưởng thành | Phù hợp với CBM |
|--------|:--------------------:|----------------|
| **PyPI / npm** | Stable, universal | ✅ Bước bắt buộc trước khi làm gì khác |
| **Skill files** (SKILL.md) | Stable — đã có skill-creator | ✅ Hướng dẫn Claude dùng CLI đúng |
| **Slash commands** | Stable — `/review-gate`, `/implement` đã chạy ổn | ✅ Shortcut cho workflow hay dùng |
| **MCP server** | Stable protocol, đã có registry | ✅ Tools xuất hiện trong context, UX cao nhất |
| **Plugin marketplace** | Research preview (Cowork) | ⚠️ Schema có thể thay đổi, nhưng là official channel |

### 2.3 Competitive landscape

| Tool | MCP | Plugin | PyPI | Đặc điểm |
|------|:---:|:------:|:----:|---------|
| **repomix** | ✅ | — | ✅ | Bundle codebase thành 1 file cho Claude, không có dependency graph |
| **serena** | ✅ | — | — | LSP-based symbol search, không có diff engine |
| **code2prompt** | — | — | ✅ | CLI bundle codebase, không có query engine |
| **CBM (ta)** | ❌ | ❌ | ❌ | Có đầy đủ graph + diff + api-catalog + dual-snapshot nhưng chưa distribute |

**Gap rõ ràng:** Ta có sản phẩm tốt hơn nhưng chưa lên kệ. Đây là ưu tiên số 1 để không mất mindshare.

---

## 3. Phân tích 4 integration path

### Path A — PyPI + Skill + Slash Commands (MVP)

**Cách làm:** Publish `codebase-map` lên PyPI; user `pipx install codebase-map`; add skill file + 3 slash command vào `~/.claude/`; skill dạy Claude dùng CLI đúng cú pháp.

| Tiêu chí | Đánh giá |
|---------|----------|
| Effort | ⭐ 3 ngày |
| UX cho user | ⭐⭐⭐ (user phải nhớ setup 2 bước) |
| Discoverability | ⭐⭐ (search PyPI + GitHub) |
| Risk | ⭐ Rất thấp |
| Maintenance | ⭐ Thấp |

**Ưu:** Ship nhanh, zero dependency vào plugin ecosystem đang là research preview. Claude Code user nào cũng dùng được ngay.

**Nhược:** User phải memorize command `codebase-map query ...`, không tự động. UX chưa "native Claude".

### Path B — MCP Server

**Cách làm:** Viết MCP server (Node hoặc Python) expose 5 tools — `cbm_query`, `cbm_impact`, `cbm_search`, `cbm_snapshot_diff`, `cbm_api_catalog`. User config vào `claude_desktop_config.json` hoặc Cowork MCP registry. Claude **tự gọi tools khi cần** — user không cần biết CBM tồn tại.

| Tiêu chí | Đánh giá |
|---------|----------|
| Effort | ⭐⭐⭐ 5 ngày |
| UX cho user | ⭐⭐⭐⭐⭐ Claude tự hoạt động |
| Discoverability | ⭐⭐⭐⭐ (MCP registry Anthropic) |
| Risk | ⭐⭐ Trung bình (graph.json load perf, tools shape cần design kỹ) |
| Maintenance | ⭐⭐⭐ Trung bình |

**Ưu:** UX cao cấp nhất. Dev hỏi "where is `CustomerService.create` called from?" → Claude tự gọi `cbm_impact` và trả lời. Không có learning curve cho user.

**Nhược:** Cần host process (stdio hoặc HTTP), thêm attack surface. Nếu graph.json > 10MB phải lazy load.

### Path C — Plugin Marketplace

**Cách làm:** Bundle skills + commands + MCP config + post-install hook thành 1 file `.plugin`, publish lên marketplace `hypercommerce-vn/claude-plugins`. User: `/plugin install cbm` là xong.

| Tiêu chí | Đánh giá |
|---------|----------|
| Effort | ⭐⭐ 3 ngày (sau khi đã có Path A + B) |
| UX cho user | ⭐⭐⭐⭐⭐ Một lệnh |
| Discoverability | ⭐⭐⭐⭐⭐ Marketplace + featured |
| Risk | ⭐⭐⭐ Cao (plugin schema research preview) |
| Maintenance | ⭐⭐ Thấp |

**Ưu:** Official Anthropic channel, distribution mạnh nhất, featured nếu chất lượng tốt.

**Nhược:** Plugin system Cowork đang research preview, schema có thể thay đổi. Phải maintain theo changelog Anthropic.

### Path D — All-in (Combo)

**Cách làm:** Làm tuần tự Path A → Path B → Path C. Mỗi path build trên nền path trước.

| Tiêu chí | Đánh giá |
|---------|----------|
| Effort | ⭐⭐⭐⭐ 11 ngày làm việc (3 tuần có buffer) |
| UX cho user | ⭐⭐⭐⭐⭐ |
| Discoverability | ⭐⭐⭐⭐⭐ (4 channel: PyPI, npm, MCP registry, Plugin marketplace) |
| Risk | ⭐⭐ (phase-gating giảm risk) |
| Maintenance | ⭐⭐⭐ |

**Ưu:** Coverage hoàn hảo mọi loại user (dev terminal, Cowork desktop, IDE plugin). Phase-gating cho phép ship incremental value ngay từ tuần 1.

**Nhược:** Nhiều artifact cần maintain (PyPI, npm, plugin repo, skill files). Cần quy trình version bump đồng bộ.

---

## 4. Khuyến nghị: Path D — All-in, triển khai theo 3 phase

### 4.1 Rationale

Anh chọn "Dev trước, Cowork sau" + "Tất cả 3 path" trong AskUserQuestion, đã rõ hướng. Phase-gating cho phép:

1. **Ship value tuần 1** — dev Claude Code dùng được CBM qua `pipx install` + skill file. Feedback vòng đầu ngay.
2. **Tuần 2** — MCP server nâng UX lên tầng "auto". Đây là vũ khí cạnh tranh với repomix/serena.
3. **Tuần 3** — Plugin marketplace đóng gói tất cả, mở rộng sang Cowork user (PM/PO/CEO).

### 4.2 Timeline chi tiết

```
Tuần 1 (17-23/04)      Tuần 2 (24-30/04)       Tuần 3 (01-07/05)
─────────────────      ─────────────────       ─────────────────
Phase 1 (5 SP)         Phase 2 (8 SP)          Phase 3 (5 SP)
PyPI + Skill           MCP server               Plugin bundle
                                                Cowork variant

D1: Publish PyPI       D1-2: MCP scaffold       D1: Plugin manifest
D2: SKILL.md           D3-4: 5 tools            D2: Bundle + hook
D3: 3 slash commands   D5: Integration test     D3: Submit marketplace
D4: Test + docs        D6-7: Package + NPM      D4: Cowork version
D5: v2.2.1 release     D8: Docs + release       D5: Launch blog post
```

**Total:** 18 SP trong 15 working days. Compatible với capacity team hiện tại (PM: anh, TechLead: 1, tester: 1).

### 4.3 Success metrics (30-90 ngày sau launch)

| Metric | Target 30d | Target 90d |
|--------|:----------:|:----------:|
| PyPI downloads / tháng | 200 | 1,500 |
| GitHub stars | 50 | 300 |
| Plugin installs | 100 | 500 |
| MCP tool invocations / tuần | 500 | 5,000 |
| PR mention CBM / tháng | 5 | 30 |
| KMP inbound inquiry (vì biết CBM) | 2 | 15 |

### 4.4 Risk register

| # | Risk | P | I | Mitigation |
|---|------|:-:|:-:|-----------|
| R1 | Plugin schema research preview thay đổi | 3 | 2 | Follow Cowork docs hàng tuần, giữ Path A + B độc lập với plugin |
| R2 | MCP server perf với graph.json > 10MB | 2 | 3 | Lazy load, streaming response, cache in memory với TTL |
| R3 | Adoption chậm — dev không biết CBM | 3 | 3 | Sample repo + video demo 2 phút + blog post launch week |
| R4 | PyPI name `codebase-map` đã bị chiếm | 1 | 2 | Check ngay ngày D1. Fallback: `codebase-map-hc` hoặc `cbm-graph` |
| R5 | Breaking change Anthropic MCP protocol | 2 | 3 | Version server bump theo SDK, semver strict |
| R6 | User confuse CBM vs KMP | 2 | 2 | README + landing page có 1 sơ đồ rõ ranh giới |

---

## 5. Resource & Budget

### 5.1 Nhân lực

| Role | Load | Ngày | Ghi chú |
|------|------|------|--------|
| CEO (anh) | 10% | 3 ngày | Review + approve mỗi phase gate |
| CTO | 30% | 5 ngày | Design MCP tools, review PR |
| TechLead | 100% | 15 ngày | Implementation chính |
| Tester | 20% | 3 ngày | Integration test + regression |
| Marketing (anh kiêm) | 10% | 2 ngày | Launch blog + social |

### 5.2 Chi phí

| Hạng mục | Chi phí | Ghi chú |
|----------|:-------:|--------|
| PyPI hosting | $0 | Free for OSS |
| npm hosting | $0 | Free |
| GitHub Actions | $0 | Public repo unlimited |
| MCP registry | $0 | Free |
| Plugin marketplace | $0 | Free publish |
| Launch assets (video, blog) | ~$100 | Canva Pro + Loom |
| **Total** | **~$100** | |

### 5.3 Opportunity cost

15 ngày TechLead. So với giá trị: CBM trở thành top-of-mind cho cộng đồng Claude dev → KMP có lead funnel dài hạn. ROI tích cực nếu đạt 50%+ target metric 90d.

---

## 6. Quyết định cần anh approve

| # | Quyết định | Khuyến nghị | Anh approve |
|---|-----------|------------|:-----------:|
| D1 | Chọn Path D (all-in 3-phase) | ✅ Yes | ☐ |
| D2 | Start Phase 1 ngày 17/04 | ✅ Yes | ☐ |
| D3 | TechLead full-time cho sprint này | ✅ Yes | ☐ |
| D4 | PyPI name: `codebase-map` (fallback `cbm-graph`) | ✅ Yes | ☐ |
| D5 | MCP server viết bằng Python (reuse codebase_map package, không repo riêng) | ✅ Yes (Python, share repo) | ☐ |
| D6 | Plugin repo tách riêng: `hypercommerce-vn/claude-plugins` | ✅ Yes | ☐ |
| D7 | Launch blog post trên dev.to + Medium, crosspost HC blog | ✅ Yes | ☐ |

---

## 7. Next actions (nếu CEO approve)

1. **Hôm nay (16/04):** Anh approve memo này + Technical Plan đi kèm.
2. **Ngày mai (17/04):** TechLead kick-off sprint, tạo branch `feat/cbm-claude-integration`.
3. **Cuối tuần 1 (23/04):** Review gate Phase 1, anh approve → merge + release v2.2.1.
4. **Cuối tuần 2 (30/04):** Review gate Phase 2, MCP server lên npm.
5. **Cuối tuần 3 (07/05):** Plugin marketplace live, launch blog post, update BRIEF.md + board.

---

## 8. Kết luận

CBM có sản phẩm mạnh hơn đối thủ (dual-snapshot, API catalog, coverage overlay) nhưng **đang mất cơ hội distribution** vì chưa native Claude. Làm 3-phase combo trong 3 tuần, chi phí $100 + 15 ngày TechLead, đổi lấy vị thế đầu tàu trong segment "codebase intelligence cho Claude dev". Đây là vòng đầu tư đáng giá nhất trong Q2/2026 cho Hyper Commerce.

Khuyến nghị anh approve ngay để Phase 1 bắt đầu sáng mai.

---

*Strategy Memo v1.0 · Created 16/04/2026 · For CEO review*
*Paired with: `Technical_Plan_CBM_Claude_Integration.md`*
