# HC-AI | ticket: MEM-M1-07
"""Tests for GitOwnershipLearner — detect author attribution and bus factor."""

from pathlib import Path
from typing import List

import pytest

from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.git_ownership_learner import (
    GitOwnershipLearner,
    _extract_domain_from_path,
)
from knowledge_memory.verticals.codebase.vault import CodebaseVault

# --- Unit tests for helper functions ---


class TestExtractDomainFromPath:
    """Tests for _extract_domain_from_path helper."""

    def test_modules_pattern(self) -> None:
        assert _extract_domain_from_path("app/modules/crm/service.py") == "crm"
        assert _extract_domain_from_path("modules/billing/models.py") == "billing"

    def test_apps_pattern(self) -> None:
        assert _extract_domain_from_path("apps/users/views.py") == "users"

    def test_components_pattern(self) -> None:
        assert (
            _extract_domain_from_path("components/dashboard/widget.py") == "dashboard"
        )

    def test_fallback_first_dir(self) -> None:
        result = _extract_domain_from_path("pipeline/process.py")
        assert result == "pipeline"

    def test_root_level(self) -> None:
        assert _extract_domain_from_path("main.py") == "root"

    def test_skip_common_roots(self) -> None:
        result = _extract_domain_from_path("src/crm/handler.py")
        assert result == "crm"


# --- Fixtures ---


@pytest.fixture()
def learner() -> GitOwnershipLearner:
    return GitOwnershipLearner()


@pytest.fixture()
def single_owner_evidences() -> List[Evidence]:
    """Evidences showing single-owner dominance on several files."""
    return [
        # File 1: single owner (100%)
        Evidence(
            source="modules/pipeline/processor.py",
            data={
                "file_path": "modules/pipeline/processor.py",
                "author": "alice",
                "commits": 47,
                "pct": 94.0,
            },
        ),
        Evidence(
            source="modules/pipeline/processor.py",
            data={
                "file_path": "modules/pipeline/processor.py",
                "author": "bob",
                "commits": 3,
                "pct": 6.0,
            },
        ),
        # File 2: single owner (90%)
        Evidence(
            source="modules/pipeline/transformer.py",
            data={
                "file_path": "modules/pipeline/transformer.py",
                "author": "alice",
                "commits": 36,
                "pct": 90.0,
            },
        ),
        Evidence(
            source="modules/pipeline/transformer.py",
            data={
                "file_path": "modules/pipeline/transformer.py",
                "author": "charlie",
                "commits": 4,
                "pct": 10.0,
            },
        ),
        # File 3: multi-owner (healthy)
        Evidence(
            source="modules/crm/service.py",
            data={
                "file_path": "modules/crm/service.py",
                "author": "bob",
                "commits": 15,
                "pct": 50.0,
            },
        ),
        Evidence(
            source="modules/crm/service.py",
            data={
                "file_path": "modules/crm/service.py",
                "author": "charlie",
                "commits": 10,
                "pct": 33.3,
            },
        ),
        Evidence(
            source="modules/crm/service.py",
            data={
                "file_path": "modules/crm/service.py",
                "author": "alice",
                "commits": 5,
                "pct": 16.7,
            },
        ),
        # File 4: single owner on CRM route
        Evidence(
            source="modules/crm/route.py",
            data={
                "file_path": "modules/crm/route.py",
                "author": "bob",
                "commits": 25,
                "pct": 83.3,
            },
        ),
        Evidence(
            source="modules/crm/route.py",
            data={
                "file_path": "modules/crm/route.py",
                "author": "alice",
                "commits": 5,
                "pct": 16.7,
            },
        ),
        # File 5: multi-owner billing
        Evidence(
            source="modules/billing/invoice.py",
            data={
                "file_path": "modules/billing/invoice.py",
                "author": "charlie",
                "commits": 12,
                "pct": 48.0,
            },
        ),
        Evidence(
            source="modules/billing/invoice.py",
            data={
                "file_path": "modules/billing/invoice.py",
                "author": "bob",
                "commits": 8,
                "pct": 32.0,
            },
        ),
        Evidence(
            source="modules/billing/invoice.py",
            data={
                "file_path": "modules/billing/invoice.py",
                "author": "alice",
                "commits": 5,
                "pct": 20.0,
            },
        ),
    ]


# --- Learner tests ---


class TestGitOwnershipBasic:
    """Basic learner metadata tests."""

    def test_learner_name(self, learner: GitOwnershipLearner) -> None:
        assert learner.LEARNER_NAME == "codebase.git_ownership"

    def test_learner_category(self, learner: GitOwnershipLearner) -> None:
        assert learner.LEARNER_CATEGORY == "ownership"

    def test_min_confidence(self, learner: GitOwnershipLearner) -> None:
        assert learner.MIN_CONFIDENCE == 60.0

    def test_describe(self, learner: GitOwnershipLearner) -> None:
        desc = learner.describe()
        assert desc["name"] == "codebase.git_ownership"
        assert desc["category"] == "ownership"

    def test_configurable_thresholds(self) -> None:
        learner = GitOwnershipLearner()
        assert learner.SINGLE_OWNER_PCT == 80.0
        assert learner.BUS_FACTOR_THRESHOLD == 1


class TestGitOwnershipExtract:
    """Tests for evidence extraction."""

    def test_extract_from_vault_ownership(self, tmp_path: Path) -> None:
        """Extract uses vault query_ownership when data is stored."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.store_ownership(
            [
                {
                    "file_path": "svc.py",
                    "author": "alice",
                    "commits": 10,
                    "pct": 100.0,
                },
            ]
        )

        learner = GitOwnershipLearner()
        result = learner.extract_evidence(vault)
        assert len(result) == 1
        assert result[0].data["author"] == "alice"
        assert result[0].data["commits"] == 10

    def test_extract_from_corpus_fallback(self) -> None:
        """Falls back to corpus iterator when no stored data."""
        vault = CodebaseVault()
        vault._vault_dir = Path("/fake")
        evs = [
            Evidence(
                source="a.py",
                data={"author": "alice", "file_path": "a.py", "commits": 5},
            ),
        ]
        vault.load_evidences(evs)

        learner = GitOwnershipLearner()
        result = learner.extract_evidence(vault)
        assert len(result) == 1

    def test_extract_skips_no_author(self) -> None:
        """Corpus items without author are skipped."""
        vault = CodebaseVault()
        vault._vault_dir = Path("/fake")
        evs = [
            Evidence(source="a.py", data={"name": "func", "type": "function"}),
        ]
        vault.load_evidences(evs)

        learner = GitOwnershipLearner()
        result = learner.extract_evidence(vault)
        assert len(result) == 0


class TestGitOwnershipCluster:
    """Tests for clustering logic."""

    def test_cluster_produces_single_owner_files(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """Cluster produces single_owner_files cluster."""
        clusters = learner.cluster(single_owner_evidences)
        sof = [c for c in clusters if c["pattern_type"] == "single_owner_files"]
        assert len(sof) == 1

    def test_single_owner_count(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """Correctly counts single-owner files."""
        clusters = learner.cluster(single_owner_evidences)
        sof = [c for c in clusters if c["pattern_type"] == "single_owner_files"][0]
        # pipeline/processor (94%), pipeline/transformer (90%), crm/route (83.3%)
        assert sof["single_owner_count"] == 3
        assert sof["total_files"] == 5

    def test_cluster_produces_author_distribution(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """Cluster produces author_distribution cluster."""
        clusters = learner.cluster(single_owner_evidences)
        ad = [c for c in clusters if c["pattern_type"] == "author_distribution"]
        assert len(ad) == 1
        assert ad[0]["total_authors"] == 3  # alice, bob, charlie

    def test_author_distribution_top_authors(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """Top authors sorted by commit count."""
        clusters = learner.cluster(single_owner_evidences)
        ad = [c for c in clusters if c["pattern_type"] == "author_distribution"][0]
        # alice: 47+36+5+5 = 93, bob: 3+15+25+8 = 51, charlie: 4+10+12 = 26
        top = ad["top_authors"]
        assert top[0]["author"] == "alice"
        assert top[1]["author"] == "bob"
        assert top[2]["author"] == "charlie"

    def test_cluster_produces_domain_bus_factor(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """Cluster produces domain_bus_factor cluster."""
        clusters = learner.cluster(single_owner_evidences)
        dbf = [c for c in clusters if c["pattern_type"] == "domain_bus_factor"]
        assert len(dbf) == 1
        assert dbf[0]["total_domains"] >= 2  # pipeline, crm, billing

    def test_bus_factor_risk_detection(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """Pipeline domain has bus factor = 1 (alice dominates)."""
        clusters = learner.cluster(single_owner_evidences)
        dbf = [c for c in clusters if c["pattern_type"] == "domain_bus_factor"][0]
        pipeline = [d for d in dbf["domains"] if d["domain"] == "pipeline"]
        assert len(pipeline) == 1
        assert pipeline[0]["bus_factor"] == 1
        assert pipeline[0]["is_risk"] is True
        assert pipeline[0]["top_author"] == "alice"

    def test_healthy_domain_not_risk(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """CRM domain has 3 contributors, not a risk."""
        clusters = learner.cluster(single_owner_evidences)
        dbf = [c for c in clusters if c["pattern_type"] == "domain_bus_factor"][0]
        crm = [d for d in dbf["domains"] if d["domain"] == "crm"]
        assert len(crm) == 1
        assert crm[0]["total_authors"] == 3

    def test_cluster_produces_knowledge_concentration(
        self, learner: GitOwnershipLearner, single_owner_evidences: List[Evidence]
    ) -> None:
        """Cluster produces knowledge_concentration cluster."""
        clusters = learner.cluster(single_owner_evidences)
        kc = [c for c in clusters if c["pattern_type"] == "knowledge_concentration"]
        assert len(kc) == 1
        assert kc[0]["total_authors"] == 3

    def test_empty_evidences(self, learner: GitOwnershipLearner) -> None:
        """Empty input produces no clusters."""
        clusters = learner.cluster([])
        assert clusters == []

    def test_single_evidence(self, learner: GitOwnershipLearner) -> None:
        """Single evidence still produces clusters."""
        evs = [
            Evidence(
                source="a.py",
                data={"file_path": "a.py", "author": "alice", "commits": 10},
            ),
        ]
        clusters = learner.cluster(evs)
        # Should produce at least single_owner + author_distribution
        assert len(clusters) >= 2


class TestGitOwnershipConfidence:
    """Tests for confidence calculation."""

    def test_single_owner_high_pct(self, learner: GitOwnershipLearner) -> None:
        """High single-owner % → high confidence."""
        cluster = {
            "pattern_type": "single_owner_files",
            "total_files": 100,
            "single_owner_pct": 60.0,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 60.0

    def test_single_owner_zero_files(self, learner: GitOwnershipLearner) -> None:
        """Zero files → zero confidence."""
        cluster = {
            "pattern_type": "single_owner_files",
            "total_files": 0,
            "single_owner_pct": 0,
        }
        assert learner.calculate_confidence(cluster) == 0.0

    def test_author_dist_many_commits(self, learner: GitOwnershipLearner) -> None:
        """Many commits → high confidence."""
        cluster = {
            "pattern_type": "author_distribution",
            "total_authors": 5,
            "total_commits": 200,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 90.0

    def test_author_dist_few_commits(self, learner: GitOwnershipLearner) -> None:
        """Few commits → lower confidence."""
        cluster = {
            "pattern_type": "author_distribution",
            "total_authors": 2,
            "total_commits": 10,
        }
        conf = learner.calculate_confidence(cluster)
        assert 60.0 <= conf < 90.0

    def test_bus_factor_with_risk(self, learner: GitOwnershipLearner) -> None:
        """Risk domains boost confidence."""
        cluster = {
            "pattern_type": "domain_bus_factor",
            "total_domains": 5,
            "risk_domain_count": 2,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 70.0

    def test_bus_factor_no_risk(self, learner: GitOwnershipLearner) -> None:
        """No risk domains → base confidence."""
        cluster = {
            "pattern_type": "domain_bus_factor",
            "total_domains": 5,
            "risk_domain_count": 0,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 60.0

    def test_knowledge_concentration(self, learner: GitOwnershipLearner) -> None:
        """Specialist percentage drives confidence."""
        cluster = {
            "pattern_type": "knowledge_concentration",
            "total_authors": 10,
            "specialist_pct": 50.0,
        }
        conf = learner.calculate_confidence(cluster)
        assert conf >= 60.0

    def test_unknown_pattern_type(self, learner: GitOwnershipLearner) -> None:
        """Unknown type returns 0."""
        assert learner.calculate_confidence({"pattern_type": "unknown"}) == 0.0


class TestGitOwnershipPattern:
    """Tests for pattern generation."""

    def test_single_owner_pattern(self, learner: GitOwnershipLearner) -> None:
        """single_owner_files cluster → Pattern with metadata."""
        cluster = {
            "pattern_type": "single_owner_files",
            "total_files": 50,
            "single_owner_count": 20,
            "single_owner_pct": 40.0,
            "single_owner_files": [
                {
                    "file_path": "svc.py",
                    "top_author": "alice",
                    "top_pct": 95.0,
                    "total_commits": 20,
                    "author_count": 2,
                }
            ],
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "ownership::single_owner_files"
        assert p.category == "ownership"
        assert p.metadata["single_owner_count"] == 20
        assert p.metadata["single_owner_pct"] == 40.0

    def test_author_distribution_pattern(self, learner: GitOwnershipLearner) -> None:
        """author_distribution cluster → Pattern with top authors."""
        cluster = {
            "pattern_type": "author_distribution",
            "top_authors": [{"author": "alice", "commits": 100, "pct": 60.0}],
            "total_authors": 5,
            "total_commits": 170,
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "ownership::author_distribution"
        assert p.metadata["total_authors"] == 5

    def test_bus_factor_pattern(self, learner: GitOwnershipLearner) -> None:
        """domain_bus_factor cluster → Pattern with risk domains."""
        cluster = {
            "pattern_type": "domain_bus_factor",
            "total_domains": 3,
            "risk_domain_count": 1,
            "risk_domains": [
                {
                    "domain": "pipeline",
                    "bus_factor": 1,
                    "top_author": "alice",
                    "top_author_pct": 94.0,
                    "file_count": 5,
                }
            ],
            "domains": [
                {
                    "domain": "crm",
                    "bus_factor": 2,
                    "total_authors": 3,
                    "is_risk": False,
                }
            ],
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "ownership::domain_bus_factor"
        assert p.metadata["risk_domain_count"] == 1
        assert p.metadata["risk_domains"][0]["domain"] == "pipeline"

    def test_knowledge_concentration_pattern(
        self, learner: GitOwnershipLearner
    ) -> None:
        """knowledge_concentration cluster → Pattern."""
        cluster = {
            "pattern_type": "knowledge_concentration",
            "total_authors": 5,
            "specialist_count": 2,
            "generalist_count": 1,
            "specialist_pct": 40.0,
            "specialists": [
                {"author": "alice", "domain_count": 1, "domains": ["pipeline"]},
            ],
            "generalists": [
                {"author": "charlie", "domain_count": 3},
            ],
            "evidences": [],
        }
        p = learner.cluster_to_pattern(cluster)
        assert p.name == "ownership::knowledge_concentration"
        assert p.metadata["specialist_count"] == 2


class TestGitOwnershipVault:
    """Tests for vault store/query ownership methods."""

    def test_store_and_query_ownership(self, tmp_path: Path) -> None:
        """Store ownership records and query them back."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.store_ownership(
            [
                {"file_path": "a.py", "author": "alice", "commits": 10, "pct": 80.0},
                {"file_path": "a.py", "author": "bob", "commits": 2, "pct": 20.0},
                {"file_path": "b.py", "author": "alice", "commits": 5, "pct": 100.0},
            ]
        )

        all_records = vault.query_ownership()
        assert len(all_records) == 3

    def test_query_ownership_by_file(self, tmp_path: Path) -> None:
        """Filter ownership by file_path."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.store_ownership(
            [
                {"file_path": "a.py", "author": "alice", "commits": 10, "pct": 80.0},
                {"file_path": "b.py", "author": "bob", "commits": 5, "pct": 100.0},
            ]
        )

        result = vault.query_ownership(file_path="a.py")
        assert len(result) == 1
        assert result[0]["author"] == "alice"

    def test_query_ownership_by_author(self, tmp_path: Path) -> None:
        """Filter ownership by author."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.store_ownership(
            [
                {"file_path": "a.py", "author": "alice", "commits": 10, "pct": 80.0},
                {"file_path": "b.py", "author": "bob", "commits": 5, "pct": 100.0},
                {"file_path": "c.py", "author": "alice", "commits": 3, "pct": 60.0},
            ]
        )

        result = vault.query_ownership(author="alice")
        assert len(result) == 2

    def test_ownership_count(self, tmp_path: Path) -> None:
        """Count ownership records."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.store_ownership(
            [
                {"file_path": "a.py", "author": "alice", "commits": 10, "pct": 100.0},
                {"file_path": "b.py", "author": "bob", "commits": 5, "pct": 100.0},
            ]
        )
        assert vault.ownership_count() == 2

    def test_ownership_count_empty(self, tmp_path: Path) -> None:
        """Empty vault returns 0."""
        vault = CodebaseVault()
        vault.init(tmp_path)
        assert vault.ownership_count() == 0


class TestGitOwnershipE2E:
    """End-to-end test with vault + runtime."""

    def test_e2e_via_runtime(
        self, single_owner_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """GitOwnershipLearner produces patterns through LearnerRuntime."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime

        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.load_evidences(single_owner_evidences)

        learner = GitOwnershipLearner()
        runtime = LearnerRuntime(vault=vault, learners=[learner])
        patterns = runtime.run()

        # Should produce ≥3 patterns (acceptance criteria)
        assert len(patterns) >= 3
        categories = {p.category for p in patterns}
        assert "ownership" in categories

        # Verify patterns were committed to vault
        stored = vault.query_patterns(category="ownership")
        assert len(stored) >= 3

    def test_e2e_confidence_above_threshold(
        self, single_owner_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """All emitted patterns have confidence >= 60%."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime

        vault = CodebaseVault()
        vault.init(tmp_path)
        vault.load_evidences(single_owner_evidences)

        learner = GitOwnershipLearner()
        runtime = LearnerRuntime(vault=vault, learners=[learner])
        patterns = runtime.run()

        for p in patterns:
            assert (
                p.confidence >= 60.0
            ), f"Pattern {p.name} has confidence {p.confidence} < 60"

    def test_e2e_all_three_learners(
        self, single_owner_evidences: List[Evidence], tmp_path: Path
    ) -> None:
        """All 3 learners run together without conflict."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime
        from knowledge_memory.verticals.codebase.layer_learner import LayerLearner
        from knowledge_memory.verticals.codebase.naming_learner import NamingLearner

        vault = CodebaseVault()
        vault.init(tmp_path)

        # Need naming-compatible evidences too
        naming_evs = [
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
                data={"name": "Customer", "type": "class", "layer": "service"},
            ),
            Evidence(
                source="route.py",
                data={
                    "name": "endpoint",
                    "type": "function",
                    "layer": "route",
                    "file_path": "app/routes/customer.py",
                },
                metadata={"layer": "route"},
            ),
            Evidence(
                source="model.py",
                data={
                    "name": "UserModel",
                    "type": "class",
                    "layer": "model",
                    "file_path": "app/models/user.py",
                },
                metadata={"layer": "model"},
            ),
        ]

        # Combine naming + ownership evidences
        all_evs = naming_evs + single_owner_evidences
        vault.load_evidences(all_evs)

        naming = NamingLearner()
        layers = LayerLearner()
        ownership = GitOwnershipLearner()
        runtime = LearnerRuntime(vault=vault, learners=[naming, layers, ownership])
        patterns = runtime.run()

        categories = {p.category for p in patterns}
        assert "naming" in categories
        assert "layers" in categories
        assert "ownership" in categories

    def test_e2e_from_stored_ownership(self, tmp_path: Path) -> None:
        """GitOwnershipLearner reads from vault-stored ownership data."""
        from knowledge_memory.core.learners.runtime import LearnerRuntime

        vault = CodebaseVault()
        vault.init(tmp_path)

        # Store ownership data directly (as bootstrap would)
        vault.store_ownership(
            [
                {
                    "file_path": "modules/crm/service.py",
                    "author": "alice",
                    "commits": 30,
                    "pct": 75.0,
                },
                {
                    "file_path": "modules/crm/service.py",
                    "author": "bob",
                    "commits": 10,
                    "pct": 25.0,
                },
                {
                    "file_path": "modules/crm/route.py",
                    "author": "alice",
                    "commits": 20,
                    "pct": 100.0,
                },
                {
                    "file_path": "modules/billing/invoice.py",
                    "author": "charlie",
                    "commits": 15,
                    "pct": 60.0,
                },
                {
                    "file_path": "modules/billing/invoice.py",
                    "author": "bob",
                    "commits": 10,
                    "pct": 40.0,
                },
                {
                    "file_path": "modules/billing/payment.py",
                    "author": "charlie",
                    "commits": 8,
                    "pct": 80.0,
                },
                {
                    "file_path": "modules/billing/payment.py",
                    "author": "alice",
                    "commits": 2,
                    "pct": 20.0,
                },
            ]
        )

        learner = GitOwnershipLearner()
        runtime = LearnerRuntime(vault=vault, learners=[learner])
        patterns = runtime.run()

        assert len(patterns) >= 3
        pattern_names = {p.name for p in patterns}
        assert "ownership::single_owner_files" in pattern_names
        assert "ownership::author_distribution" in pattern_names
        assert "ownership::domain_bus_factor" in pattern_names
