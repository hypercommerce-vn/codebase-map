# HC-AI | ticket: MEM-M3-03
"""Mermaid diagram generator for onboarding reports.

Generates Mermaid syntax for: architecture overview, domain map,
and call flow diagrams from vault patterns + graph data.

Design decision D-M3-03: Mermaid is OPTIONAL.
If not available, diagrams are skipped with a note.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("codebase-memory.mermaid")


def generate_architecture_diagram(
    layers: dict[str, int],
    domains: list[str] | None = None,
) -> str:
    """Generate Mermaid architecture layer diagram.

    Args:
        layers: Layer name → node count mapping.
        domains: Optional list of domain names.

    Returns:
        Mermaid diagram string (graph TD format).
    """
    lines = ["graph TD"]

    # Sort layers by count (largest first)
    sorted_layers = sorted(layers.items(), key=lambda x: -x[1])

    for i, (layer, count) in enumerate(sorted_layers):
        node_id = f"L{i}"
        lines.append(f"    {node_id}[{layer} — {count} nodes]")

    # Connect layers top-to-bottom
    for i in range(len(sorted_layers) - 1):
        lines.append(f"    L{i} --> L{i + 1}")

    # Add domains as subgraph if available
    if domains and len(domains) > 1:
        lines.append("")
        lines.append("    subgraph Domains")
        for j, domain in enumerate(domains[:8]):
            lines.append(f"        D{j}[{domain}]")
        lines.append("    end")

    return "\n".join(lines)


def generate_domain_map(
    edges: list[dict[str, str]],
    nodes: list[dict[str, Any]] | None = None,
) -> str:
    """Generate Mermaid domain relationship diagram.

    Shows connections between domains based on cross-domain edges.

    Args:
        edges: List of edge dicts with source_name/target_name.
        nodes: Optional list of node dicts for domain extraction.
    """
    # Build domain-to-domain relationships
    domain_edges: dict[tuple[str, str], int] = {}
    node_domains: dict[str, str] = {}

    if nodes:
        for n in nodes:
            name = n.get("name", "")
            fpath = n.get("file_path", "")
            domain = _extract_domain(fpath)
            if domain:
                node_domains[name] = domain

    for e in edges:
        src = e.get("source_name", "")
        tgt = e.get("target_name", "")
        src_domain = node_domains.get(src, "")
        tgt_domain = node_domains.get(tgt, "")

        if src_domain and tgt_domain and src_domain != tgt_domain:
            key = (src_domain, tgt_domain)
            domain_edges[key] = domain_edges.get(key, 0) + 1

    if not domain_edges:
        return "graph LR\n    A[No cross-domain dependencies detected]"

    lines = ["graph LR"]
    seen_domains: set[str] = set()

    for (src, tgt), count in sorted(domain_edges.items(), key=lambda x: -x[1]):
        if src not in seen_domains:
            lines.append(f"    {_safe_id(src)}[{src}]")
            seen_domains.add(src)
        if tgt not in seen_domains:
            lines.append(f"    {_safe_id(tgt)}[{tgt}]")
            seen_domains.add(tgt)
        lines.append(f"    {_safe_id(src)} -->|{count} calls| {_safe_id(tgt)}")

    return "\n".join(lines)


def generate_call_flow(
    function_name: str,
    callers: list[str],
    callees: list[str],
) -> str:
    """Generate Mermaid call flow diagram for a single function.

    Shows: callers → function → callees.
    """
    lines = ["graph LR"]
    fid = _safe_id(function_name)
    lines.append(f"    {fid}[{function_name}]")
    lines.append(f"    style {fid} fill:#6366f1,color:#fff")

    for c in callers[:5]:
        cid = _safe_id(c)
        lines.append(f"    {cid}[{c}] --> {fid}")

    for c in callees[:5]:
        cid = _safe_id(c)
        lines.append(f"    {fid} --> {cid}[{c}]")

    return "\n".join(lines)


def wrap_mermaid_block(diagram: str) -> str:
    """Wrap diagram in Markdown code block."""
    return f"```mermaid\n{diagram}\n```"


def _extract_domain(file_path: str) -> str:
    """Extract domain from file path."""
    if not file_path or "/" not in file_path:
        return ""
    return file_path.split("/")[0]


def _safe_id(name: str) -> str:
    """Convert name to safe Mermaid node ID."""
    return name.replace(".", "_").replace("/", "_").replace("-", "_")
