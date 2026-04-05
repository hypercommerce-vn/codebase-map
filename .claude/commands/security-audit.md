# /security-audit — Codebase Map Security Audit

# HC-AI | ticket: FDD-TOOL-CODEMAP

> Slash command kích hoạt khi user gõ `/security-audit`.
> Kiểm tra bảo mật 3 tầng cho codebase-map tool.
> Simplified from HC Security Audit v1.0 (bỏ tenant/JWT/RBAC — không áp dụng cho CLI tool).

---

## 3-TẦNG SECURITY AUDIT

### Tầng 1 — Input Validation & Path Safety (CRITICAL)

```bash
# Scan cho path traversal risks
grep -rn "open\|os.path\|pathlib" codebase_map/ --include="*.py" | grep -v "__pycache__"

# Check YAML config parsing safety
grep -rn "yaml.load\|yaml.unsafe" codebase_map/ --include="*.py"
# Phải dùng yaml.safe_load(), KHÔNG yaml.load()
```

Checklist:
- [ ] YAML config dùng `safe_load()` (không `yaml.load()`)
- [ ] File paths được validate trước khi đọc
- [ ] Không có path traversal vulnerability (../ escape)
- [ ] Config `exclude_patterns` không bị bypass
- [ ] Output paths được sanitize

### Tầng 2 — Dependency & Code Safety

```bash
# Kiểm tra dependencies
pip-audit 2>/dev/null || echo "pip-audit not installed"

# Hardcoded secrets scan
grep -rn "password\|secret\|api_key\|token" codebase_map/ --include="*.py" | grep -v "test_\|example\|#"

# Eval/exec risks
grep -rn "eval\|exec\|__import__\|subprocess" codebase_map/ --include="*.py"
```

Checklist:
- [ ] Không có `eval()` hoặc `exec()` trên user input
- [ ] Không có hardcoded credentials
- [ ] Dependencies không có known vulnerabilities
- [ ] AST parsing dùng `ast.parse()` (safe, không execute code)
- [ ] Không có subprocess calls trên user-controlled input

### Tầng 3 — Output Safety

- [ ] HTML output escape user content (function names, file paths)
- [ ] JSON output không leak system paths ngoài project scope
- [ ] D3.js bundle integrity (không bị tamper)
- [ ] Generated HTML không có XSS vectors từ parsed code

---

## OUTPUT FORMAT

```markdown
## Security Audit Report — Codebase Map

| Tầng | Score | Status |
|------|-------|--------|
| 1. Input & Path Safety | X/35 | PASS/FAIL |
| 2. Dependency & Code | X/35 | PASS/FAIL |
| 3. Output Safety | X/30 | PASS/FAIL |
| **Total** | **X/100** | **PASS/FAIL** |

### Issues Found
| # | Severity | Tầng | Issue | Fix |
|---|----------|------|-------|-----|
| 1 | CRITICAL/HIGH/MEDIUM | 1-3 | ... | ... |
```

---

*security-audit.md v1.0 | Codebase Map | Adapted from HC v1.0 | 06/04/2026*
