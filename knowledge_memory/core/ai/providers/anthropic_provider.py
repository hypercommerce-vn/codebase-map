# HC-AI | ticket: MEM-M2-01
"""AnthropicProvider — Claude LLM integration via Anthropic SDK.

BYOK: reads API key from env var specified in config['api_key_env'].
Supports: chat, token counting (estimate), cost estimation.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from knowledge_memory.core.ai.providers.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ProviderError,
)

logger = logging.getLogger(__name__)

# HC-AI | ticket: MEM-M2-01
# Pricing per 1M tokens (USD) — updated as of April 2026
_ANTHROPIC_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1M, output_per_1M)
    "claude-opus-4-20250514": (15.0, 75.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (0.80, 4.0),
}


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider.

    Config example::

        llm:
          provider: "anthropic"
          model: "claude-sonnet-4-20250514"
          api_key_env: "ANTHROPIC_API_KEY"
          max_tokens: 1024
          temperature: 0.3
    """

    PROVIDER_NAME = "anthropic"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._api_key_env = config.get("api_key_env", "ANTHROPIC_API_KEY")
        self._client = None

    def _get_client(self) -> Any:
        """Lazy-init Anthropic client."""
        if self._client is not None:
            return self._client

        api_key = os.environ.get(self._api_key_env)
        if not api_key:
            raise ProviderError(
                self.PROVIDER_NAME,
                f"API key not found. Set env var: {self._api_key_env}",
                retryable=False,
            )

        try:
            import anthropic

            self._client = anthropic.Anthropic(api_key=api_key)
            return self._client
        except ImportError:
            raise ProviderError(
                self.PROVIDER_NAME,
                "anthropic package not installed. Run: pip install anthropic",
                retryable=False,
            )

    def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Send chat request to Claude API."""
        client = self._get_client()

        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        temperature = kwargs.get("temperature", self._temperature)

        # Separate system message from conversation
        system_msg = ""
        api_messages: list[dict[str, str]] = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                api_messages.append({"role": m.role, "content": m.content})

        start = time.monotonic()
        try:
            create_kwargs: dict[str, Any] = {
                "model": self._model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_messages,
            }
            if system_msg:
                create_kwargs["system"] = system_msg

            response = client.messages.create(**create_kwargs)
        except Exception as e:
            retryable = "rate" in str(e).lower() or "overloaded" in str(e).lower()
            raise ProviderError(self.PROVIDER_NAME, str(e), retryable=retryable) from e

        elapsed_ms = (time.monotonic() - start) * 1000

        content = ""
        if response.content:
            content = response.content[0].text

        input_tokens = getattr(response.usage, "input_tokens", 0)
        output_tokens = getattr(response.usage, "output_tokens", 0)
        cost = self.estimate_cost(input_tokens, output_tokens)

        logger.info(
            "Anthropic chat: model=%s in=%d out=%d cost=$%.4f latency=%.0fms",
            self._model,
            input_tokens,
            output_tokens,
            cost,
            elapsed_ms,
        )

        return ChatResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self._model,
            provider=self.PROVIDER_NAME,
            cost=cost,
            latency_ms=elapsed_ms,
        )

    def count_tokens(self, text: str) -> int:
        """Estimate token count (approximate: 4 chars per token)."""
        # Anthropic doesn't have a public tokenizer yet
        # Use conservative estimate: ~4 chars per token
        return max(1, len(text) // 4)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD using current model pricing."""
        pricing = _ANTHROPIC_PRICING.get(self._model)
        if not pricing:
            # Fallback: try prefix match
            for model_key, prices in _ANTHROPIC_PRICING.items():
                if self._model.startswith(model_key.rsplit("-", 1)[0]):
                    pricing = prices
                    break
        if not pricing:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        return input_cost + output_cost

    def supports(self, feature: str) -> bool:
        """Anthropic supports streaming, tools, vision."""
        return feature in {"streaming", "tools", "vision", "json_mode"}
