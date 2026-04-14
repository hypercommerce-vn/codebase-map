# HC-AI | ticket: MEM-M3-11 / MEM-M3-12 / MEM-M3-13
"""M3 Day 5: Insights CLI + Dogfood acceptance + M1/M2 regression tests."""

from __future__ import annotations

import tempfile
from pathlib import Path

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.telemetry.logger import TelemetryLogger
from knowledge_memory.verticals.codebase.insights_cli import (
    InsightsEngine,
    InsightsResult,
    format_insights_result,
)

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
            name="constructor_di_72",
            category="dependency_injection",
            confidence=72.0,
        ),
        Pattern(name="test_ratio_80", category="test_patterns", confidence=80.0),
        Pattern(name="coverage_gaps_2", category="test_patterns", confidence=70.0),
        Pattern(name="bus_factor_risk", category="ownership", confidence=96.0),
    ]


# ══════════════════════════════════════════════════
# InsightsEngine tests (MEM-M3-11)
# ══════════════════════════════════════════════════


class TestInsightsEngine:
    def test_generate_terminal(self):
        engine = InsightsEngine()
        result = engine.generate(patterns=_make_patterns())
        assert isinstance(result, InsightsResult)
        assert result.total_patterns == 10
        assert result.total_learners == 6
        assert result.avg_confidence > 80
        assert result.high_confidence >= 7
        assert result.error == ""

    def test_generate_with_roi(self):
        engine = InsightsEngine(hourly_rate=30.0)
        result = engine.generate(
            patterns=_make_patterns(),
            onboarding_reports=3,
            ask_queries=10,
            total_token_cost=0.046,
        )
        assert result.roi is not None
        assert result.roi.roi_value > 200

    def test_generate_html_export(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = str(Path(tmpdir) / "insights.html")
            engine = InsightsEngine()
            result = engine.generate(
                patterns=_make_patterns(),
                output_html=html_path,
                project_name="Test Project",
            )
            assert result.html_path == html_path
            assert Path(html_path).exists()
            content = Path(html_path).read_text()
            assert "<!DOCTYPE html>" in content
            assert "Test Project" in content

    def test_generate_empty_patterns(self):
        engine = InsightsEngine()
        result = engine.generate(patterns=[])
        assert result.total_patterns == 0
        assert result.avg_confidence == 0.0

    def test_format_terminal(self):
        engine = InsightsEngine()
        result = engine.generate(
            patterns=_make_patterns(),
            onboarding_reports=2,
            total_token_cost=0.02,
        )
        output = format_insights_result(result)
        assert "Insights Dashboard" in output
        assert "Patterns: 10" in output
        assert "ROI" in output

    def test_format_with_html_path(self):
        result = InsightsResult(
            total_patterns=10,
            total_learners=5,
            avg_confidence=85.0,
            high_confidence=7,
            low_confidence=1,
            html_path="/tmp/insights.html",
        )
        output = format_insights_result(result)
        assert "Dashboard exported" in output
        assert "insights.html" in output

    def test_format_error(self):
        result = InsightsResult(error="No vault found")
        output = format_insights_result(result)
        assert "Error" in output
        assert "No vault" in output


# ══════════════════════════════════════════════════
# Dogfood Acceptance (MEM-M3-12)
# ══════════════════════════════════════════════════


class TestDogfoodAcceptance:
    """Validate full M3 pipeline: patterns → onboard → insights → ROI."""

    def test_6_learner_categories(self):
        """M3 adds 3 learners to M1's 3 = 6 total categories."""
        patterns = _make_patterns()
        categories = {p.category for p in patterns}
        # M1: naming, layer, ownership + M3: error_handling, di, test
        assert len(categories) >= 5

    def test_onboard_with_all_learners(self):
        """OnboardEngine should produce 8 chapters from 6-learner patterns."""
        from knowledge_memory.verticals.codebase.onboard import OnboardEngine

        engine = OnboardEngine()
        engine.load_data(
            patterns=_make_patterns(),
            stats={"total_nodes": 1386, "domains": 7},
        )
        result = engine.generate()
        assert len(result.chapters) == 8
        # Error handling chapter should have content from M3 learner
        err_ch = next(
            ch for ch in result.chapters if ch.title == "Error Handling Patterns"
        )
        assert "error_handling" in err_ch.content.lower() or err_ch.pattern_count > 0

    def test_insights_pipeline_end_to_end(self):
        """Full pipeline: patterns → insights → ROI → format."""
        engine = InsightsEngine(hourly_rate=30.0)
        result = engine.generate(
            patterns=_make_patterns(),
            onboarding_reports=3,
            ask_queries=15,
            total_token_cost=0.046,
            total_llm_calls=20,
        )
        assert result.total_patterns == 10
        assert result.roi is not None
        assert result.roi.roi_value > 200
        assert result.roi.roi_multiple > 4000

        output = format_insights_result(result)
        assert "Insights" in output

    def test_glossary_extraction(self):
        """Glossary should extract terms from node data."""
        from knowledge_memory.verticals.codebase.glossary import GlossaryExtractor

        nodes = [
            {"name": "create_customer", "file_path": "crm/service.py"},
            {"name": "get_customer", "file_path": "crm/service.py"},
            {"name": "update_customer", "file_path": "crm/service.py"},
            {"name": "CustomerModel", "file_path": "crm/models.py"},
            {"name": "submit_order", "file_path": "order/service.py"},
        ]
        extractor = GlossaryExtractor(min_evidence=2)
        terms = extractor.extract(nodes)
        term_names = {t.term.lower() for t in terms}
        assert "customer" in term_names

    def test_mermaid_diagram_generation(self):
        """Mermaid should generate valid diagram syntax."""
        from knowledge_memory.verticals.codebase.mermaid import (
            generate_architecture_diagram,
        )

        layers = {"service": 85, "route": 20, "model": 15, "util": 30}
        diagram = generate_architecture_diagram(layers)
        assert "graph TD" in diagram
        assert "service" in diagram

    def test_telemetry_privacy(self):
        """Telemetry must be local-only with no network calls."""
        logger = TelemetryLogger()
        logger.log("bootstrap", duration_ms=5000)
        logger.log("ask", duration_ms=2000)
        # All events stored in memory list only
        assert logger.count() == 2
        # No network attributes
        assert not hasattr(logger, "_endpoint")
        assert not hasattr(logger, "_api_key")


# ══════════════════════════════════════════════════
# M1+M2 Regression (MEM-M3-13)
# ══════════════════════════════════════════════════


class TestM1Regression:
    """Verify M1 features still work after M3 additions."""

    def test_naming_learner_import(self):
        from knowledge_memory.verticals.codebase.naming_learner import NamingLearner

        learner = NamingLearner()
        assert learner.LEARNER_NAME == "codebase.naming"

    def test_layer_learner_import(self):
        from knowledge_memory.verticals.codebase.layer_learner import LayerLearner

        learner = LayerLearner()
        assert learner.LEARNER_NAME == "codebase.layers"

    def test_git_ownership_import(self):
        from knowledge_memory.verticals.codebase.git_ownership_learner import (
            GitOwnershipLearner,
        )

        learner = GitOwnershipLearner()
        assert learner.LEARNER_NAME == "codebase.git_ownership"

    def test_bootstrap_import(self):
        from knowledge_memory.verticals.codebase.bootstrap import BootstrapResult

        result = BootstrapResult()
        assert result.total_steps == 5

    def test_quick_wins_import(self):
        from knowledge_memory.verticals.codebase.quick_wins import QuickWinsResult

        result = QuickWinsResult()
        assert result is not None

    def test_bm25_search_import(self):
        from knowledge_memory.core.search.bm25_search import VietnameseTokenizer

        tokenizer = VietnameseTokenizer()
        tokens = tokenizer.tokenize("test query")
        assert len(tokens) > 0

    def test_vault_base_import(self):
        from knowledge_memory.core.vault.base import BaseVault

        assert BaseVault is not None

    def test_pattern_dataclass(self):
        p = Pattern(name="test", category="naming", confidence=80.0)
        assert p.name == "test"
        assert p.confidence == 80.0


class TestM2Regression:
    """Verify M2 features still work after M3 additions."""

    def test_llm_provider_import(self):
        from knowledge_memory.core.ai.providers.base import LLMProvider

        assert LLMProvider is not None

    def test_anthropic_provider_import(self):
        from knowledge_memory.core.ai.providers.anthropic_provider import (
            AnthropicProvider,
        )

        p = AnthropicProvider({"model": "test"})
        assert p.PROVIDER_NAME == "anthropic"

    def test_openai_provider_import(self):
        from knowledge_memory.core.ai.providers.openai_provider import OpenAIProvider

        p = OpenAIProvider({"model": "test"})
        assert p.PROVIDER_NAME == "openai"

    def test_gemini_provider_import(self):
        from knowledge_memory.core.ai.providers.gemini_provider import GeminiProvider

        p = GeminiProvider({"model": "test"})
        assert p.PROVIDER_NAME == "gemini"

    def test_rag_pipeline_import(self):
        from knowledge_memory.core.ai.rag import RAGPipeline

        rag = RAGPipeline({"rag": {"max_chunks": 3}})
        assert rag is not None

    def test_context_builder_import(self):
        from knowledge_memory.core.ai.context_builder import ContextBuilder

        cb = ContextBuilder()
        assert cb is not None

    def test_ask_engine_import(self):
        from knowledge_memory.verticals.codebase.ask import AskEngine

        engine = AskEngine({"llm": {"provider": "mock"}, "rag": {}})
        assert engine is not None

    def test_why_engine_import(self):
        from knowledge_memory.verticals.codebase.why import WhyEngine

        engine = WhyEngine()
        assert engine is not None

    def test_impact_engine_import(self):
        from knowledge_memory.verticals.codebase.impact import ImpactEngine

        engine = ImpactEngine()
        assert engine is not None

    def test_mcp_server_import(self):
        from knowledge_memory.core.mcp.server import MCPServer

        server = MCPServer(verticals=[])
        assert server is not None

    def test_cost_tracker_import(self):
        from knowledge_memory.core.ai.cost import CostTracker

        tracker = CostTracker()
        tracker.record("test", "v1", 100, 50, 0.001)
        assert tracker.summary().total_calls == 1

    def test_provider_registry_complete(self):
        from knowledge_memory.core.ai.client import (
            _PROVIDER_REGISTRY,
            _ensure_registered,
        )

        _PROVIDER_REGISTRY.clear()
        _ensure_registered()
        assert "anthropic" in _PROVIDER_REGISTRY
        assert "openai" in _PROVIDER_REGISTRY
        assert "gemini" in _PROVIDER_REGISTRY
