# HC-AI | ticket: MEM-M3-10
"""Insights HTML dashboard exporter — single-file interactive viewer.

Design ref: kmp-M3-design.html Screen E.
Design decision D-M3-05: single-file, no external deps, CSS-only charts.

Sections:
1. Pattern confidence heatmap
2. Learner efficiency summary
3. ROI calculator
4. Usage timeline
"""

from __future__ import annotations

from typing import Any

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.telemetry.roi import ROIMetrics


def export_insights_html(
    patterns: list[Pattern],
    roi: ROIMetrics | None = None,
    usage_stats: dict[str, Any] | None = None,
    project_name: str = "Codebase",
) -> str:
    """Generate self-contained HTML insights dashboard.

    Args:
        patterns: All committed patterns from vault.
        roi: ROI metrics (optional).
        usage_stats: LLM usage summary (optional).
        project_name: Project name for title.

    Returns:
        Complete HTML string (self-contained, no external deps).
    """
    # Group patterns by category
    by_category: dict[str, list[Pattern]] = {}
    for p in patterns:
        by_category.setdefault(p.category, []).append(p)

    # Sort categories by pattern count
    sorted_cats = sorted(by_category.items(), key=lambda x: -len(x[1]))

    # Build HTML sections
    pattern_rows = _build_pattern_rows(sorted_cats)
    learner_cards = _build_learner_cards(sorted_cats)
    roi_section = _build_roi_section(roi)
    usage_section = _build_usage_section(usage_stats)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KMP Insights &mdash; {project_name}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #0d1117; color: #e6edf3; font-size: 14px; line-height: 1.6; }}
.container {{ max-width: 1000px; margin: 0 auto; padding: 32px 24px; }}
h1 {{ font-size: 24px; margin-bottom: 8px; color: #e6edf3; }}
h2 {{ font-size: 18px; margin: 32px 0 16px; color: #8b949e;
  border-bottom: 1px solid #30363d; padding-bottom: 8px; }}
.sub {{ color: #8b949e; font-size: 13px; margin-bottom: 32px; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px; margin-bottom: 24px; }}
.card {{ background: #161b22; border: 1px solid #30363d; border-radius: 10px;
  padding: 20px; }}
.card-title {{ font-size: 12px; color: #8b949e; text-transform: uppercase;
  letter-spacing: 0.5px; margin-bottom: 8px; }}
.card-value {{ font-size: 28px; font-weight: 700; color: #e6edf3; }}
.card-detail {{ font-size: 12px; color: #8b949e; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th {{ text-align: left; padding: 8px 12px; background: #0d1117;
  border-bottom: 1px solid #30363d; color: #8b949e; font-size: 12px;
  text-transform: uppercase; letter-spacing: 0.5px; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #21262d; color: #e6edf3; }}
.bar {{ height: 8px; border-radius: 4px; background: #21262d; }}
.bar-fill {{ height: 100%; border-radius: 4px; }}
.bar-green {{ background: #3fb950; }}
.bar-yellow {{ background: #d29922; }}
.bar-red {{ background: #f85149; }}
.badge {{ display: inline-block; font-size: 11px; padding: 2px 8px;
  border-radius: 10px; font-weight: 600; }}
.badge-green {{ background: rgba(63,185,80,0.15); color: #3fb950; }}
.badge-yellow {{ background: rgba(210,153,34,0.15); color: #d29922; }}
.roi-highlight {{ font-size: 36px; font-weight: 700; color: #3fb950; }}
footer {{ margin-top: 48px; padding: 16px 0; border-top: 1px solid #30363d;
  font-size: 12px; color: #484f58; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <h1>KMP Insights Dashboard</h1>
  <p class="sub">Knowledge Memory Platform &mdash; {project_name}
    &middot; {len(patterns)} patterns
    &middot; {len(by_category)} learners</p>

  <!-- Summary Cards -->
  <div class="grid">
    <div class="card">
      <div class="card-title">Total Patterns</div>
      <div class="card-value">{len(patterns)}</div>
      <div class="card-detail">{len(by_category)} learner categories</div>
    </div>
    <div class="card">
      <div class="card-title">Avg Confidence</div>
      <div class="card-value">{_avg_confidence(patterns):.0f}%</div>
      <div class="card-detail">Threshold: 60%</div>
    </div>
    <div class="card">
      <div class="card-title">High Confidence</div>
      <div class="card-value">{sum(1 for p in patterns if p.confidence >= 80)}</div>
      <div class="card-detail">&ge;80% confidence</div>
    </div>
    <div class="card">
      <div class="card-title">Low Confidence</div>
      <div class="card-value">{sum(1 for p in patterns if p.confidence < 70)}</div>
      <div class="card-detail">&lt;70% (needs review)</div>
    </div>
  </div>

  <!-- Pattern Confidence Heatmap -->
  <h2>Pattern Confidence</h2>
  <table>
    <thead><tr><th>Pattern</th><th>Category</th><th>Confidence</th><th></th></tr></thead>
    <tbody>
{pattern_rows}
    </tbody>
  </table>

  <!-- Learner Summary -->
  <h2>Learner Efficiency</h2>
  <div class="grid">
{learner_cards}
  </div>

  <!-- ROI -->
  <h2>Return on Investment</h2>
{roi_section}

  <!-- Usage -->
  <h2>LLM Usage</h2>
{usage_section}

  <footer>
    Auto-generated by Knowledge Memory Platform &middot;
    {len(patterns)} patterns &middot;
    Local data only &middot; Privacy-safe
  </footer>
</div>
</body>
</html>"""
    return html


def _avg_confidence(patterns: list[Pattern]) -> float:
    if not patterns:
        return 0.0
    return sum(p.confidence for p in patterns) / len(patterns)


def _confidence_class(conf: float) -> str:
    if conf >= 80:
        return "green"
    if conf >= 60:
        return "yellow"
    return "red"


def _build_pattern_rows(
    sorted_cats: list[tuple[str, list[Pattern]]],
) -> str:
    rows = []
    for cat, patterns in sorted_cats:
        for p in sorted(patterns, key=lambda x: -x.confidence):
            cls = _confidence_class(p.confidence)
            badge_cls = f"badge-{cls}"
            bar_cls = f"bar-{cls}"
            rows.append(
                f"      <tr>"
                f"<td>{p.name}</td>"
                f"<td>{cat}</td>"
                f"<td><span class='badge {badge_cls}'>"
                f"{p.confidence:.0f}%</span></td>"
                f"<td style='width:40%'>"
                f"<div class='bar'>"
                f"<div class='bar-fill {bar_cls}' "
                f"style='width:{p.confidence}%'></div>"
                f"</div></td></tr>"
            )
    return "\n".join(rows)


def _build_learner_cards(
    sorted_cats: list[tuple[str, list[Pattern]]],
) -> str:
    cards = []
    for cat, patterns in sorted_cats:
        avg = sum(p.confidence for p in patterns) / len(patterns)
        cards.append(
            f"    <div class='card'>"
            f"<div class='card-title'>{cat}</div>"
            f"<div class='card-value'>{len(patterns)}</div>"
            f"<div class='card-detail'>"
            f"Avg confidence: {avg:.0f}%</div></div>"
        )
    return "\n".join(cards)


def _build_roi_section(roi: ROIMetrics | None) -> str:
    if not roi:
        return "  <p style='color:#8b949e'>No ROI data yet.</p>"

    return (
        f"  <div class='grid'>"
        f"<div class='card'>"
        f"<div class='card-title'>Estimated ROI</div>"
        f"<div class='roi-highlight'>${roi.roi_value:,.2f}</div>"
        f"<div class='card-detail'>"
        f"{roi.hours_saved_estimate:.1f}h saved "
        f"&times; ${roi.hourly_rate:.0f}/h</div></div>"
        f"<div class='card'>"
        f"<div class='card-title'>Token Cost</div>"
        f"<div class='card-value'>${roi.total_token_cost:.3f}</div>"
        f"<div class='card-detail'>"
        f"{roi.total_llm_calls} LLM calls</div></div>"
        f"<div class='card'>"
        f"<div class='card-title'>Return Multiple</div>"
        f"<div class='card-value'>"
        f"{roi.roi_multiple:,.0f}x</div>"
        f"<div class='card-detail'>Savings / Cost</div></div>"
        f"</div>"
    )


def _build_usage_section(
    usage_stats: dict[str, Any] | None,
) -> str:
    if not usage_stats:
        return "  <p style='color:#8b949e'>No usage data yet.</p>"

    total = usage_stats.get("total_calls", 0)
    cost = usage_stats.get("total_cost", 0)
    by_provider = usage_stats.get("by_provider", {})

    rows = []
    for provider, stats in by_provider.items():
        rows.append(
            f"      <tr>"
            f"<td>{provider}</td>"
            f"<td>{stats.get('calls', 0)}</td>"
            f"<td>${stats.get('cost', 0):.3f}</td></tr>"
        )

    return (
        f"  <table>"
        f"<thead><tr><th>Provider</th><th>Calls</th>"
        f"<th>Cost</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        f"<tfoot><tr><td><strong>Total</strong></td>"
        f"<td><strong>{total}</strong></td>"
        f"<td><strong>${cost:.3f}</strong></td></tr></tfoot>"
        f"</table>"
    )
