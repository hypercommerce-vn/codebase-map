# HC-AI | ticket: MEM-M2-07 / MEM-M2-08
"""Tests for MCP Hub: registry, server, tool_base, and codebase tools."""

from __future__ import annotations

from knowledge_memory.core.mcp.registry import (
    TOOLS,
    clear_registry,
    list_tools,
    register_tool,
)
from knowledge_memory.core.mcp.server import MCPServer
from knowledge_memory.core.mcp.tool_base import BaseMCPTool, ToolInput, ToolResult

# ── Helpers ──────────────────────────────────


def _sample_nodes():
    return [
        {
            "name": "login",
            "file_path": "auth/router.py",
            "layer": "route",
            "node_type": "function",
            "line_start": 12,
        },
        {
            "name": "authenticate",
            "file_path": "auth/service.py",
            "layer": "service",
            "node_type": "function",
            "line_start": 45,
        },
        {
            "name": "hash_password",
            "file_path": "auth/utils.py",
            "layer": "util",
            "node_type": "function",
            "line_start": 8,
        },
    ]


def _sample_edges():
    return [
        {"source_name": "login", "target_name": "authenticate"},
        {"source_name": "authenticate", "target_name": "hash_password"},
    ]


# ══════════════════════════════════════════════════
# ToolBase tests
# ══════════════════════════════════════════════════


class TestToolBase:
    def test_tool_result_success(self):
        r = ToolResult.success({"key": "value"})
        assert not r.is_error
        assert r.content == {"key": "value"}

    def test_tool_result_failure(self):
        r = ToolResult.failure("something broke")
        assert r.is_error
        assert r.error == "something broke"

    def test_to_mcp_schema(self):
        class DummyTool(BaseMCPTool):
            name = "test_tool"
            description = "A test tool"
            input_schema = [
                ToolInput(name="query", type="string", description="Search query"),
                ToolInput(
                    name="limit",
                    type="integer",
                    description="Max results",
                    required=False,
                ),
            ]

            def execute(self, **kwargs):
                return ToolResult.success("ok")

        tool = DummyTool()
        schema = tool.to_mcp_schema()
        assert schema["name"] == "test_tool"
        assert schema["description"] == "A test tool"
        assert "query" in schema["inputSchema"]["properties"]
        assert "query" in schema["inputSchema"]["required"]
        assert "limit" not in schema["inputSchema"]["required"]


# ══════════════════════════════════════════════════
# Registry tests
# ══════════════════════════════════════════════════


class TestRegistry:
    def setup_method(self):
        clear_registry()

    def test_register_tool_decorator(self):
        @register_tool("my_tool")
        class MyTool(BaseMCPTool):
            description = "My tool"
            input_schema = []

            def execute(self, **kwargs):
                return ToolResult.success("hello")

        assert "my_tool" in TOOLS
        assert TOOLS["my_tool"].name == "my_tool"

    def test_list_tools(self):
        @register_tool("tool_a")
        class ToolA(BaseMCPTool):
            description = "Tool A"
            input_schema = []

            def execute(self, **kwargs):
                return ToolResult.success("a")

        schemas = list_tools()
        assert len(schemas) >= 1
        names = [s["name"] for s in schemas]
        assert "tool_a" in names

    def test_clear_registry(self):
        @register_tool("temp")
        class TempTool(BaseMCPTool):
            description = "Temp"
            input_schema = []

            def execute(self, **kwargs):
                return ToolResult.success("")

        assert "temp" in TOOLS
        clear_registry()
        assert "temp" not in TOOLS

    def test_tool_execution_via_registry(self):
        @register_tool("adder")
        class AdderTool(BaseMCPTool):
            description = "Add numbers"
            input_schema = [
                ToolInput(name="a", type="integer"),
                ToolInput(name="b", type="integer"),
            ]

            def execute(self, **kwargs):
                a = int(kwargs.get("a", 0))
                b = int(kwargs.get("b", 0))
                return ToolResult.success({"sum": a + b})

        result = TOOLS["adder"].execute(a=3, b=4)
        assert result.content == {"sum": 7}


# ══════════════════════════════════════════════════
# MCPServer tests
# ══════════════════════════════════════════════════


class TestMCPServer:
    def setup_method(self):
        clear_registry()

        @register_tool("test_tool")
        class TestTool(BaseMCPTool):
            description = "Test tool"
            input_schema = [
                ToolInput(name="x", type="string", description="Input"),
            ]

            def execute(self, **kwargs):
                x = kwargs.get("x", "")
                return ToolResult.success(f"echo: {x}")

        self.server = MCPServer(verticals=[])
        self.server._initialized = True

    def test_initialize(self):
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {},
            }
        )
        assert resp["result"]["serverInfo"]["name"] == "knowledge-memory"
        assert "capabilities" in resp["result"]

    def test_tools_list(self):
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }
        )
        tools = resp["result"]["tools"]
        names = [t["name"] for t in tools]
        assert "test_tool" in names

    def test_tools_call_success(self):
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "test_tool", "arguments": {"x": "hello"}},
            }
        )
        content = resp["result"]["content"][0]["text"]
        assert "echo: hello" in content

    def test_tools_call_not_found(self):
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "nonexistent", "arguments": {}},
            }
        )
        assert "error" in resp
        assert "not found" in resp["error"]["message"].lower()

    def test_method_not_found(self):
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "unknown/method",
                "params": {},
            }
        )
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_notification_no_response(self):
        resp = self.server.handle_request(
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
        )
        assert resp == {}


# ══════════════════════════════════════════════════
# Codebase MCP Tools tests
# ══════════════════════════════════════════════════


class TestCodebaseMCPTools:
    def setup_method(self):
        clear_registry()
        from knowledge_memory.verticals.codebase import mcp_tools

        mcp_tools.configure_tools(
            nodes=_sample_nodes(),
            edges=_sample_edges(),
        )
        # Re-import triggers @register_tool
        import importlib

        importlib.reload(mcp_tools)
        mcp_tools.configure_tools(
            nodes=_sample_nodes(),
            edges=_sample_edges(),
        )

    def test_find_function_exact(self):
        tool = TOOLS.get("find_function")
        assert tool is not None
        result = tool.execute(name="authenticate")
        assert not result.is_error
        assert result.content["name"] == "authenticate"

    def test_find_function_partial(self):
        tool = TOOLS["find_function"]
        result = tool.execute(name="auth")
        assert not result.is_error
        # Should match authenticate
        content = result.content
        if "matches" in content:
            assert content["count"] >= 1
        else:
            assert "name" in content

    def test_find_function_not_found(self):
        tool = TOOLS["find_function"]
        result = tool.execute(name="zzz_nonexistent_zzz")
        assert result.is_error
        assert "not found" in result.error.lower()

    def test_find_function_no_param(self):
        tool = TOOLS["find_function"]
        result = tool.execute()
        assert result.is_error

    def test_explain_module(self):
        tool = TOOLS.get("explain_module")
        assert tool is not None
        result = tool.execute(module="auth")
        assert not result.is_error
        assert result.content["total_functions"] >= 2

    def test_explain_module_not_found(self):
        tool = TOOLS["explain_module"]
        result = tool.execute(module="zzz_nonexistent")
        assert result.is_error

    def test_pattern_check_snake_case(self):
        tool = TOOLS.get("pattern_check")
        assert tool is not None
        result = tool.execute(function="get_user_by_id")
        assert not result.is_error
        assert len(result.content["violations"]) == 0

    def test_pattern_check_camel_case(self):
        tool = TOOLS["pattern_check"]
        result = tool.execute(function="getUserById")
        assert not result.is_error
        assert len(result.content["violations"]) >= 1
        assert "camelCase" in result.content["violations"][0]["detail"]

    def test_impact_tool(self):
        tool = TOOLS.get("impact")
        assert tool is not None
        result = tool.execute(function="authenticate")
        assert not result.is_error
        assert result.content["function"] == "authenticate"
        assert len(result.content["direct_callers"]) >= 1

    def test_impact_tool_not_found(self):
        tool = TOOLS["impact"]
        result = tool.execute(function="zzz_nonexistent_zzz")
        assert result.is_error

    def test_all_four_tools_registered(self):
        expected = {"find_function", "explain_module", "pattern_check", "impact"}
        assert expected.issubset(set(TOOLS.keys()))
