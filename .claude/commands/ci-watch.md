# /ci-watch — Watch CI Status, Auto-Fix & Re-push

# HC-AI | ticket: FDD-TOOL-CODEMAP

> Slash command cho dev: kiểm tra CI status, đọc lỗi, tự fix, push lại.
> Adapted from HC CI-Watch v1.0 — CEO Decision 05/04/2026.

---

## TRIGGER

Khi dev gõ `/ci-watch` hoặc `/ci-watch PR #XX`.

---

## QUY TRÌNH — 5 BƯỚC

### Bước 1: Xác định PR và CI status

```
1. Nếu có argument PR #XX → dùng PR đó
2. Nếu không → git branch --show-current → tìm PR cho branch hiện tại
3. Chạy: gh pr checks <number> → lấy trạng thái từng check
4. Nếu tất cả PASS → báo "CI green, no action needed" → DONE
5. Nếu có FAIL → tiếp bước 2
```

### Bước 2: Đọc error logs

```
1. gh run list --branch <branch> --limit 1 → lấy run ID mới nhất
2. gh run view <run-id> --log-failed → đọc logs của jobs bị fail
3. Phân loại lỗi:
   - FORMAT: black/isort errors → Auto-fix (Bước 3)
   - LINT: flake8 errors → Attempt fix (Bước 3)
   - SELF-TEST: generate/summary failures → Analyze (Bước 4)
```

### Bước 3: Auto-fix (FORMAT + LINT)

```
1. FORMAT errors:
   - black codebase_map/ && isort codebase_map/
   - git add -A → commit "[ci-fix] auto-format black + isort"

2. LINT errors (flake8):
   - Đọc file + line number từ flake8 output
   - Fix từng lỗi (unused import, whitespace, line length)
   - git add → commit "[ci-fix] fix flake8 lint errors"

3. Push tất cả fixes: git push
```

### Bước 4: Self-test failures (cần user confirm)

```
1. Đọc CI output → tìm error message
2. Đọc source file liên quan
3. Phân tích root cause:
   - Parser bug → propose fix
   - Config issue → propose fix
   - Import error → propose fix
4. HIỂN THỊ diff cho dev review TRƯỚC KHI apply
5. Nếu dev approve → apply fix → commit → push
6. Nếu dev reject → show guidance, dev tự fix
```

### Bước 5: Re-check CI status

```
1. Chờ 30 giây sau push
2. gh pr checks <number> → kiểm tra CI đang chạy lại
3. Báo dev: "CI re-running. Check back in ~3 minutes or run /ci-watch again."
```

---

## SAFETY RULES

1. **Max 2 auto-fix cycles** per invocation — tránh loop vô hạn
2. **KHÔNG auto-fix logic bugs** — luôn show cho dev
3. **Luôn show diff** trước khi push
4. **Commit message prefix:** `[ci-fix]` để phân biệt với code commits

---

## OUTPUT FORMAT

```markdown
# CI Watch Report — PR #XX

## CI Status
| Check | Status | Details |
|-------|--------|---------|
| Lint | ✅/❌ | black, isort, flake8 |
| Self-test | ✅/❌ | generate, summary |

## Errors Found
| # | Category | File:Line | Error | Auto-fixable? |
|---|----------|-----------|-------|---------------|
| 1 | FORMAT | codebase_map/cli.py:10 | black formatting | ✅ Fixed |
| 2 | LINT | codebase_map/parsers/python_parser.py:25 | unused import | ✅ Fixed |

## Actions Taken
- [x] Auto-fixed: black + isort formatting
- [x] Auto-fixed: flake8 unused import
- [ ] Pending: self-test failure (needs dev review)

## Next Step
- CI re-running after push. ETA: ~3 minutes.
- Run `/ci-watch` again to check results.
```

---

*ci-watch.md v1.0 | Codebase Map | Adapted from HC v1.0 | 06/04/2026*
