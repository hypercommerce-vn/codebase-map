# HC-AI | ticket: MEM-M2-04
"""Ask command — natural language Q&A about the codebase.

Design ref: kmp-M2-design.html Screen A (ask command).
Flow: query → RAG retrieve → context build → LLM chat → format with citations.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from knowledge_memory.core.ai.client import chat_with_fallback
from knowledge_memory.core.ai.context_builder import ContextBuilder
from knowledge_memory.core.ai.providers.base import ProviderError
from knowledge_memory.core.ai.rag import RAGPipeline
from knowledge_memory.core.learners.pattern import Pattern

logger = logging.getLogger("codebase-memory.ask")


@dataclass
class AskResult:
    """Result of an ask query."""

    query: str
    answer: str
    citations: list[Citation]
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    retrieval_ms: float = 0.0
    generation_ms: float = 0.0
    total_ms: float = 0.0
    chunks_used: int = 0
    fallback_used: bool = False
    error: str = ""


@dataclass
class Citation:
    """A source citation from the answer."""

    source: str
    chunk_type: str = "function"
    relevance: float = 0.0


# HC-AI | ticket: MEM-M2-04
class AskEngine:
    """Codebase Q&A engine.

    Orchestrates: RAG retrieval → context building → LLM chat.
    Requires vault with patterns + graph data indexed.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._rag = RAGPipeline(config)
        self._ctx_builder = ContextBuilder(config)
        self._indexed = False

    def index_vault(
        self,
        patterns: list[Pattern],
        nodes: dict[str, Any] | None = None,
        edges: list[Any] | None = None,
    ) -> None:
        """Index vault data for RAG retrieval.

        Call once after loading vault, before any ask() calls.
        """
        if patterns:
            self._rag.index_patterns(patterns)
        if nodes:
            self._rag.index_functions(nodes)
        if edges:
            self._rag.index_graph_edges(edges)
        self._rag.build()
        self._indexed = True
        logger.info(
            "AskEngine indexed: %d patterns, %d nodes",
            len(patterns),
            len(nodes) if nodes else 0,
        )

    def ask(
        self,
        query: str,
        vault_summary: str = "",
    ) -> AskResult:
        """Ask a question about the codebase.

        Args:
            query: Natural language question.
            vault_summary: Optional vault summary for extra context.

        Returns:
            AskResult with answer, citations, cost, and timing.
        """
        total_start = time.monotonic()

        if not self._indexed:
            return AskResult(
                query=query,
                answer="",
                citations=[],
                error="Vault not indexed. Run bootstrap first.",
            )

        # Step 1: RAG retrieve
        rag_result = self._rag.retrieve(query)
        retrieval_ms = rag_result.retrieval_ms

        # Step 2: Build context
        ctx = self._ctx_builder.build(
            query=query,
            rag_result=rag_result,
            extra_context=vault_summary,
        )
        messages = self._ctx_builder.to_messages(ctx)

        # Step 3: LLM chat
        gen_start = time.monotonic()
        try:
            response = chat_with_fallback(self._config, messages)
        except ProviderError as e:
            total_ms = (time.monotonic() - total_start) * 1000
            return AskResult(
                query=query,
                answer="",
                citations=[],
                retrieval_ms=retrieval_ms,
                total_ms=total_ms,
                error=str(e),
            )
        generation_ms = (time.monotonic() - gen_start) * 1000

        # Build citations from chunks used
        citations = [
            Citation(
                source=chunk.source,
                chunk_type=chunk.chunk_type,
                relevance=chunk.score,
            )
            for chunk in ctx.context_chunks
        ]

        total_ms = (time.monotonic() - total_start) * 1000

        return AskResult(
            query=query,
            answer=response.content,
            citations=citations,
            provider=response.provider,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=response.cost,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
            total_ms=total_ms,
            chunks_used=len(ctx.context_chunks),
            fallback_used=response.metadata.get("fallback", False),
        )


def format_ask_result(result: AskResult) -> str:
    """Format AskResult for terminal output.

    Design ref: kmp-M2-design.html Screen A.
    """
    lines: list[str] = []

    lines.append("Knowledge Memory \u2014 Ask")
    lines.append(
        f"Provider: {result.provider} ({result.model}) "
        f"\u00b7 {result.chunks_used} chunks"
    )
    lines.append("")

    if result.error:
        lines.append(f"\u2717 Error: {result.error}")
        return "\n".join(lines)

    # Retrieval stats
    lines.append(
        f"\u25b6 Retrieving context... "
        f"\u2713 {result.chunks_used} chunks ({result.retrieval_ms:.0f}ms)"
    )
    lines.append(
        f"\u25b6 Generating answer... "
        f"\u2713 ({result.generation_ms:.0f}ms "
        f"\u00b7 {result.input_tokens} in + {result.output_tokens} out tokens)"
    )
    lines.append("")

    # Answer
    lines.append("Answer:")
    lines.append("")
    for line in result.answer.split("\n"):
        lines.append(f"  {line}")
    lines.append("")

    # Citations
    if result.citations:
        sep = "\u2501" * 50
        lines.append(sep)
        lines.append(f"Citations ({len(result.citations)} sources):")
        for c in result.citations:
            rel = f"{c.relevance:.0%}" if c.relevance else ""
            lines.append(f"  {c.source}  {rel}")

    # Cost
    lines.append("")
    lines.append(
        f"Cost: ${result.cost:.3f} "
        f"({result.input_tokens} in + {result.output_tokens} out "
        f"\u00b7 {result.provider} {result.model})"
    )

    if result.fallback_used:
        lines.append("(via fallback provider)")

    return "\n".join(lines)
