<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate — PR #155 Round 1

- Date: 2026-11-16
- Mode: Remote Full (after push + CI)
- Branch: `claude/epic-yonath-a6064b` → `main`, reviewed head `cd8721a` (+ board commit `b77c4b0`)
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/155
- Title: fix(exporter): show real version, singular stat labels, hide empty Flows row
- Scope: exporter bugs found on the website `/demo/` map by the PR #152 review gate (CBM-WEB, "Tách ra làm ticket riêng").
- Files: `codebase_map/exporters/html_exporter.py`, `tests/codebase_map/test_html_exporter_header.py` (new), `docs/active/map-demo-fixes/Proposal_Map_Layout_and_Package_Domains.md` (new, proposal only), `project/board.html`, `BRIEF.md`, `docs/README.md`
- PR class: **Bug fix with HTML change** → Tester verify + CTO A+C+E + Designer C+D.
- Reviewers: CTO and Designer ran as independent agents with the diff and the rubric, not the author's conclusions.

---

## Tier 1 — TESTER (blocking gates)

| Check | Result |
|---|---|
| Lint, CI-pinned (`black==24.10.0 --target-version py310`, `isort==5.13.2 --profile black`, flake8) on `codebase_map/ tests/` | PASS |
| `pytest tests/ -q` | PASS: 180 passed (174 + 6 new) |
| CI on `cd8721a` | PASS 9/9 (reported by CTO) |
| Bugs reproduced on `main` (browser, 1094×800) | badge `v2.0`; "1 domains"; empty "🧭 Flows:" row, because `.flow-bar { display:flex }` overrides `[hidden]` |
| Fix verified (browser) | badge `v2.4.0`; "200 nodes · 165 edges · 1 domain"; Flows row `display:none`, breadcrumb moves up 28 px |
| Flows bar still shows when flows exist | 3-node graph with flows: bar `display:flex`, chips `checkout 2`, `signup 1` |
| Mutation check | 4 of the 6 new tests fail on main's exporter. The other 2 are guards. |
| Self-scan regression: same source (main HEAD) scanned with old and new code | 200 nodes / 992 edges both ways; `graph.json` identical |
| HC regression (`HyperCommerce/backend` + `frontend/src`): old vs new code | 1624 nodes / 9989 edges / 11 domains both ways; `graph.json` identical (scan output went to the scratchpad, the HC repo was not touched) |
| Self-scan of this branch | 200 nodes / 993 edges. The +1 edge is the new `from codebase_map import __version__` import in the scanned source itself. |
| Website build (`website/build.py`) | demo shows `v2.4.0` and carries both fixes |

Tester verdict: **GREEN**.

---

## Tier 2 — CTO (bug-fix scope: A + C + E = 60 pts)

### A. Code Logic & Correctness — 22/25
- All three fixes are correct in a real browser. Importing `__version__` is safe: the module only defines a string, and builder/cli already import it. f-string braces are correct.
- `.flow-bar[hidden]` (specificity 0,2,0) beats `.flow-bar` (0,1,0). The bar still shows when flows exist.
- (-3) **should-fix:** the same plural bug is still in 7 other strings on the page: "1 routes", "1 nodes", "1 layers", "1 results", "1 dependencies", "1 dependents", "1 edges" (lines 757, 915, 927, 932-933, 1253, 1539-1541). The detail panel and search count show these on the demo all the time: 33 self-scan nodes have exactly 1 dependency and 94 have exactly 1 dependent. Two of the six new tests also pass on the old code.

### C. Parser Accuracy & Graph Integrity — 25/25 (AUTO-BLOCK gate cleared)
- From fresh `git archive` copies with `--no-cache`: old and new code give byte-identical nodes and edges on the same source. The only branch difference is one legitimate `imports` edge plus 3 nodes shifted by one line.

### E. Production Readiness — 10/10
- Lint clean, 180/180 tests, CI 9/9, no unused imports, `HC-AI` markers present.

Nits:
- The tests assert on JS source text (`statLabel(nodes.length, 'node')`), so a harmless rename would break them. The Node behaviour test is the one that matters.
- The `634a7bb` message gives 992 edges, which is the same-source comparison; the branch self-scan is 993.
- The board commit was not pushed yet.

Proposal doc: 13 claims confirmed. Inaccurate or incomplete:
- (a) Vertical numbers were measured with the empty Flows row still showing.
- (b) The 1094 px overlaps are 272/110 px, not 280/118.
- (c) The TS `_infer_domain` is "similar", not "the same".
- (d) **No rule for sources without `base_module`.** VIBE zero-config uses `SourceConfig(path=".")` with no `base_module`, so the proposal would do nothing for vibecoding users.
- (e) #147 does not touch the parser, and the VIBE stack already contains #145.
- (f) 992 vs 993 edges.

**CTO total: 57/60 → 95.0 / 100**

---

## Tier 3 — DESIGNER (bug-fix scope: C + D = 40 pts)

Checked in the browser at 1440×900, 1094×800, 820×800 and 375×812. Old and new HTML were compared for 0-, 1-, 2- and 30-node graphs; the 30-node graph has flows and 3 domains.

### C. Interactive Elements — 20/20
- Node click/hover, zoom/pan, Fit, search, filters, flow chip toggling (9 lit / 21 dimmed, then restored), minimap and toolbar all behave the same as on main.

### D. Data Display — 19/20
- Header correct for all graph sizes: "0 nodes / 0 edges / 0 domains", "1 node / 0 edges / 1 domain", "2 nodes / 1 edge / 1 domain", "30 nodes / 29 edges / 3 domains".
- Badge grows from 34 to 44 px with the same font, padding, radius and colours, and the 12 px spacing between badges is kept.
- With no flows, the canvas gains 28 px. With flows, chip positions are pixel-identical to main.
- (-1) **should-fix S1:** the same grammar bug is in other labels on the page (e.g. "1 results", "Calls 1 dependencies"), next to a header that is now correct.

**Designer total: 39/40 → 97.5 / 100**

Nits, all already on main (follow-ups):
- N1: flow chips have no gap between them.
- N2: flow chips cannot be reached with the keyboard.
- N3: the version badge has low contrast (~1.8:1, design token).
- N4: auto-fit runs on a fixed 3 s timer and can leave the canvas empty in a background tab.
- N5: the flow bar shows on non-graph tabs.

Proposal §4: agrees with option A, and lists 8 amendments (legend groups wrap; toolbar/minimap overlap at 769–837 px; panel back to the design's z 20; max-height floor; topbar stats hidden ≤768 px per design; Fit leaves room for overlays; 820 px added to the screenshot set). It also corrects the doc: the minimap covering the panel is **drift from the approved design**, not a design gap.

---

## Tier 4 — Impact Analysis (`codebase-map diff origin/main --json`)

| Metric | Value |
|---|---|
| Changed files | 2 (`html_exporter.py`, new test file) |
| Changed nodes | 3. `_build_html` is the real change; `_load_d3_bundle` and `export_html` only moved down one line because of the new import. |
| Impact zone | 2 (`cli._cmd_generate`, `cli.main`) |
| Risk level | 🟢 Low |

---

## Score

```
Final = CTO × 0.6 + Designer × 0.4 = 95.0 × 0.6 + 97.5 × 0.4 = 96.0
```

- Tester GREEN · CTO dim C 25/25 (no auto-block)
- Verdict: **SHIPIT + NOTE** (no blockers). Both reviewers independently raised the same should-fix (remaining plurals), so it was fixed before CEO review, along with the proposal corrections. See Round 2.

## Applied after Round 1
- `87b39fb` fix(exporter): `plural(count, noun, many)` helper behind `statLabel` and all 9 count labels; a parametrized test per old hardcoded label; the Node test covers the irregular "dependency" plural. 188 tests pass. Of the 14 tests in the file, 12 fail on main's exporter and 9 fail on `634a7bb`. Browser on the self-scan: "1 result", "1 dependency", "1 dependent", "2 edges".
- `d1e0c9c` docs(proposal): corrections (a)–(f) and the Designer's §4 amendments; rule 3 now defines the no-`base_module` case (path relative to `sources[].path`).
- Found while verifying: `translate(NaN,NaN)` console errors after switching tabs happen on main too (same 15 errors). Recorded as a follow-up together with N4.
