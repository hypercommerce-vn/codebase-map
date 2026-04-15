# HC-AI | ticket: KMP-MCP-01
"""HTTP transport for KMP MCP Server — FastAPI wrapper.

Bridges HTTP requests to MCPServer.handle_request() so KMP can run
inside Docker and be accessed over the network (not just stdio).

Endpoints:
    POST /mcp    — JSON-RPC 2.0 (same protocol as stdio transport)
    GET  /health — container health check
    GET  /info   — vault metadata

Usage:
    VAULT_ROOT=/workspace uvicorn knowledge_memory.http_server:app \
        --host 0.0.0.0 --port 9100

Env vars:
    VAULT_ROOT — path to project root containing .knowledge-memory/
                 (defaults to cwd)
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("codebase-memory.http")

# HC-AI | ticket: KMP-MCP-01
# Module-level server + vault references — set on startup
_mcp_server = None
_vault_info: dict[str, Any] = {}


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load vault and configure MCP tools on server start."""
    global _mcp_server, _vault_info

    # Log to stderr (keep stdout clean for potential mixed usage)
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )

    from knowledge_memory.core.mcp.server import MCPServer
    from knowledge_memory.verticals.codebase.mcp_tools import configure_tools
    from knowledge_memory.verticals.codebase.vault import CodebaseVault

    vault_root = Path(os.environ.get("VAULT_ROOT", os.getcwd()))
    vault_dir = vault_root / ".knowledge-memory"

    if not vault_dir.exists():
        logger.error(
            "Vault not found at %s. "
            "Run: codebase-memory init && codebase-memory bootstrap",
            vault_dir,
        )
        # Don't sys.exit — let health check report unhealthy
        _vault_info = {"status": "error", "detail": "Vault not found"}
        yield
        return

    # Open vault + load data
    vault = CodebaseVault()
    vault.open(vault_root)

    nodes = vault.query_nodes()
    edges = vault.query_edges()
    patterns = vault.query_patterns()

    logger.info(
        "Vault loaded: %d nodes, %d edges, %d patterns",
        len(nodes),
        len(edges),
        len(patterns),
    )

    # Discover tools FIRST (triggers @register_tool decorators)
    # Must happen before configure_tools() because discover_tools()
    # reloads the module which resets module-level variables.
    server = MCPServer(verticals=["codebase"])
    server.discover_tools()

    # THEN configure tools with vault data
    configure_tools(
        vault=vault,
        nodes=nodes,
        edges=edges,
        patterns=patterns,
    )

    _mcp_server = server
    _vault_info = {
        "vault_root": str(vault_root),
        "nodes": len(nodes),
        "edges": len(edges),
        "patterns": len(patterns),
    }

    logger.info("HTTP MCP server ready at %s", vault_root)
    yield


def _create_app() -> FastAPI:
    """Create FastAPI app with lifespan startup."""

    app = FastAPI(
        title="KMP MCP Server",
        description="Knowledge Memory Platform — HTTP transport for MCP",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        lifespan=_lifespan,
    )

    @app.get("/health")
    async def health() -> JSONResponse:
        """Health check endpoint for Docker HEALTHCHECK."""
        if _mcp_server is None:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "detail": "MCP server not initialized"},
            )
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", **_vault_info},
        )

    @app.get("/info")
    async def info() -> JSONResponse:
        """Vault metadata — nodes, edges, patterns count."""
        return JSONResponse(content=_vault_info)

    @app.post("/mcp")
    async def mcp_endpoint(request: Request) -> JSONResponse:
        """JSON-RPC 2.0 endpoint — same protocol as stdio transport.

        Accepts the same requests as the stdio MCP server:
        - initialize, tools/list, tools/call, resources/list, resources/read
        """
        if _mcp_server is None:
            return JSONResponse(
                status_code=503,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": "MCP server not initialized",
                    },
                },
            )

        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error — invalid JSON",
                    },
                },
            )

        response = _mcp_server.handle_request(body)

        if not response:
            # Notification — no response body
            return JSONResponse(status_code=204, content=None)

        return JSONResponse(content=response)

    return app


# HC-AI | ticket: KMP-MCP-01
# Module-level app instance for uvicorn
app = _create_app()
