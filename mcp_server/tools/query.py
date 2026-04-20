# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP tool: ``cbm_query`` — full details of a function/class node.

Reuses :class:`codebase_map.graph.query.QueryEngine` via the shared
``GraphCache`` singleton (CBM-INT-206) to avoid re-parsing ``graph.json``
on every call.
"""

from __future__ import annotations

from typing import Any

import mcp.types as types

from mcp_server import server as _server
from mcp_server.graph_cache import CACHE, DEFAULT_GRAPH_FILE

TOOL = types.Tool(
    name="cbm_query",
    description=(
        "Get full details of a function/class: file path, layer, dependencies, "
        "callers, impact zone, suggested test files. Use when user asks "
        "'where is X defined', 'what does X do', 'show me details of X'."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Function or class name. Exact match preferred; falls back "
                    "to fuzzy search and uses the first result."
                ),
            },
            "graph_file": {
                "type": "string",
                "default": DEFAULT_GRAPH_FILE,
                "description": "Path to Codebase Map graph.json",
            },
        },
        "required": ["name"],
    },
)


async def handle(arguments: dict[str, Any]) -> list[types.TextContent]:
    name = arguments["name"]
    graph_file = arguments.get("graph_file", DEFAULT_GRAPH_FILE)

    engine = CACHE.get(graph_file)
    result = engine.query_node(name)

    if result is None:
        text = (
            f"No node found matching '{name}'. Try `cbm_search` with a keyword "
            f"to find the exact node name."
        )
    else:
        text = result.to_text()

    return [types.TextContent(type="text", text=text)]


_server.register_tool(TOOL, handle)
