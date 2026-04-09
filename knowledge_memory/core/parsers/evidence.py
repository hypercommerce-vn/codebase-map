"""Evidence dataclass — raw unit of corpus data. See architecture.md §4.2."""

# HC-AI | ticket: KMP-M0-02

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Evidence:
    """A raw piece of evidence yielded by a parser for learners to consume.

    Attributes:
        source: Origin identifier (e.g. file path, URL, document id).
        data: Arbitrary parser-specific payload (text, AST node, row, ...).
        line_range: Optional ``(start, end)`` 1-indexed line range in source.
        commit_sha: Optional git commit SHA the evidence was extracted from.
        metadata: Free-form extra fields (parser-specific).
    """

    source: str
    data: dict[str, Any] = field(default_factory=dict)
    line_range: Optional[tuple[int, int]] = None
    commit_sha: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
