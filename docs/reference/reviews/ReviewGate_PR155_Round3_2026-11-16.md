<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate — PR #155 Round 3 (final)

- Date: 2026-11-16
- Mode: Remote Full, CTO confirmation after the Round 2 fixes and the merge of `origin/main`
- Reviewed head: `a008efc`. Since Round 2: `e17dcbf` (last two plural labels), `24d97d8` (proposal figures), `a0888a2` (merge of #154, docs-only conflicts), `a008efc` (reports)
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/155
- Designer: Round 2 gave 40/40, and nothing in its scope changed except the two labels it had flagged. The CTO checked both in the browser ("LOC 1 line", "found 1 node"), so the Designer score carries over.

---

## Tier 1 — TESTER

| Check | Result |
|---|---|
| CI on `a008efc` | **PASS 9/9**: generate, impact, lint, notify, snapshot-impact, test 3.10 / 3.11 / 3.12, website |
| Mergeability | MERGEABLE (`mergeStateStatus` CLEAN) |
| `pytest tests/ -q` | 190 passed |
| Lint (CI-pinned) | PASS |
| Mutation check | with the `d1e0c9c` exporter, 3 tests fail: the two new label cases and `test_helpers_pluralize` |

## Tier 2 — CTO: 60/60 → 100 / 100

- **A. 25/25.** Every count label goes through `plural()`, `statLabel()` or `countLabel()`, including strings built with `+`. The only count text left is invariant: "cls", "fn", and the diff legend words.
- **C. 25/25.** Self-scan with `--no-cache`: 200 nodes / 993 edges, with no edge change since Round 2. The only node change is `_build_html.line_end`, because the template grew by 3 lines. The parser is untouched.
- **E. 10/10.** Lint clean, no unused imports, `HC-AI` marker present, CI 9/9.
- **Merge `a0888a2`** is resolved correctly: no conflict markers, and all of #154's content is kept. The only line from main that was replaced is the split-out header ("đang xử lý ở phiên riêng"); it now links PR #155. The scores shown on the board match the reports.
- **Nits (docs only), applied after this round:**
  - The board card said the self-scan has 992 edges; it now explains 992 for the same source vs 993 on this branch.
  - The proposal's 1440 px panel/minimap figure is now 0–~102 px.

## Tier 3 — DESIGNER: 40/40 → 100 / 100 (Round 2, carried over)

## Tier 4 — Impact Analysis
Unchanged from Round 1: 🟢 Low. The only code file is `html_exporter.py`; the impact zone is `cli._cmd_generate` and `cli.main`.

---

## Score

```
Final = CTO × 0.6 + Designer × 0.4 = 100 × 0.6 + 100 × 0.4 = 100
```

| Round | CTO | Designer | Final | Status |
|---|---|---|---|---|
| 1 | 95.0 | 97.5 | 96.0 | SHIPIT + NOTE (should-fix: remaining plurals) |
| 2 | 93.3 | 100 | 96.0 | blocked by process (conflict with #154, no CI) |
| 3 | 100 | 100 | **100** | **SHIPIT** |

## Verdict: SHIPIT

## Recommendation to CEO
- **Approve and merge PR #155.**
  - It fixes the version badge, all singular/plural labels and the empty Flows row on the map and the website `/demo/` page.
  - Graph output is identical for the same source, on CBM and on Hyper Commerce.
  - CI passes 9/9.
- **Separate decisions, no code yet:** see `docs/active/map-demo-fixes/Proposal_Map_Layout_and_Package_Domains.md`.
  - §4 canvas layout: option A is recommended. It needs a design update first.
  - §5 package-based domains: questions Q5a–c, to be done after #145 and the VIBE stack.

## Follow-ups (already on main, not in this PR)
1. Auto-fit runs on a fixed 3 s timer. When the graph is hidden (another tab, or a background browser tab) it leaves the canvas empty or logs `translate(NaN,NaN)`. This matters for `/demo/`.
2. Flow chips have a 0 px gap between them and can't be reached with the keyboard (`<span>` instead of `<button aria-pressed>`).
3. The version badge contrast is about 1.8:1 (design token).
4. The Flows row and breadcrumb show on the Executive, API and Diff tabs.
5. `project_name` goes into `<title>` without escaping.
6. The header edge badge (165, edges inside the graph) differs from the CLI/JSON total (992/993).
