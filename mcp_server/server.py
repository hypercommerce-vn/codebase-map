# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP Server scaffold for Codebase Map.

Exposes the Codebase Map query engine as Model Context Protocol tools for
Claude Code / Cowork / Desktop. This Day-1 scaffold (CBM-INT-201) provides
the server skeleton only:

* Server instance is created with the public PyPI name ``codebase-map``.
* A module-level ``TOOL_REGISTRY`` dict lets subsequent sprint tasks
  (CBM-INT-202..205) register their tool schema + handler without editing
  this file.
* ``list_tools()`` returns the registry contents (empty on Day 1).
* ``call_tool()`` dispatches by name and raises ``ValueError`` for unknown
  tools.
* ``main()`` runs the stdio transport.

The ``mcp`` package is an **optional** runtime dependency — install with
``pip install codebase-map[mcp]``. If it's missing we raise a clear error at
import time rather than failing later with an obscure traceback.
"""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

try:
    import mcp.types as types
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError as exc:  # pragma: no cover - dependency guard
    raise ImportError(
        "The Codebase Map MCP server requires the 'mcp' package. "
        "Install it with: pip install codebase-map[mcp]"
    ) from exc

from mcp_server import __version__

# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

#: Handler coroutine signature:
#: ``async def handler(arguments: dict) -> list[TextContent]``.
ToolHandler = Callable[[dict[str, Any]], Awaitable[list[types.TextContent]]]

#: Registry mapping tool name -> (schema, handler). Tool modules shipping in
#: CBM-INT-202..205 will populate this dict at import time.
TOOL_REGISTRY: dict[str, tuple[types.Tool, ToolHandler]] = {}


def register_tool(tool: types.Tool, handler: ToolHandler) -> None:
    """Register an MCP tool + handler.

    Called by tool modules (``mcp_server/tools/*.py``) at import time. Raises
    ``ValueError`` if a tool with the same name is already registered to
    catch accidental duplicate registrations.
    """
    if tool.name in TOOL_REGISTRY:
        raise ValueError(f"Tool already registered: {tool.name}")
    TOOL_REGISTRY[tool.name] = (tool, handler)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

# Server name matches PyPI package name for discoverability.
server: Server = Server("codebase-map", version=__version__)


@server.list_tools()
async def _list_tools() -> list[types.Tool]:
    """Return the list of tools currently registered.

    Empty on Day 1; populated as CBM-INT-202..205 land.
    """
    return [tool for (tool, _handler) in TOOL_REGISTRY.values()]


@server.call_tool()
async def _call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    """Dispatch an MCP tool call to the registered handler.

    Raises ``ValueError`` for unknown tool names — the MCP SDK turns this
    into a well-formed JSON-RPC error response for the client.
    """
    entry = TOOL_REGISTRY.get(name)
    if entry is None:
        raise ValueError(f"Unknown tool: {name}")
    _tool, handler = entry
    return await handler(arguments or {})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def _run() -> None:
    """Run the MCP server over stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Synchronous entry point invoked by ``python -m mcp_server``."""
    # Import tool package here (not at module top) so tool modules can freely
    # ``import mcp_server.server`` during their self-registration without
    # causing a circular import. By ``main()`` time the server module is
    # fully initialised.
    import mcp_server.tools  # noqa: F401  (triggers tool registration)

    asyncio.run(_run())


if __name__ == "__main__":  # pragma: no cover
    main()
