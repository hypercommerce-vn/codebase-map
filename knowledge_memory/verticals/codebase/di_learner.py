# HC-AI | ticket: MEM-M3-05
"""DependencyInjectionLearner — detect DI patterns in codebase.

Analyzes: constructor injection, service locator, factory patterns,
singleton usage, and dependency inversion compliance.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault

# HC-AI | ticket: MEM-M3-05
_INIT_RE = re.compile(r"^__init__$")
_CONSTRUCTOR_PARAMS_HINTS = (
    "service",
    "repository",
    "repo",
    "client",
    "provider",
    "handler",
    "manager",
    "factory",
    "gateway",
    "adapter",
    "bus",
    "dispatcher",
)
_FACTORY_NAMES = (
    "create_",
    "build_",
    "make_",
    "get_instance",
    "get_provider",
    "factory",
)
_SINGLETON_NAMES = ("instance", "singleton", "_instance", "get_instance")
_LOCATOR_NAMES = ("get_service", "resolve", "locate", "container", "injector")


class DependencyInjectionLearner(BaseLearner[Evidence, Dict]):
    """Detect dependency injection patterns in codebase evidence.

    Produces patterns for:
    - Constructor injection (% of __init__ with service params)
    - Factory pattern usage
    - Service locator anti-pattern detection
    - Singleton usage
    """

    LEARNER_NAME = "codebase.dependency_injection"
    LEARNER_CATEGORY = "dependency_injection"

    def extract_evidence(self, vault: "BaseVault") -> List[Evidence]:
        """Extract DI-related evidence from vault nodes."""
        evidences: List[Evidence] = []

        if not hasattr(vault, "query_nodes"):
            return evidences

        nodes = vault.query_nodes()
        for node in nodes:
            name = node.get("name", "")
            fpath = node.get("file_path", "")

            evidences.append(
                Evidence(
                    source=fpath,
                    data={
                        "name": name,
                        "file_path": fpath,
                        "node_type": node.get("node_type", "function"),
                        "layer": node.get("layer", "unknown"),
                    },
                )
            )

        return evidences

    def cluster(self, evidences: List[Evidence]) -> List[Dict]:
        """Group evidence into DI pattern clusters."""
        clusters: List[Dict] = []

        constructors_with_injection: List[str] = []
        constructors_total = 0
        factory_functions: List[str] = []
        singleton_refs: List[str] = []
        locator_refs: List[str] = []

        for ev in evidences:
            data = ev.data
            name = data.get("name", "")
            lower_name = name.lower()

            # Constructor injection detection
            if name == "__init__":
                constructors_total += 1
                # Check file path for service/handler hints
                fpath = data.get("file_path", "").lower()
                if any(h in fpath for h in _CONSTRUCTOR_PARAMS_HINTS):
                    constructors_with_injection.append(data.get("file_path", ""))

            # Factory pattern detection
            if any(lower_name.startswith(f) for f in _FACTORY_NAMES):
                factory_functions.append(name)

            # Singleton detection
            if any(s in lower_name for s in _SINGLETON_NAMES):
                singleton_refs.append(name)

            # Service locator detection
            if any(loc in lower_name for loc in _LOCATOR_NAMES):
                locator_refs.append(name)

        # Cluster 1: Constructor injection
        if constructors_total >= self.MIN_EVIDENCE_COUNT:
            clusters.append(
                {
                    "pattern_type": "constructor_injection",
                    "total_constructors": constructors_total,
                    "with_injection": len(constructors_with_injection),
                    "files": constructors_with_injection[:10],
                    "evidences": evidences[:20],
                }
            )

        # Cluster 2: Factory pattern
        if factory_functions:
            clusters.append(
                {
                    "pattern_type": "factory_pattern",
                    "functions": factory_functions,
                    "count": len(factory_functions),
                    "evidences": [
                        ev
                        for ev in evidences
                        if ev.data.get("name", "") in factory_functions
                    ],
                }
            )

        # Cluster 3: Singleton
        if singleton_refs:
            clusters.append(
                {
                    "pattern_type": "singleton_pattern",
                    "refs": singleton_refs,
                    "count": len(singleton_refs),
                    "evidences": [
                        ev
                        for ev in evidences
                        if ev.data.get("name", "") in singleton_refs
                    ],
                }
            )

        # Cluster 4: Service locator (anti-pattern)
        if locator_refs:
            clusters.append(
                {
                    "pattern_type": "service_locator",
                    "refs": locator_refs,
                    "count": len(locator_refs),
                    "evidences": [
                        ev
                        for ev in evidences
                        if ev.data.get("name", "") in locator_refs
                    ],
                }
            )

        return clusters

    def calculate_confidence(self, cluster: Dict) -> float:
        """Calculate confidence score (0-100) for a cluster."""
        ptype = cluster.get("pattern_type", "")

        if ptype == "constructor_injection":
            total = cluster.get("total_constructors", 0)
            with_inj = cluster.get("with_injection", 0)
            if total == 0:
                return 0.0
            ratio = with_inj / total
            return min(ratio * 130, 100.0)

        if ptype == "factory_pattern":
            count = cluster.get("count", 0)
            if count >= 5:
                return 90.0
            if count >= 2:
                return 75.0
            return 60.0

        if ptype == "singleton_pattern":
            count = cluster.get("count", 0)
            return min(65.0 + count * 5, 90.0)

        if ptype == "service_locator":
            count = cluster.get("count", 0)
            return min(70.0 + count * 5, 95.0)

        return 50.0

    def cluster_to_pattern(self, cluster: Dict) -> Pattern:
        """Convert a cluster into a Pattern object."""
        ptype = cluster.get("pattern_type", "unknown")
        evidences = cluster.get("evidences", [])
        confidence = self.calculate_confidence(cluster)

        if ptype == "constructor_injection":
            total = cluster.get("total_constructors", 0)
            with_inj = cluster.get("with_injection", 0)
            pct = (with_inj / total * 100) if total > 0 else 0
            return Pattern(
                name=f"constructor_injection_{pct:.0f}pct",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "total_constructors": total,
                    "with_injection": with_inj,
                    "pct": round(pct, 1),
                    "description": (
                        f"{pct:.0f}% of constructors use dependency injection"
                    ),
                },
                evidence=evidences,
            )

        if ptype == "factory_pattern":
            functions = cluster.get("functions", [])
            return Pattern(
                name=f"factory_pattern_{len(functions)}",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "count": len(functions),
                    "functions": functions,
                    "description": (f"{len(functions)} factory functions detected"),
                },
                evidence=evidences,
            )

        if ptype == "singleton_pattern":
            refs = cluster.get("refs", [])
            return Pattern(
                name=f"singleton_usage_{len(refs)}",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "count": len(refs),
                    "refs": refs,
                    "description": (f"{len(refs)} singleton references detected"),
                },
                evidence=evidences,
            )

        # service_locator
        refs = cluster.get("refs", [])
        return Pattern(
            name=f"service_locator_{len(refs)}",
            category=self.LEARNER_CATEGORY,
            confidence=confidence,
            metadata={
                "type": ptype,
                "count": len(refs),
                "refs": refs,
                "description": (
                    f"{len(refs)} service locator usages "
                    "(consider constructor injection instead)"
                ),
            },
            evidence=evidences,
        )
