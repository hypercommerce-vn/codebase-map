# HC-AI | ticket: MEM-M3-01 / MEM-M3-04
"""Tests for onboard command + ErrorHandlingLearner."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.error_handling_learner import (
    ErrorHandlingLearner,
)
from knowledge_memory.verticals.codebase.onboard import (
    OnboardEngine,
    OnboardResult,
    format_onboard_result,
)

# ── Helpers ──────────────────────────────────


def _make_pattern(name, category, confidence=85.0, **meta):
    return Pattern(
        name=name,
        category=category,
        confidence=confidence,
        metadata={"description": f"Pattern: {name}", **meta},
        evidence=[],
    )


def _make_patterns():
    """Simulate patterns from M1 + M3 learners."""
    return [
        _make_pattern("snake_case_98pct", "naming", 94.0),
        _make_pattern("crud_prefix_78pct", "naming", 85.0),
        _make_pattern("service_layer_43pct", "layer", 91.0),
        _make_pattern("domain_boundary_7", "layer", 88.0),
        _make_pattern("single_owner_pipeline", "ownership", 96.0),
        _make_pattern("bus_factor_risk", "ownership", 92.0),
        _make_pattern(
            "error_handling_coverage_87pct", "error_handling", 87.0, coverage_pct=87.0
        ),
        _make_pattern("custom_exceptions_12", "error_handling", 85.0),
    ]


def _make_vault_nodes():
    """Simulate vault nodes for ErrorHandlingLearner."""
    return [
        {
            "name": "handle_error",
            "file_path": "utils.py",
            "node_type": "function",
            "layer": "util",
            "metadata_json": "{}",
        },
        {
            "name": "retry_request",
            "file_path": "http.py",
            "node_type": "function",
            "layer": "util",
            "metadata_json": "{}",
        },
        {
            "name": "validate_input",
            "file_path": "service.py",
            "node_type": "function",
            "layer": "service",
            "metadata_json": "{}",
        },
        {
            "name": "NotFoundError",
            "file_path": "errors.py",
            "node_type": "class",
            "layer": "model",
            "metadata_json": "{}",
        },
        {
            "name": "AuthenticationError",
            "file_path": "errors.py",
            "node_type": "class",
            "layer": "model",
            "metadata_json": "{}",
        },
        {
            "name": "ValidationError",
            "file_path": "errors.py",
            "node_type": "class",
            "layer": "model",
            "metadata_json": "{}",
        },
        {
            "name": "create_customer",
            "file_path": "crm/service.py",
            "node_type": "function",
            "layer": "service",
            "metadata_json": "{}",
        },
        {
            "name": "get_order",
            "file_path": "order/service.py",
            "node_type": "function",
            "layer": "service",
            "metadata_json": "{}",
        },
        {
            "name": "log_error_event",
            "file_path": "telemetry.py",
            "node_type": "function",
            "layer": "util",
            "metadata_json": "{}",
        },
        {
            "name": "catch_exception",
            "file_path": "middleware.py",
            "node_type": "function",
            "layer": "core",
            "metadata_json": "{}",
        },
    ]


# ══════════════════════════════════════════════════
# ErrorHandlingLearner tests
# ══════════════════════════════════════════════════


class TestErrorHandlingLearner:
    def _run_learner(self, nodes=None):
        learner = ErrorHandlingLearner()
        vault = MagicMock()
        vault.query_nodes.return_value = _make_vault_nodes() if nodes is None else nodes
        evidences = learner.extract_evidence(vault)
        clusters = learner.cluster(evidences)
        return learner, evidences, clusters

    def test_extract_evidence(self):
        learner, evidences, _ = self._run_learner()
        assert len(evidences) == 10
        assert all(isinstance(e, Evidence) for e in evidences)

    def test_cluster_types(self):
        _, _, clusters = self._run_learner()
        types = {c["pattern_type"] for c in clusters}
        # Should detect at least try_except_coverage and custom_exceptions
        assert "try_except_coverage" in types
        assert "custom_exceptions" in types

    def test_custom_exceptions_detected(self):
        _, _, clusters = self._run_learner()
        exc_cluster = next(
            (c for c in clusters if c["pattern_type"] == "custom_exceptions"), None
        )
        assert exc_cluster is not None
        assert exc_cluster["count"] == 3
        assert "NotFoundError" in exc_cluster["exceptions"]
        assert "AuthenticationError" in exc_cluster["exceptions"]

    def test_retry_pattern_detected(self):
        _, _, clusters = self._run_learner()
        retry = next(
            (c for c in clusters if c["pattern_type"] == "retry_pattern"), None
        )
        assert retry is not None
        assert "retry_request" in retry["functions"]

    def test_confidence_custom_exceptions(self):
        learner, _, clusters = self._run_learner()
        exc_cluster = next(
            c for c in clusters if c["pattern_type"] == "custom_exceptions"
        )
        conf = learner.calculate_confidence(exc_cluster)
        assert conf >= 70.0  # 3 exceptions → 85%

    def test_cluster_to_pattern(self):
        learner, _, clusters = self._run_learner()
        for cluster in clusters:
            pattern = learner.cluster_to_pattern(cluster)
            assert isinstance(pattern, Pattern)
            assert pattern.category == "error_handling"
            assert pattern.confidence > 0

    def test_learner_name(self):
        learner = ErrorHandlingLearner()
        assert learner.LEARNER_NAME == "codebase.error_handling"
        assert learner.LEARNER_CATEGORY == "error_handling"

    def test_empty_vault(self):
        learner, evidences, clusters = self._run_learner(nodes=[])
        assert len(evidences) == 0
        assert len(clusters) == 0

    def test_no_query_nodes(self):
        learner = ErrorHandlingLearner()
        vault = MagicMock(spec=[])  # No query_nodes method
        evidences = learner.extract_evidence(vault)
        assert len(evidences) == 0


# ══════════════════════════════════════════════════
# OnboardEngine tests
# ══════════════════════════════════════════════════


class TestOnboardEngine:
    def test_generate_8_chapters(self):
        engine = OnboardEngine()
        engine.load_data(
            patterns=_make_patterns(), stats={"total_nodes": 1386, "domains": 7}
        )
        result = engine.generate()
        assert isinstance(result, OnboardResult)
        assert len(result.chapters) == 8
        assert result.success

    def test_chapter_titles(self):
        engine = OnboardEngine()
        engine.load_data(patterns=_make_patterns())
        result = engine.generate()
        titles = [ch.title for ch in result.chapters]
        assert "Project Overview" in titles
        assert "Naming Conventions" in titles
        assert "Error Handling Patterns" in titles
        assert "Domain Glossary" in titles

    def test_chapters_have_content(self):
        engine = OnboardEngine()
        engine.load_data(
            patterns=_make_patterns(), stats={"total_nodes": 100, "domains": 3}
        )
        result = engine.generate()
        for ch in result.chapters:
            assert ch.content, f"Chapter {ch.number} has no content"
            assert ch.title, f"Chapter {ch.number} has no title"

    def test_naming_chapter_has_patterns(self):
        engine = OnboardEngine()
        engine.load_data(patterns=_make_patterns())
        result = engine.generate()
        naming_ch = next(
            ch for ch in result.chapters if ch.title == "Naming Conventions"
        )
        assert "snake_case" in naming_ch.content

    def test_error_handling_chapter(self):
        engine = OnboardEngine()
        engine.load_data(patterns=_make_patterns())
        result = engine.generate()
        err_ch = next(
            ch for ch in result.chapters if ch.title == "Error Handling Patterns"
        )
        assert (
            "error_handling" in err_ch.content.lower()
            or "coverage" in err_ch.content.lower()
        )

    def test_generate_writes_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = OnboardEngine()
            engine.load_data(patterns=_make_patterns(), stats={"total_nodes": 100})
            result = engine.generate(output_dir=tmpdir)
            assert result.output_path
            assert Path(result.output_path).exists()
            content = Path(result.output_path).read_text()
            assert "# Onboarding Guide" in content
            assert "## 1. Project Overview" in content

    def test_generate_empty_patterns(self):
        engine = OnboardEngine()
        engine.load_data(patterns=[])
        result = engine.generate()
        assert result.success
        assert len(result.chapters) == 8
        # Chapters should have fallback messages
        for ch in result.chapters:
            assert ch.content

    def test_generate_performance(self):
        """Report generation should be fast (< 500ms)."""
        engine = OnboardEngine()
        engine.load_data(patterns=_make_patterns() * 5, stats={"total_nodes": 5000})
        result = engine.generate()
        assert result.elapsed_seconds < 0.5

    def test_glossary_chapter_with_terms(self):
        engine = OnboardEngine()
        terms = [
            {"term": "Customer", "domain": "crm", "evidence": 23},
            {"term": "Order", "domain": "ecommerce", "evidence": 47},
        ]
        engine.load_data(patterns=[], stats={"glossary_terms": terms})
        result = engine.generate()
        glossary_ch = next(
            ch for ch in result.chapters if ch.title == "Domain Glossary"
        )
        assert "Customer" in glossary_ch.content
        assert "Order" in glossary_ch.content


# ══════════════════════════════════════════════════
# Format output tests
# ══════════════════════════════════════════════════


class TestFormatOnboardResult:
    def test_format_success(self):
        engine = OnboardEngine()
        engine.load_data(
            patterns=_make_patterns(),
            stats={"total_nodes": 1386, "domains": 7},
        )
        result = engine.generate()
        output = format_onboard_result(result)
        assert "Knowledge Memory" in output
        assert "Onboarding" in output
        assert "Ch.1" in output
        assert "Ch.8" in output
        assert "8 chapters" in output

    def test_format_error(self):
        result = OnboardResult(
            chapters=[],
            error="Vault not initialized",
        )
        output = format_onboard_result(result)
        assert "Error" in output
        assert "Vault not initialized" in output

    def test_format_with_output_path(self):
        engine = OnboardEngine()
        engine.load_data(patterns=_make_patterns())
        with tempfile.TemporaryDirectory() as tmpdir:
            result = engine.generate(output_dir=tmpdir)
            output = format_onboard_result(result)
            assert "Output:" in output
            assert "onboarding-report.md" in output
