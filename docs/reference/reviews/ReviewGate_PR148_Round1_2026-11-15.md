<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate — PR #148 Round 1

- Date: 2026-11-15
- Mode: Remote Full (after push + CI)
- Branch: `claude/sleepy-kare-6ceeae` → `main`
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/148
- Title: fix(parser): only match full-line `# flow:` annotation comments
- Scope: CM-S3-04 business-flow annotations. Bug found while building the website demo (CBM-WEB): fake flow chips "name1, name2" on CBM's map of its own source.
- Files touched: `codebase_map/parsers/python_parser.py` (1 regex + 2 comment lines), `tests/codebase_map/test_python_parser_flows.py` (new)
- PR class: **Bug fix (parser only)** → Tester verify fix + CTO A+C+E. Designer skipped (no HTML/D3 change).

---

## Tier 1 — TESTER (blocking gates)

| Check | Result |
|---|---|
| Lint, CI-pinned versions (`black==24.10.0`, `isort==5.13.2`, flake8) on `codebase_map/ tests/` | PASS |
| `pytest tests/ -q` | PASS: 174 passed (158 before this PR + 16 new) |
| CI on PR (attempt 4, after the org billing lock was cleared) | PASS 8/8: lint, test 3.10 / 3.11 / 3.12, generate, impact, snapshot-impact, notify |
| Bug reproduced on `main` | `_extract_flow_annotations` tagged with flows `['name1', 'name2']` |
| Fix verified on branch | 0 nodes tagged with flows; `name1` appears 0 times in `index.html` |
| Self-scan regression, `main` vs branch | Nodes 200 = 200, edges 992 = 992, node ids and edge set **identical**. The only change is the removed fake flows. |
| HC regression (`HyperCommerce/backend`, 357 files) | 3060 nodes old = new. HC has 0 `# flow:` comments, so the HC map cannot change. |
| CLI smoke: `summary` / `search` / `query` / `impact` | PASS (exit 0, expected output) |
| Edge: file with syntax error | skipped, 0 nodes, no crash |
| Edge: empty file | 0 nodes, no crash |
| Edge: `# flow:` with nothing after it, or only commas | node parsed, no flows, no crash |
| Real annotations still work | `# flow: signup, crm-sync` above a class; indented `# flow: checkout` above a method; `#flow:checkout`; `# Flow : Onboarding_v2` |
| Prose no longer matches | CM-S3-04 doc comment, `# see the flow: ...`, `# workflow: ci`, `# flowchart: a, b`, docstring quoting `# flow:`, trailing `x = 1  # flow: checkout` |

### Mutation test (are the tests protective?)
The old regex was put back temporarily and the new test file run against it:

- **Before the round-1 fix:** 6 tests failed (good), but both self-scan tests **passed**. The two added comment lines push the CM-S3-04 doc comment 6 lines above `_extract_flow_annotations`, outside the 5-line lookup window, so the node-level self-scan checks were position-dependent and did not guard the regex.
- **Fixed in this round:** added `test_self_source_has_no_annotation_lines`, which checks every `codebase_map/*.py` file at line level, independent of line positions. The old regex matches 4 lines in CBM's own source: the CM-S3-04 comment, a docstring, `cli.py:40` ("one-command flow: after ..."), and a CSS line in `html_exporter.py:125` (`overflow: hidden` → flow `hidden`).
- **After:** 7 tests fail against the old regex, including the new self-scan check. The source file was restored afterwards (`git checkout`).

Tester verdict: **GREEN**.

---

## Tier 2 — CTO (bug-fix scope: A + C + E = 60 pts)

### A. Code Logic & Correctness — 24/25
- New pattern `^\s*#\s*flow\s*:\s*([A-Za-z0-9_,\-\s]+)` (IGNORECASE): the line must *be* the comment and the comment must *start* with `flow:`. Matches the documented form (ONBOARDING.md §6, full-line comment above def/class).
- A narrower "`#` then `flow:`" rule searched anywhere in the line would **not** have fixed the bug: the doc comment quotes `` `# flow: name1, name2` `` in backticks. Full-line anchoring is required.
- `flow\s*:` stops `flowchart:` matching; `^\s*#\s*flow` stops `workflow:` matching. Both were false positives before.
- Behaviour change: a comment after code (`x = 1  # flow: a`) is no longer an annotation. It was never documented or tested, and the PR body calls the change out.
- (-1) Pre-existing, not introduced: a line *inside a multi-line string* that starts with `# flow:` still matches, because detection is line-based. A complete fix would read only real comment tokens (`tokenize`). Non-blocking follow-up.

### C. Parser Accuracy & Graph Integrity — 25/25 (AUTO-BLOCK gate cleared)
- Node ids and the edge set are identical to `main` on the self-scan; HC node count is unchanged.
- `_FLOW_PATTERN` only feeds `metadata["flows"]`, so call graph, layers and domains cannot change by construction, and the regression run confirms it.
- Metadata accuracy improves: the only fake flow annotation in the self-scan is removed.

### E. Production Readiness — 10/10
- Lint PASS with CI-pinned versions; CI 8/8 green on Python 3.10 / 3.11 / 3.12.
- No dead code or unused imports.
- `# HC-AI | ticket: FDD-TOOL-CODEMAP` on the changed parser block and the new test module.

**CTO total: 59/60 → 98.3 / 100**

---

## Tier 3 — DESIGNER

Skipped (bug-fix class, no HTML/D3 change). Checked by reading the code: `#flow-bar` is rendered with the `hidden` attribute and stays hidden when no node has flows (`html_exporter.py:1016`). The detail panel shows a Flows row only when present (`html_exporter.py:1554`). After this fix, CBM's self-scan (and the website `/demo/` page built from it) shows no Flows bar instead of the fake "name1, name2" chips. A browser check was attempted but the pane could not open local files in this session.

---

## Tier 4 — Impact Analysis (`codebase-map diff origin/main --json`)

| Metric | Value |
|---|---|
| Changed files | 2 (`python_parser.py`, new test file) |
| Changed nodes (as reported) | 20 |
| Impact zone | **0** |
| Risk level | 🟢 Low |

The 20 "changed nodes" are every function in `python_parser.py` below line 43, flagged because the 2 added comment lines shift their positions by 2. The only semantic change is the module-level `_FLOW_PATTERN` constant, whose single consumer is `_extract_flow_annotations` → `PythonParser.parse_file` (impact: 1 caller).

---

## Final Score

```
Final = CTO score (Designer skipped, no HTML changes)
      = 98.3
```

- CTO dim C = 25 (≥ 20, no auto-block)
- Tester: GREEN
- Final: **98.3 / 100**
- Threshold: ≥ 95 → **SHIPIT** (same threshold as PR #39)

## Verdict: SHIPIT

## Follow-ups (non-blocking)

1. Detect flow annotations from real comment tokens (`tokenize`) instead of lines, so text inside multi-line strings can never match.
2. `_FDD_PATTERN` is unanchored on purpose (`# HC-AI | ticket: FDD-...` needs mid-comment matching). The CM-S2-08 doc comment quoting `# FDD: FDD-XXX-NNN` also matches it, but sits 6 lines above the next def, outside the 5-line window, so nothing shows today. Same position-dependence risk.
3. Board: the CBM-WEB card tracking this bug lives on `feat/cbm-website`; its status line is updated there (not in this PR).

## Recommendation to CEO

**Approve & merge PR #148.** One-line regex fix, HC and self-scan graphs unchanged apart from removing the fake flows, CI green on all three Python versions. After merge, the next website build drops the fake "name1, name2" chips from `/demo/` automatically.
