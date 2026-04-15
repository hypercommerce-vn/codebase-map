# HC-AI | ticket: MEM-M2-08
"""MCP Server — stdio transport with auto-discovery.

Architecture spec: §4.4 MCP Hub.
Imports vertical packages → triggers @register_tool decorators → serves.
Adapter pattern (MEM-M2-07): protocol handling isolated here.
"""

from __future__ import annotations

import importlib
import json
import logging
import sys
from typing import Any

from knowledge_memory.core.mcp.registry import (
    RESOURCES,
    TOOLS,
    list_resources,
    list_tools,
)
from knowledge_memory.core.mcp.tool_base import ToolResult

logger = logging.getLogger("codebase-memory.mcp.server")


# HC-AI | ticket: MEM-M2-08
class MCPServer:
    """MCP Server with stdio transport.

    Discovers tools from vertical imports, then serves them
    over stdin/stdout using MCP protocol (JSON-RPC 2.0 subset).

    This is the adapter layer (MEM-M2-07) — if MCP protocol
    changes, only this file needs updating.
    """

    def __init__(self, verticals: list[str] | None = None) -> None:
        self._verticals = verticals or ["codebase"]
        self._initialized = False

    def discover_tools(self) -> None:
        """Import vertical packages to trigger @register_tool decorators.

        Uses reload() if module already imported (e.g., after clear_registry).
        """
        for v in self._verticals:
            module_name = f"knowledge_memory.verticals.{v}.mcp_tools"
            try:
                mod = importlib.import_module(module_name)
                # Re-trigger decorators if module was already cached
                if module_name in sys.modules:
                    importlib.reload(mod)
                logger.info("Loaded MCP tools from vertical: %s", v)
            except ImportError as e:
                logger.warning("No MCP tools for vertical '%s': %s", v, e)

        self._initialized = True
        logger.info(
            "MCP server ready: %d tools, %d resources",
            len(TOOLS),
            len(RESOURCES),
        )

    def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle a single MCP JSON-RPC request.

        Supported methods:
        - initialize: handshake
        - tools/list: list registered tools
        - tools/call: execute a tool
        - resources/list: list registered resources
        - resources/read: read a resource
        """
        method = request.get("method", "")
        req_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return self._resp(
                req_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"listChanged": False},
                    },
                    "serverInfo": {
                        "name": "knowledge-memory",
                        "version": "1.0.0",
                    },
                },
            )

        if method == "tools/list":
            return self._resp(req_id, {"tools": list_tools()})

        if method == "tools/call":
            return self._handle_tool_call(req_id, params)

        if method == "resources/list":
            return self._resp(req_id, {"resources": list_resources()})

        if method == "resources/read":
            return self._handle_resource_read(req_id, params)

        if method == "notifications/initialized":
            # Client acknowledgement — no response needed
            return {}

        return self._error(req_id, -32601, f"Method not found: {method}")

    def _handle_tool_call(self, req_id: Any, params: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered tool."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool = TOOLS.get(tool_name)
        if not tool:
            return self._error(
                req_id,
                -32602,
                f"Tool not found: '{tool_name}'. " f"Available: {list(TOOLS.keys())}",
            )

        try:
            result = tool.execute(**arguments)
        except Exception as e:
            logger.error("Tool '%s' failed: %s", tool_name, e)
            result = ToolResult.failure(str(e))

        if result.is_error:
            return self._resp(
                req_id,
                {
                    "content": [{"type": "text", "text": result.error}],
                    "isError": True,
                },
            )

        # Format content
        if isinstance(result.content, dict):
            text = json.dumps(result.content, indent=2, default=str)
        elif isinstance(result.content, str):
            text = result.content
        else:
            text = str(result.content)

        return self._resp(
            req_id,
            {
                "content": [{"type": "text", "text": text}],
            },
        )

    def _handle_resource_read(
        self, req_id: Any, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Read a registered resource."""
        uri = params.get("uri", "")

        resource = RESOURCES.get(uri)
        if not resource:
            return self._error(
                req_id,
                -32602,
                f"Resource not found: '{uri}'. " f"Available: {list(RESOURCES.keys())}",
            )

        try:
            content = resource.read()
        except Exception as e:
            logger.error("Resource '%s' read failed: %s", uri, e)
            return self._error(req_id, -32603, str(e))

        return self._resp(
            req_id,
            {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": resource.mime_type,
                        "text": content,
                    }
                ],
            },
        )

    def run_stdio(self) -> None:
        """Run the server on stdio transport (blocking).

        Reads JSON-RPC requests from stdin, writes responses to stdout.
        """
        if not self._initialized:
            self.discover_tools()

        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
            except json.JSONDecodeError:
                continue

            response = self.handle_request(request)
            if response:  # Skip empty responses (notifications)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

    @staticmethod
    def _resp(req_id: Any, result: Any) -> dict[str, Any]:
        """Format a JSON-RPC success response."""
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    @staticmethod
    def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
        """Format a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        }
