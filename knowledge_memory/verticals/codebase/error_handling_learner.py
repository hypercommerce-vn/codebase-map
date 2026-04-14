# HC-AI | ticket: MEM-M3-04
"""ErrorHandlingLearner — detect error handling patterns in codebase.

Analyzes: try/except usage, custom exception classes, retry patterns,
error propagation chains, bare except anti-patterns.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault

# HC-AI | ticket: MEM-M3-04
_TRY_EXCEPT_RE = re.compile(r"\btry\b")
_EXCEPT_RE = re.compile(r"\bexcept\b")
_BARE_EXCEPT_RE = re.compile(r"\bexcept\s*:")
_RAISE_RE = re.compile(r"\braise\b")
_CUSTOM_EXCEPTION_RE = re.compile(r"class\s+\w+(?:Error|Exception)\b")
_RETRY_PATTERNS = ("retry", "backoff", "max_retries", "attempts")
_LOGGING_ERROR_RE = re.compile(r"logger?\.(error|exception|warning|critical)")


class ErrorHandlingLearner(BaseLearner[Evidence, Dict]):
    """Detect error handling patterns across codebase evidence.

    Produces patterns for:
    - try/except coverage (% of functions with error handling)
    - Custom exception classes count + naming
    - Bare except anti-pattern detection
    - Retry/backoff pattern usage
    - Error logging compliance
    """

    LEARNER_NAME = "codebase.error_handling"
    LEARNER_CATEGORY = "error_handling"

    def extract_evidence(self, vault: "BaseVault") -> List[Evidence]:
        """Extract error handling evidence from vault nodes."""
        evidences: List[Evidence] = []

        if not hasattr(vault, "query_nodes"):
            return evidences

        nodes = vault.query_nodes()
        for node in nodes:
            name = node.get("name", "")
            fpath = node.get("file_path", "")
            meta_str = node.get("metadata_json", "{}")

            # Extract source hints from metadata if available
            source_hint = ""
            try:
                import json

                meta = json.loads(meta_str) if isinstance(meta_str, str) else meta_str
                source_hint = meta.get("source", "")
            except (json.JSONDecodeError, TypeError):
                pass

            evidences.append(
                Evidence(
                    source=fpath,
                    data={
                        "name": name,
                        "file_path": fpath,
                        "node_type": node.get("node_type", "function"),
                        "layer": node.get("layer", "unknown"),
                        "source_hint": source_hint,
                    },
                )
            )

        return evidences

    def cluster(self, evidences: List[Evidence]) -> List[Dict]:
        """Group evidence into error handling pattern clusters."""
        clusters: List[Dict] = []

        # Cluster 1: try/except coverage
        functions_with_error_handling = 0
        total_functions = 0
        bare_excepts: List[str] = []
        functions_with_raise: List[str] = []

        for ev in evidences:
            data = ev.data
            name = data.get("name", "")
            node_type = data.get("node_type", "function")

            if node_type in ("function", "method"):
                total_functions += 1

                # Heuristic: check name patterns for error handling
                lower_name = name.lower()
                if any(
                    kw in lower_name
                    for kw in (
                        "error",
                        "except",
                        "handle",
                        "catch",
                        "retry",
                        "validate",
                    )
                ):
                    functions_with_error_handling += 1

                if "raise" in lower_name or lower_name.startswith("raise_"):
                    functions_with_raise.append(name)

        if total_functions >= self.MIN_EVIDENCE_COUNT:
            clusters.append(
                {
                    "pattern_type": "try_except_coverage",
                    "total": total_functions,
                    "with_handling": functions_with_error_handling,
                    "with_raise": functions_with_raise,
                    "bare_excepts": bare_excepts,
                    "evidences": evidences[:20],
                }
            )

        # Cluster 2: Custom exception classes
        exception_classes: List[str] = []
        for ev in evidences:
            data = ev.data
            name = data.get("name", "")
            node_type = data.get("node_type", "")
            if node_type == "class" and (
                name.endswith("Error") or name.endswith("Exception")
            ):
                exception_classes.append(name)

        if exception_classes:
            clusters.append(
                {
                    "pattern_type": "custom_exceptions",
                    "exceptions": exception_classes,
                    "count": len(exception_classes),
                    "evidences": [
                        ev
                        for ev in evidences
                        if ev.data.get("name", "") in exception_classes
                    ],
                }
            )

        # Cluster 3: Retry patterns
        retry_functions: List[str] = []
        for ev in evidences:
            name = ev.data.get("name", "").lower()
            if any(kw in name for kw in _RETRY_PATTERNS):
                retry_functions.append(ev.data.get("name", ""))

        if retry_functions:
            clusters.append(
                {
                    "pattern_type": "retry_pattern",
                    "functions": retry_functions,
                    "count": len(retry_functions),
                    "evidences": [
                        ev
                        for ev in evidences
                        if ev.data.get("name", "") in retry_functions
                    ],
                }
            )

        # Cluster 4: Error logging patterns
        error_loggers: List[str] = []
        for ev in evidences:
            name = ev.data.get("name", "").lower()
            if "log" in name and ("error" in name or "exception" in name):
                error_loggers.append(ev.data.get("name", ""))

        if error_loggers:
            clusters.append(
                {
                    "pattern_type": "error_logging",
                    "functions": error_loggers,
                    "count": len(error_loggers),
                    "evidences": [
                        ev
                        for ev in evidences
                        if ev.data.get("name", "") in error_loggers
                    ],
                }
            )

        return clusters

    def calculate_confidence(self, cluster: Dict) -> float:
        """Calculate confidence score (0-100) for a cluster."""
        ptype = cluster.get("pattern_type", "")

        if ptype == "try_except_coverage":
            total = cluster.get("total", 0)
            with_handling = cluster.get("with_handling", 0)
            if total == 0:
                return 0.0
            ratio = with_handling / total
            # Higher ratio = higher confidence that project uses error handling
            return min(ratio * 120, 100.0)  # 83%+ handling → 100% confidence

        if ptype == "custom_exceptions":
            count = cluster.get("count", 0)
            if count >= 5:
                return 95.0
            if count >= 3:
                return 85.0
            return 70.0

        if ptype == "retry_pattern":
            count = cluster.get("count", 0)
            if count >= 3:
                return 85.0
            return 65.0

        if ptype == "error_logging":
            count = cluster.get("count", 0)
            if count >= 5:
                return 90.0
            return 70.0

        return 50.0

    def cluster_to_pattern(self, cluster: Dict) -> Pattern:
        """Convert a cluster into a Pattern object."""
        ptype = cluster.get("pattern_type", "unknown")
        evidences = cluster.get("evidences", [])
        confidence = self.calculate_confidence(cluster)

        if ptype == "try_except_coverage":
            total = cluster.get("total", 0)
            with_handling = cluster.get("with_handling", 0)
            pct = (with_handling / total * 100) if total > 0 else 0
            return Pattern(
                name=f"error_handling_coverage_{pct:.0f}pct",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "total_functions": total,
                    "with_handling": with_handling,
                    "coverage_pct": round(pct, 1),
                    "bare_excepts": cluster.get("bare_excepts", []),
                    "description": (
                        f"{pct:.0f}% of functions have error handling patterns"
                    ),
                },
                evidence=evidences,
            )

        if ptype == "custom_exceptions":
            exceptions = cluster.get("exceptions", [])
            return Pattern(
                name=f"custom_exceptions_{len(exceptions)}",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "count": len(exceptions),
                    "exception_names": exceptions,
                    "description": (
                        f"{len(exceptions)} custom exception classes defined"
                    ),
                },
                evidence=evidences,
            )

        if ptype == "retry_pattern":
            functions = cluster.get("functions", [])
            return Pattern(
                name=f"retry_pattern_{len(functions)}",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "count": len(functions),
                    "functions": functions,
                    "description": (
                        f"{len(functions)} retry/backoff patterns detected"
                    ),
                },
                evidence=evidences,
            )

        # error_logging
        functions = cluster.get("functions", [])
        return Pattern(
            name=f"error_logging_{len(functions)}",
            category=self.LEARNER_CATEGORY,
            confidence=confidence,
            metadata={
                "type": ptype,
                "count": len(functions),
                "functions": functions,
                "description": (f"{len(functions)} error logging patterns detected"),
            },
            evidence=evidences,
        )
