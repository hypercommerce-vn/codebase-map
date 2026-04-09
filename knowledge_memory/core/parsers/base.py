"""BaseParser abstract class — see architecture.md §3 / §4.2."""

# HC-AI | ticket: KMP-M0-02

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterator

from knowledge_memory.core.parsers.evidence import Evidence


class BaseParser(ABC):
    """Abstract base class for every vertical parser.

    A parser converts raw source artefacts (files, rows, documents) into a
    stream of :class:`Evidence` objects that learners can consume. Concrete
    subclasses must set ``PARSER_NAME``/``SUPPORTED_EXTENSIONS`` and
    implement :meth:`parse`.
    """

    #: Short identifier (e.g. ``"python_ast"``, ``"hello_txt"``).
    PARSER_NAME: str = ""
    #: File extensions this parser can handle (e.g. ``(".py",)``).
    SUPPORTED_EXTENSIONS: tuple[str, ...] = ()

    @abstractmethod
    def parse(self, source: Path) -> Iterator[Evidence]:
        """Yield :class:`Evidence` objects extracted from ``source``."""

    def supports(self, source: Path) -> bool:
        """Return True if this parser can handle the given source path."""
        if not self.SUPPORTED_EXTENSIONS:
            return False
        return source.suffix in self.SUPPORTED_EXTENSIONS

    def describe(self) -> dict[str, Any]:
        """Return a short descriptor dict useful for logging / MCP."""
        return {
            "name": self.PARSER_NAME,
            "extensions": list(self.SUPPORTED_EXTENSIONS),
        }
