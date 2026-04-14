# HC-AI | ticket: MEM-M3-03 / MEM-M3-07
"""Tests for Mermaid diagrams + Glossary extractor."""

from __future__ import annotations

from knowledge_memory.verticals.codebase.glossary import GlossaryExtractor, GlossaryTerm
from knowledge_memory.verticals.codebase.mermaid import (
    generate_architecture_diagram,
    generate_call_flow,
    generate_domain_map,
    wrap_mermaid_block,
)

# ── Test data ──────────────────────────────────


def _sample_nodes():
    return [
        {
            "name": "create_customer",
            "file_path": "crm/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "get_customer",
            "file_path": "crm/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "update_customer",
            "file_path": "crm/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "CustomerModel",
            "file_path": "crm/models.py",
            "node_type": "class",
            "layer": "model",
        },
        {
            "name": "submit_order",
            "file_path": "order/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "get_order",
            "file_path": "order/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "OrderItem",
            "file_path": "order/models.py",
            "node_type": "class",
            "layer": "model",
        },
        {
            "name": "create_invoice",
            "file_path": "billing/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "InvoiceError",
            "file_path": "billing/errors.py",
            "node_type": "class",
            "layer": "model",
        },
        {
            "name": "authenticate",
            "file_path": "auth/service.py",
            "node_type": "function",
            "layer": "service",
        },
        {
            "name": "login",
            "file_path": "auth/router.py",
            "node_type": "function",
            "layer": "route",
        },
        {
            "name": "pipeline_runner",
            "file_path": "pipeline/runner.py",
            "node_type": "function",
            "layer": "util",
        },
    ]


def _sample_edges():
    return [
        {"source_name": "login", "target_name": "authenticate"},
        {"source_name": "submit_order", "target_name": "create_invoice"},
        {"source_name": "create_customer", "target_name": "CustomerModel"},
        {"source_name": "get_order", "target_name": "OrderItem"},
    ]


# ══════════════════════════════════════════════════
# Mermaid tests
# ══════════════════════════════════════════════════


class TestMermaidArchitecture:
    def test_basic_diagram(self):
        layers = {"service": 85, "route": 20, "model": 15, "util": 30}
        result = generate_architecture_diagram(layers)
        assert "graph TD" in result
        assert "service" in result
        assert "85 nodes" in result

    def test_with_domains(self):
        layers = {"service": 50}
        domains = ["crm", "order", "billing", "auth"]
        result = generate_architecture_diagram(layers, domains)
        assert "subgraph Domains" in result
        assert "crm" in result

    def test_empty_layers(self):
        result = generate_architecture_diagram({})
        assert "graph TD" in result


class TestMermaidDomainMap:
    def test_cross_domain_edges(self):
        result = generate_domain_map(_sample_edges(), _sample_nodes())
        assert "graph LR" in result
        # order → billing is cross-domain
        assert "order" in result
        assert "billing" in result

    def test_no_cross_domain(self):
        # All edges within same domain
        edges = [
            {"source_name": "create_customer", "target_name": "get_customer"},
        ]
        nodes = [
            {"name": "create_customer", "file_path": "crm/a.py"},
            {"name": "get_customer", "file_path": "crm/b.py"},
        ]
        result = generate_domain_map(edges, nodes)
        assert "No cross-domain" in result

    def test_empty_edges(self):
        result = generate_domain_map([])
        assert "No cross-domain" in result


class TestMermaidCallFlow:
    def test_basic_flow(self):
        result = generate_call_flow(
            "authenticate",
            callers=["login", "api_login"],
            callees=["hash_password", "find_user"],
        )
        assert "graph LR" in result
        assert "authenticate" in result
        assert "login" in result
        assert "hash_password" in result

    def test_empty_callers(self):
        result = generate_call_flow("orphan_func", [], [])
        assert "orphan_func" in result


class TestMermaidWrap:
    def test_wrap_block(self):
        result = wrap_mermaid_block("graph TD\n    A --> B")
        assert result.startswith("```mermaid")
        assert result.endswith("```")


# ══════════════════════════════════════════════════
# Glossary tests
# ══════════════════════════════════════════════════


class TestGlossaryExtractor:
    def test_extract_terms(self):
        extractor = GlossaryExtractor(min_evidence=2)
        terms = extractor.extract(_sample_nodes())
        assert len(terms) > 0
        # "customer" appears 4 times (create_customer, get_customer,
        # update_customer, CustomerModel)
        term_names = {t.term.lower() for t in terms}
        assert "customer" in term_names

    def test_terms_sorted_by_evidence(self):
        extractor = GlossaryExtractor(min_evidence=2)
        terms = extractor.extract(_sample_nodes())
        # Should be sorted by evidence count descending
        for i in range(len(terms) - 1):
            assert terms[i].evidence_count >= terms[i + 1].evidence_count

    def test_min_evidence_filter(self):
        extractor = GlossaryExtractor(min_evidence=10)
        terms = extractor.extract(_sample_nodes())
        # Very high threshold should filter most terms
        for t in terms:
            assert t.evidence_count >= 10

    def test_code_stopwords_filtered(self):
        extractor = GlossaryExtractor(min_evidence=1)
        terms = extractor.extract(_sample_nodes())
        term_names = {t.term.lower() for t in terms}
        # Common code words should be filtered
        assert "get" not in term_names
        assert "create" not in term_names
        assert "service" not in term_names

    def test_domain_assignment(self):
        extractor = GlossaryExtractor(min_evidence=2)
        terms = extractor.extract(_sample_nodes())
        customer_term = next((t for t in terms if t.term.lower() == "customer"), None)
        if customer_term:
            assert customer_term.domain == "crm"

    def test_confidence_scales_with_evidence(self):
        extractor = GlossaryExtractor(min_evidence=1)
        terms = extractor.extract(_sample_nodes())
        if len(terms) >= 2:
            high = max(terms, key=lambda t: t.evidence_count)
            low = min(terms, key=lambda t: t.evidence_count)
            assert high.confidence >= low.confidence

    def test_format_table(self):
        extractor = GlossaryExtractor(min_evidence=2)
        terms = extractor.extract(_sample_nodes())
        table = extractor.format_table(terms)
        assert "| Term |" in table
        assert "Domain" in table

    def test_format_table_empty(self):
        extractor = GlossaryExtractor()
        table = extractor.format_table([])
        assert "No business terms" in table

    def test_format_terminal(self):
        extractor = GlossaryExtractor(min_evidence=2)
        terms = extractor.extract(_sample_nodes())
        output = extractor.format_terminal(terms)
        assert "Knowledge Memory" in output
        assert "Glossary" in output
        assert "Total:" in output

    def test_format_terminal_empty(self):
        extractor = GlossaryExtractor()
        output = extractor.format_terminal([])
        assert "No business terms" in output

    def test_empty_nodes(self):
        extractor = GlossaryExtractor()
        terms = extractor.extract([])
        assert len(terms) == 0

    def test_glossary_term_dataclass(self):
        term = GlossaryTerm(
            term="Customer",
            domain="crm",
            evidence_count=23,
            sources=["crm/service.py"],
            confidence=92.0,
        )
        assert term.term == "Customer"
        assert term.confidence == 92.0
