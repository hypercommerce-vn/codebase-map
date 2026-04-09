"""Parser abstraction — see architecture.md §3.

Exposes the :class:`~knowledge_memory.core.parsers.evidence.Evidence` dataclass,
which is the raw input unit every learner consumes.
"""

# HC-AI | ticket: KMP-M0-02

from knowledge_memory.core.parsers.evidence import Evidence

__all__ = ["Evidence"]
