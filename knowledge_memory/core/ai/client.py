# HC-AI | ticket: MEM-M2-01
"""AI Client — provider factory + fallback logic.

Architecture spec: §4.3 AI Gateway.
Selects provider from config, handles fallback on failure.
"""

from __future__ import annotations

import logging
from typing import Any

from knowledge_memory.core.ai.providers.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ProviderError,
)

logger = logging.getLogger(__name__)

# HC-AI | ticket: MEM-M2-01
_PROVIDER_REGISTRY: dict[str, type[LLMProvider]] = {}


def register_provider(name: str, cls: type[LLMProvider]) -> None:
    """Register a provider class by name."""
    _PROVIDER_REGISTRY[name] = cls


def get_provider(config: dict[str, Any]) -> LLMProvider:
    """Create an LLM provider instance from config.

    Config format::

        llm:
          provider: "anthropic"
          model: "claude-sonnet-4-20250514"
          api_key_env: "ANTHROPIC_API_KEY"
          max_tokens: 1024
          temperature: 0.3

    Raises:
        ProviderError: If provider not found or not configured.
    """
    llm_config = config.get("llm", {})
    if not llm_config:
        raise ProviderError("none", "No LLM provider configured in config.yaml")

    name = llm_config.get("provider", "")
    if not name:
        raise ProviderError("none", "llm.provider not set in config.yaml")

    # Lazy-register built-in providers
    _ensure_registered()

    cls = _PROVIDER_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_PROVIDER_REGISTRY.keys())) or "(none)"
        raise ProviderError(name, f"Unknown provider '{name}'. Available: {available}")

    return cls(llm_config)


def get_fallback_provider(config: dict[str, Any]) -> LLMProvider | None:
    """Create fallback provider from config, or None if not configured."""
    llm_config = config.get("llm", {})
    fallback_config = llm_config.get("fallback", {})
    if not fallback_config or not fallback_config.get("provider"):
        return None

    _ensure_registered()
    name = fallback_config["provider"]
    cls = _PROVIDER_REGISTRY.get(name)
    if cls is None:
        logger.warning("Fallback provider '%s' not available", name)
        return None

    return cls(fallback_config)


def chat_with_fallback(
    config: dict[str, Any],
    messages: list[ChatMessage],
    **kwargs: Any,
) -> ChatResponse:
    """Chat with automatic fallback on provider failure.

    If primary provider fails with a retryable error, tries fallback provider.
    Returns response with provider field indicating which was used.
    """
    primary = get_provider(config)
    try:
        return primary.chat(messages, **kwargs)
    except ProviderError as e:
        if not e.retryable:
            raise

        logger.warning("Primary provider failed: %s — trying fallback", e)
        fallback = get_fallback_provider(config)
        if fallback is None:
            raise ProviderError(
                primary.PROVIDER_NAME,
                f"Primary failed ({e}) and no fallback configured",
            ) from e

        logger.info("Falling back to %s", fallback.PROVIDER_NAME)
        response = fallback.chat(messages, **kwargs)
        response.metadata["fallback"] = True
        response.metadata["primary_error"] = str(e)
        return response


def _ensure_registered() -> None:
    """Lazy-register built-in providers on first use."""
    if _PROVIDER_REGISTRY:
        return

    from knowledge_memory.core.ai.providers.anthropic_provider import AnthropicProvider
    from knowledge_memory.core.ai.providers.gemini_provider import GeminiProvider
    from knowledge_memory.core.ai.providers.openai_provider import OpenAIProvider

    register_provider("anthropic", AnthropicProvider)
    register_provider("openai", OpenAIProvider)
    register_provider("gemini", GeminiProvider)
