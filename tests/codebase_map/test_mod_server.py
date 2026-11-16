# HC-AI | ticket: VIBE-105
"""Tests for codebase_map.mod.server — HTTP endpoints."""

from __future__ import annotations

import json
import socket
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from codebase_map.mod.server import make_server


def _free_port() -> int:
    """Grab an unused loopback port."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture()
def server(tmp_path: Path):
    port = _free_port()
    httpd = make_server(tmp_path, host="127.0.0.1", port=port)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)


class TestEndpoints:
    def test_health(self, server):
        with urlopen(f"{server}/api/health", timeout=3) as r:
            assert r.status == 200
            body = json.loads(r.read().decode())
            assert body == {"ok": True}

    def test_status(self, server):
        with urlopen(f"{server}/api/status", timeout=3) as r:
            assert r.status == 200
            data = json.loads(r.read().decode())
            # Status always collects, even without git/gh/snapshot.
            assert "sprint" in data
            assert "branch" in data
            assert "risk_level" in data
            assert data["errors"] == {}

    def test_root_returns_html(self, server):
        with urlopen(f"{server}/", timeout=3) as r:
            assert r.status == 200
            assert "text/html" in r.headers["Content-Type"]
            assert b"CBM Mod" in r.read()

    def test_404_on_unknown(self, server):
        import urllib.error

        with pytest.raises(urllib.error.HTTPError) as exc:
            urlopen(f"{server}/no-such-path", timeout=3)
        assert exc.value.code == 404

    def test_cors_headers(self, server):
        with urlopen(f"{server}/api/health", timeout=3) as r:
            assert r.headers["Access-Control-Allow-Origin"] == "*"

    def test_options_preflight(self, server):
        req = Request(f"{server}/api/status", method="OPTIONS")
        with urlopen(req, timeout=3) as r:
            assert r.status == 204
            assert r.headers["Access-Control-Allow-Origin"] == "*"
            assert "GET" in r.headers["Access-Control-Allow-Methods"]
