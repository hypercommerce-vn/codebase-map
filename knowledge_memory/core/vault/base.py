"""BaseVault abstract class — see architecture.md §4.1."""

# HC-AI | ticket: KMP-M0-02

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence


class BaseVault(ABC):
    """Abstract base class for every vertical vault.

    Concrete subclasses (e.g. ``CodebaseVault``) must set ``VERTICAL_NAME``
    and implement the four abstract methods below. Concrete helpers for
    reading/writing patterns will land on this class in M1.
    """

    #: Must be overridden by concrete subclasses (e.g. ``"codebase"``).
    VERTICAL_NAME: str = ""

    @abstractmethod
    def init(self, root: Path, force: bool = False) -> None:
        """Create the ``.knowledge-memory/<vertical>/`` folder structure.

        Args:
            root: Project root directory where the vault will be created.
            force: If True, overwrite any existing vault.
        """

    @abstractmethod
    def snapshot(self) -> "object":
        """Create a new snapshot of the corpus and return a Snapshot handle."""

    @abstractmethod
    def get_corpus_iterator(self) -> Iterator[Evidence]:
        """Yield :class:`Evidence` objects for learners to consume."""

    @abstractmethod
    def schema_extension_sql(self) -> str:
        """Return vertical-specific SQL (extra tables) appended to core schema."""

    # --- Concrete helpers (stubs — filled in M1) -------------------------

    def commit_pattern(self, pattern: Pattern) -> None:
        """Persist a :class:`Pattern` to the vault. (M1 implementation.)"""
        raise NotImplementedError("commit_pattern will be implemented in M1")

    def query_patterns(self, category: Optional[str] = None) -> list[Pattern]:
        """Query committed patterns, optionally filtered by category. (M1.)"""
        raise NotImplementedError("query_patterns will be implemented in M1")
