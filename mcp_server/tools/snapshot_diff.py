# HC-AI | ticket: FDD-TOOL-CODEMAP
"""MCP tool: ``cbm_snapshot_diff`` — compare two graph snapshots.

Wraps the CBM Python API (``SnapshotManager`` + ``SnapshotDiff`` + the
``diff_formatter`` helpers) that powers the ``codebase-map snapshot-diff``
CLI. Accepts snapshot labels (resolved via the default cache dir) or direct
file paths for either side.
"""

from __future__ import annotations

from typing import Any

import mcp.types as types

from codebase_map.graph.diff_formatter import (
    filter_breaking_only,
    format_diff_json,
    format_diff_markdown,
    format_diff_text,
    format_test_plan,
)
from codebase_map.graph.snapshot_diff import SnapshotDiff
from codebase_map.snapshot import SnapshotManager
from mcp_server import server as _server

DEFAULT_DEPTH = 2
MIN_DEPTH = 1
MAX_DEPTH = 3
VALID_FORMATS = ("text", "markdown", "json")
DEFAULT_FORMAT = "markdown"


TOOL = types.Tool(
    name="cbm_snapshot_diff",
    description=(
        "Compare two graph snapshots (baseline vs current). Returns added / "
        "removed / modified / renamed functions + affected callers. Use when "
        "user asks 'what changed between baseline and post-dev', 'generate PR "
        "impact report', 'before/after diff'. Prefer this over git-diff for "
        "richer caller analysis."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "baseline": {
                "type": "string",
                "description": (
                    "Snapshot label (e.g., 'baseline') OR file path to "
                    "snapshot JSON."
                ),
            },
            "current": {
                "type": "string",
                "description": (
                    "Snapshot label (e.g., 'post-dev') OR file path to "
                    "snapshot JSON."
                ),
            },
            "depth": {
                "type": "integer",
                "default": DEFAULT_DEPTH,
                "minimum": MIN_DEPTH,
                "maximum": MAX_DEPTH,
                "description": (
                    "Caller traversal depth. 1=direct, 2=PR-review sweet "
                    "spot, 3=wide."
                ),
            },
            "breaking_only": {
                "type": "boolean",
                "default": False,
                "description": ("Filter to only breaking changes (signature/removal)."),
            },
            "test_plan": {
                "type": "boolean",
                "default": False,
                "description": ("Include suggested test plan (which tests to update)."),
            },
            "format": {
                "type": "string",
                "default": DEFAULT_FORMAT,
                "enum": list(VALID_FORMATS),
                "description": ("Output format. markdown preferred for PR body paste."),
            },
        },
        "required": ["baseline", "current"],
    },
)


def _render(result: Any, fmt: str) -> str:
    if fmt == "json":
        return format_diff_json(result)
    if fmt == "text":
        return format_diff_text(result)
    return format_diff_markdown(result)


async def handle(arguments: dict[str, Any]) -> list[types.TextContent]:
    baseline = arguments["baseline"]
    current = arguments["current"]
    depth = max(MIN_DEPTH, min(int(arguments.get("depth", DEFAULT_DEPTH)), MAX_DEPTH))
    breaking_only = bool(arguments.get("breaking_only", False))
    want_test_plan = bool(arguments.get("test_plan", False))
    fmt = arguments.get("format", DEFAULT_FORMAT)
    if fmt not in VALID_FORMATS:
        fmt = DEFAULT_FORMAT

    # SnapshotManager.load() accepts both labels and file paths. It searches
    # the default cache dir (.codebase-map-cache/snapshots) relative to CWD.
    mgr = SnapshotManager()
    try:
        baseline_graph = mgr.load(baseline)
        current_graph = mgr.load(current)
    except FileNotFoundError as exc:
        # Message from SnapshotManager already includes the unresolved label
        # and a hint to run `codebase-map snapshots list`.
        return [types.TextContent(type="text", text=str(exc))]

    result = SnapshotDiff(baseline_graph, current_graph).compute(depth=depth)

    if breaking_only:
        result = filter_breaking_only(result)

    if want_test_plan:
        # Test plan output supplements the formatted diff so the model gets
        # both the summary and the actionable follow-up in one response.
        body = _render(result, fmt)
        plan = format_test_plan(result)
        text = f"{body}\n\n{plan}"
    else:
        text = _render(result, fmt)

    return [types.TextContent(type="text", text=text)]


_server.register_tool(TOOL, handle)
