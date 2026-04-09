# HC-AI | ticket: KMP-M0-05
"""HelloLearner — trivial reference learner that counts word frequency."""

from typing import TYPE_CHECKING

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault


class HelloLearner(BaseLearner[Evidence, dict]):
    """Count word frequency across Evidence — reference implementation."""

    LEARNER_NAME = "hello.word_count"
    LEARNER_CATEGORY = "stats"
    MIN_EVIDENCE_COUNT = 1
    MIN_CONFIDENCE = 50.0

    def extract_evidence(self, vault: "BaseVault") -> list[Evidence]:
        """Return all evidence from the vault corpus iterator."""
        return list(vault.get_corpus_iterator())

    def cluster(self, evidences: list[Evidence]) -> list[dict]:
        """Group evidence by individual words."""
        words: dict[str, list[Evidence]] = {}
        for ev in evidences:
            for word in ev.data.get("text", "").split():
                words.setdefault(word.lower(), []).append(ev)
        return [
            {"word": w, "evidences": evs}
            for w, evs in words.items()
            if len(evs) >= self.MIN_EVIDENCE_COUNT
        ]

    def calculate_confidence(self, cluster: dict) -> float:
        """Confidence scales with evidence count (capped at 100)."""
        return min(100.0, len(cluster["evidences"]) * 20.0)

    def cluster_to_pattern(self, cluster: dict) -> Pattern:
        """Convert a word cluster into a Pattern."""
        return Pattern(
            name=f"frequent_word::{cluster['word']}",
            category=self.LEARNER_CATEGORY,
            confidence=0.0,
            evidence=cluster["evidences"][:20],
        )
