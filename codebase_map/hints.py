# HC-AI | ticket: CBM-USER-HINTS
"""User Hints for Codebase Map (CBM) — contextual guidance for every command.

Mirrors KMP hints system (knowledge_memory/core/hints.py).
CEO requirement: each command needs what/how/quality/improve guidance.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QualityLevel:
    """A single quality indicator."""

    level: str  # "perfect" | "good" | "normal" | "bad"
    description: str


@dataclass
class UserHint:
    """User-facing hint for a CBM command."""

    command: str
    title: str
    what_it_does: str
    how_to_use: str
    quality_levels: list[QualityLevel] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    next_step: str = ""


# HC-AI | ticket: CBM-USER-HINTS
HINTS: dict[str, UserHint] = {
    "generate": UserHint(
        command="codebase-map generate",
        title="Function Dependency Graph Generator",
        what_it_does=(
            "Parses your codebase using AST analysis and builds a "
            "function dependency graph (nodes = functions/classes, "
            "edges = call relationships). Outputs JSON + interactive "
            "HTML visualization. Foundation for all other CBM commands."
        ),
        how_to_use=(
            "Run `codebase-map generate -c codebase-map.yaml`. "
            "Add `--label name` to create a named snapshot. "
            "Output dir configured in YAML `output.dir`."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "1000+ nodes, 5000+ edges, 5+ domains, <30s build time",
            ),
            QualityLevel(
                "good",
                "100-1000 nodes, layers correctly classified",
            ),
            QualityLevel(
                "normal",
                "<100 nodes — small project or narrow scan scope",
            ),
            QualityLevel(
                "bad",
                "0 nodes — check source paths in config YAML",
            ),
        ],
        suggestions=[
            "Expand sources in config to include all code directories",
            "Exclude migrations, tests, __pycache__ for cleaner graph",
            "Use `--label` to create snapshots for before/after comparison",
        ],
        next_step=(
            "Run `codebase-map summary` to verify graph stats, "
            "or open the HTML file in browser."
        ),
    ),
    "query": UserHint(
        command="codebase-map query",
        title="Function/Class Lookup",
        what_it_does=(
            "Look up detailed information about a specific function or "
            "class: file location, line number, layer, domain, "
            "dependencies (who it calls), and dependents (who calls it)."
        ),
        how_to_use=(
            'Run `codebase-map query "function_name" -f graph.json`. '
            "Supports partial name matching."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "Function found with full metadata + callers + callees",
            ),
            QualityLevel(
                "good",
                "Function found but no callers (isolated utility)",
            ),
            QualityLevel(
                "bad",
                "Not found — check spelling or run generate first",
            ),
        ],
        suggestions=[
            "Use partial names for fuzzy matching",
            "Check layer classification is correct for the function",
        ],
    ),
    "impact": UserHint(
        command="codebase-map impact",
        title="Impact Zone Analysis",
        what_it_does=(
            "Shows all functions that depend on a given function/class. "
            "Helps you understand the blast radius before modifying code. "
            "Groups impacted nodes by domain for targeted testing."
        ),
        how_to_use=(
            'Run `codebase-map impact "ClassName" -f graph.json`. '
            "Shows direct dependents + transitive impact zone."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "Impact zone shown with domain grouping, <50 affected nodes",
            ),
            QualityLevel(
                "normal",
                "Large impact zone (50+) — consider splitting the class",
            ),
            QualityLevel(
                "bad",
                "0 dependents — function may be orphaned (unused)",
            ),
        ],
        suggestions=[
            "High impact zone (50+) = split the function/class",
            "Check if orphan functions (0 dependents) can be removed",
            "Use before refactoring to understand risk",
        ],
    ),
    "summary": UserHint(
        command="codebase-map summary",
        title="Graph Statistics Overview",
        what_it_does=(
            "Shows high-level statistics: total nodes, edges, "
            "breakdown by layer (route/service/model/util) and domain. "
            "Quick health check for your graph."
        ),
        how_to_use="Run `codebase-map summary -f graph.json`.",
        quality_levels=[
            QualityLevel(
                "perfect",
                "All layers present, domains match project structure",
            ),
            QualityLevel(
                "normal",
                "Most nodes in 'util' — layer classification may need tuning",
            ),
            QualityLevel(
                "bad",
                "0 nodes — graph file missing or empty",
            ),
        ],
        suggestions=[
            "If >50% nodes are 'unknown' layer, check classifier config",
            "Compare node count with `find . -name '*.py' | wc -l`",
        ],
    ),
    "search": UserHint(
        command="codebase-map search",
        title="Keyword Search Across Graph",
        what_it_does=(
            "Search all functions/classes by keyword. "
            "Matches against names, file paths, and domains. "
            "Useful for finding all functions related to a feature."
        ),
        how_to_use=(
            'Run `codebase-map search "keyword" -f graph.json`. '
            "Results sorted by relevance."
        ),
        quality_levels=[
            QualityLevel("perfect", "Relevant results with file paths"),
            QualityLevel(
                "normal",
                "Too many results — use more specific keyword",
            ),
            QualityLevel("bad", "0 results — check keyword spelling"),
        ],
    ),
    "diff": UserHint(
        command="codebase-map diff",
        title="Git Diff Impact Analysis",
        what_it_does=(
            "Compares your current branch against a git ref (e.g., main) "
            "to find changed files, changed functions, and their impact "
            "zone. Shows which functions are affected by your changes."
        ),
        how_to_use=(
            "Run `codebase-map diff main -f graph.json`. "
            "Add `--json` for machine-readable output."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "Changed nodes + impact zone clearly identified",
            ),
            QualityLevel(
                "normal",
                "Large impact zone — consider splitting PR",
            ),
            QualityLevel(
                "bad",
                "No changes detected — check git ref is correct",
            ),
        ],
        suggestions=[
            "Run before creating PR to assess structural impact",
            "Use `--json` output for CI integration",
            "Impact zone >50 nodes = consider splitting the PR",
        ],
    ),
    "snapshot-diff": UserHint(
        command="codebase-map snapshot-diff",
        title="Dual-Snapshot Structural Diff",
        what_it_does=(
            "Compares two graph snapshots (before/after) to find: "
            "added, removed, modified, and renamed functions. "
            "Detects affected callers and generates PR Impact reports. "
            "This is CBM's most powerful feature (v2.2)."
        ),
        how_to_use=(
            "Run `codebase-map snapshot-diff "
            "--baseline <label> --current <label> "
            "--format markdown`. "
            "Formats: text (terminal), markdown (PR body), json (CI)."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "Diff shows added/removed/modified with affected callers",
            ),
            QualityLevel(
                "good",
                "Changes detected but 0 affected callers (additive PR)",
            ),
            QualityLevel(
                "normal",
                "No changes — snapshots are identical",
            ),
            QualityLevel(
                "bad",
                "Baseline not found — run `snapshots list` to check",
            ),
        ],
        suggestions=[
            "Use `--format markdown` and paste into PR body",
            "Use `--breaking-only` to see only risky changes",
            "Use `--test-plan` for domain-grouped testing checklist",
            "Use `--depth 2` or `3` for deeper caller analysis",
        ],
        next_step="Copy markdown output into your PR description.",
    ),
    "snapshots": UserHint(
        command="codebase-map snapshots",
        title="Snapshot Management",
        what_it_does=(
            "List, view, and clean graph snapshots. "
            "Snapshots are saved versions of your graph with metadata "
            "(branch, commit SHA, timestamp, label). "
            "Used for before/after comparison with snapshot-diff."
        ),
        how_to_use=(
            "Run `codebase-map snapshots list` to see all snapshots. "
            "Use `snapshots clean --keep 10` to remove old ones."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "Multiple snapshots with clear labels and dates",
            ),
            QualityLevel(
                "normal",
                "Only 1 snapshot — generate more with --label",
            ),
            QualityLevel(
                "bad",
                "0 snapshots — run generate with --label first",
            ),
        ],
    ),
    "api-catalog": UserHint(
        command="codebase-map api-catalog",
        title="API Route Catalog",
        what_it_does=(
            "Lists all API routes/endpoints found in the codebase "
            "with their HTTP methods, handler functions, and service "
            "dependencies. Useful for API documentation and review."
        ),
        how_to_use=(
            "Run `codebase-map api-catalog -f graph.json`. "
            "Shows routes grouped by domain/module."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "All routes listed with methods and handler functions",
            ),
            QualityLevel(
                "normal",
                "Some routes missing — check if route layer is classified correctly",
            ),
            QualityLevel(
                "bad",
                "0 routes — project may not use standard route patterns",
            ),
        ],
    ),
    "coverage": UserHint(
        command="codebase-map coverage",
        title="Test Coverage Overlay",
        what_it_does=(
            "Overlays test coverage data onto the function graph. "
            "Shows which functions are tested and which are not. "
            "Helps identify testing gaps in critical code paths."
        ),
        how_to_use=(
            "Run `codebase-map coverage -f graph.json "
            "--coverage-file .coverage`. "
            "Requires pytest-cov output."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                ">80% functions covered, critical paths all green",
            ),
            QualityLevel(
                "normal",
                "50-80% coverage — focus on service layer gaps",
            ),
            QualityLevel(
                "bad",
                "<50% or no coverage file — run pytest --cov first",
            ),
        ],
        suggestions=[
            "Focus coverage on service + route layers first",
            "Use with impact command to find untested high-impact functions",
        ],
    ),
    "check-staleness": UserHint(
        command="codebase-map check-staleness",
        title="Graph Freshness Check",
        what_it_does=(
            "Checks if your graph is outdated compared to recent "
            "code changes. Warns if graph was generated before the "
            "latest commits. Can notify via Telegram."
        ),
        how_to_use=(
            "Run `codebase-map check-staleness -f graph.json`. "
            "Add `--notify` to send Telegram alert if stale."
        ),
        quality_levels=[
            QualityLevel("perfect", "Graph is fresh (generated after latest commit)"),
            QualityLevel(
                "normal",
                "Graph is 1-3 days old — consider regenerating",
            ),
            QualityLevel(
                "bad",
                "Graph is >7 days old — regenerate before using",
            ),
        ],
    ),
}


def get_hint(command: str) -> UserHint | None:
    """Get hint for a CBM command."""
    return HINTS.get(command)


def list_commands() -> list[str]:
    """List all CBM commands with hints."""
    return sorted(HINTS.keys())


def format_hint(hint: UserHint) -> str:
    """Format a UserHint for terminal output."""
    lines: list[str] = []

    lines.append(f"\u2501\u2501 {hint.title} \u2501\u2501")
    lines.append(f"Command: {hint.command}")
    lines.append("")

    lines.append("\u25b6 WHAT IT DOES")
    lines.append(f"  {hint.what_it_does}")
    lines.append("")

    lines.append("\u25b6 HOW TO USE")
    lines.append(f"  {hint.how_to_use}")
    lines.append("")

    if hint.quality_levels:
        lines.append("\u25b6 RESULT QUALITY")
        icons = {
            "perfect": "\u2705",
            "good": "\U0001f535",
            "normal": "\U0001f7e1",
            "bad": "\U0001f534",
        }
        for q in hint.quality_levels:
            icon = icons.get(q.level, "\u25cb")
            lines.append(f"  {icon} {q.level.upper()}: {q.description}")
        lines.append("")

    if hint.suggestions:
        lines.append("\u25b6 IMPROVE RESULTS")
        for s in hint.suggestions:
            lines.append(f"  \u2022 {s}")
        lines.append("")

    if hint.next_step:
        lines.append(f"\u27a1 Next: {hint.next_step}")

    return "\n".join(lines)


def format_all_hints_summary() -> str:
    """Format summary of all CBM commands."""
    lines = [
        "Codebase Map \u2014 User Guide",
        "",
        "Available commands:",
        "",
    ]

    for cmd in sorted(HINTS.keys()):
        hint = HINTS[cmd]
        lines.append(f"  {cmd:<18} {hint.title}")

    lines.append("")
    lines.append("Run `codebase-map help <command>` for detailed guidance.")

    return "\n".join(lines)
