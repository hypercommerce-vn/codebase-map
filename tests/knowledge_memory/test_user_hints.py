# HC-AI | ticket: KMP-USER-HINTS
"""Tests for User Hints system — all commands have guidance."""

from __future__ import annotations

from knowledge_memory.core.hints import (
    HINTS,
    format_all_hints_summary,
    format_hint,
    get_hint,
    list_commands,
)


class TestHintData:
    """Verify all hint data is complete and well-formed."""

    def test_all_12_commands_have_hints(self):
        expected = {
            "init",
            "bootstrap",
            "quick-wins",
            "ask",
            "why",
            "impact",
            "mcp",
            "onboard",
            "glossary",
            "insights",
            "roi",
            "usage",
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

    def test_quality_levels_have_valid_types(self):
        valid = {"perfect", "good", "normal", "bad"}
        for cmd, hint in HINTS.items():
            for q in hint.quality_levels:
                assert q.level in valid, f"{cmd}: invalid quality level '{q.level}'"
                assert q.description, f"{cmd}: empty description for {q.level}"

    def test_suggestions_are_strings(self):
        for cmd, hint in HINTS.items():
            for s in hint.suggestions:
                assert isinstance(s, str)
                assert len(s) > 5, f"{cmd}: suggestion too short"


class TestGetHint:
    def test_get_existing(self):
        hint = get_hint("ask")
        assert hint is not None
        assert hint.command == "codebase-memory ask"

    def test_get_nonexistent(self):
        hint = get_hint("nonexistent_command_xyz")
        assert hint is None

    def test_list_commands(self):
        cmds = list_commands()
        assert len(cmds) >= 12
        assert "ask" in cmds
        assert "bootstrap" in cmds
        assert "impact" in cmds


class TestFormatHint:
    def test_format_init(self):
        hint = get_hint("init")
        output = format_hint(hint)
        assert "Vault Initialization" in output
        assert "WHAT IT DOES" in output
        assert "HOW TO USE" in output
        assert "RESULT QUALITY" in output
        assert "PERFECT" in output
        assert "BAD" in output
        assert "Next:" in output

    def test_format_ask(self):
        hint = get_hint("ask")
        output = format_hint(hint)
        assert "Natural Language Q&A" in output
        assert "IMPROVE RESULTS" in output
        assert "Be specific" in output

    def test_format_bootstrap(self):
        hint = get_hint("bootstrap")
        output = format_hint(hint)
        assert "5-Step Learning Pipeline" in output
        assert "25+ patterns" in output

    def test_format_impact(self):
        hint = get_hint("impact")
        output = format_hint(hint)
        assert "Change Impact" in output
        assert "HIGH" in output
        assert "integration tests" in output

    def test_format_mcp(self):
        hint = get_hint("mcp")
        output = format_hint(hint)
        assert "MCP Server" in output
        assert "find_function" in output

    def test_format_onboard(self):
        hint = get_hint("onboard")
        output = format_hint(hint)
        assert "8-chapter" in output
        assert "Mermaid" in output

    def test_format_roi(self):
        hint = get_hint("roi")
        output = format_hint(hint)
        assert "ROI" in output
        assert "$200" in output

    def test_format_has_all_sections(self):
        """Every formatted hint must have all 4 CEO-required sections."""
        for cmd, hint in HINTS.items():
            output = format_hint(hint)
            assert "WHAT IT DOES" in output, f"{cmd}: missing WHAT IT DOES"
            assert "HOW TO USE" in output, f"{cmd}: missing HOW TO USE"
            assert "RESULT QUALITY" in output, f"{cmd}: missing QUALITY"


class TestFormatSummary:
    def test_summary_lists_all_commands(self):
        output = format_all_hints_summary()
        assert "User Guide" in output
        for cmd in ["ask", "bootstrap", "impact", "onboard", "roi"]:
            assert cmd in output

    def test_summary_has_titles(self):
        output = format_all_hints_summary()
        assert "Natural Language Q&A" in output
        assert "5-Step Learning Pipeline" in output


class TestHintContent:
    """Validate specific hint content matches design spec."""

    def test_init_next_step(self):
        hint = get_hint("init")
        assert "bootstrap" in hint.next_step

    def test_bootstrap_has_6_learners(self):
        hint = get_hint("bootstrap")
        assert "6 learners" in hint.what_it_does

    def test_ask_mentions_byok(self):
        hint = get_hint("ask")
        assert "BYOK" in hint.how_to_use

    def test_impact_mentions_depth(self):
        hint = get_hint("impact")
        assert "--depth" in hint.how_to_use

    def test_roi_mentions_privacy(self):
        hint = get_hint("roi")
        assert "privacy" in hint.what_it_does.lower()

    def test_usage_mentions_cost_threshold(self):
        hint = get_hint("usage")
        assert "$0.005" in hint.quality_levels[0].description
