# HC-AI | ticket: MEM-M3-06
"""TestPatternsLearner — detect testing patterns in codebase.

Analyzes: pytest fixtures, parametrize usage, test naming,
test-to-code ratio, coverage gaps by domain.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault

# HC-AI | ticket: MEM-M3-06
_TEST_FILE_RE = re.compile(r"(^test_|_test\.py$|tests/|/test/)")
_TEST_FUNC_RE = re.compile(r"^test_")
_FIXTURE_HINTS = ("fixture", "conftest", "setup", "teardown")
_PARAMETRIZE_HINTS = ("parametrize", "param", "mark.parametrize")


class TestPatternsLearner(BaseLearner[Evidence, Dict]):
    """Detect testing patterns across codebase evidence.

    Produces patterns for:
    - Test-to-code ratio (test files vs source files)
    - Test naming convention (test_ prefix compliance)
    - Fixture usage patterns
    - Coverage gaps (domains with no test files)
    """

    LEARNER_NAME = "codebase.test_patterns"
    LEARNER_CATEGORY = "test_patterns"

    def extract_evidence(self, vault: "BaseVault") -> List[Evidence]:
        """Extract testing evidence from vault nodes."""
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
                        "is_test_file": bool(_TEST_FILE_RE.search(fpath)),
                        "is_test_func": bool(_TEST_FUNC_RE.match(name)),
                    },
                )
            )

        return evidences

    def cluster(self, evidences: List[Evidence]) -> List[Dict]:
        """Group evidence into testing pattern clusters."""
        clusters: List[Dict] = []

        test_files: set[str] = set()
        source_files: set[str] = set()
        test_funcs: List[str] = []
        fixture_funcs: List[str] = []
        parametrize_funcs: List[str] = []
        domains_with_tests: set[str] = set()
        domains_without_tests: set[str] = set()
        all_domains: set[str] = set()

        for ev in evidences:
            data = ev.data
            fpath = data.get("file_path", "")
            name = data.get("name", "")
            is_test = data.get("is_test_file", False)

            # Track files
            if is_test:
                test_files.add(fpath)
            else:
                source_files.add(fpath)

            # Track test functions
            if data.get("is_test_func", False):
                test_funcs.append(name)

            # Fixture detection
            lower_name = name.lower()
            if any(h in lower_name for h in _FIXTURE_HINTS):
                fixture_funcs.append(name)

            # Parametrize detection
            if any(h in lower_name for h in _PARAMETRIZE_HINTS):
                parametrize_funcs.append(name)

            # Domain tracking
            domain = self._extract_domain(fpath)
            if domain:
                all_domains.add(domain)
                if is_test:
                    domains_with_tests.add(domain)

        domains_without_tests = all_domains - domains_with_tests

        # Cluster 1: Test-to-code ratio
        if source_files:
            clusters.append(
                {
                    "pattern_type": "test_code_ratio",
                    "test_files": len(test_files),
                    "source_files": len(source_files),
                    "test_funcs": len(test_funcs),
                    "ratio": (
                        len(test_files) / len(source_files) if source_files else 0
                    ),
                    "evidences": evidences[:20],
                }
            )

        # Cluster 2: Test naming
        if test_funcs:
            prefixed = sum(1 for t in test_funcs if t.startswith("test_"))
            clusters.append(
                {
                    "pattern_type": "test_naming",
                    "total_tests": len(test_funcs),
                    "with_prefix": prefixed,
                    "compliance": (
                        prefixed / len(test_funcs) * 100 if test_funcs else 0
                    ),
                    "evidences": [
                        ev for ev in evidences if ev.data.get("is_test_func")
                    ][:20],
                }
            )

        # Cluster 3: Fixtures
        if fixture_funcs:
            clusters.append(
                {
                    "pattern_type": "fixture_usage",
                    "fixtures": fixture_funcs,
                    "count": len(fixture_funcs),
                    "evidences": [
                        ev
                        for ev in evidences
                        if ev.data.get("name", "") in fixture_funcs
                    ],
                }
            )

        # Cluster 4: Coverage gaps
        if domains_without_tests:
            clusters.append(
                {
                    "pattern_type": "coverage_gaps",
                    "domains_without_tests": sorted(domains_without_tests),
                    "domains_with_tests": sorted(domains_with_tests),
                    "gap_count": len(domains_without_tests),
                    "evidences": evidences[:10],
                }
            )

        return clusters

    def calculate_confidence(self, cluster: Dict) -> float:
        """Calculate confidence score (0-100)."""
        ptype = cluster.get("pattern_type", "")

        if ptype == "test_code_ratio":
            ratio = cluster.get("ratio", 0)
            if ratio >= 0.8:
                return 95.0
            if ratio >= 0.5:
                return 80.0
            if ratio >= 0.2:
                return 65.0
            return 50.0

        if ptype == "test_naming":
            compliance = cluster.get("compliance", 0)
            return min(compliance, 100.0)

        if ptype == "fixture_usage":
            count = cluster.get("count", 0)
            if count >= 5:
                return 85.0
            return 65.0

        if ptype == "coverage_gaps":
            gaps = cluster.get("gap_count", 0)
            if gaps >= 3:
                return 90.0
            return 70.0

        return 50.0

    def cluster_to_pattern(self, cluster: Dict) -> Pattern:
        """Convert a cluster into a Pattern object."""
        ptype = cluster.get("pattern_type", "unknown")
        evidences = cluster.get("evidences", [])
        confidence = self.calculate_confidence(cluster)

        if ptype == "test_code_ratio":
            ratio = cluster.get("ratio", 0)
            test_f = cluster.get("test_files", 0)
            src_f = cluster.get("source_files", 0)
            return Pattern(
                name=f"test_ratio_{ratio:.0%}",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "test_files": test_f,
                    "source_files": src_f,
                    "ratio": round(ratio, 2),
                    "test_funcs": cluster.get("test_funcs", 0),
                    "description": (
                        f"Test-to-code ratio: {ratio:.0%} "
                        f"({test_f} test / {src_f} source files)"
                    ),
                },
                evidence=evidences,
            )

        if ptype == "test_naming":
            compliance = cluster.get("compliance", 0)
            return Pattern(
                name=f"test_naming_{compliance:.0f}pct",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "compliance": round(compliance, 1),
                    "total_tests": cluster.get("total_tests", 0),
                    "description": (f"test_ prefix compliance: {compliance:.0f}%"),
                },
                evidence=evidences,
            )

        if ptype == "fixture_usage":
            fixtures = cluster.get("fixtures", [])
            return Pattern(
                name=f"pytest_fixtures_{len(fixtures)}",
                category=self.LEARNER_CATEGORY,
                confidence=confidence,
                metadata={
                    "type": ptype,
                    "count": len(fixtures),
                    "fixtures": fixtures,
                    "description": (f"{len(fixtures)} pytest fixtures detected"),
                },
                evidence=evidences,
            )

        # coverage_gaps
        gaps = cluster.get("domains_without_tests", [])
        return Pattern(
            name=f"coverage_gaps_{len(gaps)}",
            category=self.LEARNER_CATEGORY,
            confidence=confidence,
            metadata={
                "type": ptype,
                "gap_count": len(gaps),
                "domains_without_tests": gaps,
                "domains_with_tests": cluster.get("domains_with_tests", []),
                "description": (
                    f"{len(gaps)} domains without test files: " f"{', '.join(gaps)}"
                ),
            },
            evidence=evidences,
        )

    @staticmethod
    def _extract_domain(file_path: str) -> str:
        """Extract domain from file path."""
        if not file_path or "/" not in file_path:
            return ""
        return file_path.split("/")[0]
