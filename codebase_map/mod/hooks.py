# HC-AI | ticket: VIBE-106
"""Git hook installer for the CBM Mod.

Day 6 ships one hook — ``post-commit`` — that regenerates the codebase
map after every commit so the Timeline tab always has a fresh snapshot
to compare against.

Install is explicitly opt-in (CEO decision #5) via
``codebase-map mod enable-hooks``; uninstall via
``codebase-map mod disable-hooks``. If the user already has a
pre-existing ``post-commit`` hook, we back it up to
``post-commit.cbm-backup`` so nothing is overwritten silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

HOOK_NAME = "post-commit"
BACKUP_SUFFIX = ".cbm-backup"
MARKER = "# CBM-MOD-HOOK v1 — managed by `codebase-map mod enable-hooks`"

HOOK_SCRIPT = f"""#!/usr/bin/env bash
{MARKER}
# Regenerate the codebase map after every commit so the Timeline tab
# always has a fresh snapshot to compare against. Fails silently so a
# missing config, a parser error or an interrupted run never blocks a
# commit (the commit has already succeeded at this point).

CBM_CONFIG="$(git rev-parse --show-toplevel)/codebase-map.yaml"
if [ -f "$CBM_CONFIG" ]; then
  (codebase-map generate -c "$CBM_CONFIG" >/dev/null 2>&1 || true) &
fi
"""


@dataclass
class HookStatus:
    installed: bool
    path: Optional[Path]
    is_managed: bool  # True when our MARKER is in the script
    backed_up: Optional[Path]  # existing backup, if any

    def to_dict(self) -> dict:
        return {
            "installed": self.installed,
            "path": str(self.path) if self.path else None,
            "is_managed": self.is_managed,
            "backed_up": str(self.backed_up) if self.backed_up else None,
        }


def _hooks_dir(repo: Path) -> Path:
    return repo / ".git" / "hooks"


def status(repo: Path) -> HookStatus:
    hook = _hooks_dir(repo) / HOOK_NAME
    backup = _hooks_dir(repo) / (HOOK_NAME + BACKUP_SUFFIX)
    if not hook.exists():
        return HookStatus(
            installed=False,
            path=hook,
            is_managed=False,
            backed_up=backup if backup.exists() else None,
        )
    try:
        text = hook.read_text(encoding="utf-8")
    except OSError:
        text = ""
    return HookStatus(
        installed=True,
        path=hook,
        is_managed=MARKER in text,
        backed_up=backup if backup.exists() else None,
    )


def enable(repo: Path) -> HookStatus:
    """Install the managed post-commit hook.

    If an unmanaged hook already lives at the target path, it is moved
    to ``<name>.cbm-backup`` before ours is written, never deleted.
    """
    hdir = _hooks_dir(repo)
    hdir.mkdir(parents=True, exist_ok=True)
    hook = hdir / HOOK_NAME
    backup = hdir / (HOOK_NAME + BACKUP_SUFFIX)

    if hook.exists():
        try:
            existing = hook.read_text(encoding="utf-8")
        except OSError:
            existing = ""
        if MARKER not in existing and not backup.exists():
            hook.rename(backup)
        elif MARKER in existing:
            # Already ours — overwrite to pick up any script update.
            pass

    hook.write_text(HOOK_SCRIPT, encoding="utf-8")
    try:
        hook.chmod(0o755)
    except OSError:
        pass
    return status(repo)


def disable(repo: Path) -> HookStatus:
    """Uninstall the managed hook and restore any prior backup.

    Only removes the hook when we are sure we own it (MARKER present).
    If a ``.cbm-backup`` exists, it is renamed back into place.
    """
    hdir = _hooks_dir(repo)
    hook = hdir / HOOK_NAME
    backup = hdir / (HOOK_NAME + BACKUP_SUFFIX)

    if hook.exists():
        try:
            text = hook.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if MARKER in text:
            hook.unlink(missing_ok=True)

    if backup.exists() and not hook.exists():
        backup.rename(hook)

    return status(repo)
