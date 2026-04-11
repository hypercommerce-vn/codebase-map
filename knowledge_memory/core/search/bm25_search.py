# HC-AI | ticket: MEM-M1-12
"""BM25 full-text search with Vietnamese language support.

Spike validation: Can BM25 effectively search Vietnamese + English
mixed content in codebase patterns and evidence?

Key challenges:
- Vietnamese uses spaces between syllables, not words
  ("quản lý đơn hàng" = 4 syllables, 1 concept: "order management")
- Codebase context mixes Vietnamese comments + English identifiers
- Need recall ≥75% on Vietnamese queries

Approach:
1. VietnameseTokenizer — syllable-aware tokenizer with bigram expansion
2. BM25Index — wrapper around rank_bm25 with tokenizer integration
3. PatternSearchEngine — search committed patterns in vault
"""

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# HC-AI | ticket: MEM-M1-12
# Vietnamese diacritics and tone marks for detection
_VIET_TONE_MARKS = set(
    "àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệ"
    "ìíỉĩịòóỏõọôốồổỗộơớờởỡợ"
    "ùúủũụưứừửữựỳýỷỹỵđ"
    "ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆ"
    "ÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢ"
    "ÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ"
)

# Common Vietnamese compound words in tech/codebase context
# HC-AI | ticket: MEM-M1-12
_VIET_COMPOUNDS: Dict[str, str] = {
    "quản lý": "quản_lý",
    "đơn hàng": "đơn_hàng",
    "khách hàng": "khách_hàng",
    "sản phẩm": "sản_phẩm",
    "thanh toán": "thanh_toán",
    "giỏ hàng": "giỏ_hàng",
    "tài khoản": "tài_khoản",
    "người dùng": "người_dùng",
    "hệ thống": "hệ_thống",
    "cơ sở dữ liệu": "cơ_sở_dữ_liệu",
    "dữ liệu": "dữ_liệu",
    "giao diện": "giao_diện",
    "chức năng": "chức_năng",
    "kiến trúc": "kiến_trúc",
    "bảo mật": "bảo_mật",
    "xác thực": "xác_thực",
    "phân quyền": "phân_quyền",
    "cấu hình": "cấu_hình",
    "triển khai": "triển_khai",
    "mã nguồn": "mã_nguồn",
    "kiểm thử": "kiểm_thử",
    "lỗi": "lỗi",
    "tệp tin": "tệp_tin",
    "thư mục": "thư_mục",
    "truy vấn": "truy_vấn",
    "tối ưu": "tối_ưu",
    "hiệu suất": "hiệu_suất",
    "tích hợp": "tích_hợp",
    "phụ thuộc": "phụ_thuộc",
    "lớp dịch vụ": "lớp_dịch_vụ",
    "lớp mô hình": "lớp_mô_hình",
    "lớp điều khiển": "lớp_điều_khiển",
    "xử lý": "xử_lý",
    "báo cáo": "báo_cáo",
    "nhập khẩu": "nhập_khẩu",
    "xuất khẩu": "xuất_khẩu",
    "đăng nhập": "đăng_nhập",
    "đăng ký": "đăng_ký",
    "cập nhật": "cập_nhật",
    "xóa": "xóa",
    "tìm kiếm": "tìm_kiếm",
    "danh sách": "danh_sách",
}

# Sort compounds by length (longest first) for greedy matching
_SORTED_COMPOUNDS = sorted(_VIET_COMPOUNDS.items(), key=lambda x: -len(x[0]))

# HC-AI | ticket: MEM-M1-12
# Stopwords: Vietnamese + English (minimal set for codebase context)
_STOPWORDS_VI = {
    "và",
    "của",
    "là",
    "có",
    "được",
    "cho",
    "với",
    "trong",
    "này",
    "các",
    "một",
    "không",
    "những",
    "đã",
    "để",
    "từ",
    "đến",
    "theo",
    "về",
    "sẽ",
    "khi",
    "tại",
    "bởi",
    "hoặc",
    "hay",
    "nhưng",
    "vì",
    "nếu",
    "thì",
    "cũng",
    "mà",
    "do",
    "nên",
    "rất",
    "đều",
    "như",
}

_STOPWORDS_EN = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "shall",
    "of",
    "in",
    "to",
    "for",
    "with",
    "on",
    "at",
    "by",
    "from",
    "as",
    "into",
    "through",
    "during",
    "before",
    "after",
    "and",
    "but",
    "or",
    "nor",
    "not",
    "so",
    "if",
    "then",
    "than",
    "that",
    "this",
    "it",
    "its",
    "they",
    "them",
    "their",
}

_STOPWORDS = _STOPWORDS_VI | _STOPWORDS_EN

# Code identifier pattern (camelCase, snake_case, PascalCase)
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*")
_CAMEL_SPLIT_RE = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def _has_vietnamese(text: str) -> bool:
    """Check if text contains Vietnamese diacritical characters."""
    return any(c in _VIET_TONE_MARKS for c in text)


def _split_camel_case(name: str) -> List[str]:
    """Split camelCase/PascalCase into words.

    >>> _split_camel_case("CustomerService")
    ['Customer', 'Service']
    >>> _split_camel_case("get_order_by_id")
    ['get', 'order', 'by', 'id']
    """
    # First split on underscores
    parts = name.split("_")
    result = []
    for part in parts:
        if not part:
            continue
        # Split camelCase
        sub_parts = _CAMEL_SPLIT_RE.split(part)
        result.extend(s.lower() for s in sub_parts if s)
    return result


def _apply_compound_detection(text: str) -> str:
    """Replace known Vietnamese compound words with joined tokens.

    Greedy longest-match replacement.
    """
    lower = text.lower()
    for compound, joined in _SORTED_COMPOUNDS:
        lower = lower.replace(compound, joined)
    return lower


@dataclass
class VietnameseTokenizer:
    """Tokenizer with Vietnamese compound word detection.

    Strategies:
    - ``syllable``: Split on whitespace only (baseline)
    - ``compound``: Detect Vietnamese compounds → join with underscore
    - ``bigram``: Add bigrams of consecutive syllables

    All strategies also split code identifiers (camelCase, snake_case).
    """

    # HC-AI | ticket: MEM-M1-12
    strategy: str = "compound"
    remove_stopwords: bool = True
    min_token_length: int = 2

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into search tokens."""
        if not text or not text.strip():
            return []

        if self.strategy == "syllable":
            return self._tokenize_syllable(text)
        elif self.strategy == "bigram":
            return self._tokenize_bigram(text)
        else:  # compound (default)
            return self._tokenize_compound(text)

    def _tokenize_syllable(self, text: str) -> List[str]:
        """Baseline: split on whitespace + punctuation."""
        tokens = self._extract_base_tokens(text)
        return self._filter(tokens)

    def _tokenize_compound(self, text: str) -> List[str]:
        """Compound detection: join Vietnamese compounds.

        Strategy: extract code identifiers first (preserve case for
        camelCase splitting), then apply compound detection on rest.
        """
        tokens = self._extract_base_tokens(text, apply_compounds=True)
        return self._filter(tokens)

    def _tokenize_bigram(self, text: str) -> List[str]:
        """Bigram expansion: unigrams + Vietnamese bigrams."""
        # Start with compound tokens
        compound_tokens = self._tokenize_compound(text)

        # Add bigrams from original syllables (for Vietnamese coverage)
        syllables = self._extract_base_tokens(text, apply_compounds=False)
        syllables = [s for s in syllables if s not in _STOPWORDS]
        bigrams = []
        for i in range(len(syllables) - 1):
            if _has_vietnamese(syllables[i]) or _has_vietnamese(syllables[i + 1]):
                bigrams.append(f"{syllables[i]}_{syllables[i + 1]}")

        return compound_tokens + bigrams

    def _extract_base_tokens(
        self, text: str, apply_compounds: bool = False
    ) -> List[str]:
        """Extract tokens from mixed Vietnamese + English text.

        Args:
            text: Input text (Vietnamese, English, or mixed).
            apply_compounds: If True, detect Vietnamese compound words
                and join them with underscores before tokenizing.
        """
        tokens: List[str] = []

        # Split on whitespace and common punctuation first
        words = re.split(r'[\s,.:;!?\(\)\{\}\[\]"\'`/\\|<>@#$%^&*+=~\-]+', text)

        # Separate code identifiers from non-code words
        code_words: List[str] = []
        text_words: List[str] = []
        for w in words:
            w = w.strip()
            if not w:
                continue
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", w):
                code_words.append(w)
            else:
                text_words.append(w)

        # Process code identifiers (split camelCase/snake_case)
        for cw in code_words:
            tokens.extend(_split_camel_case(cw))

        # Process text words (Vietnamese + mixed)
        if apply_compounds and text_words:
            # Rejoin and apply compound detection, then re-split
            joined = " ".join(text_words)
            compound_text = _apply_compound_detection(joined)
            for part in compound_text.split():
                part = part.strip()
                if part:
                    tokens.append(part)
        else:
            for tw in text_words:
                tokens.append(tw.lower())

        return tokens

    def _filter(self, tokens: List[str]) -> List[str]:
        """Apply stopword removal and min-length filter."""
        result = []
        for t in tokens:
            t = t.lower().strip()
            if len(t) < self.min_token_length:
                continue
            if self.remove_stopwords and t in _STOPWORDS:
                continue
            result.append(t)
        return result


# ── BM25 Index ──────────────────────────────────────────


@dataclass
class SearchResult:
    """A single search result with score and document reference."""

    doc_id: str
    score: float
    document: Dict[str, Any] = field(default_factory=dict)


class BM25Index:
    """BM25 search index with Vietnamese tokenizer integration.

    Uses rank_bm25 library for scoring. Wraps with:
    - VietnameseTokenizer for indexing + query tokenization
    - Document metadata storage for result enrichment
    - Configurable k1/b parameters

    HC-AI | ticket: MEM-M1-12
    """

    def __init__(
        self,
        tokenizer: Optional[VietnameseTokenizer] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self._tokenizer = tokenizer or VietnameseTokenizer()
        self._k1 = k1
        self._b = b
        self._documents: List[Dict[str, Any]] = []
        self._doc_ids: List[str] = []
        self._corpus_tokens: List[List[str]] = []
        self._bm25 = None
        self._indexed = False

    @property
    def document_count(self) -> int:
        """Number of indexed documents."""
        return len(self._documents)

    @property
    def is_indexed(self) -> bool:
        """Whether the index has been built."""
        return self._indexed

    def add_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a document to the index (call build() after adding all docs)."""
        tokens = self._tokenizer.tokenize(text)
        self._doc_ids.append(doc_id)
        self._corpus_tokens.append(tokens)
        self._documents.append(
            {
                "id": doc_id,
                "text": text,
                "tokens": tokens,
                **(metadata or {}),
            }
        )
        self._indexed = False  # Invalidate existing index

    def build(self) -> None:
        """Build the BM25 index from added documents."""
        if not self._corpus_tokens:
            self._indexed = True
            return

        try:
            from rank_bm25 import BM25Okapi

            self._bm25 = BM25Okapi(self._corpus_tokens, k1=self._k1, b=self._b)
            self._indexed = True
        except ImportError:
            # Fallback: pure-Python BM25 implementation
            self._bm25 = _PureBM25(self._corpus_tokens, k1=self._k1, b=self._b)
            self._indexed = True

    def search(
        self, query: str, top_k: int = 10, min_score: float = 0.0
    ) -> List[SearchResult]:
        """Search the index with a query string.

        Args:
            query: Search query (Vietnamese, English, or mixed).
            top_k: Maximum number of results to return.
            min_score: Minimum BM25 score threshold.

        Returns:
            List of SearchResult sorted by score descending.
        """
        if not self._indexed:
            self.build()

        if self._bm25 is None or not self._corpus_tokens:
            return []

        query_tokens = self._tokenizer.tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Rank by score
        scored_docs = []
        for i, score in enumerate(scores):
            if score > min_score:
                scored_docs.append((i, float(score)))

        scored_docs.sort(key=lambda x: -x[1])

        results = []
        for idx, score in scored_docs[:top_k]:
            results.append(
                SearchResult(
                    doc_id=self._doc_ids[idx],
                    score=score,
                    document=self._documents[idx],
                )
            )

        return results

    def search_patterns(
        self, query: str, patterns: list, top_k: int = 10
    ) -> List[SearchResult]:
        """Convenience: index Pattern objects and search.

        Each pattern is indexed by: name + category + metadata description.
        """
        # Re-index if needed
        if not self._indexed or self.document_count == 0:
            for p in patterns:
                text_parts = [p.name, p.category]
                if hasattr(p, "metadata") and isinstance(p.metadata, dict):
                    for v in p.metadata.values():
                        if isinstance(v, str):
                            text_parts.append(v)
                self.add_document(
                    doc_id=p.name,
                    text=" ".join(text_parts),
                    metadata={"pattern": p},
                )
            self.build()

        return self.search(query, top_k=top_k)


# ── Pure Python BM25 fallback ───────────────────────────


class _PureBM25:
    """Minimal BM25 Okapi implementation (no numpy dependency).

    HC-AI | ticket: MEM-M1-12
    Used as fallback when rank_bm25 is not installed.
    """

    def __init__(
        self,
        corpus: List[List[str]],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_lengths) / max(self.corpus_size, 1)
        self.corpus = corpus

        # Build document frequency
        self.df: Dict[str, int] = {}
        for doc in corpus:
            seen = set(doc)
            for token in seen:
                self.df[token] = self.df.get(token, 0) + 1

        # Pre-compute IDF
        self.idf: Dict[str, float] = {}
        for token, freq in self.df.items():
            self.idf[token] = math.log(
                (self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0
            )

    def get_scores(self, query: List[str]) -> List[float]:
        """Compute BM25 scores for all documents given query tokens."""
        scores = [0.0] * self.corpus_size
        for q in query:
            if q not in self.idf:
                continue
            idf_val = self.idf[q]
            for i, doc in enumerate(self.corpus):
                tf = doc.count(q)
                if tf == 0:
                    continue
                dl = self.doc_lengths[i]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf_val * numerator / denominator
        return scores


# ── Recall Benchmark ─────────────────────────────────────


@dataclass
class BenchmarkResult:
    """Result of a recall benchmark run."""

    strategy: str
    total_queries: int
    total_relevant: int
    total_retrieved: int
    recall: float
    precision: float
    f1: float
    per_query: List[Dict[str, Any]] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary."""
        return (
            f"Strategy: {self.strategy}\n"
            f"  Queries: {self.total_queries}\n"
            f"  Recall:    {self.recall:.1%}\n"
            f"  Precision: {self.precision:.1%}\n"
            f"  F1:        {self.f1:.1%}\n"
        )


def run_recall_benchmark(
    documents: List[Tuple[str, str]],
    queries: List[Tuple[str, List[str]]],
    strategy: str = "compound",
    top_k: int = 5,
) -> BenchmarkResult:
    """Run recall benchmark on a set of documents and queries.

    Args:
        documents: List of (doc_id, text) tuples.
        queries: List of (query, [expected_doc_ids]) tuples.
        strategy: Tokenizer strategy ("syllable", "compound", "bigram").
        top_k: Number of results to retrieve per query.

    Returns:
        BenchmarkResult with recall, precision, F1 metrics.
    """
    tokenizer = VietnameseTokenizer(strategy=strategy)
    index = BM25Index(tokenizer=tokenizer)

    for doc_id, text in documents:
        index.add_document(doc_id, text)
    index.build()

    total_relevant = 0
    total_retrieved_relevant = 0
    total_retrieved = 0
    per_query = []

    for query_text, expected_ids in queries:
        results = index.search(query_text, top_k=top_k)
        retrieved_ids = {r.doc_id for r in results}
        expected_set = set(expected_ids)

        hits = retrieved_ids & expected_set
        q_recall = len(hits) / max(len(expected_set), 1)
        q_precision = len(hits) / max(len(retrieved_ids), 1)

        total_relevant += len(expected_set)
        total_retrieved_relevant += len(hits)
        total_retrieved += len(retrieved_ids)

        per_query.append(
            {
                "query": query_text,
                "expected": expected_ids,
                "retrieved": [r.doc_id for r in results],
                "hits": list(hits),
                "recall": q_recall,
                "precision": q_precision,
            }
        )

    recall = total_retrieved_relevant / max(total_relevant, 1)
    precision = total_retrieved_relevant / max(total_retrieved, 1)
    f1 = (
        2 * recall * precision / max(recall + precision, 1e-9)
        if (recall + precision) > 0
        else 0.0
    )

    return BenchmarkResult(
        strategy=strategy,
        total_queries=len(queries),
        total_relevant=total_relevant,
        total_retrieved=total_retrieved_relevant,
        recall=recall,
        precision=precision,
        f1=f1,
        per_query=per_query,
    )
