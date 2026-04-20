# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP tool: ``cbm_search`` — fuzzy search nodes by keyword."""

from __future__ import annotations

from typing import Any

import mcp.types as types

from mcp_server import server as _server
from mcp_server.graph_cache import CACHE, DEFAULT_GRAPH_FILE

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


TOOL = types.Tool(
    name="cbm_search",
    description=(
        "Fuzzy search nodes by keyword across names, IDs, and docstrings. "
        "Use when user asks 'find X', 'search for X', 'where is X mentioned'."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "keyword": {
                "type": "string",
                "description": "Keyword to match (case-insensitive substring).",
            },
            "graph_file": {
                "type": "string",
                "default": DEFAULT_GRAPH_FILE,
                "description": "Path to Codebase Map graph.json",
            },
            "limit": {
                "type": "integer",
                "default": DEFAULT_LIMIT,
                "minimum": 1,
                "maximum": MAX_LIMIT,
                "description": (
                    f"Max results to return (default {DEFAULT_LIMIT}, "
                    f"max {MAX_LIMIT})."
                ),
            },
        },
        "required": ["keyword"],
    },
)


async def handle(arguments: dict[str, Any]) -> list[types.TextContent]:
    keyword = arguments["keyword"]
    graph_file = arguments.get("graph_file", DEFAULT_GRAPH_FILE)
    limit = min(int(arguments.get("limit", DEFAULT_LIMIT)), MAX_LIMIT)

    engine = CACHE.get(graph_file)
    results = engine.search(keyword)
    total = len(results)
    truncated = results[:limit]

    if total == 0:
        text = f"No nodes match '{keyword}'."
    else:
        header = f"Found {total} node(s) matching '{keyword}'"
        if total > limit:
            header += f" (showing first {limit})"
        lines = [header + ":", ""]
        for node in truncated:
            lines.append(
                f"  {node.name}  [{node.node_type.value}]  "
                f"{node.file_path}:{node.line_start}  layer={node.layer.value}"
            )
        text = "\n".join(lines)

    return [types.TextContent(type="text", text=text)]


_server.register_tool(TOOL, handle)
