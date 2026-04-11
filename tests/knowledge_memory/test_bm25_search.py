# HC-AI | ticket: MEM-M1-12
"""Tests for BM25 search with Vietnamese language validation.

Spike: Validate BM25 recall ≥75% on Vietnamese codebase content.
"""

from knowledge_memory.core.search.bm25_search import (
    BM25Index,
    VietnameseTokenizer,
    _apply_compound_detection,
    _has_vietnamese,
    _PureBM25,
    _split_camel_case,
    run_recall_benchmark,
)

# ── Vietnamese Detection ─────────────────────────────────


class TestVietnameseDetection:
    """Test Vietnamese character detection."""

    def test_detect_vietnamese_text(self):
        assert _has_vietnamese("quản lý đơn hàng")

    def test_detect_no_vietnamese(self):
        assert not _has_vietnamese("customer service layer")

    def test_detect_mixed(self):
        assert _has_vietnamese("CustomerService quản lý")

    def test_empty_text(self):
        assert not _has_vietnamese("")

    def test_uppercase_vietnamese(self):
        assert _has_vietnamese("ĐƠN HÀNG")


# ── CamelCase Splitting ──────────────────────────────────


class TestCamelCaseSplit:
    """Test code identifier splitting."""

    def test_pascal_case(self):
        assert _split_camel_case("CustomerService") == ["customer", "service"]

    def test_snake_case(self):
        assert _split_camel_case("get_order_by_id") == [
            "get",
            "order",
            "by",
            "id",
        ]

    def test_camel_case(self):
        assert _split_camel_case("getOrderById") == [
            "get",
            "order",
            "by",
            "id",
        ]

    def test_single_word(self):
        assert _split_camel_case("order") == ["order"]

    def test_acronym(self):
        result = _split_camel_case("HTMLParser")
        assert "html" in result or "parser" in result

    def test_empty(self):
        assert _split_camel_case("") == []

    def test_underscore_prefix(self):
        result = _split_camel_case("_private_method")
        assert "private" in result
        assert "method" in result


# ── Compound Detection ───────────────────────────────────


class TestCompoundDetection:
    """Test Vietnamese compound word joining."""

    def test_basic_compound(self):
        result = _apply_compound_detection("quản lý đơn hàng")
        assert "quản_lý" in result
        assert "đơn_hàng" in result

    def test_multi_word_compound(self):
        result = _apply_compound_detection("cơ sở dữ liệu")
        assert "cơ_sở_dữ_liệu" in result

    def test_no_compound(self):
        result = _apply_compound_detection("hello world")
        assert result == "hello world"

    def test_mixed_vi_en(self):
        result = _apply_compound_detection("khách hàng service")
        assert "khách_hàng" in result
        assert "service" in result

    def test_case_insensitive(self):
        result = _apply_compound_detection("Quản Lý đơn hàng")
        assert "quản_lý" in result


# ── Tokenizer ────────────────────────────────────────────


class TestVietnameseTokenizer:
    """Test tokenizer strategies."""

    def test_syllable_strategy(self):
        tok = VietnameseTokenizer(strategy="syllable")
        tokens = tok.tokenize("quản lý đơn hàng")
        assert "quản" in tokens
        assert "hàng" in tokens

    def test_compound_strategy(self):
        tok = VietnameseTokenizer(strategy="compound")
        tokens = tok.tokenize("quản lý đơn hàng")
        assert "quản_lý" in tokens
        assert "đơn_hàng" in tokens

    def test_bigram_strategy(self):
        tok = VietnameseTokenizer(strategy="bigram")
        tokens = tok.tokenize("quản lý đơn hàng tốt")
        # Should include both compounds and bigrams
        assert "quản_lý" in tokens or any("quản" in t for t in tokens)

    def test_code_identifiers(self):
        tok = VietnameseTokenizer(strategy="compound")
        tokens = tok.tokenize("CustomerService.create_order()")
        assert "customer" in tokens
        assert "service" in tokens
        assert "create" in tokens
        assert "order" in tokens

    def test_mixed_vi_code(self):
        tok = VietnameseTokenizer(strategy="compound")
        tokens = tok.tokenize("# quản lý khách hàng — CustomerService")
        assert "quản_lý" in tokens
        assert "khách_hàng" in tokens
        assert "customer" in tokens
        assert "service" in tokens

    def test_stopword_removal(self):
        tok = VietnameseTokenizer(strategy="compound", remove_stopwords=True)
        tokens = tok.tokenize("đây là hệ thống quản lý")
        assert "là" not in tokens
        assert "quản_lý" in tokens

    def test_no_stopword_removal(self):
        tok = VietnameseTokenizer(strategy="compound", remove_stopwords=False)
        tokens = tok.tokenize("đây là quản lý")
        assert "là" in tokens

    def test_min_length_filter(self):
        tok = VietnameseTokenizer(strategy="syllable", min_token_length=3)
        tokens = tok.tokenize("a ab abc abcd")
        assert "a" not in tokens
        assert "ab" not in tokens
        assert "abc" in tokens

    def test_empty_text(self):
        tok = VietnameseTokenizer()
        assert tok.tokenize("") == []
        assert tok.tokenize("   ") == []
        assert tok.tokenize(None) == []  # type: ignore[arg-type]

    def test_english_only(self):
        tok = VietnameseTokenizer(strategy="compound")
        tokens = tok.tokenize("service layer pattern detection")
        assert "service" in tokens
        assert "layer" in tokens
        assert "pattern" in tokens

    def test_punctuation_handling(self):
        tok = VietnameseTokenizer(strategy="compound")
        tokens = tok.tokenize("quản_lý: [đơn hàng] (v2)")
        assert "đơn_hàng" in tokens


# ── BM25 Index ───────────────────────────────────────────


class TestBM25Index:
    """Test BM25 index creation and search."""

    def test_basic_search(self):
        idx = BM25Index()
        idx.add_document("d1", "customer service for order management")
        idx.add_document("d2", "database migration scripts")
        idx.add_document("d3", "user authentication and authorization")
        idx.build()

        results = idx.search("customer order")
        assert len(results) > 0
        assert results[0].doc_id == "d1"

    def test_vietnamese_search(self):
        idx = BM25Index()
        idx.add_document("d1", "quản lý đơn hàng khách hàng")
        idx.add_document("d2", "cơ sở dữ liệu migration")
        idx.add_document("d3", "xác thực và phân quyền người dùng")
        idx.build()

        results = idx.search("đơn hàng")
        assert len(results) > 0
        assert results[0].doc_id == "d1"

    def test_mixed_language_search(self):
        idx = BM25Index()
        idx.add_document(
            "d1",
            "CustomerService quản lý khách hàng API endpoint",
        )
        idx.add_document("d2", "OrderService xử lý đơn hàng pipeline")
        idx.add_document("d3", "AuthService xác thực bảo mật token")
        idx.build()

        results = idx.search("khách hàng customer")
        assert len(results) > 0
        assert results[0].doc_id == "d1"

    def test_top_k_limit(self):
        idx = BM25Index()
        for i in range(10):
            idx.add_document(f"d{i}", f"document {i} content")
        idx.build()

        results = idx.search("document content", top_k=3)
        assert len(results) <= 3

    def test_min_score_filter(self):
        idx = BM25Index()
        idx.add_document("d1", "exact match query terms")
        idx.add_document("d2", "completely unrelated content xyz")
        idx.build()

        results = idx.search("exact match query", min_score=0.5)
        # d1 should score higher than d2
        if results:
            assert results[0].doc_id == "d1"

    def test_empty_index(self):
        idx = BM25Index()
        idx.build()
        results = idx.search("anything")
        assert results == []

    def test_empty_query(self):
        idx = BM25Index()
        idx.add_document("d1", "some content")
        idx.build()
        results = idx.search("")
        assert results == []

    def test_document_count(self):
        idx = BM25Index()
        assert idx.document_count == 0
        idx.add_document("d1", "content")
        assert idx.document_count == 1
        idx.add_document("d2", "more content")
        assert idx.document_count == 2

    def test_is_indexed(self):
        idx = BM25Index()
        assert not idx.is_indexed
        idx.add_document("d1", "content")
        assert not idx.is_indexed
        idx.build()
        assert idx.is_indexed
        # Adding new doc invalidates
        idx.add_document("d2", "more")
        assert not idx.is_indexed

    def test_auto_build_on_search(self):
        # BM25 IDF needs ≥3 docs for meaningful discrimination
        idx = BM25Index()
        idx.add_document("d1", "hello world greeting welcome")
        idx.add_document("d2", "foo bar baz something else")
        idx.add_document("d3", "xyz abc def another thing")
        # Should auto-build on first search
        results = idx.search("hello world")
        assert len(results) > 0
        assert results[0].doc_id == "d1"

    def test_search_result_fields(self):
        idx = BM25Index()
        idx.add_document("d1", "test content data value", metadata={"extra": "data"})
        idx.add_document("d2", "unrelated stuff here now")
        idx.add_document("d3", "another random topic xyz")
        idx.build()
        results = idx.search("test content data")
        assert results[0].doc_id == "d1"
        assert results[0].score > 0
        assert results[0].document["extra"] == "data"

    def test_custom_k1_b(self):
        idx = BM25Index(k1=2.0, b=0.5)
        idx.add_document("d1", "custom parameters test config")
        idx.add_document("d2", "something entirely different here")
        idx.add_document("d3", "random unrelated words topic")
        idx.build()
        results = idx.search("custom parameters")
        assert len(results) > 0
        assert results[0].doc_id == "d1"


# ── Pure Python BM25 ────────────────────────────────────


class TestPureBM25:
    """Test fallback pure-Python BM25 implementation."""

    def test_basic_scoring(self):
        corpus = [
            ["hello", "world"],
            ["foo", "bar", "baz"],
            ["hello", "foo"],
        ]
        bm25 = _PureBM25(corpus)
        scores = bm25.get_scores(["hello"])
        assert scores[0] > 0  # "hello world" should score
        assert scores[1] == 0  # "foo bar baz" shouldn't
        assert scores[2] > 0  # "hello foo" should score

    def test_empty_corpus(self):
        bm25 = _PureBM25([])
        scores = bm25.get_scores(["anything"])
        assert scores == []

    def test_idf_weighting(self):
        corpus = [
            ["common", "rare"],
            ["common", "word"],
            ["common", "thing"],
        ]
        bm25 = _PureBM25(corpus)
        # "rare" appears in only 1 doc, should have higher IDF
        scores_rare = bm25.get_scores(["rare"])
        scores_common = bm25.get_scores(["common"])
        assert scores_rare[0] > scores_common[0]

    def test_term_frequency(self):
        corpus = [
            ["word", "word", "word"],  # High TF
            ["word"],  # Low TF
        ]
        bm25 = _PureBM25(corpus)
        scores = bm25.get_scores(["word"])
        assert scores[0] > scores[1]


# ── Vietnamese Recall Benchmark ──────────────────────────


# HC-AI | ticket: MEM-M1-12
# Realistic corpus: Vietnamese codebase documentation + comments
_BENCHMARK_DOCUMENTS = [
    (
        "order_service",
        "OrderService quản lý đơn hàng: tạo đơn, cập nhật trạng thái, "
        "xử lý thanh toán. CRUD operations cho order pipeline.",
    ),
    (
        "customer_service",
        "CustomerService quản lý khách hàng: đăng ký, cập nhật thông tin, "
        "phân nhóm khách hàng VIP. create_customer update_customer.",
    ),
    (
        "auth_service",
        "AuthService xác thực và phân quyền người dùng. JWT token, "
        "đăng nhập SSO, OAuth2. SecurityMiddleware bảo mật API.",
    ),
    (
        "product_catalog",
        "ProductCatalog quản lý sản phẩm: danh mục, giá, tồn kho. "
        "Tìm kiếm sản phẩm BM25. Product CRUD + category tree.",
    ),
    (
        "payment_gateway",
        "PaymentGateway thanh toán: VNPay, MoMo, ZaloPay integration. "
        "Xử lý giao dịch, hoàn tiền, đối soát. Transaction pipeline.",
    ),
    (
        "inventory_worker",
        "InventoryWorker quản lý tồn kho: đồng bộ stock, cảnh báo hết hàng. "
        "Celery task background job xử lý batch.",
    ),
    (
        "report_service",
        "ReportService báo cáo doanh thu, thống kê đơn hàng theo tháng. "
        "Excel export, PDF generation. Analytics dashboard.",
    ),
    (
        "notification_service",
        "NotificationService gửi thông báo: email, SMS, push notification. "
        "Template engine, queue worker, retry logic.",
    ),
    (
        "cart_service",
        "CartService giỏ hàng: thêm sản phẩm, cập nhật số lượng, "
        "áp dụng mã giảm giá. Redis session, coupon validation.",
    ),
    (
        "migration_config",
        "Database migration cấu hình: Alembic versions, schema upgrade. "
        "Cơ sở dữ liệu PostgreSQL + Redis cache layer.",
    ),
    (
        "layer_architecture",
        "Kiến trúc lớp dịch vụ: route → service → repository → model. "
        "Clean Architecture, dependency injection, SOLID principles.",
    ),
    (
        "test_suite",
        "Kiểm thử tự động: unit test, integration test, e2e test. "
        "pytest fixture, mock, coverage report. CI/CD pipeline.",
    ),
    (
        "user_profile",
        "Hồ sơ người dùng: thông tin cá nhân, địa chỉ giao hàng, "
        "lịch sử mua hàng. UserProfile model serializer.",
    ),
    (
        "search_engine",
        "Công cụ tìm kiếm: full-text search, filter, sort, pagination. "
        "Elasticsearch integration, Vietnamese tokenizer.",
    ),
    (
        "deployment_config",
        "Triển khai hệ thống: Docker, Kubernetes, CI/CD. "
        "Cấu hình môi trường staging, production. Health check.",
    ),
]

# HC-AI | ticket: MEM-M1-12
# Queries with expected relevant documents
_BENCHMARK_QUERIES = [
    # Vietnamese queries
    ("quản lý đơn hàng", ["order_service", "report_service"]),
    ("khách hàng VIP", ["customer_service"]),
    ("xác thực người dùng", ["auth_service"]),
    ("thanh toán VNPay", ["payment_gateway"]),
    ("sản phẩm tồn kho", ["product_catalog", "inventory_worker"]),
    ("giỏ hàng giảm giá", ["cart_service"]),
    ("báo cáo doanh thu", ["report_service"]),
    ("cơ sở dữ liệu migration", ["migration_config"]),
    ("kiến trúc lớp dịch vụ", ["layer_architecture"]),
    ("kiểm thử tự động", ["test_suite"]),
    ("người dùng hồ sơ", ["user_profile", "auth_service"]),
    ("tìm kiếm sản phẩm", ["search_engine", "product_catalog"]),
    ("triển khai Docker", ["deployment_config"]),
    ("gửi thông báo email", ["notification_service"]),
    ("cập nhật trạng thái đơn", ["order_service"]),
    # English queries (should also work)
    ("CustomerService CRUD", ["customer_service"]),
    ("JWT authentication", ["auth_service"]),
    ("Celery background task", ["inventory_worker"]),
    ("Redis cache session", ["cart_service", "migration_config"]),
    ("Elasticsearch full-text", ["search_engine"]),
    # Mixed queries
    ("OrderService xử lý pipeline", ["order_service", "payment_gateway"]),
    ("đăng nhập OAuth2 token", ["auth_service"]),
    ("quản lý sản phẩm catalog", ["product_catalog"]),
    ("cấu hình Kubernetes deploy", ["deployment_config"]),
]


class TestVietnameseRecallBenchmark:
    """Spike benchmark: BM25 recall on Vietnamese codebase content.

    Target: recall ≥ 75% on Vietnamese + mixed queries.
    """

    def test_compound_strategy_recall(self):
        """CRITICAL: Compound strategy must achieve ≥75% recall."""
        result = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            _BENCHMARK_QUERIES,
            strategy="compound",
            top_k=5,
        )
        assert result.recall >= 0.75, (
            f"Compound recall {result.recall:.1%} < 75% target. "
            f"Per-query: {result.per_query}"
        )

    def test_syllable_strategy_recall(self):
        """Baseline: syllable strategy recall (may be lower)."""
        result = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            _BENCHMARK_QUERIES,
            strategy="syllable",
            top_k=5,
        )
        # Just record, no hard failure
        assert result.recall > 0, "Syllable strategy should find something"

    def test_bigram_strategy_recall(self):
        """Bigram strategy recall."""
        result = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            _BENCHMARK_QUERIES,
            strategy="bigram",
            top_k=5,
        )
        assert result.recall >= 0.75, f"Bigram recall {result.recall:.1%} < 75% target"

    def test_compound_beats_syllable(self):
        """Compound strategy should outperform syllable on Vietnamese."""
        compound = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            _BENCHMARK_QUERIES,
            strategy="compound",
            top_k=5,
        )
        syllable = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            _BENCHMARK_QUERIES,
            strategy="syllable",
            top_k=5,
        )
        assert compound.recall >= syllable.recall, (
            f"Compound ({compound.recall:.1%}) should beat "
            f"syllable ({syllable.recall:.1%})"
        )

    def test_vietnamese_only_queries_recall(self):
        """Recall on Vietnamese-only queries (first 15)."""
        vi_queries = _BENCHMARK_QUERIES[:15]
        result = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            vi_queries,
            strategy="compound",
            top_k=5,
        )
        assert (
            result.recall >= 0.75
        ), f"Vietnamese-only recall {result.recall:.1%} < 75%"

    def test_english_only_queries_recall(self):
        """Recall on English-only queries."""
        en_queries = _BENCHMARK_QUERIES[15:20]
        result = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            en_queries,
            strategy="compound",
            top_k=5,
        )
        assert result.recall >= 0.70, f"English-only recall {result.recall:.1%} < 70%"

    def test_mixed_queries_recall(self):
        """Recall on mixed Vi+En queries."""
        mixed_queries = _BENCHMARK_QUERIES[20:]
        result = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            mixed_queries,
            strategy="compound",
            top_k=5,
        )
        assert result.recall >= 0.70, f"Mixed recall {result.recall:.1%} < 70%"

    def test_benchmark_result_summary(self):
        """BenchmarkResult produces valid summary string."""
        result = run_recall_benchmark(
            _BENCHMARK_DOCUMENTS,
            _BENCHMARK_QUERIES[:5],
            strategy="compound",
            top_k=5,
        )
        summary = result.summary()
        assert "Recall" in summary
        assert "Precision" in summary
        assert "compound" in summary


# ── Edge Cases ───────────────────────────────────────────


class TestEdgeCases:
    """Edge cases for Vietnamese BM25 search."""

    def test_single_document_corpus(self):
        """BM25 IDF is 0 when all docs contain the term → use PureBM25."""
        from knowledge_memory.core.search.bm25_search import _PureBM25

        # PureBM25 uses +1 in IDF formula, so single-doc works
        corpus = [["quản_lý", "đơn_hàng"]]
        bm25 = _PureBM25(corpus)
        scores = bm25.get_scores(["đơn_hàng"])
        assert scores[0] > 0

    def test_discriminative_search(self):
        """BM25 ranks relevant doc higher than irrelevant docs."""
        idx = BM25Index()
        idx.add_document("d1", "quản lý đơn hàng khách hàng")
        idx.add_document("d2", "unrelated content something else")
        idx.add_document("d3", "another different topic entirely")
        idx.build()
        results = idx.search("đơn hàng")
        assert len(results) > 0
        assert results[0].doc_id == "d1"

    def test_very_long_document(self):
        long_text = "quản lý đơn hàng " * 100
        idx = BM25Index()
        idx.add_document("d1", long_text)
        idx.add_document("d2", "short doc about something else")
        idx.add_document("d3", "another unrelated topic here")
        idx.build()
        results = idx.search("đơn hàng")
        assert len(results) > 0
        assert results[0].doc_id == "d1"

    def test_special_characters_in_query(self):
        idx = BM25Index()
        idx.add_document("d1", "test: [đơn hàng] {v2.0}")
        idx.add_document("d2", "something completely different here")
        idx.add_document("d3", "unrelated content about animals")
        idx.build()
        results = idx.search("[đơn hàng] v2.0")
        assert len(results) > 0

    def test_unicode_normalization(self):
        """Vietnamese text with different Unicode compositions."""
        idx = BM25Index()
        idx.add_document("d1", "quản lý dự án phần mềm")
        idx.add_document("d2", "something else entirely different")
        idx.add_document("d3", "random english content here today")
        idx.build()
        results = idx.search("quản lý")
        assert len(results) > 0

    def test_all_stopwords_query(self):
        idx = BM25Index()
        idx.add_document("d1", "content here")
        idx.build()
        results = idx.search("the a an is")
        assert results == []

    def test_pattern_search_convenience(self):
        """Test search_patterns convenience method."""
        from knowledge_memory.core.learners.pattern import Pattern

        patterns = [
            Pattern(
                name="naming::snake_case",
                category="naming",
                confidence=85.0,
                metadata={"description": "hàm sử dụng snake_case convention"},
            ),
            Pattern(
                name="layers::service_layer",
                category="layers",
                confidence=90.0,
                metadata={"description": "lớp dịch vụ xử lý business logic"},
            ),
            Pattern(
                name="ownership::bus_factor",
                category="ownership",
                confidence=75.0,
                metadata={"description": "rủi ro bus factor tập trung"},
            ),
        ]
        idx = BM25Index()
        results = idx.search_patterns("snake_case naming", patterns)
        assert len(results) > 0
        assert results[0].doc_id == "naming::snake_case"
