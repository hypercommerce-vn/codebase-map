# HC-AI | ticket: FDD-TOOL-CODEMAP
"""CLI entry point — codebase-map generate|query|impact|summary."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codebase_map import __version__


def build_parser() -> argparse.ArgumentParser:
    """The command-line parser, separate from running a command."""
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
        default=None,
        help=(
            "Path to a YAML or JSON config file. Default: codebase-map.yaml, "
            "then codebase-map.json; if neither exists the sources are "
            "auto-detected."
        ),
    )
    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-02: Incremental cache flag
    gen.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable incremental cache, force full re-parse",
    )
    # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-04)
    # Unified one-command flow: after generating graph.json, also emit
    # pr_diff.json vs the given git ref so the HTML PR Diff view is baked
    # in automatically. Previously required a separate `codebase-map diff`
    # invocation piped into pr_diff.json.
    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CBM-P1-02: Snapshot label flag for metadata versioning
    gen.add_argument(
        "--label",
        default="",
        metavar="NAME",
        help=(
            "Snapshot label (e.g. 'baseline', 'post-dev'). "
            "Default: auto-generate from branch + SHA + timestamp."
        ),
    )
    gen.add_argument(
        "--diff",
        default="",
        metavar="REF",
        help=(
            "Also bake a PR Diff view against this git ref (e.g. 'main'). "
            "Writes pr_diff.json next to graph.json and auto-loads it in HTML."
        ),
    )
    gen.add_argument(
        "--diff-depth",
        type=int,
        default=3,
        help="Impact analysis depth for --diff (default: 3)",
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

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CBM-P1-04/05: Snapshot management commands
    snap_p = sub.add_parser("snapshots", help="Manage graph snapshots")
    snap_p.add_argument(
        "action",
        choices=["list", "clean"],
        help="Action: 'list' to show snapshots, 'clean' to remove old ones",
    )
    snap_p.add_argument(
        "--keep",
        type=int,
        default=10,
        help="Number of newest snapshots to keep (default: 10, used with 'clean')",
    )
    snap_p.add_argument(
        "-c",
        "--config",
        default="codebase-map.yaml",
        help="Config file (for project root detection)",
    )
    snap_p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON (used with 'list')",
    )

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-103: features, acceptance criteria and evidence
    _add_features_parser(sub)

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CBM-P2-05/06/07/08: Snapshot diff — compare two graph snapshots
    sdiff_p = sub.add_parser(
        "snapshot-diff",
        help="Compare two graph snapshots (dual-snapshot diff engine)",
    )
    sdiff_p.add_argument(
        "--baseline",
        required=True,
        help="Baseline graph file path or snapshot label",
    )
    sdiff_p.add_argument(
        "--current",
        required=True,
        help="Current graph file path or snapshot label",
    )
    sdiff_p.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        dest="output_format",
        help="Output format (default: text)",
    )
    sdiff_p.add_argument(
        "--depth",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Affected callers depth (default: 1, max: 3)",
    )
    sdiff_p.add_argument(
        "--breaking-only",
        action="store_true",
        help="Show only breaking changes (with affected callers)",
    )
    sdiff_p.add_argument(
        "--test-plan",
        action="store_true",
        help="Output suggested test plan grouped by domain",
    )
    sdiff_p.add_argument(
        "-c",
        "--config",
        default="codebase-map.yaml",
        help="Config file (for snapshot dir detection)",
    )

    # HC-AI | ticket: VIBE-106
    # CBM Mod — status line / pane / Claude Replay backend
    mod_p = sub.add_parser(
        "mod",
        help="CBM Mod server for Claude Code pane",
        description=(
            "Run the loopback pane server (Graph · Timeline · Claude "
            "Replay) and manage its opt-in git hooks."
        ),
    )
    mod_sub = mod_p.add_subparsers(dest="mod_cmd", help="Mod subcommand")
    mod_serve = mod_sub.add_parser("serve", help="Run the local Mod server")
    mod_serve.add_argument("--host", default="127.0.0.1", help="Bind host")
    mod_serve.add_argument("--port", type=int, default=7430, help="Bind port")
    mod_serve.add_argument("--repo", default=".", help="Repository root")
    mod_serve.add_argument("-v", "--verbose", action="store_true", help="Log requests")
    mod_status = mod_sub.add_parser("status", help="Print status JSON once and exit")
    mod_status.add_argument("--repo", default=".", help="Repository root")
    # Hook management (opt-in per CEO decision #5).
    mod_enable = mod_sub.add_parser(
        "enable-hooks", help="Install the post-commit snapshot hook"
    )
    mod_enable.add_argument("--repo", default=".", help="Repository root")
    mod_disable = mod_sub.add_parser(
        "disable-hooks", help="Uninstall the post-commit snapshot hook"
    )
    mod_disable.add_argument("--repo", default=".", help="Repository root")
    mod_hooks_status = mod_sub.add_parser(
        "hooks-status", help="Print hook install state as JSON"
    )
    mod_hooks_status.add_argument("--repo", default=".", help="Repository root")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _use_utf8_output()

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
    elif args.command == "snapshots":
        return _cmd_snapshots(args)
    elif args.command == "snapshot-diff":
        return _cmd_snapshot_diff(args)
    elif args.command == "features":
        return _cmd_features(args)
    elif args.command == "mod":
        return _cmd_mod(args)

    return 0


def _cmd_mod(args: argparse.Namespace) -> int:
    # HC-AI | ticket: VIBE-106
    import json as _json
    import logging as _logging

    from codebase_map.mod import collect_status
    from codebase_map.mod import hooks as _hooks
    from codebase_map.mod.server import serve

    if args.mod_cmd == "serve":
        _logging.basicConfig(
            level=_logging.INFO if args.verbose else _logging.WARNING,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        serve(args.repo, args.host, args.port)
        return 0
    if args.mod_cmd == "status":
        data = collect_status(args.repo)
        print(_json.dumps(data.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.mod_cmd == "enable-hooks":
        st = _hooks.enable(Path(args.repo))
        print(_json.dumps(st.to_dict(), indent=2))
        return 0
    if args.mod_cmd == "disable-hooks":
        st = _hooks.disable(Path(args.repo))
        print(_json.dumps(st.to_dict(), indent=2))
        return 0
    if args.mod_cmd == "hooks-status":
        st = _hooks.status(Path(args.repo))
        print(_json.dumps(st.to_dict(), indent=2))
        return 0
    print(
        "[ERROR] Unknown mod subcommand. "
        "Try 'mod serve', 'mod status', 'mod enable-hooks', "
        "'mod disable-hooks', or 'mod hooks-status'."
    )
    return 1


# HC-AI | ticket: FDD-TOOL-CODEMAP
# VIBE-104: output is UTF-8 whatever the platform default is. On Windows a
# redirected stdout uses a legacy code page, and printing a Vietnamese feature
# name to it raises UnicodeEncodeError.
def _use_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        encoding = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None and encoding != "utf8":
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


# HC-AI | ticket: FDD-TOOL-CODEMAP
# VIBE-101: a config file is optional. An explicit -c path must exist; with no
# flag the default file names are tried, then the sources are auto-detected.
_DEFAULT_CONFIG_NAMES = ("codebase-map.yaml", "codebase-map.json")


def _load_generate_config(config_arg: str | None):
    """Return the Config for ``generate``, or None after printing an error."""
    from codebase_map.config import Config

    candidates = [config_arg] if config_arg else list(_DEFAULT_CONFIG_NAMES)
    for candidate in candidates:
        if Path(candidate).exists():
            try:
                return Config.from_file(candidate)
            except RuntimeError as exc:
                print(f"[ERROR] {exc}")
                return None

    if config_arg:
        print(f"[ERROR] Config not found: {config_arg}")
        print("Create a codebase-map.yaml or use --config to specify path.")
        return None

    config = Config.auto_detect(Path("."))
    if not config.sources:
        print("[ERROR] No config file and no Python or TypeScript/JavaScript")
        print(f"        source files found in {Path.cwd()}.")
        return None
    languages = ", ".join(source.language for source in config.sources)
    print(f"[AUTO] No config file found. Auto-detected sources: {languages}.")
    return config


def _cmd_generate(args: argparse.Namespace) -> int:
    from codebase_map.exporters.html_exporter import export_html
    from codebase_map.exporters.json_exporter import export_json
    from codebase_map.graph.builder import GraphBuilder

    config = _load_generate_config(getattr(args, "config", None))
    if config is None:
        return 1
    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S2-02: Incremental cache support
    use_cache = not getattr(args, "no_cache", False)
    # CBM-P1-02: Pass snapshot label to builder
    label = getattr(args, "label", "") or ""
    builder = GraphBuilder(config, use_cache=use_cache, label=label)
    graph = builder.build()

    output_dir = config.project_root / config.output.dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if "json" in config.output.formats:
        export_json(graph, output_dir / "graph.json")

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CBM-P1-03: Auto-save snapshot to .codebase-map-cache/snapshots/
    from codebase_map.snapshot import SnapshotManager

    snap_mgr = SnapshotManager(
        str(config.project_root / ".codebase-map-cache" / "snapshots")
    )
    snap_path = snap_mgr.save(graph)
    print(f"[OK] Snapshot saved: {snap_path.name}")

    # HC-AI | ticket: CM-HOTFIX-V2.0.1 (POST-CM-S3-04)
    # When --diff <ref> is supplied, run the diff analyzer now and write
    # pr_diff.json into the output dir. export_html() will auto-bake it
    # into the PR Diff view on the next line, so users get a single-command
    # workflow instead of the previous 2-step dance.
    diff_ref = getattr(args, "diff", "") or ""
    if diff_ref:
        try:
            from codebase_map.graph.diff import DiffAnalyzer

            analyzer = DiffAnalyzer(graph, project_root=config.project_root)
            diff_result = analyzer.analyze(
                ref=diff_ref, depth=getattr(args, "diff_depth", 3)
            )
            diff_path = output_dir / "pr_diff.json"
            diff_path.write_text(diff_result.to_json(indent=2), encoding="utf-8")
            print(
                f"[OK] PR Diff baked: {diff_path} "
                f"(vs {diff_ref} — {len(diff_result.changed_nodes)} changed, "
                f"{len(diff_result.impacted_nodes)} impacted)"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] --diff {diff_ref} failed: {exc}")
            print("       HTML will render without PR Diff view.")

    if "html" in config.output.formats:
        export_html(graph, output_dir / "index.html")

    n_nodes = len(graph.nodes)
    n_edges = len(graph.edges)
    print(f"\n[DONE] {graph.project} — {n_nodes} nodes, {n_edges} edges")
    stats = graph.stats()
    print(f"  Layers: {stats['by_layer']}")
    print(f"  Domains: {stats['by_domain']}")

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CBM-P1-01: Print snapshot metadata summary
    meta = graph.metadata
    if meta.get("version") == "2.1":
        print(
            f"  Snapshot: label={meta.get('label', '?')} "
            f"branch={meta.get('branch', '?')} "
            f"sha={meta.get('commit_sha', '?')}"
        )

    # Print cache stats
    cs = builder.cache_stats
    if cs.total_files > 0:
        build_ms = meta.get("build_time_ms", 0)
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


# HC-AI | ticket: FDD-TOOL-CODEMAP
# CBM-P1-04/05: Snapshot list + clean commands
def _cmd_snapshots(args: argparse.Namespace) -> int:
    """Manage graph snapshots — list or clean (CBM-P1-04, CBM-P1-05)."""
    from codebase_map.snapshot import SnapshotManager

    # Resolve snapshot directory from config or default
    config_path = Path(args.config)
    if config_path.exists():
        project_root = config_path.parent
    else:
        project_root = Path.cwd()

    snap_dir = str(project_root / ".codebase-map-cache" / "snapshots")
    mgr = SnapshotManager(snap_dir)

    if args.action == "list":
        return _snapshots_list(mgr, json_output=args.json_output)
    elif args.action == "clean":
        return _snapshots_clean(mgr, keep=args.keep)

    return 0


def _snapshots_list(mgr, json_output: bool = False) -> int:
    """CBM-P1-04: Display snapshot table."""
    import json as json_mod

    snapshots = mgr.list_snapshots()

    if not snapshots:
        print("No snapshots found.")
        print("Run 'codebase-map generate --label <name>' to create one.")
        return 0

    if json_output:
        print(json_mod.dumps([s.to_dict() for s in snapshots], indent=2))
        return 0

    # Table header
    print(f"\nSNAPSHOTS ({len(snapshots)} found)")
    print(
        f"{'Label':<30s} {'Date':<20s} {'Branch':<20s} "
        f"{'SHA':<9s} {'Nodes':>6s} {'Edges':>6s} {'Size':>8s}"
    )
    print("-" * 103)

    for s in snapshots:
        # Format date (trim timezone/microseconds for display)
        date_display = s.date[:19] if len(s.date) > 19 else s.date
        # Format file size
        if s.file_size >= 1024 * 1024:
            size_str = f"{s.file_size / (1024 * 1024):.1f}MB"
        elif s.file_size >= 1024:
            size_str = f"{s.file_size // 1024}KB"
        else:
            size_str = f"{s.file_size}B"

        print(
            f"{s.label:<30s} {date_display:<20s} {s.branch:<20s} "
            f"{s.sha:<9s} {s.nodes:>6d} {s.edges:>6d} {size_str:>8s}"
        )

    print()
    return 0


def _snapshots_clean(mgr, keep: int = 10) -> int:
    """CBM-P1-05: Remove old snapshots, keep N newest."""
    snapshots_before = mgr.list_snapshots()

    if not snapshots_before:
        print("No snapshots to clean.")
        return 0

    removed, kept = mgr.clean(keep=keep)
    print(f"Removed {removed} snapshot(s), kept {kept}.")
    return 0


# HC-AI | ticket: FDD-TOOL-CODEMAP
# CBM-P2-05/06/07/08: Dual-snapshot diff command
def _cmd_snapshot_diff(args: argparse.Namespace) -> int:
    """Compare two graph snapshots — dual-snapshot diff engine."""
    from codebase_map.graph.diff_formatter import (
        filter_breaking_only,
        format_diff_json,
        format_diff_markdown,
        format_diff_text,
        format_test_plan,
    )
    from codebase_map.graph.snapshot_diff import SnapshotDiff
    from codebase_map.snapshot import SnapshotManager

    # Resolve snapshot files
    config_path = Path(args.config)
    if config_path.exists():
        project_root = config_path.parent
    else:
        project_root = Path.cwd()

    snap_dir = project_root / ".codebase-map-cache" / "snapshots"
    mgr = SnapshotManager(str(snap_dir))

    try:
        baseline = mgr.load(args.baseline)
    except FileNotFoundError:
        print(f"[ERROR] Baseline not found: {args.baseline}")
        return 1

    try:
        current = mgr.load(args.current)
    except FileNotFoundError:
        print(f"[ERROR] Current not found: {args.current}")
        return 1

    # Compute diff
    diff = SnapshotDiff(baseline, current)
    result = diff.compute(depth=args.depth)

    # Apply breaking-only filter
    if args.breaking_only:
        result = filter_breaking_only(result)

    # Output test plan if requested
    if args.test_plan:
        print(format_test_plan(result))
        return 0

    # Format output
    fmt = args.output_format
    if fmt == "json":
        print(format_diff_json(result))
    elif fmt == "markdown":
        print(format_diff_markdown(result))
    else:
        print(format_diff_text(result))

    return 0


if __name__ == "__main__":
    sys.exit(main())


# HC-AI | ticket: FDD-TOOL-CODEMAP
# VIBE-103: `features` — the store of features, acceptance criteria and
# evidence kept in .cbm/features.json, and what a change does to them.
def _add_features_parser(sub) -> None:
    feat_p = sub.add_parser(
        "features",
        help="Features, acceptance criteria and evidence (.cbm/features.json)",
    )
    feat_sub = feat_p.add_subparsers(dest="features_command")

    def command(name: str, help_text: str) -> argparse.ArgumentParser:
        parser = feat_sub.add_parser(name, help=help_text)
        parser.add_argument(
            "-c",
            "--config",
            default=None,
            help="Config file. Default: codebase-map.yaml / .json, else auto-detect.",
        )
        parser.add_argument(
            "--store",
            default=None,
            help="Feature store file (default: .cbm/features.json in the project)",
        )
        parser.add_argument(
            "--json", action="store_true", dest="json_output", help="Output as JSON"
        )
        return parser

    command("status", "Features with their screens, files and criterion status")

    impact_p = command("impact", "What the change between two snapshots touches")
    impact_p.add_argument("--baseline", required=True, help="Snapshot before")
    impact_p.add_argument("--current", required=True, help="Snapshot after")

    add_p = command("add", "Add a feature, or update an existing one")
    add_p.add_argument("--id", required=True, dest="feature_id", help="e.g. booking")
    add_p.add_argument("--name", default=None, help="Name shown to the owner")
    add_p.add_argument(
        "--files",
        default=None,
        nargs="+",
        help="Files, folders or globs (* and ?) that implement the feature",
    )
    add_p.add_argument(
        "--append",
        action="store_true",
        help="Add --files to the feature's existing ones instead of replacing them",
    )
    add_p.add_argument("--summary", default=None, help="One sentence about it")

    crit_p = command("criterion", "Add an acceptance criterion to a feature")
    crit_p.add_argument("--feature", required=True, help="Feature id")
    crit_p.add_argument("--text", required=True, help="The criterion, in plain words")
    crit_p.add_argument("--id", default=None, dest="criterion_id", help="Optional id")

    ev_p = command("evidence", "Record that a criterion was checked just now")
    ev_p.add_argument("--criterion", required=True, help="Criterion id")
    ev_p.add_argument(
        "--kind",
        required=True,
        choices=["manual", "test"],
        help="manual: a person tried it; test: an automated test passed",
    )
    ev_p.add_argument("--note", default="", help="Who checked, or which test")


def _cmd_features(args: argparse.Namespace) -> int:
    """Features, acceptance criteria and evidence."""
    import json as json_mod

    from codebase_map.features import FeatureStoreError

    if not args.features_command:
        print("Usage: codebase-map features {status,impact,add,criterion,evidence}")
        return 1
    try:
        output = _run_features(args)
    except FeatureStoreError as exc:
        if args.json_output:
            print(json_mod.dumps({"error": str(exc)}, ensure_ascii=False))
        else:
            print(f"[ERROR] {exc}")
        return 1
    if output is None:
        return 1
    data, text = output
    if args.json_output:
        print(json_mod.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(text)
    return 0


def _run_features(args: argparse.Namespace):
    """Run one `features` command; return (data for JSON, text) or None on error."""
    from codebase_map.features import (
        FeatureMap,
        FeatureStore,
        FeatureStoreError,
        compute_impact,
        format_impact_text,
        format_status_text,
    )
    from codebase_map.snapshot import SnapshotManager

    command = args.features_command
    config_path = Path(args.config) if args.config else None
    root = config_path.parent if config_path and config_path.exists() else Path(".")
    store_path = Path(args.store) if args.store else FeatureStore.default_path(root)
    store = FeatureStore.load(store_path)

    if command == "impact":
        snapshots = SnapshotManager(str(root / ".codebase-map-cache" / "snapshots"))
        graphs = []
        for label in (args.baseline, args.current):
            try:
                graphs.append(snapshots.load(label))
            except FileNotFoundError:
                raise FeatureStoreError(f"Snapshot not found: {label}") from None
        data = compute_impact(store, graphs[0], graphs[1])
        return data, format_impact_text(data)

    if command == "criterion":
        criterion = store.add_criterion(args.feature, args.text, args.criterion_id)
        store.save(store_path)
        return criterion.to_dict(), f"[OK] Criterion {criterion.id} added."

    # The remaining commands look at the code as it is now
    graph = _current_graph(args.config)
    if graph is None:
        return None

    if command == "add":
        # An existing feature keeps whatever the command does not give
        known = next((f for f in store.features if f.id == args.feature_id), None)
        name = args.name or (known.name if known else None)
        files = args.files or (list(known.files) if known else None)
        if name is None or files is None:
            raise FeatureStoreError("A new feature needs --name and --files.")
        if args.append and known and args.files:
            files = known.files + [p for p in args.files if p not in known.files]
        summary = args.summary
        if summary is None:
            summary = known.summary if known else ""
        feature = store.upsert_feature(args.feature_id, name, files, summary)
        store.save(store_path)
        scope = FeatureMap(store, graph).scope(feature.id)
        files = graph.metadata["files"]
        unmatched = [
            pattern
            for pattern in feature.files
            if not any(_feature_pattern_hits(pattern, path, graph) for path in files)
        ]
        data = {
            **feature.to_dict(),
            "matched_files": scope.owned_files,
            "unmatched_patterns": unmatched,
        }
        text = (
            f"[OK] Feature {feature.id} saved: {len(scope.owned_files)} file(s), "
            f"{len(scope.owned_nodes)} function(s)."
        )
        if unmatched:
            text += "\n[WARN] Patterns that match nothing: " + ", ".join(unmatched)
        return data, text

    feature_map = FeatureMap(store, graph)
    if command == "evidence":
        feature, _ = store.criterion(args.criterion)
        fingerprint = feature_map.scope(feature.id).fingerprint
        criterion = store.record_evidence(
            args.criterion, args.kind, args.note, fingerprint
        )
        store.save(store_path)
        return criterion.to_dict(), f"[OK] Evidence recorded for {criterion.id}."

    data = feature_map.to_dict()
    data["store"] = str(store_path)
    return data, format_status_text(data)


def _feature_pattern_hits(pattern: str, path: str, graph) -> bool:
    """True when a feature pattern matches the file or one of its functions."""
    from codebase_map.features import _is_id_pattern, pattern_matches

    if pattern_matches(pattern, path):
        return True
    return _is_id_pattern(pattern) and any(
        pattern_matches(pattern, node.id)
        for node in graph.nodes.values()
        if node.file_path.replace("\\", "/") == path
    )


def _current_graph(config_arg: str | None):
    """Build the graph of the code as it is now, without writing any file.

    Progress and warnings go to stderr, so stdout carries only the result.
    """
    import contextlib

    from codebase_map.graph.builder import GraphBuilder

    with contextlib.redirect_stdout(sys.stderr):
        config = _load_generate_config(config_arg)
        if config is None:
            return None
        return GraphBuilder(config, use_cache=False).build()
