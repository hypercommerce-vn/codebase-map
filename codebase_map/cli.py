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
    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-02: Incremental cache flag
    gen.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable incremental cache, force full re-parse",
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
    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-10: Sprint metric recording
    diff_p.add_argument(
        "--record-metric",
        default="",
        metavar="PR_NUMBER",
        help="Record this diff as PR impact metric (CM-S2-10)",
    )
    diff_p.add_argument(
        "--metric-threshold",
        type=int,
        default=50,
        help="Impact threshold for high risk classification",
    )

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # api-catalog — generate API catalog (CM-S2-07)
    api_p = sub.add_parser(
        "api-catalog", help="Extract API routes and generate catalog"
    )
    api_p.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )
    api_p.add_argument(
        "-o",
        "--output",
        default="",
        help="Output file (default: print to stdout)",
    )
    api_p.add_argument(
        "--format",
        choices=["text", "json", "html"],
        default="text",
        help="Output format",
    )
    api_p.add_argument("--method", default="", help="Filter by HTTP method")
    api_p.add_argument("--domain", default="", help="Filter by domain")
    api_p.add_argument("--path", default="", help="Filter by path substring")

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # coverage — test coverage overlay (CM-S2-03)
    cov_p = sub.add_parser("coverage", help="Overlay test coverage on graph nodes")
    cov_p.add_argument(
        "coverage_file",
        nargs="?",
        default="coverage.json",
        help="Path to pytest-cov JSON report (default: coverage.json)",
    )
    cov_p.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )
    cov_p.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # check-staleness — graph age alert (CM-S2-11)
    stale_p = sub.add_parser(
        "check-staleness", help="Check if graph.json is stale (CM-S2-11)"
    )
    stale_p.add_argument(
        "-f",
        "--file",
        default="docs/function-map/graph.json",
        help="Path to graph.json",
    )
    stale_p.add_argument(
        "--warn-days", type=int, default=3, help="Warning threshold in days"
    )
    stale_p.add_argument(
        "--alert-days", type=int, default=7, help="Alert threshold in days"
    )
    stale_p.add_argument(
        "--notify",
        action="store_true",
        help="Send Telegram notification on alert (uses env vars)",
    )
    stale_p.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
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
    elif args.command == "coverage":
        return _cmd_coverage(args)
    elif args.command == "api-catalog":
        return _cmd_api_catalog(args)
    elif args.command == "check-staleness":
        return _cmd_check_staleness(args)

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
    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-02: Incremental cache support
    use_cache = not getattr(args, "no_cache", False)
    builder = GraphBuilder(config, use_cache=use_cache)
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

    # Print cache stats
    cs = builder.cache_stats
    if cs.total_files > 0:
        build_ms = graph.metadata.get("build_time_ms", 0)
        print(f"  Build time: {build_ms}ms")
        print(
            f"  Cache: {cs.cached_files}/{cs.total_files} files cached "
            f"({cs.cache_hit_rate:.0f}% hit rate), "
            f"{cs.parsed_files} re-parsed"
        )
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

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-10: Record sprint metric if requested
    if getattr(args, "record_metric", ""):
        from codebase_map.graph.metrics import MetricStore

        cache_dir = project_root / ".codebase-map-cache"
        store = MetricStore.load(cache_dir, threshold=args.metric_threshold)
        metric = store.record(
            pr_number=args.record_metric,
            ref=args.ref,
            changed_files=len(result.changed_files),
            changed_nodes=len(result.changed_nodes),
            impact_zone=len(result.impacted_nodes),
        )
        store.save()
        print(
            f"\n[METRIC] PR #{metric.pr_number} recorded: "
            f"impact={metric.impact_zone} risk={metric.risk} "
            f"(threshold={store.threshold})"
        )

    return 0


# HC-AI | ticket: FDD-TOOL-CODEMAP
def _cmd_coverage(args: argparse.Namespace) -> int:
    """Test coverage overlay — map coverage data to graph nodes (CM-S2-03)."""
    import json as json_mod

    from codebase_map.graph.coverage import CoverageOverlay
    from codebase_map.graph.query import QueryEngine

    graph_path = Path(args.file)
    if not graph_path.exists():
        print(f"[ERROR] Graph file not found: {graph_path}")
        print("Run 'codebase-map generate' first to create the graph.")
        return 1

    coverage_path = Path(args.coverage_file)
    if not coverage_path.exists():
        print(f"[ERROR] Coverage file not found: {coverage_path}")
        print("Generate with: pytest --cov --cov-report=json")
        return 1

    engine = QueryEngine.from_json(str(graph_path))
    overlay = CoverageOverlay.from_json(str(coverage_path))

    stats = overlay.apply(engine.graph)

    if args.json_output:
        print(json_mod.dumps(stats, indent=2))
    else:
        print(overlay.summary_text(engine.graph))

    return 0


# HC-AI | ticket: FDD-TOOL-CODEMAP
def _cmd_api_catalog(args: argparse.Namespace) -> int:
    """Generate API catalog from graph routes (CM-S2-07)."""
    from codebase_map.graph.api_catalog import APICatalog
    from codebase_map.graph.query import QueryEngine

    graph_path = Path(args.file)
    if not graph_path.exists():
        print(f"[ERROR] Graph file not found: {graph_path}")
        print("Run 'codebase-map generate' first to create the graph.")
        return 1

    engine = QueryEngine.from_json(str(graph_path))
    catalog = APICatalog.from_graph(engine.graph)

    # Apply filters by rebuilding endpoint list
    if args.method or args.domain or args.path:
        filtered = catalog.filter(
            method=args.method, domain=args.domain, path_contains=args.path
        )
        catalog.endpoints = filtered
        catalog.by_domain = {}
        catalog.by_method = {}
        for ep in filtered:
            catalog.by_domain.setdefault(ep.domain, []).append(ep)
            catalog.by_method.setdefault(ep.http_method, []).append(ep)

    # Render
    if args.format == "json":
        output = catalog.to_json()
    elif args.format == "html":
        output = catalog.to_html()
    else:
        output = catalog.to_text()

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(
            f"[OK] API catalog exported: {out_path} "
            f"({catalog.total_endpoints} endpoints)"
        )
    else:
        print(output)

    return 0


# HC-AI | ticket: FDD-TOOL-CODEMAP
def _cmd_check_staleness(args: argparse.Namespace) -> int:
    """Staleness alert — warn if graph.json is too old (CM-S2-11)."""
    import json as json_mod
    import os
    from datetime import datetime, timezone
    from urllib import error as urllib_error
    from urllib import request as urllib_request

    graph_path = Path(args.file)
    if not graph_path.exists():
        print(f"[ERROR] Graph file not found: {graph_path}")
        return 1

    try:
        data = json_mod.loads(graph_path.read_text(encoding="utf-8"))
    except (OSError, json_mod.JSONDecodeError) as e:
        print(f"[ERROR] Cannot read graph: {e}")
        return 1

    generated_at = data.get("generated_at", "")
    project = data.get("project", "unknown")
    n_nodes = len(data.get("nodes", []))
    n_edges = len(data.get("edges", []))

    if not generated_at:
        print("[ERROR] graph.json missing 'generated_at' field")
        return 1

    try:
        gen_dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
    except ValueError:
        print(f"[ERROR] Invalid generated_at: {generated_at}")
        return 1

    now = datetime.now(timezone.utc)
    if gen_dt.tzinfo is None:
        gen_dt = gen_dt.replace(tzinfo=timezone.utc)
    days_elapsed = (now - gen_dt).days

    if days_elapsed >= args.alert_days:
        status = "alert"
        icon = "🔴"
    elif days_elapsed >= args.warn_days:
        status = "warning"
        icon = "🟡"
    else:
        status = "fresh"
        icon = "🟢"

    payload = {
        "project": project,
        "generated_at": generated_at,
        "days_elapsed": days_elapsed,
        "status": status,
        "warn_days": args.warn_days,
        "alert_days": args.alert_days,
        "nodes": n_nodes,
        "edges": n_edges,
    }

    if args.json_output:
        print(json_mod.dumps(payload, indent=2))
    else:
        print(f"{icon} Codebase Map Staleness — {project}")
        print(f"  Generated: {generated_at}")
        print(f"  Age: {days_elapsed} days ({status})")
        print(f"  Stats: {n_nodes} nodes · {n_edges} edges")
        print(f"  Thresholds: warn={args.warn_days}d · alert={args.alert_days}d")

    # Telegram notification on alert
    if args.notify and status == "alert":
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            text = (
                f"🔴 *Codebase Map Stale*\n"
                f"Project: `{project}`\n"
                f"Age: *{days_elapsed} days* (alert ≥ {args.alert_days})\n"
                f"Generated: {generated_at}\n"
                f"Stats: {n_nodes} nodes · {n_edges} edges\n"
                f"Run `codebase-map generate` to refresh."
            )
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            body = json_mod.dumps(
                {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
            ).encode()
            req = urllib_request.Request(
                url, data=body, headers={"Content-Type": "application/json"}
            )
            try:
                urllib_request.urlopen(req, timeout=10)
                print("[NOTIFY] Telegram alert sent")
            except urllib_error.URLError as e:
                print(f"[NOTIFY] Telegram failed: {e}")
        else:
            print("[NOTIFY] TELEGRAM_BOT_TOKEN/CHAT_ID not set, skipping")

    # Exit code: 0 fresh, 1 warning, 2 alert
    if status == "alert":
        return 2
    if status == "warning":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
