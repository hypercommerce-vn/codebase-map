# HC-AI | ticket: MEM-M2-03 / MEM-M2-04
"""Tests for ContextBuilder + AskEngine."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from knowledge_memory.core.ai.context_builder import ContextBuilder, ContextResult
from knowledge_memory.core.ai.providers.base import ChatResponse, ProviderError
from knowledge_memory.core.ai.rag import RAGResult, RetrievedChunk
from knowledge_memory.verticals.codebase.ask import (
    AskEngine,
    AskResult,
    Citation,
    format_ask_result,
)

# ── Helpers ──────────────────────────────────────


def _make_chunk(
    cid: str,
    content: str,
    source: str,
    score: float = 0.8,
    chunk_type: str = "function",
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=cid,
        content=content,
        source=source,
        score=score,
        chunk_type=chunk_type,
    )


def _make_rag_result(
    query: str = "test",
    chunks: list[RetrievedChunk] | None = None,
) -> RAGResult:
    return RAGResult(
        query=query,
        chunks=chunks or [],
        retrieval_ms=15.0,
        total_tokens=100,
    )


def _make_pattern(name, category="naming", confidence=0.9):
    p = MagicMock()
    p.name = name
    p.category = category
    p.confidence = confidence
    p.metadata = {"description": f"Pattern {name}"}
    p.evidence_summary = f"Evidence for {name}"
    return p


# ══════════════════════════════════════════════════
# ContextBuilder tests
# ══════════════════════════════════════════════════


class TestContextBuilder:
    def test_build_with_chunks(self):
        cb = ContextBuilder()
        chunks = [
            _make_chunk("c1", "def login(): pass", "auth/router.py:12"),
            _make_chunk("c2", "def authenticate(): ...", "auth/service.py:45"),
        ]
        rag = _make_rag_result("How does auth work?", chunks)
        result = cb.build("How does auth work?", rag)

        assert isinstance(result, ContextResult)
        assert "auth/router.py" in result.system_prompt
        assert "auth/service.py" in result.system_prompt
        assert result.user_message == "How does auth work?"
        assert len(result.context_chunks) == 2
        assert result.total_tokens_estimate > 0

    def test_build_with_empty_chunks(self):
        cb = ContextBuilder()
        rag = _make_rag_result("test", [])
        result = cb.build("test", rag)
        assert "No relevant context found" in result.system_prompt
        assert len(result.context_chunks) == 0

    def test_build_with_extra_context(self):
        cb = ContextBuilder()
        rag = _make_rag_result("test", [])
        result = cb.build("test", rag, extra_context="25 patterns, 1386 nodes")
        assert "25 patterns" in result.system_prompt

    def test_build_respects_token_budget(self):
        cb = ContextBuilder({"rag": {"max_context_tokens": 10}})
        chunks = [
            _make_chunk("c1", "x" * 100, "file1.py"),
            _make_chunk("c2", "y" * 100, "file2.py"),
        ]
        rag = _make_rag_result("test", chunks)
        result = cb.build("test", rag)
        assert result.truncated is True
        assert len(result.context_chunks) < 2

    def test_build_performance(self):
        """Context build must be fast (< 50ms)."""
        cb = ContextBuilder()
        chunks = [
            _make_chunk(f"c{i}", f"content {i}" * 20, f"file{i}.py") for i in range(5)
        ]
        rag = _make_rag_result("test query", chunks)
        result = cb.build("test query", rag)
        assert result.build_ms < 50

    def test_to_messages_format(self):
        cb = ContextBuilder()
        rag = _make_rag_result("test", [_make_chunk("c1", "code", "f.py")])
        ctx = cb.build("test", rag)
        messages = cb.to_messages(ctx)

        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert messages[1].content == "test"

    def test_chunk_header_format(self):
        cb = ContextBuilder()
        chunk = _make_chunk("c1", "content", "auth/service.py:45", score=0.85)
        header = cb._chunk_header(chunk, 1)
        assert "[1]" in header
        assert "FUNCTION" in header
        assert "auth/service.py" in header
        assert "85%" in header

    def test_system_prompt_has_rules(self):
        cb = ContextBuilder()
        rag = _make_rag_result("test", [_make_chunk("c1", "x", "f.py")])
        result = cb.build("test", rag)
        assert "codebase expert" in result.system_prompt
        assert "cite" in result.system_prompt.lower()


# ══════════════════════════════════════════════════
# AskEngine tests
# ══════════════════════════════════════════════════


class TestAskEngine:
    def _mock_config(self):
        return {
            "llm": {"provider": "mock", "model": "mock-v1"},
            "rag": {"max_chunks": 3, "min_score": 0.01},
        }

    def test_ask_not_indexed_returns_error(self):
        engine = AskEngine(self._mock_config())
        result = engine.ask("test")
        assert result.error
        assert "not indexed" in result.error.lower()

    def test_index_vault_sets_indexed(self):
        engine = AskEngine(self._mock_config())
        patterns = [_make_pattern("test_pattern")]
        engine.index_vault(patterns)
        assert engine._indexed is True

    @patch("knowledge_memory.verticals.codebase.ask.chat_with_fallback")
    def test_ask_returns_result(self, mock_chat):
        mock_chat.return_value = ChatResponse(
            content="Auth uses JWT tokens.",
            input_tokens=200,
            output_tokens=50,
            model="mock-v1",
            provider="mock",
            cost=0.002,
            latency_ms=500,
        )

        engine = AskEngine(self._mock_config())
        # Index enough patterns for BM25 to work
        patterns = [_make_pattern(f"p_{i}", f"cat_{i % 3}") for i in range(10)]
        engine.index_vault(patterns)

        result = engine.ask("test question")
        assert isinstance(result, AskResult)
        assert result.answer == "Auth uses JWT tokens."
        assert result.provider == "mock"
        assert result.cost == 0.002
        assert result.total_ms > 0
        assert result.error == ""

    @patch("knowledge_memory.verticals.codebase.ask.chat_with_fallback")
    def test_ask_with_citations(self, mock_chat):
        mock_chat.return_value = ChatResponse(
            content="Answer with citations",
            input_tokens=100,
            output_tokens=30,
            model="v1",
            provider="mock",
            cost=0.001,
        )

        engine = AskEngine(self._mock_config())
        patterns = [
            _make_pattern("auth_jwt", "auth"),
            _make_pattern("snake_case", "naming"),
            _make_pattern("service_layer", "layer"),
            _make_pattern("crud_prefix", "naming"),
            _make_pattern("domain_boundary", "structure"),
        ]
        engine.index_vault(patterns)
        result = engine.ask("auth jwt")

        assert isinstance(result.citations, list)
        # Citations come from RAG chunks used
        for c in result.citations:
            assert isinstance(c, Citation)
            assert c.source

    @patch("knowledge_memory.verticals.codebase.ask.chat_with_fallback")
    def test_ask_provider_error(self, mock_chat):
        mock_chat.side_effect = ProviderError(
            "mock", "connection failed", retryable=False
        )

        engine = AskEngine(self._mock_config())
        patterns = [_make_pattern(f"p_{i}") for i in range(5)]
        engine.index_vault(patterns)
        result = engine.ask("test")
        assert result.error
        assert "connection failed" in result.error

    @patch("knowledge_memory.verticals.codebase.ask.chat_with_fallback")
    def test_ask_fallback_used(self, mock_chat):
        mock_chat.return_value = ChatResponse(
            content="Fallback answer",
            input_tokens=100,
            output_tokens=30,
            model="fb-v1",
            provider="openai",
            cost=0.001,
            metadata={"fallback": True},
        )

        engine = AskEngine(self._mock_config())
        patterns = [_make_pattern(f"p_{i}") for i in range(5)]
        engine.index_vault(patterns)
        result = engine.ask("test")
        assert result.fallback_used is True


# ══════════════════════════════════════════════════
# Format output tests
# ══════════════════════════════════════════════════


class TestFormatAskResult:
    def test_format_success(self):
        result = AskResult(
            query="How does auth work?",
            answer="Auth uses JWT tokens.",
            citations=[
                Citation("auth/router.py:12", "function", 0.9),
                Citation("auth/service.py:45", "function", 0.85),
            ],
            provider="anthropic",
            model="claude-sonnet",
            input_tokens=200,
            output_tokens=50,
            cost=0.003,
            retrieval_ms=15.0,
            generation_ms=500.0,
            total_ms=520.0,
            chunks_used=2,
        )
        output = format_ask_result(result)
        assert "Knowledge Memory" in output
        assert "anthropic" in output
        assert "Auth uses JWT" in output
        assert "auth/router.py" in output
        assert "$0.003" in output

    def test_format_error(self):
        result = AskResult(
            query="test",
            answer="",
            citations=[],
            error="API key not found",
        )
        output = format_ask_result(result)
        assert "Error" in output
        assert "API key" in output

    def test_format_fallback(self):
        result = AskResult(
            query="test",
            answer="Fallback answer",
            citations=[],
            provider="openai",
            model="gpt-4o",
            fallback_used=True,
            cost=0.001,
        )
        output = format_ask_result(result)
        assert "fallback" in output.lower()

    def test_format_no_citations(self):
        result = AskResult(
            query="test",
            answer="No context available",
            citations=[],
            provider="mock",
            model="v1",
        )
        output = format_ask_result(result)
        assert "No context" in output

    def test_format_has_timing(self):
        result = AskResult(
            query="test",
            answer="answer",
            citations=[Citation("f.py", "function")],
            provider="mock",
            model="v1",
            retrieval_ms=15.0,
            generation_ms=500.0,
            chunks_used=1,
        )
        output = format_ask_result(result)
        assert "15ms" in output or "15" in output
        assert "500ms" in output or "500" in output
