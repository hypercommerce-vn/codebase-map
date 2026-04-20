# Giải thích chi tiết — Phase 2: MCP Server (UX cao)

> **Câu hỏi CEO:** Tại sao Phase 2 là "UX cao" — "Claude tự gọi tools không cần user gõ lệnh"? Cụ thể nó khác gì Phase 1?
>
> **Trả lời ngắn:** Phase 1 bắt user **gõ lệnh đúng tên** (`/cbm-impact function_x`). Phase 2 cho user **hỏi bằng tiếng tự nhiên** ("Nếu đổi function X thì ảnh hưởng ai?") — Claude tự hiểu ý và gọi tool CBM phù hợp, user không cần biết tool tồn tại.
>
> **Prepared for:** Đoàn Đình Tỉnh — CEO, Hyper Commerce
> **Date:** 2026-04-16

---

## 1. MCP là gì — giải thích cho CEO trong 1 phút

**MCP = Model Context Protocol.**

Đây là giao thức chuẩn do Anthropic công bố 11/2024, cho phép **Claude giao tiếp trực tiếp với công cụ bên ngoài** (database, API, file system, CBM, Slack, Gmail...) mà không cần user copy-paste dữ liệu qua lại.

### Analogy dễ hiểu:

| MCP giống như... | Giải thích |
|---|---|
| **USB cho AI** | Cắm tool nào vào, Claude xài tool đó ngay, không cần code lại |
| **Phụ tá riêng của Claude** | Claude quyết định khi nào gọi, gọi cái gì, gọi như thế nào |
| **Menu nhà hàng** | User order bằng tiếng bình thường, bếp (tool) biết phải nấu gì |

### Khác biệt với cách Claude hiện tại làm việc:

**Hôm nay (không có MCP):**
```
User → copy code vào chat → Claude đọc → trả lời
User → paste output error → Claude phân tích → trả lời
User → gõ slash command → Claude chạy command fixed → trả lời
```

**Với MCP (Phase 2):**
```
User → hỏi tự nhiên → Claude gọi tool MCP → nhận data → trả lời
(Claude tự quyết gọi tool nào, không cần user biết tool tồn tại)
```

---

## 2. Phase 1 vs Phase 2 — Khác biệt cốt lõi

### 2.1. Bảng so sánh

| Tiêu chí | Phase 1 — Slash Command | **Phase 2 — MCP Auto-invoke** |
|---|---|---|
| User cần làm gì | Gõ đúng `/cbm-impact`, `/cbm-diff`... | Hỏi bằng tiếng bình thường |
| User cần nhớ lệnh không? | **Có** — phải biết tên 3 command | **Không** — hỏi là được |
| Claude tự quyết? | Không — chỉ chạy khi user gõ | **Có — tự chọn tool, tự gọi** |
| Số tool CBM expose | 3 command cố định | 5 tool linh hoạt |
| UX paradigm | CLI-like (gõ đúng cú pháp) | Chat-like (hỏi tự nhiên) |
| Thích hợp cho | Dev quen command line | **Mọi user, kể cả non-dev qua Cowork** |
| Phát hiện tool | User phải đọc docs | Claude tự phát hiện + suggest |
| Multi-step query | Phải gõ nhiều command rời | **Claude chain nhiều tool trong 1 lượt** |

### 2.2. Ví dụ cụ thể — Cùng một câu hỏi, UX khác nhau

**Câu hỏi của user:** *"Nếu tôi rename method `calculate_total` trong ShoppingCart thì ảnh hưởng những đâu?"*

**Phase 1 — User phải làm:**
```
$ claude "gì đó..."
Claude: "Để xem impact, dùng slash command /cbm-impact"
$ /cbm-impact calculate_total ShoppingCart
→ Output JSON
Claude: [đọc JSON] "Impact: 12 callers, 3 test..."
```
👉 **3 bước, user phải biết tool tồn tại + gõ đúng cú pháp.**

**Phase 2 — User chỉ cần:**
```
$ claude "Nếu tôi rename method calculate_total trong ShoppingCart thì ảnh hưởng những đâu?"

Claude tự động:
  1. [Detected intent: impact analysis]
  2. [Auto-call tool: cbm_impact(node="ShoppingCart.calculate_total")]
  3. [Receive: 12 callers, 3 tests, 2 external APIs]
  4. [Format thành câu trả lời tự nhiên]

Claude trả lời:
  "Rename `calculate_total` sẽ ảnh hưởng 12 nơi gọi, 3 test file, và 2 API
   public (/api/v1/cart/total, /api/v1/checkout/summary).
   Anh muốn em chuẩn bị migration plan không?"
```
👉 **1 bước. User không cần biết CBM, không cần biết tool, không cần gõ lệnh.**

---

## 3. 5 Tool CBM expose qua MCP (Phase 2)

Mỗi tool là 1 "API" Claude có thể tự gọi. Tool nào được chọn phụ thuộc **intent** từ câu hỏi user.

| # | Tool MCP | Mô tả ngắn | Trigger intent (Claude auto-detect) |
|---|---|---|---|
| 1 | `cbm_query` | Query graph theo tên/pattern | "cho tôi xem function X", "list methods in class Y" |
| 2 | `cbm_search` | Full-text search trong graph | "tìm chỗ nào gọi payment API", "search code containing..." |
| 3 | `cbm_impact` | Impact analysis khi thay đổi node | "đổi X thì ảnh hưởng ai", "safe to remove Y?", "dependencies of Z" |
| 4 | `cbm_snapshot_diff` | So sánh 2 snapshot graph | "gì đổi giữa v1 và v2", "PR này thay đổi gì", "diff baseline hôm qua" |
| 5 | `cbm_api_catalog` | Liệt kê toàn bộ API endpoint | "có API nào", "endpoints của service X", "public API catalog" |

### 3.1. Cơ chế "auto-detect intent"

Claude không "đoán" — mỗi tool có **schema JSON** với `description`, `parameters`, `examples`. LLM Claude dùng description để matching với câu hỏi user.

Ví dụ `cbm_impact` schema:
```json
{
  "name": "cbm_impact",
  "description": "Analyze impact of changing a function/class. Returns list of callers, tests, external APIs affected. Use when user asks 'what does X affect', 'safe to remove', 'dependencies of', 'rename impact', 'breaking change'.",
  "parameters": {
    "node": {"type": "string", "description": "Full name like 'ClassName.method_name'"},
    "depth": {"type": "integer", "default": 3, "description": "How deep to trace callers"}
  },
  "examples": [
    {"input": {"node": "ShoppingCart.calculate_total"}, "output": "12 callers, 3 tests..."}
  ]
}
```

Description **càng chi tiết** → Claude càng gọi đúng tool. Đây là nghệ thuật quan trọng khi thiết kế MCP (tốn thời gian nhất trong 8 SP Phase 2).

---

## 4. Flow kỹ thuật — Chuyện gì xảy ra khi user hỏi

```
┌─────────────────────────────────────────────────────────────┐
│  User (qua Claude Code CLI hoặc Claude Desktop hoặc Cowork) │
│  "Nếu đổi ShoppingCart.calculate_total thì ảnh hưởng ai?"    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Claude (LLM) — Intent Recognition                          │
│                                                              │
│  Input: câu hỏi user + list tool schemas available           │
│  Process: match intent "impact analysis" với tool descriptions│
│  Output: quyết định gọi cbm_impact(                          │
│    node="ShoppingCart.calculate_total")                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  MCP Protocol (stdio / SSE transport)                       │
│                                                              │
│  {"jsonrpc":"2.0","method":"tools/call",                     │
│   "params":{"name":"cbm_impact",                             │
│              "arguments":{"node":"ShoppingCart..."}}}        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  CBM MCP Server (local process, Python)                     │
│                                                              │
│  1. Load graph.json (từ GraphCache, invalidate theo mtime)  │
│  2. Run QueryEngine.impact(node, depth=3)                    │
│  3. Format result → structured JSON                          │
│                                                              │
│  Response:                                                   │
│  {"callers": [...12 items],                                  │
│   "tests": [...3 items],                                     │
│   "external_apis": [...2 items],                             │
│   "risk_score": 0.72}                                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Claude (LLM) — Natural Response Formation                  │
│                                                              │
│  Input: structured JSON từ tool                              │
│  Process: format thành ngôn ngữ tự nhiên                     │
│  Output:                                                     │
│  "Rename calculate_total sẽ ảnh hưởng 12 nơi gọi,            │
│   3 test file, và 2 API public. Em muốn phân tích            │
│   chi tiết từng API không?"                                  │
└──────────────────────────────────────────────────────────────┘
```

**Latency breakdown (target < 500ms total):**
- Intent detection (Claude): ~200ms (server-side)
- MCP transport overhead: ~10ms
- CBM query execution: ~50ms (graph in memory cache)
- Response formation: ~200ms
- **Total: ~460ms** — mượt như chat bình thường

---

## 5. 4 Scenario thực tế — UX before/after

### 5.1. Scenario A — Dev mới onboard

**Context:** Dev mới join team, chưa hiểu gì về codebase.

| Cũ (không có CBM+MCP) | Mới (có CBM+MCP) |
|---|---|
| Đọc README 2 giờ | Hỏi: "Cấu trúc dự án này thế nào?" |
| Clone repo, mở IDE, browse | Claude gọi `cbm_query` + `cbm_api_catalog` |
| Hỏi senior dev, chặn họ 30 phút | Claude trả lời có layer, module, API chính |
| Mất **1-2 ngày** nắm basic | Mất **15 phút** nắm basic |

### 5.2. Scenario B — Code review PR

**Context:** Dev mở PR thay đổi 5 file, reviewer muốn hiểu impact.

| Cũ | Mới (có CBM+MCP) |
|---|---|
| Đọc từng file diff | Hỏi: "PR này thay đổi gì quan trọng, có breaking change không?" |
| Tự tìm callers của hàm đổi | Claude gọi `cbm_snapshot_diff` (baseline vs PR branch) |
| Sợ sót bug regression | Claude gọi `cbm_impact` cho từng node modified |
| Mất **30-60 phút** review | Trả lời trong **30 giây** với risk score |

### 5.3. Scenario C — Debug production

**Context:** API `/api/v1/checkout` đang lỗi 500, cần trace cause.

| Cũ | Mới |
|---|---|
| Grep "checkout" toàn repo | "Endpoint /api/v1/checkout gọi những gì?" |
| Trace từng import thủ công | Claude gọi `cbm_impact` reverse từ endpoint |
| Mất **30-60 phút** | Trả lời: "checkout → CartService → PaymentGateway + InventoryCheck..." trong **10 giây** |

### 5.4. Scenario D — Refactor lớn

**Context:** CEO yêu cầu tách module `billing` thành service riêng.

| Cũ | Mới |
|---|---|
| Đoán effort bằng cảm giác | "Module billing có bao nhiêu coupling với phần còn lại?" |
| Lập kế hoạch thiếu | Claude gọi `cbm_search` + `cbm_impact` batch |
| Refactor 2 tuần, phát hiện phụ thuộc ẩn giữa chừng | Kết quả: 47 cross-module dependency, 12 shared DB table, risk HIGH |
| Làm lại plan | **Quyết đi/không đi trong 10 phút**, effort estimate chính xác |

---

## 6. Implementation breakdown Phase 2 — 8 SP chi tiết

| Task ID | Mô tả | SP | Ai làm |
|---|---|---|---|
| CBM-INT-201 | MCP server scaffold (`mcp_server/server.py`) với stdio transport | 1 | TechLead |
| CBM-INT-202 | `GraphCache` class với mtime-based invalidation | 1 | TechLead |
| CBM-INT-203 | Tool 1: `cbm_query` — query graph by name/pattern | 1 | TechLead |
| CBM-INT-204 | Tool 2+3: `cbm_search` + `cbm_impact` | 1.5 | TechLead |
| CBM-INT-205 | Tool 4: `cbm_snapshot_diff` | 1 | TechLead |
| CBM-INT-206 | Tool 5: `cbm_api_catalog` | 0.5 | TechLead |
| CBM-INT-207 | Tool schema descriptions + examples (tuning cho auto-invoke) | 1 | TechLead |
| CBM-INT-208 | Config mẫu Claude Desktop + Claude Code + Cursor + docs | 1 | TechLead |
| **Tổng** | | **8** | |

### 6.1. Việc quan trọng nhất — Tool Schema Tuning (CBM-INT-207)

Đây là task **dễ underestimate** nhưng quyết định chất lượng UX:

- Nếu description tool quá chung → Claude không gọi đúng lúc cần
- Nếu description quá hẹp → Claude không dùng được cho biến thể câu hỏi
- Cần viết **examples** cụ thể để LLM học pattern
- Cần test với **50+ câu hỏi biến thể** (VN + EN) → iterate description

**Đây là phần "làm AI thay người" — tốn thời gian nhất, đáng 1 SP riêng.**

### 6.2. Config mẫu cho user (CBM-INT-208)

Sau Phase 2, user setup:

**Claude Desktop (file `claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "codebase-map": {
      "command": "codebase-map-mcp",
      "args": ["--graph", "/path/to/project/docs/function-map/graph.json"]
    }
  }
}
```

**Claude Code CLI:**
```bash
$ claude mcp add codebase-map codebase-map-mcp --graph ./docs/function-map/graph.json
```

**Cowork (khi có plugin — Phase 3):**
Click install → tự động set up → xong.

---

## 7. Tại sao Phase 2 = Moat thực sự của CBM

### 7.1. Phase 1 chỉ là hook — Phase 2 là daily use

| Metric | Phase 1 (Slash Command) | **Phase 2 (MCP Auto)** |
|---|---|---|
| User dùng lần đầu | 70% (tò mò thử) | 70% |
| **Retention tuần 2** | 15% (quên command) | **50%** (hỏi tự nhiên) |
| **Daily active use** | 5% | **35%** |
| Word-of-mouth | Thấp | Cao (dev khoe "Claude tự hiểu codebase") |

Dẫn chứng: Cursor AI, Continue.dev, Sourcegraph Cody đều chứng minh — **natural language + auto-invoke** là khác biệt giữa "dev thử 1 lần" và "dev dùng hàng ngày".

### 7.2. Phase 2 mở ra Vietnamese-friendly AI coding

Slash command không "hiểu" tiếng Việt. MCP auto-invoke thì Claude tự hiểu:
- *"function tính tổng giỏ hàng có ai gọi không?"*
- *"nếu xóa service thanh toán thì sao?"*
- *"module đơn hàng có dính dáng gì tới module kho?"*

→ Đây là **cửa mở** cho dev Việt dùng AI coding — khác biệt cạnh tranh lớn với repomix/serena (đều EN-only UX).

### 7.3. Phase 2 là cầu nối sang KMP

- CBM MCP server = **graph layer**
- KMP MCP server (sau này) = **RAG layer trên graph + code semantic**
- Chung protocol → user install cả hai → upgrade path tự nhiên → revenue

---

## 8. Rủi ro kỹ thuật Phase 2 (CTO view)

| # | Rủi ro | Mitigation |
|---|---|---|
| R1 | Graph quá lớn (>10MB JSON) → MCP latency cao | `GraphCache` + lazy load subgraph |
| R2 | Claude gọi sai tool do description không rõ | CBM-INT-207: iterate tool schema với 50+ test prompt |
| R3 | MCP version breaking change | Pin protocol version, semver giữ backward compat |
| R4 | Concurrent graph generation + query | File lock + graceful degradation |
| R5 | User config sai path graph → confused UX | Error message rõ + auto-detect `./docs/function-map/graph.json` |
| R6 | Security: MCP server expose graph path | Bind local only, auth token tùy chọn |

---

## 9. Đo lường thành công Phase 2

### 9.1. KPI technical

| Metric | Target |
|---|---|
| P95 tool call latency | < 500ms |
| Tool invocation accuracy (đúng tool) | > 90% |
| Graph load time (first) | < 2s |
| MCP uptime local | > 99% |

### 9.2. KPI business (30 ngày sau phát hành)

| Metric | Target |
|---|---|
| MCP tool call total | 5.000/tuần |
| Unique MCP users | 500 |
| Average tool calls/user/ngày | 5+ |
| User survey "saves time vs alternative" | > 70% yes |

---

## 10. Tổng kết — Tại sao Phase 2 đáng đầu tư

1. **UX khác biệt 10x** — user không cần học command, hỏi là được
2. **Daily-use moat** — retention tuần 2 tăng từ 15% → 50%
3. **Vietnamese-first** — dev Việt có công cụ code analysis hiểu tiếng Việt đầu tiên
4. **Bridge sang KMP** — protocol chung, upgrade path tự nhiên, kéo user từ free → paid
5. **Competitive gap** — repomix, serena chưa có MCP server → CBM vươn lên dẫn đầu ngay khi launch

**Chi phí 8 SP (2 tuần) là rẻ cho tác động này.** Đây là sprint đáng giá nhất trong chuỗi CBM-INT.

---

## Liên kết

- [Technical Plan](./Technical_Plan_CBM_Claude_Integration.md) — Phase 2 nằm trong Section 2 của file này
- [Strategy Memo](./Strategy_Memo_CBM_Claude_Integration.md) — Lý do chọn 3-phase combo
- [Language Coverage Analysis](./Language_Coverage_Analysis.md)
- [Project Archetype GTM](./Project_Archetype_GTM_Strategy.md)
- [CBM UI Preview Integration](./CBM_UI_Preview_Integration.md)
- [Open Source Publishing Strategy](./Open_Source_Publishing_Strategy.md)

---

*Phase2_MCP_Explainer.md v1.0 — Hướng dẫn chi tiết Phase 2 cho CEO · Codebase Map project · 16/04/2026*
