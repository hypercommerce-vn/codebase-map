# HC-AI | ticket: MEM-M3-09
"""ROI calculator — estimate return on investment from KMP usage.

Design ref: kmp-M3-design.html Screen F.
Formula: ROI = (hours_saved * hourly_rate) - token_cost
Default hourly_rate: $30 (configurable in config.yaml).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ROIMetrics:
    """ROI calculation result."""

    onboarding_reports: int = 0
    hours_saved_estimate: float = 0.0
    hourly_rate: float = 30.0
    total_token_cost: float = 0.0
    total_llm_calls: int = 0
    roi_value: float = 0.0
    roi_multiple: float = 0.0

    def compute(self) -> None:
        """Compute ROI value and multiple."""
        gross_savings = self.hours_saved_estimate * self.hourly_rate
        self.roi_value = gross_savings - self.total_token_cost
        if self.total_token_cost > 0:
            self.roi_multiple = gross_savings / self.total_token_cost
        else:
            self.roi_multiple = 0.0


class ROICalculator:
    """Calculate ROI from telemetry + cost data.

    Combines:
    - Onboarding time saved (estimated from report count)
    - LLM token cost (from CostTracker)
    - Configurable hourly rate
    """

    # HC-AI | ticket: MEM-M3-09
    # Estimated hours saved per onboarding report
    HOURS_PER_REPORT = 2.5
    # Estimated hours saved per ask/why/impact query
    HOURS_PER_QUERY = 0.1

    def __init__(self, hourly_rate: float = 30.0) -> None:
        self._hourly_rate = hourly_rate

    def calculate(
        self,
        onboarding_reports: int = 0,
        ask_queries: int = 0,
        total_token_cost: float = 0.0,
        total_llm_calls: int = 0,
    ) -> ROIMetrics:
        """Calculate ROI metrics.

        Args:
            onboarding_reports: Number of onboarding reports generated.
            ask_queries: Number of ask/why/impact queries run.
            total_token_cost: Total LLM API cost in USD.
            total_llm_calls: Total number of LLM calls.

        Returns:
            ROIMetrics with computed roi_value and roi_multiple.
        """
        hours_saved = (
            onboarding_reports * self.HOURS_PER_REPORT
            + ask_queries * self.HOURS_PER_QUERY
        )

        metrics = ROIMetrics(
            onboarding_reports=onboarding_reports,
            hours_saved_estimate=hours_saved,
            hourly_rate=self._hourly_rate,
            total_token_cost=total_token_cost,
            total_llm_calls=total_llm_calls,
        )
        metrics.compute()
        return metrics


def format_roi(metrics: ROIMetrics) -> str:
    """Format ROI metrics for terminal output.

    Design ref: kmp-M3-design.html Screen F.
    """
    lines = [
        "Knowledge Memory \u2014 ROI Report",
        "",
    ]

    lines.append(f"  {'Metric':<30} {'Value':>10}")
    lines.append(f"  {'Onboarding reports':<30} {metrics.onboarding_reports:>10}")
    lines.append(
        f"  {'New dev time saved (est.)':<30} " f"{metrics.hours_saved_estimate:>9.1f}h"
    )
    lines.append(f"  {'LLM token cost':<30} ${metrics.total_token_cost:>9.3f}")
    lines.append(f"  {'Hourly rate (config)':<30} " f"${metrics.hourly_rate:>8.0f}/h")

    sep = "  " + "\u2501" * 42
    lines.append(sep)
    lines.append(f"  {'Estimated ROI:':<30} ${metrics.roi_value:>9.2f}")
    if metrics.roi_multiple > 0:
        lines.append(f"  {'Return multiple:':<30} " f"{metrics.roi_multiple:>9,.0f}x")

    lines.append("")
    lines.append("  All data stored locally. No cloud sync. Privacy-safe.")

    return "\n".join(lines)
