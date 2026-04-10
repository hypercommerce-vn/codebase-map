# HC-AI | ticket: MEM-M1-02
"""PythonASTParser — parse Python files into Evidence objects for KMP."""

import ast
import fnmatch
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union

from knowledge_memory.core.parsers.base import BaseParser
from knowledge_memory.core.parsers.evidence import Evidence


def _decorator_names(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef],
) -> List[str]:
    """Extract decorator names as strings."""
    names: List[str] = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            names.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.append(ast.unparse(dec))
        elif isinstance(dec, ast.Call):
            func = dec.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(ast.unparse(func))
            else:
                names.append(ast.unparse(dec))
        else:
            names.append(ast.unparse(dec))
    return names


def _detect_layer(file_path: str) -> str:
    """Detect architecture layer from file path (lightweight version)."""
    p = file_path.lower()
    fname = p.rsplit("/", 1)[-1] if "/" in p else p

    if "router" in fname or "/endpoints/" in p or "/api/" in p:
        return "route"
    if "service" in fname or "/services/" in p:
        return "service"
    if "model" in fname or "/models/" in p:
        return "model"
    if fname.startswith("test_") or "/tests/" in p or "conftest" in fname:
        return "test"
    if "schema" in fname or "/schemas/" in p:
        return "schema"
    if any(
        kw in p
        for kw in (
            "utils",
            "helpers",
            "processor",
            "pipeline",
            "builder",
            "mapper",
        )
    ):
        return "util"
    return "unknown"


def _extract_calls(
    node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
) -> List[str]:
    """Extract function/method call names from a function body."""
    calls: List[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Name):
                calls.append(child.func.id)
            elif isinstance(child.func, ast.Attribute):
                calls.append(child.func.attr)
    return calls


class PythonASTParser(BaseParser):
    """Parse Python files via AST, yielding Evidence per function/class/method.

    Each Evidence contains structured data about one code entity:
    name, type (function/class/method), file path, line range,
    decorators, parameters, calls made, and detected layer.
    """

    PARSER_NAME = "python_ast"
    SUPPORTED_EXTENSIONS = (".py",)

    def parse(self, source: Path) -> Iterator[Evidence]:
        """Parse a Python file, yield Evidence per function/class/method."""
        if not source.exists() or source.suffix != ".py":
            return

        try:
            text = source.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            return

        try:
            tree = ast.parse(text, filename=str(source))
        except SyntaxError:
            return

        file_str = str(source)
        layer = _detect_layer(file_str)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                yield Evidence(
                    source=file_str,
                    data={
                        "name": node.name,
                        "type": "class",
                        "layer": layer,
                        "decorators": _decorator_names(node),
                        "bases": [ast.unparse(b) for b in node.bases],
                        "method_count": sum(
                            1
                            for n in node.body
                            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                        ),
                    },
                    line_range=(node.lineno, node.end_lineno or node.lineno),
                    metadata={"file_path": file_str, "layer": layer},
                )

                # Also yield each method inside the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        yield self._func_to_evidence(
                            item,
                            file_str,
                            layer,
                            class_name=node.name,
                        )

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip methods already yielded inside ClassDef
                if self._is_method(node, tree):
                    continue
                yield self._func_to_evidence(node, file_str, layer)

    def _func_to_evidence(
        self,
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        file_str: str,
        layer: str,
        class_name: Optional[str] = None,
    ) -> Evidence:
        """Convert a function/method AST node to Evidence."""
        params: List[str] = []
        for arg in node.args.args:
            if arg.arg not in ("self", "cls"):
                params.append(arg.arg)

        name = f"{class_name}.{node.name}" if class_name else node.name
        node_type = "method" if class_name else "function"

        return Evidence(
            source=file_str,
            data={
                "name": name,
                "type": node_type,
                "layer": layer,
                "decorators": _decorator_names(node),
                "params": params,
                "calls": _extract_calls(node),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "return_type": (ast.unparse(node.returns) if node.returns else ""),
            },
            line_range=(node.lineno, node.end_lineno or node.lineno),
            metadata={
                "file_path": file_str,
                "layer": layer,
                "class_name": class_name or "",
            },
        )

    # HC-AI | ticket: MEM-M1-02
    def parse_directory(
        self,
        root: Path,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> Iterator[Evidence]:
        """Scan a directory tree for Python files and yield Evidence.

        Args:
            root: Project root directory to scan.
            include: Glob patterns for files to include (default: ``["**/*.py"]``).
            exclude: Glob patterns for files to exclude
                     (default: common non-source dirs).

        Yields:
            Evidence objects for every function/class/method found.
        """
        if include is None:
            include = ["**/*.py"]
        if exclude is None:
            exclude = [
                "**/__pycache__/**",
                "**/.venv/**",
                "**/venv/**",
                "**/node_modules/**",
                "**/.git/**",
                "**/dist/**",
                "**/.tox/**",
                "**/.mypy_cache/**",
                "**/.pytest_cache/**",
            ]

        # Collect matching files
        files: List[Path] = []
        for pattern in include:
            for p in root.glob(pattern):
                if p.is_file() and self.supports(p):
                    # Check exclude patterns
                    rel = str(p.relative_to(root))
                    if not any(fnmatch.fnmatch(rel, ex) for ex in exclude):
                        files.append(p)

        # Deduplicate and sort for deterministic ordering
        files = sorted(set(files))

        for f in files:
            yield from self.parse(f)

    # HC-AI | ticket: MEM-M1-02
    def scan_stats(
        self,
        root: Path,
        include: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
    ) -> Dict[str, int]:
        """Scan directory and return stats without yielding all evidence.

        Returns dict with keys: files, nodes, classes, functions, methods.
        Useful for pre-scan estimation and summary display.
        """
        if include is None:
            include = ["**/*.py"]
        if exclude is None:
            exclude = [
                "**/__pycache__/**",
                "**/.venv/**",
                "**/venv/**",
                "**/node_modules/**",
                "**/.git/**",
            ]

        stats: Dict[str, int] = {
            "files": 0,
            "nodes": 0,
            "classes": 0,
            "functions": 0,
            "methods": 0,
        }

        files: List[Path] = []
        for pattern in include:
            for p in root.glob(pattern):
                if p.is_file() and self.supports(p):
                    rel = str(p.relative_to(root))
                    if not any(fnmatch.fnmatch(rel, ex) for ex in exclude):
                        files.append(p)

        files = sorted(set(files))
        stats["files"] = len(files)

        for f in files:
            for ev in self.parse(f):
                stats["nodes"] += 1
                node_type = ev.data.get("type", "")
                if node_type == "class":
                    stats["classes"] += 1
                elif node_type == "function":
                    stats["functions"] += 1
                elif node_type == "method":
                    stats["methods"] += 1

        return stats

    @staticmethod
    def _is_method(
        node: Union[ast.FunctionDef, ast.AsyncFunctionDef],
        tree: ast.Module,
    ) -> bool:
        """Check if a function node is a method inside a class."""
        for cls_node in ast.walk(tree):
            if isinstance(cls_node, ast.ClassDef):
                if node in cls_node.body:
                    return True
        return False
