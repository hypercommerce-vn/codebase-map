# HC-AI | ticket: MEM-M2-03
"""Context builder — assemble RAG chunks into LLM prompt.

Takes retrieved chunks from RAGPipeline, formats them as context
for the LLM provider. Respects token budget and priority ordering.

Performance SLA: < 200ms (combined with RAG retrieval).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from knowledge_memory.core.ai.providers.base import ChatMessage
from knowledge_memory.core.ai.rag import RAGResult, RetrievedChunk


@dataclass
class ContextResult:
    """Result of context assembly."""

    system_prompt: str
    user_message: str
    context_chunks: list[RetrievedChunk]
    total_tokens_estimate: int
    build_ms: float = 0.0
    truncated: bool = False


# HC-AI | ticket: MEM-M2-03
_SYSTEM_TEMPLATE = (
    "You are a codebase expert assistant. "
    "Answer questions about the codebase using ONLY the context provided below. "
    "Always cite specific file paths and line numbers when referencing code. "
    "If the context doesn't contain enough information, say so clearly.\n\n"
    "## Codebase Context\n\n"
    "{context}\n\n"
    "## Rules\n"
    "- Be concise and factual\n"
    "- Cite file:line for every function mentioned\n"
    "- If unsure, say 'Not enough context to answer definitively'\n"
    "- Reference patterns by name and confidence percentage"
)


class ContextBuilder:
    """Build LLM prompts from RAG-retrieved chunks.

    Assembles context within a token budget, prioritizing
    higher-scored chunks. Formats as system prompt + user message.

    Config::

        rag:
          max_context_tokens: 4000
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        rag_config = (config or {}).get("rag", {})
        self._max_context_tokens = rag_config.get("max_context_tokens", 4000)

    def build(
        self,
        query: str,
        rag_result: RAGResult,
        extra_context: str = "",
    ) -> ContextResult:
        """Assemble context from RAG chunks into LLM messages.

        Args:
            query: Original user question.
            rag_result: Retrieved chunks from RAGPipeline.
            extra_context: Optional additional context (e.g., vault summary).

        Returns:
            ContextResult with formatted system prompt and user message.
        """
        start = time.monotonic()

        # Select chunks within token budget
        selected: list[RetrievedChunk] = []
        token_count = 0
        truncated = False

        # Chunks already sorted by score from RAG
        for chunk in rag_result.chunks:
            chunk_tokens = self._estimate_tokens(chunk.content)
            if token_count + chunk_tokens > self._max_context_tokens:
                truncated = True
                break
            selected.append(chunk)
            token_count += chunk_tokens

        # Format context sections
        context_parts: list[str] = []

        if extra_context:
            context_parts.append(f"### Vault Summary\n{extra_context}")

        for i, chunk in enumerate(selected, 1):
            header = self._chunk_header(chunk, i)
            context_parts.append(f"{header}\n{chunk.content}")

        context_text = (
            "\n\n".join(context_parts)
            if context_parts
            else ("No relevant context found in vault.")
        )

        system_prompt = _SYSTEM_TEMPLATE.format(context=context_text)
        user_message = query

        # Estimate total tokens
        total = self._estimate_tokens(system_prompt) + self._estimate_tokens(
            user_message
        )

        elapsed = (time.monotonic() - start) * 1000

        return ContextResult(
            system_prompt=system_prompt,
            user_message=user_message,
            context_chunks=selected,
            total_tokens_estimate=total,
            build_ms=elapsed,
            truncated=truncated,
        )

    def to_messages(self, ctx: ContextResult) -> list[ChatMessage]:
        """Convert ContextResult to ChatMessage list for LLM provider."""
        return [
            ChatMessage(role="system", content=ctx.system_prompt),
            ChatMessage(role="user", content=ctx.user_message),
        ]

    def _chunk_header(self, chunk: RetrievedChunk, index: int) -> str:
        """Format a chunk header with source and score."""
        type_label = chunk.chunk_type.upper()
        score_pct = f"{chunk.score:.0%}" if chunk.score < 1 else "100%"
        return f"### [{index}] {type_label}: {chunk.source} (relevance: {score_pct})"

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 chars per token."""
        return max(1, len(text) // 4)
