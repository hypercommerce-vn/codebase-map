# HC-AI | ticket: VIBE-105
"""Tests for codebase_map.mod.status — status aggregator."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from codebase_map.mod.status import (
    StatusData,
    _sprint_from_branch,
    _sprint_from_claude_md,
    collect_status,
    get_branch,
    get_risk,
    get_snapshot,
    get_sprint,
)


def _git_init(path: Path) -> None:
    """Initialise a bare-minimum git repo for branch tests."""
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=path, check=True)
    (path / "README.md").write_text("x")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


class TestBranchParse:
    @pytest.mark.parametrize(
        "branch,expected",
        [
            ("feat/vibe-105-cbm-mod", "VIBE-105"),
            ("fix/cm-s2-01-cache", "CM-S2-01"),  # multi-component ticket id
            ("hotfix/kmp-42", "KMP-42"),
            ("docs/cbm-999-readme", "CBM-999"),
            ("feat/cbm-p1-03-metadata", "CBM-P1-03"),
            ("main", None),
            ("", None),
            (None, None),
            ("feature/no-ticket", None),
        ],
    )
    def test_ticket_slug_extraction(self, branch, expected):
        assert _sprint_from_branch(branch) == expected


class TestSprintFromClaudeMd:
    def test_returns_none_when_missing(self, tmp_path: Path):
        assert _sprint_from_claude_md(tmp_path) is None

    def test_picks_first_not_done_row(self, tmp_path: Path):
        (tmp_path / "CLAUDE.md").write_text(
            "# Roadmap\n"
            "| **v1.0** | CM-S1 | Core | 8 | ✅ Done |\n"
            "| **v2.0** | CM-S2 | Flow | 10 | 🚧 In progress |\n"
            "| **v3.0** | CM-S3 | Next | 5 | Planned |\n"
        )
        assert _sprint_from_claude_md(tmp_path) == "CM-S2"

    def test_falls_back_to_last_done(self, tmp_path: Path):
        (tmp_path / "CLAUDE.md").write_text(
            "| **v1.0** | CM-S1 | Core | 8 | ✅ Done |\n"
            "| **v2.0** | CM-S2 | Flow | 10 | ✅ Done |\n"
        )
        assert _sprint_from_claude_md(tmp_path) == "CM-S2"

    def test_skips_dash_sprint(self, tmp_path: Path):
        (tmp_path / "CLAUDE.md").write_text("| **v1.0** | — | Core | 8 | ✅ Done |\n")
        assert _sprint_from_claude_md(tmp_path) is None


class TestGetBranch:
    def test_returns_branch(self, tmp_path: Path):
        _git_init(tmp_path)
        assert get_branch(tmp_path) == "main"

    def test_none_when_no_repo(self, tmp_path: Path):
        assert get_branch(tmp_path) is None


class TestGetSprint:
    def test_prefers_branch_over_claude(self, tmp_path: Path):
        _git_init(tmp_path)
        subprocess.run(
            ["git", "checkout", "-q", "-b", "feat/vibe-105-xyz"],
            cwd=tmp_path,
            check=True,
        )
        (tmp_path / "CLAUDE.md").write_text(
            "| **v1.0** | OTHER-1 | Flow | 1 | In progress |\n"
        )
        assert get_sprint(tmp_path) == "VIBE-105"

    def test_falls_back_to_claude_md(self, tmp_path: Path):
        _git_init(tmp_path)  # branch = main, not a ticket slug
        (tmp_path / "CLAUDE.md").write_text(
            "| **v1.0** | CM-S4 | Next | 3 | In progress |\n"
        )
        assert get_sprint(tmp_path) == "CM-S4"


class TestGetSnapshot:
    def test_unknown_when_no_dir(self, tmp_path: Path):
        state, delta = get_snapshot(tmp_path)
        assert state == "unknown"
        assert delta is None

    def test_clean_when_no_py_newer(self, tmp_path: Path):
        snap_dir = tmp_path / ".codebase-map" / "snapshots"
        snap_dir.mkdir(parents=True)
        snap = snap_dir / "s1.json"
        snap.write_text("{}")
        # Make sure src dir exists but has no newer files
        (tmp_path / "codebase_map").mkdir()
        state, _ = get_snapshot(tmp_path)
        assert state == "clean"

    def test_dirty_when_py_file_newer(self, tmp_path: Path):
        import os
        import time

        snap_dir = tmp_path / ".codebase-map" / "snapshots"
        snap_dir.mkdir(parents=True)
        snap = snap_dir / "s1.json"
        snap.write_text("{}")
        src = tmp_path / "codebase_map"
        src.mkdir()
        py = src / "foo.py"
        py.write_text("x = 1")
        # Force py mtime newer than snapshot
        later = time.time() + 10
        os.utime(py, (later, later))
        state, delta = get_snapshot(tmp_path)
        assert state == "dirty"
        assert delta and "newer" in delta


class TestGetRisk:
    @pytest.mark.parametrize(
        "snap,level",
        [("clean", "low"), ("dirty", "medium"), ("unknown", "unknown")],
    )
    def test_level_follows_snapshot(self, snap, level, tmp_path: Path):
        assert get_risk(tmp_path, snap)[0] == level


class TestCollectStatus:
    def test_returns_status_data_even_on_empty_dir(self, tmp_path: Path):
        d = collect_status(tmp_path)
        assert isinstance(d, StatusData)
        # No git / gh / snapshot means everything degrades to a sensible default
        assert d.ci_state == "unknown"
        assert d.snapshot_state == "unknown"
        assert d.risk_level == "unknown"
        assert d.errors == {}

    def test_dict_shape(self, tmp_path: Path):
        d = collect_status(tmp_path).to_dict()
        # Six status slots + errors container per the design preview.
        assert set(d.keys()) >= {
            "sprint",
            "branch",
            "pr_number",
            "pr_url",
            "ci_state",
            "snapshot_state",
            "risk_level",
            "errors",
        }
