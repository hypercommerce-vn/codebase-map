# HC-AI | ticket: MEM-M1-05
"""NamingLearner — detect naming conventions from codebase evidence."""

import re
from collections import Counter
from typing import TYPE_CHECKING, Dict, List, Tuple

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault

# HC-AI | ticket: MEM-M1-05
_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
_CAMEL_CASE_RE = re.compile(r"^[a-z][a-zA-Z0-9]*$")
_PASCAL_CASE_RE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
_UPPER_SNAKE_RE = re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$")

# Common CRUD prefixes for service methods
_CRUD_PREFIXES = ("get_", "create_", "update_", "delete_", "list_", "find_")
# Common dunder/private patterns to skip
_SKIP_PREFIXES = ("__", "_pytest")


def _classify_case(name: str) -> str:
    """Classify a name into a case style.

    Returns one of: snake_case, camelCase, PascalCase, UPPER_SNAKE, mixed.
    """
    # Strip leading underscores for classification
    stripped = name.lstrip("_")
    if not stripped:
        return "mixed"

    if _SNAKE_CASE_RE.match(stripped):
        return "snake_case"
    if _PASCAL_CASE_RE.match(stripped):
        return "PascalCase"
    if _CAMEL_CASE_RE.match(stripped):
        return "camelCase"
    if _UPPER_SNAKE_RE.match(stripped):
        return "UPPER_SNAKE"
    return "mixed"


def _extract_prefix(name: str) -> str:
    """Extract the first word/prefix from a snake_case name.

    Returns prefix with trailing underscore (e.g. ``"get_"``),
    or empty string if no underscore found.
    """
    idx = name.find("_")
    if idx > 0:
        return name[: idx + 1]
    return ""


# HC-AI | ticket: MEM-M1-05
# Cluster types for NamingLearner
# Each cluster is a dict with: pattern_type, data, evidences
# pattern_type: "case_convention" | "prefix_pattern" | "violation"


class NamingLearner(BaseLearner[Evidence, Dict]):
    """Detect naming conventions across codebase evidence.

    Produces patterns for:
    - Case convention compliance (snake_case %, PascalCase for classes)
    - CRUD prefix patterns in service methods
    - Naming violations (non-conforming names)
    - Prefix frequency distribution

    Design ref: kmp-M1-design.html Screen C item 6-7, Screen D NamingLearner.
    """

    LEARNER_NAME = "codebase.naming"
    LEARNER_CATEGORY = "naming"
    MIN_EVIDENCE_COUNT = 5
    MIN_CONFIDENCE = 60.0

    def extract_evidence(self, vault: "BaseVault") -> List[Evidence]:
        """Pull function/method/class evidence from vault corpus."""
        results: List[Evidence] = []
        for ev in vault.get_corpus_iterator():
            name = ev.data.get("name", "")
            node_type = ev.data.get("type", "")
            # Skip empty names and dunders
            if not name or name.startswith("__"):
                continue
            if node_type in ("function", "method", "class"):
                results.append(ev)
        return results

    def cluster(self, evidences: List[Evidence]) -> List[Dict]:
        """Group evidence into naming pattern clusters.

        Produces clusters for:
        1. Case convention analysis (snake_case compliance for funcs/methods)
        2. CRUD prefix patterns (for service-layer methods)
        3. Naming violations (non-snake_case functions/methods)
        """
        clusters: List[Dict] = []

        # Separate by type
        funcs_methods: List[Evidence] = []
        classes: List[Evidence] = []
        for ev in evidences:
            if ev.data.get("type") in ("function", "method"):
                funcs_methods.append(ev)
            elif ev.data.get("type") == "class":
                classes.append(ev)

        # --- Cluster 1: Function/method case convention ---
        if funcs_methods:
            case_counts: Counter = Counter()
            violations: List[Evidence] = []
            conforming: List[Evidence] = []

            for ev in funcs_methods:
                # For methods like "Class.method", check the method part
                raw_name = ev.data.get("name", "")
                name = raw_name.split(".")[-1] if "." in raw_name else raw_name
                case = _classify_case(name)
                case_counts[case] += 1
                if case == "snake_case":
                    conforming.append(ev)
                else:
                    violations.append(ev)

            total = sum(case_counts.values())
            clusters.append(
                {
                    "pattern_type": "case_convention",
                    "target": "functions_methods",
                    "case_counts": dict(case_counts),
                    "total": total,
                    "conforming": conforming,
                    "violations": violations,
                    "dominant_case": (
                        case_counts.most_common(1)[0][0] if case_counts else "unknown"
                    ),
                }
            )

        # --- Cluster 2: Class naming convention (PascalCase) ---
        if classes:
            class_case_counts: Counter = Counter()
            class_violations: List[Evidence] = []
            class_conforming: List[Evidence] = []

            for ev in classes:
                name = ev.data.get("name", "")
                case = _classify_case(name)
                class_case_counts[case] += 1
                if case == "PascalCase":
                    class_conforming.append(ev)
                else:
                    class_violations.append(ev)

            total_cls = sum(class_case_counts.values())
            clusters.append(
                {
                    "pattern_type": "case_convention",
                    "target": "classes",
                    "case_counts": dict(class_case_counts),
                    "total": total_cls,
                    "conforming": class_conforming,
                    "violations": class_violations,
                    "dominant_case": (
                        class_case_counts.most_common(1)[0][0]
                        if class_case_counts
                        else "unknown"
                    ),
                }
            )

        # --- Cluster 3: CRUD prefix patterns (service layer) ---
        service_methods: List[Evidence] = [
            ev
            for ev in funcs_methods
            if ev.data.get("layer") == "service"
            or ev.metadata.get("layer") == "service"
        ]
        if service_methods:
            prefix_counts: Counter = Counter()
            prefix_evidences: Dict[str, List[Evidence]] = {}

            for ev in service_methods:
                raw_name = ev.data.get("name", "")
                name = raw_name.split(".")[-1] if "." in raw_name else raw_name
                prefix = _extract_prefix(name)
                if prefix in _CRUD_PREFIXES:
                    prefix_counts[prefix] += 1
                    prefix_evidences.setdefault(prefix, []).append(ev)

            if prefix_counts:
                crud_total = sum(prefix_counts.values())
                clusters.append(
                    {
                        "pattern_type": "prefix_pattern",
                        "prefix_counts": dict(prefix_counts),
                        "prefix_evidences": prefix_evidences,
                        "total_service_methods": len(service_methods),
                        "crud_total": crud_total,
                        "evidences": service_methods,
                    }
                )

        # --- Cluster 4: General prefix frequency ---
        if funcs_methods:
            all_prefix_counts: Counter = Counter()
            for ev in funcs_methods:
                raw_name = ev.data.get("name", "")
                name = raw_name.split(".")[-1] if "." in raw_name else raw_name
                prefix = _extract_prefix(name)
                if prefix and not name.startswith("_"):
                    all_prefix_counts[prefix] += 1

            # Only emit top prefixes with ≥3 occurrences
            top_prefixes = {
                p: c for p, c in all_prefix_counts.most_common(10) if c >= 3
            }
            if top_prefixes:
                clusters.append(
                    {
                        "pattern_type": "prefix_frequency",
                        "prefix_counts": top_prefixes,
                        "total_functions": len(funcs_methods),
                        "evidences": funcs_methods,
                    }
                )

        return clusters

    def calculate_confidence(self, cluster: Dict) -> float:
        """Calculate confidence based on cluster type and data.

        - case_convention: based on % compliance (high compliance = high conf)
        - prefix_pattern: based on coverage of service methods
        - prefix_frequency: based on consistency of prefix usage
        """
        pattern_type = cluster.get("pattern_type", "")

        if pattern_type == "case_convention":
            total = cluster.get("total", 0)
            if total == 0:
                return 0.0
            conforming_count = len(cluster.get("conforming", []))
            pct = (conforming_count / total) * 100
            # Scale: 90%+ compliance → 90+ confidence
            return min(100.0, pct)

        if pattern_type == "prefix_pattern":
            total_svc = cluster.get("total_service_methods", 0)
            crud_total = cluster.get("crud_total", 0)
            if total_svc == 0:
                return 0.0
            coverage = (crud_total / total_svc) * 100
            # 80%+ CRUD coverage → high confidence
            return min(100.0, coverage * 1.1)

        if pattern_type == "prefix_frequency":
            prefix_counts = cluster.get("prefix_counts", {})
            total = cluster.get("total_functions", 0)
            if not prefix_counts or total == 0:
                return 0.0
            # Sum of top prefixes as % of total
            top_sum = sum(prefix_counts.values())
            coverage = (top_sum / total) * 100
            return min(100.0, max(60.0, coverage))

        return 0.0

    def cluster_to_pattern(self, cluster: Dict) -> Pattern:
        """Convert a naming cluster into a Pattern."""
        pattern_type = cluster.get("pattern_type", "")

        if pattern_type == "case_convention":
            target = cluster.get("target", "unknown")
            dominant = cluster.get("dominant_case", "unknown")
            total = cluster.get("total", 0)
            conforming_count = len(cluster.get("conforming", []))
            violations = cluster.get("violations", [])
            pct = round((conforming_count / total) * 100, 1) if total else 0

            # Collect violation names (max 10 for metadata)
            violation_names = [ev.data.get("name", "") for ev in violations[:10]]

            return Pattern(
                name=f"naming::{target}_{dominant}",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("conforming", [])[:20],
                metadata={
                    "target": target,
                    "dominant_case": dominant,
                    "compliance_pct": pct,
                    "total": total,
                    "violation_count": len(violations),
                    "violations": violation_names,
                    "case_distribution": cluster.get("case_counts", {}),
                },
            )

        if pattern_type == "prefix_pattern":
            prefix_counts = cluster.get("prefix_counts", {})
            total_svc = cluster.get("total_service_methods", 0)
            crud_total = cluster.get("crud_total", 0)

            # Build distribution string
            distribution: List[Tuple[str, int]] = sorted(
                prefix_counts.items(), key=lambda x: x[1], reverse=True
            )

            return Pattern(
                name="naming::crud_prefix_pattern",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "prefix_distribution": dict(distribution),
                    "total_service_methods": total_svc,
                    "crud_coverage_pct": (
                        round((crud_total / total_svc) * 100, 1) if total_svc else 0
                    ),
                },
            )

        if pattern_type == "prefix_frequency":
            prefix_counts = cluster.get("prefix_counts", {})
            return Pattern(
                name="naming::prefix_frequency",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "top_prefixes": cluster.get("prefix_counts", {}),
                    "total_functions": cluster.get("total_functions", 0),
                },
            )

        # Fallback
        return Pattern(
            name=f"naming::{pattern_type}",
            category=self.LEARNER_CATEGORY,
        )
