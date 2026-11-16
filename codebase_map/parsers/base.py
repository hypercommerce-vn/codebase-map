# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Abstract base parser — extend for each language."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from codebase_map.graph.models import Edge, Node


# HC-AI | ticket: FDD-TOOL-CODEMAP
# VIBE-102: one way to turn a source file into text, shared by the parsers and
# the builder, so they agree on what line 1 is.
def decode_source(raw: bytes) -> str:
    """Decode source bytes: UTF-8 with or without a BOM, or UTF-16 with a BOM.

    Editors on Windows write the BOM; left in, it hides the first line from
    every pattern that looks for a statement at the start of a line.
    """
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


class BaseParser(ABC):
    """Interface for language-specific parsers."""

    @abstractmethod
    def parse_file(
        self, file_path: Path, base_module: str = "", rel_path: Path | None = None
    ) -> tuple[list[Node], list[Edge]]:
        """Parse a single file and return nodes + edges.

        ``file_path`` is where the file is read from. ``rel_path`` is the same
        file relative to the project root; when given, node ids, layer and
        domain are derived from it so they do not depend on where the project
        sits on disk.
        """
        ...

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of file extensions this parser handles."""
        ...

    # VIBE-102: True where indentation is syntax, so fingerprints keep it
    indent_matters = False

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-103: optional hooks, used to tell which file depends on which and
    # which top-level lines cannot change how the program behaves.
    def module_id(self, rel_path: Path, base_module: str = "") -> str:
        """Module id of a project file, as used in node ids and import targets."""
        return ""

    def non_runtime_ranges(self, lines: list[str]) -> list[tuple[int, int]]:
        """1-based line ranges outside functions that do not run: imports, types."""
        return []
