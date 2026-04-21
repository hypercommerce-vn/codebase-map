<!-- HC-AI | ticket: CBM-INT-305 | author: TechLead agent | date: 21/04/2026 -->
<!-- Loom production-ready script — CEO records in 1 take · 2 min (120s) · 12 scenes × 10s -->

# CBM Launch Demo Video — Script + Storyboard

**Duration:** 2 minutes (120 seconds)
**Format:** Loom screen recording with voice-over
**Target audience:** HN / Reddit / dev.to viewer · senior backend engineer
**Call to action:** `pipx install 'codebase-map[mcp]'`
**Recorder:** CEO (Đoàn Đình Tỉnh) · 1-take goal

---

## Shot list · 12 scenes × 10 seconds

### Scene 1 · 0:00 – 0:10 · Hook
- **Screen:** Claude Code open in a FastAPI repo. Cursor blinking in a code file.
- **Action:** None — static shot, viewer reads the code.
- **Voice:** "Every day, developers ask: where is this function called from? What breaks if I change it? Here's how we taught Claude to answer, in one second."

### Scene 2 · 0:10 – 0:20 · Install
- **Screen:** Terminal, iTerm full-screen, 18pt font.
- **Action:** Type `pipx install 'codebase-map[mcp]'` → Enter. Install completes showing `cbm-mcp` and `codebase-map` entry points.
- **Voice:** "One command. No setup. pipx install codebase-map with the MCP extra — that's it."

### Scene 3 · 0:20 – 0:30 · Wire into Claude Desktop
- **Screen:** VS Code open on `claude_desktop_config.json`.
- **Action:** Paste the 3-line block: `"codebase-map": { "command": "cbm-mcp" }` inside `mcpServers`. Save.
- **Voice:** "Drop this three-line block into your Claude Desktop config. Restart Claude. Done."

### Scene 4 · 0:30 – 0:40 · Generate the graph
- **Screen:** Terminal in `/tmp/fastapi-test`.
- **Action:** Run `codebase-map generate -c codebase-map.yaml`. Output shows node + edge counts.
- **Voice:** "In your repo, run generate once. CBM parses the AST and writes a dependency graph — a few hundred milliseconds on a medium codebase."

### Scene 5 · 0:40 – 0:50 · First question — impact
- **Screen:** Claude Desktop window, chat empty.
- **Action:** Type: *"What breaks if I change APIRouter?"* → Enter.
- **Voice:** "Ask Claude anything structural. Claude sees the MCP tools and picks the right one — here, `cbm_impact`."

### Scene 6 · 0:50 – 1:00 · Impact response
- **Screen:** Claude's response. Auto-invoke pill visible: `cbm_impact`.
- **Action:** None — let viewer read. Highlight the lines: `1 node affected · Risk: Low · Suggested PR split: single commit`.
- **Voice:** "One affected node, low risk, no cross-layer fallout. Claude gives you the blast radius before you touch a single line."

### Scene 7 · 1:00 – 1:10 · Second question — PR diff
- **Screen:** Claude Desktop, same session.
- **Action:** Type: *"Generate a PR body comparing my branch to main, with a test plan."* → Enter.
- **Voice:** "Or ask for a PR body. Claude reaches for `cbm_snapshot_diff` — added nodes, removed nodes, breaking changes, test plan, all in Markdown."

### Scene 8 · 1:10 – 1:20 · Snapshot diff response
- **Screen:** Claude's Markdown output, clean rendered.
- **Action:** Scroll slowly through the table of changes + the test-plan bullets at the bottom.
- **Voice:** "Ready to paste straight into GitHub. No more staring at git diff trying to write review notes."

### Scene 9 · 1:20 – 1:30 · Third question — onboarding
- **Screen:** Claude Desktop, new prompt.
- **Action:** Type: *"Onboard me to this Python repo."* → Enter. Claude runs the `/cbm-onboard` skill, returns 5 bullets.
- **Voice:** "New engineer on a new codebase? Ask for onboarding. Five bullets — layers, entry points, hotspots — in about ten seconds."

### Scene 10 · 1:30 – 1:40 · Plugin install flow
- **Screen:** Claude Code terminal.
- **Action:** Type `/plugin marketplace add hypercommerce-vn/claude-plugins` → Enter. Then `/plugin install codebase-map` → Enter.
- **Voice:** "Prefer one-click? The Claude plugin wires everything for you — skills, slash commands, MCP server, all in two commands."

### Scene 11 · 1:40 – 1:50 · Archetype packs callout
- **Screen:** GitHub page of `hypercommerce-vn/claude-plugins`. README rendered showing 3 packs: core, AI Agent, SaaS B2B (bilingual).
- **Action:** Slow scroll past the table.
- **Voice:** "Two archetype packs ship alongside — one for AI-agent repos, one for SaaS B2B. English and Vietnamese, domain-tuned out of the box."

### Scene 12 · 1:50 – 2:00 · Numbers + CTA
- **Screen:** Split view — left: dev.to blog post "From what-does-this-code-do to where-does-it-call"; right: pypi.org/project/codebase-map/.
- **Action:** None — static end card with install command overlaid.
- **Voice:** "Twenty story points shipped in three days. Forty-times cache speedup. 158 passing tests. MIT. Try it now: pipx install codebase-map with the MCP extra."

---

## B-roll suggestions

- Close-up of terminal cursor blinking after `pipx install` completes (0:17 area)
- Zoom-in on the auto-invoke pill in Claude Desktop (every tool-call scene)
- D3.js graph HTML scroll/zoom for 2 seconds during Scene 4 overflow
- GitHub Actions green checkmark on v2.4.0 release (if extra second available)

## Captions (SRT format)

```srt
1
00:00:00,000 --> 00:00:10,000
Every day, developers ask: where is this function called from?
What breaks if I change it? Here's how we taught Claude to answer.

2
00:00:10,000 --> 00:00:20,000
One command. No setup.
pipx install codebase-map with the MCP extra.

3
00:00:20,000 --> 00:00:30,000
Drop this three-line block into your Claude Desktop config.
Restart Claude. Done.

4
00:00:30,000 --> 00:00:40,000
Run codebase-map generate once.
CBM parses the AST and writes a dependency graph.

5
00:00:40,000 --> 00:00:50,000
Ask Claude anything structural.
It picks the right MCP tool — here, cbm_impact.

6
00:00:50,000 --> 00:01:00,000
One affected node, low risk, no cross-layer fallout.
Blast radius before you touch a line.

7
00:01:00,000 --> 00:01:10,000
Ask for a PR body. Claude reaches for cbm_snapshot_diff.
Added, removed, breaking, test plan — all Markdown.

8
00:01:10,000 --> 00:01:20,000
Ready to paste into GitHub.
No more staring at git diff.

9
00:01:20,000 --> 00:01:30,000
New engineer? Ask for onboarding.
Five bullets in ten seconds.

10
00:01:30,000 --> 00:01:40,000
Prefer one-click?
The Claude plugin wires everything.

11
00:01:40,000 --> 00:01:50,000
Two archetype packs ship alongside.
AI Agent and SaaS B2B, bilingual.

12
00:01:50,000 --> 00:02:00,000
Twenty SP in three days. 40x cache speedup.
158 passing tests. MIT. Try it now.
```

## Screenshot checklist (pre-recording prep)

- [ ] FastAPI repo cloned at `/tmp/fastapi-test` with `codebase-map.yaml` pre-written
- [ ] Graph already generated once off-camera so Scene 4 runs in <3s
- [ ] Claude Desktop with MCP configured and restarted, `cbm-mcp` green in settings
- [ ] `claude_desktop_config.json` open in VS Code with cursor at the insertion point
- [ ] Terminal font size bumped to 18pt (iTerm → Preferences → Profiles → Text)
- [ ] Browser zoomed to 125% for pypi.org and dev.to end card
- [ ] Do Not Disturb ON · desktop notifications silenced
- [ ] Loom quality set to HD (1080p) and webcam OFF (screen-only)
- [ ] 3-line MCP config block copied to clipboard for Scene 3 paste
- [ ] Test run once muted to confirm timing hits 120s ± 3s

## Post-production notes

- Add a subtle lower-third at 0:00 with title "Codebase Map for Claude · v2.5"
- Bake captions in (English) — burn-in for silent social preview
- Export 1920×1080, MP4, H.264, under 40MB for dev.to inline embed
- Thumbnail: Claude Desktop screenshot with tool-call pill visible
