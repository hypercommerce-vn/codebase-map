# HC-AI | ticket: MEM-M1-08
"""Tests for patterns.md generator."""

from pathlib import Path

import pytest

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.patterns_generator import generate_patterns_md
from knowledge_memory.verticals.codebase.vault import CodebaseVault

# --- Fixtures ---


@pytest.fixture()
def vault_with_patterns(tmp_path: Path) -> CodebaseVault:
    """Vault with committed patterns from all 3 learners."""
    vault = CodebaseVault()
    vault.init(tmp_path)

    patterns = [
        # Naming patterns
        Pattern(
            name="naming::functions_methods_snake_case",
            category="naming",
            confidence=95.0,
            evidence=[Evidence(source="a.py", data={"name": "x"})] * 5,
            metadata={
                "target": "functions_methods",
                "dominant_case": "snake_case",
                "compliance_pct": 95.0,
                "total": 100,
                "violation_count": 5,
                "violations": ["getUser", "processItem"],
                "case_distribution": {"snake_case": 95, "camelCase": 5},
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
                "total": 20,
                "violation_count": 0,
                "violations": [],
                "case_distribution": {"PascalCase": 20},
            },
        ),
        Pattern(
            name="naming::crud_prefix_pattern",
            category="naming",
            confidence=88.0,
            evidence=[],
            metadata={
                "prefix_distribution": {"get_": 15, "create_": 8, "update_": 5},
                "total_service_methods": 40,
                "crud_coverage_pct": 70.0,
            },
        ),
        # Layer patterns
        Pattern(
            name="layers::distribution",
            category="layers",
            confidence=90.0,
            evidence=[],
            metadata={
                "layer_pct": {
                    "service": 35.0,
                    "route": 25.0,
                    "model": 20.0,
                    "util": 15.0,
                    "unknown": 5.0,
                },
                "recognized_pct": 95.0,
                "total": 200,
                "layer_counts": {
                    "service": 70,
                    "route": 50,
                    "model": 40,
                    "util": 30,
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
                "mismatch_count": 2,
                "mismatched_samples": [
                    {"file_path": "bad.py", "detected": "service", "stored": "util"},
                ],
            },
        ),
        # Ownership patterns
        Pattern(
            name="ownership::single_owner_files",
            category="ownership",
            confidence=80.0,
            evidence=[],
            metadata={
                "total_files": 50,
                "single_owner_count": 15,
                "single_owner_pct": 30.0,
                "top_single_owner_files": [
                    {"file": "pipeline.py", "author": "alice", "pct": 95.0},
                ],
            },
        ),
        Pattern(
            name="ownership::domain_bus_factor",
            category="ownership",
            confidence=85.0,
            evidence=[],
            metadata={
                "risk_domain_count": 1,
                "total_domains": 4,
                "risk_domains": [
                    {
                        "domain": "pipeline",
                        "top_author": "alice",
                        "top_author_pct": 94.0,
                        "file_count": 5,
                    },
                ],
                "healthy_domains": [
                    {"domain": "crm", "bus_factor": 3, "total_authors": 5},
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
                    {"author": "alice", "commits": 200, "pct": 45.0},
                    {"author": "bob", "commits": 150, "pct": 33.0},
                ],
                "total_commits": 450,
                "total_authors": 5,
            },
        ),
    ]

    for p in patterns:
        p.vertical = "codebase"
        vault.commit_pattern(p)

    return vault


# --- Tests ---


class TestPatternsGeneratorBasic:
    """Basic generation tests."""

    def test_generates_markdown_string(
        self, vault_with_patterns: CodebaseVault
    ) -> None:
        """generate_patterns_md returns a string."""
        content = generate_patterns_md(vault_with_patterns)
        assert isinstance(content, str)
        assert len(content) > 0

    def test_header_present(self, vault_with_patterns: CodebaseVault) -> None:
        """Output has Codebase Patterns header."""
        content = generate_patterns_md(vault_with_patterns)
        assert "# Codebase Patterns" in content

    def test_metadata_present(self, vault_with_patterns: CodebaseVault) -> None:
        """Output has generation metadata."""
        content = generate_patterns_md(vault_with_patterns)
        assert "Generated:" in content
        assert "Vertical: codebase" in content
        assert "Patterns: 8" in content

    def test_footer_present(self, vault_with_patterns: CodebaseVault) -> None:
        """Output has footer with summary."""
        content = generate_patterns_md(vault_with_patterns)
        assert "Generated by Codebase Memory" in content


class TestPatternsGeneratorSections:
    """Section grouping tests."""

    def test_naming_section(self, vault_with_patterns: CodebaseVault) -> None:
        """Naming Conventions section present."""
        content = generate_patterns_md(vault_with_patterns)
        assert "## Naming Conventions" in content

    def test_layers_section(self, vault_with_patterns: CodebaseVault) -> None:
        """Layer Architecture section present."""
        content = generate_patterns_md(vault_with_patterns)
        assert "## Layer Architecture" in content

    def test_ownership_section(self, vault_with_patterns: CodebaseVault) -> None:
        """Code Ownership section present."""
        content = generate_patterns_md(vault_with_patterns)
        assert "## Code Ownership" in content

    def test_sections_in_order(self, vault_with_patterns: CodebaseVault) -> None:
        """Sections appear in defined order: naming, layers, ownership."""
        content = generate_patterns_md(vault_with_patterns)
        idx_naming = content.index("## Naming Conventions")
        idx_layers = content.index("## Layer Architecture")
        idx_ownership = content.index("## Code Ownership")
        assert idx_naming < idx_layers < idx_ownership


class TestPatternsGeneratorContent:
    """Content rendering tests."""

    def test_confidence_shown(self, vault_with_patterns: CodebaseVault) -> None:
        """Each pattern shows confidence percentage."""
        content = generate_patterns_md(vault_with_patterns)
        assert "Confidence:" in content
        assert "95%" in content

    def test_naming_violations_shown(self, vault_with_patterns: CodebaseVault) -> None:
        """Naming violations listed."""
        content = generate_patterns_md(vault_with_patterns)
        assert "violations" in content.lower()

    def test_layer_distribution_shown(self, vault_with_patterns: CodebaseVault) -> None:
        """Layer distribution bars rendered."""
        content = generate_patterns_md(vault_with_patterns)
        assert "service:" in content
        assert "route:" in content

    def test_bus_factor_risk_shown(self, vault_with_patterns: CodebaseVault) -> None:
        """Bus factor risk domains shown."""
        content = generate_patterns_md(vault_with_patterns)
        assert "pipeline" in content
        assert "alice" in content

    def test_crud_coverage_shown(self, vault_with_patterns: CodebaseVault) -> None:
        """CRUD prefix coverage shown."""
        content = generate_patterns_md(vault_with_patterns)
        assert "CRUD prefix coverage" in content

    def test_author_distribution_shown(
        self, vault_with_patterns: CodebaseVault
    ) -> None:
        """Author distribution shown."""
        content = generate_patterns_md(vault_with_patterns)
        assert "Top contributors" in content


class TestPatternsGeneratorThreshold:
    """Confidence threshold filtering tests."""

    def test_threshold_filters_patterns(
        self, vault_with_patterns: CodebaseVault
    ) -> None:
        """High threshold filters out low-confidence patterns."""
        content = generate_patterns_md(vault_with_patterns, confidence_threshold=90.0)
        # Only patterns ≥90% should appear
        assert "Patterns:" in content
        # 95% naming, 100% classes, 90% distribution, 90% author_dist = 4
        assert "Patterns: 4" in content

    def test_zero_threshold_includes_all(
        self, vault_with_patterns: CodebaseVault
    ) -> None:
        """Zero threshold includes all patterns."""
        content = generate_patterns_md(vault_with_patterns, confidence_threshold=0.0)
        assert "Patterns: 8" in content


class TestPatternsGeneratorFile:
    """File writing tests."""

    def test_writes_to_vault_dir(self, vault_with_patterns: CodebaseVault) -> None:
        """patterns.md written to vault verticals directory."""
        generate_patterns_md(vault_with_patterns)
        dest = vault_with_patterns.vault_dir / "verticals" / "codebase" / "patterns.md"
        assert dest.exists()
        content = dest.read_text()
        assert "# Codebase Patterns" in content

    def test_writes_to_custom_path(
        self, vault_with_patterns: CodebaseVault, tmp_path: Path
    ) -> None:
        """patterns.md written to custom output path."""
        out = tmp_path / "custom_patterns.md"
        generate_patterns_md(vault_with_patterns, output_path=str(out))
        assert out.exists()
        content = out.read_text()
        assert "# Codebase Patterns" in content

    def test_empty_vault_produces_valid_md(self, tmp_path: Path) -> None:
        """Empty vault produces valid Markdown with 0 patterns."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        content = generate_patterns_md(vault)
        assert "# Codebase Patterns" in content
        assert "Patterns: 0" in content
