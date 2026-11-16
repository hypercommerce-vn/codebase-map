# HC-AI | ticket: VIBE-106
"""Tests for codebase_map.mod.hooks — post-commit hook installer."""

from __future__ import annotations

import subprocess
from pathlib import Path

from codebase_map.mod.hooks import (
    BACKUP_SUFFIX,
    HOOK_NAME,
    MARKER,
    disable,
    enable,
    status,
)


def _init_git(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    # Ensure .git/hooks exists — git init creates it by default but be defensive.
    (path / ".git" / "hooks").mkdir(parents=True, exist_ok=True)


class TestStatus:
    def test_not_installed_when_hook_missing(self, tmp_path: Path):
        _init_git(tmp_path)
        s = status(tmp_path)
        assert s.installed is False
        assert s.is_managed is False
        assert s.backed_up is None

    def test_installed_but_unmanaged_when_foreign_hook_present(self, tmp_path: Path):
        _init_git(tmp_path)
        (tmp_path / ".git" / "hooks" / HOOK_NAME).write_text(
            "#!/bin/sh\necho not ours\n"
        )
        s = status(tmp_path)
        assert s.installed is True
        assert s.is_managed is False


class TestEnable:
    def test_fresh_install(self, tmp_path: Path):
        _init_git(tmp_path)
        s = enable(tmp_path)
        assert s.installed is True
        assert s.is_managed is True
        assert s.backed_up is None
        # Managed marker lands in the script body.
        assert MARKER in s.path.read_text()
        # Executable bit is set (ignored on exotic FSs; tolerate failure).
        assert s.path.stat().st_mode & 0o100

    def test_backs_up_existing_unmanaged_hook(self, tmp_path: Path):
        _init_git(tmp_path)
        prior = "#!/bin/sh\necho prior\n"
        (tmp_path / ".git" / "hooks" / HOOK_NAME).write_text(prior)

        s = enable(tmp_path)
        assert s.is_managed is True
        assert s.backed_up is not None
        # Backup preserves the original content byte-for-byte.
        assert s.backed_up.read_text() == prior

    def test_reenable_is_idempotent(self, tmp_path: Path):
        _init_git(tmp_path)
        enable(tmp_path)
        s = enable(tmp_path)
        assert s.is_managed is True
        # Second enable does not produce a second backup from our own hook.
        assert s.backed_up is None


class TestDisable:
    def test_removes_managed_hook(self, tmp_path: Path):
        _init_git(tmp_path)
        enable(tmp_path)
        s = disable(tmp_path)
        # With no prior backup, disable leaves the hook absent.
        assert s.installed is False

    def test_restores_prior_hook_from_backup(self, tmp_path: Path):
        _init_git(tmp_path)
        prior = "#!/bin/sh\necho prior\n"
        (tmp_path / ".git" / "hooks" / HOOK_NAME).write_text(prior)
        enable(tmp_path)
        s = disable(tmp_path)
        assert s.installed is True
        assert s.is_managed is False  # back to the user's own script
        assert (tmp_path / ".git" / "hooks" / HOOK_NAME).read_text() == prior
        # Backup consumed after restore.
        assert not (tmp_path / ".git" / "hooks" / (HOOK_NAME + BACKUP_SUFFIX)).exists()

    def test_leaves_foreign_hook_alone(self, tmp_path: Path):
        _init_git(tmp_path)
        foreign = "#!/bin/sh\necho foreign\n"
        (tmp_path / ".git" / "hooks" / HOOK_NAME).write_text(foreign)
        # Never enabled — disable must not touch a hook we do not own.
        s = disable(tmp_path)
        assert s.installed is True
        assert s.is_managed is False
        assert (tmp_path / ".git" / "hooks" / HOOK_NAME).read_text() == foreign
