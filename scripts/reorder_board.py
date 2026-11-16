#!/usr/bin/env python3
# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Put the sections of project/board.html into reading order.

The board grew by appending, so the sprint sections ended up interleaved with
the PR history, CI and decision sections. This script moves whole blocks; it
never edits a line. Order after running it:

    header and overview
    CM-S1 · CM-S2 · CM-S3            (sprint task boards, oldest first)
    CBM-INT-S1 · S2 · S3 · CBM-VIBE  (initiative task boards)
    Acceptance criteria
    Key decisions (timeline)
    CI pipeline
    PR history                        (the long table, last)
    sub-pages and footer

A block starts at its marker line and runs to the next marker. Run it again
after other edits to the board: it is idempotent, and it refuses to write if
any line would be lost or duplicated.

Usage:  python3 scripts/reorder_board.py [--check] [path]
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "project" / "board.html"
RULE = "  <!-- ══"

# (key, how to find the first line of the block)
#   ("line", text)   the line that equals text
#   ("rule", h2 id)  the "<!-- ══" comment that opens the section with that h2 id
MARKERS = [
    ("cm-s1", ("line", "  <!-- CM-S1 Task Board -->")),
    ("pr-history", ("line", "  <!-- PR History -->")),
    ("ci", ("line", "  <!-- CI Pipeline -->")),
    ("acceptance", ("line", "  <!-- Acceptance Criteria -->")),
    ("decisions", ("line", "  <!-- Key Decisions -->")),
    ("cm-s2", ("line", "  <!-- CM-S2 Task Board -->")),
    ("cm-s3", ("line", "  <!-- CM-S3 Task Board -->")),
    ("cbm-int-s1", ("rule", "cbm-int-s1")),
    ("cbm-int-s2", ("rule", "cbm-int-s2")),
    ("cbm-int-s3", ("rule", "cbm-int-s3")),
    ("cbm-vibe-t1", ("rule", "cbm-vibe-t1")),
    ("footer", ("line", "</div><!-- /page-board -->")),
]
OPTIONAL = {"cbm-vibe-t1"}

TARGET = [
    "header",
    "cm-s1",
    "cm-s2",
    "cm-s3",
    "cbm-int-s1",
    "cbm-int-s2",
    "cbm-int-s3",
    "cbm-vibe-t1",
    "acceptance",
    "decisions",
    "ci",
    "pr-history",
    "footer",
]


def _find(lines: list[str], how: tuple[str, str]) -> int | None:
    kind, value = how
    if kind == "line":
        hits = [i for i, line in enumerate(lines) if line == value]
    else:
        hits = []
        for i, line in enumerate(lines):
            if line.lstrip().startswith(f'<h2 id="{value}"'):
                start = i
                while start > 0 and not lines[start].startswith(RULE):
                    start -= 1
                # an attribution comment directly above the rule belongs to it
                if start > 0 and lines[start - 1].startswith("  <!-- HC-AI"):
                    start -= 1
                hits.append(start)
    if len(hits) > 1:
        raise SystemExit(f"[ERROR] Marker for {value!r} found {len(hits)} times.")
    return hits[0] if hits else None


def split_blocks(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    """Return (block keys in file order, {key: lines})."""
    starts: list[tuple[int, str]] = []
    for key, how in MARKERS:
        index = _find(lines, how)
        if index is None:
            if key in OPTIONAL:
                continue
            raise SystemExit(f"[ERROR] Marker for block {key!r} not found.")
        starts.append((index, key))
    starts.sort()
    order = ["header"] + [key for _, key in starts]
    bounds = [0] + [index for index, _ in starts] + [len(lines)]
    blocks = {key: lines[bounds[n] : bounds[n + 1]] for n, key in enumerate(order)}
    return order, blocks


def reorder(text: str) -> tuple[str, list[str], list[str]]:
    """Return (new text, order before, order after)."""
    lines = text.split("\n")
    before, blocks = split_blocks(lines)
    after = [key for key in TARGET if key in blocks]
    if set(after) != set(before):
        raise SystemExit("[ERROR] Unknown block; nothing written.")
    new_lines = [line for key in after for line in blocks[key]]
    if Counter(new_lines) != Counter(lines) or len(new_lines) != len(lines):
        raise SystemExit("[ERROR] Lines would be lost or duplicated; nothing written.")
    return "\n".join(new_lines), before, after


def main(argv: list[str]) -> int:
    check = "--check" in argv
    paths = [arg for arg in argv if not arg.startswith("--")]
    path = Path(paths[0]) if paths else DEFAULT_PATH
    text = path.read_text(encoding="utf-8")
    new_text, before, after = reorder(text)
    if before == after:
        print(f"[OK] {path.name}: sections are already in order.")
        return 0
    print("Before: " + " · ".join(before))
    print("After:  " + " · ".join(after))
    if check:
        print("[CHECK] Not in order; run without --check to rewrite.")
        return 1
    path.write_text(new_text, encoding="utf-8")
    print(
        f"[OK] {path.name} rewritten: {len(new_text.splitlines())} lines, none edited."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
