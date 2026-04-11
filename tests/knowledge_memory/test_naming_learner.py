# HC-AI | ticket: MEM-M1-05
"""Tests for NamingLearner — detect naming conventions."""

from pathlib import Path
from typing import List

import pytest

from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.naming_learner import (
    NamingLearner,
    _classify_case,
    _extract_prefix,
)
from knowledge_memory.verticals.codebase.vault import CodebaseVault

# --- Unit tests for helper functions ---


class TestClassifyCase:
    """Tests for _classify_case helper."""

    def test_snake_case(self) -> None:
        assert _classify_case("get_customer") == "snake_case"
        assert _classify_case("create_order") == "snake_case"
        assert _classify_case("x") == "snake_case"

    def test_pascal_case(self) -> None:
        assert _classify_case("CustomerService") == "PascalCase"
        assert _classify_case("OrderManager") == "PascalCase"

    def test_camel_case(self) -> None:
        assert _classify_case("getCustomer") == "camelCase"
        assert _classify_case("processOrder") == "camelCase"

    def test_upper_snake(self) -> None:
        assert _classify_case("MAX_RETRIES") == "UPPER_SNAKE"
        assert _classify_case("API_KEY") == "UPPER_SNAKE"

    def test_mixed(self) -> None:
        assert _classify_case("get_Customer") == "mixed"
        assert _classify_case("My_func_Name") == "mixed"

    def test_leading_underscore(self) -> None:
        """Leading underscores are stripped before classification."""
        assert _classify_case("_private_method") == "snake_case"
        assert _classify_case("__dunder") == "snake_case"

    def test_empty(self) -> None:
        assert _classify_case("") == "mixed"
        assert _classify_case("_") == "mixed"


class TestExtractPrefix:
    """Tests for _extract_prefix helper."""

    def test_snake_prefix(self) -> None:
        assert _extract_prefix("get_customer") == "get_"
        assert _extract_prefix("create_order") == "create_"

    def test_no_underscore(self) -> None:
        assert _extract_prefix("process") == ""
        assert _extract_prefix("Customer") == ""

    def test_leading_underscore(self) -> None:
        # First underscore at index 0, so idx > 0 is False
        assert _extract_prefix("_private") == ""


# --- Fixtures ---


@pytest.fixture()
def learner() -> NamingLearner:
    return NamingLearner()


@pytest.fixture()
def snake_case_evidences() -> List[Evidence]:
    """Evidences with mostly snake_case function names."""
    return [
        Evidence(
            source="svc.py",
            data={"name": "get_customer", "type": "function", "layer": "service"},
            metadata={"layer": "service"},
        ),
        Evidence(
            source="svc.py",
            data={"name": "create_order", "type": "function", "layer": "service"},
            metadata={"layer": "service"},
        ),
        Evidence(
            source="svc.py",
            data={"name": "update_profile", "type": "method", "layer": "service"},
            metadata={"layer": "service"},
        ),
        Evidence(
            source="svc.py",
            data={"name": "delete_item", "type": "method", "layer": "service"},
            metadata={"layer": "service"},
        ),
        Evidence(
            source="svc.py",
            data={"name": "list_products", "type": "function", "layer": "service"},
            metadata={"layer": "service"},
        ),
        Evidence(
            source="svc.py",
            data={"name": "find_user", "type": "function", "layer": "service"},
            metadata={"layer": "service"},
        ),
        Evidence(
            source="util.py",
            data={"name": "format_name", "type": "function", "layer": "util"},
            metadata={"layer": "util"},
        ),
        Evidence(
            source="util.py",
            data={"name": "parse_date", "type": "function", "layer": "util"},
            metadata={"layer": "util"},
        ),
        # One camelCase violation
        Evidence(
            source="crm.py",
            data={"name": "getCustomer", "type": "function", "layer": "service"},
            metadata={"layer": "service"},
        ),
        # Classes
        Evidence(
            source="svc.py",
            data={"name": "CustomerService", "type": "class", "layer": "service"},
        ),
        Evidence(
            source="svc.py",
            data={"name": "OrderManager", "type": "class", "layer": "service"},
        ),
    ]


# --- Learner tests ---


class TestNamingLearnerBasic:
    """Basic learner metadata tests."""

    def test_learner_name(self, learner: NamingLearner) -> None:
        assert learner.LEARNER_NAME == "codebase.naming"

    def test_learner_category(self, learner: NamingLearner) -> None:
        assert learner.LEARNER_CATEGORY == "naming"

    def test_min_confidence(self, learner: NamingLearner) -> None:
        assert learner.MIN_CONFIDENCE == 60.0

    def test_describe(self, learner: NamingLearner) -> None:
        desc = learner.describe()
        assert desc["name"] == "codebase.naming"
        assert desc["category"] == "naming"


class TestNamingLearnerExtract:
    """Tests for evidence extraction."""

    def test_extract_filters_dunders(self, learner: NamingLearner) -> None:
        """Dunder methods are excluded."""
        vault = CodebaseVault()
        vault._vault_dir = Path("/fake")  # bypass init check
        evs = [
            Evidence(source="a.py", data={"name": "__init__", "type": "method"}),
            Evidence(source="a.py", data={"name": "get_data", "type": "function"}),
            Evidence(source="a.py", data={"name": "__str__", "type": "method"}),
        ]
        vault.load_evidences(evs)
        result = learner.extract_evidence(vault)
        assert len(result) == 1
        assert result[0].data["name"] == "get_data"

    def test_extract_keeps_classes(self, learner: NamingLearner) -> None:
        """Classes are included in extraction."""
        vault = CodebaseVault()
        vault._vault_dir = Path("/fake")
        evs = [
            Evidence(source="a.py", data={"name": "MyClass", "type": "class"}),
            Evidence(source="a.py", data={"name": "my_func", "type": "function"}),
        ]
        vault.load_evidences(evs)
        result = learner.extract_evidence(vault)
        assert len(result) == 2


class TestNamingLearnerCluster:
    """Tests for clustering logic."""

    def test_cluster_produces_case_convention(
        self, learner: NamingLearner, snake_case_evidences: List[Evidence]
    ) -> None:
        """Cluster produces case_convention clusters."""
        # Extract only funcs/methods/classes
        clusters = learner.cluster(snake_case_evidences)
        case_clusters = [c for c in clusters if c["pattern_type"] == "case_convention"]
        assert len(case_clusters) >= 1  # At least func/method convention

    def test_cluster_detects_snake_case_dominant(
        self, learner: NamingLearner, snake_case_evidences: List[Evidence]
    ) -> None:
        """Dominant case for functions/methods is snake_case."""
        clusters = learner.cluster(snake_case_evidences)
        func_cluster = [
            c
            for c in clusters
            if c.get("pattern_type") == "case_convention"
            and c.get("target") == "functions_methods"
        ]
        assert len(func_cluster) == 1
        assert func_cluster[0]["dominant_case"] == "snake_case"

    def test_cluster_detects_violations(
        self, learner: NamingLearner, snake_case_evidences: List[Evidence]
    ) -> None:
        """Violations (camelCase) are tracked."""
        clusters = learner.cluster(snake_case_evidences)
        func_cluster = [
            c
            for c in clusters
            if c.get("pattern_type") == "case_convention"
            and c.get("target") == "functions_methods"
        ]
        assert len(func_cluster[0]["violations"]) >= 1

    def test_cluster_class_pascal_case(
        self, learner: NamingLearner, snake_case_evidences: List[Evidence]
    ) -> None:
        """Class cluster detects PascalCase as dominant."""
        clusters = learner.cluster(snake_case_evidences)
        class_cluster = [
            c
            for c in clusters
            if c.get("pattern_type") == "case_convention"
            and c.get("target") == "classes"
        ]
        assert len(class_cluster) == 1
        assert class_cluster[0]["dominant_case"] == "PascalCase"

    def test_cluster_crud_prefix(
        self, learner: NamingLearner, snake_case_evidences: List[Evidence]
    ) -> None:
        """CRUD prefix patterns detected in service layer."""
        clusters = learner.cluster(snake_case_evidences)
        prefix_clusters = [c for c in clusters if c["pattern_type"] == "prefix_pattern"]
        assert len(prefix_clusters) == 1
        pc = prefix_clusters[0]["prefix_counts"]
        assert "get_" in pc
        assert "create_" in pc


class TestNamingLearnerConfidence:
    """Tests for confidence calculation."""

    def test_case_convention_high_compliance(self, learner: NamingLearner) -> None:
        """High compliance → high confidence."""
        cluster = {
            "pattern_type": "case_convention",
            "total": 100,
            "conforming": [None] * 95,  # 95% compliance
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 90.0

    def test_case_convention_low_compliance(self, learner: NamingLearner) -> None:
        """Low compliance → low confidence."""
        cluster = {
            "pattern_type": "case_convention",
            "total": 100,
            "conforming": [None] * 40,  # 40%
        }
        conf = learner.calculate_confidence(cluster)
        assert conf < 60.0

    def test_prefix_pattern_confidence(self, learner: NamingLearner) -> None:
        """CRUD prefix coverage drives confidence."""
        cluster = {
            "pattern_type": "prefix_pattern",
            "total_service_methods": 10,
            "crud_total": 8,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 80.0

    def test_zero_total_returns_zero(self, learner: NamingLearner) -> None:
        """Zero total → zero confidence."""
        cluster = {
            "pattern_type": "case_convention",
            "total": 0,
            "conforming": [],
        }
        assert learner.calculate_confidence(cluster) == 0.0


class TestNamingLearnerPattern:
    """Tests for pattern generation."""

    def test_case_convention_pattern(self, learner: NamingLearner) -> None:
        """case_convention cluster → Pattern with metadata."""
        cluster = {
            "pattern_type": "case_convention",
            "target": "functions_methods",
            "dominant_case": "snake_case",
            "total": 100,
            "conforming": [Evidence(source="a.py", data={"name": "x"})] * 5,
            "violations": [Evidence(source="b.py", data={"name": "getX"})],
            "case_counts": {"snake_case": 99, "camelCase": 1},
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "naming::functions_methods_snake_case"
        assert p.category == "naming"
        assert p.metadata["compliance_pct"] == 5.0  # 5/100
        assert p.metadata["violation_count"] == 1

    def test_crud_prefix_pattern(self, learner: NamingLearner) -> None:
        """prefix_pattern cluster → Pattern with CRUD distribution."""
        cluster = {
            "pattern_type": "prefix_pattern",
            "prefix_counts": {"get_": 10, "create_": 5},
            "total_service_methods": 20,
            "crud_total": 15,
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "naming::crud_prefix_pattern"
        assert p.metadata["crud_coverage_pct"] == 75.0


class TestNamingLearnerVaultQuery:
    """Tests for vault-stored node extraction path."""

    def test_extract_from_stored_nodes(self, tmp_path: Path) -> None:
        """NamingLearner reads from vault query_nodes when data is stored."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        # Store nodes into vault SQLite
        vault.store_nodes(
            [
                {
                    "name": "get_customer",
                    "file_path": "svc.py",
                    "node_type": "function",
                    "layer": "service",
                    "line_start": 10,
                    "line_end": 20,
                },
                {
                    "name": "Customer",
                    "file_path": "svc.py",
                    "node_type": "class",
                    "layer": "service",
                    "line_start": 1,
                    "line_end": 50,
                },
                {
                    "name": "__init__",
                    "file_path": "svc.py",
                    "node_type": "method",
                    "layer": "service",
                    "line_start": 5,
                    "line_end": 8,
                },
            ]
        )

        learner = NamingLearner()
        result = learner.extract_evidence(vault)

        # __init__ should be filtered out
        assert len(result) == 2
        names = {ev.data["name"] for ev in result}
        assert "get_customer" in names
        assert "Customer" in names
        assert "__init__" not in names

    def test_extract_stored_includes_layer_metadata(self, tmp_path: Path) -> None:
        """Stored node extraction preserves layer in metadata."""
        vault = CodebaseVault()
        vault.init(tmp_path)

        vault.store_nodes(
            [
                {
                    "name": "process_order",
                    "file_path": "order_svc.py",
                    "node_type": "function",
                    "layer": "service",
                    "line_start": 1,
                    "line_end": 10,
                },
            ]
        )

        learner = NamingLearner()
        result = learner.extract_evidence(vault)
        assert len(result) == 1
        assert result[0].data["layer"] == "service"
        assert result[0].metadata["layer"] == "service"


class TestNamingLearnerE2E:
    """End-to-end test with vault + runtime."""

    def test_e2e_via_runtime(
        self, snake_case_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """NamingLearner produces patterns through LearnerRuntime."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime

        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.load_evidences(snake_case_evidences)

        learner = NamingLearner()
        runtime = LearnerRuntime(vault=vault, learners=[learner])
        patterns = runtime.run()

        assert len(patterns) >= 2  # case conv + prefix pattern at minimum
        categories = {p.category for p in patterns}
        assert "naming" in categories

        # Verify patterns were committed to vault
        stored = vault.query_patterns(category="naming")
        assert len(stored) >= 2

    def test_e2e_confidence_above_threshold(
        self, snake_case_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """All emitted patterns have confidence ≥ 60%."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime

        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.load_evidences(snake_case_evidences)

        learner = NamingLearner()
        runtime = LearnerRuntime(vault=vault, learners=[learner])
        patterns = runtime.run()

        for p in patterns:
            assert (
                p.confidence >= 60.0
            ), f"Pattern {p.name} has confidence {p.confidence} < 60"
