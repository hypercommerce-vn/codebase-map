# HC-AI | ticket: MEM-M3-02 / MEM-M3-05 / MEM-M3-06
"""Tests for DI learner, TestPatterns learner, and chapter templates."""

from __future__ import annotations

from unittest.mock import MagicMock

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.verticals.codebase.di_learner import DependencyInjectionLearner
from knowledge_memory.verticals.codebase.templates.onboarding.chapter_template import (
    get_chapter_titles,
    render_chapter,
)
from knowledge_memory.verticals.codebase.test_patterns_learner import (
    TestPatternsLearner,
)

# ── Shared test data ──────────────────────────


def _make_di_nodes():
    return [
        {
            "name": "__init__",
            "file_path": "crm/service.py",
            "node_type": "method",
            "layer": "service",
        },
        {
            "name": "__init__",
            "file_path": "auth/handler.py",
            "node_type": "method",
            "layer": "service",
        },
        {
            "name": "__init__",
            "file_path": "utils/helper.py",
            "node_type": "method",
            "layer": "util",
        },
        {
            "name": "__init__",
            "file_path": "billing/gateway.py",
            "node_type": "method",
            "layer": "service",
        },
        {
            "name": "__init__",
            "file_path": "models/user.py",
            "node_type": "method",
            "layer": "model",
        },
        {
            "name": "__init__",
            "file_path": "pipeline/adapter.py",
            "node_type": "method",
            "layer": "service",
        },
        {
            "name": "create_service",
            "file_path": "factory.py",
            "node_type": "function",
            "layer": "util",
        },
        {
            "name": "build_pipeline",
            "file_path": "factory.py",
            "node_type": "function",
            "layer": "util",
        },
        {
            "name": "get_instance",
            "file_path": "singleton.py",
            "node_type": "function",
            "layer": "util",
        },
        {
            "name": "get_service",
            "file_path": "container.py",
            "node_type": "function",
            "layer": "util",
        },
    ]


def _make_test_nodes():
    return [
        {
            "name": "test_login",
            "file_path": "tests/test_auth.py",
            "node_type": "function",
            "layer": "test",
        },
        {
            "name": "test_create_user",
            "file_path": "tests/test_crm.py",
            "node_type": "function",
            "layer": "test",
        },
        {
            "name": "test_order_flow",
            "file_path": "tests/test_order.py",
            "node_type": "function",
            "layer": "test",
        },
        {
            "name": "fixture_db",
            "file_path": "tests/conftest.py",
            "node_type": "function",
            "layer": "test",
        },
        {
            "name": "setup_auth",
            "file_path": "tests/conftest.py",
            "node_type": "function",
            "layer": "test",
        },
        {
            "name": "login",
            "file_path": "auth/router.py",
            "node_type": "function",
            "layer": "route",
        },
        {
            "name": "authenticate",
            "file_path": "auth/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "create_invoice",
            "file_path": "billing/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "get_order",
            "file_path": "order/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "send_email",
            "file_path": "pipeline/worker.py",
            "node_type": "function",
            "layer": "util",
        },
    ]


# ══════════════════════════════════════════════════
# DependencyInjectionLearner tests
# ══════════════════════════════════════════════════


class TestDILearner:
    def _run(self, nodes=None):
        learner = DependencyInjectionLearner()
        vault = MagicMock()
        vault.query_nodes.return_value = _make_di_nodes() if nodes is None else nodes
        evidences = learner.extract_evidence(vault)
        clusters = learner.cluster(evidences)
        return learner, evidences, clusters

    def test_extract_evidence(self):
        _, evidences, _ = self._run()
        assert len(evidences) == 10

    def test_constructor_injection_detected(self):
        _, _, clusters = self._run()
        ci = next(
            (c for c in clusters if c["pattern_type"] == "constructor_injection"),
            None,
        )
        assert ci is not None
        assert ci["total_constructors"] >= 5

    def test_factory_pattern_detected(self):
        _, _, clusters = self._run()
        fp = next(
            (c for c in clusters if c["pattern_type"] == "factory_pattern"),
            None,
        )
        assert fp is not None
        assert "create_service" in fp["functions"]
        assert "build_pipeline" in fp["functions"]

    def test_singleton_detected(self):
        _, _, clusters = self._run()
        sg = next(
            (c for c in clusters if c["pattern_type"] == "singleton_pattern"),
            None,
        )
        assert sg is not None
        assert "get_instance" in sg["refs"]

    def test_service_locator_detected(self):
        _, _, clusters = self._run()
        sl = next(
            (c for c in clusters if c["pattern_type"] == "service_locator"),
            None,
        )
        assert sl is not None
        assert "get_service" in sl["refs"]

    def test_cluster_to_pattern(self):
        learner, _, clusters = self._run()
        for cluster in clusters:
            pattern = learner.cluster_to_pattern(cluster)
            assert isinstance(pattern, Pattern)
            assert pattern.category == "dependency_injection"
            assert pattern.confidence > 0

    def test_learner_name(self):
        learner = DependencyInjectionLearner()
        assert learner.LEARNER_NAME == "codebase.dependency_injection"

    def test_empty_vault(self):
        _, evidences, clusters = self._run(nodes=[])
        assert len(evidences) == 0


# ══════════════════════════════════════════════════
# TestPatternsLearner tests
# ══════════════════════════════════════════════════


class TestTestPatternsLearner:
    def _run(self, nodes=None):
        learner = TestPatternsLearner()
        vault = MagicMock()
        vault.query_nodes.return_value = _make_test_nodes() if nodes is None else nodes
        evidences = learner.extract_evidence(vault)
        clusters = learner.cluster(evidences)
        return learner, evidences, clusters

    def test_extract_evidence(self):
        _, evidences, _ = self._run()
        assert len(evidences) == 10

    def test_test_code_ratio(self):
        _, _, clusters = self._run()
        ratio = next(
            (c for c in clusters if c["pattern_type"] == "test_code_ratio"),
            None,
        )
        assert ratio is not None
        assert ratio["test_files"] >= 3
        assert ratio["source_files"] >= 4

    def test_test_naming_compliance(self):
        _, _, clusters = self._run()
        naming = next(
            (c for c in clusters if c["pattern_type"] == "test_naming"),
            None,
        )
        assert naming is not None
        assert naming["compliance"] == 100.0  # All test_ prefix

    def test_fixture_detected(self):
        _, _, clusters = self._run()
        fix = next(
            (c for c in clusters if c["pattern_type"] == "fixture_usage"),
            None,
        )
        assert fix is not None
        assert "fixture_db" in fix["fixtures"]
        assert "setup_auth" in fix["fixtures"]

    def test_coverage_gaps(self):
        _, _, clusters = self._run()
        gaps = next(
            (c for c in clusters if c["pattern_type"] == "coverage_gaps"),
            None,
        )
        assert gaps is not None
        # billing and pipeline have no test files
        assert "billing" in gaps["domains_without_tests"]

    def test_cluster_to_pattern(self):
        learner, _, clusters = self._run()
        for cluster in clusters:
            pattern = learner.cluster_to_pattern(cluster)
            assert isinstance(pattern, Pattern)
            assert pattern.category == "test_patterns"

    def test_learner_name(self):
        learner = TestPatternsLearner()
        assert learner.LEARNER_NAME == "codebase.test_patterns"

    def test_empty_vault(self):
        _, evidences, clusters = self._run(nodes=[])
        assert len(evidences) == 0


# ══════════════════════════════════════════════════
# Chapter template tests
# ══════════════════════════════════════════════════


class TestChapterTemplates:
    def test_render_chapter_1(self):
        result = render_chapter(
            1,
            {
                "total_nodes": "1386",
                "domains": "7",
                "architecture_summary": "Service-oriented, 43% service layer",
                "top_patterns": "snake_case 98%, CRUD prefix 78%",
                "mermaid_placeholder": "",
            },
        )
        assert "1386 functions" in result
        assert "7 domains" in result
        assert "Service-oriented" in result

    def test_render_chapter_2(self):
        result = render_chapter(
            2,
            {
                "naming_patterns": "- snake_case: 98.2%\n- CRUD: 78%",
            },
        )
        assert "Naming Conventions" in result
        assert "snake_case" in result

    def test_render_chapter_4(self):
        result = render_chapter(
            4,
            {
                "error_patterns": "- try/except: 87% coverage",
            },
        )
        assert "Error Handling" in result

    def test_render_chapter_8(self):
        result = render_chapter(
            8,
            {
                "glossary_table": "| Customer | CRM | 23 |",
            },
        )
        assert "Glossary" in result
        assert "Customer" in result

    def test_render_missing_vars(self):
        """Missing variables should not crash (safe_substitute keeps ${var})."""
        result = render_chapter(1, {})
        assert "Project Overview" in result
        # safe_substitute preserves missing ${var} — this is correct behavior
        assert len(result) > 0

    def test_render_invalid_chapter(self):
        result = render_chapter(99, {})
        assert "No template" in result

    def test_get_chapter_titles(self):
        titles = get_chapter_titles()
        assert len(titles) == 8
        assert titles[1] == "Project Overview"
        assert titles[8] == "Domain Glossary"

    def test_all_8_chapters_render(self):
        """All 8 chapters should render without errors."""
        for num in range(1, 9):
            result = render_chapter(num, {})
            assert result, f"Chapter {num} rendered empty"
            assert f"## {num}." in result
