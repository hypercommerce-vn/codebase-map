# HC-AI | ticket: FDD-TOOL-CODEMAP
"""TypeScript / JavaScript Parser (CM-S3-06).

Regex-based line parser for .ts/.tsx/.js/.jsx files. Extracts:
  - Function declarations (function foo, const foo = () => ...)
  - Class declarations and methods
  - Decorators (@Controller, @Get, @Post → ROUTE)
  - Imports (import ... from './module')
  - Call expressions (best-effort, body scan)

Design note: chosen over tree-sitter WASM to keep zero-deps + offline.
The regex approach targets common, well-formatted TS/JS patterns and
should hit ≥95% function/class capture for typical NestJS/Express/Next.js
codebases. Edge cases (deeply nested arrow chains, computed prop names)
are tolerated by skip-not-crash.
"""
from __future__ import annotations

import re
from pathlib import Path

from codebase_map.graph.models import Edge, EdgeType, LayerType, Node, NodeType
from codebase_map.parsers.base import BaseParser

# HC-AI | ticket: FDD-TOOL-CODEMAP
# Reuse FDD comment annotation regex for parity with python_parser
_FDD_PATTERN = re.compile(
    r"//[^\n]*?(?:FDD|ticket)\s*:\s*(FDD-[A-Z]+-[A-Z0-9]+)", re.IGNORECASE
)

# function foo(...)  /  export function foo(...)  /  export default function foo
_FUNC_DECL = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\("
)

# const foo = (...) => ...  /  export const foo = async (...) =>
_ARROW_CONST = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*"
    r"(?::\s*[^=]+)?=\s*(?:async\s+)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"
)

# class Foo  /  export class Foo  /  export default class Foo extends Bar
_CLASS_DECL = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:abstract\s+)?class\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)"
    r"(?:\s+extends\s+(?P<base>[A-Za-z_$][\w$.]*))?"
)

# Method inside class body: foo(...) {   /   async foo(...) {   /   private foo(...) :
_METHOD_DECL = re.compile(
    r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|readonly\s+|async\s+)*"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*\(.*\)\s*(?::\s*[^={]+)?\s*\{"
)

# Decorators: @Controller(...)  @Get('/path')  @Post()
_DECORATOR = re.compile(r"^\s*@(?P<name>[A-Za-z_$][\w$.]*)")

# Imports: import { Foo, Bar } from './baz'  /  import Default from "x"
_IMPORT = re.compile(r"^\s*import\s+(?:[^'\"]+from\s+)?['\"](?P<src>[^'\"]+)['\"]")

# Call expression — best effort: name( OR obj.name(
_CALL = re.compile(r"(?P<name>[A-Za-z_$][\w$]*)\s*\(")

# Tokens that look like calls but are control flow / not real function calls
_CALL_BLOCKLIST = {
    "if",
    "for",
    "while",
    "switch",
    "return",
    "catch",
    "function",
    "typeof",
    "new",
    "await",
    "throw",
    "yield",
    "class",
    "super",
    "constructor",
    "import",
    "export",
    "Number",
    "String",
    "Boolean",
    "Array",
    "Object",
    "Map",
    "Set",
    "Promise",
}

# Decorators that mark routes (NestJS / common HTTP frameworks)
_ROUTE_DECORATORS = {
    "Controller",
    "Get",
    "Post",
    "Put",
    "Patch",
    "Delete",
    "Options",
    "Head",
    "All",
    "Route",
    "RestController",
}


class TypeScriptParser(BaseParser):
    """Regex-based TS/JS parser. Extends BaseParser interface."""

    def supported_extensions(self) -> list[str]:
        return [".ts", ".tsx", ".js", ".jsx"]

    # ─────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────
    def parse_file(
        self, file_path: Path, base_module: str = ""
    ) -> tuple[list[Node], list[Edge]]:
        try:
            source = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"[WARN] TS parser: cannot read {file_path}: {exc}")
            return [], []

        try:
            return self._parse_source(source, file_path, base_module)
        except Exception as exc:  # noqa: BLE001 — graceful skip per AC
            print(f"[WARN] TS parser: failed on {file_path}: {exc}")
            return [], []

    # ─────────────────────────────────────────────────────────────────
    # Core
    # ─────────────────────────────────────────────────────────────────
    def _parse_source(
        self, source: str, file_path: Path, base_module: str
    ) -> tuple[list[Node], list[Edge]]:
        nodes: list[Node] = []
        edges: list[Edge] = []

        # Build module path: base_module + file stem (without ext)
        rel_module = self._module_id(file_path, base_module)
        domain = self._infer_domain(file_path, base_module)
        layer = self._infer_layer(file_path)

        lines = source.splitlines()
        fdd_by_line = self._extract_fdd(lines)

        # State
        class_stack: list[tuple[str, int]] = []  # [(class_id, brace_depth)]
        pending_decorators: list[str] = []
        depth = 0  # global brace depth
        current_func_id: str | None = None
        current_func_brace: int = -1

        for idx, raw in enumerate(lines, start=1):
            line = self._strip_comment(raw)

            # Track decorators (apply to next decl)
            dec_match = _DECORATOR.match(line)
            if dec_match:
                pending_decorators.append(dec_match.group("name"))
                continue

            # Imports → edges from module → imported source
            imp_match = _IMPORT.match(line)
            if imp_match:
                edges.append(
                    Edge(
                        source=rel_module,
                        target=imp_match.group("src"),
                        edge_type=EdgeType.IMPORTS,
                    )
                )
                continue

            # Class declaration
            cls_match = _CLASS_DECL.match(line)
            if cls_match:
                cname = cls_match.group("name")
                cid = f"{rel_module}.{cname}"
                node = self._make_node(
                    nid=cid,
                    name=cname,
                    ntype=self._classify_class(pending_decorators),
                    layer=layer,
                    domain=domain,
                    file_path=str(file_path),
                    line_start=idx,
                    decorators=pending_decorators[:],
                    fdd=self._find_fdd(fdd_by_line, idx),
                )
                nodes.append(node)
                # inheritance edge
                base = cls_match.group("base")
                if base:
                    edges.append(
                        Edge(
                            source=cid,
                            target=base,
                            edge_type=EdgeType.INHERITS,
                        )
                    )
                pending_decorators.clear()
                # Class body opens at next `{` — assume same line for simplicity
                if "{" in line:
                    class_stack.append((cid, depth))
                    depth += line.count("{") - line.count("}")
                continue

            # Function declaration
            fn_match = _FUNC_DECL.match(line) or _ARROW_CONST.match(line)
            if fn_match:
                fname = fn_match.group("name")
                fid = f"{rel_module}.{fname}"
                ntype = self._classify_func(pending_decorators)
                node = self._make_node(
                    nid=fid,
                    name=fname,
                    ntype=ntype,
                    layer=layer,
                    domain=domain,
                    file_path=str(file_path),
                    line_start=idx,
                    decorators=pending_decorators[:],
                    fdd=self._find_fdd(fdd_by_line, idx),
                )
                nodes.append(node)
                pending_decorators.clear()
                current_func_id = fid
                current_func_brace = depth
                depth += line.count("{") - line.count("}")
                continue

            # Method inside class
            if class_stack and _METHOD_DECL.match(line):
                m_match = _METHOD_DECL.match(line)
                assert m_match is not None
                mname = m_match.group("name")
                if mname not in _CALL_BLOCKLIST or mname == "constructor":
                    cls_id, _ = class_stack[-1]
                    mid = f"{cls_id}.{mname}"
                    ntype = (
                        NodeType.ROUTE
                        if any(d in _ROUTE_DECORATORS for d in pending_decorators)
                        else NodeType.METHOD
                    )
                    node = self._make_node(
                        nid=mid,
                        name=mname,
                        ntype=ntype,
                        layer=layer,
                        domain=domain,
                        file_path=str(file_path),
                        line_start=idx,
                        decorators=pending_decorators[:],
                        fdd=self._find_fdd(fdd_by_line, idx),
                        parent_class=cls_id,
                    )
                    nodes.append(node)
                    pending_decorators.clear()
                    current_func_id = mid
                    current_func_brace = depth
                depth += line.count("{") - line.count("}")
                continue

            # Inside a function body → harvest call edges (best effort)
            if current_func_id is not None:
                for call in _CALL.finditer(line):
                    cname = call.group("name")
                    if cname in _CALL_BLOCKLIST:
                        continue
                    edges.append(
                        Edge(
                            source=current_func_id,
                            target=cname,
                            edge_type=EdgeType.CALLS,
                        )
                    )

            # Brace tracking
            depth += line.count("{") - line.count("}")

            # Pop class if we exited its body
            while class_stack and depth <= class_stack[-1][1]:
                class_stack.pop()

            # Reset current_func when we exit its scope
            if current_func_id is not None and depth <= current_func_brace:
                current_func_id = None
                current_func_brace = -1

            # Reset stale decorators (orphan decorator with no decl)
            if line.strip() and not _DECORATOR.match(line):
                pending_decorators.clear()

        return nodes, edges

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────
    def _make_node(
        self,
        nid: str,
        name: str,
        ntype: NodeType,
        layer: LayerType,
        domain: str,
        file_path: str,
        line_start: int,
        decorators: list[str],
        fdd: str,
        parent_class: str = "",
    ) -> Node:
        node = Node(
            id=nid,
            name=name,
            node_type=ntype,
            layer=layer,
            module_domain=domain,
            file_path=file_path,
            line_start=line_start,
            decorators=decorators,
            parent_class=parent_class,
        )
        if fdd:
            node.metadata["fdd"] = fdd
        node.metadata["language"] = "typescript"
        return node

    def _module_id(self, file_path: Path, base_module: str) -> str:
        stem = file_path.with_suffix("").as_posix()
        if base_module:
            return f"{base_module}.{stem.replace('/', '.')}"
        return stem.replace("/", ".")

    def _infer_domain(self, file_path: Path, base_module: str) -> str:
        parts = file_path.parts
        for known in (
            "crm",
            "cdp",
            "ecommerce",
            "auth",
            "billing",
            "private_traffic",
            "core",
        ):
            if known in parts:
                return known
        return base_module or "core"

    def _infer_layer(self, file_path: Path) -> LayerType:
        s = file_path.as_posix().lower()
        if "/test" in s or s.endswith(".test.ts") or s.endswith(".spec.ts"):
            return LayerType.TEST
        if "controller" in s or "/routes" in s or "/router" in s:
            return LayerType.ROUTER
        if "service" in s:
            return LayerType.SERVICE
        if "repository" in s or "/repo" in s:
            return LayerType.REPOSITORY
        if "model" in s or "entity" in s or "schema" in s:
            return LayerType.MODEL
        if "worker" in s or "queue" in s or "job" in s:
            return LayerType.WORKER
        if "util" in s or "helper" in s:
            return LayerType.UTIL
        return LayerType.UNKNOWN

    def _classify_func(self, decorators: list[str]) -> NodeType:
        if any(d in _ROUTE_DECORATORS for d in decorators):
            return NodeType.ROUTE
        return NodeType.FUNCTION

    def _classify_class(self, decorators: list[str]) -> NodeType:
        if any(d in _ROUTE_DECORATORS for d in decorators):
            return NodeType.ROUTE  # NestJS @Controller
        return NodeType.CLASS

    def _extract_fdd(self, lines: list[str]) -> dict[int, str]:
        result: dict[int, str] = {}
        for idx, line in enumerate(lines, start=1):
            m = _FDD_PATTERN.search(line)
            if m:
                result[idx] = m.group(1).upper()
        return result

    def _find_fdd(self, fdd_by_line: dict[int, str], line_start: int) -> str:
        for offset in range(0, 6):
            cand = fdd_by_line.get(line_start - offset)
            if cand:
                return cand
        return ""

    def _strip_comment(self, line: str) -> str:
        # Remove `// ...` trailing comment, but preserve URLs in strings (best effort)
        idx = line.find("//")
        if idx >= 0 and not (line[:idx].count('"') % 2 or line[:idx].count("'") % 2):
            return line[:idx]
        return line
