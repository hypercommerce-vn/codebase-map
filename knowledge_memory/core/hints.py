# HC-AI | ticket: KMP-USER-HINTS
"""User Hints system — contextual guidance for every KMP command.

CEO requirement: each function needs user-facing guidance including:
1. What it does (purpose + meaning)
2. How to use (commands + options)
3. Result quality indicators (perfect/good/normal/bad)
4. Suggestions to improve results

Matches design in kmp-final-v1-design.html (19 screens with hints).
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
    """User-facing hint for a command/screen."""

    command: str
    title: str
    what_it_does: str
    how_to_use: str
    quality_levels: list[QualityLevel] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    next_step: str = ""


# HC-AI | ticket: KMP-USER-HINTS
# All hints matching kmp-final-v1-design.html

HINTS: dict[str, UserHint] = {
    "init": UserHint(
        command="codebase-memory init",
        title="Vault Initialization",
        what_it_does=(
            "Initializes a Knowledge Memory vault in your project root. "
            "Creates SQLite databases, config file, and directory structure "
            "that stores learned patterns about your codebase. Run once per project."
        ),
        how_to_use=(
            "Run `codebase-memory init` in your project root. "
            "Use `--force` to reinitialize (warning: destroys existing data). "
            "After init, edit `.knowledge-memory/config.yaml` to customize."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "All 6 checkmarks green, vault.db created, .gitignore updated",
            ),
            QualityLevel(
                "good",
                "All checkmarks but .gitignore already had the entry",
            ),
            QualityLevel("bad", "Error — usually permissions issue or disk full"),
        ],
        next_step="Run `codebase-memory bootstrap` to start learning patterns.",
    ),
    "bootstrap": UserHint(
        command="codebase-memory bootstrap",
        title="5-Step Learning Pipeline",
        what_it_does=(
            "Scans your entire codebase using AST parsing, then runs 6 learners "
            "to discover patterns (naming conventions, architecture layers, error "
            "handling, DI, testing, ownership). Produces patterns.md + quick-wins.md."
        ),
        how_to_use=(
            "Run `codebase-memory bootstrap` after init. "
            "Use `--resume` to continue after Ctrl+C. "
            "Re-run to refresh after code changes."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "25+ patterns, all 6 learners pass, <5 min, 10 quick wins",
            ),
            QualityLevel("good", "15-25 patterns, 5/6 learners (1 skipped), <5 min"),
            QualityLevel(
                "normal",
                "5-15 patterns — small codebase or few conventions established",
            ),
            QualityLevel(
                "bad",
                "0 patterns — check scan scope in config.yaml",
            ),
        ],
        suggestions=[
            "Expand scan scope in config.yaml (include more directories)",
            "Ensure git history has 50+ commits for ownership patterns",
            "Lower confidence threshold from 60% to 40% for exploratory analysis",
        ],
    ),
    "quick-wins": UserHint(
        command="quick-wins (after bootstrap)",
        title="10 Actionable Insights",
        what_it_does=(
            "Generates 10 actionable insights from vault patterns. "
            "Fixed ratio: 5 structure + 3 pattern + 2 risk. "
            "Each insight includes confidence score and evidence file paths."
        ),
        how_to_use=(
            "Auto-generated after bootstrap step 5. "
            "Saved to quick-wins.md. View inline in terminal output."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "10 insights, all >=70% confidence, clear evidence paths",
            ),
            QualityLevel(
                "good",
                "8-10 insights, 2-3 below 70%",
            ),
            QualityLevel("normal", "5-7 insights — small project"),
            QualityLevel("bad", "<5 insights or all <60% — scan scope too narrow"),
        ],
        suggestions=[
            "Focus on risk items first (items 9-10)",
            "God classes >30 methods should be split",
            "Single-owner domains need knowledge transfer sessions",
        ],
    ),
    "ask": UserHint(
        command="codebase-memory ask",
        title="Natural Language Q&A",
        what_it_does=(
            "Ask any question about your codebase in natural language. "
            "Uses BM25 + graph proximity to find relevant context, "
            "then sends to your LLM provider for an answer with citations."
        ),
        how_to_use=(
            'Run `codebase-memory ask "How is authentication handled?"`. '
            "Use `--stream` for real-time output. "
            "Requires LLM provider configured in config.yaml (BYOK)."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "3+ citations, answer references specific files/lines, <5s",
            ),
            QualityLevel("good", "1-2 citations, answer is relevant but generic"),
            QualityLevel(
                "normal",
                "0 citations, answer from LLM knowledge only",
            ),
            QualityLevel(
                "bad",
                '"Not enough context" — run bootstrap first or rephrase',
            ),
        ],
        suggestions=[
            "Be specific: 'How does auth middleware validate JWT?'",
            "Use function names: 'What does OrderService.submit_order do?'",
            "Re-run bootstrap after code changes for fresh context",
        ],
    ),
    "why": UserHint(
        command="codebase-memory why",
        title="Dependency Explanation",
        what_it_does=(
            "Finds all call paths between two functions/modules using BFS. "
            "Shows direct, transitive, and shared-module paths. "
            "Detects cross-domain coupling and references related patterns."
        ),
        how_to_use=(
            'Run `codebase-memory why "OrderService calls BillingService"`. '
            "Names are fuzzy-matched — partial names work."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "Multiple paths found, cross-domain note with suggestion",
            ),
            QualityLevel("good", "1 direct path found"),
            QualityLevel(
                "bad",
                '"No path found" — names may be wrong, try partial match',
            ),
        ],
        suggestions=[
            "Cross-domain coupling often indicates need for shared interface",
            "Check architecture note in output for specific suggestions",
        ],
    ),
    "impact": UserHint(
        command="codebase-memory impact",
        title="Change Impact Analysis",
        what_it_does=(
            "Predicts the impact of modifying a function. "
            "Finds all callers (direct + transitive), classifies risk "
            "(HIGH=route, MEDIUM=service, LOW=test), recommends testing strategy."
        ),
        how_to_use=(
            'Run `codebase-memory impact "auth/service.py:authenticate"`. '
            "Use `--depth 2` for transitive callers. "
            "Accepts function name or file:function format."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "Risk level shown, callers listed with paths, recommendation given",
            ),
            QualityLevel("good", "Callers found, MEDIUM risk (ambiguous impact)"),
            QualityLevel("normal", "LOW risk — few callers, safe to modify"),
            QualityLevel(
                "bad",
                "HIGH risk with 10+ route callers — add integration tests first",
            ),
        ],
        suggestions=[
            "Always add tests for HIGH-risk function callers before modifying",
            "Consider extracting shared interface if 10+ cross-domain callers",
            "Use --depth 3 to see full blast radius before major refactors",
        ],
    ),
    "mcp": UserHint(
        command="codebase-memory mcp serve",
        title="MCP Server for AI Agents",
        what_it_does=(
            "Exposes 4 tools via MCP protocol: find_function, explain_module, "
            "pattern_check, impact. AI agents (Claude Code, Cursor) can query "
            "your vault directly during code review and implementation."
        ),
        how_to_use=(
            "Run `codebase-memory mcp serve` to start on stdio. "
            "Configure in your AI tool's MCP settings."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "4 tools + 2 resources registered, AI agent calls work",
            ),
            QualityLevel(
                "good",
                "Server starts but tools return empty (vault needs bootstrap)",
            ),
            QualityLevel(
                "bad",
                "Connection refused — check stdio transport config",
            ),
        ],
        suggestions=[
            "Run bootstrap first so tools have data",
            "pattern_check is useful during code review",
        ],
    ),
    "onboard": UserHint(
        command="codebase-memory onboard",
        title="Onboarding Report Generator",
        what_it_does=(
            "Generates a personalized 8-chapter onboarding guide from vault patterns. "
            "Covers: overview, naming, layers, errors, testing, DI, "
            "ownership, glossary. "
            "Includes Mermaid architecture diagrams."
        ),
        how_to_use=(
            "Run `codebase-memory onboard`. "
            "Output saved to onboarding-report.md. "
            "Share with new team members or commit to repo."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "8 chapters, 3 diagrams, 20+ patterns, 30+ glossary terms",
            ),
            QualityLevel(
                "good",
                '6-8 chapters, some show "no patterns detected"',
            ),
            QualityLevel(
                "bad",
                "Empty chapters — vault has <5 patterns, bootstrap needed",
            ),
        ],
        suggestions=[
            "Commit onboarding-report.md to your repo",
            "Update quarterly or after major refactors",
            "Pair new devs with the report + a domain expert",
        ],
    ),
    "glossary": UserHint(
        command="codebase-memory glossary",
        title="Domain Glossary",
        what_it_does=(
            "Extracts business domain terms from function names, class names, "
            "and file paths. Builds term-to-domain mapping with evidence count."
        ),
        how_to_use="Run `codebase-memory glossary` after bootstrap.",
        quality_levels=[
            QualityLevel(
                "perfect",
                "30+ terms across 5+ domains, matches business vocabulary",
            ),
            QualityLevel("good", "15-30 terms, some generic words"),
            QualityLevel("bad", "<10 terms — codebase too small or generic naming"),
        ],
        suggestions=[
            "Use descriptive function names with domain terms",
            "The more domain-specific your code, the richer the glossary",
        ],
    ),
    "insights": UserHint(
        command="codebase-memory insights",
        title="Insights Dashboard",
        what_it_does=(
            "Generates self-contained HTML dashboard: pattern confidence heatmap, "
            "learner efficiency, ROI calculator, LLM usage. "
            "Works offline, no external dependencies."
        ),
        how_to_use=(
            "Run `codebase-memory insights --html` to export dashboard. "
            "Without --html, shows terminal summary."
        ),
        quality_levels=[
            QualityLevel(
                "perfect",
                "25+ patterns, positive ROI, usage data from 10+ queries",
            ),
            QualityLevel(
                "good",
                "Dashboard renders but ROI empty (no LLM usage yet)",
            ),
            QualityLevel(
                "bad",
                "Empty dashboard — run bootstrap + ask questions first",
            ),
        ],
        suggestions=[
            "Export monthly for engineering leadership",
            "ROI section quantifies time saved vs API cost",
        ],
    ),
    "roi": UserHint(
        command="codebase-memory roi",
        title="Return on Investment",
        what_it_does=(
            "Calculates ROI: (hours saved x hourly rate) - LLM token cost. "
            "Hours saved from onboarding reports (2.5h each) + queries (0.1h each). "
            "Default rate $30/h. All data local, privacy-safe."
        ),
        how_to_use="Run `codebase-memory roi` for current ROI metrics.",
        quality_levels=[
            QualityLevel("perfect", "ROI > $200, return multiple > 1000x"),
            QualityLevel("good", "ROI positive, multiple > 100x"),
            QualityLevel("normal", "ROI near zero — early usage, keep going"),
            QualityLevel("bad", "Negative ROI — switch to cheaper LLM model"),
        ],
        suggestions=[
            "Generate onboarding reports for every new team member (biggest driver)",
            "Use ask for code review prep instead of manual exploration",
            "Set hourly_rate in config.yaml to your team's actual rate",
        ],
    ),
    "usage": UserHint(
        command="codebase-memory usage",
        title="LLM Cost Tracking",
        what_it_does=(
            "Shows cumulative LLM usage: provider, calls, tokens (in+out), "
            "cost per provider, average cost per query, most expensive query."
        ),
        how_to_use="Run `codebase-memory usage` to see current stats.",
        quality_levels=[
            QualityLevel("perfect", "Low avg cost (<$0.005/query)"),
            QualityLevel("good", "Moderate cost, most queries <$0.01"),
            QualityLevel("normal", "High cost — switch to cheaper model"),
            QualityLevel("bad", "$0.05+/query — expensive model for simple questions"),
        ],
        suggestions=[
            "Use gpt-4o-mini or gemini-2.0-flash for routine questions",
            "Reserve claude-sonnet for complex architecture questions",
            "Set max_tokens: 512 for concise answers",
        ],
    ),
}


def get_hint(command: str) -> UserHint | None:
    """Get hint for a command. Returns None if not found."""
    return HINTS.get(command)


def list_commands() -> list[str]:
    """List all commands that have hints."""
    return sorted(HINTS.keys())


def format_hint(hint: UserHint, use_color: bool = True) -> str:
    """Format a UserHint for terminal output.

    Matches the design in kmp-final-v1-design.html.
    """
    lines: list[str] = []

    # Header
    lines.append(f"\u2501\u2501 {hint.title} \u2501\u2501")
    lines.append(f"Command: {hint.command}")
    lines.append("")

    # What it does
    lines.append("\u25b6 WHAT IT DOES")
    lines.append(f"  {hint.what_it_does}")
    lines.append("")

    # How to use
    lines.append("\u25b6 HOW TO USE")
    lines.append(f"  {hint.how_to_use}")
    lines.append("")

    # Quality levels
    if hint.quality_levels:
        lines.append("\u25b6 RESULT QUALITY")
        level_icons = {
            "perfect": "\u2705",
            "good": "\U0001f535",
            "normal": "\U0001f7e1",
            "bad": "\U0001f534",
        }
        for q in hint.quality_levels:
            icon = level_icons.get(q.level, "\u25cb")
            label = q.level.upper()
            lines.append(f"  {icon} {label}: {q.description}")
        lines.append("")

    # Suggestions
    if hint.suggestions:
        lines.append("\u25b6 IMPROVE RESULTS")
        for s in hint.suggestions:
            lines.append(f"  \u2022 {s}")
        lines.append("")

    # Next step
    if hint.next_step:
        lines.append(f"\u27a1 Next: {hint.next_step}")

    return "\n".join(lines)


def format_all_hints_summary() -> str:
    """Format a summary of all available hints."""
    lines = [
        "Knowledge Memory \u2014 User Guide",
        "",
        "Available commands with hints:",
        "",
    ]

    for cmd in sorted(HINTS.keys()):
        hint = HINTS[cmd]
        lines.append(f"  {cmd:<14} {hint.title}")

    lines.append("")
    lines.append("Run `codebase-memory help <command>` for detailed guidance.")

    return "\n".join(lines)
