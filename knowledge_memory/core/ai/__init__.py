# HC-AI | ticket: MEM-M2-01
"""AI Gateway — multi-LLM provider abstraction with BYOK.

See architecture.md §4.3. M2 implementation:
- providers/base.py — LLMProvider ABC
- providers/anthropic_provider.py — AnthropicProvider
- client.py — factory + fallback logic
- rag.py — BM25 + graph proximity RAG pipeline
"""

from knowledge_memory.core.ai.client import (
    chat_with_fallback,
    get_fallback_provider,
    get_provider,
)
from knowledge_memory.core.ai.providers.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
    ProviderError,
)
from knowledge_memory.core.ai.rag import RAGPipeline, RAGResult, RetrievedChunk

__all__ = [
    "LLMProvider",
    "ChatMessage",
    "ChatResponse",
    "ProviderError",
    "get_provider",
    "get_fallback_provider",
    "chat_with_fallback",
    "RAGPipeline",
    "RAGResult",
    "RetrievedChunk",
]
