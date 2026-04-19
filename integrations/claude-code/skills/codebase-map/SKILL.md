---
name: codebase-map
description: >
  Use this skill when the user wants to understand a Python or TypeScript
  codebase, find where a function is called from, analyze PR impact, generate
  an API catalog, or compare code snapshots before/after a refactor.
  Triggers: "impact", "callers", "who calls", "dependency graph", "onboard
  this repo", "what breaks if I change X", "blast radius", "API endpoints in
  this project", "diff vs main", "before/after refactor", "is this safe to
  delete".
---

# Codebase Map Skill

You have access to `codebase-map` CLI (v2.2+). It parses Python and TypeScript
source files and builds a function/class dependency graph you can query.
Useful for onboarding a new repo, answering "who calls X", sizing a refactor
blast radius, generating an API catalog, and producing before/after diffs for
PR bodies.

## Prerequisite check

Before running any CBM command in a session, verify install:

```bash
codebase-map --version
```

If the command is not found, tell the user to install it:

```bash
pipx install codebase-map
```

If `pipx` itself is not available, `pip install codebase-map` works too.

## Workflow for a new repo

Follow these steps the first time you touch an unfamiliar repo.

### 1. Check for `codebase-map.yaml`

```bash
ls codebase-map.yaml 2>/dev/null || echo "MISSING"
```

If the file is missing, inspect the repo to decide Python vs TypeScript:

```bash
ls -la
# look for pyproject.toml, requirements.txt → Python
# look for package.json, tsconfig.json → TypeScript
```

### 2. Create a default config if missing

**Python project:**

```yaml
project: "my-project"
sources:
  - path: "src"
    language: python
    base_module: "src"
    exclude:
      - "__pycache__"
      - "migrations"
      - ".venv"
      - "tests"
output:
  dir: "docs/function-map"
  formats: [json, html]
graph:
  depth: 3
  group_by: module
```

**TypeScript project:**

```yaml
project: "my-project"
sources:
  - path: "src"
    language: typescript
    exclude:
      - "node_modules"
      - "dist"
      - "build"
output:
  dir: "docs/function-map"
  formats: [json, html]
graph:
  depth: 3
  group_by: module
```

Adjust `path` and `base_module` to match the actual source directory.

### 3. Generate the graph

```bash
codebase-map generate -c codebase-map.yaml
```

This writes `graph.json` and `index.html` to the output directory
(`docs/function-map/` by default).

### 4. Always start with `summary`

```bash
codebase-map summary -f docs/function-map/graph.json
```

Gives node/edge/domain counts in under a second. Always run this first when
onboarding — it tells you the shape of the codebase before you query.

## Command reference

All commands accept `-f PATH` to point at a specific `graph.json` (default is
`docs/function-map/graph.json`).

| Command | Purpose | Example |
|---------|---------|---------|
| `summary` | Node/edge/domain overview | `codebase-map summary -f graph.json` |
| `query` | Details for one function or class | `codebase-map query "CustomerService.create" -f graph.json` |
| `impact` | Blast radius (who breaks if X changes) | `codebase-map impact "process_payment" -f graph.json --depth 2` |
| `search` | Fuzzy keyword search | `codebase-map search "pipeline" -f graph.json` |
| `api-catalog` | HTTP route list | `codebase-map api-catalog -f graph.json --format text` |
| `diff` | Git-diff impact (branch vs ref) | `codebase-map diff main -f graph.json --depth 2` |
| `coverage` | Overlay pytest-cov on graph | `codebase-map coverage coverage.json -f graph.json` |
| `check-staleness` | Warn if graph.json is old | `codebase-map check-staleness -f graph.json` |
| `snapshots list` | List labeled snapshots | `codebase-map snapshots list` |
| `snapshot-diff` | Diff two labeled snapshots | `codebase-map snapshot-diff --baseline baseline --current post-dev --format markdown` |
| `generate --label NAME` | Save a labeled snapshot | `codebase-map generate --label baseline` |
| `generate --diff REF` | Bake PR Diff view into HTML | `codebase-map generate --diff main` |

Useful flags:

- `query` and `impact` accept `--depth N` (default 3).
- `api-catalog` accepts `--format {text,json,html}`, `--method`, `--domain`, `--path`.
- `diff` accepts `--json`, `--depth N`, `--record-metric PR_NUMBER`.
- `snapshot-diff` accepts `--depth {1,2,3}`, `--breaking-only`, `--test-plan`, `--format {text,markdown,json}`.

## Dual-snapshot diff (before/after a refactor)

Use this when the user wants a PR body section summarising what the refactor
changed.

```bash
# 1. Before starting work — on the base branch
codebase-map generate --label baseline

# 2. Make code changes on the feature branch

# 3. After work is done
codebase-map generate --label post-dev

# 4. Diff
codebase-map snapshot-diff \
    --baseline baseline \
    --current post-dev \
    --format markdown \
    --test-plan
```

Paste the markdown output into the PR body. Add `--breaking-only` to focus
only on signatures that grew affected callers, and `--depth 2` to widen the
caller reach in the report.

## Rules

- **Always run `summary` first** when onboarding an unfamiliar repo. It is
  the cheapest sanity check and tells you scale before you query.
- **Impact depth defaults**: use `--depth 1` for a quick local check, the
  default `3` for exploratory questions, `--depth 2` as the sweet spot for PR
  review discussions.
- **Staleness**: if `graph.json` is older than 7 days (check with
  `codebase-map check-staleness -f graph.json`), regenerate before querying.
  Answers from a stale graph are misleading.
- **TypeScript repos**: the config must set `language: typescript` on the
  source entry. The TS parser is v2.0+ only; older CBM versions silently
  skip `.ts` files.
- **PR workflow**: generate the labeled `baseline` snapshot BEFORE starting
  any refactor, then the `post-dev` snapshot AFTER, then diff. Doing this
  mid-refactor loses the baseline.
- **Quote names that contain spaces or special chars** when passing to
  `query`, `impact`, or `search`.

## When not to use

- User just wants to read a single file — use the Read tool directly.
- The repo is tiny (fewer than ~10 source files) — `grep` is faster than
  `generate`. CBM pays off on repos with hundreds+ functions.
- User is asking about the CBM tool itself (how it works, roadmap, config
  schema) — answer from this skill's knowledge rather than running commands.
- Repo is not Python or TypeScript. Java and JavaScript parsers are on the
  roadmap (v2.4). For other languages, tell the user and stop.
