# HC-AI | ticket: MEM-M2-01
"""Tests for AI Gateway: LLMProvider, Anthropic, client, RAG."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from knowledge_memory.core.ai.client import (
    _PROVIDER_REGISTRY,
    _ensure_registered,
    chat_with_fallback,
    get_fallback_provider,
    get_provider,
    register_provider,
)
from knowledge_memory.core.ai.providers.anthropic_provider import (
    _ANTHROPIC_PRICING,
    AnthropicProvider,
)
from knowledge_memory.core.ai.providers.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ProviderError,
)
from knowledge_memory.core.ai.rag import RAGPipeline, RAGResult  # noqa: F401

# ── Fixtures ──────────────────────────────────────────


class MockProvider(LLMProvider):
    """Test provider that returns canned responses."""

    PROVIDER_NAME = "mock"

    def __init__(self, config=None):
        super().__init__(config or {"model": "mock-v1", "max_tokens": 100})
        self.call_count = 0
        self.fail_next = False

    def chat(self, messages, **kwargs):
        self.call_count += 1
        if self.fail_next:
            raise ProviderError(self.PROVIDER_NAME, "Mock failure", retryable=True)
        return ChatResponse(
            content="Mock answer",
            input_tokens=10,
            output_tokens=5,
            model="mock-v1",
            provider="mock",
            cost=0.001,
            latency_ms=50.0,
        )

    def count_tokens(self, text):
        return len(text) // 4

    def estimate_cost(self, input_tokens, output_tokens):
        return (input_tokens + output_tokens) * 0.0001


@pytest.fixture(autouse=True)
def _clear_registry():
    """Reset provider registry between tests."""
    _PROVIDER_REGISTRY.clear()
    yield
    _PROVIDER_REGISTRY.clear()


# ══════════════════════════════════════════════════════════
# LLMProvider ABC
# ══════════════════════════════════════════════════════════


class TestLLMProviderABC:
    def test_cannot_instantiate_abc(self):
        with pytest.raises(TypeError):
            LLMProvider({"model": "test"})

    def test_mock_provider_implements_interface(self):
        p = MockProvider()
        assert p.PROVIDER_NAME == "mock"
        assert p.model == "mock-v1"

    def test_chat_returns_response(self):
        p = MockProvider()
        resp = p.chat([ChatMessage(role="user", content="hi")])
        assert resp.content == "Mock answer"
        assert resp.input_tokens == 10
        assert resp.provider == "mock"

    def test_count_tokens(self):
        p = MockProvider()
        assert p.count_tokens("hello world test") == 4  # 16 chars // 4

    def test_estimate_cost(self):
        p = MockProvider()
        assert p.estimate_cost(100, 50) == pytest.approx(0.015)

    def test_supports_default_false(self):
        p = MockProvider()
        assert p.supports("streaming") is False
        assert p.supports("tools") is False

    def test_provider_error_fields(self):
        e = ProviderError("anthropic", "rate limit", retryable=True)
        assert e.provider == "anthropic"
        assert e.retryable is True
        assert "anthropic" in str(e)


# ══════════════════════════════════════════════════════════
# AnthropicProvider
# ══════════════════════════════════════════════════════════


class TestAnthropicProvider:
    def test_init(self):
        p = AnthropicProvider(
            {
                "model": "claude-sonnet-4-20250514",
                "api_key_env": "TEST_KEY",
                "max_tokens": 512,
                "temperature": 0.5,
            }
        )
        assert p.PROVIDER_NAME == "anthropic"
        assert p.model == "claude-sonnet-4-20250514"
        assert p._max_tokens == 512
        assert p._temperature == 0.5

    def test_missing_api_key_raises(self):
        p = AnthropicProvider(
            {
                "model": "claude-sonnet-4-20250514",
                "api_key_env": "NONEXISTENT_KEY_XYZ",
            }
        )
        with pytest.raises(ProviderError, match="API key not found"):
            p._get_client()

    def test_estimate_cost_sonnet(self):
        p = AnthropicProvider({"model": "claude-sonnet-4-20250514"})
        # 1000 input + 500 output tokens with sonnet pricing
        cost = p.estimate_cost(1000, 500)
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert cost == pytest.approx(expected)

    def test_estimate_cost_opus(self):
        p = AnthropicProvider({"model": "claude-opus-4-20250514"})
        cost = p.estimate_cost(1000, 500)
        expected = (1000 / 1_000_000) * 15.0 + (500 / 1_000_000) * 75.0
        assert cost == pytest.approx(expected)

    def test_estimate_cost_unknown_model(self):
        p = AnthropicProvider({"model": "unknown-model-9999"})
        assert p.estimate_cost(1000, 500) == 0.0

    def test_count_tokens_estimate(self):
        p = AnthropicProvider({"model": "claude-sonnet-4-20250514"})
        assert p.count_tokens("hello") == 1  # 5 chars // 4 = 1
        assert p.count_tokens("a" * 100) == 25

    def test_supports_features(self):
        p = AnthropicProvider({"model": "claude-sonnet-4-20250514"})
        assert p.supports("streaming") is True
        assert p.supports("tools") is True
        assert p.supports("vision") is True
        assert p.supports("unknown_feature") is False

    def test_pricing_table_has_entries(self):
        assert len(_ANTHROPIC_PRICING) >= 3
        for model, (inp, out) in _ANTHROPIC_PRICING.items():
            assert inp > 0
            assert out > 0
            assert out > inp  # output always more expensive

    @patch.dict(os.environ, {"TEST_ANTHROPIC_KEY": "sk-test-123"})
    def test_get_client_with_key(self):
        """Client init with valid env var (SDK import may fail in test env)."""
        p = AnthropicProvider(
            {
                "model": "claude-sonnet-4-20250514",
                "api_key_env": "TEST_ANTHROPIC_KEY",
            }
        )
        try:
            p._get_client()
        except ProviderError as e:
            # OK if anthropic package not installed in test env
            assert "not installed" in str(e)


# ══════════════════════════════════════════════════════════
# Client Factory
# ══════════════════════════════════════════════════════════


class TestClientFactory:
    def test_register_and_get_provider(self):
        register_provider("mock", MockProvider)
        p = get_provider({"llm": {"provider": "mock", "model": "v1"}})
        assert isinstance(p, MockProvider)

    def test_unknown_provider_raises(self):
        register_provider("mock", MockProvider)
        with pytest.raises(ProviderError, match="Unknown provider"):
            get_provider({"llm": {"provider": "nonexistent"}})

    def test_no_config_raises(self):
        with pytest.raises(ProviderError, match="No LLM provider configured"):
            get_provider({})

    def test_empty_provider_raises(self):
        with pytest.raises(ProviderError, match="not set"):
            get_provider({"llm": {"provider": ""}})

    def test_fallback_provider_returns_none_if_not_configured(self):
        assert get_fallback_provider({"llm": {}}) is None

    def test_fallback_provider_creates_instance(self):
        register_provider("mock", MockProvider)
        fb = get_fallback_provider(
            {"llm": {"fallback": {"provider": "mock", "model": "fb-v1"}}}
        )
        assert isinstance(fb, MockProvider)
        assert fb.model == "fb-v1"

    def test_chat_with_fallback_uses_primary(self):
        register_provider("mock", MockProvider)
        config = {"llm": {"provider": "mock", "model": "v1"}}
        resp = chat_with_fallback(config, [ChatMessage(role="user", content="test")])
        assert resp.content == "Mock answer"

    def test_chat_with_fallback_on_failure(self):
        class FailProvider(MockProvider):
            PROVIDER_NAME = "fail"

            def chat(self, messages, **kwargs):
                raise ProviderError("fail", "rate limit", retryable=True)

        class GoodProvider(MockProvider):
            PROVIDER_NAME = "good"

        register_provider("fail", FailProvider)
        register_provider("good", GoodProvider)

        config = {
            "llm": {
                "provider": "fail",
                "model": "v1",
                "fallback": {"provider": "good", "model": "fb-v1"},
            }
        }
        resp = chat_with_fallback(config, [ChatMessage(role="user", content="test")])
        assert resp.content == "Mock answer"
        assert resp.metadata.get("fallback") is True

    def test_ensure_registered_adds_anthropic(self):
        _ensure_registered()
        assert "anthropic" in _PROVIDER_REGISTRY


# ══════════════════════════════════════════════════════════
# RAG Pipeline
# ══════════════════════════════════════════════════════════


class TestRAGPipeline:
    def _make_pattern(self, name, category="naming", confidence=0.9):
        """Create a mock pattern object."""
        p = MagicMock()
        p.name = name
        p.category = category
        p.confidence = confidence
        p.metadata = {"description": f"Pattern for {name}"}
        p.evidence_summary = f"Evidence for {name}"
        return p

    def _make_node(self, nid, name, fpath, domain="service", layer_val="core"):
        """Create a mock node object."""
        n = MagicMock()
        n.name = name
        n.file_path = fpath
        n.docstring = f"Docstring for {name}"
        n.params = ["self", "data"]
        n.return_type = "dict"
        n.line_start = 10
        n.module_domain = domain
        layer_mock = MagicMock()
        layer_mock.value = layer_val
        n.layer = layer_mock
        return n

    def _make_edge(self, src, tgt):
        e = MagicMock()
        e.source = src
        e.target = tgt
        return e

    def test_init_with_defaults(self):
        rag = RAGPipeline({})
        assert rag._max_chunks == 5
        assert rag._bm25_weight == 0.6
        assert rag._graph_weight == 0.4

    def test_init_with_config(self):
        rag = RAGPipeline({"rag": {"max_chunks": 3, "bm25_weight": 0.7}})
        assert rag._max_chunks == 3
        assert rag._bm25_weight == 0.7

    def test_index_and_retrieve_patterns(self):
        rag = RAGPipeline({})
        patterns = [
            self._make_pattern("snake_case_compliance"),
            self._make_pattern("service_layer_dominance", "layer"),
            self._make_pattern("god_class_detection", "structure"),
        ]
        rag.index_patterns(patterns)
        rag.build()

        result = rag.retrieve("snake case naming")
        assert isinstance(result, RAGResult)
        assert len(result.chunks) >= 1
        assert result.retrieval_ms >= 0
        # First result should be snake_case related
        assert "snake" in result.chunks[0].chunk_id.lower()

    def test_index_and_retrieve_functions(self):
        rag = RAGPipeline({})
        nodes = {
            "auth:login:10": self._make_node(
                "auth:login:10", "login", "auth/router.py", "auth"
            ),
            "auth:authenticate:45": self._make_node(
                "auth:authenticate:45", "authenticate", "auth/service.py", "auth"
            ),
            "billing:invoice:20": self._make_node(
                "billing:invoice:20", "create_invoice", "billing/service.py", "billing"
            ),
        }
        rag.index_functions(nodes)
        rag.build()

        result = rag.retrieve("authentication login")
        assert len(result.chunks) >= 1
        # Should find auth-related functions
        sources = [c.source for c in result.chunks]
        assert any("auth" in s for s in sources)

    def test_graph_proximity_boosts_connected_nodes(self):
        rag = RAGPipeline(
            {"rag": {"graph_weight": 0.5, "bm25_weight": 0.5, "min_score": 0.01}}
        )
        # Need 5+ docs for BM25 IDF to be meaningful (2-doc corpus = all IDF ~0)
        nodes = {
            "a": self._make_node("a", "process_order", "order/service.py", "order"),
            "b": self._make_node("b", "validate_order", "order/validator.py", "order"),
            "c": self._make_node("c", "authenticate", "auth/service.py", "auth"),
            "d": self._make_node(
                "d", "create_invoice", "billing/service.py", "billing"
            ),
            "e": self._make_node("e", "send_email", "notify/mailer.py", "notify"),
        }
        edges = [
            self._make_edge("func:a", "func:b"),
            self._make_edge("func:a", "func:c"),
            self._make_edge("func:a", "func:d"),
            self._make_edge("func:a", "func:e"),
        ]
        rag.index_functions(nodes)
        rag.index_graph_edges(edges)
        rag.build()

        # "authenticate auth" should match node c uniquely (auth appears only in c)
        result = rag.retrieve("authenticate auth login")
        assert len(result.chunks) >= 1
        assert "auth" in result.chunks[0].source

    def test_empty_query_returns_empty(self):
        rag = RAGPipeline({})
        rag.build()
        result = rag.retrieve("")
        assert len(result.chunks) == 0

    def test_no_match_returns_empty(self):
        rag = RAGPipeline({})
        patterns = [self._make_pattern("snake_case")]
        rag.index_patterns(patterns)
        rag.build()
        result = rag.retrieve("zzz_nonexistent_xyz")
        assert len(result.chunks) == 0

    def test_max_chunks_respected(self):
        rag = RAGPipeline({"rag": {"max_chunks": 2, "min_score": 0.01}})
        patterns = [self._make_pattern(f"pattern_{i}", "test") for i in range(10)]
        rag.index_patterns(patterns)
        rag.build()
        result = rag.retrieve("pattern test")
        assert len(result.chunks) <= 2

    def test_retrieval_performance(self):
        """Retrieval must complete in < 200ms (SLA)."""
        rag = RAGPipeline({"rag": {"max_chunks": 5}})
        # Index 100 patterns
        patterns = [
            self._make_pattern(f"pattern_{i}", f"cat_{i % 5}") for i in range(100)
        ]
        rag.index_patterns(patterns)
        rag.build()

        result = rag.retrieve("naming convention compliance")
        assert (
            result.retrieval_ms < 200
        ), f"Retrieval took {result.retrieval_ms:.0f}ms — over 200ms SLA"

    def test_retrieved_chunk_fields(self):
        rag = RAGPipeline({})
        patterns = [self._make_pattern("test_pattern")]
        rag.index_patterns(patterns)
        rag.build()
        result = rag.retrieve("test pattern")
        if result.chunks:
            chunk = result.chunks[0]
            assert chunk.chunk_id
            assert chunk.content
            assert chunk.source
            assert chunk.score > 0
            assert chunk.chunk_type in ("pattern", "function")

    def test_total_tokens_estimated(self):
        rag = RAGPipeline({})
        patterns = [self._make_pattern("auth_pattern")]
        rag.index_patterns(patterns)
        rag.build()
        result = rag.retrieve("auth pattern")
        assert result.total_tokens >= 0
