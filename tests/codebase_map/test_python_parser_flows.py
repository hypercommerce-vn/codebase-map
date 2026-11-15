# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CM-S3-04 business-flow annotations (`# flow: a, b`) in PythonParser.

Fixture sources are built with "\\n".join(...) so no line of this file starts
with a real `# flow:` comment.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codebase_map.parsers.python_parser import PythonParser, _extract_flow_annotations

REPO_ROOT = Path(__file__).resolve().parents[2]


def _parse(tmp_path: Path, lines: list[str]) -> dict[str, list[str]]:
    """Parse a fixture module; return {node name: flows} for tagged nodes."""
    src = tmp_path / "svc.py"
    src.write_text("\n".join(lines) + "\n", encoding="utf-8")
    nodes, _ = PythonParser().parse_file(src, "app")
    return {n.name: n.metadata["flows"] for n in nodes if n.metadata.get("flows")}


class TestRealFlowAnnotations:
    """Documented `# flow:` comments are still picked up."""

    @pytest.mark.parametrize(
        "line, expected",
        [
            ("# flow: signup, crm-sync", ["signup", "crm-sync"]),
            ("#flow:checkout", ["checkout"]),
            ("    # flow: checkout", ["checkout"]),
            ("# Flow : Onboarding_v2", ["Onboarding_v2"]),
        ],
    )
    def test_extract_matches_annotation_line(
        self, line: str, expected: list[str]
    ) -> None:
        assert _extract_flow_annotations(line) == {1: expected}

    def test_annotation_above_class_tags_node(self, tmp_path: Path) -> None:
        flows = _parse(
            tmp_path,
            [
                "# FDD: FDD-CRM-001",
                "# flow: signup, crm-sync",
                "class CustomerService:",
                "    pass",
            ],
        )
        assert flows["CustomerService"] == ["crm-sync", "signup"]

    def test_indented_annotation_tags_method(self, tmp_path: Path) -> None:
        flows = _parse(
            tmp_path,
            [
                "class OrderService:",
                "    # flow: checkout",
                "    def place(self):",
                "        return 1",
            ],
        )
        assert flows["place"] == ["checkout"]


class TestProseMentioningFlowIsIgnored:
    """Comments that merely contain `flow:` must not create flows."""

    @pytest.mark.parametrize(
        "line",
        [
            "# CM-S3-04: Business flow tagging — parse `# flow: name1, name2` comments",
            "# see the flow: it goes a, b",
            "# workflow: ci",
            "# flowchart: a, b",
            '"""Scan source for `# flow: name` comments."""',
            "x = 1  # flow: checkout",
        ],
    )
    def test_extract_ignores_non_annotation(self, line: str) -> None:
        assert _extract_flow_annotations(line) == {}

    def test_doc_comment_above_def_does_not_tag_def(self, tmp_path: Path) -> None:
        flows = _parse(
            tmp_path,
            [
                "# CM-S3-04: Business flow tagging — parse `# flow: name1, name2`",
                "PATTERN = 1",
                "",
                "",
                "def extract():",
                "    return PATTERN",
            ],
        )
        assert flows == {}


class TestSelfScan:
    """CBM mapping its own source must not show fake flows."""

    def test_self_scan_has_no_fake_flows(self) -> None:
        parser = PythonParser()
        tagged: dict[str, list[str]] = {}
        for py in sorted((REPO_ROOT / "codebase_map").rglob("*.py")):
            nodes, _ = parser.parse_file(py, "codebase_map")
            for n in nodes:
                if n.metadata.get("flows"):
                    tagged[n.id] = n.metadata["flows"]
        fake = {nid: f for nid, f in tagged.items() if {"name1", "name2"} & set(f)}
        assert fake == {}

    def test_extract_flow_annotations_node_untagged(self) -> None:
        src = REPO_ROOT / "codebase_map" / "parsers" / "python_parser.py"
        nodes, _ = PythonParser().parse_file(src, "codebase_map")
        target = [n for n in nodes if n.name == "_extract_flow_annotations"]
        assert len(target) == 1
        assert "flows" not in target[0].metadata
