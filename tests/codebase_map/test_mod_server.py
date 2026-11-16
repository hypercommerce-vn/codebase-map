# HC-AI | ticket: VIBE-105
"""Tests for codebase_map.mod.server — HTTP endpoints."""

from __future__ import annotations

import json
import socket
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from codebase_map.mod.server import PANE_DIR, make_server


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

    def test_root_returns_pane_html(self, server):
        with urlopen(f"{server}/", timeout=3) as r:
            assert r.status == 200
            assert "text/html" in r.headers["Content-Type"]
            body = r.read()
            assert b"CBM Mod Pane" in body
            assert b'data-tab="graph"' in body
            assert b'data-tab="timeline"' in body
            assert b'data-tab="replay"' in body

    def test_pane_assets_served(self, server):
        for asset, needle in [
            ("styles.css", b"status-line"),
            ("app.js", b"fetchStatus"),
        ]:
            with urlopen(f"{server}/{asset}", timeout=3) as r:
                assert r.status == 200
                assert needle in r.read()

    def test_404_on_unknown(self, server):
        with pytest.raises(HTTPError) as exc:
            urlopen(f"{server}/no-such-path", timeout=3)
        assert exc.value.code == 404

    def test_pane_path_traversal_blocked(self, server):
        # Encoded traversal must not escape the pane dir.
        for bad in ["/..%2fetc%2fpasswd", "/..%2F..%2F..%2Fetc%2Fpasswd"]:
            with pytest.raises(HTTPError) as exc:
                urlopen(f"{server}{bad}", timeout=3)
            assert exc.value.code == 404

    def test_graph_404_when_missing(self, server):
        with pytest.raises(HTTPError) as exc:
            urlopen(f"{server}/api/graph", timeout=3)
        assert exc.value.code == 404
        body = json.loads(exc.value.read().decode())
        assert body["error"] == "graph not found"
        assert "hint" in body


class TestGraphEndpoint:
    def _start(self, repo: Path):
        port = _free_port()
        httpd = make_server(repo, host="127.0.0.1", port=port)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return httpd, thread, f"http://127.0.0.1:{port}"

    def test_graph_returned_when_present(self, tmp_path):
        gdir = tmp_path / "docs" / "function-map"
        gdir.mkdir(parents=True)
        payload = {"project": "fx", "nodes": [{"id": "a"}], "edges": []}
        (gdir / "graph.json").write_text(json.dumps(payload))
        httpd, thread, base = self._start(tmp_path)
        try:
            with urlopen(f"{base}/api/graph", timeout=3) as r:
                assert r.status == 200
                data = json.loads(r.read().decode())
                assert data["project"] == "fx"
                assert len(data["nodes"]) == 1
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)


class TestPaneAssetsOnDisk:
    """Sanity: the three pane files are shipped in the package."""

    @pytest.mark.parametrize("name", ["index.html", "styles.css", "app.js"])
    def test_pane_file_present(self, name):
        assert (PANE_DIR / name).is_file(), f"missing pane asset: {name}"


def _write_min_snapshot(path: Path, nodes: int, label: str = "test") -> None:
    """Write a small graph snapshot with N nodes under path."""
    data = {
        "project": "fixture",
        "generated_at": "2026-11-16T00:00:00+00:00",
        "stats": {"total_functions": nodes, "total_edges": max(0, nodes - 1)},
        "nodes": [
            {
                "id": f"m.f{i}",
                "name": f"f{i}",
                "type": "function",
                "layer": "core",
                "domain": "other",
                "file": "m.py",
                "line_start": i * 10,
                "line_end": i * 10 + 5,
                "docstring": "",
                "decorators": [],
                "params": [],
                "return_type": "None",
                "parent_class": "",
                "metadata": {},
            }
            for i in range(nodes)
        ],
        "edges": [
            {
                "source": f"m.f{i}",
                "target": f"m.f{i + 1}",
                "type": "calls",
                "metadata": {},
            }
            for i in range(nodes - 1)
        ],
        "metadata": {"label": label, "branch": "main", "commit_sha": "abc1234"},
    }
    path.write_text(json.dumps(data))


class TestSnapshotsEndpoint:
    def _start(self, repo: Path):
        port = _free_port()
        httpd = make_server(repo, host="127.0.0.1", port=port)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return httpd, thread, f"http://127.0.0.1:{port}"

    def test_empty_when_no_dir(self, tmp_path):
        httpd, thread, base = self._start(tmp_path)
        try:
            with urlopen(f"{base}/api/snapshots", timeout=3) as r:
                assert r.status == 200
                data = json.loads(r.read().decode())
                assert data["snapshots"] == []
                assert "hint" in data
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_lists_sorted_newest_first(self, tmp_path):
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        snap_dir.mkdir(parents=True)
        for i, name in enumerate(["a", "b", "c"]):
            _write_min_snapshot(snap_dir / f"{name}.json", nodes=3 + i, label=name)
        # Give b and c distinct generated_at so order is deterministic.
        for nm, ts in [("a", "01"), ("b", "02"), ("c", "03")]:
            p = snap_dir / f"{nm}.json"
            data = json.loads(p.read_text())
            data["generated_at"] = f"2026-11-{ts}T00:00:00+00:00"
            p.write_text(json.dumps(data))

        httpd, thread, base = self._start(tmp_path)
        try:
            with urlopen(f"{base}/api/snapshots", timeout=3) as r:
                data = json.loads(r.read().decode())
                ids = [s["id"] for s in data["snapshots"]]
                assert ids == ["c", "b", "a"]
                assert data["count"] == 3
                assert data["snapshots"][0]["nodes"] == 5
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_single_snapshot_returns_graph(self, tmp_path):
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        snap_dir.mkdir(parents=True)
        _write_min_snapshot(snap_dir / "x.json", nodes=4)
        httpd, thread, base = self._start(tmp_path)
        try:
            with urlopen(f"{base}/api/snapshots/x", timeout=3) as r:
                data = json.loads(r.read().decode())
                assert len(data["nodes"]) == 4
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_single_snapshot_404_on_bad_id(self, tmp_path):
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        snap_dir.mkdir(parents=True)
        httpd, thread, base = self._start(tmp_path)
        try:
            with pytest.raises(HTTPError) as exc:
                urlopen(f"{base}/api/snapshots/nope", timeout=3)
            assert exc.value.code == 404
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_snapshot_id_traversal_blocked(self, tmp_path):
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        snap_dir.mkdir(parents=True)
        httpd, thread, base = self._start(tmp_path)
        try:
            with pytest.raises(HTTPError) as exc:
                urlopen(f"{base}/api/snapshots/..%2fsecret", timeout=3)
            assert exc.value.code == 404
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_diff_requires_base(self, tmp_path):
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        snap_dir.mkdir(parents=True)
        _write_min_snapshot(snap_dir / "x.json", nodes=3)
        httpd, thread, base = self._start(tmp_path)
        try:
            with pytest.raises(HTTPError) as exc:
                urlopen(f"{base}/api/snapshots/x/diff", timeout=3)
            assert exc.value.code == 400
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_diff_returns_summary(self, tmp_path):
        snap_dir = tmp_path / ".codebase-map-cache" / "snapshots"
        snap_dir.mkdir(parents=True)
        _write_min_snapshot(snap_dir / "old.json", nodes=3, label="old")
        _write_min_snapshot(snap_dir / "new.json", nodes=5, label="new")
        httpd, thread, base = self._start(tmp_path)
        try:
            with urlopen(f"{base}/api/snapshots/new/diff?base=old", timeout=3) as r:
                data = json.loads(r.read().decode())
                assert "summary" in data
                summary = data["summary"]
                # Added 2 functions (3→5).
                assert summary["functions_added"] == 2
                assert summary["functions_removed"] == 0
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)

    def test_cors_headers(self, server):
        with urlopen(f"{server}/api/health", timeout=3) as r:
            assert r.headers["Access-Control-Allow-Origin"] == "*"

    def test_options_preflight(self, server):
        req = Request(f"{server}/api/status", method="OPTIONS")
        with urlopen(req, timeout=3) as r:
            assert r.status == 204
            assert r.headers["Access-Control-Allow-Origin"] == "*"
            assert "GET" in r.headers["Access-Control-Allow-Methods"]
