# HC-AI | ticket: VIBE-106
"""Local HTTP server for the CBM Mod.

Routes:

    GET /api/health                       {"ok": true}
    GET /api/status                       status aggregator JSON
    GET /api/graph                        graph.json (404 if not generated yet)
    GET /api/snapshots                    list of stored snapshots
    GET /api/snapshots/<id>               one snapshot (full graph JSON)
    GET /api/snapshots/<id>/diff?base=<y> diff this snapshot vs base (JSON)
    GET /api/replay/sessions              list Claude Code sessions for this repo
    GET /api/replay/sessions/<id>         ordered replay steps for one session
    GET /                                 the pane shell (index.html)
    GET /<asset>                          pane assets — same dir only

Who may call it
---------------
The API returns things that must stay on this machine: the repo's Claude
Code conversation transcripts (/api/replay/*), the code graph and its
snapshots. There is no login, so every request is checked before a route
runs and gets 403 unless all of these hold:

* ``Host`` is one of this server's own names with the bound port:
  ``127.0.0.1``, ``localhost`` or ``[::1]`` (plus the address passed to
  ``--host`` when that is one specific address). A browser sends the name
  it was told to open, so a page that reaches this socket under a foreign
  name (DNS rebinding) is refused.
* ``Origin``, when the client sends one, is ``http://`` + that ``Host``,
  i.e. the request comes from a page this server served. Browsers add
  ``Origin`` to cross-origin reads, so those are refused.
* On /api/*, ``Sec-Fetch-Site``, when the client sends one, is
  ``same-origin`` or ``none`` (the user typed the address). Browsers attach
  it to say where a request comes from, which catches the cross-site
  requests that carry no ``Origin``: a ``<script>`` or ``<img>`` tag,
  ``fetch(..., {mode: "no-cors"})``, a link or frame aimed at an API URL.
  The pane shell and its assets stay reachable from a link or a frame.

No ``Access-Control-Allow-*`` header is sent, so a browser never hands a
response to a page from another origin either. The pane does not need one:
index.html, its assets and /api/* all come from this one origin, and
app.js only uses relative URLs.

Binding to 127.0.0.1 (the default) keeps other machines out. It does not
keep out a web page open in a browser on this machine; the checks above
do. They are not authentication: any local program can still call the API,
and so can the network if you bind to a non-loopback address.
"""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import signal
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote

from codebase_map.mod.status import collect_status

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7430

# HC-AI | ticket: VIBE-106
# Names under which a browser on this machine reaches the loopback
# interface. A request whose ``Host`` is anything else was addressed to some
# other name that merely resolves here.
_LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "[::1]")
_WILDCARD_BINDS = ("", "0.0.0.0", "::")
# ``Sec-Fetch-Site`` values the API answers to. "" stands for no header:
# curl, scripts and browsers too old to send it.
_OWN_FETCH_SITES = ("", "same-origin", "none")

PANE_DIR = Path(__file__).parent / "pane"

# Candidate locations for the generated graph, searched in order.
GRAPH_CANDIDATES = [
    "docs/function-map/graph.json",
    "graph.json",
    ".codebase-map/graph.json",
]

# Candidate locations for snapshot cache dir, searched in order.
SNAPSHOT_CANDIDATES = [
    ".codebase-map-cache/snapshots",
    ".codebase-map/snapshots",
]

log = logging.getLogger("codebase_map.mod.server")


def _resolve_graph(repo: Path) -> Optional[Path]:
    for rel in GRAPH_CANDIDATES:
        p = repo / rel
        if p.is_file():
            return p
    return None


def _resolve_snapshot_dir(repo: Path) -> Optional[Path]:
    for rel in SNAPSHOT_CANDIDATES:
        p = repo / rel
        if p.is_dir():
            return p
    return None


def _snapshot_by_id(snap_dir: Path, snap_id: str) -> Optional[Path]:
    """Resolve a snapshot id (filename stem) to a file path.

    Rejects traversal and only accepts a bare `.json` under ``snap_dir``.
    """
    if "/" in snap_id or "\\" in snap_id or ".." in snap_id:
        return None
    p = (snap_dir / f"{snap_id}.json").resolve()
    try:
        p.relative_to(snap_dir.resolve())
    except ValueError:
        return None
    if not p.is_file():
        return None
    return p


# HC-AI | ticket: VIBE-106
def allowed_hosts(bind_host: str, port: int) -> frozenset[str]:
    """Return the ``Host`` header values (lower-case) the server answers to.

    Always the loopback names with the bound port. When the socket is bound
    to one specific address (``--host 192.168.1.5``), that address counts
    too, since the operator chose to serve it. A wildcard bind adds nothing:
    it names no address a browser could be told to open.
    """
    names = set(_LOOPBACK_HOSTS)
    if bind_host not in _WILDCARD_BINDS:
        names.add(f"[{bind_host}]" if ":" in bind_host else bind_host)
    hosts = {f"{name}:{port}" for name in names}
    if port == 80:
        hosts |= names  # clients leave the default port out
    return frozenset(h.lower() for h in hosts)


class _Handler(BaseHTTPRequestHandler):
    repo_root: Path = Path(".")
    pane_dir: Path = PANE_DIR

    # HC-AI | ticket: VIBE-106
    def _gate(self) -> bool:
        """Answer 403 unless the request is this server's own business.

        That means: addressed to one of the server's own names, and not sent
        by a page from another origin (see "Who may call it" in the module
        docstring). Returns True when the request may go on to a route.
        """
        bind_host, port = self.server.server_address[:2]
        allowed = allowed_hosts(bind_host, port)
        hosts = self.headers.get_all("Host") or []
        host = hosts[0].strip().lower() if len(hosts) == 1 else ""
        origin = self.headers.get("Origin")
        site = (self.headers.get("Sec-Fetch-Site") or "").strip().lower()
        if host not in allowed:
            reason = "host not allowed"
        elif origin is not None and origin.strip().lower() != f"http://{host}":
            reason = "origin not allowed"
        elif site not in _OWN_FETCH_SITES and self.path.startswith("/api/"):
            reason = "cross-site request"
        else:
            return True
        log.warning(
            "refused %s %r: %s (Host: %r, Origin: %r, Sec-Fetch-Site: %r)",
            self.command,
            self.path,
            reason,
            ", ".join(hosts) or None,
            origin,
            site or None,
        )
        self._json(
            403,
            {"error": "forbidden", "reason": reason, "allowed_hosts": sorted(allowed)},
        )
        return False

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        # No Access-Control-* headers: nothing here is for other origins.
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, data: dict) -> None:
        self._send(
            status,
            json.dumps(data, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _serve_pane_file(self, filename: str) -> bool:
        """Serve a single file from the pane dir. Returns True if served."""
        # No traversal: only allow plain filenames that exist in pane_dir.
        if "/" in filename or ".." in filename or filename.startswith("."):
            return False
        path = (self.pane_dir / filename).resolve()
        try:
            path.relative_to(self.pane_dir.resolve())
        except ValueError:
            return False
        if not path.is_file():
            return False
        ctype, _ = mimetypes.guess_type(path.name)
        ctype = ctype or "application/octet-stream"
        self._send(200, path.read_bytes(), ctype)
        return True

    def do_OPTIONS(self) -> None:  # noqa: N802
        # HC-AI | ticket: VIBE-106
        # A CORS preflight gets no Access-Control-* answer (and 403 from the
        # gate when it names another origin), so the browser never sends the
        # real request.
        if not self._gate():
            return
        self.send_response(204)
        self.send_header("Allow", "GET, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if not self._gate():
            return
        path = self.path.split("?", 1)[0]

        if path == "/api/health":
            self._json(200, {"ok": True})
            return
        if path == "/api/status":
            data = collect_status(self.repo_root)
            self._json(200, data.to_dict())
            return
        if path == "/api/graph":
            gpath = _resolve_graph(self.repo_root)
            if gpath is None:
                self._json(
                    404,
                    {
                        "error": "graph not found",
                        "hint": "run `codebase-map generate` to create it",
                        "searched": GRAPH_CANDIDATES,
                    },
                )
                return
            self._send(200, gpath.read_bytes(), "application/json; charset=utf-8")
            return

        if path == "/api/snapshots":
            self._json(200, self._list_snapshots())
            return

        if path.startswith("/api/snapshots/"):
            self._snapshot_route(path)
            return

        if path == "/api/replay/sessions":
            self._json(200, self._list_replay_sessions())
            return

        if path.startswith("/api/replay/sessions/"):
            self._replay_route(path)
            return

        if path == "/" or path == "/index.html":
            if self._serve_pane_file("index.html"):
                return
            self._json(500, {"error": "pane/index.html missing"})
            return

        # Any other single-segment path: try pane dir
        if path.startswith("/") and path.count("/") == 1:
            if self._serve_pane_file(path[1:]):
                return

        self._json(404, {"error": "not found", "path": path})

    # ------ snapshot routes ------

    def _list_snapshots(self) -> dict:
        snap_dir = _resolve_snapshot_dir(self.repo_root)
        if snap_dir is None:
            return {
                "snapshots": [],
                "hint": (
                    "run `codebase-map generate` to create snapshots "
                    "(stored in .codebase-map-cache/snapshots/)"
                ),
                "searched": SNAPSHOT_CANDIDATES,
            }
        items = []
        for fp in sorted(snap_dir.glob("*.json")):
            try:
                with fp.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            meta = data.get("metadata", {}) or {}
            stats = data.get("stats", {}) or {}
            items.append(
                {
                    "id": fp.stem,
                    "label": meta.get("label") or "unknown",
                    "generated_at": data.get("generated_at")
                    or meta.get("generated_at")
                    or "",
                    "branch": meta.get("branch", "unknown"),
                    "commit_sha": (meta.get("commit_sha") or "")[:7],
                    "nodes": stats.get("total_functions")
                    or stats.get("nodes")
                    or len(data.get("nodes", [])),
                    "edges": stats.get("total_edges")
                    or stats.get("edges")
                    or len(data.get("edges", [])),
                    "size_bytes": fp.stat().st_size,
                }
            )
        # Newest first — sort by generated_at descending.
        items.sort(key=lambda s: s["generated_at"], reverse=True)
        return {"snapshots": items, "count": len(items)}

    def _snapshot_route(self, path: str) -> None:
        # Shape: /api/snapshots/<id>[/diff]
        tail = path[len("/api/snapshots/") :]
        if not tail:
            self._json(404, {"error": "missing snapshot id"})
            return
        parts = tail.split("/", 1)
        snap_id = unquote(parts[0])
        action = parts[1] if len(parts) > 1 else ""

        snap_dir = _resolve_snapshot_dir(self.repo_root)
        if snap_dir is None:
            self._json(404, {"error": "no snapshot cache dir"})
            return
        snap_file = _snapshot_by_id(snap_dir, snap_id)
        if snap_file is None:
            self._json(404, {"error": "snapshot not found", "id": snap_id})
            return

        if action == "":
            self._send(200, snap_file.read_bytes(), "application/json; charset=utf-8")
            return
        if action == "diff":
            query = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            base_id = (query.get("base") or [""])[0]
            if not base_id:
                self._json(400, {"error": "missing ?base=<id> query"})
                return
            base_file = _snapshot_by_id(snap_dir, base_id)
            if base_file is None:
                self._json(404, {"error": "base snapshot not found", "id": base_id})
                return
            self._json(200, self._compute_diff(base_file, snap_file))
            return
        self._json(404, {"error": "unknown snapshot action", "action": action})

    @staticmethod
    def _compute_diff(base_file: Path, current_file: Path) -> dict:
        # Imported lazily so the server module stays cheap to import.
        from codebase_map.graph.diff_formatter import _result_to_dict
        from codebase_map.graph.models import Graph
        from codebase_map.graph.snapshot_diff import SnapshotDiff

        with base_file.open("r", encoding="utf-8") as f:
            base = Graph.from_dict(json.load(f))
        with current_file.open("r", encoding="utf-8") as f:
            current = Graph.from_dict(json.load(f))
        result = SnapshotDiff(base, current).compute()
        return _result_to_dict(result)

    # ------ replay routes (VIBE-106 Day 4) ------

    def _list_replay_sessions(self) -> dict:
        from codebase_map.mod.replay import (
            DEFAULT_PROJECTS_DIR,
            list_sessions,
            project_sessions_dir,
        )

        sessions = list_sessions(self.repo_root)
        return {
            "sessions": [s.to_dict() for s in sessions],
            "count": len(sessions),
            "projects_dir": str(project_sessions_dir(self.repo_root)),
            "default_root": str(DEFAULT_PROJECTS_DIR),
        }

    def _replay_route(self, path: str) -> None:
        from codebase_map.mod.replay import parse_session, project_sessions_dir

        tail = path[len("/api/replay/sessions/") :]
        if not tail:
            self._json(404, {"error": "missing session id"})
            return
        parts = tail.split("/", 1)
        session_id = unquote(parts[0])
        action = parts[1] if len(parts) > 1 else ""

        # Only filename-safe ids are valid session uuids.
        if (
            "/" in session_id
            or "\\" in session_id
            or ".." in session_id
            or session_id.startswith(".")
        ):
            self._json(404, {"error": "invalid session id"})
            return

        sdir = project_sessions_dir(self.repo_root)
        jsonl = sdir / f"{session_id}.jsonl"
        try:
            jsonl_resolved = jsonl.resolve()
            jsonl_resolved.relative_to(sdir.resolve())
        except (OSError, ValueError):
            self._json(404, {"error": "session not found", "id": session_id})
            return
        if not jsonl_resolved.is_file():
            self._json(404, {"error": "session not found", "id": session_id})
            return

        if action == "":
            steps = parse_session(jsonl_resolved)
            self._json(
                200,
                {
                    "id": session_id,
                    "step_count": len(steps),
                    "steps": [s.to_dict() for s in steps],
                },
            )
            return
        self._json(404, {"error": "unknown replay action", "action": action})

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        log.info("%s - %s", self.address_string(), fmt % args)


def make_server(
    repo: Path, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT
) -> ThreadingHTTPServer:
    """Create a configured ThreadingHTTPServer bound to the loopback."""
    handler = type(
        "_BoundHandler",
        (_Handler,),
        {"repo_root": repo.resolve(), "pane_dir": PANE_DIR},
    )
    httpd = ThreadingHTTPServer((host, port), handler)
    return httpd


def serve(
    repo: Path | str = ".",
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Run the server until SIGINT/SIGTERM."""
    repo_path = Path(repo).resolve()
    httpd = make_server(repo_path, host, port)

    def _stop(*_):
        log.info("stopping")
        httpd.shutdown()

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    log.info("CBM Mod server on http://%s:%d (repo=%s)", host, port, repo_path)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="cbm-mod", description="CBM Mod server")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--repo", default=".", help="Repository root")
    parser.add_argument("-v", "--verbose", action="store_true", help="Log requests")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    serve(args.repo, args.host, args.port)
    return 0


if __name__ == "__main__":
    sys.exit(main())
