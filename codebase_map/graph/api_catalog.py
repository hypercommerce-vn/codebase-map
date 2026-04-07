# HC-AI | ticket: FDD-TOOL-CODEMAP
"""API Catalog auto-gen — extract routes from graph, group by domain.

CM-S2-07: Scan graph for ROUTE nodes, extract HTTP method, path,
auth requirements, params, and response schema. Group by domain
and output as JSON, text, or HTML catalog.

Usage:
    catalog = APICatalog.from_graph(graph)
    catalog.to_text()   # terminal output
    catalog.to_json()   # structured data
    catalog.to_html()   # standalone HTML catalog page
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from codebase_map.graph.models import Graph, Node, NodeType


@dataclass
class APIEndpoint:
    """A single API endpoint extracted from a route node."""

    node_id: str
    name: str
    http_method: str  # GET, POST, PATCH, DELETE, PUT
    path: str  # /api/v1/customers/{id}
    domain: str
    auth: str  # "JWT", "JWT + Admin", "Public", "Unknown"
    file_path: str
    line_start: int
    handler: str  # function name
    params: list[str] = field(default_factory=list)
    return_type: str = ""
    docstring: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "http_method": self.http_method,
            "path": self.path,
            "domain": self.domain,
            "auth": self.auth,
            "file": self.file_path,
            "line": self.line_start,
            "handler": self.handler,
            "params": self.params,
            "return_type": self.return_type,
            "docstring": self.docstring,
        }


# HC-AI | ticket: FDD-TOOL-CODEMAP
class APICatalog:
    """Build an API catalog from a parsed graph."""

    # Auth decorator patterns
    _AUTH_PATTERNS = {
        "jwt_admin": re.compile(
            r"(admin|superuser|staff|require_admin)", re.IGNORECASE
        ),
        "jwt": re.compile(
            r"(jwt|bearer|require_auth|login_required|current_user|authenticated)",
            re.IGNORECASE,
        ),
        "public": re.compile(r"(public|allow_any|no_auth)", re.IGNORECASE),
    }

    def __init__(self) -> None:
        self.endpoints: list[APIEndpoint] = []
        self.by_domain: dict[str, list[APIEndpoint]] = {}
        self.by_method: dict[str, list[APIEndpoint]] = {}
        self._generated_at: str = ""
        self._project: str = ""

    @classmethod
    def from_graph(cls, graph: Graph) -> APICatalog:
        """Extract all ROUTE nodes from graph and build the catalog."""
        catalog = cls()
        catalog._generated_at = graph.generated_at
        catalog._project = graph.project

        for node in graph.nodes.values():
            if node.node_type != NodeType.ROUTE:
                continue

            endpoint = cls._node_to_endpoint(node)
            if endpoint:
                catalog.endpoints.append(endpoint)

        # Sort by path for stable output
        catalog.endpoints.sort(key=lambda e: (e.domain, e.path, e.http_method))

        # Build indexes
        for ep in catalog.endpoints:
            catalog.by_domain.setdefault(ep.domain, []).append(ep)
            catalog.by_method.setdefault(ep.http_method, []).append(ep)

        return catalog

    @classmethod
    def _node_to_endpoint(cls, node: Node) -> APIEndpoint | None:
        """Convert a ROUTE node to an APIEndpoint."""
        # HTTP method from metadata (set by python_parser)
        http_method = node.metadata.get("http_method", "")
        if not http_method:
            http_method = cls._extract_method_from_decorators(node.decorators)
        if not http_method:
            return None

        # Path extraction from decorator arguments
        path = cls._extract_path_from_decorators(node.decorators)

        # Auth detection
        auth = cls._detect_auth(node.decorators, node.params)

        return APIEndpoint(
            node_id=node.id,
            name=node.name,
            http_method=http_method.upper(),
            path=path or f"/{node.name}",
            domain=node.module_domain,
            auth=auth,
            file_path=node.file_path,
            line_start=node.line_start,
            handler=node.name,
            params=list(node.params),
            return_type=node.return_type,
            docstring=node.docstring[:200] if node.docstring else "",
        )

    @staticmethod
    def _extract_method_from_decorators(decorators: list[str]) -> str:
        """Extract HTTP method from decorator names (fallback)."""
        methods = {"get", "post", "put", "patch", "delete", "head", "options"}
        for dec in decorators:
            parts = dec.lower().split(".")
            for part in parts:
                if part in methods:
                    return part
        return ""

    @staticmethod
    def _extract_path_from_decorators(decorators: list[str]) -> str:
        """Extract URL path from decorator call arguments.

        Decorators may be stored as: 'router.get' or 'router.get("/path")'.
        The parser currently stores names only, so we try to extract from
        the full decorator strings if they contain quotes.
        """
        path_pattern = re.compile(r"""['"]([^'"]*)['"]""")
        for dec in decorators:
            match = path_pattern.search(dec)
            if match:
                candidate = match.group(1)
                # Only accept strings that look like paths
                if candidate.startswith("/") or "{" in candidate:
                    return candidate
        return ""

    @classmethod
    def _detect_auth(cls, decorators: list[str], params: list[str]) -> str:
        """Detect auth requirements from decorators and params."""
        combined = " ".join(decorators) + " " + " ".join(params)

        if cls._AUTH_PATTERNS["jwt_admin"].search(combined):
            return "JWT + Admin"
        if cls._AUTH_PATTERNS["jwt"].search(combined):
            return "JWT"
        if cls._AUTH_PATTERNS["public"].search(combined):
            return "Public"
        return "Unknown"

    @property
    def total_endpoints(self) -> int:
        return len(self.endpoints)

    @property
    def domain_count(self) -> int:
        return len(self.by_domain)

    def filter(
        self,
        method: str = "",
        domain: str = "",
        path_contains: str = "",
    ) -> list[APIEndpoint]:
        """Filter endpoints by method, domain, or path substring."""
        results = list(self.endpoints)
        if method:
            results = [e for e in results if e.http_method == method.upper()]
        if domain:
            results = [e for e in results if e.domain == domain]
        if path_contains:
            pc = path_contains.lower()
            results = [e for e in results if pc in e.path.lower()]
        return results

    def to_dict(self) -> dict[str, Any]:
        """Serialize full catalog to dict."""
        return {
            "project": self._project,
            "generated_at": self._generated_at,
            "total_endpoints": self.total_endpoints,
            "domain_count": self.domain_count,
            "by_method": {m: len(eps) for m, eps in sorted(self.by_method.items())},
            "by_domain": {d: len(eps) for d, eps in sorted(self.by_domain.items())},
            "endpoints": [e.to_dict() for e in self.endpoints],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def to_text(self) -> str:
        """Human-readable catalog for terminal output."""
        lines = [
            f"=== API Catalog: {self._project} ===",
            f"Generated: {self._generated_at}",
            f"Total endpoints: {self.total_endpoints}",
            f"Domains: {self.domain_count}",
            "",
            "By method:",
        ]
        for method, eps in sorted(self.by_method.items()):
            lines.append(f"  {method:8s} {len(eps):4d}")

        lines.append("")
        lines.append("Endpoints by domain:")
        for domain in sorted(self.by_domain.keys()):
            eps = self.by_domain[domain]
            lines.append(f"\n  {domain} — {len(eps)} endpoint(s):")
            for ep in eps:
                auth_tag = f"[{ep.auth}]" if ep.auth != "Unknown" else ""
                lines.append(f"    {ep.http_method:7s} {ep.path:40s} {auth_tag}")
                lines.append(
                    f"             → {ep.handler} " f"({ep.file_path}:{ep.line_start})"
                )

        return "\n".join(lines)

    def to_html(self) -> str:
        """Generate a standalone HTML catalog page."""
        rows = []
        for domain in sorted(self.by_domain.keys()):
            eps = self.by_domain[domain]
            rows.append(
                f'<h2 class="api-group">{_escape(domain)} '
                f'<span class="count">{len(eps)} endpoints</span></h2>'
            )
            rows.append('<div class="api-list">')
            for ep in eps:
                method_class = f"http-{ep.http_method}"
                rows.append(
                    f'<div class="api-endpoint">'
                    f'<span class="http-method {method_class}">'
                    f"{_escape(ep.http_method)}</span>"
                    f'<span class="api-path">{_escape(ep.path)}</span>'
                    f'<span class="api-auth">🔒 {_escape(ep.auth)}</span>'
                    f'<div class="api-handler">Handler: '
                    f"<code>{_escape(ep.handler)}</code> "
                    f'<span class="api-file">{_escape(ep.file_path)}:'
                    f"{ep.line_start}</span></div>"
                    f"</div>"
                )
            rows.append("</div>")

        body = "\n".join(rows)
        return _HTML_TEMPLATE.format(
            project=_escape(self._project),
            generated_at=_escape(self._generated_at),
            total=self.total_endpoints,
            domains=self.domain_count,
            body=body,
        )


def _escape(value: str) -> str:
    """Minimal HTML escape."""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# HC-AI | ticket: FDD-TOOL-CODEMAP
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>API Catalog — {project}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #f8fafc; color: #0f172a; margin: 0; padding: 20px; }}
header {{ background: white; padding: 20px; border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0,0,0,.06); margin-bottom: 20px; }}
header h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
header .stats {{ display: flex; gap: 20px; color: #475569; font-size: 14px; }}
header .stats span strong {{ color: #0f172a; font-size: 18px; }}
.api-group {{ margin-top: 24px; font-size: 18px;
              padding: 8px 12px; background: white; border-radius: 6px;
              border-left: 4px solid #6366f1; }}
.api-group .count {{ color: #94a3b8; font-size: 13px; font-weight: normal; }}
.api-list {{ display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }}
.api-endpoint {{ background: white; padding: 12px 16px; border-radius: 6px;
                 border: 1px solid #e2e8f0; display: grid;
                 grid-template-columns: 80px 1fr auto; gap: 12px;
                 align-items: center; }}
.http-method {{ font-weight: 700; font-size: 12px; padding: 4px 8px;
                border-radius: 4px; text-align: center; color: white; }}
.http-GET {{ background: #15803d; }}
.http-POST {{ background: #1d4ed8; }}
.http-PATCH {{ background: #b45309; }}
.http-PUT {{ background: #7c3aed; }}
.http-DELETE {{ background: #b91c1c; }}
.api-path {{ font-family: 'SF Mono', Menlo, monospace; font-size: 14px;
             color: #0f172a; }}
.api-auth {{ color: #64748b; font-size: 12px; }}
.api-handler {{ grid-column: 1 / -1; color: #64748b; font-size: 12px;
                margin-top: 4px; padding-top: 6px;
                border-top: 1px dashed #e2e8f0; }}
.api-handler code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 3px;
                     color: #0f172a; }}
.api-file {{ margin-left: 8px; color: #94a3b8; }}
</style>
</head>
<body>
<header>
  <h1>🗺️ API Catalog — {project}</h1>
  <div class="stats">
    <span><strong>{total}</strong> endpoints</span>
    <span><strong>{domains}</strong> domains</span>
    <span>Generated: {generated_at}</span>
  </div>
</header>
{body}
</body>
</html>
"""
