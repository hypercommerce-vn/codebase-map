# HC-AI | ticket: MEM-M3-08 / MEM-M3-09 / MEM-M3-10
"""Tests for telemetry, ROI calculator, and insights HTML dashboard."""

from __future__ import annotations

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.telemetry.logger import TelemetryEvent, TelemetryLogger
from knowledge_memory.core.telemetry.roi import ROICalculator, ROIMetrics, format_roi
from knowledge_memory.verticals.codebase.insights_html import export_insights_html

# ── Helpers ──────────────────────────────────


def _make_patterns():
    return [
        Pattern(name="snake_case_98", category="naming", confidence=94.0),
        Pattern(name="crud_prefix_78", category="naming", confidence=85.0),
        Pattern(name="service_layer_43", category="layer", confidence=91.0),
        Pattern(name="domain_boundary", category="layer", confidence=88.0),
        Pattern(name="error_handling_87", category="error_handling", confidence=87.0),
        Pattern(name="custom_exceptions", category="error_handling", confidence=82.0),
        Pattern(
            name="constructor_di_72", category="dependency_injection", confidence=72.0
        ),
        Pattern(name="test_ratio_80", category="test_patterns", confidence=80.0),
        Pattern(name="coverage_gaps_2", category="test_patterns", confidence=70.0),
        Pattern(name="bus_factor_risk", category="ownership", confidence=96.0),
    ]


# ══════════════════════════════════════════════════
# TelemetryLogger tests
# ══════════════════════════════════════════════════


class TestTelemetryLogger:
    def test_log_event(self):
        logger = TelemetryLogger()
        event = logger.log("bootstrap", "5 steps", duration_ms=5700)
        assert isinstance(event, TelemetryEvent)
        assert event.action == "bootstrap"
        assert event.duration_ms == 5700
        assert len(logger.events) == 1

    def test_log_multiple(self):
        logger = TelemetryLogger()
        logger.log("bootstrap", duration_ms=5000)
        logger.log("ask", "auth question", duration_ms=2100)
        logger.log("ask", "order question", duration_ms=1800)
        assert logger.count() == 3
        assert logger.count("ask") == 2

    def test_events_by_action(self):
        logger = TelemetryLogger()
        logger.log("bootstrap")
        logger.log("ask", "q1")
        logger.log("ask", "q2")
        ask_events = logger.events_by_action("ask")
        assert len(ask_events) == 2

    def test_total_duration(self):
        logger = TelemetryLogger()
        logger.log("ask", duration_ms=1000)
        logger.log("ask", duration_ms=2000)
        logger.log("why", duration_ms=500)
        assert logger.total_duration_ms("ask") == 3000
        assert logger.total_duration_ms() == 3500

    def test_summary(self):
        logger = TelemetryLogger()
        logger.log("bootstrap", duration_ms=5000)
        logger.log("ask", duration_ms=2000)
        s = logger.summary()
        assert s["total_events"] == 2
        assert s["by_action"]["bootstrap"] == 1
        assert s["by_action"]["ask"] == 1

    def test_clear(self):
        logger = TelemetryLogger()
        logger.log("test")
        assert logger.count() == 1
        logger.clear()
        assert logger.count() == 0

    def test_metadata(self):
        logger = TelemetryLogger()
        event = logger.log("ask", metadata={"provider": "anthropic", "cost": 0.003})
        assert event.metadata["provider"] == "anthropic"

    def test_timestamp_auto(self):
        logger = TelemetryLogger()
        event = logger.log("test")
        assert event.timestamp > 0


# ══════════════════════════════════════════════════
# ROICalculator tests
# ══════════════════════════════════════════════════


class TestROICalculator:
    def test_basic_roi(self):
        calc = ROICalculator(hourly_rate=30.0)
        metrics = calc.calculate(
            onboarding_reports=3,
            ask_queries=10,
            total_token_cost=0.046,
            total_llm_calls=15,
        )
        assert isinstance(metrics, ROIMetrics)
        # 3 reports * 2.5h + 10 queries * 0.1h = 8.5h
        assert metrics.hours_saved_estimate == 8.5
        # 8.5h * $30 - $0.046 = $254.954
        assert abs(metrics.roi_value - 254.954) < 0.01
        assert metrics.roi_multiple > 5000

    def test_zero_cost(self):
        calc = ROICalculator()
        metrics = calc.calculate(onboarding_reports=1)
        # 1 report * 2.5h * $30 = $75
        assert metrics.roi_value == 75.0
        assert metrics.roi_multiple == 0.0  # No cost → no multiple

    def test_no_reports(self):
        calc = ROICalculator()
        metrics = calc.calculate(total_token_cost=0.01)
        assert metrics.roi_value < 0  # Cost with no savings

    def test_custom_hourly_rate(self):
        calc = ROICalculator(hourly_rate=100.0)
        metrics = calc.calculate(onboarding_reports=1, total_token_cost=0.01)
        # 2.5h * $100 - $0.01 = $249.99
        assert abs(metrics.roi_value - 249.99) < 0.01

    def test_format_roi(self):
        calc = ROICalculator()
        metrics = calc.calculate(
            onboarding_reports=3,
            total_token_cost=0.046,
            total_llm_calls=15,
        )
        output = format_roi(metrics)
        assert "ROI Report" in output
        assert "Onboarding" in output
        assert "Privacy-safe" in output


# ══════════════════════════════════════════════════
# Insights HTML tests
# ══════════════════════════════════════════════════


class TestInsightsHTML:
    def test_basic_export(self):
        html = export_insights_html(_make_patterns())
        assert "<!DOCTYPE html>" in html
        assert "KMP Insights" in html
        assert "10" in html  # 10 patterns
        assert "naming" in html

    def test_pattern_confidence_bars(self):
        html = export_insights_html(_make_patterns())
        assert "bar-fill" in html
        assert "bar-green" in html  # High confidence patterns

    def test_learner_cards(self):
        html = export_insights_html(_make_patterns())
        assert "naming" in html
        assert "error_handling" in html
        assert "ownership" in html

    def test_with_roi(self):
        roi = ROIMetrics(
            onboarding_reports=3,
            hours_saved_estimate=8.5,
            hourly_rate=30.0,
            total_token_cost=0.046,
            total_llm_calls=15,
        )
        roi.compute()
        html = export_insights_html(_make_patterns(), roi=roi)
        assert "ROI" in html
        assert "$" in html

    def test_with_usage_stats(self):
        usage = {
            "total_calls": 15,
            "total_cost": 0.046,
            "by_provider": {
                "anthropic": {"calls": 12, "cost": 0.042},
                "openai": {"calls": 3, "cost": 0.004},
            },
        }
        html = export_insights_html(_make_patterns(), usage_stats=usage)
        assert "anthropic" in html
        assert "openai" in html

    def test_empty_patterns(self):
        html = export_insights_html([])
        assert "<!DOCTYPE html>" in html
        assert "0" in html

    def test_self_contained(self):
        """HTML must be self-contained (no external deps)."""
        html = export_insights_html(_make_patterns())
        assert "http://" not in html
        assert "https://" not in html
        assert "<link" not in html
        assert "<script src" not in html

    def test_custom_project_name(self):
        html = export_insights_html(_make_patterns(), project_name="Hyper Commerce")
        assert "Hyper Commerce" in html

    def test_confidence_badges(self):
        html = export_insights_html(_make_patterns())
        assert "badge-green" in html  # >= 80%
        assert "badge-yellow" in html  # 60-79%
