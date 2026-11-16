# HC-AI | ticket: VIBE-106
"""Status line data aggregator.

Collects six slots the CBM Mod status line shows:
sprint, branch, pr, ci, snapshot, risk.

Every source can fail (no git, no gh, no BRIEF.md) and the aggregator
degrades to a neutral value instead of raising, so the status line
always has something to render.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class StatusData:
    sprint: Optional[str] = None
    branch: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    ci_state: str = "unknown"  # pass | fail | running | unknown
    ci_duration: Optional[str] = None
    snapshot_state: str = "unknown"  # clean | dirty | unknown
    snapshot_delta: Optional[str] = None  # e.g. "+12 nodes"
    risk_level: str = "unknown"  # low | medium | high | unknown
    risk_note: Optional[str] = None
    errors: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _run(cmd: list[str], cwd: Path, timeout: float = 5.0) -> Optional[str]:
    """Run a command and return stripped stdout, or None on any failure."""
    try:
        r = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        if r.returncode != 0:
            return None
        return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return None


def get_branch(repo: Path) -> Optional[str]:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo)


_BRANCH_TICKET = re.compile(
    r"^(?:feat|fix|docs|chore|refactor|test|hotfix)/([a-z]+(?:-[a-z]*\d+)+)",
    re.IGNORECASE,
)
_ROADMAP_ROW = re.compile(
    r"^\|\s*\*?\*?v[\d.]+\*?\*?\s*\|\s*([A-Z0-9\-]+)\s*\|.*?\|.*?\|\s*(.*?)\s*\|\s*$"
)


def _sprint_from_branch(branch: Optional[str]) -> Optional[str]:
    if not branch:
        return None
    m = _BRANCH_TICKET.match(branch)
    return m.group(1).upper() if m else None


def _sprint_from_claude_md(repo: Path) -> Optional[str]:
    """Parse the last in-progress sprint from CLAUDE.md's ROADMAP table."""
    claude = repo / "CLAUDE.md"
    if not claude.exists():
        return None
    try:
        text = claude.read_text(encoding="utf-8")
    except OSError:
        return None
    last_done = None
    for line in text.splitlines():
        m = _ROADMAP_ROW.match(line)
        if not m:
            continue
        sprint, status = m.group(1), m.group(2)
        if sprint == "—":
            continue
        if "Done" not in status:
            return sprint
        last_done = sprint
    return last_done


def get_sprint(repo: Path, branch: Optional[str] = None) -> Optional[str]:
    """Return the current sprint / ticket id.

    Branch convention ``feat/<slug>-<n>`` is the authoritative source for
    in-progress work (and the mod runs inside such a branch). CLAUDE.md's
    ROADMAP table is the fallback for branches like ``main``.
    """
    if branch is None:
        branch = get_branch(repo)
    from_branch = _sprint_from_branch(branch)
    if from_branch:
        return from_branch
    return _sprint_from_claude_md(repo)


def get_pr(repo: Path) -> tuple[Optional[int], Optional[str]]:
    if not shutil.which("gh"):
        return None, None
    out = _run(["gh", "pr", "view", "--json", "number,url"], repo, timeout=8.0)
    if not out:
        return None, None
    try:
        data = json.loads(out)
        return data.get("number"), data.get("url")
    except json.JSONDecodeError:
        return None, None


def get_ci(repo: Path, pr_number: Optional[int]) -> tuple[str, Optional[str]]:
    """Return (state, duration) for the latest CI run on the current PR.

    state ∈ {pass, fail, running, unknown}.
    """
    if not shutil.which("gh") or pr_number is None:
        return "unknown", None
    out = _run(
        [
            "gh",
            "run",
            "list",
            "--branch",
            get_branch(repo) or "HEAD",
            "--limit",
            "1",
            "--json",
            "status,conclusion,createdAt,updatedAt",
        ],
        repo,
        timeout=8.0,
    )
    if not out:
        return "unknown", None
    try:
        runs = json.loads(out)
        if not runs:
            return "unknown", None
        run = runs[0]
        status = run.get("status", "")
        conclusion = run.get("conclusion") or ""
        if status == "completed":
            return ("pass" if conclusion == "success" else "fail", None)
        if status in ("in_progress", "queued", "waiting"):
            return "running", None
        return "unknown", None
    except (json.JSONDecodeError, KeyError, IndexError):
        return "unknown", None


def get_snapshot(repo: Path) -> tuple[str, Optional[str]]:
    """Check whether the stored graph snapshot matches the current code.

    Dirty means ``codebase_map/`` has files newer than the latest snapshot;
    this is a cheap stand-in for a full re-parse comparison.
    """
    snap_dir = repo / ".codebase-map" / "snapshots"
    if not snap_dir.exists():
        return "unknown", None
    snapshots = sorted(snap_dir.glob("*.json"))
    if not snapshots:
        return "unknown", None
    latest = snapshots[-1]
    latest_mtime = latest.stat().st_mtime
    src_dirs = [repo / "codebase_map"]
    delta_nodes = 0
    dirty = False
    for src in src_dirs:
        if not src.exists():
            continue
        for p in src.rglob("*.py"):
            if p.stat().st_mtime > latest_mtime:
                dirty = True
                delta_nodes += 1
    if dirty:
        return "dirty", f"~{delta_nodes} files newer"
    return "clean", None


def get_risk(repo: Path, snapshot_state: str) -> tuple[str, Optional[str]]:
    """Derive a traffic-light risk level from the snapshot state.

    A full diff-engine pass happens on Day 5; Day 1 returns a coarse
    proxy: clean=low, dirty=medium, unknown=unknown.
    """
    if snapshot_state == "clean":
        return "low", "no pending changes"
    if snapshot_state == "dirty":
        return "medium", "pending changes not yet diffed"
    return "unknown", None


def collect_status(repo: Path | str = ".") -> StatusData:
    """Collect all six status slots. Never raises."""
    repo_path = Path(repo).resolve()
    data = StatusData()

    try:
        data.branch = get_branch(repo_path)
    except Exception as e:  # noqa: BLE001
        data.errors["branch"] = str(e)

    try:
        data.sprint = get_sprint(repo_path, data.branch)
    except Exception as e:  # noqa: BLE001
        data.errors["sprint"] = str(e)

    try:
        data.pr_number, data.pr_url = get_pr(repo_path)
    except Exception as e:  # noqa: BLE001
        data.errors["pr"] = str(e)

    try:
        data.ci_state, data.ci_duration = get_ci(repo_path, data.pr_number)
    except Exception as e:  # noqa: BLE001
        data.errors["ci"] = str(e)

    try:
        data.snapshot_state, data.snapshot_delta = get_snapshot(repo_path)
    except Exception as e:  # noqa: BLE001
        data.errors["snapshot"] = str(e)

    try:
        data.risk_level, data.risk_note = get_risk(repo_path, data.snapshot_state)
    except Exception as e:  # noqa: BLE001
        data.errors["risk"] = str(e)

    return data
