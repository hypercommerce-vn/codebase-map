# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP tool: ``cbm_api_catalog`` — list HTTP API routes with optional filters.

Reuses :class:`codebase_map.graph.api_catalog.APICatalog` which extracts
``ROUTE`` nodes from the parsed graph. Supports filtering by HTTP method
and domain. Output is either human-readable text (default) or JSON.
"""

from __future__ import annotations

from typing import Any

import mcp.types as types

from codebase_map.graph.api_catalog import APICatalog
from mcp_server import server as _server
from mcp_server.graph_cache import CACHE, DEFAULT_GRAPH_FILE

TOOL = types.Tool(
    name="cbm_api_catalog",
    description=(
        "List all HTTP API routes in the codebase. Optionally filter by "
        "method (GET/POST/...) or domain. Use when user asks 'what APIs "
        "does this project have', 'list all endpoints', 'which routes "
        "match X'."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "graph_file": {
                "type": "string",
                "default": DEFAULT_GRAPH_FILE,
                "description": "Path to Codebase Map graph.json",
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", ""],
                "default": "",
                "description": "HTTP method filter. Empty = all methods.",
            },
            "domain": {
                "type": "string",
                "default": "",
                "description": (
                    "Domain filter (e.g. 'customer', 'order'). Empty = all."
                ),
            },
            "format": {
                "type": "string",
                "enum": ["text", "json"],
                "default": "text",
                "description": "Output format: human text or JSON.",
            },
        },
    },
)


async def handle(arguments: dict[str, Any]) -> list[types.TextContent]:
    graph_file = arguments.get("graph_file", DEFAULT_GRAPH_FILE)
    method = (arguments.get("method") or "").strip()
    domain = (arguments.get("domain") or "").strip()
    fmt = arguments.get("format", "text")

    engine = CACHE.get(graph_file)
    catalog = APICatalog.from_graph(engine.graph)

    if method or domain:
        filtered = catalog.filter(method=method, domain=domain)
        catalog.endpoints = filtered
        catalog.by_domain = {}
        catalog.by_method = {}
        for ep in filtered:
            catalog.by_domain.setdefault(ep.domain, []).append(ep)
            catalog.by_method.setdefault(ep.http_method, []).append(ep)

    if catalog.total_endpoints == 0:
        filter_desc = []
        if method:
            filter_desc.append(f"method={method}")
        if domain:
            filter_desc.append(f"domain={domain}")
        suffix = f" (filters: {', '.join(filter_desc)})" if filter_desc else ""
        text = (
            f"No API routes found{suffix}. Ensure the graph was generated "
            f"with a parser that emits ROUTE nodes."
        )
    elif fmt == "json":
        text = catalog.to_json()
    else:
        text = catalog.to_text()

    return [types.TextContent(type="text", text=text)]


_server.register_tool(TOOL, handle)
