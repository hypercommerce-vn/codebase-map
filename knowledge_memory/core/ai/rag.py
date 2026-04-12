# HC-AI | ticket: MEM-M2-02
"""RAG pipeline — BM25 + AST graph proximity retrieval.

Architecture spec: §4.3 AI Gateway (RAG subsystem).
Uses BM25Index from M1 spike (core/search/bm25_search.py) + graph
structural proximity for re-ranking.

Performance SLA: context retrieval < 200ms.
Recall target: >= 75% on codebase queries.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from knowledge_memory.core.search.bm25_search import BM25Index, VietnameseTokenizer

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A single chunk retrieved by RAG."""

    chunk_id: str
    content: str
    source: str  # file_path or pattern name
    score: float  # combined BM25 + graph proximity score
    chunk_type: str = "pattern"  # "pattern" | "function" | "evidence"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGResult:
    """Result of a RAG retrieval operation."""

    query: str
    chunks: list[RetrievedChunk]
    retrieval_ms: float = 0.0
    total_tokens: int = 0


# HC-AI | ticket: MEM-M2-02
class RAGPipeline:
    """Retrieval-Augmented Generation pipeline.

    Two-stage retrieval:
    1. BM25 keyword search on vault patterns + function docs
    2. Graph proximity re-ranking using call graph structure

    Config::

        rag:
          max_chunks: 5
          bm25_weight: 0.6
          graph_weight: 0.4
          min_score: 0.3
    """

    def __init__(self, config: dict[str, Any]) -> None:
        rag_config = config.get("rag", {})
        self._max_chunks = rag_config.get("max_chunks", 5)
        self._bm25_weight = rag_config.get("bm25_weight", 0.6)
        self._graph_weight = rag_config.get("graph_weight", 0.4)
        self._min_score = rag_config.get("min_score", 0.3)

        self._bm25 = BM25Index(tokenizer=VietnameseTokenizer(strategy="compound"))
        self._indexed = False
        self._graph_data: dict[str, dict[str, Any]] = {}

    def index_patterns(self, patterns: list[Any]) -> None:
        """Index vault patterns for BM25 search.

        Each pattern is indexed by: name + category + metadata values.
        """
        for p in patterns:
            text_parts = [p.name, p.category]
            if hasattr(p, "metadata") and isinstance(p.metadata, dict):
                for v in p.metadata.values():
                    if isinstance(v, str):
                        text_parts.append(v)
            if hasattr(p, "evidence_summary") and p.evidence_summary:
                text_parts.append(str(p.evidence_summary))

            self._bm25.add_document(
                doc_id=f"pattern:{p.name}",
                text=" ".join(text_parts),
                metadata={"pattern": p, "type": "pattern"},
            )
        self._indexed = False

    def index_functions(self, nodes: dict[str, Any]) -> None:
        """Index graph nodes (functions) for BM25 search.

        Each node indexed by: name + file_path + docstring + params.
        """
        for node_id, node in nodes.items():
            text_parts = [
                getattr(node, "name", ""),
                getattr(node, "file_path", ""),
                getattr(node, "docstring", "") or "",
            ]
            params = getattr(node, "params", [])
            if params:
                text_parts.append(" ".join(str(p) for p in params))

            layer = getattr(node, "layer", None)
            if layer:
                text_parts.append(
                    str(layer.value) if hasattr(layer, "value") else str(layer)
                )

            domain = getattr(node, "module_domain", "")
            if domain:
                text_parts.append(domain)

            self._bm25.add_document(
                doc_id=f"func:{node_id}",
                text=" ".join(text_parts),
                metadata={
                    "node": node,
                    "type": "function",
                    "file_path": getattr(node, "file_path", ""),
                    "name": getattr(node, "name", ""),
                },
            )

        self._indexed = False

    def index_graph_edges(self, edges: list[Any]) -> None:
        """Build graph adjacency for proximity scoring.

        Stores caller/callee relationships for re-ranking.
        """
        for edge in edges:
            src = edge.source if hasattr(edge, "source") else str(edge)
            tgt = edge.target if hasattr(edge, "target") else ""
            if src not in self._graph_data:
                self._graph_data[src] = {"callers": [], "callees": []}
            if tgt not in self._graph_data:
                self._graph_data[tgt] = {"callers": [], "callees": []}
            self._graph_data[src]["callees"].append(tgt)
            self._graph_data[tgt]["callers"].append(src)

    def build(self) -> None:
        """Build BM25 index. Call after adding all documents."""
        self._bm25.build()
        self._indexed = True

    def retrieve(self, query: str) -> RAGResult:
        """Retrieve relevant chunks for a query.

        Two-stage: BM25 keyword match → graph proximity re-rank.
        Returns top max_chunks results within min_score threshold.
        """
        if not self._indexed:
            self.build()

        start = time.monotonic()

        # Stage 1: BM25 retrieval (over-fetch for re-ranking)
        bm25_results = self._bm25.search(
            query, top_k=self._max_chunks * 3, min_score=0.01
        )

        if not bm25_results:
            elapsed = (time.monotonic() - start) * 1000
            return RAGResult(query=query, chunks=[], retrieval_ms=elapsed)

        # Stage 2: Graph proximity re-ranking
        scored_chunks: list[tuple[float, RetrievedChunk]] = []

        # Normalize BM25 scores to [0, 1]
        max_bm25 = max(r.score for r in bm25_results) if bm25_results else 1.0
        max_bm25 = max(max_bm25, 0.01)

        for result in bm25_results:
            bm25_norm = result.score / max_bm25

            # Graph proximity score
            graph_score = self._compute_graph_proximity(result.doc_id, query)

            combined = self._bm25_weight * bm25_norm + self._graph_weight * graph_score

            if combined < self._min_score:
                continue

            doc = result.document
            chunk_type = doc.get("type", "pattern")
            source = doc.get("file_path", doc.get("id", result.doc_id))
            content = doc.get("text", "")

            # Build richer content for context
            if chunk_type == "function":
                node = doc.get("node")
                if node:
                    name = getattr(node, "name", "")
                    fpath = getattr(node, "file_path", "")
                    params = getattr(node, "params", [])
                    ret = getattr(node, "return_type", "")
                    line = getattr(node, "line_start", 0)
                    content = (
                        f"Function: {name}({', '.join(str(p) for p in params)})"
                        f"{' -> ' + ret if ret else ''}\n"
                        f"File: {fpath}:{line}\n"
                        f"Domain: {getattr(node, 'module_domain', '?')}\n"
                        f"Layer: {getattr(node, 'layer', '?')}"
                    )
                    source = f"{fpath}:{line}"
            elif chunk_type == "pattern":
                pattern = doc.get("pattern")
                if pattern:
                    content = (
                        f"Pattern: {pattern.name}\n"
                        f"Category: {pattern.category}\n"
                        f"Confidence: {getattr(pattern, 'confidence', 0):.0%}"
                    )
                    source = f"pattern:{pattern.name}"

            scored_chunks.append(
                (
                    combined,
                    RetrievedChunk(
                        chunk_id=result.doc_id,
                        content=content,
                        source=source,
                        score=combined,
                        chunk_type=chunk_type,
                        metadata={"bm25_score": bm25_norm, "graph_score": graph_score},
                    ),
                )
            )

        # Sort by combined score and take top N
        scored_chunks.sort(key=lambda x: -x[0])
        chunks = [c for _, c in scored_chunks[: self._max_chunks]]

        elapsed = (time.monotonic() - start) * 1000

        # Estimate total tokens for context window
        total_tokens = sum(len(c.content) // 4 for c in chunks)

        logger.info(
            "RAG retrieve: query='%s' chunks=%d ms=%.0f tokens~%d",
            query[:50],
            len(chunks),
            elapsed,
            total_tokens,
        )

        return RAGResult(
            query=query,
            chunks=chunks,
            retrieval_ms=elapsed,
            total_tokens=total_tokens,
        )

    def _compute_graph_proximity(self, doc_id: str, query: str) -> float:
        """Compute graph proximity score for a document.

        Higher score if the function has many callers/callees
        (structurally important in the codebase).
        """
        if not self._graph_data:
            return 0.0

        # Extract node key from doc_id (e.g., "func:module:function:line")
        node_key = doc_id
        if node_key.startswith("func:"):
            node_key = node_key[5:]
        elif node_key.startswith("pattern:"):
            # Patterns don't have graph proximity
            return 0.0

        info = self._graph_data.get(node_key)
        if not info:
            return 0.0

        # Score based on connectivity (normalized)
        callers = len(info.get("callers", []))
        callees = len(info.get("callees", []))
        connectivity = callers + callees

        # Normalize: 10+ connections = score 1.0
        return min(connectivity / 10.0, 1.0)
