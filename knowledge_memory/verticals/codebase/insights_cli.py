# HC-AI | ticket: MEM-M3-11
"""Insights CLI command — weekly/on-demand insights report.

Design ref: kmp-M3-design.html Screen E.
Outputs: terminal summary or HTML dashboard export.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.telemetry.roi import ROICalculator, ROIMetrics
from knowledge_memory.verticals.codebase.insights_html import export_insights_html


@dataclass
class InsightsResult:
    """Result of generating insights report."""

    total_patterns: int = 0
    total_learners: int = 0
    avg_confidence: float = 0.0
    high_confidence: int = 0
    low_confidence: int = 0
    roi: ROIMetrics | None = None
    html_path: str = ""
    elapsed_ms: float = 0.0
    error: str = ""


class InsightsEngine:
    """Generate insights reports from vault patterns + telemetry.

    Supports two output modes:
    - Terminal: summary stats + ROI
    - HTML: full interactive dashboard export
    """

    def __init__(self, hourly_rate: float = 30.0) -> None:
        self._hourly_rate = hourly_rate

    def generate(
        self,
        patterns: list[Pattern],
        onboarding_reports: int = 0,
        ask_queries: int = 0,
        total_token_cost: float = 0.0,
        total_llm_calls: int = 0,
        usage_stats: dict[str, Any] | None = None,
        output_html: str = "",
        project_name: str = "Codebase",
    ) -> InsightsResult:
        """Generate insights report.

        Args:
            patterns: Committed patterns from vault.
            onboarding_reports: Count of onboard reports generated.
            ask_queries: Count of ask/why/impact queries.
            total_token_cost: Total LLM API cost.
            total_llm_calls: Total LLM calls.
            usage_stats: LLM usage by provider.
            output_html: Path to write HTML dashboard (empty = skip).
            project_name: Project name for HTML title.

        Returns:
            InsightsResult with stats and optional HTML path.
        """
        start = time.monotonic()

        # Compute stats
        categories = {p.category for p in patterns}
        avg_conf = (
            sum(p.confidence for p in patterns) / len(patterns) if patterns else 0.0
        )
        high = sum(1 for p in patterns if p.confidence >= 80)
        low = sum(1 for p in patterns if p.confidence < 70)

        # ROI calculation
        calc = ROICalculator(hourly_rate=self._hourly_rate)
        roi = calc.calculate(
            onboarding_reports=onboarding_reports,
            ask_queries=ask_queries,
            total_token_cost=total_token_cost,
            total_llm_calls=total_llm_calls,
        )

        # HTML export
        html_path = ""
        if output_html:
            html = export_insights_html(
                patterns=patterns,
                roi=roi,
                usage_stats=usage_stats,
                project_name=project_name,
            )
            Path(output_html).parent.mkdir(parents=True, exist_ok=True)
            Path(output_html).write_text(html, encoding="utf-8")
            html_path = output_html

        elapsed = (time.monotonic() - start) * 1000

        return InsightsResult(
            total_patterns=len(patterns),
            total_learners=len(categories),
            avg_confidence=avg_conf,
            high_confidence=high,
            low_confidence=low,
            roi=roi,
            html_path=html_path,
            elapsed_ms=elapsed,
        )


def format_insights_result(result: InsightsResult) -> str:
    """Format InsightsResult for terminal output.

    Design ref: kmp-M3-design.html Screen E.
    """
    lines = [
        "Knowledge Memory \u2014 Insights Dashboard",
        "",
    ]

    if result.error:
        lines.append(f"\u2717 Error: {result.error}")
        return "\n".join(lines)

    lines.append("\u25b6 Collecting metrics...")
    lines.append(
        f"  \u2713 Patterns: {result.total_patterns} "
        f"({result.total_learners} learners)"
    )
    lines.append(f"  \u2713 Avg confidence: {result.avg_confidence:.0f}%")
    lines.append(f"  \u2713 High confidence (\u226580%): {result.high_confidence}")
    lines.append(f"  \u2713 Low confidence (<70%): {result.low_confidence}")

    if result.roi:
        lines.append(f"  \u2713 ROI estimate: ${result.roi.roi_value:,.2f}")

    if result.html_path:
        lines.append("")
        lines.append("\u2713 Dashboard exported!")
        lines.append(f"  {result.html_path}")
        lines.append("")
        lines.append("Open in browser to view interactive charts.")

    return "\n".join(lines)
