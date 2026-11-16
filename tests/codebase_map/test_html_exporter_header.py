# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for the HTML exporter header: version badge, stat labels, flow bar.

Regressions found on the website demo map (PR #152 review gate):
the badge said "v2.0", the header said "1 domains", and an empty
"Flows:" row showed when no node had flows.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from codebase_map import __version__
from codebase_map.exporters.html_exporter import export_html
from codebase_map.graph.models import Graph, LayerType, Node, NodeType


def _node(name: str, domain: str = "other", flows: list[str] | None = None) -> Node:
    return Node(
        id=f"pkg.mod.{name}",
        name=name,
        node_type=NodeType.FUNCTION,
        layer=LayerType.UTIL,
        module_domain=domain,
        file_path="pkg/mod.py",
        line_start=1,
        metadata={"flows": flows} if flows else {},
    )


@pytest.fixture()
def html(tmp_path: Path) -> str:
    """Exported HTML for a one-domain graph with no flow annotations."""
    graph = Graph(project="demo", generated_at="2026-11-16T00:00:00Z")
    graph.add_node(_node("alpha"))
    graph.add_node(_node("beta"))
    out = export_html(graph, tmp_path / "index.html")
    return out.read_text(encoding="utf-8")


class TestVersionBadge:
    def test_badge_shows_package_version(self, html: str) -> None:
        assert f'<span class="logo-ver">v{__version__}</span>' in html


class TestStatLabels:
    def test_badges_use_singular_aware_helper(self, html: str) -> None:
        assert "statLabel(nodes.length, 'node')" in html
        assert "statLabel(edges.length, 'edge')" in html
        assert "statLabel(domainCount, 'domain')" in html
        assert "</strong> domains`" not in html

    @pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
    def test_helper_pluralizes(self, html: str) -> None:
        match = re.search(r"function statLabel\(count, noun\) \{.*?\n\}", html, re.S)
        assert match, "statLabel helper not found in exported HTML"
        script = match.group(0) + (
            "\nconsole.log(JSON.stringify("
            "[0, 1, 2].map(n => statLabel(n, 'domain'))));"
        )
        result = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        assert json.loads(result.stdout) == [
            "<strong>0</strong> domains",
            "<strong>1</strong> domain",
            "<strong>2</strong> domains",
        ]


class TestFlowBar:
    def test_flow_bar_starts_hidden(self, html: str) -> None:
        assert '<div id="flow-bar" class="flow-bar" hidden>' in html

    def test_hidden_attribute_wins_over_flex(self, html: str) -> None:
        """`.flow-bar { display: flex }` must not override `[hidden]`."""
        assert re.search(r"\.flow-bar\[hidden\]\s*\{\s*display:\s*none;?\s*\}", html)

    def test_flow_data_still_exported(self, tmp_path: Path) -> None:
        """Nodes with flows still reach the page, so the bar can show."""
        graph = Graph(project="demo", generated_at="2026-11-16T00:00:00Z")
        graph.add_node(_node("checkout", flows=["checkout"]))
        out = export_html(graph, tmp_path / "index.html")
        assert '"flows": ["checkout"]' in out.read_text(encoding="utf-8")
