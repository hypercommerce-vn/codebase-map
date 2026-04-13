# HC-AI | ticket: MEM-M2-09 / MEM-M2-10 / MEM-M2-11
"""Tests for OpenAI/Gemini providers + CostTracker + cross-provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from knowledge_memory.core.ai.client import _PROVIDER_REGISTRY, _ensure_registered
from knowledge_memory.core.ai.cost import CostTracker, UsageEntry, format_usage_summary
from knowledge_memory.core.ai.providers.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ProviderError,
)
from knowledge_memory.core.ai.providers.gemini_provider import GeminiProvider
from knowledge_memory.core.ai.providers.openai_provider import OpenAIProvider

# ══════════════════════════════════════════════════
# OpenAIProvider tests
# ══════════════════════════════════════════════════


class TestOpenAIProvider:
    def _make_provider(self, model="gpt-4o-mini"):
        return OpenAIProvider(
            {"provider": "openai", "model": model, "api_key_env": "OPENAI_API_KEY"}
        )

    def test_provider_name(self):
        p = self._make_provider()
        assert p.PROVIDER_NAME == "openai"
        assert p.model == "gpt-4o-mini"

    def test_no_api_key_raises(self):
        p = self._make_provider()
        p._api_key_env = "NONEXISTENT_KEY_XYZ"
        try:
            p._get_client()
            assert False, "Should have raised"
        except ProviderError as e:
            assert "not found" in str(e).lower()
            assert not e.retryable

    def test_estimate_cost_gpt4o_mini(self):
        p = self._make_provider("gpt-4o-mini")
        # 1000 input + 500 output tokens
        cost = p.estimate_cost(1000, 500)
        # gpt-4o-mini: $0.15/1M in, $0.60/1M out
        expected = (1000 / 1_000_000) * 0.15 + (500 / 1_000_000) * 0.60
        assert abs(cost - expected) < 0.0001

    def test_estimate_cost_gpt4o(self):
        p = self._make_provider("gpt-4o")
        cost = p.estimate_cost(10000, 5000)
        # gpt-4o: $2.50/1M in, $10.0/1M out
        expected = (10000 / 1_000_000) * 2.50 + (5000 / 1_000_000) * 10.0
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_unknown_model(self):
        p = self._make_provider("gpt-99-future")
        assert p.estimate_cost(1000, 500) == 0.0

    def test_count_tokens_fallback(self):
        p = self._make_provider()
        count = p.count_tokens("Hello world, this is a test.")
        assert count > 0

    def test_supports(self):
        p = self._make_provider()
        assert p.supports("streaming")
        assert p.supports("tools")
        assert p.supports("json_mode")
        assert not p.supports("nonexistent_feature")

    @patch.dict("os.environ", {"TEST_OPENAI_KEY": "sk-test"})
    def test_chat_mock(self):
        p = self._make_provider()
        p._api_key_env = "TEST_OPENAI_KEY"

        mock_client = MagicMock()
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 50

        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client.chat.completions.create.return_value = mock_response
        p._client = mock_client

        result = p.chat([ChatMessage(role="user", content="Hello")])
        assert isinstance(result, ChatResponse)
        assert result.content == "Test response"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.provider == "openai"


# ══════════════════════════════════════════════════
# GeminiProvider tests
# ══════════════════════════════════════════════════


class TestGeminiProvider:
    def _make_provider(self, model="gemini-2.0-flash"):
        return GeminiProvider(
            {"provider": "gemini", "model": model, "api_key_env": "GOOGLE_API_KEY"}
        )

    def test_provider_name(self):
        p = self._make_provider()
        assert p.PROVIDER_NAME == "gemini"
        assert p.model == "gemini-2.0-flash"

    def test_no_api_key_raises(self):
        p = self._make_provider()
        p._api_key_env = "NONEXISTENT_GEMINI_KEY"
        try:
            p._get_client()
            assert False, "Should have raised"
        except ProviderError as e:
            assert "not found" in str(e).lower()

    def test_estimate_cost_flash(self):
        p = self._make_provider("gemini-2.0-flash")
        cost = p.estimate_cost(10000, 5000)
        # flash: $0.10/1M in, $0.40/1M out
        expected = (10000 / 1_000_000) * 0.10 + (5000 / 1_000_000) * 0.40
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_pro(self):
        p = self._make_provider("gemini-1.5-pro")
        cost = p.estimate_cost(10000, 5000)
        expected = (10000 / 1_000_000) * 1.25 + (5000 / 1_000_000) * 5.0
        assert abs(cost - expected) < 0.001

    def test_estimate_cost_unknown(self):
        p = self._make_provider("gemini-99-future")
        assert p.estimate_cost(1000, 500) == 0.0

    def test_count_tokens(self):
        p = self._make_provider()
        count = p.count_tokens("Hello world")
        assert count > 0

    def test_supports(self):
        p = self._make_provider()
        assert p.supports("streaming")
        assert p.supports("tools")
        assert p.supports("vision")
        assert not p.supports("json_mode")


# ══════════════════════════════════════════════════
# CostTracker tests
# ══════════════════════════════════════════════════


class TestCostTracker:
    def test_record_entry(self):
        tracker = CostTracker()
        entry = tracker.record("anthropic", "claude-sonnet", 200, 50, 0.003)
        assert isinstance(entry, UsageEntry)
        assert entry.provider == "anthropic"
        assert entry.cost == 0.003
        assert len(tracker.entries) == 1

    def test_summary_empty(self):
        tracker = CostTracker()
        s = tracker.summary()
        assert s.total_calls == 0
        assert s.total_cost == 0.0

    def test_summary_single_provider(self):
        tracker = CostTracker()
        tracker.record("anthropic", "sonnet", 200, 50, 0.003)
        tracker.record("anthropic", "sonnet", 300, 80, 0.005)
        s = tracker.summary()
        assert s.total_calls == 2
        assert s.total_input_tokens == 500
        assert s.total_output_tokens == 130
        assert abs(s.total_cost - 0.008) < 0.0001
        assert "anthropic" in s.by_provider
        assert s.by_provider["anthropic"].calls == 2

    def test_summary_multi_provider(self):
        tracker = CostTracker()
        tracker.record("anthropic", "sonnet", 200, 50, 0.003)
        tracker.record("openai", "gpt-4o-mini", 150, 40, 0.001)
        tracker.record("gemini", "flash", 100, 30, 0.0005)
        s = tracker.summary()
        assert s.total_calls == 3
        assert len(s.by_provider) == 3
        assert "anthropic" in s.by_provider
        assert "openai" in s.by_provider
        assert "gemini" in s.by_provider

    def test_most_expensive_tracked(self):
        tracker = CostTracker()
        tracker.record("anthropic", "sonnet", 200, 50, 0.003, query_preview="cheap q")
        tracker.record(
            "anthropic", "opus", 1000, 500, 0.050, query_preview="expensive query"
        )
        s = tracker.summary()
        assert s.most_expensive_cost == 0.050
        assert "expensive" in s.most_expensive_query

    def test_clear(self):
        tracker = CostTracker()
        tracker.record("anthropic", "sonnet", 200, 50, 0.003)
        assert len(tracker.entries) == 1
        tracker.clear()
        assert len(tracker.entries) == 0
        s = tracker.summary()
        assert s.total_calls == 0


# ══════════════════════════════════════════════════
# Format usage summary tests
# ══════════════════════════════════════════════════


class TestFormatUsageSummary:
    def test_format_empty(self):
        tracker = CostTracker()
        output = format_usage_summary(tracker.summary())
        assert "No LLM calls" in output

    def test_format_with_data(self):
        tracker = CostTracker()
        tracker.record("anthropic", "sonnet", 4200, 2100, 0.042)
        tracker.record("openai", "gpt-4o-mini", 890, 450, 0.004)
        output = format_usage_summary(tracker.summary())
        assert "anthropic" in output
        assert "openai" in output
        assert "0.042" in output
        assert "Total" in output

    def test_format_avg_cost(self):
        tracker = CostTracker()
        tracker.record("anthropic", "sonnet", 200, 50, 0.006)
        tracker.record("anthropic", "sonnet", 200, 50, 0.006)
        output = format_usage_summary(tracker.summary())
        assert "$0.006" in output  # avg

    def test_format_most_expensive(self):
        tracker = CostTracker()
        tracker.record("anthropic", "opus", 1000, 500, 0.050, query_preview="big query")
        output = format_usage_summary(tracker.summary())
        assert "big query" in output


# ══════════════════════════════════════════════════
# Cross-provider factory registration
# ══════════════════════════════════════════════════


class TestProviderRegistry:
    def test_all_three_registered(self):
        _PROVIDER_REGISTRY.clear()
        _ensure_registered()
        assert "anthropic" in _PROVIDER_REGISTRY
        assert "openai" in _PROVIDER_REGISTRY
        assert "gemini" in _PROVIDER_REGISTRY

    def test_provider_interface_compliance(self):
        """All providers implement LLMProvider ABC correctly."""
        _PROVIDER_REGISTRY.clear()
        _ensure_registered()
        for name, cls in _PROVIDER_REGISTRY.items():
            instance = cls({"provider": name, "model": "test"})
            assert isinstance(instance, LLMProvider)
            assert instance.PROVIDER_NAME == name
            # count_tokens and estimate_cost should work without API key
            assert instance.count_tokens("hello") > 0
            assert instance.estimate_cost(0, 0) == 0.0

    def test_cost_comparison_across_providers(self):
        """Same token count, different costs per provider."""
        _PROVIDER_REGISTRY.clear()
        _ensure_registered()

        configs = {
            "anthropic": {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
            "openai": {"provider": "openai", "model": "gpt-4o-mini"},
            "gemini": {"provider": "gemini", "model": "gemini-2.0-flash"},
        }

        costs = {}
        for name, cfg in configs.items():
            provider = _PROVIDER_REGISTRY[name](cfg)
            costs[name] = provider.estimate_cost(10000, 5000)

        # All should return positive costs
        for name, cost in costs.items():
            assert cost > 0, f"{name} returned zero cost"

        # Gemini flash should be cheapest, Anthropic in middle
        assert costs["gemini"] < costs["openai"] < costs["anthropic"]
