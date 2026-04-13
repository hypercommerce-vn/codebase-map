# HC-AI | ticket: MEM-M2-08
"""Codebase vertical MCP tools — 4 tools registered via @register_tool.

Design ref: kmp-M2-design.html Screen F-G (MCP server + tool execution).
Auto-discovered when server imports this module.

Tools:
1. find_function — search vault by function name
2. explain_module — describe module structure
3. pattern_check — validate code against learned patterns
4. impact — analyze change impact via call graph
"""

from __future__ import annotations

import logging
from typing import Any

from knowledge_memory.core.mcp.registry import register_tool
from knowledge_memory.core.mcp.tool_base import BaseMCPTool, ToolInput, ToolResult

logger = logging.getLogger("codebase-memory.mcp.tools")

# HC-AI | ticket: MEM-M2-08
# Module-level vault reference — set by server before serving
_vault = None
_graph_nodes: list[dict[str, Any]] = []
_graph_edges: list[dict[str, str]] = []
_patterns: list[Any] = []


def configure_tools(
    vault: Any = None,
    nodes: list[dict[str, Any]] | None = None,
    edges: list[dict[str, str]] | None = None,
    patterns: list[Any] | None = None,
) -> None:
    """Configure tool data sources. Called by server before serving."""
    global _vault, _graph_nodes, _graph_edges, _patterns
    _vault = vault
    _graph_nodes = nodes or []
    _graph_edges = edges or []
    _patterns = patterns or []


@register_tool("find_function")
class FindFunctionTool(BaseMCPTool):
    """Search codebase vault by function name."""

    description = "Find a Python function by name in the codebase vault"
    input_schema = [
        ToolInput(
            name="name",
            type="string",
            description="Function name to search (exact or partial match)",
        ),
    ]

    def execute(self, **kwargs: Any) -> ToolResult:
        name = kwargs.get("name", "")
        if not name:
            return ToolResult.failure("Parameter 'name' is required")

        lower = name.lower()
        matches = []

        for node in _graph_nodes:
            node_name = node.get("name", "")
            if lower in node_name.lower():
                matches.append(node)

        if not matches:
            # Fuzzy suggestions
            all_names = [n.get("name", "") for n in _graph_nodes[:20]]
            return ToolResult.failure(
                f"Function '{name}' not found. "
                f"Did you mean: {', '.join(all_names[:5])}?"
            )

        results = []
        for m in matches[:10]:
            # Find callers/callees
            node_name = m.get("name", "")
            callers = [
                e["source_name"]
                for e in _graph_edges
                if e.get("target_name") == node_name
            ]
            callees = [
                e["target_name"]
                for e in _graph_edges
                if e.get("source_name") == node_name
            ]

            results.append(
                {
                    "name": node_name,
                    "file": f"{m.get('file_path', '')}:{m.get('line_start', 0)}",
                    "type": m.get("node_type", "function"),
                    "layer": m.get("layer", "unknown"),
                    "callers": len(callers),
                    "callees": len(callees),
                    "callers_list": callers[:5],
                    "callees_list": callees[:5],
                }
            )

        if len(results) == 1:
            return ToolResult.success(results[0])
        return ToolResult.success({"matches": results, "count": len(results)})


@register_tool("explain_module")
class ExplainModuleTool(BaseMCPTool):
    """Generate explanation for a module/file."""

    description = "Explain the structure and purpose of a module in the codebase"
    input_schema = [
        ToolInput(
            name="module",
            type="string",
            description="Module path (e.g., 'auth/service.py' or 'auth')",
        ),
    ]

    def execute(self, **kwargs: Any) -> ToolResult:
        module = kwargs.get("module", "")
        if not module:
            return ToolResult.failure("Parameter 'module' is required")

        # Find nodes in this module
        lower = module.lower()
        nodes_in_module = [
            n for n in _graph_nodes if lower in n.get("file_path", "").lower()
        ]

        if not nodes_in_module:
            return ToolResult.failure(f"Module '{module}' not found in vault")

        # Analyze structure
        layers: dict[str, int] = {}
        types: dict[str, int] = {}
        for n in nodes_in_module:
            layer = n.get("layer", "unknown")
            ntype = n.get("node_type", "function")
            layers[layer] = layers.get(layer, 0) + 1
            types[ntype] = types.get(ntype, 0) + 1

        # Count external dependencies
        module_names = {n.get("name", "") for n in nodes_in_module}
        external_callers = set()
        external_callees = set()
        for e in _graph_edges:
            src = e.get("source_name", "")
            tgt = e.get("target_name", "")
            if src in module_names and tgt not in module_names:
                external_callees.add(tgt)
            if tgt in module_names and src not in module_names:
                external_callers.add(src)

        files = sorted({n.get("file_path", "") for n in nodes_in_module})

        return ToolResult.success(
            {
                "module": module,
                "files": files,
                "total_functions": len(nodes_in_module),
                "layers": layers,
                "types": types,
                "external_callers": len(external_callers),
                "external_callees": len(external_callees),
                "top_functions": [n.get("name", "") for n in nodes_in_module[:10]],
            }
        )


@register_tool("pattern_check")
class PatternCheckTool(BaseMCPTool):
    """Validate code against learned patterns."""

    description = "Check if a function follows codebase naming and layer patterns"
    input_schema = [
        ToolInput(
            name="function",
            type="string",
            description="Function name to check",
        ),
        ToolInput(
            name="file",
            type="string",
            description="File path of the function",
            required=False,
        ),
    ]

    def execute(self, **kwargs: Any) -> ToolResult:
        function = kwargs.get("function", "")
        file_path = kwargs.get("file", "")
        if not function:
            return ToolResult.failure("Parameter 'function' is required")

        violations: list[dict[str, str]] = []
        passes: list[dict[str, str]] = []

        # Check naming convention (snake_case)
        import re

        if re.match(r"^[a-z][a-z0-9_]*$", function):
            passes.append(
                {
                    "check": "naming",
                    "status": "pass",
                    "detail": f"'{function}' follows snake_case convention",
                }
            )
        else:
            # Detect what convention it uses
            if re.match(r"^[a-z].*[A-Z]", function):
                expected = re.sub(r"([A-Z])", r"_\1", function).lower()
                violations.append(
                    {
                        "check": "naming",
                        "status": "fail",
                        "detail": f"camelCase detected. Expected: {expected}",
                        "severity": "medium",
                    }
                )
            elif re.match(r"^[A-Z]", function):
                passes.append(
                    {
                        "check": "naming",
                        "status": "pass",
                        "detail": f"'{function}' is PascalCase (class name OK)",
                    }
                )
            else:
                violations.append(
                    {
                        "check": "naming",
                        "status": "fail",
                        "detail": f"Non-standard naming: '{function}'",
                        "severity": "low",
                    }
                )

        # Check layer placement (if file path given)
        if file_path:
            layer = self._detect_layer(file_path)
            prefix = function.split("_")[0] if "_" in function else ""
            if layer == "route" and prefix not in (
                "get",
                "post",
                "put",
                "delete",
                "patch",
                "list",
            ):
                violations.append(
                    {
                        "check": "layer_convention",
                        "status": "warn",
                        "detail": (
                            f"Route function '{function}' doesn't start with "
                            "HTTP verb prefix (get/post/put/delete)"
                        ),
                        "severity": "low",
                    }
                )
            else:
                passes.append(
                    {
                        "check": "layer_convention",
                        "status": "pass",
                        "detail": f"Layer '{layer}' convention OK",
                    }
                )

        total_checks = len(violations) + len(passes)
        return ToolResult.success(
            {
                "function": function,
                "file": file_path,
                "violations": violations,
                "passes": passes,
                "compliance": f"{len(passes)}/{total_checks} checks passed",
            }
        )

    @staticmethod
    def _detect_layer(file_path: str) -> str:
        """Detect layer from file path."""
        lower = file_path.lower()
        if "router" in lower or "route" in lower or "api" in lower:
            return "route"
        if "service" in lower:
            return "service"
        if "model" in lower:
            return "model"
        if "test" in lower:
            return "test"
        return "util"


@register_tool("impact")
class ImpactTool(BaseMCPTool):
    """Analyze change impact via call graph."""

    description = "Analyze the impact of modifying a function using the call graph"
    input_schema = [
        ToolInput(
            name="function",
            type="string",
            description="Function name to analyze impact for",
        ),
        ToolInput(
            name="depth",
            type="integer",
            description="Caller traversal depth (1-3, default 1)",
            required=False,
        ),
    ]

    def execute(self, **kwargs: Any) -> ToolResult:
        function = kwargs.get("function", "")
        depth = int(kwargs.get("depth", 1))
        if not function:
            return ToolResult.failure("Parameter 'function' is required")

        from knowledge_memory.verticals.codebase.impact import ImpactEngine

        engine = ImpactEngine()
        engine.load_graph(_graph_nodes, _graph_edges)
        result = engine.analyze(function, depth=min(max(depth, 1), 3))

        if result.error:
            return ToolResult.failure(result.error)

        return ToolResult.success(
            {
                "function": result.function_name,
                "file": result.file_path,
                "layer": result.layer,
                "domain": result.domain,
                "direct_callers": [
                    {
                        "name": c.name,
                        "file": c.file_path,
                        "risk": c.risk,
                    }
                    for c in result.direct_callers
                ],
                "transitive_callers": len(result.transitive_callers),
                "risk_level": result.risk_level,
                "recommendation": result.recommendation,
            }
        )
