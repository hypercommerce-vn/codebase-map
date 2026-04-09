"""LearnerRuntime — orchestrator wiring vault + learners + parsers.

See architecture.md §4.2. Day-2 scope delivers the interface + skeleton
body; richer scheduling (parallel execution, progress reporting, snapshot
integration) lands in M1.
"""

# HC-AI | ticket: KMP-M0-03

from typing import TYPE_CHECKING, Optional

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.base import BaseParser

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault


class LearnerRuntime:
    """Coordinate learners and parsers against a vault.

    The runtime owns two registries (learners and parsers) and exposes a
    single :meth:`run` entry point that iterates the registered learners,
    delegates extraction/clustering to each, and commits high-confidence
    patterns to the vault.
    """

    def __init__(
        self,
        vault: Optional["BaseVault"] = None,
        learners: Optional[list[BaseLearner]] = None,
        parsers: Optional[list[BaseParser]] = None,
    ) -> None:
        self.vault: Optional["BaseVault"] = vault
        self._learners: list[BaseLearner] = list(learners or [])
        self._parsers: list[BaseParser] = list(parsers or [])

    # --- Registration -----------------------------------------------------

    def register_learner(self, learner: BaseLearner) -> None:
        """Add a learner to the runtime registry."""
        if not isinstance(learner, BaseLearner):
            raise TypeError(
                f"Expected BaseLearner instance, got {type(learner).__name__}"
            )
        self._learners.append(learner)

    def register_parser(self, parser: BaseParser) -> None:
        """Add a parser to the runtime registry."""
        if not isinstance(parser, BaseParser):
            raise TypeError(
                f"Expected BaseParser instance, got {type(parser).__name__}"
            )
        self._parsers.append(parser)

    @property
    def learners(self) -> list[BaseLearner]:
        return list(self._learners)

    @property
    def parsers(self) -> list[BaseParser]:
        return list(self._parsers)

    # --- Execution --------------------------------------------------------

    def run(self, vault: Optional["BaseVault"] = None) -> list[Pattern]:
        """Run every registered learner against ``vault`` and return patterns.

        For each learner the runtime: extracts evidence, short-circuits if
        below ``MIN_EVIDENCE_COUNT``, clusters, scores, and commits every
        cluster whose confidence meets ``MIN_CONFIDENCE`` to the vault.
        """
        target_vault = vault or self.vault
        if target_vault is None:
            raise ValueError("LearnerRuntime.run requires a vault")

        emitted: list[Pattern] = []
        for learner in self._learners:
            evidence = learner.extract_evidence(target_vault)
            if len(evidence) < learner.MIN_EVIDENCE_COUNT:
                continue
            for cluster in learner.cluster(evidence):
                confidence = learner.calculate_confidence(cluster)
                if confidence < learner.MIN_CONFIDENCE:
                    continue
                pattern = learner.cluster_to_pattern(cluster)
                pattern.confidence = confidence
                if not pattern.vertical:
                    pattern.vertical = getattr(type(target_vault), "VERTICAL_NAME", "")
                target_vault.commit_pattern(pattern)
                emitted.append(pattern)
        return emitted
