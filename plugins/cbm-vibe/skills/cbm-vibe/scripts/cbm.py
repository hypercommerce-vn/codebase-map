#!/usr/bin/env python3
# HC-AI | ticket: FDD-TOOL-CODEMAP
"""VIBE-104: run codebase-map from inside the skill, with nothing installed.

Usage:  python3 cbm.py <codebase-map arguments>
   e.g. python3 cbm.py features status --json

The distributed skill carries a copy of the ``codebase_map`` package in
``vendor/`` next to this file. Inside the codebase-map repository there is no
copy; the package at the repository root is used instead.
"""

import sys
from pathlib import Path

MINIMUM_PYTHON = (3, 9)


def _package_root():
    """The folder that holds the ``codebase_map`` package, or None."""
    here = Path(__file__).resolve().parent
    candidates = [here / "vendor"]
    candidates.extend(here.parents)  # the repository root, when run from the repo
    for candidate in candidates:
        if (candidate / "codebase_map" / "cli.py").is_file():
            return candidate
    return None


def main():
    if sys.version_info < MINIMUM_PYTHON:
        found = "%d.%d" % sys.version_info[:2]
        print("[ERROR] Python 3.9 or newer is needed (found %s)." % found)
        return 2
    root = _package_root()
    if root is None:
        print("[ERROR] The bundled codebase_map package is missing next to cbm.py.")
        return 2
    sys.path.insert(0, str(root))
    from codebase_map.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
