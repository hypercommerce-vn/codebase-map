# HC-AI | ticket: KMP-MCP-01
"""Tests for HTTP MCP server (FastAPI wrapper).

Uses FastAPI TestClient — no vault required for basic protocol tests.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client without vault initialization."""
    import knowledge_memory.http_server as mod

    # Reset module state
    mod._mcp_server = None
    mod._vault_info = {}

    return TestClient(mod.app, raise_server_exceptions=False)


@pytest.fixture
def ready_client():
    """Create test client with a mock MCP server (simulates healthy state)."""
    import knowledge_memory.http_server as mod

    mock_server = MagicMock()
    mock_server.handle_request.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False},
            },
            "serverInfo": {"name": "knowledge-memory", "version": "1.0.0"},
        },
    }

    mod._mcp_server = mock_server
    mod._vault_info = {
        "vault_root": "/workspace",
        "nodes": 100,
        "edges": 200,
        "patterns": 5,
    }

    return TestClient(mod.app, raise_server_exceptions=False)


class TestHealth:
    """GET /health endpoint tests."""

    def test_health_unhealthy_before_init(self, client):
        """Health returns 503 when server not initialized."""
        resp = client.get("/health")
        assert resp.status_code == 503
        data = resp.json()
        assert data["status"] == "unhealthy"

    def test_health_healthy_when_ready(self, ready_client):
        """Health returns 200 when vault loaded."""
        resp = ready_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["nodes"] == 100
        assert data["edges"] == 200


class TestInfo:
    """GET /info endpoint tests."""

    def test_info_returns_vault_metadata(self, ready_client):
        """Info returns vault stats."""
        resp = ready_client.get("/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["vault_root"] == "/workspace"
        assert data["nodes"] == 100


class TestMCPEndpoint:
    """POST /mcp endpoint tests."""

    def test_mcp_503_before_init(self, client):
        """MCP returns 503 when server not initialized."""
        resp = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        assert resp.status_code == 503
        data = resp.json()
        assert data["error"]["code"] == -32603

    def test_mcp_initialize(self, ready_client):
        """MCP initialize handshake works."""
        resp = ready_client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data

    def test_mcp_tools_list(self, ready_client):
        """MCP tools/list returns registered tools."""
        ready_client.app  # noqa: B018
        import knowledge_memory.http_server as mod

        mod._mcp_server.handle_request.return_value = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "tools": [
                    {"name": "find_function"},
                    {"name": "explain_module"},
                    {"name": "pattern_check"},
                    {"name": "impact"},
                ]
            },
        }
        resp = ready_client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert resp.status_code == 200
        data = resp.json()
        tools = data["result"]["tools"]
        assert len(tools) == 4
        tool_names = [t["name"] for t in tools]
        assert "find_function" in tool_names

    def test_mcp_invalid_json(self, ready_client):
        """MCP returns parse error for invalid JSON."""
        resp = ready_client.post(
            "/mcp",
            content=b"not json",
            headers={"content-type": "application/json"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert data["error"]["code"] == -32700

    def test_mcp_notification_returns_204(self, ready_client):
        """MCP notification (no response) returns 204."""
        import knowledge_memory.http_server as mod

        mod._mcp_server.handle_request.return_value = {}

        resp = ready_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {},
            },
        )
        assert resp.status_code == 204
