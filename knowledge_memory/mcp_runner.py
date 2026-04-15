# HC-AI | ticket: KMP-MCP-01
"""MCP Server runner — load vault + configure tools + serve stdio.

Entry point for Claude Code MCP integration.
Lives at top-level (not core/) to respect import-linter boundary:
core never imports verticals.

Usage:
    python -m knowledge_memory.mcp_runner
    # or via .mcp.json config
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger("codebase-memory.mcp.runner")


def main() -> None:
    """Load vault from cwd → discover tools → configure → serve."""
    from knowledge_memory.core.mcp.server import MCPServer
    from knowledge_memory.verticals.codebase.mcp_tools import configure_tools
    from knowledge_memory.verticals.codebase.vault import CodebaseVault

    root = Path.cwd()
    vault_dir = root / ".knowledge-memory"

    # Log to stderr (stdout reserved for MCP protocol)
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s: %(message)s",
        stream=sys.stderr,
    )

    if not vault_dir.exists():
        logger.error(
            "Vault not found at %s. "
            "Run: codebase-memory init && codebase-memory bootstrap",
            vault_dir,
        )
        sys.exit(1)

    # Open vault + load data
    vault = CodebaseVault()
    vault.open(root)

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

    logger.info("MCP server starting on stdio...")
    server.run_stdio()


if __name__ == "__main__":
    main()
