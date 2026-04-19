---
name: cbm-diff
description: "Usage: /cbm-diff [git-ref] — generate PR impact report for this branch vs base."
---

Produce a Markdown PR-body section describing what this branch changed, using dual-snapshot diff when possible and git-diff as fallback.

Default base ref: `main`. Override with `$ARGUMENTS`, e.g. `/cbm-diff develop`.

## Steps

1. **Resolve base ref.** `BASE_REF=${ARGUMENTS:-main}` conceptually — use `main` if the user passed nothing.

2. **Check graph freshness:**

   ```bash
   codebase-map check-staleness -f docs/function-map/graph.json --json
   ```

   If the file is missing, or the JSON reports `stale: true`, regenerate with a `post-dev` label:

   ```bash
   codebase-map generate -c codebase-map.yaml --label post-dev
   ```

   Otherwise, still run `generate --label post-dev` before diffing so the `post-dev` snapshot exists.

3. **Dual-snapshot mode (preferred).** List snapshots:

   ```bash
   codebase-map snapshots list --json
   ```

   If a snapshot named `baseline` is present, run:

   ```bash
   codebase-map snapshot-diff \
       --baseline baseline \
       --current post-dev \
       --format markdown \
       --depth 2 \
       --test-plan
   ```

   `--depth 2` widens callers beyond the default 1 — right fit for PR review. `--test-plan` adds the grouped test-plan block at the bottom.

4. **Git-diff fallback.** If no `baseline` snapshot exists, run:

   ```bash
   codebase-map diff "$BASE_REF" -f docs/function-map/graph.json --depth 2
   ```

   Reformat the plain-text output into the same Markdown shape as step 3 (see template below). Do **not** use `--json` here — it's harder to reshape in chat.

   When presenting the fallback, nudge the user: *"For richer output next time, run `codebase-map generate --label baseline` on the base branch before starting work."*

5. **Output shape** — whichever mode ran, deliver one Markdown block the user can paste into a PR body:

   ```markdown
   ## Impact (CBM)

   **Functions changed:** N added · M removed · K modified · R renamed

   ### Added
   - `module.func` — <brief>

   ### Removed
   - …

   ### Modified / Renamed
   - …

   ### Affected callers (by domain)
   - **<domain>** — N callers: `a.b`, `c.d`, …

   ### Suggested test plan
   - [ ] …
   ```

6. **Clipboard offer.** After printing the block, offer to copy it:

   - macOS: `pbcopy`
   - Linux: `xclip -selection clipboard` or `wl-copy`

   Detect availability with `command -v pbcopy` / `command -v xclip` / `command -v wl-copy`. If none present, skip silently — don't error.

## Rules

- Keep the Markdown clean — no stray `<pre>` or terminal escape codes.
- If the diff is empty (no behavioural change), say so in one line instead of printing an empty table.
- Never auto-push or auto-commit. This command only prints text.
