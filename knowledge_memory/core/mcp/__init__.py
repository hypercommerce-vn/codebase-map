# HC-AI | ticket: MEM-M2-07 / MEM-M2-08
"""MCP Hub — tool/resource registry for vertical MCP plugins.

Architecture spec: §4.4 MCP Hub.
- registry.py: @register_tool / @register_resource decorators
- tool_base.py: BaseMCPTool / BaseMCPResource ABCs
- server.py: MCPServer with stdio transport
"""

from knowledge_memory.core.mcp.registry import (
    RESOURCES,
    TOOLS,
    clear_registry,
    list_resources,
    list_tools,
    register_resource,
    register_tool,
)
from knowledge_memory.core.mcp.server import MCPServer
from knowledge_memory.core.mcp.tool_base import (
    BaseMCPResource,
    BaseMCPTool,
    ToolInput,
    ToolResult,
)

__all__ = [
    "TOOLS",
    "RESOURCES",
    "register_tool",
    "register_resource",
    "clear_registry",
    "list_tools",
    "list_resources",
    "MCPServer",
    "BaseMCPTool",
    "BaseMCPResource",
    "ToolInput",
    "ToolResult",
]
