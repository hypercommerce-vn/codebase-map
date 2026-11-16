# HC-AI | ticket: FDD-TOOL-CODEMAP
"""TypeScript / JavaScript Parser (CM-S3-06).

Regex-based line parser for .ts/.tsx/.js/.jsx files. Extracts:
  - Function declarations (function foo, const foo = () => ...)
  - Class declarations and methods
  - Decorators (@Controller, @Get, @Post → ROUTE)
  - Imports (import ... from './module'), including multi-line ones
  - Call expressions and JSX element usage (best-effort, body scan)
  - Where each function ends, and a content fingerprint of its body

Design note: chosen over tree-sitter WASM to keep zero-deps + offline.
The regex approach targets common, well-formatted TS/JS patterns and
should hit ≥95% function/class capture for typical NestJS/Express/Next.js
codebases. Edge cases (deeply nested arrow chains, computed prop names)
are tolerated by skip-not-crash.
"""

from __future__ import annotations

import re
from pathlib import Path

from codebase_map.fingerprint import named_hashes
from codebase_map.graph.models import Edge, EdgeType, LayerType, Node, NodeType
from codebase_map.parsers.base import BaseParser

# HC-AI | ticket: FDD-TOOL-CODEMAP
# Reuse FDD comment annotation regex for parity with python_parser
_FDD_PATTERN = re.compile(
    r"//[^\n]*?(?:FDD|ticket)\s*:\s*(FDD-[A-Z]+-[A-Z0-9]+)", re.IGNORECASE
)

# function foo(...)  /  export function foo<T>(...)  /  export default function foo
# VIBE-102: an optional generic parameter list may sit between the name and "(".
_FUNC_DECL = re.compile(
    r"^\s*(?:export\s+(?P<default>default\s+)?)?(?:async\s+)?function\s*\*?\s*"
    r"(?P<name>[A-Za-z_$][\w$]*)\s*(?:<.*?>)?\s*\("
)

# const foo = (...) => ...  /  export const foo = async <T>(...): R =>
_ARROW_CONST = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*"
    r"(?::\s*[^=]+)?=\s*(?:async\s+)?(?:<[^>(]*>\s*)?"
    r"(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*(?::\s*[^=]+?)?\s*=>"
)

# VIBE-102: `const foo = (` — the parameter list continues on the next lines,
# as formatters write it for a component with several props.
_ARROW_OPEN = re.compile(
    r"^\s*(?:export\s+)?(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*"
    r"(?::\s*[^=]+)?=\s*(?:async\s+)?(?:<[^>(]*>\s*)?\("
)
# What follows the ")" that closes an arrow function's parameter list
_ARROW_TAIL = re.compile(r"\s*(?::\s*[^=]+?)?\s*=>")

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

# VIBE-102: whole import statements, which may span several lines.
#   import { Foo, Bar as Baz } from './x'  /  import Default from "x"  /  import "x"
_IMPORT_STMT = re.compile(
    r"^[ \t]*import\s+(?P<type>type\s+)?(?P<clause>[^;'\"]*?)\s*from\s*"
    r"['\"](?P<src>[^'\"]+)['\"]"
    r"|^[ \t]*import\s*['\"](?P<bare>[^'\"]+)['\"]",
    re.MULTILINE,
)
_IMPORT_LINE = re.compile(r"^\s*import\b")
# VIBE-103: `export { a, b as c } from "./x"` and `export * from "./x"`
_REEXPORT_STMT = re.compile(
    r"^[ \t]*export\s+(?P<type>type\s+)?"
    r"(?P<clause>\*(?:\s+as\s+[A-Za-z_$][\w$]*)?|\{[^}]*\})\s*from\s*"
    r"['\"](?P<src>[^'\"]+)['\"]",
    re.MULTILINE,
)
# VIBE-103: a top-level declaration that exists only for the type checker
_TYPE_DECL = re.compile(
    r"^(?:export\s+)?(?:declare\s+\S|type\s+[A-Za-z_$]|interface\s+[A-Za-z_$])"
)
_TYPE_CONTINUES_AFTER = ("=", "|", "&", ",", "<", "?", ":", "extends")
_TYPE_CONTINUES_BEFORE = ("|", "&", "?", ":", "extends")
_IDENTIFIER = re.compile(r"[A-Za-z_$][\w$]*")
_EXPORT_DEFAULT_NAME = re.compile(
    r"^\s*export\s+default\s+(?P<name>[A-Za-z_$][\w$]*)\s*;?\s*$"
)

# Call expression — best effort: name( OR obj.name(
_CALL = re.compile(r"(?P<name>[A-Za-z_$][\w$]*)\s*\(")

# VIBE-102: JSX element that uses a component, e.g. <BookingForm ... />.
# The look-behind keeps generic type arguments such as Array<Slot> out.
_JSX_TAG = re.compile(r"(?<![\w.)\]])<(?P<name>[A-Z][\w$]*)(?=[\s/>])")

# End of a function signature on the declaration line: ") {" or "): Type {"
_SIGNATURE_END = re.compile(r"\)\s*(?::\s*[^={]+)?\s*\{")

# A line ending with one of these continues on the next line.
_CONTINUATION_ENDINGS = ("=>", "(", "[", "{", ",", "+", "-", "*", "/", "&", "|", "?")
_CONTINUATION_ENDINGS += (":", "=", ".")
# A line starting with one of these continues the previous line.
_CONTINUATION_STARTS = (".", "?", ":", "+", "-", "*", "/", "%", "&", "|", "^", "=", ",")

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

# A multi-line signature that has not opened its body after this many lines is
# treated as a declaration without a body.
_MAX_SIGNATURE_LINES = 60


class _OpenFunction:
    """A function whose end has not been seen yet."""

    __slots__ = ("node", "depth_before", "opened", "expression", "balance", "parens")

    def __init__(
        self, node: Node, depth_before: int, opened: bool, expression: bool
    ) -> None:
        self.node = node
        self.depth_before = depth_before
        self.opened = opened  # the block body's "{" has been seen
        self.expression = expression  # arrow function with an expression body
        self.balance = 0  # open "(" and "[" of an expression body
        self.parens = 0  # open "(" of a signature whose body has not opened


class TypeScriptParser(BaseParser):
    """Regex-based TS/JS parser. Extends BaseParser interface."""

    def supported_extensions(self) -> list[str]:
        return [".ts", ".tsx", ".js", ".jsx"]

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-103: hooks for file-level dependencies and the runtime module hash
    def module_id(self, rel_path: Path, base_module: str = "") -> str:
        return self._module_id(rel_path, base_module)

    def non_runtime_ranges(self, lines: list[str]) -> list[tuple[int, int]]:
        """Imports, re-exports and type-only declarations at the top level."""
        source = "\n".join(lines)
        ranges: list[tuple[int, int]] = []
        for pattern in (_IMPORT_STMT, _REEXPORT_STMT):
            for match in pattern.finditer(source):
                first = source.count("\n", 0, match.start()) + 1
                last = source.count("\n", 0, match.end()) + 1
                ranges.append((first, last))
        index = 0
        while index < len(lines):
            if _TYPE_DECL.match(lines[index]):
                end = self._type_declaration_end(lines, index)
                ranges.append((index + 1, end + 1))
                index = end + 1
            else:
                index += 1
        return ranges

    def _type_declaration_end(self, lines: list[str], start: int) -> int:
        """Index of the last line of the type declaration starting at ``start``."""
        balance = 0
        for index in range(start, len(lines)):
            text = self._strip_comment(lines[index]).strip()
            balance += sum(text.count(char) for char in "{([")
            balance -= sum(text.count(char) for char in "})]")
            if balance > 0:
                continue
            if text.endswith(";"):
                return index
            following = ""
            if index + 1 < len(lines):
                following = self._strip_comment(lines[index + 1]).strip()
            if text.endswith(_TYPE_CONTINUES_AFTER):
                continue
            if following.startswith(_TYPE_CONTINUES_BEFORE):
                continue
            return index
        return len(lines) - 1

    # ─────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────
    def parse_file(
        self, file_path: Path, base_module: str = "", rel_path: Path | None = None
    ) -> tuple[list[Node], list[Edge]]:
        try:
            source = file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"[WARN] TS parser: cannot read {file_path}: {exc}")
            return [], []

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # VIBE-102: ids, layer and domain come from the project-relative path
        # when the builder supplies one, so they are the same on every machine.
        id_path = rel_path if rel_path is not None else file_path
        try:
            return self._parse_source(source, id_path, base_module)
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

        # Build module path: base_module + file stem (without ext)
        rel_module = self._module_id(file_path, base_module)
        domain = self._infer_domain(file_path, base_module)
        layer = self._infer_layer(file_path)

        lines = source.splitlines()
        fdd_by_line = self._extract_fdd(lines)
        edges: list[Edge] = self._import_edges(source, rel_module, file_path)

        # State
        class_stack: list[tuple[Node, int]] = []  # [(class node, brace depth before)]
        open_funcs: list[_OpenFunction] = []  # innermost function last
        pending_decorators: list[str] = []
        default_names: set[str] = set()  # from `export default Name;`
        depth = 0  # global brace depth
        decorator_parens = 0  # open "(" of a decorator whose arguments span lines
        # `const name = (` seen, parameter list still open:
        # (name, line, brace depth before that line, open parentheses)
        pending_arrow: tuple[str, int, int, int] | None = None

        def new_node(name: str, ntype: NodeType, idx: int, parent: str = "") -> Node:
            owner = parent or rel_module
            node = self._make_node(
                nid=f"{owner}.{name}",
                name=name,
                ntype=ntype,
                layer=layer,
                domain=domain,
                file_path=str(file_path),
                line_start=idx,
                decorators=pending_decorators[:],
                fdd=self._find_fdd(fdd_by_line, idx),
                parent_class=parent,
            )
            node.metadata["module"] = rel_module
            nodes.append(node)
            pending_decorators.clear()
            return node

        def declare_function(
            name: str,
            start: int,
            depth_before: int,
            depth_after: int,
            idx: int,
            line: str,
            tail: str,
            is_arrow: bool,
            next_text: str,
        ) -> Node:
            """Add a function that starts on line ``start``.

            ``idx`` is the line where its signature ends and ``tail`` is the
            part of that line that already belongs to the body.
            """
            self._close_pending_siblings(open_funcs, depth_before, start - 1)
            fnode = new_node(name, self._classify_func(pending_decorators), start)
            # A function declared inside another one is part of it: link them,
            # so a change in a nested handler reaches the component.
            if open_funcs and open_funcs[-1].node.id != fnode.id:
                outer = open_funcs[-1].node
                fnode.metadata["nested_in"] = outer.id
                edges.append(
                    Edge(
                        source=outer.id,
                        target=fnode.id,
                        edge_type=EdgeType.CALLS,
                        metadata={"via": "nested"},
                    )
                )
            self._harvest_calls(tail, fnode.id, edges)
            self._open_function(
                open_funcs,
                fnode,
                depth_before,
                depth_after,
                idx,
                line,
                tail,
                is_arrow,
                next_text,
            )
            return fnode

        for idx, raw in enumerate(lines, start=1):
            line = self._strip_comment(raw)
            delta = line.count("{") - line.count("}")
            next_text = ""
            if idx < len(lines):
                next_text = self._strip_comment(lines[idx]).strip()

            # Arguments of a multi-line decorator, e.g. `@Component({ ... })`
            if decorator_parens > 0:
                decorator_parens += line.count("(") - line.count(")")
                depth += delta
                continue

            # Track decorators (apply to next decl)
            dec_match = _DECORATOR.match(line)
            if dec_match:
                pending_decorators.append(dec_match.group("name"))
                decorator_parens = max(line.count("(") - line.count(")"), 0)
                depth += delta
                continue

            # Imports were collected from the whole source above
            if _IMPORT_LINE.match(line):
                depth += delta
                continue

            # The parameter list of `const name = (` may close on this line;
            # an arrow after it makes the declaration a function.
            if pending_arrow is not None:
                name, start, start_depth, parens = pending_arrow
                closing = self._closing_paren(line, parens)
                if closing < 0:
                    parens += line.count("(") - line.count(")")
                    waiting = idx - start < _MAX_SIGNATURE_LINES
                    pending_arrow = (
                        (name, start, start_depth, parens) if waiting else None
                    )
                else:
                    pending_arrow = None
                    rest = line[closing + 1 :]
                    tail_match = _ARROW_TAIL.match(rest)
                    if tail_match:
                        declare_function(
                            name,
                            start,
                            start_depth,
                            depth + delta,
                            idx,
                            line,
                            rest[tail_match.end() :],
                            True,
                            next_text,
                        )
                        depth += delta
                        continue

            # Class declaration
            cls_match = _CLASS_DECL.match(line)
            if cls_match:
                self._close_pending_siblings(open_funcs, depth, idx - 1)
                cnode = new_node(
                    cls_match.group("name"),
                    self._classify_class(pending_decorators),
                    idx,
                )
                base = cls_match.group("base")
                if base:
                    edges.append(
                        Edge(
                            source=cnode.id,
                            target=base,
                            edge_type=EdgeType.INHERITS,
                        )
                    )
                # Class body opens at next `{` — assume same line for simplicity
                if "{" in line:
                    if delta > 0:
                        class_stack.append((cnode, depth))
                    else:
                        cnode.line_end = idx
                    depth += delta
                continue

            # Function declaration
            fn_match = _FUNC_DECL.match(line)
            arrow_match = None if fn_match else _ARROW_CONST.match(line)
            decl_match = fn_match or arrow_match
            if decl_match:
                pending_arrow = None
                is_arrow = arrow_match is not None
                fnode = declare_function(
                    decl_match.group("name"),
                    idx,
                    depth,
                    depth + delta,
                    idx,
                    line,
                    self._body_tail(line, is_arrow),
                    is_arrow,
                    next_text,
                )
                if fn_match and fn_match.group("default"):
                    fnode.metadata["export_default"] = True
                depth += delta
                continue

            # `const name = (` — wait for the end of the parameter list
            open_match = _ARROW_OPEN.match(line)
            if open_match:
                parens = line.count("(") - line.count(")")
                pending_arrow = None
                if parens > 0:
                    pending_arrow = (open_match.group("name"), idx, depth, parens)

            # Method inside class. Control-flow lines such as `if (x) {` also
            # match the method pattern; they are handled as ordinary lines.
            m_match = _METHOD_DECL.match(line) if class_stack else None
            mname = m_match.group("name") if m_match else ""
            if m_match and (mname not in _CALL_BLOCKLIST or mname == "constructor"):
                cls_node, _ = class_stack[-1]
                is_route = any(d in _ROUTE_DECORATORS for d in pending_decorators)
                mnode = new_node(
                    mname,
                    NodeType.ROUTE if is_route else NodeType.METHOD,
                    idx,
                    parent=cls_node.id,
                )
                tail = self._body_tail(line, is_arrow=False)
                self._harvest_calls(tail, mnode.id, edges)
                if delta > 0:
                    open_funcs.append(_OpenFunction(mnode, depth, True, False))
                else:
                    mnode.line_end = idx
                depth += delta
                self._close_finished(
                    open_funcs, class_stack, depth, idx, line, next_text
                )
                continue

            # `export default Name;` marks an already-declared function
            default_match = _EXPORT_DEFAULT_NAME.match(line)
            if default_match:
                default_names.add(default_match.group("name"))

            # Inside a function body → harvest call edges (best effort)
            if open_funcs:
                self._harvest_calls(line, open_funcs[-1].node.id, edges)

            # Brace tracking, then close whatever ended on this line
            depth += delta
            self._close_finished(open_funcs, class_stack, depth, idx, line, next_text)

            # Reset stale decorators (orphan decorator with no decl)
            if line.strip() and not _DECORATOR.match(line):
                pending_decorators.clear()

        # Anything still open runs to the end of the file; a signature whose
        # body never opened has no body.
        for open_func in open_funcs:
            has_body = open_func.opened or open_func.expression
            open_func.node.line_end = len(lines) if has_body else 0
        for cls_node, _ in class_stack:
            cls_node.line_end = len(lines)

        for node in nodes:
            node.line_end = node.line_end or node.line_start
            if node.name in default_names and not node.parent_class:
                node.metadata["export_default"] = True
        hashes = named_hashes(lines, [(n.id, n.line_start, n.line_end) for n in nodes])
        for node in nodes:
            node.metadata["body_hash"] = hashes[node.id]

        return nodes, edges

    # ─────────────────────────────────────────────────────────────────
    # Scope tracking (VIBE-102)
    # ─────────────────────────────────────────────────────────────────
    def _open_function(
        self,
        open_funcs: list[_OpenFunction],
        node: Node,
        depth_before: int,
        depth_after: int,
        idx: int,
        line: str,
        tail: str,
        is_arrow: bool,
        next_text: str,
    ) -> None:
        """Record a freshly declared function, or finish it if it ends on ``idx``."""
        stripped = line.rstrip()
        if depth_after > depth_before:
            open_funcs.append(_OpenFunction(node, depth_before, True, False))
        elif stripped.endswith(";") or ("{" in line and stripped.endswith("}")):
            node.line_end = idx
        elif is_arrow:
            balance = self._bracket_balance(tail)
            if tail.strip() and balance <= 0 and self._expression_ends(tail, next_text):
                node.line_end = idx
                return
            open_func = _OpenFunction(node, depth_before, False, True)
            open_func.balance = balance
            open_funcs.append(open_func)
        else:
            # Signature continues on the following lines
            open_func = _OpenFunction(node, depth_before, False, False)
            open_func.parens = line.count("(") - line.count(")")
            open_funcs.append(open_func)

    def _close_finished(
        self,
        open_funcs: list[_OpenFunction],
        class_stack: list[tuple[Node, int]],
        depth: int,
        idx: int,
        line: str,
        next_text: str,
    ) -> None:
        """Pop every function and class whose body ended on line ``idx``."""
        stripped = line.strip()
        while open_funcs:
            top = open_funcs[-1]
            if top.expression:
                top.balance += self._bracket_balance(line)
                if depth < top.depth_before:
                    # The block around the arrow closed: it ended the line before
                    top.node.line_end = max(idx - 1, top.node.line_start)
                elif depth > top.depth_before or top.balance > 0:
                    break
                elif not stripped:
                    top.node.line_end = max(idx - 1, top.node.line_start)
                elif self._expression_ends(stripped, next_text):
                    top.node.line_end = idx
                else:
                    break
            elif not top.opened:
                # Braces inside the parameter list are types, not the body
                top.parens += line.count("(") - line.count(")")
                if top.parens > 0:
                    break
                if depth > top.depth_before:
                    top.opened = True
                    break
                if stripped.endswith(";"):
                    top.node.line_end = idx  # a declaration without a body
                elif idx - top.node.line_start < _MAX_SIGNATURE_LINES:
                    break
                else:
                    top.node.line_end = top.node.line_start
            elif depth <= top.depth_before:
                top.node.line_end = idx
            else:
                break
            open_funcs.pop()

        while class_stack and depth <= class_stack[-1][1]:
            cls_node, _ = class_stack.pop()
            cls_node.line_end = idx

    def _close_pending_siblings(
        self, open_funcs: list[_OpenFunction], depth: int, last_line: int
    ) -> None:
        """A new declaration ends what was still pending at the same depth.

        That is an arrow function with an expression body (it ends on the line
        before), or a signature whose body never opened, such as an overload
        (it has no body, so it ends where it started).
        """
        while open_funcs and depth <= open_funcs[-1].depth_before:
            top = open_funcs[-1]
            if top.expression:
                top.node.line_end = max(last_line, top.node.line_start)
            elif not top.opened:
                top.node.line_end = top.node.line_start
            else:
                break
            open_funcs.pop()

    @staticmethod
    def _expression_ends(text: str, next_text: str) -> bool:
        """True when a bracket-balanced expression stops at the end of ``text``.

        ``next_text`` is the following line, stripped. Code written without
        semicolons relies on this: the expression goes on only if this line
        ends, or the next one starts, with an operator.
        """
        stripped = text.strip()
        if stripped.endswith(";"):
            return True
        if stripped.endswith(_CONTINUATION_ENDINGS):
            return False
        return not next_text.startswith(_CONTINUATION_STARTS)

    @staticmethod
    def _closing_paren(text: str, open_count: int) -> int:
        """Index of the ")" that closes ``open_count`` open ones, or -1."""
        for index, char in enumerate(text):
            if char == "(":
                open_count += 1
            elif char == ")":
                open_count -= 1
                if open_count == 0:
                    return index
        return -1

    @staticmethod
    def _bracket_balance(text: str) -> int:
        return text.count("(") + text.count("[") - text.count(")") - text.count("]")

    @staticmethod
    def _body_tail(line: str, is_arrow: bool) -> str:
        """Return the part of a declaration line that belongs to the body."""
        if is_arrow:
            return line.partition("=>")[2]
        match = _SIGNATURE_END.search(line)
        return line[match.end() :] if match else ""

    @staticmethod
    def _harvest_calls(text: str, caller_id: str, edges: list[Edge]) -> None:
        """Add a CALLS edge for every call and JSX component found in ``text``."""
        for call in _CALL.finditer(text):
            cname = call.group("name")
            if cname in _CALL_BLOCKLIST:
                continue
            edges.append(Edge(source=caller_id, target=cname, edge_type=EdgeType.CALLS))
        for tag in _JSX_TAG.finditer(text):
            edges.append(
                Edge(
                    source=caller_id,
                    target=tag.group("name"),
                    edge_type=EdgeType.CALLS,
                    metadata={"via": "jsx"},
                )
            )

    # ─────────────────────────────────────────────────────────────────
    # Imports (VIBE-102)
    # ─────────────────────────────────────────────────────────────────
    def _import_edges(
        self, source: str, rel_module: str, file_path: Path
    ) -> list[Edge]:
        """One IMPORTS edge per import or re-export statement.

        ``metadata["names"]`` maps each local name to the name it has in the
        imported module ("default" for a default import, "*" for a namespace),
        which lets the builder resolve calls to the function they refer to.
        ``metadata["file"]`` is the importing file. A statement that brings in
        types only is marked ``type_only``; a re-export is marked ``reexport``
        (and ``star`` for ``export * from``).
        """
        importer = file_path.as_posix()
        edges: list[Edge] = []
        for match in _IMPORT_STMT.finditer(source):
            src = match.group("src") or match.group("bare")
            edge = Edge(source=rel_module, target=src, edge_type=EdgeType.IMPORTS)
            edge.metadata["file"] = importer
            if match.group("src"):
                names: dict[str, str] = {}
                if not match.group("type"):
                    names = self._import_names(match.group("clause") or "")
                if names:
                    edge.metadata["names"] = names
                else:
                    edge.metadata["type_only"] = True
            edges.append(edge)
        for match in _REEXPORT_STMT.finditer(source):
            edge = Edge(
                source=rel_module,
                target=match.group("src"),
                edge_type=EdgeType.IMPORTS,
                metadata={"file": importer, "reexport": True},
            )
            clause = match.group("clause")
            if match.group("type"):
                edge.metadata["type_only"] = True
            elif clause.startswith("*"):
                if " as " not in clause:
                    edge.metadata["star"] = True
            else:
                names = self._import_names(clause)
                if names:
                    edge.metadata["names"] = names
                else:
                    edge.metadata["type_only"] = True
            edges.append(edge)
        return edges

    @staticmethod
    def _import_names(clause: str) -> dict[str, str]:
        """Parse `Default, { a, b as c }` into {local name: exported name}."""
        names: dict[str, str] = {}
        outside = clause
        braces = re.search(r"\{(.*?)\}", clause, re.DOTALL)
        if braces:
            outside = clause[: braces.start()] + clause[braces.end() :]
            for part in braces.group(1).split(","):
                part = part.strip()
                if not part or part.startswith("type "):
                    continue
                exported, _, local = part.partition(" as ")
                names[(local or exported).strip()] = exported.strip()
        for part in outside.split(","):
            part = part.strip()
            if part.startswith("*"):
                alias = part.partition(" as ")[2].strip()
                if alias:
                    names[alias] = "*"
            elif part and _IDENTIFIER.fullmatch(part):
                names[part] = "default"
        return names

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

    # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-02)
    def _infer_layer(self, file_path: Path) -> LayerType:
        """Infer layer for a TS/JS file.

        POST-CM-S3-02: broadened to handle React frontend conventions so
        that typical page/component/hook files no longer fall through to
        UNKNOWN. HC baseline had 171/173 unknowns from React code — this
        maps them to the closest existing layer.
        """
        s = file_path.as_posix().lower()
        # VIBE-102: the rules below look for "/folder/". A project-relative
        # path gets a leading slash so a top-level folder matches as well.
        if not s.startswith("/"):
            s = f"/{s}"
        fname = s.rsplit("/", 1)[-1]

        # Tests first (most specific)
        if (
            "/test" in s
            or "/__tests__" in s
            or s.endswith(".test.ts")
            or s.endswith(".test.tsx")
            or s.endswith(".spec.ts")
            or s.endswith(".spec.tsx")
        ):
            return LayerType.TEST

        # Router: NestJS/Express controllers + React pages (UI routing)
        if (
            "controller" in fname
            or "/routes" in s
            or "/router" in s
            or "/pages/" in s
            or fname.endswith("page.tsx")
            or fname.endswith("page.jsx")
            or fname.endswith("page.ts")
            or fname.endswith("route.ts")
            or fname.endswith("route.tsx")
        ):
            return LayerType.ROUTER

        # Repository
        if "repository" in fname or "/repositories/" in s or "/repo/" in s:
            return LayerType.REPOSITORY

        # Schema — Zod / DTO / validation
        if (
            "schema" in fname
            or "/schemas/" in s
            or "/dto/" in s
            or fname.endswith(".dto.ts")
        ):
            return LayerType.SCHEMA

        # Model / entity — ORM layer
        if (
            "/models/" in s
            or "/entities/" in s
            or fname == "model.ts"
            or fname == "models.ts"
            or fname.endswith(".entity.ts")
            or fname.endswith(".model.ts")
        ):
            return LayerType.MODEL

        # Worker — background jobs / queues
        if (
            "/workers/" in s
            or "/jobs/" in s
            or "/queue" in s
            or fname.endswith(".worker.ts")
            or fname.endswith(".job.ts")
        ):
            return LayerType.WORKER

        # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POLISH-01)
        # Service: business logic, API clients, state stores, hooks.
        # Explicit parentheses around the "useXxx" hook rule to keep
        # `and`/`or` precedence unambiguous (flagged in PR #38 review).
        if (
            "service" in fname
            or "/services/" in s
            or "/api/" in s
            or "/hooks/" in s
            or (
                fname.startswith("use")
                and (fname.endswith(".ts") or fname.endswith(".tsx"))
            )
            or "/store/" in s
            or "/stores/" in s
            or fname.endswith(".slice.ts")
            or fname.endswith(".client.ts")
            or fname == "client.ts"
        ):
            return LayerType.SERVICE

        # Util: shared UI components, helpers, modals, dialogs, utils
        if (
            "util" in s
            or "helper" in s
            or "/components/" in s
            or "/shared/" in s
            or "/widgets/" in s
            or "/common/" in s
            or fname.endswith("modal.tsx")
            or fname.endswith("dialog.tsx")
            or fname.endswith("drawer.tsx")
            or fname.endswith("dashboard.tsx")
        ):
            return LayerType.UTIL

        # Core
        if "/core/" in s or "/config" in s or "/constants" in s:
            return LayerType.CORE

        # Fallback: React .tsx/.jsx files → UTIL (UI component),
        # plain .ts/.js → SERVICE (business logic default).
        # Better than UNKNOWN; keeps graph actionable.
        if fname.endswith(".tsx") or fname.endswith(".jsx"):
            return LayerType.UTIL
        if fname.endswith(".ts") or fname.endswith(".js"):
            return LayerType.SERVICE

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
