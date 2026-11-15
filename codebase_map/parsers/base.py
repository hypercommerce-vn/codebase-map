# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Abstract base parser — extend for each language."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from codebase_map.graph.models import Edge, Node


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
