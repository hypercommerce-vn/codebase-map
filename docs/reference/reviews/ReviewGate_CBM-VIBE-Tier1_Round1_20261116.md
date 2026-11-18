<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate — CBM-VIBE Tier 1, Rounds 1–2

- Date: 2026-11-16
- Mode: Remote Full (after push + CI)
- Covers one stack of PRs, each built on the one before:

| PR | Branch | Task | Class |
|---|---|---|---|
| [#145](https://github.com/hypercommerce-vn/codebase-map/pull/145) | `feat/cm-s4-01-config-domains` | CM-S4-01 domain overrides + tests | Feature, graph only |
| [#146](https://github.com/hypercommerce-vn/codebase-map/pull/146) | `docs/cbm-vibe-concept` | Concept, design preview v0.1, survey | Docs + design |
| [#147](https://github.com/hypercommerce-vn/codebase-map/pull/147) | `feat/vibe-101-zero-install-core` | VIBE-101 | Feature, config + CLI |
| [#149](https://github.com/hypercommerce-vn/codebase-map/pull/149) | `feat/vibe-102-content-change-detection` | VIBE-102 | Feature, parser + diff |
| [#150](https://github.com/hypercommerce-vn/codebase-map/pull/150) | `feat/vibe-103-feature-store` | VIBE-103 | Feature, graph + CLI |
| [#151](https://github.com/hypercommerce-vn/codebase-map/pull/151) | `feat/vibe-104-cbm-vibe-plugin` | VIBE-104 + review fixes | Feature, plugin + parser |
| [#153](https://github.com/hypercommerce-vn/codebase-map/pull/153) | `docs/vibe-105-install-test` | VIBE-105 guide | Docs |

- No PR changes `html_exporter.py` or any D3 view, so the Designer tier is limited to the design document (#146) and to whether the skill's output follows it (#151).
- The implementer and the gate author are the same agent. To offset that, Tier 2 includes a review by a separate agent that was given the code and not the author's conclusions (section "Independent review").

---

## Tier 1 — TESTER (blocking gates)

| Check | Result |
|---|---|
| Lint, CI-pinned versions (`black==24.10.0`, `isort==5.13.2`, flake8) on `codebase_map/ tests/ scripts/build_cbm_vibe.py plugins/cbm-vibe` | PASS |
| `pytest tests/ -q` at the top of the stack | PASS: 420 passed on Python 3.9.6, 3.11.15, 3.12.13, 3.14.3 (158 on `main` before the stack, 262 new) |
| Same, merged with current `main` (#148, #152, #154 in) | PASS: 436 passed; merge has no conflicts |
| CI on each PR (after the org billing lock was cleared on 15/11) | PASS on all seven: lint, test 3.10 / 3.11 / 3.12, generate, impact, snapshot-impact, notify |
| Self-scan regression, `main`'s scanner vs the stack's, same files | 229 common nodes: id, type, layer and domain **identical** |
| HC regression | **Not run.** The HC checkout was not used in this session. Risk is limited to Python; see CTO section C |
| CLI smoke on the sample app: `generate`, `snapshot-diff` (text / markdown / json), `features status`, `features impact` | PASS, exit 0 |
| HTML output of the sample app in a browser | Opens, no console errors, 53 nodes and 54 edges drawn (checked after VIBE-102; exporter untouched since) |
| Edge: folder with no source files | exit 1 with a reason |
| Edge: explicit config path that does not exist | exit 1, unchanged message |
| Edge: file that is not UTF-8, unbalanced braces, empty file | skipped or parsed without a crash |
| Edge: snapshot written before fingerprints existed | signatures still compared; report says content is not tracked |
| Edge: invalid feature store (10 kinds) | rejected with a reason |
| `claude plugin validate` on the plugin source and the built plugin | PASS, no warnings (Claude Code 2.1.284) |
| Built plugin's bundled tool, macOS Python 3.9.6, isolated mode (`-I`), nothing installed | whole flow passes |

### Acceptance per task

| Task | "Done when" from the approved table | Result |
|---|---|---|
| VIBE-101 | `generate` runs on Python 3.9 without PyYAML, for a Python sample and a TS sample; automated tests | Met |
| VIBE-102 | On the sample app, `lib/reminders.ts` is reported as edited and the two data-access functions are in the graph; automated tests | Met. Before: "0 modified" for the same change |
| VIBE-103 | From before/after snapshots of the sample app: "Booking and Reminders touched" and the list of criteria to recheck | Met: both `direct`, three other features `none`, 5 criteria |
| VIBE-104 | `claude plugin validate` passes; the loop "agree criteria → change report" runs on the sample project | Validate: met. Loop: **met only with a stand-in**, see below |
| VIBE-105 | Table of what works on Chat, Cowork and the Code tab on the owner's machine | **Not met.** Guide and machine checks done; the table needs the owner's hands |

**The stand-in for a real run.** `claude -p --plugin-dir …` on this machine fails with "OAuth session expired". A subagent was given only `SKILL.md` and played Claude with a salon owner on a copy of the sample app, two turns. It agreed criteria before editing, recorded them, snapshotted, edited, snapshotted, ran the impact and wrote the report without claiming anything works. This shows the instructions lead to the intended behaviour. It does not show that Claude picks the skill up unprompted from the user's words.

Tester verdict: **GREEN for #145–#151 and #153 as code and documents; VIBE-105 itself stays open.**

---

## Tier 2 — CTO

### Independent review (16/11)

A separate agent read the new code and was asked for reproduced defects only, with the costly failure defined as *false reassurance*: an edit that can change behaviour after which a dependent feature still shows its evidence as verified. It wrote and ran its own probe scripts and reported 10 such cases, each with the input and the output line. All were real.

| # | Finding | Fix (commit `eab0b16` on #151) |
|---|---|---|
| 1 | A component whose props are on the following lines was not a usage edge | JSX pattern accepts end of line |
| 2 | App in a subfolder, a `tsconfig` alias other than root `@/`, or a Python package below a subfolder: nothing linked | Imports resolve through `tsconfig`/`jsconfig` `paths` and against every folder above the importer; Python targets match by the tail of the node id |
| 3 | Fingerprints ignored whitespace that carries meaning: a Python statement moved out of an `if`, `return` followed by a newline | Fingerprints keep line breaks and in-line text; Python keeps indentation relative to the block |
| 4 | Calls outside a captured function were dropped: `export const POST = withAuth(...)`, an Express inline handler, a class field, a decorator, `ITEMS = seed()` | Class-level calls belong to the class; file-level calls become `files[path].calls` and feed a feature's reach; decorators are edges |
| 5 | A call with type arguments (`getJson<T>(…)`) or an optional call was not an edge | Call pattern extended |
| 6 | `require()` and `import()` created no dependency; `.mjs` / `.cjs` / `.mts` not scanned | Both are import edges; extensions added |
| 7 | `//` inside a template literal or a regular expression cut the line, so a function ended early or swallowed the next one | A code-only view of each line (strings, templates, regexes, comments blanked; state kept across lines) drives all structure |
| 8 | A type declaration's range swallowed the runtime lines after it | Measured on the code-only view; cannot pass the next statement |
| 9 | Names that never resolved: import-then-export without `from`, `export default memo(X)`, a base class in another file | All three resolved |
| 10 | A file saved with a BOM lost its imports (TypeScript) or all its nodes (Python) | One decoder for both parsers and the builder |

Smaller items fixed in the same commit: glob forms (`**/`, `{a,b}`, leading `./`); a file glob no longer matches function names; two unrelated same-named handlers are no longer reported as a rename; long lists say how many entries are left out; a feature store in another encoding gives a clear error; the cache no longer keeps flows removed from the config (a pre-existing bug).

The reproductions are now `tests/codebase_map/test_review_findings.py` (39 tests). Run against the code as it was before the fix, 33 of them fail; the other 6 pin behaviour that already held and must not regress (a type-only edit, a function moved unchanged, a pattern that must not match).

Reported and **not** fixed:

- Two files with the same stem (`lib/util.js` and `lib/util.ts`) share node ids, so an edit in one can be hidden by the other. Rare; needs an id scheme decision.
- `exclusive_hashes` is quadratic in the number of functions per file: 2,000 functions take 0.4 s, 8,000 take 5.9 s. Slow, not a hang.
- Forms that still yield no node (`export default async (req, res) => {`, an object-literal API, a default parameter containing a call). Their calls now count as the file's calls and their text is in the file's top-level hash, so they are covered for reach and for change detection, but they do not appear on the map.

What the reviewer probed that held up: default parameter values, module constants in imported files, code after the last function, class fields, JSX attributes and text, decorator arguments, functions two hops away, default and namespace imports, CRLF files, cache equivalence over edit / delete / add, 3,840 randomly mutated files through the parser with no exception.

### A. Code Logic & Correctness — 22/25

- Round 1 would have scored lower: ten reproduced false-reassurance cases is a correctness failure of the feature's central promise. All ten are closed with tests, which is why this is not a block.
- (-2) The TypeScript parser is still line- and pattern-based. The code-only view removes the worst class of errors, but there is no proof of absence; the next review will find more forms. Known ones are listed in the README.
- (-1) `affected_callers` in `snapshot-diff` still ignores body changes, by design of CBM-P2. A reader of the text report may expect otherwise; the feature layer is where body changes are mapped.

### B. Architecture & Structure — 19/25

- Separation holds: parsers produce nodes and edges, the builder resolves, `snapshot_diff` compares, `features` maps, the CLI only prints. The plugin calls the CLI and keeps no second copy of the package in the repository.
- (-3) File size against the 300-line guideline: `typescript_parser.py` is 1,225 lines, `features.py` 862, `builder.py` 734, `cli.py` 1,140 (870 before the stack). The parser should be split into lexing, scope tracking and imports.
- (-2) `_resolve_typescript_calls` and `_TsImportResolver` live in `builder.py`; language-specific resolution belongs with the parser.
- (-1) `exclusive_hashes` is O(n²) per file.

### C. Parser Accuracy & Graph Integrity — 22/25 (AUTO-BLOCK gate: needs ≥ 20)

- On this repository's own source, ids, types, layers and domains of all 229 common nodes are identical to `main`'s scanner.
- TypeScript: on the sample app 45 of 140 call edges point at a project function and none that should resolve is left unresolved (reviewer's check). Before the stack: 0 of them, and two functions missing.
- Python: new edges only (relative imports, decorators, class bodies, tail matching). No existing edge is removed.
- (-2) HC regression was not run, so the Python changes are verified on this repository and on small fixtures only.
- (-1) False positives introduced on purpose: a call edge for a nested function it may never call, `a<b>(c)` read as a call with type arguments, a tail match that can hit a same-named external module. Each errs towards asking for a recheck.

### D. Output Quality — 14/15

- JSON reports are valid and stable (sorted); `--json` prints nothing else on stdout; the HTML map opens.
- (-1) The API Catalog tab still shows 0 for a Next.js app: route handlers are not marked as routes in the graph. The `features status` output does list them as endpoints.

### E. Production Readiness — 9/10

- Lint and CI green on every PR; output is UTF-8 on every platform; cache version bumped twice with a reason each time.
- (-1) Not run on Windows. The UTF-8 and BOM fixes target it, but nothing was executed there.

**CTO score: 86/100.** Dimension C is above the block threshold.

---

## Tier 3 — DESIGNER

Scope: the design document in #146 and whether the skill follows it. No HTML or D3 output changed.

| Item | Result |
|---|---|
| Design preview v0.1 (`CBM-VIBE-Design-Preview.html`) | Approved by the CEO on 13/11/2026 |
| Report layout in the skill | **Round 1: did not match.** The skill used its own section names and had no verdict line |
| Fix (commit `ba392c0` on #151) | Section names, their order, the three-level verdict line and the three "where this reaches" lines now follow the preview; tests tie the names and the order to the preview file |
| "Where this reaches" computed, not guessed | `features status` lists, per feature, the features that depend on it (`affects`); the skill uses it |
| Plain-language rules (no file names, no percentages by default) | In the skill; held in both stand-in turns |
| Buttons in the preview ("Đúng rồi, làm đi", "Đạt / Không đạt") | Tier 1 is text in the conversation; the skill asks in words. Buttons are tier 3 |

Designer score for the matched scope: **92/100** (-8: buttons and the visual states of the preview are not reproducible in chat text; the "application map" moment has no automated check against the preview).

---

## Score and verdict

Final = CTO × 0.6 + Designer × 0.4 = 86 × 0.6 + 92 × 0.4 = **88.4**

This is below the 90 that the gate asks for, and it is reported as such rather than rounded up. What stands between this score and a higher one is not a known defect:

1. **File size and placement** (B): a refactor of the TypeScript parser, best done as its own PR with no behaviour change.
2. **HC regression and a Windows run** (C, E): need the HC checkout and a Windows machine.
3. **A run in Claude itself** (VIBE-104 acceptance, VIBE-105): needs the owner to log in and install.

**Verdict: no known false-reassurance case remains open; SHIPIT is the owner's call with the three notes above.** A third round after items 2 and 3 would settle the score.

## Merge order

`#145 → #146 → #147 → #149 → #150 → #151 → #153`, or #151 alone and then #153. PRs #156 and #157 (CBM Mod, another session) also change `codebase_map/cli.py` and `project/board.html`; whichever stack merges second has to be rebased.

## Addendum — 18/11/2026, after `main` took VIBE-106

This section records what changed after the rounds above. It replaces the merge order and corrects one sentence of the verdict.

**Merge with `main`.** VIBE-106 (CBM Mod) was merged into `main` on 16/11 and touched `codebase_map/cli.py`, the README and the board. #151 now contains `main` up to #168. The one hand-resolved file, `cli.py`, keeps both sides: `build_parser()` with the `features` group, and the `mod` group with `_cmd_mod`. On the merged tree: pinned black, isort and flake8 are clean, 554 tests pass on Python 3.9.6, 3.11.15, 3.12.13 and 3.14.3, and CI is green on #151.

**Finding 11 — fixed.** The skill pre-approves `python3 …/scripts/cbm.py *`. The runner passed every argument through and the build copied the whole package, so after the merge the pre-approved command could start the pane's web server and install a git post-commit hook, and the plugin archive carried that code. Older commands had the same shape on a smaller scale (`check-staleness --notify` posts to Telegram, `api-catalog -o` writes to any path, `snapshots clean` deletes snapshots). The runner now parses the command line with the tool's own parser and runs only `generate`, `features`, `query`, `impact`, `summary`, `search`, `snapshot-diff` and `snapshots list`; the build leaves `codebase_map/mod` out. A test fails when the CLI gains a command that is in neither the allowed nor the refused set. With the previous runner and build script, 29 of the 62 plugin tests fail.

**Second stand-in run, with the final skill.** A subagent played Claude through the three moments on a fresh copy of the sample app. Turn 1 stopped for agreement with four criteria and the three "reaches" lines; turn 2 produced the approved layout (verdict line, three questions, "Tự kiểm trong 1 phút") with all four criteria "Chưa kiểm" and no evidence recorded; turn 3 listed six features with counts per state. Re-running `features impact` on that project gave the same picture as the report. The run still does not show whether Claude triggers the skill from a user's words.

**What the debrief exposed — fixed in #151.**

| Gap | Fix |
|---|---|
| An endpoint called by screens of two features was listed in one feature only | SKILL.md: list it in both. A test pins the gap and the remedy |
| The agent read `module_level_changed: false` on a shared file as "behaviour unchanged" | `unowned_changes[]` now carries `behaviour_changed`; the skill allows that sentence only when it is `false` |
| Commands kept in a shell variable and piped, which would not match the pre-approved command | SKILL.md: one full command per call |
| The count in "AI đã làm gì" was undefined | SKILL.md defines it |

The three turns ran before these four fixes; the run was not repeated afterwards.

**Correction to the verdict.** "No known false-reassurance case remains open" no longer holds as written. One path is known and open: the tool does not follow `fetch("/api/…")`. If an endpoint file is listed in only one of the features whose screens call it, an edit behind the endpoint leaves the other feature's evidence at "verified". Reproduced on the trial project: the criterion stayed `verified`; with the endpoint file added to the second feature it became `needs_recheck`. This is mitigated by an instruction, not by the tool. Following fetch URLs to route files is the first thing to build in tier 2.

**Score.** Not re-computed. The three notes above stand, and the open path in the previous paragraph is a fourth.

**Outside this stack.** `tests/codebase_map/test_mod_server.py::TestEndpoints::test_status` (VIBE-106) timed out once on CI (Python 3.10, #153): it allows 3 seconds for a request whose handler calls `gh` over the network. It passed on re-run.

**Merge order, replacing the section above.** #151 first, with a merge commit as for earlier PRs; #145, #146, #147, #149 and #150 are contained in it and GitHub marks them merged. #147, #149 and #150 on their own conflict with `main` in `codebase_map/cli.py`. Then #153, #166, #167.
