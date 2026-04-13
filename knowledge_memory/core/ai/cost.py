# HC-AI | ticket: MEM-M2-11
"""Cost calculator + usage tracking for LLM providers.

Design ref: kmp-M2-design.html Screen I (cost tracking).
Tracks per-query and cumulative usage across providers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class UsageEntry:
    """A single LLM usage record."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    query_preview: str = ""
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class UsageSummary:
    """Aggregated usage across providers."""

    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    by_provider: dict[str, ProviderUsage] = field(default_factory=dict)
    most_expensive_query: str = ""
    most_expensive_cost: float = 0.0


@dataclass
class ProviderUsage:
    """Usage for a single provider."""

    provider: str
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0


# HC-AI | ticket: MEM-M2-11
class CostTracker:
    """Track LLM usage and costs across providers.

    Thread-safe for single-threaded CLI usage.
    Usage logged in memory; optionally persisted to vault.
    """

    def __init__(self) -> None:
        self._entries: list[UsageEntry] = []

    def record(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency_ms: float = 0.0,
        query_preview: str = "",
    ) -> UsageEntry:
        """Record a single LLM call."""
        entry = UsageEntry(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            latency_ms=latency_ms,
            query_preview=query_preview[:80],
        )
        self._entries.append(entry)
        return entry

    def summary(self) -> UsageSummary:
        """Compute aggregated usage summary."""
        s = UsageSummary()

        for e in self._entries:
            s.total_calls += 1
            s.total_input_tokens += e.input_tokens
            s.total_output_tokens += e.output_tokens
            s.total_cost += e.cost

            if e.provider not in s.by_provider:
                s.by_provider[e.provider] = ProviderUsage(provider=e.provider)
            p = s.by_provider[e.provider]
            p.calls += 1
            p.input_tokens += e.input_tokens
            p.output_tokens += e.output_tokens
            p.cost += e.cost

            if e.cost > s.most_expensive_cost:
                s.most_expensive_cost = e.cost
                s.most_expensive_query = e.query_preview

        return s

    @property
    def entries(self) -> list[UsageEntry]:
        """All recorded entries."""
        return list(self._entries)

    def clear(self) -> None:
        """Clear all usage records."""
        self._entries.clear()


def format_usage_summary(summary: UsageSummary) -> str:
    """Format UsageSummary for terminal output.

    Design ref: kmp-M2-design.html Screen I.
    """
    lines: list[str] = []
    lines.append("Knowledge Memory \u2014 LLM Usage Summary")
    lines.append("")

    if summary.total_calls == 0:
        lines.append("No LLM calls recorded yet.")
        return "\n".join(lines)

    # Header
    header = (
        f"  {'Provider':<16} {'Calls':>6}  "
        f"{'Tokens In':>10}  {'Tokens Out':>10}  {'Cost':>8}"
    )
    lines.append(header)

    for p in sorted(summary.by_provider.values(), key=lambda x: -x.cost):
        lines.append(
            f"  {p.provider:<16} {p.calls:>6}  "
            f"{p.input_tokens:>10,}  {p.output_tokens:>10,}  "
            f"${p.cost:>7.3f}"
        )

    sep = "  " + "\u2501" * 60
    lines.append(sep)
    lines.append(
        f"  {'Total':<16} {summary.total_calls:>6}  "
        f"{summary.total_input_tokens:>10,}  "
        f"{summary.total_output_tokens:>10,}  "
        f"${summary.total_cost:>7.3f}"
    )
    lines.append("")

    if summary.total_calls > 0:
        avg = summary.total_cost / summary.total_calls
        lines.append(f"  Avg ${avg:.3f}/query")

    if summary.most_expensive_query:
        lines.append(
            f'  Most expensive: "{summary.most_expensive_query}" '
            f"(${summary.most_expensive_cost:.3f})"
        )

    return "\n".join(lines)
