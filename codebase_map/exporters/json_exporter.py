# HC-AI | ticket: FDD-TOOL-CODEMAP
"""JSON Exporter — structured output for programmatic access."""
from __future__ import annotations

import json
from pathlib import Path

from codebase_map.graph.models import Graph


def export_json(graph: Graph, output_path: str | Path) -> Path:
    """Export graph to JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = graph.to_dict()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    n = len(graph.nodes)
    e = len(graph.edges)
    print(f"[OK] JSON exported: {path} ({n} nodes, {e} edges)")
    return path
