# HC-AI | ticket: MEM-M1-10
"""Tests for Quick Wins generator — 10 insights (5+3+2)."""

from pathlib import Path

import pytest

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.quick_wins import (
    Insight,
    QuickWinsResult,
    generate_quick_wins,
)
from knowledge_memory.verticals.codebase.vault import CodebaseVault

# --- Fixtures ---


@pytest.fixture()
def vault_full(tmp_path: Path) -> CodebaseVault:
    """Vault with patterns from all 3 learners (realistic mix)."""
    vault = CodebaseVault()
    vault.init(tmp_path)

    patterns = [
        # --- Layer patterns (structure insights) ---
        Pattern(
            name="layers::distribution",
            category="layers",
            confidence=94.0,
            evidence=[],
            metadata={
                "layer_pct": {
                    "service": 43.0,
                    "route": 22.0,
                    "model": 18.0,
                    "util": 12.0,
                    "unknown": 5.0,
                },
                "recognized_pct": 95.0,
                "total": 200,
                "layer_counts": {
                    "service": 86,
                    "route": 44,
                    "model": 36,
                    "util": 24,
                    "unknown": 10,
                },
            },
        ),
        Pattern(
            name="layers::compliance",
            category="layers",
            confidence=85.0,
            evidence=[],
            metadata={
                "compliance_pct": 85.0,
                "total": 100,
                "mismatch_count": 3,
                "mismatched_samples": [
                    {
                        "file_path": "utils/bad_service.py",
                        "detected": "service",
                        "stored": "util",
                    },
                ],
            },
        ),
        Pattern(
            name="layers::domain_grouping",
            category="layers",
            confidence=91.0,
            evidence=[],
            metadata={
                "total_domains": 5,
                "multi_layer_domains": 3,
                "domains": [
                    {
                        "domain": "crm",
                        "node_count": 45,
                        "layers": {"service": 20, "route": 15, "model": 10},
                    },
                    {
                        "domain": "billing",
                        "node_count": 30,
                        "layers": {"service": 15, "model": 15},
                    },
                    {
                        "domain": "auth",
                        "node_count": 20,
                        "layers": {"service": 10, "route": 10},
                    },
                    {
                        "domain": "pipeline",
                        "node_count": 15,
                        "layers": {"service": 15},
                    },
                    {
                        "domain": "shared",
                        "node_count": 10,
                        "layers": {"util": 10},
                    },
                ],
            },
        ),
        Pattern(
            name="layers::depth_analysis",
            category="layers",
            confidence=78.0,
            evidence=[],
            metadata={
                "depth_stats": {
                    "service": {
                        "avg_depth": 3.2,
                        "min_depth": 1,
                        "max_depth": 6,
                        "count": 15,
                    },
                    "route": {
                        "avg_depth": 1.5,
                        "min_depth": 1,
                        "max_depth": 2,
                        "count": 10,
                    },
                }
            },
        ),
        Pattern(
            name="layers::file_concentration",
            category="layers",
            confidence=75.0,
            evidence=[],
            metadata={
                "hotspot_dirs": {
                    "app/services/crm": 25,
                    "app/services/billing": 18,
                    "app/routes": 12,
                }
            },
        ),
        # --- Naming patterns (pattern insights) ---
        Pattern(
            name="naming::functions_methods_snake_case",
            category="naming",
            confidence=98.0,
            evidence=[Evidence(source="a.py", data={"name": "x"})] * 5,
            metadata={
                "target": "functions_methods",
                "dominant_case": "snake_case",
                "compliance_pct": 98.2,
                "total": 200,
                "violation_count": 4,
                "violations": [
                    "getCustomer",
                    "processOrder",
                    "fetchData",
                    "buildQuery",
                ],
                "case_distribution": {"snake_case": 196, "camelCase": 4},
            },
        ),
        Pattern(
            name="naming::classes_PascalCase",
            category="naming",
            confidence=100.0,
            evidence=[Evidence(source="a.py", data={"name": "X"})] * 3,
            metadata={
                "target": "classes",
                "dominant_case": "PascalCase",
                "compliance_pct": 100.0,
                "total": 30,
                "violation_count": 0,
                "violations": [],
                "case_distribution": {"PascalCase": 30},
            },
        ),
        Pattern(
            name="naming::crud_prefix_pattern",
            category="naming",
            confidence=85.0,
            evidence=[],
            metadata={
                "prefix_distribution": {
                    "get_": 25,
                    "create_": 12,
                    "update_": 8,
                    "delete_": 5,
                },
                "total_service_methods": 65,
                "crud_coverage_pct": 77.0,
            },
        ),
        # --- Ownership patterns (risk insights) ---
        Pattern(
            name="ownership::domain_bus_factor",
            category="ownership",
            confidence=88.0,
            evidence=[],
            metadata={
                "risk_domain_count": 1,
                "total_domains": 5,
                "risk_domains": [
                    {
                        "domain": "pipeline",
                        "top_author": "alice",
                        "top_author_pct": 94.0,
                        "file_count": 8,
                    },
                ],
                "healthy_domains": [
                    {"domain": "crm", "bus_factor": 3, "total_authors": 5},
                ],
            },
        ),
        Pattern(
            name="ownership::single_owner_files",
            category="ownership",
            confidence=82.0,
            evidence=[],
            metadata={
                "total_files": 60,
                "single_owner_count": 12,
                "single_owner_pct": 20.0,
                "top_single_owner_files": [
                    {"file": "pipeline/core.py", "author": "alice", "pct": 95.0},
                    {"file": "pipeline/runner.py", "author": "alice", "pct": 90.0},
                ],
            },
        ),
        Pattern(
            name="ownership::author_distribution",
            category="ownership",
            confidence=90.0,
            evidence=[],
            metadata={
                "top_authors": [
                    {"author": "alice", "commits": 200, "pct": 40.0},
                    {"author": "bob", "commits": 150, "pct": 30.0},
                ],
                "total_commits": 500,
                "total_authors": 6,
            },
        ),
    ]

    for p in patterns:
        p.vertical = "codebase"
        vault.commit_pattern(p)

    return vault


@pytest.fixture()
def vault_minimal(tmp_path: Path) -> CodebaseVault:
    """Vault with minimal patterns (only naming)."""
    vault = CodebaseVault()
    vault.init(tmp_path)

    patterns = [
        Pattern(
            name="naming::functions_methods_snake_case",
            category="naming",
            confidence=95.0,
            evidence=[Evidence(source="a.py", data={"name": "x"})] * 3,
            metadata={
                "target": "functions_methods",
                "dominant_case": "snake_case",
                "compliance_pct": 95.0,
                "total": 50,
                "violation_count": 3,
                "violations": ["getUser"],
                "case_distribution": {"snake_case": 47, "camelCase": 3},
            },
        ),
    ]

    for p in patterns:
        p.vertical = "codebase"
        vault.commit_pattern(p)

    return vault


@pytest.fixture()
def vault_empty(tmp_path: Path) -> CodebaseVault:
    """Empty vault with no patterns."""
    vault = CodebaseVault()
    vault.init(tmp_path)
    return vault


# --- Insight class tests ---


class TestInsight:
    """Tests for Insight data class."""

    def test_basic_creation(self) -> None:
        i = Insight(
            number=1,
            title="Test",
            description="Desc",
            evidence="file.py",
            confidence=90.0,
            action="Do something",
            category="structure",
        )
        assert i.number == 1
        assert i.title == "Test"
        assert i.confidence == 90.0
        assert i.category == "structure"
        assert not i.needs_review

    def test_needs_review_low_confidence(self) -> None:
        i = Insight(
            number=1,
            title="Low",
            description="Desc",
            evidence="f.py",
            confidence=55.0,
            action="Fix",
            category="risks",
        )
        assert i.needs_review is True

    def test_confidence_label_green(self) -> None:
        i = Insight(
            number=1,
            title="",
            description="",
            evidence="",
            confidence=90.0,
            action="",
            category="structure",
        )
        assert i.confidence_label == "green"

    def test_confidence_label_yellow(self) -> None:
        i = Insight(
            number=1,
            title="",
            description="",
            evidence="",
            confidence=70.0,
            action="",
            category="structure",
        )
        assert i.confidence_label == "yellow"

    def test_confidence_label_red(self) -> None:
        i = Insight(
            number=1,
            title="",
            description="",
            evidence="",
            confidence=50.0,
            action="",
            category="risks",
        )
        assert i.confidence_label == "red"


class TestQuickWinsResult:
    """Tests for QuickWinsResult."""

    def test_empty_result(self) -> None:
        r = QuickWinsResult()
        assert r.insight_count == 0
        assert r.structure_insights == []
        assert r.pattern_insights == []
        assert r.risk_insights == []

    def test_categorized_access(self) -> None:
        r = QuickWinsResult()
        r.insights = [
            Insight(1, "A", "", "", 90, "", "structure"),
            Insight(2, "B", "", "", 80, "", "patterns"),
            Insight(3, "C", "", "", 70, "", "risks"),
        ]
        assert len(r.structure_insights) == 1
        assert len(r.pattern_insights) == 1
        assert len(r.risk_insights) == 1


# --- Generator tests ---


class TestQuickWinsBasic:
    """Basic generation tests."""

    def test_returns_result(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        assert isinstance(result, QuickWinsResult)

    def test_total_patterns_tracked(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        assert result.total_patterns >= 8

    def test_output_path_set(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        assert result.output_path is not None
        assert "quick-wins.md" in result.output_path


class TestQuickWinsRatio:
    """Tests for the 5+3+2 fixed ratio."""

    def test_structure_max_5(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        assert len(result.structure_insights) <= 5

    def test_patterns_max_3(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        assert len(result.pattern_insights) <= 3

    def test_risks_max_2(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        assert len(result.risk_insights) <= 2

    def test_total_max_10(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        assert result.insight_count <= 10

    def test_full_vault_produces_insights(self, vault_full: CodebaseVault) -> None:
        """Full vault should produce insights in all 3 categories."""
        result = generate_quick_wins(vault_full)
        assert len(result.structure_insights) >= 1
        assert len(result.pattern_insights) >= 1
        assert len(result.risk_insights) >= 1


class TestQuickWinsNumbering:
    """Tests for sequential numbering."""

    def test_sequential_numbers(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        numbers = [i.number for i in result.insights]
        expected = list(range(1, len(numbers) + 1))
        assert numbers == expected

    def test_structure_first(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        if result.insights:
            assert result.insights[0].category == "structure"


class TestQuickWinsStructure:
    """Tests for structure insights extraction."""

    def test_dominant_layer_detected(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        titles = [i.title for i in result.structure_insights]
        assert any("Service" in t and "dominant" in t for t in titles)

    def test_domains_detected(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        titles = [i.title for i in result.structure_insights]
        assert any("domain" in t.lower() for t in titles)

    def test_compliance_insight(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        titles = [i.title for i in result.structure_insights]
        assert any("compliance" in t.lower() for t in titles)

    def test_structure_has_evidence(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        for i in result.structure_insights:
            assert i.evidence != ""


class TestQuickWinsPatterns:
    """Tests for pattern insights extraction."""

    def test_naming_convention_detected(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        titles = [i.title for i in result.pattern_insights]
        assert any("naming" in t.lower() or "snake_case" in t for t in titles)

    def test_crud_prefix_detected(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        titles = [i.title for i in result.pattern_insights]
        assert any("crud" in t.lower() or "prefix" in t.lower() for t in titles)

    def test_patterns_sorted_by_confidence(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        pats = result.pattern_insights
        if len(pats) >= 2:
            for a, b in zip(pats, pats[1:]):
                assert a.confidence >= b.confidence


class TestQuickWinsRisks:
    """Tests for risk insights extraction."""

    def test_bus_factor_risk_detected(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        titles = [i.title for i in result.risk_insights]
        assert any("bus factor" in t.lower() or "pipeline" in t.lower() for t in titles)

    def test_single_owner_detected(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        titles = [i.title for i in result.risk_insights]
        assert any("single owner" in t.lower() for t in titles)

    def test_risks_have_action(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        for i in result.risk_insights:
            assert i.action != ""


class TestQuickWinsConfidence:
    """Tests for confidence threshold filtering."""

    def test_high_threshold_reduces_insights(self, vault_full: CodebaseVault) -> None:
        result_low = generate_quick_wins(vault_full, confidence_threshold=60.0)
        result_high = generate_quick_wins(vault_full, confidence_threshold=90.0)
        assert result_high.insight_count <= result_low.insight_count

    def test_zero_threshold_includes_all(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full, confidence_threshold=0.0)
        assert result.total_patterns >= 8


class TestQuickWinsEdgeCases:
    """Edge case tests."""

    def test_empty_vault(self, vault_empty: CodebaseVault) -> None:
        result = generate_quick_wins(vault_empty)
        assert result.insight_count == 0
        assert result.total_patterns == 0

    def test_minimal_vault(self, vault_minimal: CodebaseVault) -> None:
        """Vault with only naming patterns produces pattern insights."""
        result = generate_quick_wins(vault_minimal)
        assert result.insight_count >= 1
        assert len(result.pattern_insights) >= 1
        # No structure or risk insights
        assert len(result.structure_insights) == 0
        assert len(result.risk_insights) == 0

    def test_deterministic(self, vault_full: CodebaseVault) -> None:
        """Same vault produces same insights."""
        r1 = generate_quick_wins(vault_full)
        r2 = generate_quick_wins(vault_full)
        titles1 = [i.title for i in r1.insights]
        titles2 = [i.title for i in r2.insights]
        assert titles1 == titles2


class TestQuickWinsFile:
    """File output tests."""

    def test_writes_to_vault_dir(self, vault_full: CodebaseVault) -> None:
        generate_quick_wins(vault_full)
        dest = vault_full.vault_dir / "verticals" / "codebase" / "quick-wins.md"
        assert dest.exists()
        content = dest.read_text()
        assert "# Quick Wins" in content

    def test_writes_to_custom_path(
        self, vault_full: CodebaseVault, tmp_path: Path
    ) -> None:
        out = tmp_path / "my-wins.md"
        generate_quick_wins(vault_full, output_path=str(out))
        assert out.exists()
        content = out.read_text()
        assert "# Quick Wins" in content

    def test_empty_vault_valid_md(self, vault_empty: CodebaseVault) -> None:
        generate_quick_wins(vault_empty)
        dest = vault_empty.vault_dir / "verticals" / "codebase" / "quick-wins.md"
        assert dest.exists()
        content = dest.read_text()
        assert "# Quick Wins" in content
        assert "0 actionable insights" in content


class TestQuickWinsMarkdown:
    """Markdown content tests."""

    def test_header(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        assert "# Quick Wins" in content

    def test_structure_section(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        assert "## Structure" in content

    def test_patterns_section(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        assert "## Patterns" in content

    def test_risks_section(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        assert "## Risks" in content

    def test_footer(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        assert "Generated by Codebase Memory" in content

    def test_evidence_in_markdown(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        assert "**Evidence:**" in content

    def test_action_in_markdown(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        assert "**Action:**" in content

    def test_confidence_in_titles(self, vault_full: CodebaseVault) -> None:
        result = generate_quick_wins(vault_full)
        content = Path(result.output_path).read_text()
        # Each insight title has confidence %
        assert "%" in content
