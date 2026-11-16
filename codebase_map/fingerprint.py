# HC-AI | ticket: FDD-TOOL-CODEMAP
"""VIBE-102: content fingerprints for functions and files.

A fingerprint is a short hash of source text with whitespace collapsed, so
re-indenting or re-wrapping code does not change it but any edit to a token,
string or comment does. The snapshot diff compares fingerprints to see that a
function body or a file changed even when no signature did.
"""

from __future__ import annotations

import hashlib
from typing import Iterable, Sequence

HASH_LENGTH = 16


def text_hash(text: str) -> str:
    """Hash text after collapsing every run of whitespace to one space."""
    normalised = " ".join(text.split())
    return hashlib.sha256(normalised.encode("utf-8")).hexdigest()[:HASH_LENGTH]


def lines_hash(lines: list[str], start: int, end: int) -> str:
    """Hash the 1-based, inclusive line range ``start..end``."""
    return text_hash("\n".join(lines[start - 1 : max(start, end)]))


def lines_hash_excluding(
    lines: list[str], start: int, end: int, holes: Iterable[tuple[int, int]]
) -> str:
    """Hash ``start..end`` without the line ranges listed in ``holes``."""
    skipped = _line_set(holes)
    kept = [
        line
        for number, line in enumerate(lines[start - 1 : max(start, end)], start)
        if number not in skipped
    ]
    return text_hash("\n".join(kept))


def module_level_hash(lines: list[str], covered: Iterable[tuple[int, int]]) -> str:
    """Hash the lines that are not inside any function or class."""
    return lines_hash_excluding(lines, 1, len(lines), covered)


def exclusive_hashes(lines: list[str], ranges: Sequence[tuple[int, int]]) -> list[str]:
    """Fingerprint each line range without the ranges nested inside it.

    Every line then counts towards exactly one fingerprint — the innermost
    function or class that contains it — so editing a method changes the
    method's fingerprint and not its class's. The result is in input order.
    """
    hashes: list[str] = []
    for index, (start, end) in enumerate(ranges):
        holes = [
            (other_start, other_end)
            for other, (other_start, other_end) in enumerate(ranges)
            if other != index
            and (other_start, other_end) != (start, end)
            and start <= other_start
            and other_end <= end
        ]
        hashes.append(lines_hash_excluding(lines, start, end, holes))
    return hashes


def named_hashes(
    lines: list[str], items: Sequence[tuple[str, int, int]]
) -> dict[str, str]:
    """Exclusive fingerprints keyed by name, for ``(name, start, end)`` items.

    Two items may share a name — the graph keys nodes by id, and two helpers
    called ``handleClick`` in one file get the same id. Their fingerprints are
    combined, so an edit to either one changes the fingerprint of that name.
    """
    per_item = exclusive_hashes(lines, [(start, end) for _, start, end in items])
    grouped: dict[str, list[str]] = {}
    for (name, _, _), digest in zip(items, per_item):
        grouped.setdefault(name, []).append(digest)
    return {
        name: digests[0] if len(digests) == 1 else text_hash(" ".join(digests))
        for name, digests in grouped.items()
    }


def _line_set(ranges: Iterable[tuple[int, int]]) -> set[int]:
    numbers: set[int] = set()
    for start, end in ranges:
        numbers.update(range(start, max(start, end) + 1))
    return numbers
