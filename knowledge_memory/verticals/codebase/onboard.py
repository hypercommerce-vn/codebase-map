# HC-AI | ticket: MEM-M3-01
"""Onboard command — generate personalized 8-chapter onboarding report.

Design ref: kmp-M3-design.html Screen A+B.
Reads vault patterns → personalizes template → outputs Markdown report.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from knowledge_memory.core.learners.pattern import Pattern

logger = logging.getLogger("codebase-memory.onboard")


@dataclass
class ChapterResult:
    """Result of generating a single chapter."""

    number: int
    title: str
    key_metric: str
    content: str
    pattern_count: int = 0


@dataclass
class OnboardResult:
    """Result of full onboarding report generation."""

    chapters: list[ChapterResult]
    total_patterns: int = 0
    total_learners: int = 0
    total_nodes: int = 0
    elapsed_seconds: float = 0.0
    output_path: str = ""
    error: str = ""

    @property
    def success(self) -> bool:
        return len(self.chapters) > 0 and not self.error


def _ch1_overview(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 1: Project Overview."""
    nodes = stats.get("total_nodes", 0)
    domains = stats.get("domains", 0)
    metric = f"{domains} domains, {nodes} functions"

    lines = [
        f"This project has **{nodes} functions** across **{domains} domains**.",
        "",
    ]

    # Find layer distribution pattern
    for p in patterns:
        meta = p.metadata if isinstance(p.metadata, dict) else {}
        if "layer" in p.category.lower():
            desc = meta.get("description", "")
            if desc:
                lines.append(f"**Architecture:** {desc}")
                break

    return metric, "\n".join(lines)


def _ch2_naming(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 2: Naming Conventions."""
    lines = []
    metric = "See patterns"

    for p in patterns:
        meta = p.metadata if isinstance(p.metadata, dict) else {}
        name_lower = p.name.lower()
        if "case" in name_lower or "naming" in name_lower:
            desc = meta.get("description", p.name)
            conf = p.confidence
            lines.append(f"- **{p.name}** — {desc} (Confidence: {conf:.0f}%)")
            if "compliance" in name_lower:
                metric = f"{desc}"
        elif "prefix" in name_lower or "crud" in name_lower:
            desc = meta.get("description", p.name)
            lines.append(f"- **{p.name}** — {desc} (Confidence: {p.confidence:.0f}%)")

    if not lines:
        lines.append(
            "No naming patterns detected yet. Run `bootstrap` with NamingLearner."
        )

    return metric, "\n".join(lines)


def _ch3_layers(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 3: Architecture Layers."""
    lines = []
    metric = "Layer analysis"

    for p in patterns:
        meta = p.metadata if isinstance(p.metadata, dict) else {}
        if p.category == "layer":
            desc = meta.get("description", p.name)
            lines.append(f"- **{p.name}** — {desc} (Confidence: {p.confidence:.0f}%)")
            if "dominant" in p.name.lower() or "service" in p.name.lower():
                metric = desc

    if not lines:
        lines.append("No layer patterns detected. Run `bootstrap` with LayerLearner.")

    return metric, "\n".join(lines)


def _ch4_errors(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 4: Error Handling Patterns."""
    lines = []
    metric = "Error handling analysis"

    for p in patterns:
        meta = p.metadata if isinstance(p.metadata, dict) else {}
        if p.category == "error_handling":
            desc = meta.get("description", p.name)
            lines.append(f"- **{p.name}** — {desc} (Confidence: {p.confidence:.0f}%)")
            if "coverage" in p.name.lower():
                pct = meta.get("coverage_pct", 0)
                metric = f"try/except {pct:.0f}%"

    if not lines:
        lines.append(
            "No error handling patterns detected. "
            "Run `bootstrap` with ErrorHandlingLearner (M3)."
        )

    return metric, "\n".join(lines)


def _ch5_testing(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 5: Testing Patterns."""
    lines = []
    metric = "Test analysis"

    for p in patterns:
        if p.category == "test_patterns":
            meta = p.metadata if isinstance(p.metadata, dict) else {}
            desc = meta.get("description", p.name)
            lines.append(f"- **{p.name}** — {desc} (Confidence: {p.confidence:.0f}%)")

    if not lines:
        lines.append(
            "No test patterns detected. "
            "Run `bootstrap` with TestPatternsLearner (M3)."
        )

    return metric, "\n".join(lines)


def _ch6_di(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 6: Dependency Injection."""
    lines = []
    metric = "DI analysis"

    for p in patterns:
        if p.category == "dependency_injection":
            meta = p.metadata if isinstance(p.metadata, dict) else {}
            desc = meta.get("description", p.name)
            lines.append(f"- **{p.name}** — {desc} (Confidence: {p.confidence:.0f}%)")

    if not lines:
        lines.append(
            "No DI patterns detected. "
            "Run `bootstrap` with DependencyInjectionLearner (M3)."
        )

    return metric, "\n".join(lines)


def _ch7_ownership(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 7: Code Ownership."""
    lines = []
    metric = "Ownership analysis"

    for p in patterns:
        if p.category == "ownership":
            meta = p.metadata if isinstance(p.metadata, dict) else {}
            desc = meta.get("description", p.name)
            lines.append(f"- **{p.name}** — {desc} (Confidence: {p.confidence:.0f}%)")
            if "bus" in p.name.lower() or "single" in p.name.lower():
                metric = desc

    if not lines:
        lines.append(
            "No ownership patterns detected. Run `bootstrap` with GitOwnershipLearner."
        )

    return metric, "\n".join(lines)


def _ch8_glossary(patterns: list[Pattern], stats: dict) -> tuple[str, str]:
    """Chapter 8: Domain Glossary."""
    terms = stats.get("glossary_terms", [])
    metric = f"{len(terms)} business terms" if terms else "Glossary pending"

    if terms:
        lines = ["| Term | Domain | Evidence |", "|------|--------|----------|"]
        for t in terms[:20]:
            lines.append(
                f"| {t.get('term', '')} | {t.get('domain', '')} | "
                f"{t.get('evidence', 0)} references |"
            )
        if len(terms) > 20:
            lines.append(f"| ... | | {len(terms) - 20} more |")
    else:
        lines = [
            "No glossary data yet. "
            "Run `codebase-memory glossary` (M3) to extract terms."
        ]

    return metric, "\n".join(lines)


# Fix: define _CHAPTERS after all template functions
_CHAPTERS = [
    {
        "number": 1,
        "title": "Project Overview",
        "categories": ["layer", "structure"],
        "template": _ch1_overview,
    },
    {
        "number": 2,
        "title": "Naming Conventions",
        "categories": ["naming"],
        "template": _ch2_naming,
    },
    {
        "number": 3,
        "title": "Architecture Layers",
        "categories": ["layer"],
        "template": _ch3_layers,
    },
    {
        "number": 4,
        "title": "Error Handling Patterns",
        "categories": ["error_handling"],
        "template": _ch4_errors,
    },
    {
        "number": 5,
        "title": "Testing Patterns",
        "categories": ["test_patterns"],
        "template": _ch5_testing,
    },
    {
        "number": 6,
        "title": "Dependency Injection",
        "categories": ["dependency_injection"],
        "template": _ch6_di,
    },
    {
        "number": 7,
        "title": "Code Ownership",
        "categories": ["ownership"],
        "template": _ch7_ownership,
    },
    {
        "number": 8,
        "title": "Domain Glossary",
        "categories": [],
        "template": _ch8_glossary,
    },
]


class OnboardEngine:
    """Generate personalized onboarding report from vault patterns."""

    def __init__(self) -> None:
        self._patterns: list[Pattern] = []
        self._stats: dict[str, Any] = {}

    def load_data(
        self,
        patterns: list[Pattern],
        stats: dict[str, Any] | None = None,
    ) -> None:
        """Load patterns and stats for report generation."""
        self._patterns = patterns
        self._stats = stats or {}

    def generate(self, output_dir: str = "") -> OnboardResult:
        """Generate 8-chapter onboarding report."""
        start = time.monotonic()
        chapters: list[ChapterResult] = []

        for ch_def in _CHAPTERS:
            # Filter patterns for this chapter's categories
            categories = ch_def["categories"]
            if categories:
                ch_patterns = [p for p in self._patterns if p.category in categories]
            else:
                ch_patterns = self._patterns

            # Generate chapter content
            template_fn = ch_def["template"]
            metric, content = template_fn(ch_patterns, self._stats)

            chapters.append(
                ChapterResult(
                    number=ch_def["number"],
                    title=ch_def["title"],
                    key_metric=metric,
                    content=content,
                    pattern_count=len(ch_patterns),
                )
            )

        elapsed = time.monotonic() - start

        # Build full report
        output_path = ""
        if output_dir:
            output_path = str(Path(output_dir) / "onboarding-report.md")
            report_md = self._render_report(chapters)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(report_md, encoding="utf-8")

        learner_categories = {p.category for p in self._patterns}

        return OnboardResult(
            chapters=chapters,
            total_patterns=len(self._patterns),
            total_learners=len(learner_categories),
            total_nodes=self._stats.get("total_nodes", 0),
            elapsed_seconds=elapsed,
            output_path=output_path,
        )

    def _render_report(self, chapters: list[ChapterResult]) -> str:
        """Render full Markdown report."""
        lines = [
            "# Onboarding Guide",
            "",
            "> Auto-generated by KMP v1.0.0",
            f"> Patterns: {len(self._patterns)} "
            f"| Learners: {len({p.category for p in self._patterns})}",
            "",
            "---",
            "",
        ]

        for ch in chapters:
            lines.append(f"## {ch.number}. {ch.title}")
            lines.append("")
            lines.append(ch.content)
            lines.append("")

        return "\n".join(lines)


def format_onboard_result(result: OnboardResult) -> str:
    """Format OnboardResult for terminal output.

    Design ref: kmp-M3-design.html Screen A.
    """
    lines: list[str] = []
    lines.append("Knowledge Memory \u2014 Onboarding Report Generator")
    lines.append(
        f"Vault: {result.total_patterns} patterns "
        f"\u00b7 {result.total_learners} learners "
        f"\u00b7 {result.total_nodes} nodes"
    )
    lines.append("")

    if result.error:
        lines.append(f"\u2717 Error: {result.error}")
        return "\n".join(lines)

    lines.append("\u25b6 Generating chapters...")
    for ch in result.chapters:
        lines.append(f"  \u2713 Ch.{ch.number}: {ch.title}  " f"\u2014 {ch.key_metric}")

    lines.append("")
    sep = "\u2501" * 50
    lines.append(sep)
    lines.append(
        f"\u2713 Onboarding report generated!  "
        f"{len(result.chapters)} chapters \u00b7 {result.elapsed_seconds:.1f}s"
    )

    if result.output_path:
        lines.append("")
        lines.append(f"Output: {result.output_path}")

    return "\n".join(lines)
