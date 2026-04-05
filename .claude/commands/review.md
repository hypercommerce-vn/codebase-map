# /review — Codebase Map Code Review

# HC-AI | ticket: FDD-TOOL-CODEMAP

> Slash command kích hoạt khi user gõ `/review` hoặc cần review code.
> 5 dimensions review, mỗi dimension 20 điểm, tổng 100.
> Adapted from HC Review v1.0.

---

## 5-DIMENSION CODE REVIEW

### Dimension 1 — Correctness (20 điểm)

- [ ] (5) Parser logic đúng — extract đủ functions, classes, methods, decorators
- [ ] (5) Edge cases handled (empty files, syntax errors, encoding issues)
- [ ] (5) Error handling đúng pattern (try/except, logging, graceful skip)
- [ ] (5) Graph builder output nhất quán (nodes + edges match parser output)

### Dimension 2 — Architecture (20 điểm)

- [ ] (5) Layer separation đúng: Parser → Graph → Exporter → CLI
- [ ] (5) DRY — không duplicate code > 10 dòng
- [ ] (5) BaseParser interface được tuân thủ (cho future TS parser)
- [ ] (5) Config schema đúng YAML spec

### Dimension 3 — Accuracy (20 điểm)

- [ ] (7) Node count chính xác — không thiếu, không thừa
- [ ] (5) Edge (call graph) chính xác — false positive < 5%
- [ ] (5) Layer classification đúng (route/service/model/util/schema/test)
- [ ] (3) Metadata đầy đủ (file path, line number, node type)

### Dimension 4 — Output Quality (20 điểm)

- [ ] (5) JSON output valid, schema consistent
- [ ] (5) HTML render đúng (D3.js graph, colors, interactions)
- [ ] (5) CLI output helpful (summary stats, search results formatted)
- [ ] (5) Design match 100% với design-preview/ (nếu có FE changes)

### Dimension 5 — Production Readiness (20 điểm)

- [ ] (5) Lint pass: black + isort + flake8
- [ ] (5) No dead code, unused imports
- [ ] (5) CI workflow pass (lint + self-test)
- [ ] (5) Comment `# HC-AI | ticket: FDD-TOOL-CODEMAP`

---

## SCORING

| Score | Verdict |
|-------|---------|
| 95-100 | ✅ SHIPIT |
| 85-94 | ⚠️ Minor issues — fix rồi merge |
| 70-84 | 🔄 Revise — fix rồi review lại |
| < 70 | ❌ Reject — rework |

---

*review.md v1.0 | Codebase Map | Adapted from HC v1.0 | 06/04/2026*
