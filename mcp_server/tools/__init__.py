# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tool modules for the Codebase Map MCP server.

Each tool module self-registers with ``mcp_server.server.TOOL_REGISTRY`` at
import time. Importing this package triggers registration for all shipped
tools — the server does ``import mcp_server.tools`` before serving requests.
"""

from mcp_server.tools import impact, query, search, snapshot_diff  # noqa: F401
