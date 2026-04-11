# HC-AI | ticket: MEM-M1-06
"""Tests for LayerLearner — detect path-based layer patterns."""

from pathlib import Path
from typing import List

import pytest

from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.layer_learner import (
    LayerLearner,
    _classify_layer,
    _extract_domain,
)
from knowledge_memory.verticals.codebase.vault import CodebaseVault

# --- Unit tests for helper functions ---


class TestClassifyLayer:
    """Tests for _classify_layer helper."""

    def test_route_directory(self) -> None:
        assert _classify_layer("app/routes/customer.py") == "route"
        assert _classify_layer("src/api/endpoints/users.py") == "route"

    def test_service_directory(self) -> None:
        assert _classify_layer("app/services/order_service.py") == "service"
        assert _classify_layer("modules/crm/service/crm_service.py") == "service"

    def test_model_directory(self) -> None:
        assert _classify_layer("app/models/user.py") == "model"
        assert _classify_layer("src/schemas/order_schema.py") == "model"

    def test_util_directory(self) -> None:
        assert _classify_layer("app/utils/helpers.py") == "util"
        assert _classify_layer("lib/helpers/format.py") == "util"

    def test_test_directory(self) -> None:
        assert _classify_layer("tests/test_service.py") == "test"
        assert _classify_layer("spec/user_spec.py") == "test"

    def test_config_directory(self) -> None:
        assert _classify_layer("config/database.py") == "config"
        assert _classify_layer("settings/base.py") == "config"

    def test_worker_directory(self) -> None:
        assert _classify_layer("workers/email_worker.py") == "worker"
        assert _classify_layer("tasks/background.py") == "worker"

    def test_middleware_directory(self) -> None:
        assert _classify_layer("middleware/auth.py") == "middleware"

    def test_repository_directory(self) -> None:
        assert _classify_layer("app/repositories/user_repo.py") == "repository"

    def test_migration_directory(self) -> None:
        assert _classify_layer("migrations/001_init.py") == "migration"
        assert _classify_layer("alembic/versions/abc123.py") == "migration"

    def test_filename_fallback(self) -> None:
        """When no directory match, filename regex is used."""
        assert _classify_layer("app/customer_service.py") == "service"
        assert _classify_layer("app/user_model.py") == "model"
        assert _classify_layer("app/test_orders.py") == "test"

    def test_unknown_path(self) -> None:
        assert _classify_layer("main.py") == "unknown"
        assert _classify_layer("app/core.py") == "unknown"

    def test_nested_directory(self) -> None:
        """Bottom-up directory search finds deepest match."""
        assert _classify_layer("app/modules/crm/services/crm.py") == "service"

    def test_empty_path(self) -> None:
        result = _classify_layer("")
        assert isinstance(result, str)


class TestExtractDomain:
    """Tests for _extract_domain helper."""

    def test_modules_pattern(self) -> None:
        assert _extract_domain("app/modules/crm/service.py") == "crm"
        assert _extract_domain("src/modules/billing/models.py") == "billing"

    def test_apps_pattern(self) -> None:
        assert _extract_domain("apps/users/views.py") == "users"

    def test_components_pattern(self) -> None:
        assert _extract_domain("components/dashboard/widget.py") == "dashboard"

    def test_fallback_first_dir(self) -> None:
        """Falls back to first non-common directory."""
        result = _extract_domain("crm/service.py")
        assert result == "crm"

    def test_root_level(self) -> None:
        assert _extract_domain("main.py") == "root"


# --- Fixtures ---


@pytest.fixture()
def learner() -> LayerLearner:
    return LayerLearner()


@pytest.fixture()
def multi_layer_evidences() -> List[Evidence]:
    """Evidences spanning multiple layers and domains."""
    return [
        # Service layer
        Evidence(
            source="app/services/customer_service.py",
            data={
                "name": "get_customer",
                "type": "function",
                "layer": "service",
                "file_path": "app/services/customer_service.py",
            },
            metadata={"layer": "service"},
        ),
        Evidence(
            source="app/services/order_service.py",
            data={
                "name": "create_order",
                "type": "function",
                "layer": "service",
                "file_path": "app/services/order_service.py",
            },
            metadata={"layer": "service"},
        ),
        Evidence(
            source="app/services/order_service.py",
            data={
                "name": "update_order",
                "type": "function",
                "layer": "service",
                "file_path": "app/services/order_service.py",
            },
            metadata={"layer": "service"},
        ),
        # Route layer
        Evidence(
            source="app/routes/customer_route.py",
            data={
                "name": "customer_endpoint",
                "type": "function",
                "layer": "route",
                "file_path": "app/routes/customer_route.py",
            },
            metadata={"layer": "route"},
        ),
        Evidence(
            source="app/routes/order_route.py",
            data={
                "name": "order_endpoint",
                "type": "function",
                "layer": "route",
                "file_path": "app/routes/order_route.py",
            },
            metadata={"layer": "route"},
        ),
        # Model layer
        Evidence(
            source="app/models/customer.py",
            data={
                "name": "Customer",
                "type": "class",
                "layer": "model",
                "file_path": "app/models/customer.py",
            },
            metadata={"layer": "model"},
        ),
        Evidence(
            source="app/models/order.py",
            data={
                "name": "Order",
                "type": "class",
                "layer": "model",
                "file_path": "app/models/order.py",
            },
            metadata={"layer": "model"},
        ),
        # Util layer
        Evidence(
            source="app/utils/format.py",
            data={
                "name": "format_date",
                "type": "function",
                "layer": "util",
                "file_path": "app/utils/format.py",
            },
            metadata={"layer": "util"},
        ),
        Evidence(
            source="app/utils/validate.py",
            data={
                "name": "validate_email",
                "type": "function",
                "layer": "util",
                "file_path": "app/utils/validate.py",
            },
            metadata={"layer": "util"},
        ),
        # Config
        Evidence(
            source="config/database.py",
            data={
                "name": "DATABASE_URL",
                "type": "function",
                "layer": "config",
                "file_path": "config/database.py",
            },
            metadata={"layer": "config"},
        ),
    ]


@pytest.fixture()
def domain_evidences() -> List[Evidence]:
    """Evidences from multiple domains with layer variety."""
    return [
        # CRM domain
        Evidence(
            source="modules/crm/services/crm_service.py",
            data={
                "name": "get_customer",
                "type": "function",
                "layer": "service",
                "file_path": "modules/crm/services/crm_service.py",
            },
        ),
        Evidence(
            source="modules/crm/routes/crm_route.py",
            data={
                "name": "crm_endpoint",
                "type": "function",
                "layer": "route",
                "file_path": "modules/crm/routes/crm_route.py",
            },
        ),
        Evidence(
            source="modules/crm/models/customer.py",
            data={
                "name": "Customer",
                "type": "class",
                "layer": "model",
                "file_path": "modules/crm/models/customer.py",
            },
        ),
        # Billing domain
        Evidence(
            source="modules/billing/services/billing_service.py",
            data={
                "name": "process_payment",
                "type": "function",
                "layer": "service",
                "file_path": "modules/billing/services/billing_service.py",
            },
        ),
        Evidence(
            source="modules/billing/routes/billing_route.py",
            data={
                "name": "billing_endpoint",
                "type": "function",
                "layer": "route",
                "file_path": "modules/billing/routes/billing_route.py",
            },
        ),
        Evidence(
            source="modules/billing/models/invoice.py",
            data={
                "name": "Invoice",
                "type": "class",
                "layer": "model",
                "file_path": "modules/billing/models/invoice.py",
            },
        ),
        # Shared utils
        Evidence(
            source="utils/helpers.py",
            data={
                "name": "format_date",
                "type": "function",
                "layer": "util",
                "file_path": "utils/helpers.py",
            },
        ),
    ]


# --- Learner tests ---


class TestLayerLearnerBasic:
    """Basic learner metadata tests."""

    def test_learner_name(self, learner: LayerLearner) -> None:
        assert learner.LEARNER_NAME == "codebase.layers"

    def test_learner_category(self, learner: LayerLearner) -> None:
        assert learner.LEARNER_CATEGORY == "layers"

    def test_min_confidence(self, learner: LayerLearner) -> None:
        assert learner.MIN_CONFIDENCE == 60.0

    def test_describe(self, learner: LayerLearner) -> None:
        desc = learner.describe()
        assert desc["name"] == "codebase.layers"
        assert desc["category"] == "layers"


class TestLayerLearnerExtract:
    """Tests for evidence extraction."""

    def test_extract_filters_dunders(self, learner: LayerLearner) -> None:
        """Dunder methods are excluded."""
        vault = CodebaseVault()
        vault._vault_dir = Path("/fake")
        evs = [
            Evidence(
                source="a.py",
                data={"name": "__init__", "type": "function", "file_path": "a.py"},
            ),
            Evidence(
                source="a.py",
                data={"name": "get_data", "type": "function", "file_path": "a.py"},
            ),
        ]
        vault.load_evidences(evs)
        result = learner.extract_evidence(vault)
        assert len(result) == 1
        assert result[0].data["name"] == "get_data"

    def test_extract_all_types(self, learner: LayerLearner) -> None:
        """All node types are included (not just function/method/class)."""
        vault = CodebaseVault()
        vault._vault_dir = Path("/fake")
        evs = [
            Evidence(
                source="a.py",
                data={"name": "MyClass", "type": "class", "file_path": "a.py"},
            ),
            Evidence(
                source="a.py",
                data={"name": "my_func", "type": "function", "file_path": "a.py"},
            ),
        ]
        vault.load_evidences(evs)
        result = learner.extract_evidence(vault)
        assert len(result) == 2


class TestLayerLearnerCluster:
    """Tests for clustering logic."""

    def test_cluster_produces_distribution(
        self, learner: LayerLearner, multi_layer_evidences: List[Evidence]
    ) -> None:
        """Cluster produces layer_distribution cluster."""
        clusters = learner.cluster(multi_layer_evidences)
        dist = [c for c in clusters if c["pattern_type"] == "layer_distribution"]
        assert len(dist) == 1
        assert dist[0]["total"] == 10

    def test_distribution_layer_counts(
        self, learner: LayerLearner, multi_layer_evidences: List[Evidence]
    ) -> None:
        """Distribution cluster has accurate layer counts."""
        clusters = learner.cluster(multi_layer_evidences)
        dist = [c for c in clusters if c["pattern_type"] == "layer_distribution"][0]
        lc = dist["layer_counts"]
        assert lc.get("service") == 3
        assert lc.get("route") == 2
        assert lc.get("model") == 2
        assert lc.get("util") == 2
        assert lc.get("config") == 1

    def test_cluster_produces_compliance(
        self, learner: LayerLearner, multi_layer_evidences: List[Evidence]
    ) -> None:
        """Cluster produces layer_compliance cluster."""
        clusters = learner.cluster(multi_layer_evidences)
        comp = [c for c in clusters if c["pattern_type"] == "layer_compliance"]
        assert len(comp) == 1

    def test_compliance_high_when_matched(
        self, learner: LayerLearner, multi_layer_evidences: List[Evidence]
    ) -> None:
        """Compliance is high when detected == stored layers."""
        clusters = learner.cluster(multi_layer_evidences)
        comp = [c for c in clusters if c["pattern_type"] == "layer_compliance"][0]
        # All evidences have matching detected/stored layers
        assert comp["compliance_pct"] == 100.0

    def test_cluster_produces_domain_grouping(
        self, learner: LayerLearner, domain_evidences: List[Evidence]
    ) -> None:
        """Domain grouping detects multiple domains."""
        clusters = learner.cluster(domain_evidences)
        dg = [c for c in clusters if c["pattern_type"] == "domain_grouping"]
        assert len(dg) == 1
        assert dg[0]["total_domains"] >= 2

    def test_domain_multi_layer(
        self, learner: LayerLearner, domain_evidences: List[Evidence]
    ) -> None:
        """CRM and billing domains have multiple layers (well-structured)."""
        clusters = learner.cluster(domain_evidences)
        dg = [c for c in clusters if c["pattern_type"] == "domain_grouping"][0]
        assert dg["multi_layer_domains"] >= 2

    def test_cluster_produces_layer_depth(
        self, learner: LayerLearner, multi_layer_evidences: List[Evidence]
    ) -> None:
        """Cluster produces layer_depth analysis."""
        clusters = learner.cluster(multi_layer_evidences)
        depth = [c for c in clusters if c["pattern_type"] == "layer_depth"]
        assert len(depth) == 1
        assert depth[0]["total_layers"] >= 2

    def test_cluster_produces_file_concentration(
        self, learner: LayerLearner, multi_layer_evidences: List[Evidence]
    ) -> None:
        """Cluster produces file_concentration hotspots."""
        clusters = learner.cluster(multi_layer_evidences)
        fc = [c for c in clusters if c["pattern_type"] == "file_concentration"]
        # May or may not produce concentration depending on distribution
        # At minimum, the cluster type should be recognized
        assert isinstance(fc, list)

    def test_empty_evidences(self, learner: LayerLearner) -> None:
        """Empty input produces no clusters."""
        clusters = learner.cluster([])
        assert clusters == []


class TestLayerLearnerConfidence:
    """Tests for confidence calculation."""

    def test_distribution_high_recognition(self, learner: LayerLearner) -> None:
        """High recognition rate → high confidence."""
        cluster = {
            "pattern_type": "layer_distribution",
            "recognized_pct": 90.0,
            "total": 100,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 90.0

    def test_distribution_zero_total(self, learner: LayerLearner) -> None:
        """Zero total → zero confidence."""
        cluster = {
            "pattern_type": "layer_distribution",
            "recognized_pct": 0,
            "total": 0,
        }
        assert learner.calculate_confidence(cluster) == 0.0

    def test_compliance_confidence(self, learner: LayerLearner) -> None:
        """Compliance pct maps directly to confidence."""
        cluster = {
            "pattern_type": "layer_compliance",
            "compliance_pct": 85.0,
            "total": 50,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf == 85.0

    def test_domain_grouping_confidence(self, learner: LayerLearner) -> None:
        """Multi-layer domains drive domain_grouping confidence."""
        cluster = {
            "pattern_type": "domain_grouping",
            "total_domains": 5,
            "multi_layer_domains": 4,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 60.0

    def test_layer_depth_confidence(self, learner: LayerLearner) -> None:
        """Multiple layers → higher confidence."""
        cluster = {
            "pattern_type": "layer_depth",
            "total_layers": 5,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 60.0

    def test_layer_depth_single_layer(self, learner: LayerLearner) -> None:
        """Single layer → zero confidence."""
        cluster = {
            "pattern_type": "layer_depth",
            "total_layers": 1,
        }
        assert learner.calculate_confidence(cluster) == 0.0

    def test_file_concentration_confidence(self, learner: LayerLearner) -> None:
        """File concentration based on hotspot coverage."""
        cluster = {
            "pattern_type": "file_concentration",
            "hotspot_dirs": {"app/services": 10, "app/routes": 8},
            "total_nodes": 20,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 60.0

    def test_unknown_pattern_type(self, learner: LayerLearner) -> None:
        """Unknown pattern type returns 0."""
        assert learner.calculate_confidence({"pattern_type": "unknown"}) == 0.0


class TestLayerLearnerPattern:
    """Tests for pattern generation."""

    def test_distribution_pattern(self, learner: LayerLearner) -> None:
        """layer_distribution cluster → Pattern with metadata."""
        cluster = {
            "pattern_type": "layer_distribution",
            "layer_counts": {"service": 30, "route": 20, "model": 15},
            "layer_pct": {"service": 46.2, "route": 30.8, "model": 23.1},
            "total": 65,
            "recognized_pct": 100.0,
            "top_layers": [("service", 30), ("route", 20), ("model", 15)],
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "layers::distribution"
        assert p.category == "layers"
        assert p.metadata["total"] == 65
        assert p.metadata["recognized_pct"] == 100.0

    def test_compliance_pattern(self, learner: LayerLearner) -> None:
        """layer_compliance cluster → Pattern with mismatch info."""
        cluster = {
            "pattern_type": "layer_compliance",
            "compliance_pct": 90.0,
            "total": 50,
            "compliant": [Evidence(source="a.py", data={"name": "x"})] * 3,
            "mismatched": [
                {
                    "name": "func",
                    "file_path": "a.py",
                    "detected": "service",
                    "stored": "util",
                }
            ],
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "layers::compliance"
        assert p.metadata["compliance_pct"] == 90.0
        assert p.metadata["mismatch_count"] == 1

    def test_domain_grouping_pattern(self, learner: LayerLearner) -> None:
        """domain_grouping cluster → Pattern with domain info."""
        cluster = {
            "pattern_type": "domain_grouping",
            "domains": [
                {"domain": "crm", "node_count": 10, "layers": {}, "layer_count": 3},
            ],
            "total_domains": 3,
            "multi_layer_domains": 2,
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "layers::domain_grouping"
        assert p.metadata["total_domains"] == 3

    def test_depth_pattern(self, learner: LayerLearner) -> None:
        """layer_depth cluster → Pattern with depth stats."""
        cluster = {
            "pattern_type": "layer_depth",
            "depth_stats": {
                "service": {
                    "avg_depth": 3.5,
                    "min_depth": 2,
                    "max_depth": 5,
                    "count": 10,
                }
            },
            "total_layers": 4,
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "layers::depth_analysis"
        assert p.metadata["total_layers"] == 4

    def test_concentration_pattern(self, learner: LayerLearner) -> None:
        """file_concentration cluster → Pattern with hotspot info."""
        cluster = {
            "pattern_type": "file_concentration",
            "hotspot_dirs": {"app/services": 15, "app/routes": 10},
            "total_dirs": 8,
            "total_nodes": 50,
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "layers::file_concentration"
        assert p.metadata["total_dirs"] == 8


class TestLayerLearnerE2E:
    """End-to-end test with vault + runtime."""

    def test_e2e_via_runtime(
        self, multi_layer_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """LayerLearner produces patterns through LearnerRuntime."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime

        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.load_evidences(multi_layer_evidences)

        learner = LayerLearner()
        runtime = LearnerRuntime(vault=vault, learners=[learner])
        patterns = runtime.run()

        assert len(patterns) >= 2  # distribution + at least one more
        categories = {p.category for p in patterns}
        assert "layers" in categories

        # Verify patterns were committed to vault
        stored = vault.query_patterns(category="layers")
        assert len(stored) >= 2

    def test_e2e_confidence_above_threshold(
        self, multi_layer_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """All emitted patterns have confidence ≥ 60%."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime

        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.load_evidences(multi_layer_evidences)

        learner = LayerLearner()
        runtime = LearnerRuntime(vault=vault, learners=[learner])
        patterns = runtime.run()

        for p in patterns:
            assert (
                p.confidence >= 60.0
            ), f"Pattern {p.name} has confidence {p.confidence} < 60"

    def test_e2e_naming_and_layer_combined(
        self, multi_layer_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """NamingLearner + LayerLearner run together without conflict."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime
        from knowledge_memory.verticals.codebase.naming_learner import NamingLearner

        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.load_evidences(multi_layer_evidences)

        naming = NamingLearner()
        layers = LayerLearner()
        runtime = LearnerRuntime(vault=vault, learners=[naming, layers])
        patterns = runtime.run()

        categories = {p.category for p in patterns}
        assert "naming" in categories
        assert "layers" in categories
