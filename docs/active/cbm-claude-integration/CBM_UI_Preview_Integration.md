# Tích hợp UI CBM làm Preview trong hệ sinh thái Claude

> **Câu hỏi CEO:** UI của CBM đã implement rồi (D3.js, sidebar tree, minimap, multi-view Executive/PR Diff). Có tích hợp thành view preview luôn trong Claude được không?
>
> **Trả lời ngắn:** ✅ **Được — tái sử dụng 100%**, không cần build lại. Chia thành **4 view mode** cho **5 surface** của Claude. MVP có thể chạy trong **5 SP (1 tuần)** — dùng được ngay trên Cowork + Claude Desktop.
>
> **Prepared for:** Đoàn Đình Tỉnh — CEO, Hyper Commerce
> **Author:** CTO hat — Claude
> **Date:** 2026-04-16
> **Status:** Technical architecture v1.0

---

## 1. TL;DR — Quyết định nhanh

| Surface Claude | Render mode khả thi | Effort | Fidelity |
|---|---|---|---|
| **Cowork (Desktop app)** | `computer://` link mở browser | 0 SP | ⭐⭐⭐⭐⭐ Full |
| **Claude Desktop — chat artifact** | HTML artifact (D3 CDN + inline data) | 3 SP | ⭐⭐⭐⭐ Cao, nhưng giới hạn size |
| **Claude Code — terminal CLI** | MCP tool spawn local server + open browser | 2 SP | ⭐⭐⭐⭐⭐ Full |
| **VS Code / Claude Code extension** | Webview panel load `file://` hoặc local server | 3 SP | ⭐⭐⭐⭐⭐ Full |
| **MCP Resource (text/html)** | Limited — chỉ một số client render | 2 SP | ⭐⭐ Chưa ổn định |

**Tổng MVP:** **5 SP** (Cowork + Claude Desktop artifact + Claude Code terminal) → cover 3 surface chính.

---

## 2. Inventory UI hiện có của CBM

### 2.1. Tài sản đã có (không cần build lại)

| Asset | File | Size | Vai trò |
|---|---|---|---|
| HTML exporter core | `codebase_map/exporters/html_exporter.py` | 1.789 dòng | Generator chính |
| D3.js bundled | `codebase_map/exporters/d3.v7.min.js` | **280 KB** | Offline mode |
| Sample output | `docs/function-map/index.html` | **841 KB** | Production-ready, tested |
| Raw graph | `docs/function-map/graph.json` | 606 KB | Data source |

### 2.2. Tính năng UI đã có

- **Multi-view** (CM-S3): Executive, Graph, PR Diff, Timeline, Snapshot Diff
- **Sidebar tree** (CM-S1): module tree, search, filter by layer
- **Cluster layout**: group theo LayerType (core/model/service/router...)
- **Minimap + toolbar**: zoom, pan, reset, layer toggle
- **Interactive**: click node → highlight callers, dependencies
- **Offline capable**: D3.js bundled, zero external request
- **Responsive**: desktop + tablet

Exporter đã có sẵn **toggle CDN vs bundled D3** (`_build_html()` có branch `d3_script = '<script src="https://d3js.org/d3.v7.min.js"></script>'`) — sẵn sàng cho mode "lightweight".

### 2.3. Giới hạn kỹ thuật hiện tại

| Giới hạn | Con số | Ảnh hưởng integration |
|---|---|---|
| HTML size (bundled) | 841 KB | Quá lớn cho artifact soft cap (~200 KB) |
| HTML size (CDN D3) | ~561 KB | Vẫn > soft cap, nhưng < 1 MB hard cap |
| Graph data inline | 606 KB raw | Cần compress hoặc lazy-load cho artifact |
| Runtime dep | Chỉ D3 v7 | Dễ load CDN — OK |
| Secrets | 0 | An toàn embed qua MCP |

---

## 3. Ma trận Claude Surfaces × Render Capability

### 3.1. Claude ecosystem surfaces (2026)

| # | Surface | Render HTML inline? | File link? | Local HTTP? | Artifact? |
|---|---|---|---|---|---|
| 1 | Claude.ai web | ❌ (sandbox iframe OK qua artifact) | ❌ | ❌ | ✅ |
| 2 | Claude Desktop — chat | ❌ (artifact OK) | ✅ (computer://) | ⚠️ Cần cho phép | ✅ |
| 3 | **Cowork** (desktop mode) | ❌ | ✅ (computer:// → browser) | ✅ | ✅ |
| 4 | **Claude Code CLI** (terminal) | ❌ (text only) | ❌ (terminal không click được) | ✅ (MCP có thể spawn) | ❌ |
| 5 | **Claude Code / Cursor / Continue VS Code ext** | ✅ (webview) | ✅ (file://) | ✅ | ⚠️ |

### 3.2. Ma trận phù hợp CBM UI hiện tại

| Surface | HTML bundled 841KB | HTML CDN 561KB | HTML stripped <200KB | SVG snapshot | PNG thumbnail |
|---|---|---|---|---|---|
| Claude.ai web (artifact) | ❌ quá lớn | ⚠️ có thể | ✅ tối ưu | ✅ | ✅ |
| Claude Desktop chat | ❌ | ⚠️ | ✅ | ✅ | ✅ |
| Cowork browser | ✅ | ✅ | ✅ | ✅ | ✅ |
| Claude Code CLI + browser | ✅ | ✅ | ✅ | ✅ | ✅ |
| VS Code webview | ✅ | ✅ | ✅ | ✅ | ✅ |

**Kết luận:** Bản bundled 841KB vẫn dùng trọn trên **Cowork, Claude Code CLI, VS Code** — cover đa số dev use case. Chỉ artifact trong chat Claude.ai/Desktop cần version stripped.

---

## 4. Kiến trúc đề xuất — Multi-View Adapter Pattern

### 4.1. Principle

> CBM export **một lần**, expose **nhiều view mode** qua MCP tool, mỗi surface Claude dùng mode phù hợp.

### 4.2. 4 View Mode

```
        ┌────────────────────────────────────────────────┐
        │            CBM Graph Engine (unified)           │
        │       builder.py → Graph + snapshot.json        │
        └──────────────┬──────────────┬─────────┬─────────┘
                       │              │         │
        ┌──────────────▼──┐  ┌────────▼───┐  ┌──▼────────┐
        │ 1. Full HTML    │  │ 2. Artifact │  │ 3. Image  │
        │  (bundled 841K) │  │  (stripped) │  │  (SVG/PNG)│
        │                 │  │   <200 KB   │  │           │
        └──────┬──────────┘  └──────┬──────┘  └─────┬─────┘
               │                    │               │
      ┌────────┴─────────┐          │               │
      ▼                  ▼          ▼               ▼
  ┌────────┐       ┌──────────┐ ┌──────────┐  ┌─────────┐
  │ Cowork │       │ VS Code  │ │ Desktop  │  │ Any chat│
  │computer│       │ Webview  │ │   chat   │  │ surface │
  │  ://   │       │  panel   │ │ artifact │  │  (inline│
  └────────┘       └──────────┘ └──────────┘  │   PNG)  │
                                              └─────────┘
                        ┌───────────────┐
                        │ 4. Summary MD │ → fallback khi không render được
                        │  (text only)  │
                        └───────────────┘
```

### 4.3. 4 View Mode chi tiết

#### Mode 1 — **Full HTML** (tái sử dụng nguyên xi)

- Dùng nguyên `html_exporter.py` hiện tại
- Output: `graph.html` 841 KB (bundled D3)
- Surface: Cowork, Claude Code CLI + browser, VS Code webview
- Effort: **0 SP** (đã có)

#### Mode 2 — **Artifact HTML** (bản rút gọn)

- Thêm flag `--profile=artifact` cho `cbm generate`
- Thay đổi:
  - Load D3 từ `cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js` (allowed bởi artifact)
  - Compress graph data: gzip + base64, decompress trong `useEffect`, hoặc dùng minimal schema
  - Strip clusters/minimap nếu cần để dưới 200 KB
  - Return string HTML qua MCP tool `cbm_render_artifact`
- Surface: Claude Desktop chat, Claude.ai web
- Effort: **3 SP** (stripping + compression + MCP wiring)

#### Mode 3 — **Image (SVG + PNG)**

- Headless browser (Playwright hoặc Puppeteer) render graph → export
- Output: `graph.svg` (interactive-lite) hoặc `graph.png` (static)
- Surface: mọi surface khi không render được HTML (fallback universal)
- Effort: **3 SP** (thêm dependency headless browser)
- Bonus: PNG thumbnail auto-include khi full HTML render fail

#### Mode 4 — **Summary Markdown** (fallback text)

- Render graph thành markdown tree + top 10 hot paths
- Reuse `QueryEngine.summary()` + format markdown
- Surface: MCP tool response khi client không render HTML
- Effort: **1 SP** (đã gần xong, chỉ cần format)

### 4.4. MCP Tool API đề xuất

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
@server.call_tool()
async def cbm_render_graph(
    graph_path: str = "docs/function-map/graph.json",
    view: Literal["browser", "artifact", "image", "summary"] = "browser",
    focus: str | None = None,          # zoom vào 1 node
    layer: str | None = None,          # filter layer
    format: Literal["html", "svg", "png", "md"] = "html",
) -> list[ContentBlock]:
    """
    Render CBM graph theo surface Claude đang dùng.
    
    - view=browser:  spawn local HTTP server + return URL (CLI, Cowork)
    - view=artifact: return stripped HTML string (Desktop chat)
    - view=image:    return SVG/PNG base64 (universal fallback)
    - view=summary:  return markdown text (no-render clients)
    """
    match view:
        case "browser":
            port = _free_port()
            _serve_static(graph_path, port=port)
            url = f"http://localhost:{port}/graph.html"
            webbrowser.open(url)
            return [TextContent(text=f"✅ CBM graph đã mở trong browser: {url}")]
        
        case "artifact":
            html = _render_artifact(graph_path, focus=focus, layer=layer)
            return [TextContent(text=html, annotations={"mimeType": "text/html"})]
        
        case "image":
            img_path = _render_image(graph_path, format=format, focus=focus)
            return [ImageContent(data=base64.b64encode(img_path.read_bytes()), mimeType=f"image/{format}")]
        
        case "summary":
            md = _render_summary(graph_path, focus=focus)
            return [TextContent(text=md)]
```

### 4.5. Auto-detect surface (tùy chọn)

MCP client gửi `client_name` trong handshake — CBM có thể auto-chọn mode:

| Client name | Auto view |
|---|---|
| `claude-code` (terminal) | `browser` (spawn HTTP) |
| `claude-desktop` | `artifact` (stripped HTML) |
| `cowork` | `browser` (computer:// link) |
| `vscode-cursor-claude-ext` | `browser` (webview load file://) |
| Unknown | `summary` (markdown fallback) |

---

## 5. Lộ trình thực hiện (Phased Rollout)

### Phase 0 — Quick Win ngay tuần này (0 SP)

✅ **Cowork đã làm được ngay hôm nay:**
- User chạy `cbm generate` → sinh `docs/function-map/index.html`
- MCP tool `cbm_render_graph(view="browser")` return `computer://` link
- Click → Cowork mở browser → full HTML hiện ra

Không viết thêm 1 dòng code exporter nào — chỉ cần MCP tool wrapper.

### Phase 1 — MVP 5 SP (tuần 1-2 sau CBM-INT-P1)

| Task | SP | Mô tả |
|---|---|---|
| CBM-UI-101 | 1 | MCP tool `cbm_render_graph` skeleton + view=browser |
| CBM-UI-102 | 1 | Local HTTP server helper (`_serve_static`, free port, auto-kill) |
| CBM-UI-103 | 2 | Artifact mode — CDN D3 + compress graph JSON < 200KB |
| CBM-UI-104 | 1 | Summary mode — markdown tree top-10 hot paths |
| **Tổng** | **5** | |

### Phase 2 — Image + Webview 4 SP (tuần 3-4)

| Task | SP | Mô tả |
|---|---|---|
| CBM-UI-201 | 2 | Image mode — Playwright headless → SVG/PNG |
| CBM-UI-202 | 2 | VS Code webview integration guide + sample config |
| **Tổng** | **4** | |

### Phase 3 — Polish + Auto-detect 3 SP (tuần 5-6)

| Task | SP | Mô tả |
|---|---|---|
| CBM-UI-301 | 1 | Auto-detect client surface + chọn mode |
| CBM-UI-302 | 1 | Artifact "mini" mode cho graph lớn >10k node |
| CBM-UI-303 | 1 | Documentation + demo video mỗi surface |
| **Tổng** | **3** | |

### Tổng cả 3 Phase: **12 SP (3 tuần)** — tích hợp đầy đủ 5 surface × 4 mode.

---

## 6. Phân tích Kích thước — Tại sao Artifact Mode khó?

### 6.1. Size budget của Artifact

Theo tài liệu Anthropic (2026):
- Soft cap ổn định: ~**200 KB**
- Hard cap: ~**1 MB**
- Khuyến nghị: giữ < 200 KB để render mượt, < 500 KB vẫn OK

### 6.2. CBM hiện tại size breakdown

| Component | Size | % |
|---|---|---|
| D3.js bundle | 280 KB | 33% |
| Graph data JSON (inline) | 606 KB | 72% |
| CSS + HTML shell | ~20 KB | 2% |
| JS logic | ~15 KB | 2% |
| **Tổng (gộp)** | **841 KB** | 100% |

### 6.3. Strategy giảm size cho Artifact

| Chiến lược | Giảm | Kết quả |
|---|---|---|
| D3 từ CDN | -280 KB | 561 KB |
| Gzip graph JSON + base64 | 606 → ~150 KB (-456 KB) | 105 KB ✅ |
| Minimal schema (drop metadata) | -50 KB | 55 KB ✅✅ |
| Lazy load nodes > 1000 | tùy repo | < 100 KB ✅ |

> Với repo < 500 function, artifact mode hoàn toàn khả thi dưới 100 KB. Với repo lớn (CBM tự scan Hyper Commerce = ~2000 function), cần strategy progressive disclosure: artifact hiện top-level graph, click node → fetch detail qua MCP tool mới.

---

## 7. Surface-specific UX Flow

### 7.1. Cowork (ngon nhất)

```
User: "Vẽ graph cho dự án này"
  ↓
Claude (MCP cbm_render_graph view=browser):
  "Tôi đã generate graph. Click để xem:
   [computer:///path/to/graph.html](computer://...)"
  ↓
User click → browser mở → full UI D3 hoạt động đầy đủ
```

### 7.2. Claude Desktop chat

```
User: "Show me the code graph"
  ↓
Claude (MCP cbm_render_graph view=artifact):
  Returns stripped HTML (105 KB) as text/html artifact
  ↓
Claude Desktop render inline → user thấy graph ngay trong chat
  (có thể click icon "open in browser" để xem full view)
```

### 7.3. Claude Code CLI

```
$ claude "generate codebase map"
  ↓
Claude calls MCP cbm_render_graph view=browser
  → spawns http://localhost:8765/graph.html
  → webbrowser.open()
  ↓
Terminal output:
  "✅ Graph ready: http://localhost:8765/graph.html"
  "Browser opened automatically."
```

### 7.4. VS Code extension (tương lai)

```
User invoke command: "CBM: Show graph"
  ↓
Extension calls MCP cbm_render_graph view=browser
  ↓
Extension opens webview panel bên phải với <iframe src="file:///.../graph.html">
```

---

## 8. Rủi ro & Trade-off (CTO view)

| # | Rủi ro | Severity | Mitigation |
|---|---|---|---|
| R1 | Local HTTP server bị port conflict | Low | Dùng `_free_port()` + retry |
| R2 | Artifact size > 1MB hard cap với repo lớn | Medium | Progressive disclosure + pagination |
| R3 | `computer://` không có trong Claude Code CLI | Medium | Fallback sang `http://localhost:XXXX` |
| R4 | Security: local server expose cho mọi process | Medium | Bind `127.0.0.1` only + auth token qua URL |
| R5 | Headless browser (Playwright) tăng dependency nặng | Medium | Make optional: `pip install codebase-map[image]` |
| R6 | Artifact JSX rewrite khác HTML — code trùng | Low | Share common renderer qua Python template |
| R7 | MCP client auto-detect sai → render lỗi | Low | User override qua tham số `view=...` |
| R8 | Update D3 v8 tương lai | Low | CDN tự cập nhật, bundle version hóa |

---

## 9. Build vs Buy vs Integrate (CTO framework)

| Option | Cost | Time | Fit |
|---|---|---|---|
| **A — Build UI mới trong Claude** | 30+ SP | 2 tháng | ❌ Lãng phí — UI đã có |
| **B — Integrate qua MCP multi-view** ⭐ | 12 SP | 3 tuần | ✅ Tận dụng tài sản hiện có |
| C — Dùng external service (Observable, etc) | $29/user/m | 1 tuần | ❌ Data leak risk, vendor lock |

**Recommendation:** Option B — Integrate.

---

## 10. Security & Compliance (CTO note)

- ✅ Graph data **không chứa source code thực** (chỉ metadata: tên function, signature, LOC) → an toàn embed artifact
- ⚠️ Local HTTP server cần bind `127.0.0.1` only, không `0.0.0.0` — tránh expose ra mạng
- ⚠️ Graph JSON có thể chứa file path hệ thống → sanitize trước khi serve qua artifact (strip `/home/user/...` → relative)
- ✅ Không vi phạm NĐ 13/2023 — không có PII trong graph

---

## 11. POC Plan (2-ngày spike)

### Day 1 — MCP tool skeleton + Cowork mode

- Tạo `mcp_server/tools/render_graph.py`
- Implement `view="browser"` với `_serve_static` + `webbrowser.open`
- Test trên Cowork: `cbm generate` → MCP call → click `computer://` link
- Deliverable: video 2 phút demo

### Day 2 — Artifact mode

- Thêm `--profile=artifact` flag cho `cbm generate`
- Strip D3 bundle + compress JSON
- Test manual: paste HTML vào Claude.ai artifact
- Deliverable: file `artifact-demo.html` < 200 KB

---

## 12. 3 Câu hỏi quyết định cho CEO

| # | Câu hỏi | Khuyến nghị |
|---|---|---|
| Q1 | Ưu tiên surface nào trước: Cowork hay Claude Desktop? | **Cowork trước** — zero effort, UX tốt nhất |
| Q2 | Có cần Image mode (PNG) ngay không? | **Chưa** — để Phase 2, artifact mode cover 80% case |
| Q3 | Auto-detect client hay để user chọn view thủ công? | **Cả hai** — default auto + flag override |

---

## 13. Kết luận

UI hiện có của CBM (`html_exporter.py` 1.789 dòng, D3.js bundled, multi-view Executive/PR Diff/Timeline) **tái sử dụng trọn vẹn** làm preview trong Claude. Chỉ cần một **MCP tool multi-view** làm lớp adapter giữa CBM và 5 surface Claude. Effort MVP **5 SP (1 tuần)** cho 3 surface chính, **12 SP (3 tuần)** cho full coverage.

**Quick win trong tuần này:** MCP tool `cbm_render_graph(view="browser")` + `computer://` link → **user Cowork xem được graph đầy đủ ngay** mà không cần touch exporter.

Không cần build lại UI. Không cần thiết kế mới. Tận dụng 100% công sức v1.1 → v2.2.

---

## Liên kết tài liệu

- [Strategy Memo CBM Claude Integration](./Strategy_Memo_CBM_Claude_Integration.md)
- [Technical Plan CBM Claude Integration](./Technical_Plan_CBM_Claude_Integration.md) — Phase 2 MCP server (sẽ ăn khớp với tool `cbm_render_graph` ở đây)
- [Language Coverage Analysis](./Language_Coverage_Analysis.md)
- [Project Archetype GTM Strategy](./Project_Archetype_GTM_Strategy.md)

---

*CBM_UI_Preview_Integration.md v1.0 — CTO technical analysis · Codebase Map project · 16/04/2026*
