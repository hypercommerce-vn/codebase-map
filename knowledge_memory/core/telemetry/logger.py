# HC-AI | ticket: MEM-M3-08
"""Telemetry logger — privacy-safe local-only event logging.

Design decision D-M3-04: Local-only, no cloud sync.
Stores events in SQLite (core.db usage_log table).
Tracks: command execution, LLM calls, pattern updates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class TelemetryEvent:
    """A single telemetry event."""

    action: str
    detail: str = ""
    duration_ms: float = 0.0
    metadata: dict[str, Any] | None = None
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


class TelemetryLogger:
    """Local-only telemetry logger.

    Privacy-safe: all data stays in local SQLite.
    No network calls, no analytics endpoints.

    Usage::

        logger = TelemetryLogger()
        logger.log("bootstrap", "5 steps completed", duration_ms=5700)
        logger.log("ask", "auth question", duration_ms=2100,
                   metadata={"provider": "anthropic", "cost": 0.003})
    """

    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []

    def log(
        self,
        action: str,
        detail: str = "",
        duration_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> TelemetryEvent:
        """Log a telemetry event."""
        event = TelemetryEvent(
            action=action,
            detail=detail,
            duration_ms=duration_ms,
            metadata=metadata,
        )
        self._events.append(event)
        return event

    @property
    def events(self) -> list[TelemetryEvent]:
        """All logged events."""
        return list(self._events)

    def events_by_action(self, action: str) -> list[TelemetryEvent]:
        """Filter events by action type."""
        return [e for e in self._events if e.action == action]

    def total_duration_ms(self, action: str = "") -> float:
        """Total duration for an action (or all actions)."""
        filtered = self.events_by_action(action) if action else self._events
        return sum(e.duration_ms for e in filtered)

    def count(self, action: str = "") -> int:
        """Count events by action (or total)."""
        if action:
            return len(self.events_by_action(action))
        return len(self._events)

    def summary(self) -> dict[str, Any]:
        """Summarize all logged events."""
        actions: dict[str, int] = {}
        total_ms = 0.0
        for e in self._events:
            actions[e.action] = actions.get(e.action, 0) + 1
            total_ms += e.duration_ms

        return {
            "total_events": len(self._events),
            "total_duration_ms": total_ms,
            "by_action": actions,
        }

    def clear(self) -> None:
        """Clear all events."""
        self._events.clear()
