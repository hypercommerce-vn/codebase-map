# HC-AI | ticket: MEM-M1-02
"""Tests for PythonASTParser — parse Python files into Evidence."""

from pathlib import Path

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


class TestPythonASTParserDirectory:
    """Tests for directory scanning (MEM-M1-02 finish)."""

    # HC-AI | ticket: MEM-M1-02

    @pytest.fixture()
    def project_dir(self, tmp_path: Path) -> Path:
        """Create a mini project directory with multiple Python files."""
        # app/service.py
        svc = tmp_path / "app" / "services"
        svc.mkdir(parents=True)
        (svc / "customer_service.py").write_text(
            "class CustomerService:\n"
            "    def create(self, name: str) -> dict:\n"
            "        return {'name': name}\n"
        )
        (svc / "order_service.py").write_text(
            "def place_order(item_id: int) -> dict:\n"
            "    return {'item': item_id}\n"
            "\n"
            "def cancel_order(order_id: int) -> bool:\n"
            "    return True\n"
        )

        # app/models/
        models = tmp_path / "app" / "models"
        models.mkdir(parents=True)
        (models / "user.py").write_text(
            "class User:\n" "    name: str\n" "    email: str\n"
        )

        # utils/
        utils = tmp_path / "utils"
        utils.mkdir()
        (utils / "helpers.py").write_text(
            "def format_name(s: str) -> str:\n" "    return s.title()\n"
        )

        # Should be excluded: __pycache__
        cache = tmp_path / "app" / "__pycache__"
        cache.mkdir()
        (cache / "cached.py").write_text("x = 1\n")

        # Should be excluded: .venv
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "pkg.py").write_text("y = 2\n")

        # Non-python file (ignored)
        (tmp_path / "README.md").write_text("# Project\n")

        return tmp_path

    def test_parse_directory_yields_evidence(
        self, parser: PythonASTParser, project_dir: Path
    ) -> None:
        """parse_directory yields Evidence from all Python files."""
        results = list(parser.parse_directory(project_dir))
        assert len(results) >= 5  # 1 class + 1 method + 2 funcs + 1 class + 1 func
        assert all(isinstance(e, Evidence) for e in results)

    def test_parse_directory_excludes_pycache(
        self, parser: PythonASTParser, project_dir: Path
    ) -> None:
        """Files in __pycache__/ are excluded by default."""
        results = list(parser.parse_directory(project_dir))
        sources = {e.source for e in results}
        assert not any("__pycache__" in s for s in sources)

    def test_parse_directory_excludes_venv(
        self, parser: PythonASTParser, project_dir: Path
    ) -> None:
        """Files in .venv/ are excluded by default."""
        results = list(parser.parse_directory(project_dir))
        sources = {e.source for e in results}
        assert not any(".venv" in s for s in sources)

    def test_parse_directory_custom_include(
        self, parser: PythonASTParser, project_dir: Path
    ) -> None:
        """Custom include pattern limits scan scope."""
        results = list(
            parser.parse_directory(project_dir, include=["app/services/**/*.py"])
        )
        # Only service files
        assert len(results) >= 3  # 1 class + 1 method + 2 funcs
        sources = {e.source for e in results}
        assert all("services" in s for s in sources)

    def test_parse_directory_custom_exclude(
        self, parser: PythonASTParser, project_dir: Path
    ) -> None:
        """Custom exclude pattern filters out matching files."""
        results = list(
            parser.parse_directory(
                project_dir,
                exclude=["**/helpers.py", "**/__pycache__/**", "**/.venv/**"],
            )
        )
        sources = {e.source for e in results}
        assert not any("helpers" in s for s in sources)

    def test_parse_directory_empty_dir(
        self, parser: PythonASTParser, tmp_path: Path
    ) -> None:
        """Empty directory yields nothing."""
        results = list(parser.parse_directory(tmp_path))
        assert results == []

    def test_scan_stats(self, parser: PythonASTParser, project_dir: Path) -> None:
        """scan_stats returns correct counts."""
        stats = parser.scan_stats(project_dir)
        assert stats["files"] >= 4  # 4 .py files (excl __pycache__, .venv)
        assert stats["nodes"] >= 5
        assert stats["classes"] >= 2  # CustomerService, User
        assert stats["functions"] >= 3  # place_order, cancel_order, format_name
        assert stats["methods"] >= 1  # create

    def test_scan_stats_empty(self, parser: PythonASTParser, tmp_path: Path) -> None:
        """scan_stats on empty dir returns all zeros."""
        stats = parser.scan_stats(tmp_path)
        assert stats["files"] == 0
        assert stats["nodes"] == 0


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
