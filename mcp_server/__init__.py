# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP Server for Codebase Map — Day 1 scaffold.

Exposes the Codebase Map query engine as Model Context Protocol tools for
Claude Code / Cowork / Desktop. The Day-1 scaffold (CBM-INT-201) ships only
the server skeleton; concrete tools ship in CBM-INT-202 through CBM-INT-205,
and the graph cache is completed in CBM-INT-206.
"""

__version__ = "0.1.0"
__all__ = ["server"]
