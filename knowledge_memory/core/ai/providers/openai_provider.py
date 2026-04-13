# HC-AI | ticket: MEM-M2-09
"""OpenAIProvider — GPT LLM integration via OpenAI SDK.

BYOK: reads API key from env var specified in config['api_key_env'].
Supports: chat, token counting (tiktoken), cost estimation.
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

# HC-AI | ticket: MEM-M2-09
# Pricing per 1M tokens (USD) — as of April 2026
_OPENAI_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1M, output_per_1M)
    "gpt-4o": (2.50, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-4": (30.0, 60.0),
    "gpt-3.5-turbo": (0.50, 1.50),
    "o1": (15.0, 60.0),
    "o1-mini": (3.0, 12.0),
    "o3-mini": (1.10, 4.40),
}


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider.

    Config example::

        llm:
          provider: "openai"
          model: "gpt-4o-mini"
          api_key_env: "OPENAI_API_KEY"
          max_tokens: 1024
          temperature: 0.3
    """

    PROVIDER_NAME = "openai"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._api_key_env = config.get("api_key_env", "OPENAI_API_KEY")
        self._client = None

    def _get_client(self) -> Any:
        """Lazy-init OpenAI client."""
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
            import openai

            self._client = openai.OpenAI(api_key=api_key)
            return self._client
        except ImportError:
            raise ProviderError(
                self.PROVIDER_NAME,
                "openai package not installed. Run: pip install openai",
                retryable=False,
            )

    def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Send chat request to OpenAI API."""
        client = self._get_client()

        max_tokens = kwargs.get("max_tokens", self._max_tokens)
        temperature = kwargs.get("temperature", self._temperature)

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        start = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=self._model,
                messages=api_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            retryable = "rate" in str(e).lower() or "429" in str(e)
            raise ProviderError(self.PROVIDER_NAME, str(e), retryable=retryable) from e

        elapsed_ms = (time.monotonic() - start) * 1000

        content = ""
        if response.choices:
            content = response.choices[0].message.content or ""

        usage = response.usage
        input_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
        cost = self.estimate_cost(input_tokens, output_tokens)

        logger.info(
            "OpenAI chat: model=%s in=%d out=%d cost=$%.4f latency=%.0fms",
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
        """Count tokens using tiktoken if available, else estimate."""
        try:
            import tiktoken

            enc = tiktoken.encoding_for_model(self._model)
            return len(enc.encode(text))
        except (ImportError, KeyError):
            # Fallback: ~4 chars per token
            return max(1, len(text) // 4)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD using current model pricing."""
        pricing = _OPENAI_PRICING.get(self._model)
        if not pricing:
            for model_key, prices in _OPENAI_PRICING.items():
                if self._model.startswith(model_key):
                    pricing = prices
                    break
        if not pricing:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        return input_cost + output_cost

    def supports(self, feature: str) -> bool:
        """OpenAI supports streaming, tools, vision, json_mode."""
        return feature in {"streaming", "tools", "vision", "json_mode"}
