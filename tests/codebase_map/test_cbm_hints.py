# HC-AI | ticket: CBM-USER-HINTS
"""Tests for CBM User Hints — all commands have guidance."""

from __future__ import annotations

from codebase_map.hints import (
    HINTS,
    format_all_hints_summary,
    format_hint,
    get_hint,
    list_commands,
)


class TestCBMHintData:
    def test_all_11_commands_have_hints(self):
        expected = {
            "generate",
            "query",
            "impact",
            "summary",
            "search",
            "diff",
            "snapshot-diff",
            "snapshots",
            "api-catalog",
            "coverage",
            "check-staleness",
        }
        assert expected.issubset(set(HINTS.keys()))

    def test_every_hint_has_required_fields(self):
        for cmd, hint in HINTS.items():
            assert hint.command, f"{cmd}: missing command"
            assert hint.title, f"{cmd}: missing title"
            assert hint.what_it_does, f"{cmd}: missing what_it_does"
            assert hint.how_to_use, f"{cmd}: missing how_to_use"
            assert (
                len(hint.quality_levels) >= 2
            ), f"{cmd}: needs at least 2 quality levels"

    def test_quality_levels_valid(self):
        valid = {"perfect", "good", "normal", "bad"}
        for cmd, hint in HINTS.items():
            for q in hint.quality_levels:
                assert q.level in valid, f"{cmd}: invalid level '{q.level}'"


class TestCBMGetHint:
    def test_get_generate(self):
        hint = get_hint("generate")
        assert hint is not None
        assert "AST" in hint.what_it_does

    def test_get_snapshot_diff(self):
        hint = get_hint("snapshot-diff")
        assert hint is not None
        assert "v2.2" in hint.what_it_does

    def test_get_nonexistent(self):
        assert get_hint("xyz_fake") is None

    def test_list_commands(self):
        cmds = list_commands()
        assert len(cmds) >= 11
        assert "generate" in cmds
        assert "snapshot-diff" in cmds


class TestCBMFormatHint:
    def test_format_generate(self):
        output = format_hint(get_hint("generate"))
        assert "Function Dependency Graph" in output
        assert "WHAT IT DOES" in output
        assert "HOW TO USE" in output
        assert "RESULT QUALITY" in output
        assert "PERFECT" in output

    def test_format_snapshot_diff(self):
        output = format_hint(get_hint("snapshot-diff"))
        assert "Dual-Snapshot" in output
        assert "--breaking-only" in output
        assert "--test-plan" in output

    def test_format_diff(self):
        output = format_hint(get_hint("diff"))
        assert "Git Diff" in output

    def test_format_impact(self):
        output = format_hint(get_hint("impact"))
        assert "Impact Zone" in output
        assert "blast radius" in output

    def test_format_all_have_sections(self):
        for cmd, hint in HINTS.items():
            output = format_hint(hint)
            assert "WHAT IT DOES" in output, f"{cmd}: missing"
            assert "HOW TO USE" in output, f"{cmd}: missing"
            assert "RESULT QUALITY" in output, f"{cmd}: missing"


class TestCBMFormatSummary:
    def test_summary_lists_all(self):
        output = format_all_hints_summary()
        assert "Codebase Map" in output
        for cmd in ["generate", "query", "snapshot-diff", "coverage"]:
            assert cmd in output


class TestCBMHintContent:
    def test_generate_mentions_label(self):
        assert "--label" in get_hint("generate").how_to_use

    def test_snapshot_diff_mentions_formats(self):
        hint = get_hint("snapshot-diff")
        assert "markdown" in hint.how_to_use
        assert "json" in hint.how_to_use

    def test_diff_mentions_git_ref(self):
        assert "main" in get_hint("diff").how_to_use

    def test_coverage_mentions_pytest(self):
        assert "pytest" in get_hint("coverage").how_to_use

    def test_staleness_mentions_telegram(self):
        assert "Telegram" in get_hint("check-staleness").what_it_does
