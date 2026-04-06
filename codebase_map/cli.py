# HC-AI | ticket: FDD-TOOL-CODEMAP
"""CLI entry point — codebase-map generate|query|impact|summary."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codebase_map import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="codebase-map",
        description="Function dependency graph generator for any codebase.",
    )
    parser.add_argument(
        "--version", action="version", version=f"codebase-map {__version__}"
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen = sub.add_parser("generate", help="Generate function map from source code")
    gen.add_argument(
        "-c",
        "--config",
        default="codebase-map.yaml",
        help="Path to config file (default: codebase-map.yaml)",
    )

    # query
    q = sub.add_parser("query", help="Query a function/class by name")
    q.add_argument("name", help="Function or class name to search")
    q.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )
    q.add_argument("-d", "--depth", type=int, default=3, help="Impact analysis depth")

    # impact
    imp = sub.add_parser("impact", help="Show impact zone for a function")
    imp.add_argument("name", help="Function or class name")
    imp.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )
    imp.add_argument("-d", "--depth", type=int, default=3, help="Analysis depth")

    # summary
    s = sub.add_parser("summary", help="Show graph summary statistics")
    s.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )

    # search
    srch = sub.add_parser("search", help="Search nodes by keyword")
    srch.add_argument("keyword", help="Search keyword")
    srch.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # diff — git diff integration (CM-S2-01)
    diff_p = sub.add_parser("diff", help="Show changed + impacted nodes from git diff")
    diff_p.add_argument(
        "ref",
        nargs="?",
        default="HEAD~1",
        help="Git ref to diff against (default: HEAD~1)",
    )
    diff_p.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )
    diff_p.add_argument(
        "-d", "--depth", type=int, default=3, help="Impact analysis depth"
    )
    diff_p.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )
    diff_p.add_argument(
        "-c",
        "--config",
        default="codebase-map.yaml",
        help="Config file (for project root detection)",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "generate":
        return _cmd_generate(args)
    elif args.command == "query":
        return _cmd_query(args)
    elif args.command == "impact":
        return _cmd_impact(args)
    elif args.command == "summary":
        return _cmd_summary(args)
    elif args.command == "search":
        return _cmd_search(args)
    elif args.command == "diff":
        return _cmd_diff(args)

    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    from codebase_map.config import Config
    from codebase_map.exporters.html_exporter import export_html
    from codebase_map.exporters.json_exporter import export_json
    from codebase_map.graph.builder import GraphBuilder

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"[ERROR] Config not found: {config_path}")
        print("Create a codebase-map.yaml or use --config to specify path.")
        return 1

    config = Config.from_yaml(config_path)
    builder = GraphBuilder(config)
    graph = builder.build()

    output_dir = config.project_root / config.output.dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if "json" in config.output.formats:
        export_json(graph, output_dir / "graph.json")

    if "html" in config.output.formats:
        export_html(graph, output_dir / "index.html")

    n_nodes = len(graph.nodes)
    n_edges = len(graph.edges)
    print(f"\n[DONE] {graph.project} — {n_nodes} nodes, {n_edges} edges")
    stats = graph.stats()
    print(f"  Layers: {stats['by_layer']}")
    print(f"  Domains: {stats['by_domain']}")
    return 0


def _cmd_query(args: argparse.Namespace) -> int:
    from codebase_map.graph.query import QueryEngine

    engine = QueryEngine.from_json(args.file)
    result = engine.query_node(args.name, depth=args.depth)
    if not result:
        print(f"[NOT FOUND] No node matching: {args.name}")
        return 1
    print(result.to_text())
    return 0


def _cmd_impact(args: argparse.Namespace) -> int:
    from codebase_map.graph.query import QueryEngine

    engine = QueryEngine.from_json(args.file)
    affected = engine.impact(args.name, depth=args.depth)
    if not affected:
        print(f"[OK] No impact found for: {args.name}")
        return 0
    print(f"=== Impact Zone for '{args.name}' ({len(affected)} affected) ===")
    for a in affected:
        print(f"  !! {a}")
    return 0


def _cmd_summary(args: argparse.Namespace) -> int:
    from codebase_map.graph.query import QueryEngine

    engine = QueryEngine.from_json(args.file)
    print(engine.summary())
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    from codebase_map.graph.query import QueryEngine

    engine = QueryEngine.from_json(args.file)
    results = engine.search(args.keyword)
    if not results:
        print(f"[NOT FOUND] No nodes matching: {args.keyword}")
        return 1
    print(f"=== Search: '{args.keyword}' ({len(results)} results) ===")
    for node in results[:50]:
        ntype = node.node_type.value
        layer = node.layer.value
        loc = f"{node.file_path}:{node.line_start}"
        print(f"  {node.name:30s} {ntype:10s} {layer:12s} {loc}")
    if len(results) > 50:
        print(f"  ... and {len(results) - 50} more")
    return 0


# HC-AI | ticket: FDD-TOOL-CODEMAP
def _cmd_diff(args: argparse.Namespace) -> int:
    """Git diff integration — show changed + impacted nodes (CM-S2-01)."""
    from codebase_map.graph.diff import DiffAnalyzer
    from codebase_map.graph.query import QueryEngine

    graph_path = Path(args.file)
    if not graph_path.exists():
        print(f"[ERROR] Graph file not found: {graph_path}")
        print("Run 'codebase-map generate' first to create the graph.")
        return 1

    engine = QueryEngine.from_json(str(graph_path))

    # Detect project root from config or graph file location
    config_path = Path(args.config)
    if config_path.exists():
        project_root = config_path.parent
    else:
        # Fallback: assume graph is in docs/function-map/ under project root
        project_root = graph_path.parent.parent.parent
        if not (project_root / ".git").exists():
            project_root = Path.cwd()

    analyzer = DiffAnalyzer(engine.graph, project_root=project_root)
    result = analyzer.analyze(ref=args.ref, depth=args.depth)

    if not result.changed_files:
        print(f"[OK] No changed Python files found for: {args.ref}")
        return 0

    if args.json_output:
        print(result.to_json())
    else:
        print(result.to_text())

    return 0


if __name__ == "__main__":
    sys.exit(main())
