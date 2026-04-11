# HC-AI | ticket: MEM-M1-11
"""Tests for CLI summary output with rich colors."""

import os
from unittest.mock import patch

import pytest

from knowledge_memory.verticals.codebase.cli_output import (
    format_bootstrap_complete,
    format_bootstrap_header,
    format_output_files,
    format_quick_wins_inline,
    format_step_progress,
    format_step_result,
    format_vault_info,
    format_vault_summary,
)
from knowledge_memory.verticals.codebase.quick_wins import Insight, QuickWinsResult

# --- Fixtures ---


@pytest.fixture()
def quick_wins_result() -> QuickWinsResult:
    """Sample QuickWinsResult with insights in all 3 categories."""
    result = QuickWinsResult()
    result.total_patterns = 20
    result.output_path = ".knowledge-memory/verticals/codebase/quick-wins.md"
    result.insights = [
        Insight(
            number=1,
            title="Service Layer dominant",
            description="43% of nodes are service-layer (86 of 200 total)",
            evidence="service/ directory",
            confidence=94.0,
            action="No action needed",
            category="structure",
        ),
        Insight(
            number=2,
            title="5 domains detected",
            description="crm, billing, auth, pipeline, shared",
            evidence="crm/",
            confidence=91.0,
            action="Good domain boundaries",
            category="structure",
        ),
        Insight(
            number=3,
            title="Layer compliance: 85%",
            description="3 files with mismatched layer",
            evidence="utils/bad_service.py",
            confidence=85.0,
            action="Review mismatched files",
            category="structure",
        ),
        Insight(
            number=4,
            title="Deep nesting in service layer",
            description="Avg depth 3.2, range 1-6 (15 files)",
            evidence="service/ files",
            confidence=78.0,
            action="Review deeply nested modules",
            category="structure",
        ),
        Insight(
            number=5,
            title="Hotspot directory: app/services/crm",
            description="25 nodes concentrated",
            evidence="app/services/crm",
            confidence=75.0,
            action="Consider splitting if >50 nodes",
            category="structure",
        ),
        Insight(
            number=6,
            title="Naming convention: snake_case",
            description="98.2% compliance — 4 violations",
            evidence="codebase-wide",
            confidence=98.0,
            action="No action needed",
            category="patterns",
        ),
        Insight(
            number=7,
            title="PascalCase classes",
            description="100% compliance",
            evidence="codebase-wide",
            confidence=100.0,
            action="No action needed",
            category="patterns",
        ),
        Insight(
            number=8,
            title="CRUD prefix pattern",
            description="77% of service methods follow CRUD naming",
            evidence="Prefixes: get_ (25), create_ (12)",
            confidence=85.0,
            action="Good naming consistency",
            category="patterns",
        ),
        Insight(
            number=9,
            title="Bus factor risk: pipeline",
            description="alice owns 94% of 8 files — bus factor = 1",
            evidence="pipeline/ directory",
            confidence=88.0,
            action="Pair program on this domain",
            category="risks",
        ),
        Insight(
            number=10,
            title="Single owner risk: 12 files",
            description="20% of files have single dominant author",
            evidence="pipeline/core.py",
            confidence=82.0,
            action="Increase code review coverage",
            category="risks",
        ),
    ]
    return result


# --- Bootstrap header tests ---


class TestBootstrapHeader:
    """Tests for bootstrap header formatting."""

    def test_plain_text(self) -> None:
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            from knowledge_memory.verticals.codebase import cli_output

            cli_output._NO_COLOR = True
            try:
                output = format_bootstrap_header()
                assert "Knowledge Memory Platform" in output
                assert "v1.0.0" in output
            finally:
                cli_output._NO_COLOR = bool(os.environ.get("NO_COLOR", ""))

    def test_returns_string(self) -> None:
        output = format_bootstrap_header()
        assert isinstance(output, str)
        assert len(output) > 0


class TestVaultInfo:
    """Tests for vault info subtitle."""

    def test_contains_vault_path(self) -> None:
        output = format_vault_info(vault_path="/my/vault/")
        assert "/my/vault/" in output

    def test_contains_vertical(self) -> None:
        output = format_vault_info(vertical="codebase")
        assert "codebase" in output

    def test_contains_schema_version(self) -> None:
        output = format_vault_info(schema_version=2)
        assert "v2" in output


class TestStepProgress:
    """Tests for step progress formatting."""

    def test_step_format(self) -> None:
        output = format_step_progress(1, 5, "Parse", "Scanning...")
        assert "[1/5]" in output
        assert "Parse" in output
        assert "Scanning..." in output

    def test_no_detail(self) -> None:
        output = format_step_progress(3, 5, "Learn")
        assert "[3/5]" in output
        assert "Learn" in output


class TestStepResult:
    """Tests for step result formatting."""

    def test_with_elapsed(self) -> None:
        output = format_step_result("25 patterns", elapsed=0.2)
        assert "✓" in output
        assert "25 patterns" in output
        assert "0.2s" in output

    def test_with_detail(self) -> None:
        output = format_step_result("Snapshot saved", "(rotation: 1/5)")
        assert "Snapshot saved" in output
        assert "1/5" in output

    def test_simple_message(self) -> None:
        output = format_step_result("Done")
        assert "✓" in output
        assert "Done" in output


class TestBootstrapComplete:
    """Tests for bootstrap completion banner."""

    def test_contains_all_info(self) -> None:
        output = format_bootstrap_complete(
            elapsed=5.7,
            pattern_count=25,
            quick_win_count=10,
        )
        assert "Bootstrap complete" in output
        assert "5.7s" in output
        assert "25 patterns" in output
        assert "10 quick wins" in output

    def test_plain_text_no_color(self) -> None:
        from knowledge_memory.verticals.codebase import cli_output

        old = cli_output._NO_COLOR
        cli_output._NO_COLOR = True
        try:
            output = format_bootstrap_complete(1.0, 5, 3)
            assert "Bootstrap complete" in output
            # Should not contain ANSI escape codes
            assert "\033[" not in output
        finally:
            cli_output._NO_COLOR = old


class TestOutputFiles:
    """Tests for output files list."""

    def test_lists_paths(self) -> None:
        output = format_output_files(
            [
                ".knowledge-memory/verticals/codebase/patterns.md",
                ".knowledge-memory/verticals/codebase/quick-wins.md",
            ]
        )
        assert "Output files:" in output
        assert "patterns.md" in output
        assert "quick-wins.md" in output

    def test_empty_list(self) -> None:
        output = format_output_files([])
        assert "Output files:" in output


# --- Quick Wins inline tests ---


class TestQuickWinsInline:
    """Tests for inline Quick Wins display."""

    def test_contains_header(self, quick_wins_result: QuickWinsResult) -> None:
        output = format_quick_wins_inline(quick_wins_result)
        assert "Quick Wins" in output

    def test_contains_structure(self, quick_wins_result: QuickWinsResult) -> None:
        output = format_quick_wins_inline(quick_wins_result)
        assert "STRUCTURE" in output

    def test_contains_patterns(self, quick_wins_result: QuickWinsResult) -> None:
        output = format_quick_wins_inline(quick_wins_result)
        assert "PATTERNS" in output

    def test_contains_risks(self, quick_wins_result: QuickWinsResult) -> None:
        output = format_quick_wins_inline(quick_wins_result)
        assert "RISKS" in output

    def test_contains_confidence(self, quick_wins_result: QuickWinsResult) -> None:
        output = format_quick_wins_inline(quick_wins_result)
        assert "%" in output

    def test_max_lines_respected(self, quick_wins_result: QuickWinsResult) -> None:
        output = format_quick_wins_inline(quick_wins_result, max_lines=10)
        lines = output.strip().split("\n")
        assert len(lines) <= 10

    def test_empty_result(self) -> None:
        result = QuickWinsResult()
        output = format_quick_wins_inline(result)
        assert "Quick Wins" in output

    def test_output_path_shown(self, quick_wins_result: QuickWinsResult) -> None:
        output = format_quick_wins_inline(quick_wins_result)
        assert "quick-wins.md" in output

    def test_plain_text_mode(self, quick_wins_result: QuickWinsResult) -> None:
        from knowledge_memory.verticals.codebase import cli_output

        old = cli_output._NO_COLOR
        cli_output._NO_COLOR = True
        try:
            output = format_quick_wins_inline(quick_wins_result)
            assert "Quick Wins" in output
            assert "STRUCTURE" in output
            assert "\033[" not in output
        finally:
            cli_output._NO_COLOR = old


# --- Vault summary tests ---


class TestVaultSummary:
    """Tests for vault summary output."""

    def test_contains_header(self) -> None:
        output = format_vault_summary()
        assert "Knowledge Memory" in output
        assert "Vault Summary" in output

    def test_contains_vault_path(self) -> None:
        output = format_vault_summary(vault_path="/custom/")
        assert "/custom/" in output

    def test_pattern_count(self) -> None:
        output = format_vault_summary(
            pattern_count=25,
            pattern_breakdown="12 naming + 8 layer + 5 ownership",
        )
        assert "25" in output
        assert "12 naming" in output

    def test_snapshot_info(self) -> None:
        output = format_vault_summary(snapshot_count=3, snapshot_limit=5)
        assert "3/5" in output

    def test_quick_wins_info(self) -> None:
        output = format_vault_summary(
            quick_win_count=10,
            quick_win_breakdown="5 structure + 3 patterns + 2 risks",
        )
        assert "10" in output
        assert "5 structure" in output

    def test_corpus_info(self) -> None:
        output = format_vault_summary(
            node_count=1386,
            edge_count=8285,
            file_count=120,
        )
        assert "1,386" in output
        assert "8,285" in output
        assert "120 files" in output

    def test_bootstrap_hint(self) -> None:
        output = format_vault_summary()
        assert "codebase-memory bootstrap" in output

    def test_plain_text_no_color(self) -> None:
        from knowledge_memory.verticals.codebase import cli_output

        old = cli_output._NO_COLOR
        cli_output._NO_COLOR = True
        try:
            output = format_vault_summary(
                pattern_count=10, node_count=500, edge_count=200, file_count=50
            )
            assert "Knowledge Memory" in output
            assert "\033[" not in output
        finally:
            cli_output._NO_COLOR = old

    def test_last_bootstrap_shown(self) -> None:
        output = format_vault_summary(last_bootstrap="2026-04-18 14:30 UTC")
        assert "2026-04-18" in output

    def test_duration_shown(self) -> None:
        output = format_vault_summary(duration=5.7)
        assert "5.7s" in output

    def test_minimal_summary(self) -> None:
        """Minimal summary with no data still produces valid output."""
        output = format_vault_summary()
        assert "Vault:" in output
        assert "Schema:" in output
        assert "Patterns:" in output
