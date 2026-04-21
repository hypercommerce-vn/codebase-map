---
name: cbm-onboard
description: Generate the codebase map for this repo and give me an onboarding summary.
---

Onboard this repo using `codebase-map`. Do not auto-open anything in the browser — the user decides.

## Steps

1. **Verify install.** Run `codebase-map --version`. If not found, tell the user `pipx install codebase-map` and stop.

2. **Check config.** See if `codebase-map.yaml` exists at the repo root:

   ```bash
   ls codebase-map.yaml 2>/dev/null || echo "MISSING"
   ```

   If missing, inspect the repo with `ls -la` and detect the stack:
   - `pyproject.toml` or `requirements.txt` → Python
   - `tsconfig.json` or `package.json` → TypeScript

   Then write a default `codebase-map.yaml`. Adjust `path` and `base_module` to match the real source directory.

   **Python template:**
   ```yaml
   project: "<repo-name>"
   sources:
     - path: "src"
       language: python
       base_module: "src"
       exclude: ["__pycache__", "migrations", ".venv", "tests"]
   output:
     dir: "docs/function-map"
     formats: [json, html]
   graph:
     depth: 3
     group_by: module
   ```

   **TypeScript template:** same shape with `language: typescript` and `exclude: ["node_modules", "dist", "build"]` (no `base_module`).

3. **Generate the graph:**

   ```bash
   codebase-map generate -c codebase-map.yaml
   ```

4. **Summary pass:**

   ```bash
   codebase-map summary -f docs/function-map/graph.json
   ```

5. **API catalog (trim to keep output tight):**

   ```bash
   codebase-map api-catalog -f docs/function-map/graph.json --format text | head -30
   ```

6. **HTML path.** Tell the user: *"Interactive graph at `docs/function-map/index.html` — open in a browser when you want to explore visually."* Do **not** auto-open.

7. **Coverage check (optional).** If `coverage.json` or `.coverage` exists at repo root, run:

   ```bash
   codebase-map coverage coverage.json -f docs/function-map/graph.json
   ```

   Otherwise skip bullet #4 below gracefully.

## Deliverable — 5-bullet onboarding summary

Close with a concise report. No JSON dumps. Readable in chat:

- **Scale:** total nodes / edges / domains (from `summary`).
- **Top 3 domains:** ranked by node count.
- **API surface:** count of HTTP routes (from `api-catalog`). Note if zero → pure library or worker.
- **Coverage gaps:** top uncovered modules (skip this bullet if no coverage data).
- **Entry points:** `main` / `__main__` / route handlers / CLI entry — use `codebase-map search "main"` if needed.

Stop there. Don't dump the full graph — the HTML is for that.
