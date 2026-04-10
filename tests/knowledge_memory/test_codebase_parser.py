# HC-AI | ticket: MEM-M1-02
"""Tests for PythonASTParser — parse Python files into Evidence."""

from pathlib import Path
from typing import List

import pytest

from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.codebase_parser import PythonASTParser


@pytest.fixture()
def parser() -> PythonASTParser:
    """Create a PythonASTParser instance."""
    return PythonASTParser()


@pytest.fixture()
def sample_py(tmp_path: Path) -> Path:
    """Create a sample Python file with classes and functions."""
    p = tmp_path / "sample_service.py"
    p.write_text(
        "class CustomerService:\n"
        '    """Service for customers."""\n'
        "\n"
        "    def create_customer(self, name: str) -> dict:\n"
        "        result = validate(name)\n"
        "        return save(result)\n"
        "\n"
        "    async def get_customer(self, id: int) -> dict:\n"
        "        return await fetch(id)\n"
        "\n"
        "\n"
        "def helper_function(x, y):\n"
        '    """A helper."""\n'
        "    return x + y\n"
    )
    return p


@pytest.fixture()
def decorated_py(tmp_path: Path) -> Path:
    """Python file with decorators."""
    p = tmp_path / "router.py"
    p.write_text(
        "from fastapi import APIRouter\n"
        "\n"
        "router = APIRouter()\n"
        "\n"
        "\n"
        '@router.get("/customers")\n'
        "def list_customers():\n"
        "    return get_all()\n"
    )
    return p


class TestPythonASTParserBasic:
    """Basic parser tests."""

    def test_parser_name(self, parser: PythonASTParser) -> None:
        assert parser.PARSER_NAME == "python_ast"

    def test_supported_extensions(self, parser: PythonASTParser) -> None:
        assert parser.SUPPORTED_EXTENSIONS == (".py",)

    def test_supports_py(self, parser: PythonASTParser) -> None:
        assert parser.supports(Path("test.py")) is True

    def test_not_supports_txt(self, parser: PythonASTParser) -> None:
        assert parser.supports(Path("test.txt")) is False

    def test_describe(self, parser: PythonASTParser) -> None:
        desc = parser.describe()
        assert desc["name"] == "python_ast"
        assert ".py" in desc["extensions"]


class TestPythonASTParserParsing:
    """Tests for actual parsing."""

    def test_parse_yields_evidence(
        self, parser: PythonASTParser, sample_py: Path
    ) -> None:
        """Parse yields Evidence for class + methods + functions."""
        results = list(parser.parse(sample_py))
        assert len(results) >= 4  # class + 2 methods + 1 function
        assert all(isinstance(e, Evidence) for e in results)

    def test_class_evidence(self, parser: PythonASTParser, sample_py: Path) -> None:
        """Class node has type='class' and method_count."""
        results = list(parser.parse(sample_py))
        classes = [e for e in results if e.data.get("type") == "class"]
        assert len(classes) == 1
        assert classes[0].data["name"] == "CustomerService"
        assert classes[0].data["method_count"] == 2

    def test_method_evidence(self, parser: PythonASTParser, sample_py: Path) -> None:
        """Methods have type='method' and class prefix in name."""
        results = list(parser.parse(sample_py))
        methods = [e for e in results if e.data.get("type") == "method"]
        assert len(methods) == 2
        names = {m.data["name"] for m in methods}
        assert "CustomerService.create_customer" in names
        assert "CustomerService.get_customer" in names

    def test_function_evidence(self, parser: PythonASTParser, sample_py: Path) -> None:
        """Top-level function has type='function'."""
        results = list(parser.parse(sample_py))
        funcs = [e for e in results if e.data.get("type") == "function"]
        assert len(funcs) == 1
        assert funcs[0].data["name"] == "helper_function"

    def test_async_detected(self, parser: PythonASTParser, sample_py: Path) -> None:
        """Async methods have is_async=True."""
        results = list(parser.parse(sample_py))
        async_evs = [e for e in results if e.data.get("is_async")]
        assert len(async_evs) == 1
        assert "get_customer" in async_evs[0].data["name"]

    def test_calls_extracted(self, parser: PythonASTParser, sample_py: Path) -> None:
        """Method calls are extracted."""
        results = list(parser.parse(sample_py))
        create = [
            e
            for e in results
            if e.data.get("name") == "CustomerService.create_customer"
        ]
        assert len(create) == 1
        assert "validate" in create[0].data["calls"]
        assert "save" in create[0].data["calls"]

    def test_params_extracted(self, parser: PythonASTParser, sample_py: Path) -> None:
        """Parameters (excluding self/cls) are extracted."""
        results = list(parser.parse(sample_py))
        create = [
            e
            for e in results
            if e.data.get("name") == "CustomerService.create_customer"
        ]
        assert "name" in create[0].data["params"]
        assert "self" not in create[0].data["params"]

    def test_line_range_set(self, parser: PythonASTParser, sample_py: Path) -> None:
        """Evidence has correct line_range."""
        results = list(parser.parse(sample_py))
        assert all(e.line_range is not None for e in results)
        assert all(e.line_range[0] >= 1 for e in results)

    def test_layer_detection_service(
        self, parser: PythonASTParser, sample_py: Path
    ) -> None:
        """File in *_service.py detected as service layer."""
        results = list(parser.parse(sample_py))
        assert all(e.data.get("layer") == "service" for e in results)

    def test_decorators_extracted(
        self, parser: PythonASTParser, decorated_py: Path
    ) -> None:
        """Decorators are extracted."""
        results = list(parser.parse(decorated_py))
        funcs = [e for e in results if e.data.get("type") == "function"]
        assert len(funcs) >= 1
        assert len(funcs[0].data["decorators"]) >= 1


class TestPythonASTParserEdgeCases:
    """Edge case tests."""

    def test_nonexistent_file(self, parser: PythonASTParser, tmp_path: Path) -> None:
        """Nonexistent file yields nothing."""
        results = list(parser.parse(tmp_path / "nope.py"))
        assert results == []

    def test_non_py_file(self, parser: PythonASTParser, tmp_path: Path) -> None:
        """Non-.py file yields nothing."""
        p = tmp_path / "readme.md"
        p.write_text("# Hello")
        results = list(parser.parse(p))
        assert results == []

    def test_syntax_error_file(self, parser: PythonASTParser, tmp_path: Path) -> None:
        """File with syntax error yields nothing (no crash)."""
        p = tmp_path / "bad.py"
        p.write_text("def broken(\n")
        results = list(parser.parse(p))
        assert results == []

    def test_empty_file(self, parser: PythonASTParser, tmp_path: Path) -> None:
        """Empty .py file yields nothing."""
        p = tmp_path / "empty.py"
        p.write_text("")
        results = list(parser.parse(p))
        assert results == []

    def test_layer_detection_router(
        self, parser: PythonASTParser, tmp_path: Path
    ) -> None:
        """Router file detected as route layer."""
        p = tmp_path / "router.py"
        p.write_text("def get_items(): pass\n")
        results = list(parser.parse(p))
        assert results[0].data["layer"] == "route"

    def test_layer_detection_model(
        self, parser: PythonASTParser, tmp_path: Path
    ) -> None:
        """Model file detected as model layer."""
        p = tmp_path / "models.py"
        p.write_text("class User: pass\n")
        results = list(parser.parse(p))
        assert results[0].data["layer"] == "model"

    def test_layer_detection_test(
        self, parser: PythonASTParser, tmp_path: Path
    ) -> None:
        """Test file detected as test layer."""
        p = tmp_path / "test_main.py"
        p.write_text("def test_something(): pass\n")
        results = list(parser.parse(p))
        assert results[0].data["layer"] == "test"
