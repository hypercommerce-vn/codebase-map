# HC-AI | ticket: VIBE-106
"""Tests for codebase_map.mod.server — HTTP endpoints."""

from __future__ import annotations

import json
import socket
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from codebase_map.mod.server import PANE_DIR, allowed_hosts, make_server


def _free_port() -> int:
    """Grab an unused loopback port."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


# HC-AI | ticket: VIBE-106
def _request(url: str, headers: dict | None = None, method: str = "GET"):
    """Send one request; return (status, headers, body), errors included."""
    req = Request(url, headers=headers or {}, method=method)
    try:
        with urlopen(req, timeout=3) as r:
            return r.status, r.headers, r.read()
    except HTTPError as e:
        return e.code, e.headers, e.read()


def _raw(port: int, request: bytes) -> bytes:
    """Send bytes as they are (urllib always adds one Host header)."""
    with socket.create_connection(("127.0.0.1", port), timeout=3) as s:
        s.sendall(request)
        chunks = []
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    return b"".join(chunks)


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

    def test_status(self, server, monkeypatch):
        # HC-AI | ticket: VIBE-106
        # collect_status shells out to git and gh, and gh may wait 8s on the
        # network, longer than this client does. Stub the one function that
        # runs commands so the endpoint is tested without spawning anything.
        from codebase_map.mod import status as status_mod

        ran = []

        def fake_run(cmd, cwd, timeout=5.0):
            ran.append(cmd[0])
            return "feat/vibe-106-cbm-mod" if cmd[0] == "git" else None

        monkeypatch.setattr(status_mod, "_run", fake_run)
        with urlopen(f"{server}/api/status", timeout=3) as r:
            assert r.status == 200
            data = json.loads(r.read().decode())
        assert "git" in ran
        assert data["branch"] == "feat/vibe-106-cbm-mod"
        assert data["sprint"] == "VIBE-106"
        # No PR and no snapshot in an empty folder: neutral values, no errors.
        assert data["pr_number"] is None
        assert data["ci_state"] == "unknown"
        assert data["risk_level"] == "unknown"
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


class TestReplayEndpoint:
    def _start(self, repo: Path, projects_root: Path):
        """Start a server that resolves sessions under ``projects_root``."""
        from codebase_map.mod import replay as replay_mod

        port = _free_port()
        # Monkey-patch the default projects dir so test repos resolve to tmp.
        orig = replay_mod.DEFAULT_PROJECTS_DIR
        replay_mod.DEFAULT_PROJECTS_DIR = projects_root
        httpd = make_server(repo, host="127.0.0.1", port=port)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return httpd, thread, f"http://127.0.0.1:{port}", orig

    def _stop(self, httpd, thread, orig):
        from codebase_map.mod import replay as replay_mod

        httpd.shutdown()
        httpd.server_close()
        thread.join(timeout=2)
        replay_mod.DEFAULT_PROJECTS_DIR = orig

    def test_empty_sessions_when_no_project_dir(self, tmp_path: Path):
        repo = tmp_path / "project"
        repo.mkdir()
        projects_root = tmp_path / "projects"
        projects_root.mkdir()
        httpd, thread, base, orig = self._start(repo, projects_root)
        try:
            with urlopen(f"{base}/api/replay/sessions", timeout=3) as r:
                data = json.loads(r.read().decode())
                assert data["count"] == 0
                assert data["sessions"] == []
        finally:
            self._stop(httpd, thread, orig)

    def test_lists_sessions(self, tmp_path: Path):
        from codebase_map.mod.replay import encode_project_dir

        repo = tmp_path / "project"
        repo.mkdir()
        projects_root = tmp_path / "projects"
        sdir = projects_root / encode_project_dir(repo)
        sdir.mkdir(parents=True)
        _write_min_session(sdir / "aaaa.jsonl", "aaaa")

        httpd, thread, base, orig = self._start(repo, projects_root)
        try:
            with urlopen(f"{base}/api/replay/sessions", timeout=3) as r:
                data = json.loads(r.read().decode())
                assert data["count"] == 1
                assert data["sessions"][0]["id"] == "aaaa"
                assert data["sessions"][0]["step_count"] == 3  # user+claude+tool
        finally:
            self._stop(httpd, thread, orig)

    def test_session_steps(self, tmp_path: Path):
        from codebase_map.mod.replay import encode_project_dir

        repo = tmp_path / "project"
        repo.mkdir()
        projects_root = tmp_path / "projects"
        sdir = projects_root / encode_project_dir(repo)
        sdir.mkdir(parents=True)
        _write_min_session(sdir / "abcd.jsonl", "abcd")

        httpd, thread, base, orig = self._start(repo, projects_root)
        try:
            with urlopen(f"{base}/api/replay/sessions/abcd", timeout=3) as r:
                data = json.loads(r.read().decode())
                assert data["id"] == "abcd"
                kinds = [s["kind"] for s in data["steps"]]
                assert kinds == ["user", "claude", "tool"]
                # The file-history-delta should attach to the Claude step.
                claude_step = next(s for s in data["steps"] if s["kind"] == "claude")
                assert claude_step["files_touched"] == ["a.py"]
        finally:
            self._stop(httpd, thread, orig)

    def test_unknown_session_404(self, tmp_path: Path):
        from codebase_map.mod.replay import encode_project_dir

        repo = tmp_path / "project"
        repo.mkdir()
        projects_root = tmp_path / "projects"
        (projects_root / encode_project_dir(repo)).mkdir(parents=True)
        httpd, thread, base, orig = self._start(repo, projects_root)
        try:
            with pytest.raises(HTTPError) as exc:
                urlopen(f"{base}/api/replay/sessions/does-not-exist", timeout=3)
            assert exc.value.code == 404
        finally:
            self._stop(httpd, thread, orig)

    def test_session_id_traversal_blocked(self, tmp_path: Path):
        from codebase_map.mod.replay import encode_project_dir

        repo = tmp_path / "project"
        repo.mkdir()
        projects_root = tmp_path / "projects"
        (projects_root / encode_project_dir(repo)).mkdir(parents=True)
        httpd, thread, base, orig = self._start(repo, projects_root)
        try:
            with pytest.raises(HTTPError) as exc:
                urlopen(f"{base}/api/replay/sessions/..%2fsecret", timeout=3)
            assert exc.value.code == 404
        finally:
            self._stop(httpd, thread, orig)


def _write_min_session(path: Path, uid: str) -> None:
    """Write a 3-event Claude Code session JSONL file."""
    events = [
        {
            "type": "user",
            "timestamp": "2026-11-15T10:00:00Z",
            "message": {"role": "user", "content": "do thing"},
        },
        {
            "type": "assistant",
            "timestamp": "2026-11-15T10:00:05Z",
            "message": {
                "role": "assistant",
                "id": "m1",
                "content": [
                    {"type": "text", "text": "ok"},
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "ls"},
                    },
                ],
            },
        },
        {
            "type": "file-history-delta",
            "timestamp": "2026-11-15T10:00:07Z",
            "messageId": "m1",
            "trackingPath": "a.py",
        },
    ]
    path.write_text("\n".join(json.dumps(e) for e in events))


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


# HC-AI | ticket: VIBE-106
FOREIGN_ORIGIN = "https://example.com"

# (path, bytes that only a served response contains)
PROTECTED = [
    ("/api/replay/sessions", b'"abcd"'),
    ("/api/replay/sessions/abcd", b"do thing"),
    ("/api/graph", b'"fx"'),
    ("/api/snapshots", b'"snap1"'),
]

PANE_FILES = [
    ("/", b"CBM Mod Pane"),
    ("/index.html", b'data-tab="replay"'),
    ("/styles.css", b"status-line"),
    ("/app.js", b"fetchStatus"),
]


def _cors_headers(headers) -> list[str]:
    return [k for k in headers.keys() if k.lower().startswith("access-control-")]


@pytest.fixture(scope="class")
def base(tmp_path_factory):
    """Base URL of one server per class: a graph, a snapshot and a session."""
    from codebase_map.mod import replay as replay_mod
    from codebase_map.mod.replay import encode_project_dir

    tmp_path = tmp_path_factory.mktemp("same-origin")
    repo = tmp_path / "project"
    gdir = repo / "docs" / "function-map"
    gdir.mkdir(parents=True)
    payload = {"project": "fx", "nodes": [{"id": "a"}], "edges": []}
    (gdir / "graph.json").write_text(json.dumps(payload))
    snap_dir = repo / ".codebase-map-cache" / "snapshots"
    snap_dir.mkdir(parents=True)
    _write_min_snapshot(snap_dir / "snap1.json", nodes=2)
    projects_root = tmp_path / "projects"
    sdir = projects_root / encode_project_dir(repo)
    sdir.mkdir(parents=True)
    _write_min_session(sdir / "abcd.jsonl", "abcd")

    port = _free_port()
    httpd = make_server(repo, host="127.0.0.1", port=port)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(replay_mod, "DEFAULT_PROJECTS_DIR", projects_root)
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}"
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=2)


class TestSameOriginOnly:
    """Only this server's own pages may read it: no other site, no other name."""

    @staticmethod
    def _port(base: str) -> int:
        return int(base.rsplit(":", 1)[1])

    # ------ what must keep working ------

    @pytest.mark.parametrize("path,marker", PROTECTED + PANE_FILES)
    def test_served_to_a_plain_request(self, base, path, marker):
        # curl, scripts and a browser's same-origin GET send no Origin.
        status, _, body = _request(f"{base}{path}")
        assert status == 200
        assert marker in body

    @pytest.mark.parametrize("path,marker", PROTECTED + PANE_FILES)
    def test_served_to_own_origin(self, base, path, marker):
        status, _, body = _request(f"{base}{path}", {"Origin": base})
        assert status == 200
        assert marker in body

    @pytest.mark.parametrize("name", ["localhost", "LocalHost", "[::1]"])
    def test_served_under_every_loopback_name(self, base, name):
        # The pane opened as http://localhost:<port>/ instead of 127.0.0.1.
        host = f"{name}:{self._port(base)}"
        for path, marker in PROTECTED + PANE_FILES:
            for headers in ({"Host": host}, {"Host": host, "Origin": f"http://{host}"}):
                status, _, body = _request(f"{base}{path}", headers)
                assert status == 200, (path, headers)
                assert marker in body, (path, headers)

    # ------ what must be refused ------

    @pytest.mark.parametrize(
        "origin",
        [
            FOREIGN_ORIGIN,
            "null",  # sandboxed frame, file:// page
            "",
            "http://localhost:3000",  # another local app
            "http://127.0.0.1",  # right name, port missing
            "https://127.0.0.1:{port}",  # right name and port, other scheme
            "http://localhost:{port}",  # this server, but not the name asked
            "http://127.0.0.1:{port}.example.com",
        ],
    )
    def test_foreign_origin_refused(self, base, origin):
        origin = origin.format(port=self._port(base))
        for path, marker in PROTECTED + PANE_FILES:
            status, headers, body = _request(f"{base}{path}", {"Origin": origin})
            assert status == 403, path
            assert json.loads(body)["reason"] == "origin not allowed", path
            assert marker not in body, path
            assert _cors_headers(headers) == [], path

    @pytest.mark.parametrize(
        "host",
        [
            "attacker.example:{port}",  # DNS rebinding: foreign name, our port
            "attacker.example",
            "127.0.0.1.attacker.example:{port}",
            "localhost.:{port}",
            "127.0.0.1",  # port missing
            "127.0.0.1:1",  # another port
            "0.0.0.0:{port}",
            "",
        ],
    )
    def test_foreign_host_refused(self, base, host):
        port = self._port(base)
        host = host.format(port=port)
        for path, marker in PROTECTED + PANE_FILES:
            status, headers, body = _request(f"{base}{path}", {"Host": host})
            assert status == 403, path
            answer = json.loads(body)
            assert answer["reason"] == "host not allowed", path
            assert f"127.0.0.1:{port}" in answer["allowed_hosts"], path
            assert marker not in body, path
            assert _cors_headers(headers) == [], path

    def test_foreign_host_refused_even_with_matching_origin(self, base):
        # A rebound page is same-origin with itself; Host gives it away.
        host = f"attacker.example:{self._port(base)}"
        headers = {"Host": host, "Origin": f"http://{host}"}
        status, _, body = _request(f"{base}/api/replay/sessions/abcd", headers)
        assert status == 403
        assert b"do thing" not in body

    def test_missing_or_repeated_host_refused(self, base):
        port = self._port(base)
        own = f"Host: 127.0.0.1:{port}\r\n".encode()
        for head in (b"", own + b"Host: attacker.example\r\n", own + own):
            raw = _raw(port, b"GET /api/graph HTTP/1.1\r\n" + head + b"\r\n")
            assert raw.split(b"\r\n", 1)[0].endswith(b"403 Forbidden"), head
            assert b'"fx"' not in raw
        # Control: the same bytes with exactly one good Host are served.
        raw = _raw(port, b"GET /api/graph HTTP/1.1\r\n" + own + b"\r\n")
        assert raw.split(b"\r\n", 1)[0].endswith(b"200 OK")
        assert b'"fx"' in raw

    @pytest.mark.parametrize("site", ["cross-site", "same-site", "Cross-Site", "bogus"])
    def test_cross_site_fetch_refused_on_api(self, base, site):
        # <script src>, <img>, fetch(mode="no-cors"), a link or a frame aimed at
        # the API carry no Origin, but the browser says where they come from.
        for path, marker in PROTECTED:
            for mode in ("no-cors", "navigate"):
                asked = {"Sec-Fetch-Site": site, "Sec-Fetch-Mode": mode}
                status, headers, body = _request(f"{base}{path}", asked)
                assert status == 403, (path, mode)
                assert json.loads(body)["reason"] == "cross-site request"
                assert marker not in body, (path, mode)
                assert _cors_headers(headers) == [], (path, mode)

    @pytest.mark.parametrize("site", ["same-origin", "none"])
    def test_own_fetch_served(self, base, site):
        # The pane's own requests, and an address the user typed.
        for path, marker in PROTECTED + PANE_FILES:
            status, _, body = _request(f"{base}{path}", {"Sec-Fetch-Site": site})
            assert status == 200, path
            assert marker in body, path

    def test_pane_shell_opens_from_a_link_or_frame(self, base):
        # Only the API is closed to other sites. The pane may be linked to or
        # framed; once loaded, its own requests are same-origin.
        asked = {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "navigate"}
        for path, marker in PANE_FILES:
            status, _, body = _request(f"{base}{path}", asked)
            assert status == 200, path
            assert marker in body, path

    def test_refused_request_never_reaches_a_route(self, base, monkeypatch):
        from codebase_map.mod import server as server_mod

        called = []
        monkeypatch.setattr(server_mod, "collect_status", called.append)
        for headers in (
            {"Origin": FOREIGN_ORIGIN},
            {"Host": "attacker.example"},
            {"Sec-Fetch-Site": "cross-site"},
        ):
            status, _, _ = _request(f"{base}/api/status", headers)
            assert status == 403, headers
        assert called == []

    # ------ CORS is gone ------

    def test_no_response_carries_cors_headers(self, base):
        paths = [p for p, _ in PROTECTED + PANE_FILES]
        paths += ["/api/health", "/api/snapshots/nope", "/api/snapshots/snap1/diff"]
        paths += ["/api/replay/sessions/nope", "/no-such-path"]
        for path in paths:
            for method in ("GET", "OPTIONS"):
                for origin in (None, base, FOREIGN_ORIGIN, "null"):
                    headers = {} if origin is None else {"Origin": origin}
                    _, got, _ = _request(f"{base}{path}", headers, method)
                    assert _cors_headers(got) == [], (method, path, origin)

    def test_options_is_not_a_cors_preflight_answer(self, base):
        status, headers, body = _request(f"{base}/api/graph", method="OPTIONS")
        assert status == 204
        assert body == b""
        assert headers["Allow"] == "GET, OPTIONS"
        assert _cors_headers(headers) == []

    def test_preflight_from_another_origin_refused(self, base):
        asked = {"Origin": FOREIGN_ORIGIN, "Access-Control-Request-Method": "GET"}
        status, headers, _ = _request(f"{base}/api/graph", asked, "OPTIONS")
        assert status == 403
        assert _cors_headers(headers) == []


class TestAllowedHosts:
    def test_loopback_names_with_the_bound_port(self):
        assert allowed_hosts("127.0.0.1", 7430) == {
            "127.0.0.1:7430",
            "localhost:7430",
            "[::1]:7430",
        }

    @pytest.mark.parametrize("bind", ["0.0.0.0", "::", ""])
    def test_wildcard_bind_adds_no_name(self, bind):
        assert allowed_hosts(bind, 7430) == allowed_hosts("127.0.0.1", 7430)

    def test_specific_bind_address_is_served_too(self):
        assert "192.168.1.5:7430" in allowed_hosts("192.168.1.5", 7430)
        assert "[2001:db8::5]:7430" in allowed_hosts("2001:db8::5", 7430)
        assert "192.168.1.5:7430" not in allowed_hosts("127.0.0.1", 7430)

    def test_default_port_may_be_left_out(self):
        assert {"localhost", "localhost:80"} <= allowed_hosts("127.0.0.1", 80)
        assert "localhost" not in allowed_hosts("127.0.0.1", 7430)
