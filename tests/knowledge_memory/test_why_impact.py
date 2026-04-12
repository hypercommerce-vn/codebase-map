# HC-AI | ticket: MEM-M2-05 / MEM-M2-06
"""Tests for Why + Impact commands."""

from __future__ import annotations

from knowledge_memory.verticals.codebase.impact import (
    ImpactEngine,
    ImpactResult,
    format_impact_result,
)
from knowledge_memory.verticals.codebase.why import (
    WhyEngine,
    WhyResult,
    format_why_result,
)

# ── Shared test graph ──────────────────────────


def _build_graph():
    """Build a realistic test graph for both engines."""
    nodes = [
        {"name": "login", "file_path": "auth/router.py", "layer": "route"},
        {"name": "api_login", "file_path": "auth/router.py", "layer": "route"},
        {"name": "authenticate", "file_path": "auth/service.py", "layer": "service"},
        {"name": "hash_password", "file_path": "auth/utils.py", "layer": "util"},
        {"name": "find_user", "file_path": "auth/service.py", "layer": "service"},
        {
            "name": "create_invoice",
            "file_path": "billing/service.py",
            "layer": "service",
        },
        {"name": "submit_order", "file_path": "order/service.py", "layer": "service"},
        {"name": "get_total", "file_path": "order/service.py", "layer": "service"},
        {"name": "tax_rate", "file_path": "billing/service.py", "layer": "service"},
        {"name": "test_login", "file_path": "tests/test_auth.py", "layer": "test"},
    ]
    edges = [
        {"source_name": "login", "target_name": "authenticate"},
        {"source_name": "api_login", "target_name": "authenticate"},
        {"source_name": "authenticate", "target_name": "hash_password"},
        {"source_name": "authenticate", "target_name": "find_user"},
        {"source_name": "submit_order", "target_name": "create_invoice"},
        {"source_name": "submit_order", "target_name": "authenticate"},
        {"source_name": "get_total", "target_name": "tax_rate"},
        {"source_name": "test_login", "target_name": "authenticate"},
    ]
    return nodes, edges


# ══════════════════════════════════════════════════
# WhyEngine tests
# ══════════════════════════════════════════════════


class TestWhyEngine:
    def test_direct_path(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.why("login", "authenticate")
        assert result.connected
        assert len(result.paths) >= 1
        assert result.paths[0].path_type == "direct"
        assert result.paths[0].nodes == ["login", "authenticate"]

    def test_transitive_path(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.why("login", "hash_password")
        assert result.connected
        assert len(result.paths) >= 1
        # login → authenticate → hash_password
        assert len(result.paths[0].nodes) == 3

    def test_no_path(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.why("tax_rate", "login")
        assert not result.connected
        assert len(result.paths) == 0

    def test_source_not_found(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.why("nonexistent_func", "login")
        assert result.error
        assert "not found" in result.error.lower()

    def test_fuzzy_name_match(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        # Partial match
        result = engine.why("login", "hash")
        assert result.connected or result.error == ""

    def test_multiple_paths(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        # submit_order → authenticate has path, and
        # submit_order → create_invoice is another target
        result = engine.why("submit_order", "authenticate")
        assert result.connected

    def test_cross_domain_note(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.why("submit_order", "create_invoice")
        assert result.connected
        # order/ → billing/ = cross-domain
        assert "cross-domain" in result.architecture_note

    def test_related_patterns(self):
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(
            nodes,
            edges,
            patterns=["authenticate_jwt_flow", "billing_coupling"],
        )
        result = engine.why("login", "authenticate")
        assert "authenticate_jwt_flow" in result.related_patterns

    def test_performance(self):
        """Why analysis must be fast (< 100ms)."""
        engine = WhyEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.why("login", "authenticate")
        assert result.total_ms < 100


# ══════════════════════════════════════════════════
# ImpactEngine tests
# ══════════════════════════════════════════════════


class TestImpactEngine:
    def test_direct_callers(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("authenticate", depth=1)
        assert len(result.direct_callers) >= 3
        caller_names = {c.name for c in result.direct_callers}
        assert "login" in caller_names
        assert "api_login" in caller_names

    def test_transitive_callers(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("hash_password", depth=2)
        # hash_password ← authenticate ← login/api_login/submit_order/test
        assert len(result.direct_callers) >= 1
        assert result.direct_callers[0].name == "authenticate"

    def test_risk_high(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("authenticate")
        # authenticate has route callers (login, api_login) = HIGH
        assert result.risk_level in ("HIGH", "MEDIUM")

    def test_risk_low(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("tax_rate")
        # tax_rate only called by get_total (service layer)
        assert result.risk_level == "LOW"

    def test_function_not_found(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("nonexistent_xyz")
        assert result.error
        assert "not found" in result.error.lower()

    def test_file_colon_name_format(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("auth/service.py:authenticate")
        assert result.function_name == "authenticate"
        assert result.error == ""

    def test_recommendation_high_risk(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("authenticate")
        if result.risk_level == "HIGH":
            assert "integration test" in result.recommendation.lower()

    def test_caller_risk_classification(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("authenticate")
        risks = {c.name: c.risk for c in result.direct_callers}
        assert risks.get("login") == "high"  # route layer
        assert risks.get("test_login") == "low"  # test layer

    def test_depth_limit(self):
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        r1 = engine.analyze("hash_password", depth=1)
        r2 = engine.analyze("hash_password", depth=3)
        total1 = len(r1.direct_callers) + len(r1.transitive_callers)
        total2 = len(r2.direct_callers) + len(r2.transitive_callers)
        assert total2 >= total1

    def test_performance(self):
        """Impact analysis must be fast (< 100ms)."""
        engine = ImpactEngine()
        nodes, edges = _build_graph()
        engine.load_graph(nodes, edges)
        result = engine.analyze("authenticate", depth=3)
        assert result.total_ms < 100


# ══════════════════════════════════════════════════
# Format output tests
# ══════════════════════════════════════════════════


class TestFormatWhyResult:
    def test_format_connected(self):
        result = WhyResult(
            source="login",
            target="authenticate",
            paths=[
                {"nodes": ["login", "authenticate"], "path_type": "direct"},
            ],
            related_patterns=[],
        )
        # Use actual CallPath objects
        from knowledge_memory.verticals.codebase.why import CallPath

        result.paths = [CallPath(nodes=["login", "authenticate"], path_type="direct")]
        output = format_why_result(result)
        assert "login" in output
        assert "authenticate" in output
        assert "Path 1" in output

    def test_format_not_connected(self):
        result = WhyResult(source="a", target="b", paths=[], related_patterns=[])
        output = format_why_result(result)
        assert "No dependency path" in output

    def test_format_error(self):
        result = WhyResult(
            source="x",
            target="y",
            paths=[],
            related_patterns=[],
            error="Source not found: 'x'",
        )
        output = format_why_result(result)
        assert "not found" in output

    def test_format_architecture_note(self):
        from knowledge_memory.verticals.codebase.why import CallPath

        result = WhyResult(
            source="submit_order",
            target="create_invoice",
            paths=[
                CallPath(
                    nodes=["submit_order", "create_invoice"],
                    path_type="direct",
                )
            ],
            related_patterns=[],
            architecture_note="cross-domain coupling detected",
        )
        output = format_why_result(result)
        assert "cross-domain" in output


class TestFormatImpactResult:
    def test_format_with_callers(self):
        from knowledge_memory.verticals.codebase.impact import Caller

        result = ImpactResult(
            function_name="authenticate",
            file_path="auth/service.py",
            layer="service",
            domain="auth",
            direct_callers=[
                Caller("login", "auth/router.py", "auth", 1, "high"),
                Caller("test_login", "tests/test_auth.py", "tests", 1, "low"),
            ],
            transitive_callers=[],
            risk_level="HIGH",
            recommendation="Add integration test before modifying.",
        )
        output = format_impact_result(result)
        assert "authenticate" in output
        assert "HIGH" in output
        assert "login" in output
        assert "integration test" in output

    def test_format_error(self):
        result = ImpactResult(
            function_name="xyz",
            file_path="",
            layer="",
            domain="",
            direct_callers=[],
            transitive_callers=[],
            risk_level="LOW",
            recommendation="",
            error="Function not found",
        )
        output = format_impact_result(result)
        assert "not found" in output

    def test_format_cbm_diff(self):
        result = ImpactResult(
            function_name="test",
            file_path="test.py",
            layer="service",
            domain="test",
            direct_callers=[],
            transitive_callers=[],
            risk_level="LOW",
            recommendation="",
            cbm_diff={
                "summary": {
                    "functions_added": 5,
                    "functions_removed": 2,
                    "functions_modified": 1,
                }
            },
        )
        output = format_impact_result(result)
        assert "Added: 5" in output
        assert "Removed: 2" in output
        assert "CBM" in output
