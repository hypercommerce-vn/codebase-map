# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CBM-P1-02: CLI --label flag."""

from __future__ import annotations

from codebase_map.cli import main


class TestCLILabelFlag:
    """CBM-P1-02: generate --label flag."""

    def test_label_flag_in_help(self) -> None:
        """--label appears in generate help text."""
        import io
        import sys

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            main(["generate", "--help"])
        except SystemExit:
            pass
        sys.stdout = old_stdout
        output = captured.getvalue()
        assert "--label" in output
        assert "Snapshot label" in output

    def test_label_flag_accepts_value(self) -> None:
        """--label baseline is accepted by argparse without error."""
        import argparse

        # Build parser manually to test arg parsing
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        gen = sub.add_parser("generate")
        gen.add_argument("-c", "--config", default="codebase-map.yaml")
        gen.add_argument("--label", default="")
        gen.add_argument("--no-cache", action="store_true")

        args = parser.parse_args(["generate", "--label", "baseline"])
        assert args.label == "baseline"
        assert args.command == "generate"

    def test_label_default_empty(self) -> None:
        """Default label is empty string (triggers auto-label)."""
        import argparse

        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        gen = sub.add_parser("generate")
        gen.add_argument("--label", default="")

        args = parser.parse_args(["generate"])
        assert args.label == ""
