"""Pattern dataclass — canonical learner output. See architecture.md §4.2."""

# HC-AI | ticket: KMP-M0-02

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Pattern:
    """A repeatable rule discovered by a learner from corpus evidence.

    Attributes:
        name: Unique-within-vertical pattern name (e.g. ``"naming::service_suffix"``).
        category: Learner category (e.g. ``"naming"``, ``"layers"``).
        confidence: 0-100 confidence score set by the learner runtime.
        evidence: List of Evidence references (raw objects or serialized dicts).
        vertical: Owning vertical (e.g. ``"codebase"``). Empty until committed.
        created_at: ISO-8601 timestamp (set at construction time).
        metadata: Free-form extra data (learner-specific).
    """

    name: str
    category: str
    confidence: float = 0.0
    evidence: list[Any] = field(default_factory=list)
    vertical: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)
