# HC-AI | ticket: MEM-M2-08
"""MCP Tool/Resource Registry — auto-discovery via @register_tool decorator.

Architecture spec: §4.4 MCP Hub.
Verticals register tools/resources via decorators.
Server imports vertical packages → triggers registration.
"""

from __future__ import annotations

import logging
from typing import Any

from knowledge_memory.core.mcp.tool_base import BaseMCPResource, BaseMCPTool

logger = logging.getLogger("codebase-memory.mcp.registry")

# HC-AI | ticket: MEM-M2-08
# Global registries — populated by @register_tool / @register_resource
TOOLS: dict[str, BaseMCPTool] = {}
RESOURCES: dict[str, BaseMCPResource] = {}


def register_tool(name: str):
    """Decorator to register an MCP tool.

    Usage::

        @register_tool("find_function")
        class FindFunctionTool(BaseMCPTool):
            ...
    """

    def deco(cls: type[BaseMCPTool]) -> type[BaseMCPTool]:
        instance = cls()
        instance.name = name
        TOOLS[name] = instance
        logger.debug("Registered MCP tool: %s", name)
        return cls

    return deco


def register_resource(uri: str):
    """Decorator to register an MCP resource.

    Usage::

        @register_resource("patterns://codebase")
        class PatternsResource(BaseMCPResource):
            ...
    """

    def deco(cls: type[BaseMCPResource]) -> type[BaseMCPResource]:
        instance = cls()
        instance.uri = uri
        RESOURCES[uri] = instance
        logger.debug("Registered MCP resource: %s", uri)
        return cls

    return deco


def clear_registry() -> None:
    """Clear all registered tools and resources (for testing)."""
    TOOLS.clear()
    RESOURCES.clear()


def list_tools() -> list[dict[str, Any]]:
    """List all registered tools as MCP schema dicts."""
    return [tool.to_mcp_schema() for tool in TOOLS.values()]


def list_resources() -> list[dict[str, Any]]:
    """List all registered resources."""
    return [
        {
            "uri": r.uri,
            "name": r.name,
            "description": r.description,
            "mimeType": r.mime_type,
        }
        for r in RESOURCES.values()
    ]
