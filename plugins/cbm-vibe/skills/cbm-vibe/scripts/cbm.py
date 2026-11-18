#!/usr/bin/env python3
# HC-AI | ticket: FDD-TOOL-CODEMAP
"""VIBE-104: run codebase-map from inside the skill, with nothing installed.

Usage:  python3 cbm.py <codebase-map arguments>
   e.g. python3 cbm.py features status --json

The distributed skill carries a copy of the ``codebase_map`` package in
``vendor/`` next to this file. Inside the codebase-map repository there is no
copy; the package at the repository root is used instead.

The skill pre-approves this script by its exact command line, so whatever it
runs happens without the user being asked first. It therefore runs only the
commands that read the project, write the map and the snapshots into it, and
keep the feature store. The rest of codebase-map is refused here: starting the
local web server or installing git hooks (``mod``), sending a notification
(``check-staleness``), writing to a path given on the command line
(``api-catalog``), deleting snapshots (``snapshots clean``). A command added
to codebase-map later is refused too, until it is listed here on purpose.
"""

import sys
from pathlib import Path

MINIMUM_PYTHON = (3, 9)

# HC-AI | ticket: FDD-TOOL-CODEMAP
# ``snapshots`` is here for ``snapshots list`` only; see _refusal.
ALLOWED_COMMANDS = frozenset(
    {
        "generate",
        "features",
        "query",
        "impact",
        "summary",
        "search",
        "snapshot-diff",
        "snapshots",
    }
)
# Known commands that stay out. tests/codebase_map/test_cbm_vibe_plugin.py
# fails when the CLI has a command that is in neither set.
REFUSED_COMMANDS = frozenset(
    {"mod", "check-staleness", "api-catalog", "diff", "coverage"}
)


def _package_root():
    """The folder that holds the ``codebase_map`` package, or None."""
    here = Path(__file__).resolve().parent
    candidates = [here / "vendor"]
    candidates.extend(here.parents)  # the repository root, when run from the repo
    for candidate in candidates:
        if (candidate / "codebase_map" / "cli.py").is_file():
            return candidate
    return None


def _refusal(args):
    """Why this parsed command line is not run from the skill, or None."""
    command = getattr(args, "command", None)
    if command is None:  # no command given: the tool prints its help
        return None
    if command not in ALLOWED_COMMANDS:
        return "'%s' is not available from the CBM-VIBE skill." % command
    if command == "snapshots" and getattr(args, "action", None) != "list":
        return "'snapshots %s' is not available from the CBM-VIBE skill." % (
            getattr(args, "action", "")
        )
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
    from codebase_map.cli import build_parser
    from codebase_map.cli import main as cli_main

    # The same parser the tool uses decides which command this is, so the
    # check cannot disagree with what would run.
    refusal = _refusal(build_parser().parse_args())
    if refusal:
        print("[ERROR] " + refusal)
        print("        Commands here: " + ", ".join(sorted(ALLOWED_COMMANDS)) + ".")
        return 2
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
