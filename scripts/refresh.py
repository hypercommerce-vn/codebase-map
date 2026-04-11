#!/usr/bin/env python3
# HC-AI | ticket: FDD-TOOL-CODEMAP
"""refresh.py — Refresh codebase-map + KMP data after PR merge.

Usage (from project root, with venv activated):
    python scripts/refresh.py          # full refresh (both tools)
    python scripts/refresh.py --map    # codebase-map only
    python scripts/refresh.py --kmp    # KMP only
    python scripts/refresh.py --quick  # skip git ownership (faster)

Requires: pip install -e ".[dev]"
Run from project root after each PR merge to keep data fresh.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

# ── Project root detection ──────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SELF_CONFIG = ROOT / "codebase-map-self.yaml"
VAULT_DIR = ROOT / ".knowledge-memory"


def _header(msg: str) -> None:
    print(f"\n{'━' * 60}")
    print(f"  {msg}")
    print(f"{'━' * 60}\n")


def _ok(msg: str) -> None:
    print(f"  \033[32m✓\033[0m {msg}")


def _warn(msg: str) -> None:
    print(f"  \033[33m⚠\033[0m {msg}")


def _err(msg: str) -> None:
    print(f"  \033[31m✗\033[0m {msg}")


def _elapsed(start: float) -> str:
    return f"{time.time() - start:.1f}s"


# ── Step 1: Codebase Map ────────────────────────────────
def run_codebase_map() -> bool:
    _header("Step 1/2 — Codebase Map (function dependency graph)")
    t = time.time()

    if not SELF_CONFIG.exists():
        _err(f"Config not found: {SELF_CONFIG}")
        return False

    # Generate graph
    cmd = [
        sys.executable,
        "-m",
        "codebase_map",
        "generate",
        "-c",
        str(SELF_CONFIG),
    ]
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)

    if result.returncode != 0:
        _err(f"Generate failed:\n{result.stderr}")
        return False

    # Parse output for stats
    for line in result.stdout.splitlines():
        if "[DONE]" in line or "[OK]" in line:
            print(f"  {line.strip()}")

    # Summary
    graph_json = ROOT / "docs" / "function-map" / "graph.json"
    graph_html = ROOT / "docs" / "function-map" / "index.html"

    if graph_json.exists():
        _ok(f"graph.json  ({graph_json.stat().st_size / 1024:.0f} KB)")
    if graph_html.exists():
        _ok(f"index.html  ({graph_html.stat().st_size / 1024:.0f} KB)")

    # Run summary
    cmd_summary = [
        sys.executable,
        "-m",
        "codebase_map",
        "summary",
        "-f",
        str(graph_json),
    ]
    sub = subprocess.run(cmd_summary, cwd=str(ROOT), capture_output=True, text=True)
    if sub.returncode == 0:
        for line in sub.stdout.strip().splitlines():
            print(f"  {line}")

    _ok(f"Codebase Map done ({_elapsed(t)})")
    return True


# ── Step 2: KMP Bootstrap ───────────────────────────────
def run_kmp(quick: bool = False) -> bool:
    _header("Step 2/2 — KMP (patterns + quick wins)")
    t = time.time()

    try:
        from knowledge_memory.verticals.codebase.bootstrap import BootstrapOrchestrator
        from knowledge_memory.verticals.codebase.cli_output import (
            format_bootstrap_complete,
            format_quick_wins_inline,
            format_vault_summary,
        )
        from knowledge_memory.verticals.codebase.quick_wins import generate_quick_wins
        from knowledge_memory.verticals.codebase.vault import CodebaseVault
    except ImportError as e:
        _err(f"KMP import failed: {e}")
        _warn("Run: pip install -e '.[dev]'")
        return False

    # Bootstrap
    include = ["codebase_map/**/*.py", "knowledge_memory/**/*.py"]
    exclude = ["__pycache__", ".venv", "tests", "*.pyc"]

    max_commits = 200 if quick else 1000
    print(f"  Mode: {'quick (skip deep git)' if quick else 'full'}")
    print(f"  Include: {', '.join(include)}")

    orch = BootstrapOrchestrator(
        root=ROOT,
        include_patterns=include,
        exclude_patterns=exclude,
        max_git_commits=max_commits,
        force_init=False,
    )

    def _progress(step: int, total: int, msg: str) -> None:
        print(f"  [{step}/{total}] {msg}")

    result = orch.run(progress_callback=_progress)

    if not result.success:
        _err("Bootstrap failed")
        for e in result.errors:
            _err(f"  {e}")
        return False

    # Learner breakdown
    for name, count in result.learner_results.items():
        short = name.split(".")[-1]
        _ok(f"{short}: {count} patterns")

    # Quick Wins
    print()
    vault = CodebaseVault()
    vault.open(ROOT)
    qw = generate_quick_wins(vault)

    # Print rich output
    print(
        format_bootstrap_complete(
            result.elapsed_seconds,
            result.pattern_count,
            qw.insight_count,
        )
    )
    print()
    print(format_quick_wins_inline(qw))

    # Vault summary
    print()
    print(
        format_vault_summary(
            vault_path=str(VAULT_DIR) + "/",
            pattern_count=result.pattern_count,
            pattern_breakdown=", ".join(
                f"{c} {n.split('.')[-1]}" for n, c in result.learner_results.items()
            ),
            snapshot_count=vault.snapshot_count(),
            quick_win_count=qw.insight_count,
            quick_win_breakdown=(
                f"{len(qw.structure_insights)} structure + "
                f"{len(qw.pattern_insights)} patterns + "
                f"{len(qw.risk_insights)} risks"
            ),
            node_count=vault.node_count(),
            edge_count=vault.edge_count(),
            file_count=result.parse_stats.get("files", 0),
            duration=result.elapsed_seconds,
        )
    )

    # Output paths
    patterns_md = VAULT_DIR / "verticals" / "codebase" / "patterns.md"
    quickwins_md = VAULT_DIR / "verticals" / "codebase" / "quick-wins.md"
    print("\n  Output files:")
    if patterns_md.exists():
        _ok(f"patterns.md   ({patterns_md.stat().st_size / 1024:.1f} KB)")
    if quickwins_md.exists():
        _ok(f"quick-wins.md ({quickwins_md.stat().st_size / 1024:.1f} KB)")

    _ok(f"KMP done ({_elapsed(t)})")
    return True


# ── Main ────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh codebase-map + KMP data after PR merge.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run from project root. Both tools refresh by default.",
    )
    parser.add_argument(
        "--map",
        action="store_true",
        help="Codebase Map only (skip KMP)",
    )
    parser.add_argument(
        "--kmp",
        action="store_true",
        help="KMP only (skip Codebase Map)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode — limit git history to 200 commits",
    )
    args = parser.parse_args()

    # Default: run both
    run_map = not args.kmp or args.map
    run_kmp_flag = not args.map or args.kmp
    if not args.map and not args.kmp:
        run_map = True
        run_kmp_flag = True

    start = time.time()
    print("\033[1mrefresh.py\033[0m — Codebase Map + KMP Data Refresh")
    print(f"Project: {ROOT.name}")
    print(
        f"Tools:   {'Codebase Map' if run_map else ''}"
        f"{'+ ' if run_map and run_kmp_flag else ''}"
        f"{'KMP' if run_kmp_flag else ''}"
    )

    ok = True

    if run_map:
        if not run_codebase_map():
            ok = False

    if run_kmp_flag:
        if not run_kmp(quick=args.quick):
            ok = False

    # Final summary
    _header("Done")
    total = _elapsed(start)
    if ok:
        _ok(f"All tools refreshed in {total}")
    else:
        _warn(f"Some tools had errors (total: {total})")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
