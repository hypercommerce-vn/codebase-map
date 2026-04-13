# HC-AI | ticket: MEM-M2-07
"""BaseMCPTool — abstract base for all MCP tools.

Each tool defines: name, description, input_schema, and execute().
Adapter pattern isolates MCP protocol details (Risk R-T3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolInput:
    """Schema definition for a tool parameter."""

    name: str
    type: str = "string"
    description: str = ""
    required: bool = True


@dataclass
class ToolResult:
    """Result from a tool execution."""

    content: Any = None
    error: str = ""
    is_error: bool = False

    @staticmethod
    def success(content: Any) -> "ToolResult":
        return ToolResult(content=content)

    @staticmethod
    def failure(error: str) -> "ToolResult":
        return ToolResult(error=error, is_error=True)


class BaseMCPTool(ABC):
    """Abstract base class for MCP tools.

    Vertical tools extend this and register via @register_tool decorator.
    The MCP adapter converts execute() results to protocol format.
    """

    name: str = ""
    description: str = ""
    input_schema: list[ToolInput] = []

    @abstractmethod
    def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Returns ToolResult with content (success) or error (failure).
        """
        ...

    def to_mcp_schema(self) -> dict[str, Any]:
        """Convert to MCP protocol tool definition.

        Adapter method: generates the JSON schema that MCP clients
        (Claude Code, Cursor) use to discover and invoke this tool.
        """
        properties: dict[str, Any] = {}
        required: list[str] = []

        for inp in self.input_schema:
            properties[inp.name] = {
                "type": inp.type,
                "description": inp.description,
            }
            if inp.required:
                required.append(inp.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


@dataclass
class BaseMCPResource(ABC):
    """Abstract base for MCP resources (read-only data providers)."""

    uri: str = ""
    name: str = ""
    description: str = ""
    mime_type: str = "text/plain"

    @abstractmethod
    def read(self) -> str:
        """Read the resource content."""
        ...
