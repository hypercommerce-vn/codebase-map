# HC-AI | ticket: MEM-M2-12
"""E2E integration tests — full pipeline from vault to answer/why/impact/MCP.

Tests the complete flow that an end-user or AI agent would experience:
1. Index vault data  2. RAG retrieve  3. Context build  4. LLM  5. Format
Also tests MCP server end-to-end with tool discovery.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from knowledge_memory.core.ai.client import _PROVIDER_REGISTRY, _ensure_registered
from knowledge_memory.core.ai.cost import CostTracker, format_usage_summary
from knowledge_memory.core.ai.providers.base import ChatResponse
from knowledge_memory.core.mcp.registry import clear_registry
from knowledge_memory.core.mcp.server import MCPServer
from knowledge_memory.verticals.codebase.ask import AskEngine, format_ask_result
from knowledge_memory.verticals.codebase.impact import (
    ImpactEngine,
    format_impact_result,
)
from knowledge_memory.verticals.codebase.why import WhyEngine, format_why_result

# ── Realistic test data simulating HC codebase ──────────


def _hc_nodes():
    """Simulate Hyper Commerce codebase nodes."""
    return [
        {
            "name": "login",
            "file_path": "auth/router.py",
            "layer": "route",
            "node_type": "function",
            "line_start": 12,
        },
        {
            "name": "api_login",
            "file_path": "auth/router.py",
            "layer": "route",
            "node_type": "function",
            "line_start": 30,
        },
        {
            "name": "authenticate",
            "file_path": "auth/service.py",
            "layer": "service",
            "node_type": "function",
            "line_start": 45,
        },
        {
            "name": "hash_password",
            "file_path": "auth/utils.py",
            "layer": "util",
            "node_type": "function",
            "line_start": 8,
        },
        {
            "name": "find_user",
            "file_path": "auth/service.py",
            "layer": "service",
            "node_type": "function",
            "line_start": 80,
        },
        {
            "name": "create_customer",
            "file_path": "crm/service.py",
            "layer": "service",
            "node_type": "function",
            "line_start": 15,
        },
        {
            "name": "validate_email",
            "file_path": "crm/service.py",
            "layer": "service",
            "node_type": "function",
            "line_start": 55,
        },
        {
            "name": "post_customer",
            "file_path": "crm/router.py",
            "layer": "route",
            "node_type": "function",
            "line_start": 5,
        },
        {
            "name": "submit_order",
            "file_path": "order/service.py",
            "layer": "service",
            "node_type": "function",
            "line_start": 20,
        },
        {
            "name": "create_invoice",
            "file_path": "billing/service.py",
            "layer": "service",
            "node_type": "function",
            "line_start": 10,
        },
    ]


def _hc_edges():
    return [
        {"source_name": "login", "target_name": "authenticate"},
        {"source_name": "api_login", "target_name": "authenticate"},
        {"source_name": "authenticate", "target_name": "hash_password"},
        {"source_name": "authenticate", "target_name": "find_user"},
        {"source_name": "post_customer", "target_name": "create_customer"},
        {"source_name": "create_customer", "target_name": "validate_email"},
        {"source_name": "submit_order", "target_name": "create_invoice"},
        {"source_name": "submit_order", "target_name": "authenticate"},
    ]


def _hc_patterns():
    """Simulate patterns from bootstrap."""
    p1 = MagicMock()
    p1.name = "snake_case_compliance"
    p1.category = "naming"
    p1.confidence = 0.94
    p1.metadata = {"description": "98.2% snake_case compliance"}
    p1.evidence_summary = "1359/1386 nodes follow snake_case"

    p2 = MagicMock()
    p2.name = "service_layer_dominant"
    p2.category = "layer"
    p2.confidence = 0.91
    p2.metadata = {"description": "43% service-layer nodes"}
    p2.evidence_summary = "596/1386 nodes in service layer"

    p3 = MagicMock()
    p3.name = "authenticate_jwt_flow"
    p3.category = "structure"
    p3.confidence = 0.88
    p3.metadata = {"description": "JWT auth via authenticate function"}
    p3.evidence_summary = "auth/service.py:authenticate handles JWT"

    p4 = MagicMock()
    p4.name = "cross_domain_order_billing"
    p4.category = "risk"
    p4.confidence = 0.85
    p4.metadata = {"description": "order domain calls billing domain"}
    p4.evidence_summary = "submit_order calls create_invoice"

    return [p1, p2, p3, p4]


# ══════════════════════════════════════════════════
# E2E: Ask pipeline
# ══════════════════════════════════════════════════


class TestE2EAskPipeline:
    """Full pipeline: index vault → ask question → get answer with citations."""

    @patch("knowledge_memory.verticals.codebase.ask.chat_with_fallback")
    def test_ask_about_auth(self, mock_chat):
        mock_chat.return_value = ChatResponse(
            content=(
                "Authentication uses JWT tokens via auth/service.py:authenticate(). "
                "Login endpoint at auth/router.py:login() validates credentials."
            ),
            input_tokens=340,
            output_tokens=180,
            model="claude-sonnet-4-20250514",
            provider="anthropic",
            cost=0.003,
            latency_ms=1800,
        )

        config = {
            "llm": {"provider": "mock", "model": "mock"},
            "rag": {"max_chunks": 5, "min_score": 0.01},
        }

        engine = AskEngine(config)
        engine.index_vault(
            patterns=_hc_patterns(),
            nodes={n["name"]: SimpleNamespace(**n) for n in _hc_nodes()},
            edges=[
                SimpleNamespace(source=e["source_name"], target=e["target_name"])
                for e in _hc_edges()
            ],
        )

        result = engine.ask("How is authentication handled?")

        assert result.error == ""
        assert "JWT" in result.answer or "auth" in result.answer.lower()
        assert result.provider == "anthropic"
        assert result.cost == 0.003
        assert result.total_ms > 0

        # Format output
        output = format_ask_result(result)
        assert "Knowledge Memory" in output
        assert "anthropic" in output

    @patch("knowledge_memory.verticals.codebase.ask.chat_with_fallback")
    def test_ask_pipeline_timing(self, mock_chat):
        """Full pipeline should be fast (< 1s excluding LLM)."""
        mock_chat.return_value = ChatResponse(
            content="Quick answer",
            input_tokens=100,
            output_tokens=20,
            model="v1",
            provider="mock",
            cost=0.001,
            latency_ms=50,
        )

        config = {"llm": {"provider": "mock"}, "rag": {"min_score": 0.01}}
        engine = AskEngine(config)
        engine.index_vault(patterns=_hc_patterns())
        result = engine.ask("test question")

        # Excluding LLM latency, pipeline should be < 500ms
        non_llm_time = result.total_ms - result.generation_ms
        assert non_llm_time < 500, f"Non-LLM pipeline took {non_llm_time:.0f}ms"


# ══════════════════════════════════════════════════
# E2E: Why pipeline
# ══════════════════════════════════════════════════


class TestE2EWhyPipeline:
    """Full pipeline: load graph → why query → formatted output."""

    def test_why_auth_chain(self):
        engine = WhyEngine()
        engine.load_graph(
            _hc_nodes(),
            _hc_edges(),
            patterns=[p.name for p in _hc_patterns()],
        )

        result = engine.why("login", "hash_password")

        assert result.connected
        assert len(result.paths) >= 1
        # login → authenticate → hash_password
        assert any(len(p.nodes) == 3 for p in result.paths)

        output = format_why_result(result)
        assert "login" in output
        assert "hash_password" in output
        assert "Path" in output

    def test_why_cross_domain(self):
        engine = WhyEngine()
        engine.load_graph(_hc_nodes(), _hc_edges())

        result = engine.why("submit_order", "create_invoice")

        assert result.connected
        assert "cross-domain" in result.architecture_note

        output = format_why_result(result)
        assert "cross-domain" in output


# ══════════════════════════════════════════════════
# E2E: Impact pipeline
# ══════════════════════════════════════════════════


class TestE2EImpactPipeline:
    """Full pipeline: load graph → impact analysis → formatted output."""

    def test_impact_authenticate(self):
        engine = ImpactEngine()
        engine.load_graph(_hc_nodes(), _hc_edges())

        result = engine.analyze("authenticate", depth=2)

        assert result.error == ""
        assert result.function_name == "authenticate"
        assert len(result.direct_callers) >= 3  # login, api_login, submit_order
        assert result.risk_level in ("HIGH", "MEDIUM")

        output = format_impact_result(result)
        assert "authenticate" in output
        assert "login" in output
        assert "Risk:" in output

    def test_impact_low_risk(self):
        engine = ImpactEngine()
        engine.load_graph(_hc_nodes(), _hc_edges())

        result = engine.analyze("validate_email")

        assert result.risk_level == "LOW"
        assert len(result.direct_callers) == 1  # create_customer


# ══════════════════════════════════════════════════
# E2E: MCP server pipeline
# ══════════════════════════════════════════════════


class TestE2EMCPPipeline:
    """Full pipeline: discover tools → call via JSON-RPC → get result."""

    def setup_method(self):
        clear_registry()

    def test_mcp_full_flow(self):
        from knowledge_memory.verticals.codebase import mcp_tools

        server = MCPServer(verticals=["codebase"])
        server.discover_tools()

        mcp_tools.configure_tools(
            nodes=_hc_nodes(),
            edges=_hc_edges(),
        )

        # Initialize
        resp = server.handle_request(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        )
        assert resp["result"]["serverInfo"]["name"] == "knowledge-memory"

        # List tools
        resp = server.handle_request(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        )
        tool_names = [t["name"] for t in resp["result"]["tools"]]
        assert set(tool_names) >= {
            "find_function",
            "explain_module",
            "pattern_check",
            "impact",
        }

        # Call find_function
        resp = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "find_function",
                    "arguments": {"name": "authenticate"},
                },
            }
        )
        assert "result" in resp
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["name"] == "authenticate"
        assert content["callers"] >= 3

        # Call impact
        resp = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "impact", "arguments": {"function": "authenticate"}},
            }
        )
        assert "result" in resp
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content["risk_level"] in ("HIGH", "MEDIUM")

        # Call pattern_check
        resp = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "pattern_check",
                    "arguments": {"function": "getOrderTotal"},
                },
            }
        )
        assert "result" in resp
        content = json.loads(resp["result"]["content"][0]["text"])
        assert len(content["violations"]) >= 1  # camelCase detected


# ══════════════════════════════════════════════════
# E2E: Cost tracking across pipeline
# ══════════════════════════════════════════════════


class TestE2ECostTracking:
    """Cost tracker accumulates across multiple ask calls."""

    @patch("knowledge_memory.verticals.codebase.ask.chat_with_fallback")
    def test_multi_query_cost_accumulation(self, mock_chat):
        responses = [
            ChatResponse(
                content="Answer 1",
                input_tokens=200,
                output_tokens=50,
                model="sonnet",
                provider="anthropic",
                cost=0.003,
            ),
            ChatResponse(
                content="Answer 2",
                input_tokens=300,
                output_tokens=80,
                model="gpt-4o-mini",
                provider="openai",
                cost=0.001,
            ),
            ChatResponse(
                content="Answer 3",
                input_tokens=150,
                output_tokens=40,
                model="flash",
                provider="gemini",
                cost=0.0005,
            ),
        ]
        mock_chat.side_effect = responses

        config = {"llm": {"provider": "mock"}, "rag": {"min_score": 0.01}}
        engine = AskEngine(config)
        engine.index_vault(patterns=_hc_patterns())

        tracker = CostTracker()
        for i in range(3):
            result = engine.ask(f"Question {i}")
            if not result.error:
                tracker.record(
                    result.provider,
                    result.model,
                    result.input_tokens,
                    result.output_tokens,
                    result.cost,
                    query_preview=result.query,
                )

        summary = tracker.summary()
        assert summary.total_calls == 3
        assert summary.total_cost > 0.004
        assert len(summary.by_provider) == 3

        output = format_usage_summary(summary)
        assert "anthropic" in output
        assert "openai" in output
        assert "gemini" in output
        assert "Total" in output


# ══════════════════════════════════════════════════
# E2E: Provider registry completeness
# ══════════════════════════════════════════════════


class TestE2EProviderRegistry:
    """Verify all 3 providers are properly registered and functional."""

    def test_all_providers_cost_estimate(self):
        _PROVIDER_REGISTRY.clear()
        _ensure_registered()

        test_cases = [
            ("anthropic", "claude-sonnet-4-20250514", 10000, 5000),
            ("openai", "gpt-4o-mini", 10000, 5000),
            ("gemini", "gemini-2.0-flash", 10000, 5000),
        ]

        for name, model, inp, out in test_cases:
            provider = _PROVIDER_REGISTRY[name]({"provider": name, "model": model})
            cost = provider.estimate_cost(inp, out)
            assert cost > 0, f"{name}/{model} returned zero cost"
            tokens = provider.count_tokens("Hello world test string")
            assert tokens > 0, f"{name}/{model} returned zero tokens"
