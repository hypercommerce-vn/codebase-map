# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP tool: ``cbm_impact`` — transitive blast radius of a node."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from mcp_server import server as _server
from mcp_server.graph_cache import CACHE, DEFAULT_GRAPH_FILE

DEFAULT_DEPTH = 3
MIN_DEPTH = 1
MAX_DEPTH = 5


TOOL = types.Tool(
    name="cbm_impact",
    description=(
        "Show all nodes affected (transitively) if this function/class "
        "changes. Use before a refactor to size the blast radius. User asks: "
        "'what breaks if I change X', 'blast radius of X', 'is it safe to "
        "delete X'."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Function or class name. Exact match preferred; falls "
                    "back to fuzzy search."
                ),
            },
            "graph_file": {
                "type": "string",
                "default": DEFAULT_GRAPH_FILE,
                "description": "Path to Codebase Map graph.json",
            },
            "depth": {
                "type": "integer",
                "default": DEFAULT_DEPTH,
                "minimum": MIN_DEPTH,
                "maximum": MAX_DEPTH,
                "description": (
                    f"Transitive depth (default {DEFAULT_DEPTH}, "
                    f"range {MIN_DEPTH}-{MAX_DEPTH})."
                ),
            },
        },
        "required": ["name"],
    },
)


def _risk_tier(count: int) -> str:
    """Return a risk-tier hint matching the ``/cbm-impact`` slash command."""
    if count <= 10:
        return "Low risk — safe local change. One PR is fine."
    if count <= 50:
        return (
            "Medium risk — keep this PR focused, add targeted tests for the "
            "affected nodes."
        )
    return (
        "HIGH RISK — split into smaller PRs: introduce the new API first, "
        "migrate callers incrementally, remove the old surface last."
    )


async def handle(arguments: dict[str, Any]) -> list[types.TextContent]:
    name = arguments["name"]
    graph_file = arguments.get("graph_file", DEFAULT_GRAPH_FILE)
    depth = max(MIN_DEPTH, min(int(arguments.get("depth", DEFAULT_DEPTH)), MAX_DEPTH))

    engine = CACHE.get(graph_file)
    affected = engine.impact(name, depth=depth)
    count = len(affected)

    if count == 0:
        text = (
            f"No impact found for '{name}'. Either the node has no dependents "
            f"or it does not exist in the graph (try `cbm_search` first)."
        )
    else:
        lines = [
            f"Impact of '{name}' at depth {depth}: {count} node(s) affected",
            f"Risk: {_risk_tier(count)}",
            "",
            "Affected nodes:",
        ]
        lines.extend(f"  !! {node_id}" for node_id in affected)
        text = "\n".join(lines)

    return [types.TextContent(type="text", text=text)]


_server.register_tool(TOOL, handle)
