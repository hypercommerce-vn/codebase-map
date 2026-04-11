# MEM-M1-12 — BM25 Vietnamese Language Validation Spike
# HC-AI | ticket: MEM-M1-12
> **Sprint:** CM-MEM-M1 · **Day:** 9 · **SP:** 2 · **Date:** 2026-04-22

---

## 1. Objective

Validate whether BM25 can effectively search Vietnamese + English mixed content in codebase patterns and evidence. Target: **recall ≥ 75%** on Vietnamese queries.

## 2. Background

KMP's Codebase Memory vertical stores patterns and evidence in Vietnamese (comments, docstrings, descriptions) + English (code identifiers, technical terms). M2 will need a search layer for AI agents to query the vault. The spike validates BM25 as a candidate before committing to implementation.

### Key Challenge: Vietnamese Tokenization

Vietnamese uses **spaces between syllables**, not words:
- "quản lý đơn hàng" = 4 syllables, but 2 concepts ("quản lý" = management, "đơn hàng" = order)
- Naive whitespace tokenization breaks compound words
- Mixed content: Vietnamese descriptions + English class names (e.g., `OrderService xử lý đơn hàng`)

## 3. Approach

### 3.1 VietnameseTokenizer — 3 Strategies

| Strategy | Description | Compound Detection |
|----------|-------------|-------------------|
| **syllable** | Whitespace + punctuation split (baseline) | No |
| **compound** | Dictionary-based Vietnamese compound joining | Yes — 42 tech terms |
| **bigram** | Compound + Vietnamese bigram expansion | Yes + bigrams |

All strategies split code identifiers (camelCase → tokens, snake_case → tokens).

### 3.2 Compound Dictionary

42 Vietnamese tech/codebase compound words:
- Business: quản_lý, đơn_hàng, khách_hàng, sản_phẩm, thanh_toán, giỏ_hàng
- Technical: cơ_sở_dữ_liệu, dữ_liệu, kiến_trúc, bảo_mật, xác_thực, phân_quyền
- Actions: cập_nhật, tìm_kiếm, triển_khai, kiểm_thử, xử_lý
- Architecture: lớp_dịch_vụ, lớp_mô_hình, lớp_điều_khiển

### 3.3 BM25 Implementation

- Primary: `rank_bm25.BM25Okapi` (pip package)
- Fallback: Pure-Python `_PureBM25` (no numpy dependency, +1 IDF smoothing)
- Parameters: k1=1.5, b=0.75 (Okapi defaults)

## 4. Benchmark Setup

### 4.1 Corpus (15 documents)

Realistic Vietnamese codebase documentation mixing Vietnamese descriptions + English code identifiers:
- `order_service`: "OrderService quản lý đơn hàng: tạo đơn, cập nhật trạng thái..."
- `customer_service`: "CustomerService quản lý khách hàng: đăng ký, cập nhật..."
- `auth_service`: "AuthService xác thực và phân quyền người dùng. JWT token..."
- ... (15 documents total, spanning services, config, architecture, testing)

### 4.2 Queries (24 total)

| Category | Count | Example |
|----------|:-----:|---------|
| Vietnamese-only | 15 | "quản lý đơn hàng", "kiến trúc lớp dịch vụ" |
| English-only | 5 | "CustomerService CRUD", "JWT authentication" |
| Mixed Vi+En | 4 | "OrderService xử lý pipeline", "đăng nhập OAuth2 token" |

Each query has 1-2 expected relevant documents (33 total relevant pairs).

## 5. Results

### 5.1 Overall Metrics

| Strategy | Recall | Precision | F1 |
|----------|:------:|:---------:|:--:|
| **syllable** (baseline) | **100.0%** | 44.1% | 61.2% |
| **compound** | **100.0%** | 54.5% | 70.6% |
| **bigram** | **100.0%** | 54.5% | 70.6% |

### 5.2 Recall by Query Type (compound strategy)

| Query Type | Recall | Precision | F1 |
|------------|:------:|:---------:|:--:|
| Vietnamese-only (15) | **100.0%** | 59.4% | 74.5% |
| English-only (5) | **100.0%** | 60.0% | 75.0% |
| Mixed Vi+En (4) | **100.0%** | 38.5% | 55.6% |

### 5.3 Per-Query Results (compound, all 24 queries)

All 24 queries achieved **100% recall** (all expected documents retrieved in top-5).

### 5.4 Key Finding: Compound > Syllable

Compound strategy improves **precision by +10.4pp** (54.5% vs 44.1%) over syllable baseline while maintaining same recall. This is because compound words reduce false positives:
- Query "đơn hàng" → compound tokenizes as `đơn_hàng` (1 token) → matches only documents about orders
- Syllable tokenizes as `đơn` + `hàng` → also matches documents containing "hàng" (goods) independently

## 6. Findings & Recommendations

### ✅ PASS: BM25 + Vietnamese compound tokenization exceeds target

- **Recall: 100%** (target was ≥75%) — all relevant documents found
- **Precision: 54.5%** — acceptable for a search layer (retrieval, not ranking)
- **F1: 70.6%** — strong baseline for M2 implementation

### Recommendation: Use `compound` strategy for M2

1. **compound** is recommended over syllable (+10pp precision) and bigram (same metrics, less complexity)
2. **42-word compound dictionary** is sufficient for tech/codebase context
3. **rank_bm25** library works well; pure-Python fallback available for minimal installs
4. For M2, consider adding:
   - SQLite FTS5 integration (built-in, no extra dependency)
   - Dynamic compound dictionary learning from vault patterns
   - Query expansion (synonym mapping for Vietnamese tech terms)

### Known Limitations

1. **Compound dictionary is static** — new terms require manual addition
2. **BM25 IDF edge case** — with very small corpus (1-2 docs), rank_bm25's IDF formula gives 0; PureBM25 fallback handles this with +1 smoothing
3. **No word segmentation** — relies on dictionary, not ML-based segmentation (e.g., underthesea, VnCoreNLP). For a codebase search context, dictionary approach is sufficient
4. **Precision on mixed queries is lower** (38.5%) — mixed Vi+En queries retrieve more false positives due to English terms being common across documents

## 7. Implementation Artifacts

| File | Description |
|------|-------------|
| `knowledge_memory/core/search/__init__.py` | Search module exports |
| `knowledge_memory/core/search/bm25_search.py` | BM25Index + VietnameseTokenizer + PureBM25 + benchmark |
| `tests/knowledge_memory/test_bm25_search.py` | 59 tests (tokenizer, BM25, recall benchmark, edge cases) |
| `docs/spikes/MEM-M1-12-bm25-vietnamese-spike.md` | This report |

### Test Coverage: 59 tests

| Test Class | Tests | Focus |
|------------|:-----:|-------|
| TestVietnameseDetection | 5 | Vietnamese character detection |
| TestCamelCaseSplit | 7 | Code identifier splitting |
| TestCompoundDetection | 5 | Vietnamese compound word joining |
| TestVietnameseTokenizer | 12 | 3 strategies, stopwords, mixed content |
| TestBM25Index | 11 | Search, ranking, metadata, edge cases |
| TestPureBM25 | 4 | Fallback BM25 implementation |
| TestVietnameseRecallBenchmark | 8 | **Recall benchmark ≥75% gate** |
| TestEdgeCases | 7 | Single doc, unicode, special chars |

## 8. Conclusion

**BM25 is validated for Vietnamese codebase search.** The compound tokenization strategy with a 42-word Vietnamese tech dictionary achieves 100% recall and 54.5% precision on a realistic benchmark. Ready for M2 integration with SQLite FTS5.

---

*Spike report · MEM-M1-12 · @TechLead · 2026-04-22*
