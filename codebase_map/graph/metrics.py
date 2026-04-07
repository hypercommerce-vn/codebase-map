# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Sprint metric tracking — record per-PR impact zones over time.

CM-S2-10: Persist {pr_number, timestamp, changed, impact, risk} entries
to `.codebase-map-cache/pr_metrics.json` for sprint health dashboards.
Threshold-based alerting on excessive impact zones.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD = 50
METRIC_FILENAME = "pr_metrics.json"


@dataclass
class PRMetric:
    """A single PR impact metric record."""

    pr_number: str
    timestamp: str
    ref: str
    changed_files: int
    changed_nodes: int
    impact_zone: int
    risk: str  # "low" | "medium" | "high"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MetricStore:
    """Persistent store for PR impact metrics."""

    path: Path
    threshold: int = DEFAULT_THRESHOLD
    entries: list[PRMetric] = field(default_factory=list)

    @classmethod
    def load(cls, cache_dir: Path, threshold: int = DEFAULT_THRESHOLD) -> MetricStore:
        store = cls(path=cache_dir / METRIC_FILENAME, threshold=threshold)
        if store.path.exists():
            try:
                data = json.loads(store.path.read_text(encoding="utf-8"))
                store.entries = [PRMetric(**e) for e in data.get("entries", [])]
                store.threshold = data.get("threshold", threshold)
            except (json.JSONDecodeError, TypeError):
                pass
        return store

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "threshold": self.threshold,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "entries": [e.to_dict() for e in self.entries],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def record(
        self,
        pr_number: str,
        ref: str,
        changed_files: int,
        changed_nodes: int,
        impact_zone: int,
    ) -> PRMetric:
        risk = self._classify(impact_zone)
        metric = PRMetric(
            pr_number=pr_number,
            timestamp=datetime.now(timezone.utc).isoformat(),
            ref=ref,
            changed_files=changed_files,
            changed_nodes=changed_nodes,
            impact_zone=impact_zone,
            risk=risk,
        )
        self.entries.append(metric)
        return metric

    def _classify(self, impact: int) -> str:
        if impact > self.threshold:
            return "high"
        if impact >= max(10, self.threshold // 5):
            return "medium"
        return "low"

    def summary(self) -> dict[str, Any]:
        if not self.entries:
            return {"total": 0, "by_risk": {}, "avg_impact": 0}
        by_risk: dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        total_impact = 0
        for e in self.entries:
            by_risk[e.risk] = by_risk.get(e.risk, 0) + 1
            total_impact += e.impact_zone
        return {
            "total": len(self.entries),
            "by_risk": by_risk,
            "avg_impact": round(total_impact / len(self.entries), 1),
            "threshold": self.threshold,
        }
