# /implement — Codebase Map Feature Implementation

# HC-AI | ticket: FDD-TOOL-CODEMAP

> Slash command kích hoạt khi user gõ `/implement` hoặc bắt đầu implement 1 feature.
> Claude thực hiện đúng 7 bước theo thứ tự, không bỏ bước nào.
> Adapted from HC Implement v1.0.

---

## 7-BƯỚC IMPLEMENT CHUẨN

### Bước 1 — Đọc Spec & Design

```bash
# Đọc feature spec trước khi làm bất cứ điều gì
cat specs/spec.md
cat project/CM-S1-TASK-BOARD.md
```

Nếu có FE (HTML/D3.js) changes:
```bash
# Đọc design approved
# Mở trong browser: design-preview/codebase-map-CM-S1-design.html
# Hoặc design tổng thể: design-preview/codebase-map-v2-design.html
```

Checklist đọc spec:
- [ ] Hiểu rõ task description + acceptance criteria
- [ ] Biết files cần tạo/sửa
- [ ] Biết design reference (nếu FE)
- [ ] Biết dependencies với tasks khác

---

### Bước 2 — Auto-Query Impact + Explore Codebase

> **CM-S2-04: Tự động query codebase map trước khi implement.**
> Giảm thời gian tìm file thủ công, bảo đảm không miss impact zone.

**Bước 2.1 — Auto-query impact zone:**

```bash
# Chạy codebase-map impact cho target class/function của feature
codebase-map impact "TargetClass" -f docs/function-map/graph.json --depth 2 --json
```

Claude parse JSON output để:
- Đếm số nodes trong impact zone
- Phân loại: target, direct dependency, route handler, event handler, async worker
- Build danh sách files cần đọc trước khi implement
- Cảnh báo nếu impact > 50 nodes (high risk change)

**Expected terminal output:**
```
[/implement] Step 2: Auto-querying codebase map...
Task: FDD-CRM-015 — Add bulk tag management to customers
Query: impact "CustomerService" --depth 2

Impact Zone (18 nodes):
  • CustomerService — target (service layer)
  • CustomerRepository — direct dependency
  • create_customer — route → CustomerService.create
  • update_customer — route → CustomerService.update
  • PipelineService.on_customer_update — event handler
  • CDPSegmentWorker.recalculate — async worker
  ... 12 more

[/implement] Files to review before implementing:
  crm/services/customer_service.py
  crm/repositories/customer_repository.py
  crm/routers/customer_router.py
  crm/models/customer.py

Proceeding to Step 3...
```

**Bước 2.2 — Explore patterns hiện có:**

```bash
# Xem parser pattern
cat codebase_map/parsers/python_parser.py
cat codebase_map/parsers/base.py

# Xem graph models
cat codebase_map/graph/models.py
cat codebase_map/graph/builder.py

# Xem exporter pattern
cat codebase_map/exporters/html_exporter.py
cat codebase_map/exporters/json_exporter.py
```

Mục tiêu: code mới phải follow đúng pattern đã có, không tự sáng tạo.

**Rule:** Nếu graph.json chưa tồn tại hoặc > 24h cũ → chạy `codebase-map generate` trước.

---

### Bước 3 — Plan (Optional review với user)

Trình bày plan ngắn gọn:
- Files sẽ tạo/sửa (list đầy đủ)
- Thay đổi models (Node, Edge, Graph nếu có)
- HTML/D3.js changes (nếu có)
- Impact lên existing features

Hỏi user: "Plan OK không, hay cần điều chỉnh?"

---

### Bước 4 — Implement + Test Loop

**Thứ tự viết code theo layer:**

```
Parser changes → Graph changes → Exporter changes → CLI changes
```

**Pattern chuẩn:**
```python
# Parser: kế thừa BaseParser, implement parse() method
# Graph: dùng Node, Edge, Graph dataclasses từ models.py
# Exporter: generate output từ Graph object
# CLI: dùng click, gọi qua builder/query engine
```

**Sau mỗi thay đổi quan trọng:**
```bash
# Self-test: chạy generate trên sample project
python -m codebase_map generate -c codebase-map.example.yaml

# Verify output
python -m codebase_map summary -f output/graph.json
```

**Comment bắt buộc trên mọi block AI-generated:**
```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
```

---

### Bước 5 — Quality Gate

```bash
# 1. Lint gate — BẮT BUỘC
black --check codebase_map/
isort --check codebase_map/
flake8 codebase_map/

# 2. Không hardcode paths
grep -r "\/Users\/" codebase_map/ --include="*.py"
# Phải trống — không có absolute paths

# 3. Verify HTML output (nếu có HTML changes)
# Mở output HTML trong browser, verify D3.js render đúng
```

---

### Bước 5.5 — Local Pre-flight Review Gate (BẮT BUỘC từ CM-S3)

> **CEO Decision 07/04/2026:** Chạy `/review-gate --local` TRƯỚC khi commit/push.
> Mục tiêu: bắt >80% issues sớm, giảm force-push, tiết kiệm CI minutes + CEO review time.

```bash
/review-gate --local
```

Claude thực hiện (đọc chi tiết ở `.claude/commands/review-gate.md` — Mode 1):

1. **Lint gate** — black + isort + flake8 (BẮT BUỘC PASS)
2. **Self-test generate** — `python -m codebase_map generate -c codebase-map-self.yaml`
3. **Impact analysis local** — `codebase-map diff main --json`
4. **CTO 5D scoring** — Claude tự chấm trên `git diff main..HEAD`
5. **Tester edge cases cơ bản** — 3-5 case chính
6. **Designer 5D local** — chỉ nếu có HTML changes, render + so với `design-preview/`

**Verdict gate:**

| Score | Action |
|-------|--------|
| ≥ 90 | ✅ GO → Bước 6 (Full Verification) → Bước 7 (Commit + PR) |
| 80–89 | ⚠️ Note → fix nhanh hoặc ghi vào PR body, cho phép push |
| < 80 | ❌ BLOCK → fix → re-run `/review-gate --local` |
| CTO Dim C < 20/25 | ❌ AUTO BLOCK — parser accuracy phải fix |
| Impact zone > 50 | ⚠️ WARN — cân nhắc split PR |

**Report lưu:** `docs/reviews/ReviewGate_Local_{branch}_{date}.md`

**Rule:** Local Pre-flight KHÔNG thay thế Remote Full (Mode 2). Sau khi push + CI pass, vẫn phải chạy `/review-gate PR #XX` trước CEO review.

---

### Bước 6 — Full Verification

```bash
# Generate trên HC project (real data)
codebase-map generate -c /path/to/HyperCommerce/codebase-map.yaml

# Verify graph stats
codebase-map summary -f graph.json
# Expected: ~1,386 nodes · ~8,285 edges · 7 domains

# Verify specific queries
codebase-map search "pipeline" -f graph.json
codebase-map impact "CustomerService" -f graph.json

# Lint final check
black --check codebase_map/ && isort --check codebase_map/ && flake8 codebase_map/
```

---

### Bước 7 — Commit + PR

```bash
# Tạo branch (KHÔNG push thẳng main)
git checkout main && git pull
git checkout -b feat/cm-s1-dayX-[slug]

# Commit với conventional message
git add [specific files only — không dùng git add -A]
git commit -m "feat(exporter): add sidebar tree to HTML output

# HC-AI | ticket: FDD-TOOL-CODEMAP"

# Push + tạo PR
git push -u origin feat/cm-s1-dayX-[slug]
gh pr create --title "feat: [mô tả ngắn]" --body "..."
```

**KHÔNG được push thẳng lên main.**

---

## CHECKLIST TRƯỚC KHI BÁO DONE

- [ ] Tất cả task requirements đã implement
- [ ] Lint pass: black + isort + flake8
- [ ] Generate chạy thành công trên sample/HC project
- [ ] HTML output render đúng trong browser (nếu có FE changes)
- [ ] Design match 100% với design-preview/ (nếu có FE changes)
- [ ] PR đã tạo đúng format
- [ ] BRIEF.md đã cập nhật trạng thái
- [ ] Comment `# HC-AI | ticket: FDD-TOOL-CODEMAP` trên AI blocks

---

*implement.md v1.1 | Codebase Map | Added Bước 5.5 Local Pre-flight | CEO Decision 07/04/2026*
