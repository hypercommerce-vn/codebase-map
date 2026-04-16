"""Smoke tests for KMP core skeleton (KMP-M0-01, KMP-M0-02)."""

# HC-AI | ticket: KMP-M0-02

import importlib

import pytest

CORE_SUBPACKAGES = [
    "knowledge_memory",
    "knowledge_memory.core",
    "knowledge_memory.core.vault",
    "knowledge_memory.core.learners",
    "knowledge_memory.core.parsers",
    "knowledge_memory.core.ai",
    "knowledge_memory.core.mcp",
    "knowledge_memory.core.licensing",
    "knowledge_memory.core.cli",
    "knowledge_memory.core.telemetry",
    "knowledge_memory.core.config",
]


@pytest.mark.parametrize("module_name", CORE_SUBPACKAGES)
def test_core_subpackages_importable(module_name):
    """Every declared core sub-package must be importable."""
    module = importlib.import_module(module_name)
    assert module is not None


def test_top_level_version():
    import knowledge_memory

    assert knowledge_memory.__version__ == "1.0.0"


def test_pattern_dataclass():
    from knowledge_memory.core.learners import Pattern

    p = Pattern(
        name="naming::service_suffix",
        category="naming",
        confidence=85.0,
        evidence=[{"source": "foo.py"}],
    )
    assert p.name == "naming::service_suffix"
    assert p.category == "naming"
    assert p.confidence == 85.0
    assert len(p.evidence) == 1
    assert p.vertical == ""
    assert p.created_at  # populated by default factory
    assert p.metadata == {}


def test_evidence_dataclass():
    from knowledge_memory.core.parsers import Evidence

    e = Evidence(
        source="src/foo.py",
        data={"text": "def hello(): pass"},
        line_range=(10, 10),
        commit_sha="abc123",
    )
    assert e.source == "src/foo.py"
    assert e.data["text"] == "def hello(): pass"
    assert e.line_range == (10, 10)
    assert e.commit_sha == "abc123"
    assert e.metadata == {}


def test_base_vault_is_abstract():
    from knowledge_memory.core.vault import BaseVault

    with pytest.raises(TypeError):
        BaseVault()  # type: ignore[abstract]


def test_base_vault_concrete_subclass_works():
    from pathlib import Path

    from knowledge_memory.core.vault import BaseVault

    class DummyVault(BaseVault):
        VERTICAL_NAME = "dummy"

        def init(self, root: Path, force: bool = False) -> None:
            return None

        def snapshot(self):
            return object()

        def get_corpus_iterator(self):
            return iter([])

        def schema_extension_sql(self) -> str:
            return ""

    v = DummyVault()
    assert v.VERTICAL_NAME == "dummy"
    assert list(v.get_corpus_iterator()) == []
    assert v.schema_extension_sql() == ""
