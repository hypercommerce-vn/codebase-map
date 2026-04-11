# HC-AI | ticket: MEM-M1-10
"""Quick Wins generator — 10 actionable insights from committed patterns.

Fixed ratio: 5 structure + 3 patterns + 2 risks.
Each insight: title, description, evidence, confidence, action.
Deterministic: same codebase → same quick wins.

Design ref: kmp-M1-design.html Screen C + D.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from knowledge_memory.core.learners.pattern import Pattern

if TYPE_CHECKING:
    from knowledge_memory.verticals.codebase.vault import CodebaseVault

# HC-AI | ticket: MEM-M1-10
# Fixed ratio per design decision D-M1-02
_STRUCTURE_COUNT = 5
_PATTERNS_COUNT = 3
_RISKS_COUNT = 2
_TOTAL_INSIGHTS = 10

# Confidence thresholds
_NEEDS_REVIEW_THRESHOLD = 60.0
_GREEN_THRESHOLD = 80.0


class Insight:
    """A single Quick Win insight."""

    def __init__(
        self,
        number: int,
        title: str,
        description: str,
        evidence: str,
        confidence: float,
        action: str,
        category: str,
        source_pattern: str = "",
    ) -> None:
        self.number = number
        self.title = title
        self.description = description
        self.evidence = evidence
        self.confidence = confidence
        self.action = action
        self.category = category  # "structure", "patterns", "risks"
        self.source_pattern = source_pattern
        self.needs_review = confidence < _NEEDS_REVIEW_THRESHOLD

    @property
    def confidence_label(self) -> str:
        """Color label for confidence score."""
        if self.confidence >= _GREEN_THRESHOLD:
            return "green"
        elif self.confidence >= _NEEDS_REVIEW_THRESHOLD:
            return "yellow"
        return "red"


class QuickWinsResult:
    """Result of Quick Wins generation."""

    def __init__(self) -> None:
        self.insights: List[Insight] = []
        self.total_patterns: int = 0
        self.output_path: Optional[str] = None

    @property
    def structure_insights(self) -> List[Insight]:
        return [i for i in self.insights if i.category == "structure"]

    @property
    def pattern_insights(self) -> List[Insight]:
        return [i for i in self.insights if i.category == "patterns"]

    @property
    def risk_insights(self) -> List[Insight]:
        return [i for i in self.insights if i.category == "risks"]

    @property
    def insight_count(self) -> int:
        return len(self.insights)


# HC-AI | ticket: MEM-M1-10
def generate_quick_wins(
    vault: "CodebaseVault",
    confidence_threshold: float = 60.0,
    output_path: Optional[str] = None,
) -> QuickWinsResult:
    """Generate 10 Quick Win insights from vault patterns.

    Fixed ratio: 5 structure + 3 patterns + 2 risks.
    Deterministic: sorted by confidence, no random sampling.

    Args:
        vault: CodebaseVault with committed patterns.
        confidence_threshold: Minimum confidence to include (60%).
        output_path: Custom output path. Default: vault verticals dir.

    Returns:
        QuickWinsResult with insights and metadata.
    """
    all_patterns = vault.query_patterns()
    filtered = [p for p in all_patterns if p.confidence >= confidence_threshold]

    result = QuickWinsResult()
    result.total_patterns = len(filtered)

    # Extract insights from patterns by category
    structure_candidates = _extract_structure_insights(filtered)
    pattern_candidates = _extract_pattern_insights(filtered)
    risk_candidates = _extract_risk_insights(filtered)

    # Take fixed ratio: 5+3+2
    selected_structure = structure_candidates[:_STRUCTURE_COUNT]
    selected_patterns = pattern_candidates[:_PATTERNS_COUNT]
    selected_risks = risk_candidates[:_RISKS_COUNT]

    # Number sequentially
    number = 1
    for insight in selected_structure:
        insight.number = number
        number += 1
    for insight in selected_patterns:
        insight.number = number
        number += 1
    for insight in selected_risks:
        insight.number = number
        number += 1

    result.insights = selected_structure + selected_patterns + selected_risks

    # Generate markdown and write to file
    md_content = _render_quick_wins_md(result)
    _write_output(vault, md_content, output_path)

    # Record output path
    if output_path:
        result.output_path = output_path
    elif vault.vault_dir:
        vert_dir = vault.vault_dir / "verticals" / "codebase"
        result.output_path = str(vert_dir / "quick-wins.md")

    return result


# HC-AI | ticket: MEM-M1-10
def _extract_structure_insights(
    patterns: List[Pattern],
) -> List[Insight]:
    """Extract structure insights from layer + naming patterns.

    Sources:
    - layers::distribution → dominant layer, layer counts
    - layers::domain_grouping → domain count, boundaries
    - layers::file_concentration → hotspot detection
    - layers::depth_analysis → nesting patterns
    - layers::compliance → layer compliance
    """
    insights: List[Insight] = []

    for p in patterns:
        meta = p.metadata

        if p.name == "layers::distribution" and "layer_pct" in meta:
            layer_pct = meta.get("layer_pct", {})
            total = meta.get("total", 0)
            recognized = meta.get("recognized_pct", 0)
            # Find dominant layer
            if layer_pct:
                dominant = max(
                    ((lyr, pct) for lyr, pct in layer_pct.items() if lyr != "unknown"),
                    key=lambda x: x[1],
                    default=("unknown", 0),
                )
                layer_counts = meta.get("layer_counts", {})
                dom_count = layer_counts.get(dominant[0], 0)
                insights.append(
                    Insight(
                        number=0,
                        title=f"{dominant[0].title()} Layer dominant",
                        description=(
                            f"{dominant[1]:.0f}% of nodes are "
                            f"{dominant[0]}-layer "
                            f"({dom_count} of {total} total)"
                        ),
                        evidence=f"{dominant[0]}/ directory",
                        confidence=p.confidence,
                        action=(
                            "No action needed — healthy pattern"
                            if recognized >= 80
                            else "Review unrecognized layers"
                        ),
                        category="structure",
                        source_pattern=p.name,
                    )
                )

        elif (
            p.name == "layers::domain_grouping"
            and "total_domains" in meta
            and "domains" in meta
        ):
            total_domains = meta.get("total_domains", 0)
            multi = meta.get("multi_layer_domains", 0)
            domains = meta.get("domains", [])
            domain_names = [d.get("domain", "") for d in domains[:7]]
            insights.append(
                Insight(
                    number=0,
                    title=f"{total_domains} domains detected",
                    description=(
                        f"{', '.join(domain_names)}"
                        f"{' — ' + str(multi) + ' multi-layer' if multi else ''}"
                    ),
                    evidence=(
                        domains[0].get("domain", "modules/") + "/"
                        if domains
                        else "modules/"
                    ),
                    confidence=p.confidence,
                    action=(
                        "Good domain boundaries"
                        if multi > 0
                        else "Consider structuring into domains"
                    ),
                    category="structure",
                    source_pattern=p.name,
                )
            )

        elif p.name == "layers::file_concentration" and "hotspot_dirs" in meta:
            hotspots = meta.get("hotspot_dirs", {})
            if hotspots:
                top_dir = max(hotspots.items(), key=lambda x: x[1])
                insights.append(
                    Insight(
                        number=0,
                        title=f"Hotspot directory: {top_dir[0]}",
                        description=(
                            f"{top_dir[1]} nodes concentrated " f"in {top_dir[0]}"
                        ),
                        evidence=top_dir[0],
                        confidence=p.confidence,
                        action="Consider splitting if >50 nodes",
                        category="structure",
                        source_pattern=p.name,
                    )
                )

        elif p.name == "layers::depth_analysis" and "depth_stats" in meta:
            stats = meta.get("depth_stats", {})
            if stats:
                deepest = max(
                    stats.items(),
                    key=lambda x: x[1].get("avg_depth", 0),
                )
                insights.append(
                    Insight(
                        number=0,
                        title=(f"Deep nesting in {deepest[0]} layer"),
                        description=(
                            f"Avg depth {deepest[1]['avg_depth']}, "
                            f"range {deepest[1]['min_depth']}-"
                            f"{deepest[1]['max_depth']} "
                            f"({deepest[1]['count']} files)"
                        ),
                        evidence=f"{deepest[0]}/ files",
                        confidence=p.confidence,
                        action="Review deeply nested modules",
                        category="structure",
                        source_pattern=p.name,
                    )
                )

        elif p.name == "layers::compliance" and "compliance_pct" in meta:
            compliance = meta.get("compliance_pct", 0)
            mismatches = meta.get("mismatch_count", 0)
            samples = meta.get("mismatched_samples", [])
            evidence_path = (
                samples[0].get("file_path", "codebase") if samples else "codebase"
            )
            insights.append(
                Insight(
                    number=0,
                    title=f"Layer compliance: {compliance:.0f}%",
                    description=(
                        f"{mismatches} files with mismatched " f"layer classification"
                        if mismatches > 0
                        else "All files match expected layers"
                    ),
                    evidence=evidence_path,
                    confidence=p.confidence,
                    action=(
                        "Review mismatched files"
                        if mismatches > 0
                        else "No action needed"
                    ),
                    category="structure",
                    source_pattern=p.name,
                )
            )

    # Sort by confidence descending (deterministic)
    insights.sort(key=lambda x: (-x.confidence, x.title))
    return insights


# HC-AI | ticket: MEM-M1-10
def _extract_pattern_insights(
    patterns: List[Pattern],
) -> List[Insight]:
    """Extract pattern insights from naming learner.

    Sources:
    - naming::*_snake_case / *_PascalCase → naming convention
    - naming::crud_prefix_pattern → CRUD coverage
    - naming::*_top_prefixes → prefix usage
    """
    insights: List[Insight] = []

    for p in patterns:
        meta = p.metadata

        if p.category == "naming" and "dominant_case" in meta:
            target = meta.get("target", "")
            dominant = meta.get("dominant_case", "")
            compliance = meta.get("compliance_pct", 0)
            violations = meta.get("violation_count", 0)
            violation_names = meta.get("violations", [])

            violation_str = ""
            if violations > 0 and violation_names:
                shown = violation_names[:3]
                violation_str = f" — {violations} violations: " f"{', '.join(shown)}"

            insights.append(
                Insight(
                    number=0,
                    title=(f"Naming convention: {dominant} " f"({target})"),
                    description=(f"{compliance:.1f}% compliance" f"{violation_str}"),
                    evidence="codebase-wide",
                    confidence=p.confidence,
                    action=(
                        "No action needed — consistent naming"
                        if compliance >= 95
                        else (f"Fix {violations} naming violations")
                    ),
                    category="patterns",
                    source_pattern=p.name,
                )
            )

        elif p.category == "naming" and (
            "crud_coverage_pct" in meta or "prefix_distribution" in meta
        ):
            coverage = meta.get("crud_coverage_pct", 0)
            dist = meta.get("prefix_distribution", {})
            prefix_str = ", ".join(f"{k} ({v})" for k, v in list(dist.items())[:4])
            insights.append(
                Insight(
                    number=0,
                    title="CRUD prefix pattern",
                    description=(
                        f"{coverage:.0f}% of service methods " f"follow CRUD naming"
                    ),
                    evidence=(
                        f"Prefixes: {prefix_str}" if prefix_str else "service methods"
                    ),
                    confidence=p.confidence,
                    action=(
                        "Good naming consistency"
                        if coverage >= 70
                        else "Standardize method prefixes"
                    ),
                    category="patterns",
                    source_pattern=p.name,
                )
            )

        elif p.category == "naming" and "top_prefixes" in meta:
            prefixes = meta.get("top_prefixes", {})
            total = meta.get("total_functions", 0)
            top_list = list(prefixes.items())[:5]
            prefix_str = ", ".join(f"{k} ({v})" for k, v in top_list)
            insights.append(
                Insight(
                    number=0,
                    title="Function prefix patterns",
                    description=(
                        f"Top prefixes across " f"{total} functions: {prefix_str}"
                    ),
                    evidence="codebase-wide",
                    confidence=p.confidence,
                    action="Document naming conventions",
                    category="patterns",
                    source_pattern=p.name,
                )
            )

    insights.sort(key=lambda x: (-x.confidence, x.title))
    return insights


# HC-AI | ticket: MEM-M1-10
def _extract_risk_insights(
    patterns: List[Pattern],
) -> List[Insight]:
    """Extract risk insights from ownership + layer patterns.

    Sources:
    - ownership::domain_bus_factor → bus factor risk
    - ownership::single_owner_files → concentration risk
    - ownership::knowledge_concentration → specialist risk
    """
    insights: List[Insight] = []

    for p in patterns:
        meta = p.metadata

        if p.name == "ownership::domain_bus_factor" and "risk_domains" in meta:
            risk_count = meta.get("risk_domain_count", 0)
            total = meta.get("total_domains", 0)
            risk_domains = meta.get("risk_domains", [])

            if risk_count > 0 and risk_domains:
                top_risk = risk_domains[0]
                insights.append(
                    Insight(
                        number=0,
                        title=(f"Bus factor risk: " f"{top_risk['domain']}"),
                        description=(
                            f"{top_risk['top_author']} owns "
                            f"{top_risk['top_author_pct']:.0f}% "
                            f"of {top_risk['file_count']} files "
                            f"— bus factor = 1"
                        ),
                        evidence=(f"{top_risk['domain']}/ directory"),
                        confidence=p.confidence,
                        action=("Pair program or cross-train " "on this domain"),
                        category="risks",
                        source_pattern=p.name,
                    )
                )
            elif risk_count == 0:
                insights.append(
                    Insight(
                        number=0,
                        title="Bus factor healthy",
                        description=(f"All {total} domains have " f"bus factor >= 2"),
                        evidence="codebase-wide",
                        confidence=p.confidence,
                        action="No action needed",
                        category="risks",
                        source_pattern=p.name,
                    )
                )

        elif p.name == "ownership::single_owner_files" and "single_owner_count" in meta:
            single = meta.get("single_owner_count", 0)
            total = meta.get("total_files", 0)
            pct = meta.get("single_owner_pct", 0)
            top_files = meta.get("top_single_owner_files", [])

            if single > 0 and top_files:
                top = top_files[0]
                insights.append(
                    Insight(
                        number=0,
                        title=(f"Single owner risk: " f"{single} files"),
                        description=(
                            f"{pct:.0f}% of files "
                            f"({single}/{total}) have a "
                            f"single dominant author"
                        ),
                        evidence=top.get("file", ""),
                        confidence=p.confidence,
                        action=("Increase code review coverage"),
                        category="risks",
                        source_pattern=p.name,
                    )
                )

        elif (
            p.name == "ownership::knowledge_concentration"
            and "specialist_count" in meta
        ):
            specialists = meta.get("specialist_count", 0)
            total_authors = meta.get("total_authors", 0)
            pct = meta.get("specialist_pct", 0)

            if specialists > 0:
                insights.append(
                    Insight(
                        number=0,
                        title=(f"Knowledge silos: " f"{specialists} specialists"),
                        description=(
                            f"{pct:.0f}% of authors "
                            f"({specialists}/{total_authors}) "
                            f"contribute to only 1 domain"
                        ),
                        evidence="git history",
                        confidence=p.confidence,
                        action="Encourage cross-domain PRs",
                        category="risks",
                        source_pattern=p.name,
                    )
                )

    insights.sort(key=lambda x: (-x.confidence, x.title))
    return insights


# HC-AI | ticket: MEM-M1-10
def _render_quick_wins_md(result: QuickWinsResult) -> str:
    """Render Quick Wins as Markdown string."""
    lines: List[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Header
    lines.append("# Quick Wins")
    lines.append("")
    lines.append(f"> Generated: {ts}")
    lines.append(
        f"> {result.insight_count} actionable insights "
        f"from {result.total_patterns} patterns"
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # Structure section
    structure = result.structure_insights
    if structure:
        lines.append(f"## Structure ({len(structure)})")
        lines.append("")
        for insight in structure:
            lines.extend(_render_insight(insight))

    # Patterns section
    pats = result.pattern_insights
    if pats:
        lines.append(f"## Patterns ({len(pats)})")
        lines.append("")
        for insight in pats:
            lines.extend(_render_insight(insight))

    # Risks section
    risks = result.risk_insights
    if risks:
        lines.append(f"## Risks ({len(risks)})")
        lines.append("")
        for insight in risks:
            lines.extend(_render_insight(insight))

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(
        f"*{result.insight_count} insights · "
        f"{result.total_patterns} patterns analyzed · "
        f"Generated by Codebase Memory*"
    )
    lines.append("")

    return "\n".join(lines)


def _render_insight(insight: Insight) -> List[str]:
    """Render a single insight as Markdown lines."""
    lines: List[str] = []
    review_flag = " [needs review]" if insight.needs_review else ""

    lines.append(
        f"### {insight.number}. {insight.title} "
        f"({insight.confidence:.0f}%){review_flag}"
    )
    lines.append("")
    lines.append(insight.description)
    lines.append(f"**Evidence:** `{insight.evidence}`")
    lines.append(f"**Action:** {insight.action}")
    lines.append("")
    return lines


def _write_output(
    vault: "CodebaseVault",
    content: str,
    output_path: Optional[str],
) -> None:
    """Write quick-wins.md to disk."""
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
    elif vault.vault_dir:
        vert_dir = vault.vault_dir / "verticals" / "codebase"
        vert_dir.mkdir(parents=True, exist_ok=True)
        dest = vert_dir / "quick-wins.md"
        dest.write_text(content, encoding="utf-8")
