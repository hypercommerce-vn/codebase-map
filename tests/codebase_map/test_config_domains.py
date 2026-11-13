# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for CM-S4-01: config-driven domain overrides."""

from __future__ import annotations

from pathlib import Path

from codebase_map.config import Config, SourceConfig
from codebase_map.graph.builder import GraphBuilder


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _project(tmp_path: Path) -> Path:
    _write(tmp_path, "app/billing/pay.py", "def charge():\n    return 1\n")
    _write(tmp_path, "app/billing/refund.py", "def refund():\n    return 2\n")
    _write(tmp_path, "app/misc/util.py", "def helper():\n    return 3\n")
    _write(tmp_path, "app/misc/other.py", "def untouched():\n    return 4\n")
    return tmp_path


def _build(root: Path, domains: dict[str, list[str]]) -> dict[str, str]:
    config = Config(
        project="demo",
        sources=[SourceConfig(path=".", language="python")],
        project_root=root,
        domains=domains,
    )
    graph = GraphBuilder(config, use_cache=False).build()
    return {node.name: node.module_domain for node in graph.nodes.values()}


class TestDomainsParsing:
    """Config.from_yaml reads the ``domains`` section."""

    def test_list_and_string_patterns(self, tmp_path: Path) -> None:
        cfg = tmp_path / "codebase-map.yaml"
        cfg.write_text(
            "project: demo\n"
            "sources:\n"
            "  - path: .\n"
            "domains:\n"
            "  thanh-toan:\n"
            "    - 'app/billing/*'\n"
            "    - '*.refund'\n"
            "  khac: 'app/misc/*'\n",
            encoding="utf-8",
        )
        config = Config.from_yaml(cfg)
        assert config.domains == {
            "thanh-toan": ["app/billing/*", "*.refund"],
            "khac": ["app/misc/*"],
        }

    def test_missing_section_gives_empty_mapping(self, tmp_path: Path) -> None:
        cfg = tmp_path / "codebase-map.yaml"
        cfg.write_text("project: demo\nsources:\n  - path: .\n", encoding="utf-8")
        assert Config.from_yaml(cfg).domains == {}


class TestDomainOverrides:
    """GraphBuilder applies ``domains`` patterns to every node."""

    def test_file_path_pattern_sets_domain(self, tmp_path: Path) -> None:
        domains = _build(_project(tmp_path), {"thanh-toan": ["app/billing/*"]})
        assert domains["charge"] == "thanh-toan"
        assert domains["refund"] == "thanh-toan"

    def test_node_id_pattern_sets_domain(self, tmp_path: Path) -> None:
        domains = _build(_project(tmp_path), {"tien-ich": ["*.helper"]})
        assert domains["helper"] == "tien-ich"

    def test_unmatched_node_keeps_parser_guess(self, tmp_path: Path) -> None:
        root = _project(tmp_path)
        baseline = _build(root, {})
        overridden = _build(root, {"thanh-toan": ["app/billing/*"]})
        assert overridden["untouched"] == baseline["untouched"]
        assert overridden["helper"] == baseline["helper"]

    def test_first_matching_domain_wins(self, tmp_path: Path) -> None:
        domains = _build(
            _project(tmp_path),
            {"dau-tien": ["app/billing/*"], "thu-hai": ["app/billing/pay.py"]},
        )
        assert domains["charge"] == "dau-tien"

    def test_no_domains_leaves_graph_unchanged(self, tmp_path: Path) -> None:
        root = _project(tmp_path)
        assert _build(root, {}) == _build(root, {})
