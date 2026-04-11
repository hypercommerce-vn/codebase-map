# HC-AI | ticket: MEM-M1-11
"""CLI summary output with rich colors for bootstrap + quick wins.

Provides formatted terminal output using the `rich` library.
Supports NO_COLOR=1 fallback for plain text environments.

Design ref: kmp-M1-design.html Screen B (bootstrap), C (quick wins), E (summary).
"""

import os
from io import StringIO
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from knowledge_memory.verticals.codebase.quick_wins import Insight, QuickWinsResult

# HC-AI | ticket: MEM-M1-11
# NO_COLOR spec: https://no-color.org/
_NO_COLOR = bool(os.environ.get("NO_COLOR", ""))


def _use_rich() -> bool:
    """Check if rich output is available and not suppressed."""
    if _NO_COLOR:
        return False
    try:
        import rich  # noqa: F401

        return True
    except ImportError:
        return False


# ═══════════════════════════════════════════════════════
# BOOTSTRAP PROGRESS OUTPUT
# ═══════════════════════════════════════════════════════


# HC-AI | ticket: MEM-M1-11
def format_bootstrap_header() -> str:
    """Format the bootstrap header line."""
    if _use_rich():
        from rich.text import Text

        t = Text()
        t.append("Knowledge Memory Platform", style="bold")
        t.append(" v1.0.0", style="dim")
        buf = StringIO()
        from rich.console import Console

        console = Console(file=buf, force_terminal=True, width=72)
        console.print(t)
        return buf.getvalue().rstrip()
    return "Knowledge Memory Platform v1.0.0"


def format_vault_info(
    vault_path: str = ".knowledge-memory/",
    vertical: str = "codebase",
    schema_version: int = 1,
) -> str:
    """Format vault info subtitle."""
    line = (
        f"Vault: {vault_path} · " f"Vertical: {vertical} · " f"Schema v{schema_version}"
    )
    if _use_rich():
        from rich.console import Console
        from rich.text import Text

        t = Text(line, style="dim")
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=72)
        console.print(t)
        return buf.getvalue().rstrip()
    return line


def format_step_progress(
    step: int,
    total: int,
    label: str,
    detail: str = "",
) -> str:
    """Format a single step progress line.

    Example: [1/5] Parse  Scanning Python files...
    """
    step_str = f"[{step}/{total}] {label}"
    if _use_rich():
        from rich.console import Console
        from rich.text import Text

        t = Text()
        t.append(step_str, style="bold")
        if detail:
            t.append(f"  {detail}", style="dim")
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=72)
        console.print(t)
        return buf.getvalue().rstrip()
    if detail:
        return f"{step_str}  {detail}"
    return step_str


def format_step_result(
    message: str,
    detail: str = "",
    elapsed: Optional[float] = None,
) -> str:
    """Format a step completion result.

    Example: ✓ 25 patterns committed (12 naming + 8 layer)  0.2s
    """
    parts = [f"  ✓ {message}"]
    if detail:
        parts.append(f" {detail}")
    if elapsed is not None:
        parts.append(f"  {elapsed:.1f}s")
    line = "".join(parts)

    if _use_rich():
        from rich.console import Console
        from rich.text import Text

        t = Text()
        t.append("  ✓ ", style="green")
        t.append(message, style="bold" if not detail else "")
        if detail:
            t.append(f" {detail}", style="dim")
        if elapsed is not None:
            t.append(f"  {elapsed:.1f}s", style="dim")
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=72)
        console.print(t)
        return buf.getvalue().rstrip()
    return line


# HC-AI | ticket: MEM-M1-11
def format_bootstrap_complete(
    elapsed: float,
    pattern_count: int,
    quick_win_count: int,
) -> str:
    """Format the bootstrap completion banner."""
    line = (
        f"✓ Bootstrap complete!  "
        f"Total: {elapsed:.1f}s · "
        f"{pattern_count} patterns · "
        f"{quick_win_count} quick wins"
    )
    if _use_rich():
        from rich.console import Console
        from rich.text import Text

        t = Text()
        t.append("✓ Bootstrap complete!", style="bold green")
        t.append(
            f"  Total: {elapsed:.1f}s · "
            f"{pattern_count} patterns · "
            f"{quick_win_count} quick wins",
            style="dim",
        )
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=72)
        console.print(t)
        return buf.getvalue().rstrip()
    return line


def format_output_files(paths: List[str]) -> str:
    """Format output files list."""
    lines = ["Output files:"]
    for p in paths:
        lines.append(f"  {p}")

    if _use_rich():
        from rich.console import Console
        from rich.text import Text

        t = Text()
        t.append("Output files:\n", style="bold")
        for p in paths:
            t.append(f"  {p}\n", style="cyan")
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=72)
        console.print(t, end="")
        return buf.getvalue().rstrip()
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# QUICK WINS INLINE OUTPUT (≤20 lines)
# ═══════════════════════════════════════════════════════


# HC-AI | ticket: MEM-M1-11
def format_quick_wins_inline(
    result: "QuickWinsResult",
    max_lines: int = 20,
) -> str:
    """Format Quick Wins for inline CLI display after bootstrap.

    Design: ≤20 lines, 3 sections, confidence color-coded.
    """
    lines: List[str] = []

    # Section header
    lines.append("━━ Quick Wins " + "━" * 44)
    lines.append("")

    # Structure insights
    structure = result.structure_insights
    if structure:
        lines.append(f"STRUCTURE ({len(structure)} insights)")
        for i in structure:
            lines.append(_format_insight_inline(i))
        lines.append("")

    # Pattern insights
    pats = result.pattern_insights
    if pats:
        lines.append(f"PATTERNS ({len(pats)} insights)")
        for i in pats:
            lines.append(_format_insight_inline(i))
        lines.append("")

    # Risk insights
    risks = result.risk_insights
    if risks:
        lines.append(f"RISKS ({len(risks)} insights)")
        for i in risks:
            lines.append(_format_insight_inline(i))
        lines.append("")

    # Footer
    lines.append("━" * 59)
    if result.output_path:
        lines.append(f"Full details: {result.output_path}")

    # Truncate to max_lines
    if len(lines) > max_lines:
        lines = lines[: max_lines - 1]
        lines.append(
            f"  ... ({result.insight_count} total insights " f"in quick-wins.md)"
        )

    plain = "\n".join(lines)

    if _use_rich():
        return _format_quick_wins_rich(result, max_lines)

    return plain


def _format_insight_inline(insight: "Insight") -> str:
    """Format a single insight as a plain-text inline line."""
    conf = f"{insight.confidence:.0f}%"
    return (
        f"  {insight.number}. {insight.title} — " f"{insight.description[:50]}  {conf}"
    )


def _format_quick_wins_rich(
    result: "QuickWinsResult",
    max_lines: int,
) -> str:
    """Format Quick Wins with rich colors."""
    from rich.console import Console
    from rich.text import Text

    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=72)

    # Header
    header = Text("━━ Quick Wins " + "━" * 44, style="bold")
    console.print(header)
    console.print()

    line_count = 2

    # Sections
    for section_name, insights, label_style in [
        ("STRUCTURE", result.structure_insights, "bold"),
        ("PATTERNS", result.pattern_insights, "bold"),
        ("RISKS", result.risk_insights, "bold red"),
    ]:
        if not insights:
            continue
        if line_count >= max_lines - 2:
            break
        t = Text()
        t.append(
            f"{section_name} ({len(insights)} insights)",
            style=label_style,
        )
        console.print(t)
        line_count += 1

        for i in insights:
            if line_count >= max_lines - 2:
                break
            t = Text()
            # Number
            num_style = "red" if i.category == "risks" else "green"
            t.append(f"  {i.number}. ", style=num_style)
            # Title
            t.append(i.title, style="bold")
            # Description (truncated)
            desc = i.description[:45]
            t.append(f" — {desc}", style="dim")
            # Confidence
            conf_style = _confidence_style(i.confidence)
            t.append(f"  {i.confidence:.0f}%", style=conf_style)
            console.print(t)
            line_count += 1

        console.print()
        line_count += 1

    # Footer
    footer = Text("━" * 59, style="dim")
    console.print(footer)
    if result.output_path:
        t = Text()
        t.append("Full details: ", style="dim")
        t.append(result.output_path, style="cyan")
        console.print(t)

    return buf.getvalue().rstrip()


def _confidence_style(confidence: float) -> str:
    """Map confidence to rich style."""
    if confidence >= 80:
        return "green"
    elif confidence >= 60:
        return "yellow"
    return "red"


# ═══════════════════════════════════════════════════════
# VAULT SUMMARY OUTPUT
# ═══════════════════════════════════════════════════════


# HC-AI | ticket: MEM-M1-11
def format_vault_summary(
    vault_path: str = ".knowledge-memory/",
    schema_version: int = 1,
    verticals: int = 1,
    vertical_name: str = "codebase",
    pattern_count: int = 0,
    pattern_breakdown: str = "",
    snapshot_count: int = 0,
    snapshot_limit: int = 5,
    quick_win_count: int = 0,
    quick_win_breakdown: str = "",
    last_bootstrap: str = "",
    duration: float = 0.0,
    node_count: int = 0,
    edge_count: int = 0,
    file_count: int = 0,
) -> str:
    """Format vault summary for `codebase-memory summary` command.

    Design ref: kmp-M1-design.html Screen E.
    """
    lines: List[str] = []
    lines.append("Knowledge Memory — Vault Summary")
    lines.append("")
    lines.append(f"  Vault:      {vault_path}")
    lines.append(f"  Schema:     v{schema_version}")
    lines.append(f"  Verticals:  {verticals} ({vertical_name})")
    lines.append("")
    pat_detail = f" ({pattern_breakdown})" if pattern_breakdown else ""
    lines.append(f"  Patterns:   {pattern_count}{pat_detail}")
    lines.append(
        f"  Snapshots:  {snapshot_count}/{snapshot_limit} " f"(rotation limit)"
    )
    qw_detail = f" ({quick_win_breakdown})" if quick_win_breakdown else ""
    lines.append(f"  Quick Wins: {quick_win_count}{qw_detail}")
    lines.append("")
    if last_bootstrap:
        lines.append(f"  Last bootstrap: {last_bootstrap}")
    if duration > 0:
        lines.append(f"  Duration:       {duration:.1f}s")
    if node_count > 0:
        corpus = (
            f"  Corpus:         "
            f"{node_count:,} nodes · "
            f"{edge_count:,} edges · "
            f"{file_count} files"
        )
        lines.append(corpus)
    lines.append("")
    lines.append("Run codebase-memory bootstrap to refresh patterns.")

    plain = "\n".join(lines)

    if _use_rich():
        return _format_vault_summary_rich(
            vault_path=vault_path,
            schema_version=schema_version,
            verticals=verticals,
            vertical_name=vertical_name,
            pattern_count=pattern_count,
            pattern_breakdown=pattern_breakdown,
            snapshot_count=snapshot_count,
            snapshot_limit=snapshot_limit,
            quick_win_count=quick_win_count,
            quick_win_breakdown=quick_win_breakdown,
            last_bootstrap=last_bootstrap,
            duration=duration,
            node_count=node_count,
            edge_count=edge_count,
            file_count=file_count,
        )

    return plain


def _format_vault_summary_rich(**kwargs) -> str:  # type: ignore[no-untyped-def]
    """Render vault summary with rich styles."""
    from rich.console import Console
    from rich.text import Text

    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=72)

    # Header
    console.print(
        Text(
            "Knowledge Memory — Vault Summary",
            style="bold",
        )
    )
    console.print()

    # Vault info
    _kv(console, "Vault:", kwargs["vault_path"], "cyan")
    _kv(console, "Schema:", f"v{kwargs['schema_version']}")
    _kv(
        console,
        "Verticals:",
        f"{kwargs['verticals']} ({kwargs['vertical_name']})",
        "dim",
    )
    console.print()

    # Patterns
    pat_detail = kwargs.get("pattern_breakdown", "")
    pat_str = str(kwargs["pattern_count"])
    if pat_detail:
        pat_str += f" ({pat_detail})"
    _kv(console, "Patterns:", pat_str)

    snap = f"{kwargs['snapshot_count']}/{kwargs['snapshot_limit']}" f" (rotation limit)"
    _kv(console, "Snapshots:", snap, "dim")

    qw_detail = kwargs.get("quick_win_breakdown", "")
    qw_str = str(kwargs["quick_win_count"])
    if qw_detail:
        qw_str += f" ({qw_detail})"
    _kv(console, "Quick Wins:", qw_str)
    console.print()

    # Bootstrap info
    if kwargs.get("last_bootstrap"):
        _kv(
            console,
            "Last bootstrap:",
            kwargs["last_bootstrap"],
            "dim",
        )
    if kwargs.get("duration", 0) > 0:
        _kv(
            console,
            "Duration:",
            f"{kwargs['duration']:.1f}s",
        )
    if kwargs.get("node_count", 0) > 0:
        corpus = (
            f"{kwargs['node_count']:,} nodes · "
            f"{kwargs['edge_count']:,} edges · "
            f"{kwargs['file_count']} files"
        )
        _kv(console, "Corpus:", corpus)
    console.print()

    # Footer hint
    t = Text()
    t.append("Run ", style="dim")
    t.append("codebase-memory bootstrap", style="bold cyan")
    t.append(" to refresh patterns.", style="dim")
    console.print(t)

    return buf.getvalue().rstrip()


def _kv(
    console,  # type: ignore[no-untyped-def]
    key: str,
    value: str,
    value_style: str = "",
) -> None:
    """Print a key-value pair with alignment."""
    from rich.text import Text

    t = Text()
    t.append(f"  {key:<16}", style="bold")
    t.append(value, style=value_style)
    console.print(t)
