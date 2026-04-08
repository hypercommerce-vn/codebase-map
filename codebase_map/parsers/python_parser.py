# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Python AST Parser.

Extracts functions, classes, methods, imports, decorators.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from codebase_map.graph.models import Edge, EdgeType, LayerType, Node, NodeType
from codebase_map.parsers.base import BaseParser

# HC-AI | ticket: FDD-TOOL-CODEMAP
# CM-S2-08: FDD spec linking — parse `# FDD: FDD-XXX-NNN` or `# ticket: FDD-XXX-NNN`
_FDD_PATTERN = re.compile(
    r"#[^\n]*?(?:FDD|ticket)\s*:\s*(FDD-[A-Z]+-[A-Z0-9]+)", re.IGNORECASE
)


def _extract_fdd_annotations(source: str) -> dict[int, str]:
    """Scan source for FDD comment annotations. Returns {line_no: fdd_id}."""
    result: dict[int, str] = {}
    for idx, line in enumerate(source.splitlines(), start=1):
        match = _FDD_PATTERN.search(line)
        if match:
            result[idx] = match.group(1).upper()
    return result


def _find_fdd_for_node(fdd_by_line: dict[int, str], line_start: int) -> str:
    """Find nearest FDD annotation within 5 lines above (or on) the def line."""
    for offset in range(0, 6):
        candidate = fdd_by_line.get(line_start - offset)
        if candidate:
            return candidate
    return ""


# HC-AI | ticket: FDD-TOOL-CODEMAP
# CM-S3-04: Business flow tagging — parse `# flow: name1, name2` comments
_FLOW_PATTERN = re.compile(r"#[^\n]*?flow\s*:\s*([A-Za-z0-9_,\-\s]+)", re.IGNORECASE)


def _extract_flow_annotations(source: str) -> dict[int, list[str]]:
    """Scan source for `# flow: name` comments. Returns {line_no: [flows]}."""
    result: dict[int, list[str]] = {}
    for idx, line in enumerate(source.splitlines(), start=1):
        m = _FLOW_PATTERN.search(line)
        if m:
            flows = [f.strip() for f in m.group(1).split(",") if f.strip()]
            if flows:
                result[idx] = flows
    return result


def _find_flows_for_node(
    flows_by_line: dict[int, list[str]], line_start: int
) -> list[str]:
    """Find nearest flow annotation within 5 lines above (or on) the def line."""
    for offset in range(0, 6):
        cand = flows_by_line.get(line_start - offset)
        if cand:
            return cand
    return []


def _get_docstring(node: ast.AST) -> str:
    """Extract docstring from a function/class/module node."""
    try:
        return ast.get_docstring(node) or ""
    except Exception:
        return ""


def _get_decorator_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
) -> list[str]:
    """Extract decorator names as strings."""
    names: list[str] = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            names.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.append(ast.unparse(dec))
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                names.append(dec.func.id)
            elif isinstance(dec.func, ast.Attribute):
                names.append(ast.unparse(dec.func))
            else:
                names.append(ast.unparse(dec))
        else:
            names.append(ast.unparse(dec))
    return names


def _get_params(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Extract parameter names (skip self/cls)."""
    params: list[str] = []
    for arg in node.args.args:
        if arg.arg not in ("self", "cls"):
            annotation = ""
            if arg.annotation:
                annotation = f": {ast.unparse(arg.annotation)}"
            params.append(f"{arg.arg}{annotation}")
    return params


def _get_return_type(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Extract return type annotation."""
    if node.returns:
        return ast.unparse(node.returns)
    return ""


# HC-AI | ticket: FDD-TOOL-CODEMAP
def _detect_layer(file_path: str) -> LayerType:
    """Detect architecture layer from file path."""
    path_lower = file_path.lower()
    fname = path_lower.rsplit("/", 1)[-1] if "/" in path_lower else path_lower

    # Router layer
    if "router.py" in fname or "/router" in path_lower:
        return LayerType.ROUTER

    # Service layer (includes client, provider — service-like)
    if "service.py" in fname or "/service" in path_lower:
        return LayerType.SERVICE
    if fname in ("client.py", "provider.py"):
        return LayerType.SERVICE

    # Repository layer
    if "repository.py" in fname or "/repository" in path_lower:
        return LayerType.REPOSITORY

    # Schema layer (Pydantic models, request/response)
    if "schemas.py" in fname or "schema.py" in fname:
        return LayerType.SCHEMA

    # Model layer (SQLAlchemy ORM)
    # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-02)
    # Added plural "models.py" to catch HC zns/models.py and similar.
    if "/models/" in path_lower or fname in ("model.py", "models.py"):
        return LayerType.MODEL

    # Test layer
    if fname.startswith("test_") or fname == "conftest.py":
        return LayerType.TEST
    if "/tests/" in path_lower:
        return LayerType.TEST

    # Core layer
    if "/core/" in path_lower:
        return LayerType.CORE

    # Worker layer (Celery tasks)
    if "/workers/" in path_lower or "tasks.py" in fname:
        return LayerType.WORKER

    # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-02)
    # Service-like directories: AI agents, adapters, integrations, clients.
    if (
        "/agent/" in path_lower
        or "/agents/" in path_lower
        or "/adapters/" in path_lower
        or "/integrations/" in path_lower
        or "/clients/" in path_lower
        or "/handlers/" in path_lower
    ):
        return LayerType.SERVICE

    # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-02)
    # Router-like directories beyond router.py naming.
    if (
        "/endpoints/" in path_lower
        or "/webhooks/" in path_lower
        or "/api/" in path_lower
    ):
        return LayerType.ROUTER

    # Util layer — broad catch for helper/utility patterns
    _util_patterns = (
        "utils",
        "helpers",
        "mapper",
        "normalizer",
        "processor",
        "analyzer",
        "pipeline",
        "matcher",
        "builder",
        "engine",
        "resolver",
        "extractor",
        "evaluator",
        "recommendation",
        "context_manager",
        "template_engine",
        "stream_processor",
        "trigger_engine",
        "plan_gating",
        "sepay_webhook",
        "tools",
    )
    for pattern in _util_patterns:
        if pattern in fname or pattern in path_lower:
            return LayerType.UTIL

    # Main entry point
    if fname == "main.py" or fname == "__init__.py":
        return LayerType.UTIL

    # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-02)
    # Additional common Python conventions.
    if (
        "/parsers/" in path_lower
        or "parser.py" in fname
        or "/graph/" in path_lower
        or "/exporters/" in path_lower
        or "exporter.py" in fname
        or "/commands/" in path_lower
        or "/queries/" in path_lower
        or "/dto/" in path_lower
        or "/middleware" in path_lower
        or "/validators/" in path_lower
        or "/licensing/" in path_lower
    ):
        return LayerType.UTIL
    if (
        "/cli" in path_lower
        or fname == "cli.py"
        or fname == "__main__.py"
        or fname == "config.py"
        or "/dependencies/" in path_lower
        or "/config/" in path_lower
    ):
        return LayerType.CORE
    if (
        "/exceptions/" in path_lower
        or "exceptions.py" in fname
        or "errors.py" in fname
        or "/events/" in path_lower
        or "/entities/" in path_lower
        or "/domain/" in path_lower
        or "constants.py" in fname
        or "enums.py" in fname
    ):
        return LayerType.CORE

    # Last-resort fallback: any .py file → UTIL rather than UNKNOWN.
    # Keeps the graph actionable; refine with more specific rules above.
    if fname.endswith(".py"):
        return LayerType.UTIL

    return LayerType.UNKNOWN


def _detect_domain(file_path: str) -> str:
    """Detect module domain from file path."""
    domains = [
        "crm",
        "cdp",
        "ecommerce",
        "private_traffic",
        "auth",
        "admin",
        "billing",
    ]
    path_lower = file_path.lower()
    for domain in domains:
        if f"/{domain}/" in path_lower or f"/{domain}\\" in path_lower:
            return domain
    if "/core/" in path_lower:
        return "core"
    if "/workers/" in path_lower:
        return "worker"
    if "/models/" in path_lower:
        return "model"
    return "other"


def _file_to_module_id(file_path: str, base_module: str = "") -> str:
    """Convert file path to Python module-style ID.

    e.g. backend/app/modules/crm/customers/service.py
         -> app.modules.crm.customers.service
    """
    # Remove .py extension
    module_path = file_path.replace(".py", "").replace("/", ".").replace("\\", ".")

    # If base_module specified, trim path up to and including the base
    if base_module:
        idx = module_path.find(base_module)
        if idx >= 0:
            module_path = module_path[idx:]

    # Clean up leading dots
    return module_path.strip(".")


class PythonParser(BaseParser):
    """Parse Python source files using AST."""

    def supported_extensions(self) -> list[str]:
        return [".py"]

    def parse_file(
        self, file_path: Path, base_module: str = ""
    ) -> tuple[list[Node], list[Edge]]:
        """Parse a single Python file into nodes and edges."""
        nodes: list[Node] = []
        edges: list[Edge] = []

        try:
            source = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            return nodes, edges

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            return nodes, edges

        file_str = str(file_path)
        module_id = _file_to_module_id(file_str, base_module)
        layer = _detect_layer(file_str)
        domain = _detect_domain(file_str)

        # Collect import targets for edge resolution
        import_map: dict[str, str] = {}  # alias -> full module path

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[-1]
                    import_map[name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    name = alias.asname or alias.name
                    import_map[name] = f"{mod}.{alias.name}" if mod else alias.name

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S2-06: Extract __init__ type hints for attribute chain resolution
        init_type_maps: dict[str, dict[str, str]] = {}
        for item in ast.iter_child_nodes(tree):
            if isinstance(item, ast.ClassDef):
                class_id = f"{module_id}.{item.name}"
                attr_types = self._extract_init_type_hints(item, import_map)
                if attr_types:
                    init_type_maps[class_id] = attr_types

        # Parse top-level items
        for item in ast.iter_child_nodes(tree):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_node = self._parse_function(
                    item, module_id, file_str, layer, domain
                )
                nodes.append(func_node)
                # Parse function body for calls
                func_edges = self._extract_call_edges(
                    item, func_node.id, import_map, module_id
                )
                edges.extend(func_edges)

            elif isinstance(item, ast.ClassDef):
                class_node, method_nodes, class_edges = self._parse_class(
                    item, module_id, file_str, layer, domain, import_map
                )
                nodes.append(class_node)
                nodes.extend(method_nodes)
                edges.extend(class_edges)

                # Inheritance edges
                for base in item.bases:
                    base_name = ast.unparse(base)
                    if base_name in import_map:
                        edges.append(
                            Edge(
                                source=class_node.id,
                                target=import_map[base_name],
                                edge_type=EdgeType.INHERITS,
                            )
                        )

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S2-06: Resolve self.attr.method() chains using __init__ type hints
        self._resolve_attribute_chains(edges, init_type_maps, import_map)

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S2-08: Extract FDD spec annotations from comments
        fdd_by_line = _extract_fdd_annotations(source)
        if fdd_by_line:
            for node_obj in nodes:
                fdd_id = _find_fdd_for_node(fdd_by_line, node_obj.line_start)
                if fdd_id:
                    node_obj.metadata["fdd"] = fdd_id

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S3-04: Business flow comment annotations
        flows_by_line = _extract_flow_annotations(source)
        if flows_by_line:
            for node_obj in nodes:
                flows = _find_flows_for_node(flows_by_line, node_obj.line_start)
                if flows:
                    existing = node_obj.metadata.get("flows", [])
                    node_obj.metadata["flows"] = sorted(set(existing) | set(flows))

        # Import edges (module-level)
        for alias_name, full_path in import_map.items():
            edges.append(
                Edge(
                    source=module_id,
                    target=full_path,
                    edge_type=EdgeType.IMPORTS,
                )
            )

        return nodes, edges

    def _parse_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_id: str,
        file_path: str,
        layer: LayerType,
        domain: str,
    ) -> Node:
        """Parse a top-level function."""
        func_id = f"{module_id}.{node.name}"
        decorators = _get_decorator_names(node)

        # Detect special types
        node_type = NodeType.FUNCTION
        metadata: dict = {}

        # FastAPI route detection
        route_decorators = {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
        }
        for dec_name in decorators:
            # router.get, router.post, etc.
            parts = dec_name.lower().split(".")
            if any(p in route_decorators for p in parts):
                node_type = NodeType.ROUTE
                metadata["http_method"] = next(
                    (p.upper() for p in parts if p in route_decorators), ""
                )
                # Extract path from decorator
                break

        # Celery task detection
        if any("task" in d.lower() or "shared_task" in d.lower() for d in decorators):
            node_type = NodeType.CELERY_TASK

        return Node(
            id=func_id,
            name=node.name,
            node_type=node_type,
            layer=layer,
            module_domain=domain,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=_get_docstring(node),
            decorators=decorators,
            params=_get_params(node),
            return_type=_get_return_type(node),
            metadata=metadata,
        )

    def _parse_class(
        self,
        node: ast.ClassDef,
        module_id: str,
        file_path: str,
        layer: LayerType,
        domain: str,
        import_map: dict[str, str],
    ) -> tuple[Node, list[Node], list[Edge]]:
        """Parse a class and its methods."""
        class_id = f"{module_id}.{node.name}"
        decorators = _get_decorator_names(node)

        # Detect if it's a model
        node_type = NodeType.CLASS
        bases = [ast.unparse(b) for b in node.bases]
        model_bases = {"TenantBase", "Base", "BaseModel", "SQLModel"}
        if any(b in model_bases for b in bases):
            node_type = NodeType.MODEL

        class_node = Node(
            id=class_id,
            name=node.name,
            node_type=node_type,
            layer=layer,
            module_domain=domain,
            file_path=file_path,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=_get_docstring(node),
            decorators=decorators,
        )

        method_nodes: list[Node] = []
        edges: list[Edge] = []

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip dunder methods except __init__
                if item.name.startswith("__") and item.name != "__init__":
                    continue

                method_id = f"{class_id}.{item.name}"
                method_decorators = _get_decorator_names(item)

                method_node = Node(
                    id=method_id,
                    name=item.name,
                    node_type=NodeType.METHOD,
                    layer=layer,
                    module_domain=domain,
                    file_path=file_path,
                    line_start=item.lineno,
                    line_end=item.end_lineno or item.lineno,
                    docstring=_get_docstring(item),
                    decorators=method_decorators,
                    params=_get_params(item),
                    return_type=_get_return_type(item),
                    parent_class=class_id,
                )
                method_nodes.append(method_node)

                # Extract calls inside this method
                method_edges = self._extract_call_edges(
                    item, method_id, import_map, module_id
                )
                edges.extend(method_edges)

        return class_node, method_nodes, edges

    def _extract_call_edges(
        self,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        caller_id: str,
        import_map: dict[str, str],
        module_id: str,
    ) -> list[Edge]:
        """Extract function/method calls from a function body."""
        edges: list[Edge] = []
        seen: set[str] = set()

        for node in ast.walk(func_node):
            if not isinstance(node, ast.Call):
                continue

            target: str = ""

            if isinstance(node.func, ast.Name):
                # Direct call: some_function()
                name = node.func.id
                target = import_map.get(name, f"{module_id}.{name}")

            elif isinstance(node.func, ast.Attribute):
                # Attribute call: self.repo.list(), service.create()
                full = ast.unparse(node.func)
                parts = full.split(".")

                # self.method() -> resolve within class
                if parts[0] == "self" and len(parts) >= 2:
                    # Record method — resolved later
                    target = f"self.{'.'.join(parts[1:])}"
                else:
                    # obj.method() — try to resolve obj via imports
                    obj_name = parts[0]
                    if obj_name in import_map:
                        target = f"{import_map[obj_name]}.{'.'.join(parts[1:])}"
                    else:
                        target = full

            if target and target not in seen:
                seen.add(target)
                edge_type = EdgeType.CALLS
                # Detect instantiation: ClassName()
                if isinstance(node.func, ast.Name) and node.func.id[0].isupper():
                    edge_type = EdgeType.INSTANTIATES

                edges.append(Edge(source=caller_id, target=target, edge_type=edge_type))

        return edges

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-06: Extract __init__ type hints to build self.attr -> Type mapping
    def _extract_init_type_hints(
        self,
        class_node: ast.ClassDef,
        import_map: dict[str, str],
    ) -> dict[str, str]:
        """Extract type hints from __init__ to map self.attr -> resolved type.

        Parses patterns like:
            def __init__(self, repo: CustomerRepository):
                self.repo = repo
        Returns: {"repo": "app.modules.crm.repository.CustomerRepository"}
        """
        attr_types: dict[str, str] = {}

        # Find __init__ method
        init_method = None
        for item in class_node.body:
            if (
                isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name == "__init__"
            ):
                init_method = item
                break

        if not init_method:
            return attr_types

        # Step 1: Build param -> type annotation map from __init__ args
        param_types: dict[str, str] = {}
        for arg in init_method.args.args:
            if arg.arg == "self" or not arg.annotation:
                continue
            type_str = ast.unparse(arg.annotation)
            # Strip Optional[] wrapper
            if type_str.startswith("Optional[") and type_str.endswith("]"):
                type_str = type_str[9:-1]
            # Strip | None union
            if " | None" in type_str:
                type_str = type_str.replace(" | None", "")
            param_types[arg.arg] = type_str

        # Step 2: Find self.attr = param assignments in __init__ body
        for stmt in ast.walk(init_method):
            if not isinstance(stmt, ast.Assign):
                continue
            # Check for self.attr = value pattern
            for target in stmt.targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    attr_name = target.attr
                    # Check if value is a parameter with a known type
                    if isinstance(stmt.value, ast.Name):
                        param_name = stmt.value.id
                        if param_name in param_types:
                            type_name = param_types[param_name]
                            # Resolve type via import_map
                            if type_name in import_map:
                                attr_types[attr_name] = import_map[type_name]
                            else:
                                attr_types[attr_name] = type_name

        # Step 3: Also check class-level type annotations
        for stmt in class_node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                attr_name = stmt.target.id
                if attr_name not in attr_types and stmt.annotation:
                    type_str = ast.unparse(stmt.annotation)
                    if type_str.startswith("Optional[") and type_str.endswith("]"):
                        type_str = type_str[9:-1]
                    if " | None" in type_str:
                        type_str = type_str.replace(" | None", "")
                    if type_str in import_map:
                        attr_types[attr_name] = import_map[type_str]
                    else:
                        attr_types[attr_name] = type_str

        return attr_types

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-06: Resolve self.attr.method() chains using __init__ type hints
    def _resolve_attribute_chains(
        self,
        edges: list[Edge],
        init_type_maps: dict[str, dict[str, str]],
        import_map: dict[str, str],
    ) -> None:
        """Resolve self.attr.method() edges to actual class.method targets.

        Example: self.repo.list() in CustomerService
        → Lookup init_type_maps["CustomerService"]["repo"]
          = "app.modules.crm.repository.CustomerRepository"
        → Resolve to "app.modules.crm.repository.CustomerRepository.list"
        """
        for edge in edges:
            if not edge.target.startswith("self."):
                continue

            parts = edge.target.split(".")
            # self.method() — only 2 parts, handled by builder._resolve_self_references
            if len(parts) <= 2:
                continue

            # self.attr.method() — 3+ parts, need __init__ type resolution
            attr_name = parts[1]
            method_chain = ".".join(parts[2:])

            # Find which class this caller belongs to
            caller_class = self._find_caller_class(edge.source)
            if not caller_class:
                continue

            # Look up attr type from __init__ hints
            type_map = init_type_maps.get(caller_class, {})
            if attr_name not in type_map:
                continue

            resolved_type = type_map[attr_name]
            resolved_target = f"{resolved_type}.{method_chain}"

            # Update edge with resolved target
            edge.target = resolved_target
            edge.metadata["resolved_from"] = f"self.{attr_name}.{method_chain}"
            edge.metadata["resolved_via"] = "init_type_hint"

    @staticmethod
    def _find_caller_class(caller_id: str) -> str:
        """Extract the parent class ID from a method's fully qualified ID.

        e.g. "app.modules.crm.service.CustomerService.create"
        → "app.modules.crm.service.CustomerService"
        """
        parts = caller_id.rsplit(".", 1)
        if len(parts) < 2:
            return ""
        # The parent should be a class (starts with uppercase)
        parent = parts[0]
        class_name = parent.rsplit(".", 1)[-1]
        if class_name and class_name[0].isupper():
            return parent
        return ""
