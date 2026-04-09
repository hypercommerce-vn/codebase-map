"""BaseLearner abstract class — see architecture.md §4.2."""

# HC-AI | ticket: KMP-M0-02

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from knowledge_memory.core.learners.pattern import Pattern

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault

E = TypeVar("E")
C = TypeVar("C")


class BaseLearner(ABC, Generic[E, C]):
    """Abstract base class for every learner.

    A learner walks corpus evidence from a vault, clusters similar items,
    scores each cluster, and emits :class:`Pattern` objects above a
    confidence threshold. Concrete subclasses must override
    ``LEARNER_NAME``, ``LEARNER_CATEGORY`` and the four abstract methods.
    """

    #: Unique learner identifier (e.g. ``"codebase.naming"``).
    LEARNER_NAME: str = ""
    #: Category bucket for emitted patterns (e.g. ``"naming"``).
    LEARNER_CATEGORY: str = ""
    #: Minimum evidence count before the learner attempts to cluster.
    MIN_EVIDENCE_COUNT: int = 5
    #: Minimum confidence (0-100) required to emit a pattern.
    MIN_CONFIDENCE: float = 60.0

    @abstractmethod
    def extract_evidence(self, vault: "BaseVault") -> list[E]:
        """Pull raw evidence from the given vault corpus."""

    @abstractmethod
    def cluster(self, evidences: list[E]) -> list[C]:
        """Group evidence into clusters representing pattern candidates."""

    @abstractmethod
    def calculate_confidence(self, cluster: C) -> float:
        """Return a 0-100 confidence score for a cluster."""

    @abstractmethod
    def cluster_to_pattern(self, cluster: C) -> Pattern:
        """Convert a cluster into a committable :class:`Pattern` object."""

    # --- Convenience ------------------------------------------------------

    def describe(self) -> dict[str, Any]:
        """Return a short descriptor dict useful for logging / MCP."""
        return {
            "name": self.LEARNER_NAME,
            "category": self.LEARNER_CATEGORY,
            "min_evidence": self.MIN_EVIDENCE_COUNT,
            "min_confidence": self.MIN_CONFIDENCE,
        }
