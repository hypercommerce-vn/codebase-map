"""Learner Runtime — orchestrates learners that extract patterns from vaults.

See architecture.md §4.2. The :class:`~knowledge_memory.core.learners.pattern.Pattern`
dataclass is the canonical output of every learner.
"""

# HC-AI | ticket: KMP-M0-02

from knowledge_memory.core.learners.pattern import Pattern

__all__ = ["Pattern"]
