# HC-AI | ticket: MEM-M2-01
"""LLMProvider ABC — multi-LLM provider abstraction with BYOK.

Architecture spec: §4.3 AI Gateway.
Each provider implements chat(), count_tokens(), estimate_cost().
Factory pattern in client.py selects provider from config.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatMessage:
    """A single message in a chat conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    """Response from an LLM provider."""

    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""
    cost: float = 0.0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderError(Exception):
    """Raised when an LLM provider call fails."""

    def __init__(self, provider: str, message: str, retryable: bool = False):
        self.provider = provider
        self.retryable = retryable
        super().__init__(f"[{provider}] {message}")


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    BYOK: API key read from environment variable, never stored in code or vault.
    Each provider must implement chat(), count_tokens(), estimate_cost().
    """

    PROVIDER_NAME: str = ""

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._model = config.get("model", "")
        self._max_tokens = config.get("max_tokens", 1024)
        self._temperature = config.get("temperature", 0.3)

    @property
    def model(self) -> str:
        """Current model name."""
        return self._model

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage],
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat request to the provider.

        Args:
            messages: Conversation history.
            **kwargs: Provider-specific options (max_tokens, temperature, etc).

        Returns:
            ChatResponse with content, token counts, and cost.

        Raises:
            ProviderError: If the API call fails.
        """
        ...

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count for a text string.

        Used for context window management before sending to LLM.
        """
        ...

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for a given token count.

        Uses current model pricing. Returns 0.0 if pricing unknown.
        """
        ...

    def supports(self, feature: str) -> bool:
        """Check if provider supports a feature.

        Known features: 'streaming', 'tools', 'vision', 'json_mode'.
        """
        return False
