# /review-gate — 3-Tầng Review Gate: Tester → CTO → Designer

# HC-AI | ticket: FDD-TOOL-CODEMAP

> Slash command kích hoạt khi user gõ `/review-gate`.
> **BẮT BUỘC** chạy trước khi chuyển PR cho CEO review.
> Adapted from HC Review Gate v2.0 — CEO Decision 04/04/2026.
> Flow: **Tester verify → CTO review → Designer review → SHIPIT → CEO**

---

## TRIGGER

Khi PM hoặc bất kỳ agent nào gõ `/review-gate PR #XX` hoặc `/review-gate` (auto-detect current branch PR).

---

## QUY TRÌNH THỰC HIỆN — 6 BƯỚC

### Bước 1: Xác định PR scope

```
1. Tìm PR number (từ argument hoặc current branch)
2. git diff main..HEAD --stat → danh sách files changed
3. Phân loại PR:
   - Feature (Parser+Exporter) → Tester full + CTO 5D + Designer 5D
   - Feature (Parser/Graph only) → Tester + CTO 5D + Designer skip
   - Feature (HTML/D3 only) → Tester + CTO A+B+E + Designer 5D
   - Bug fix → Tester verify fix + CTO A+C+E + Designer C+D (nếu HTML)
   - Docs/Config → Tester skip + CTO quick scan + Designer skip
```

### Bước 2: TESTER VERIFY (chạy trước CTO + Designer)

> Tester test thực tế — chạy tool trên HC project hoặc sample project.

```markdown
## Tester Verify — PR #XX

### Functional Test
- [ ] `codebase-map generate -c codebase-map.example.yaml` chạy thành công
- [ ] Output JSON có đủ nodes + edges
- [ ] Output HTML mở được trong browser, graph render đúng
- [ ] CLI commands hoạt động: query, impact, search, summary

### Edge Cases
- [ ] Empty project (0 Python files) → thông báo rõ ràng
- [ ] File có syntax error → skip + warning (không crash)
- [ ] Config thiếu field → error message hướng dẫn
- [ ] Path không tồn tại → error rõ ràng

### Regression
- [ ] Chạy trên HC project: verify node count, edge count không giảm bất thường
- [ ] Các CLI commands cũ vẫn hoạt động đúng
- [ ] HTML exporter vẫn render đúng (D3.js bundle hoạt động offline)

### Lint Gate
- [ ] `black --check codebase_map/` → PASS
- [ ] `isort --check codebase_map/` → PASS
- [ ] `flake8 codebase_map/` → PASS
```

**Nếu FAIL:** PM điều phối dev fix → Tester verify lại → PASS mới chuyển tiếp.

### Bước 3: CTO Review (5 Dimensions — 100 điểm)

```markdown
### A. Code Logic & Correctness (25 điểm)
- [ ] (5) AST parsing logic đúng — extract đủ functions, classes, methods
- [ ] (5) Edge cases handled (decorators, nested functions, lambdas)
- [ ] (5) Không có hardcoded paths hoặc fake data
- [ ] (5) Error handling đúng pattern (try/except có logging)
- [ ] (5) Graph builder tạo đúng nodes + edges từ parser output

### B. Architecture & Structure (25 điểm)
- [ ] (5) Separation đúng: Parser → Graph → Exporter
- [ ] (5) DRY — không duplicate code > 10 dòng
- [ ] (5) BaseParser interface được tuân thủ
- [ ] (5) Config loader xử lý đúng YAML schema
- [ ] (5) File/function size hợp lý (< 300 dòng)

### C. Parser Accuracy & Graph Integrity (25 điểm — CRITICAL)
- [ ] (7) MỌI function/class/method trong scope được parse
- [ ] (6) Call graph edges chính xác (không false positives > 5%)
- [ ] (5) Layer classification đúng (route/service/model/util/schema/test)
- [ ] (4) Node metadata đầy đủ (file, line, type, layer)
- [ ] (3) Không có orphan nodes giả (trừ constants/configs)

⚠️ AUTO BLOCK nếu dimension C < 20/25

### D. Output Quality (15 điểm)
- [ ] (5) JSON output valid, parseable, đủ fields
- [ ] (4) HTML output render đúng trong browser (Chrome, Firefox, Safari)
- [ ] (3) D3.js force graph hiển thị đúng clusters/colors
- [ ] (3) Query engine trả kết quả chính xác

### E. Production Readiness (10 điểm)
- [ ] (3) Lint pass: black + isort + flake8
- [ ] (3) CI workflow chạy thành công
- [ ] (2) Không dead code, unused imports
- [ ] (2) Comment `# HC-AI | ticket: FDD-TOOL-CODEMAP` trên AI blocks
```

### Bước 4: Designer Review (5 Dimensions — 100 điểm)

> Chỉ khi PR có HTML/D3.js changes. So với design-preview/ files.

```markdown
### A. Layout & Structure (25 điểm)
- [ ] (7) Page layout match Design approved (design-preview/)
- [ ] (6) Component hierarchy đúng (sidebar, graph area, toolbar)
- [ ] (5) Responsive behavior hợp lý
- [ ] (4) Title, header match design
- [ ] (3) Action buttons/controls đúng vị trí

### B. Visual Accuracy (25 điểm)
- [ ] (7) Color scheme match design (node colors, edge colors, background)
- [ ] (6) Typography đúng (font, size, weight)
- [ ] (5) Icon/symbol usage đúng (node shapes, layer indicators)
- [ ] (4) Spacing/padding consistent
- [ ] (3) Border, shadow, radius match design

### C. Interactive Elements (20 điểm)
- [ ] (5) Node click/hover hoạt động (tooltip, highlight)
- [ ] (5) Zoom/pan smooth
- [ ] (4) Search/filter hoạt động
- [ ] (3) Minimap hiển thị đúng (nếu có)
- [ ] (3) Legend/toolbar functional

### D. Data Display (20 điểm)
- [ ] (5) Graph nodes hiển thị đúng info (name, type, layer)
- [ ] (5) Edges hiển thị đúng (direction, weight)
- [ ] (4) Cluster grouping đúng theo domain
- [ ] (3) Node count, edge count hiển thị
- [ ] (3) Empty state khi graph rỗng

### E. Offline & Compatibility (10 điểm)
- [ ] (3) D3.js bundle hoạt động offline (không CDN)
- [ ] (3) Hoạt động trên Chrome, Firefox, Safari
- [ ] (2) File size hợp lý (< 5MB cho graph lớn)
- [ ] (2) Load time < 3s cho 1000+ nodes
```

### Bước 4.5: Impact Analysis (auto-generated — CM-S2-05)

> **CM-S2-05: Tự động chèn impact analysis vào review gate report.**
> Dùng `codebase-map diff` để phát hiện structural risk của PR.

```bash
# Lấy structural impact của PR so với main branch
codebase-map diff main -f docs/function-map/graph.json --json > /tmp/pr-impact.json
```

Parse JSON output để build section Impact Analysis:

```markdown
## Impact Analysis (auto-generated by codebase-map)

| Metric | Value |
|--------|-------|
| Changed Nodes | 8 |
| Impact Zone | 23 |
| Risk Level | 🟡 Medium |

**Risk thresholds:**
- 🟢 Low: < 10 impact nodes
- 🟡 Medium: 10–50 impact nodes
- 🔴 High: > 50 impact nodes

**Top impacted nodes:**
- `app.modules.crm.service.CustomerService.create`
- `app.modules.crm.router.create_customer`
- `app.workers.cdp_segment.recalculate`
- ... and N more

**Changed files:** (list from `diff.changed_files`)
```

**Rules:**
- 🔴 High risk (>50 nodes) → ghi chú khẩn vào verdict, khuyến nghị split PR
- 🟡 Medium risk (10–50 nodes) → note vào CEO report
- 🟢 Low risk (<10 nodes) → chỉ hiển thị, không block
- Nếu `diff` chưa có dữ liệu (graph.json cũ) → chạy `codebase-map generate` trước

---

### Bước 5: Tổng hợp Score & Verdict

```
Final Score = (CTO Score × 0.6) + (Designer Score × 0.4)
Nếu PR không có HTML changes: Final Score = CTO Score (Designer skip)
```

### Bước 6: Quyết định

| Điều kiện | Verdict | Action |
|-----------|---------|--------|
| Tester FAIL | **BLOCKED** ❌ | Fix → Tester verify lại |
| Final Score = 100% | **SHIPIT** ✅ | CEO review |
| Final Score ≥ 90% (vòng 3) | **SHIPIT + NOTE** ⚠️ | CEO review kèm minor issues |
| Final Score < 90% (vòng 3) | **THÔNG BÁO KHẨN** 🚨 | CEO + đề xuất đạt >95% |
| CTO Dim C < 20/25 | **AUTO BLOCK** ❌ | Parser accuracy — PHẢI fix |

---

## RULES

1. **KHÔNG có ngoại lệ** — mọi PR qua 3 tầng trước CEO
2. **Tester PHẢI pass trước** — CTO + Designer chỉ review khi Tester PASS
3. **Max 3 vòng** — vòng 3 mà < 90% → thông báo khẩn CEO
4. **CTO Dim C AUTO BLOCK** — parser accuracy non-negotiable
5. **Song song** — CTO + Designer review cùng lúc (sau Tester PASS)
6. **Report lưu** — `docs/reviews/ReviewGate_PR{XX}_Round{N}_{date}.md`

---

*review-gate.md v1.0 | Codebase Map | Adapted from HC v2.0 | CEO Decision 06/04/2026*
