# HC-AI | ticket: KMP-CLI-01
"""CLI entry point for codebase-memory.

Commands: init|bootstrap|summary|ask|why|impact|onboard|glossary|insights.

Provides a rich terminal interface for the Knowledge Memory Platform.
Uses existing engine modules + cli_output.py for formatted output.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# HC-AI | ticket: KMP-CLI-01
# Lazy imports inside each command to keep startup fast.

__all__ = ["main"]

_VERSION = "1.0.0"

logger = logging.getLogger("codebase-memory")


# ═══════════════════════════════════════════════════════
# ARGUMENT PARSER
# ═══════════════════════════════════════════════════════


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="codebase-memory",
        description=(
            "Knowledge Memory Platform — learn patterns, "
            "ask questions, analyze impact."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"codebase-memory {_VERSION}"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory (default: current directory)",
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # --- init ---
    sub.add_parser("init", help="Initialize vault in project")

    # --- bootstrap ---
    bs = sub.add_parser("bootstrap", help="Scan codebase + learn patterns")
    bs.add_argument(
        "--resume", action="store_true", help="Resume interrupted bootstrap"
    )
    bs.add_argument("--force", action="store_true", help="Force re-initialize vault")
    bs.add_argument(
        "--include",
        default="backend/**/*.py",
        help="Glob pattern for files to include (default: backend/**/*.py)",
    )
    bs.add_argument(
        "--exclude",
        nargs="*",
        default=None,
        help="Glob patterns to exclude",
    )

    # --- summary ---
    sub.add_parser("summary", help="Show vault status and statistics")

    # --- ask ---
    ask = sub.add_parser("ask", help="Ask a question about the codebase (requires LLM)")
    ask.add_argument("question", help="Natural language question")

    # --- why ---
    why = sub.add_parser("why", help="Explain dependency between two functions")
    why.add_argument("source", help="Source function name")
    why.add_argument("target", help="Target function name")

    # --- impact ---
    imp = sub.add_parser("impact", help="Analyze change impact of a function")
    imp.add_argument("function", help="Function name to analyze")
    imp.add_argument(
        "--depth", type=int, default=2, help="Caller traversal depth (1-3, default: 2)"
    )

    # --- onboard ---
    onb = sub.add_parser("onboard", help="Generate onboarding report")
    onb.add_argument(
        "--output-dir",
        default="",
        help="Output directory (default: .knowledge-memory/)",
    )

    # --- glossary ---
    gls = sub.add_parser("glossary", help="Extract domain vocabulary")
    gls.add_argument(
        "--limit", type=int, default=30, help="Max terms to display (default: 30)"
    )

    # --- insights ---
    ins = sub.add_parser("insights", help="Generate insights dashboard")
    ins.add_argument(
        "--html", action="store_true", help="Export interactive HTML dashboard"
    )
    ins.add_argument(
        "--project", default="Codebase", help="Project name for HTML title"
    )

    # --- quick-wins ---
    sub.add_parser("quick-wins", help="Show quick wins from last bootstrap")

    return parser


# ═══════════════════════════════════════════════════════
# RICH CONSOLE HELPERS
# ═══════════════════════════════════════════════════════


def _console():
    """Get a rich Console instance."""
    try:
        from rich.console import Console

        return Console()
    except ImportError:
        return None


def _print(msg: str, style: str = "") -> None:
    """Print with optional rich styling."""
    con = _console()
    if con and style:
        con.print(msg, style=style)
    elif con:
        con.print(msg)
    else:
        print(msg)


def _error(msg: str) -> None:
    """Print error message."""
    con = _console()
    if con:
        con.print(f"✗ {msg}", style="bold red")
    else:
        print(f"ERROR: {msg}", file=sys.stderr)


def _success(msg: str) -> None:
    """Print success message."""
    con = _console()
    if con:
        con.print(f"✓ {msg}", style="bold green")
    else:
        print(f"OK: {msg}")


# ═══════════════════════════════════════════════════════
# VAULT HELPER
# ═══════════════════════════════════════════════════════


def _open_vault(root: Path):
    """Open existing vault, return (vault, success)."""
    from knowledge_memory.verticals.codebase.vault import CodebaseVault

    vault = CodebaseVault()
    vault_dir = root / ".knowledge-memory"
    if not vault_dir.exists():
        _error(f"Vault not found at {vault_dir}.\n" "  Run: codebase-memory init")
        return None
    vault.open(root)
    return vault


# ═══════════════════════════════════════════════════════
# COMMAND IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════


# HC-AI | ticket: KMP-CLI-01
def _cmd_init(root: Path) -> int:
    """Initialize vault."""
    from knowledge_memory.verticals.codebase.vault import CodebaseVault

    vault_dir = root / ".knowledge-memory"
    if vault_dir.exists():
        _print("Vault already exists. Use --force with bootstrap to re-initialize.")
        return 0

    vault = CodebaseVault()
    vault.init(root)

    _success("Vault initialized!")
    _print(f"  Created {vault_dir}/")
    _print(f"  Created {vault_dir}/core.db")
    _print(f"  Created {vault_dir}/config.yaml")

    # Add to .gitignore
    gitignore = root / ".gitignore"
    marker = ".knowledge-memory/"
    if gitignore.exists():
        content = gitignore.read_text()
        if marker not in content:
            with open(gitignore, "a") as f:
                f.write(f"\n# KMP vault (local, not committed)\n{marker}\n")
            _print(f"  Added {marker} to .gitignore")
    else:
        gitignore.write_text(f"# KMP vault (local, not committed)\n{marker}\n")
        _print(f"  Created .gitignore with {marker}")

    _print("\nNext: codebase-memory bootstrap", style="bold cyan")
    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_bootstrap(root: Path, args: argparse.Namespace) -> int:
    """Bootstrap: scan + learn patterns."""
    from knowledge_memory.verticals.codebase.bootstrap import BootstrapOrchestrator
    from knowledge_memory.verticals.codebase.cli_output import (
        format_bootstrap_complete,
        format_bootstrap_header,
        format_quick_wins_inline,
        format_step_progress,
        format_step_result,
        format_vault_info,
    )
    from knowledge_memory.verticals.codebase.quick_wins import generate_quick_wins

    # Header
    print(format_bootstrap_header())
    print(format_vault_info())
    print()

    include = [args.include] if args.include else ["backend/**/*.py"]
    exclude = args.exclude or [
        "**/tests/**",
        "**/__pycache__/**",
        "**/.venv/**",
        "**/venv/**",
        "**/alembic/**",
        "**/migrations/**",
    ]

    orchestrator = BootstrapOrchestrator(
        root=root,
        include_patterns=include,
        exclude_patterns=exclude,
        force_init=args.force,
        resume=args.resume,
    )

    # Progress callback
    def on_progress(step: int, total: int, msg: str) -> None:
        print(format_step_progress(step, total, msg.split("...")[0], msg))

    result = orchestrator.run(progress_callback=on_progress)

    if not result.success and not result.interrupted:
        _error("Bootstrap failed!")
        for err in result.errors:
            _print(f"  - {err}", style="red")
        return 1

    # Step results
    if result.parse_stats:
        print(
            format_step_result(
                f"{result.parse_stats.get('files', 0)} files parsed, "
                f"{result.parse_stats.get('nodes', 0)} nodes"
            )
        )

    for name, count in result.learner_results.items():
        print(format_step_result(f"{name}: {count} patterns"))

    print()
    print(
        format_bootstrap_complete(
            elapsed=result.elapsed_seconds,
            pattern_count=result.pattern_count,
            quick_win_count=0,
        )
    )

    # Quick wins
    vault = _open_vault(root)
    if vault:
        try:
            qw = generate_quick_wins(vault)
            if qw.insights:
                print()
                print(format_quick_wins_inline(qw))
        except Exception:
            pass  # Quick wins are optional

    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_summary(root: Path) -> int:
    """Show vault summary."""
    from knowledge_memory.verticals.codebase.cli_output import format_vault_summary

    vault = _open_vault(root)
    if not vault:
        return 1

    patterns = vault.query_patterns()
    categories = {p.category for p in patterns}
    breakdown = ", ".join(
        f"{cat}: {sum(1 for p in patterns if p.category == cat)}"
        for cat in sorted(categories)
    )

    print(
        format_vault_summary(
            vault_path=str(root / ".knowledge-memory/"),
            pattern_count=len(patterns),
            pattern_breakdown=breakdown,
            snapshot_count=vault.snapshot_count(),
            node_count=vault.node_count(),
            edge_count=vault.edge_count(),
        )
    )
    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_ask(root: Path, args: argparse.Namespace) -> int:
    """Ask a question (requires LLM API key)."""
    _error(
        "Ask command requires LLM API key.\n"
        "  Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.\n"
        "  Configure in .knowledge-memory/config.yaml\n\n"
        "  This feature is planned for KMP M2 release."
    )
    return 1


# HC-AI | ticket: KMP-CLI-01
def _cmd_why(root: Path, args: argparse.Namespace) -> int:
    """Explain dependency between two functions."""
    from knowledge_memory.verticals.codebase.why import WhyEngine, format_why_result

    vault = _open_vault(root)
    if not vault:
        return 1

    nodes = vault.query_nodes()
    edges = vault.query_edges()
    patterns = [p.name for p in vault.query_patterns()]

    engine = WhyEngine()
    engine.load_graph(nodes, edges, patterns)
    result = engine.why(args.source, args.target)

    print(format_why_result(result))
    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_impact(root: Path, args: argparse.Namespace) -> int:
    """Analyze change impact."""
    from knowledge_memory.verticals.codebase.impact import (
        ImpactEngine,
        format_impact_result,
    )

    vault = _open_vault(root)
    if not vault:
        return 1

    nodes = vault.query_nodes()
    edges = vault.query_edges()

    engine = ImpactEngine()
    engine.load_graph(nodes, edges)
    result = engine.analyze(args.function, depth=args.depth)

    print(format_impact_result(result))
    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_onboard(root: Path, args: argparse.Namespace) -> int:
    """Generate onboarding report."""
    from knowledge_memory.verticals.codebase.onboard import (
        OnboardEngine,
        format_onboard_result,
    )

    vault = _open_vault(root)
    if not vault:
        return 1

    patterns = vault.query_patterns()
    nodes = vault.query_nodes()

    stats = {
        "total_nodes": vault.node_count(),
        "domains": len(
            set(
                n.get("file_path", "").split("/")[0]
                for n in nodes
                if n.get("file_path")
            )
        ),
    }

    engine = OnboardEngine()
    engine.load_data(patterns, stats)

    output_dir = args.output_dir or str(root / ".knowledge-memory")
    result = engine.generate(output_dir=output_dir)

    print(format_onboard_result(result))
    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_glossary(root: Path, args: argparse.Namespace) -> int:
    """Extract domain vocabulary."""
    from knowledge_memory.verticals.codebase.glossary import GlossaryExtractor

    vault = _open_vault(root)
    if not vault:
        return 1

    nodes = vault.query_nodes()
    extractor = GlossaryExtractor()
    terms = extractor.extract(nodes)

    con = _console()
    if con:
        from rich.table import Table

        table = Table(title="Domain Glossary", show_lines=False)
        table.add_column("Term", style="bold cyan")
        table.add_column("Domain", style="dim")
        table.add_column("Evidence", justify="right")
        table.add_column("Confidence", justify="right")

        for t in terms[: args.limit]:
            conf_style = (
                "green"
                if t.confidence >= 80
                else "yellow" if t.confidence >= 60 else "red"
            )
            table.add_row(
                t.term,
                t.domain,
                str(t.evidence_count),
                f"[{conf_style}]{t.confidence:.0f}%[/{conf_style}]",
            )

        con.print(table)
        if len(terms) > args.limit:
            con.print(
                f"\n  ... {len(terms) - args.limit} more terms. "
                f"Use --limit {len(terms)} to show all.",
                style="dim",
            )
    else:
        print(f"=== Glossary ({len(terms)} terms) ===\n")
        for t in terms[: args.limit]:
            print(
                f"  {t.term:<30} {t.domain:<15}"
                f" {t.evidence_count:>5}  {t.confidence:.0f}%"
            )

    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_insights(root: Path, args: argparse.Namespace) -> int:
    """Generate insights dashboard."""
    from knowledge_memory.verticals.codebase.insights_cli import (
        InsightsEngine,
        format_insights_result,
    )

    vault = _open_vault(root)
    if not vault:
        return 1

    patterns = vault.query_patterns()

    html_path = ""
    if args.html:
        html_path = str(root / ".knowledge-memory" / "insights.html")

    engine = InsightsEngine()
    result = engine.generate(
        patterns=patterns,
        output_html=html_path,
        project_name=args.project,
    )

    print(format_insights_result(result))

    if result.html_path:
        # Auto-open in browser
        try:
            import webbrowser

            webbrowser.open(f"file://{result.html_path}")
        except Exception:
            pass

    return 0


# HC-AI | ticket: KMP-CLI-01
def _cmd_quick_wins(root: Path) -> int:
    """Show quick wins."""
    from knowledge_memory.verticals.codebase.cli_output import format_quick_wins_inline
    from knowledge_memory.verticals.codebase.quick_wins import generate_quick_wins

    vault = _open_vault(root)
    if not vault:
        return 1

    result = generate_quick_wins(vault)
    print(format_quick_wins_inline(result, max_lines=40))
    return 0


# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════


def main(argv: list[str] | None = None) -> int:
    """CLI main entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)

    root = Path(args.root).resolve()

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "init": lambda: _cmd_init(root),
        "bootstrap": lambda: _cmd_bootstrap(root, args),
        "summary": lambda: _cmd_summary(root),
        "ask": lambda: _cmd_ask(root, args),
        "why": lambda: _cmd_why(root, args),
        "impact": lambda: _cmd_impact(root, args),
        "onboard": lambda: _cmd_onboard(root, args),
        "glossary": lambda: _cmd_glossary(root, args),
        "insights": lambda: _cmd_insights(root, args),
        "quick-wins": lambda: _cmd_quick_wins(root),
    }

    handler = commands.get(args.command)
    if not handler:
        parser.print_help()
        return 1

    try:
        return handler()
    except KeyboardInterrupt:
        _print("\nInterrupted.", style="yellow")
        return 130
    except Exception as exc:
        _error(f"Unexpected error: {exc}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1
