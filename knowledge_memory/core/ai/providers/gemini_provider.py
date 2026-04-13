# HC-AI | ticket: MEM-M2-10
"""GeminiProvider — Google Gemini LLM integration.

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

# HC-AI | ticket: MEM-M2-10
# Pricing per 1M tokens (USD) — as of April 2026
_GEMINI_PRICING: dict[str, tuple[float, float]] = {
    # (input_per_1M, output_per_1M)
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-flash-lite": (0.025, 0.10),
    "gemini-1.5-pro": (1.25, 5.0),
    "gemini-1.5-flash": (0.075, 0.30),
}


class GeminiProvider(LLMProvider):
    """Google Gemini provider.

    Config example::

        llm:
          provider: "gemini"
          model: "gemini-2.0-flash"
          api_key_env: "GOOGLE_API_KEY"
          max_tokens: 1024
          temperature: 0.3
    """

    PROVIDER_NAME = "gemini"

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self._api_key_env = config.get("api_key_env", "GOOGLE_API_KEY")
        self._client = None

    def _get_client(self) -> Any:
        """Lazy-init Google GenAI client."""
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
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(self._model)
            return self._client
        except ImportError:
            raise ProviderError(
                self.PROVIDER_NAME,
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai",
                retryable=False,
            )

    def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Send chat request to Gemini API."""
        client = self._get_client()

        # Convert ChatMessage to Gemini format
        # Gemini uses 'user' and 'model' roles
        system_instruction = ""
        gemini_messages: list[dict[str, str]] = []
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            elif m.role == "assistant":
                gemini_messages.append({"role": "model", "parts": [m.content]})
            else:
                gemini_messages.append({"role": "user", "parts": [m.content]})

        # Prepend system instruction as first user message if present
        if system_instruction and gemini_messages:
            first = gemini_messages[0]
            if first["role"] == "user":
                first["parts"] = [
                    f"[System instruction]\n{system_instruction}\n\n"
                    f"[User query]\n{first['parts'][0]}"
                ]

        start = time.monotonic()
        try:
            generation_config = {
                "max_output_tokens": kwargs.get("max_tokens", self._max_tokens),
                "temperature": kwargs.get("temperature", self._temperature),
            }
            response = client.generate_content(
                gemini_messages,
                generation_config=generation_config,
            )
        except Exception as e:
            retryable = "quota" in str(e).lower() or "429" in str(e)
            raise ProviderError(self.PROVIDER_NAME, str(e), retryable=retryable) from e

        elapsed_ms = (time.monotonic() - start) * 1000

        content = ""
        if response.text:
            content = response.text

        # Token counts from usage metadata
        usage = getattr(response, "usage_metadata", None)
        input_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        output_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0
        cost = self.estimate_cost(input_tokens, output_tokens)

        logger.info(
            "Gemini chat: model=%s in=%d out=%d cost=$%.4f latency=%.0fms",
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
        """Estimate token count (~4 chars per token)."""
        return max(1, len(text) // 4)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD using current model pricing."""
        pricing = _GEMINI_PRICING.get(self._model)
        if not pricing:
            for model_key, prices in _GEMINI_PRICING.items():
                if self._model.startswith(model_key):
                    pricing = prices
                    break
        if not pricing:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        return input_cost + output_cost

    def supports(self, feature: str) -> bool:
        """Gemini supports streaming, tools, vision."""
        return feature in {"streaming", "tools", "vision"}
