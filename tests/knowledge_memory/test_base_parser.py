"""Tests for BaseParser ABC (KMP-M0-02)."""

# HC-AI | ticket: KMP-M0-02

from pathlib import Path

import pytest

from knowledge_memory.core.parsers import BaseParser, Evidence


def test_base_parser_is_abstract():
    with pytest.raises(TypeError):
        BaseParser()  # type: ignore[abstract]


def test_base_parser_concrete_subclass_works():
    class DummyParser(BaseParser):
        PARSER_NAME = "dummy"
        SUPPORTED_EXTENSIONS = (".txt",)

        def parse(self, source: Path):
            yield Evidence(source=str(source), data={"ok": True})

    p = DummyParser()
    assert p.supports(Path("foo.txt")) is True
    assert p.supports(Path("foo.py")) is False
    assert p.describe() == {"name": "dummy", "extensions": [".txt"]}

    out = list(p.parse(Path("bar.txt")))
    assert len(out) == 1
    assert isinstance(out[0], Evidence)
    assert out[0].source == "bar.txt"


def test_base_parser_default_supports_false():
    class EmptyParser(BaseParser):
        def parse(self, source: Path):
            return iter([])

    assert EmptyParser().supports(Path("x.py")) is False
