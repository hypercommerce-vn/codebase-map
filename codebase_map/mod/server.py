# HC-AI | ticket: VIBE-105
"""Local HTTP server for the CBM Mod.

Routes:

    GET /api/health         {"ok": true}
    GET /api/status         status aggregator JSON
    GET /api/graph          graph.json (404 if not generated yet)
    GET /                   the pane shell (index.html)
    GET /<asset>            pane assets (app.js, styles.css) — same dir only

Binds to 127.0.0.1 so nothing on the network can reach it, and sends
permissive CORS headers so the Claude Code pane (rendered from another
origin, e.g. a devtools iframe) can fetch /api/* when the mod is enabled.
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

from codebase_map.mod.status import collect_status

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7430

PANE_DIR = Path(__file__).parent / "pane"

# Candidate locations for the generated graph, searched in order.
GRAPH_CANDIDATES = [
    "docs/function-map/graph.json",
    "graph.json",
    ".codebase-map/graph.json",
]

log = logging.getLogger("codebase_map.mod.server")


def _resolve_graph(repo: Path) -> Optional[Path]:
    for rel in GRAPH_CANDIDATES:
        p = repo / rel
        if p.is_file():
            return p
    return None


class _Handler(BaseHTTPRequestHandler):
    repo_root: Path = Path(".")
    pane_dir: Path = PANE_DIR

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
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
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
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
