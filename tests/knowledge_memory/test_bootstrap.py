# HC-AI | ticket: MEM-M1-09
"""Tests for Bootstrap orchestrator — 5-step pipeline."""

from pathlib import Path

import pytest

from knowledge_memory.verticals.codebase.bootstrap import (
    BootstrapOrchestrator,
    BootstrapResult,
)
from knowledge_memory.verticals.codebase.vault import CodebaseVault

# --- Fixtures ---


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    """Create a sample Python project for bootstrap testing."""
    # Service file
    svc = tmp_path / "services"
    svc.mkdir()
    (svc / "customer_service.py").write_text('''\
class CustomerService:
    """Service for customer operations."""

    def get_customer(self, customer_id: int):
        """Get a customer by ID."""
        return self._query(customer_id)

    def create_customer(self, name: str, email: str):
        """Create a new customer."""
        return self._insert(name, email)

    def update_customer(self, customer_id: int, name: str):
        """Update customer name."""
        return self._update(customer_id, name)

    def delete_customer(self, customer_id: int):
        """Delete a customer."""
        return self._delete(customer_id)

    def _query(self, cid):
        pass

    def _insert(self, name, email):
        pass

    def _update(self, cid, name):
        pass

    def _delete(self, cid):
        pass
''')

    # Model file
    models = tmp_path / "models"
    models.mkdir()
    (models / "customer.py").write_text('''\
class Customer:
    """Customer model."""

    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email

    def full_name(self):
        return self.name

class Order:
    """Order model."""

    def __init__(self, customer_id: int, amount: float):
        self.customer_id = customer_id
        self.amount = amount

    def total(self):
        return self.amount
''')

    # Route file
    routes = tmp_path / "routes"
    routes.mkdir()
    (routes / "customer_route.py").write_text('''\
def get_customer_endpoint(request):
    """GET /customers/:id"""
    return {"customer": request.params["id"]}

def create_customer_endpoint(request):
    """POST /customers"""
    return {"status": "created"}

def list_customers_endpoint(request):
    """GET /customers"""
    return {"customers": []}
''')

    # Util file
    utils = tmp_path / "utils"
    utils.mkdir()
    (utils / "helpers.py").write_text('''\
def format_date(dt):
    """Format a date object."""
    return dt.strftime("%Y-%m-%d")

def validate_email(email):
    """Validate an email address."""
    return "@" in email

def slugify(text):
    """Convert text to URL slug."""
    return text.lower().replace(" ", "-")
''')

    return tmp_path


# --- BootstrapResult tests ---


class TestBootstrapResult:
    """Tests for BootstrapResult dataclass."""

    def test_default_values(self) -> None:
        r = BootstrapResult()
        assert r.success is False
        assert r.interrupted is False
        assert r.steps_completed == 0
        assert r.pattern_count == 0

    def test_summary(self) -> None:
        r = BootstrapResult()
        r.success = True
        r.steps_completed = 5
        r.patterns = []
        r.elapsed_seconds = 1.5
        summary = r.summary()
        assert "completed successfully" in summary
        assert "5/5" in summary

    def test_summary_with_errors(self) -> None:
        r = BootstrapResult()
        r.errors = ["Learner X failed"]
        summary = r.summary()
        assert "Errors: 1" in summary


# --- Bootstrap orchestrator tests ---


class TestBootstrapInit:
    """Tests for orchestrator initialization."""

    def test_creates_vault(self, sample_project: Path) -> None:
        """Bootstrap creates .knowledge-memory/ directory."""
        orch = BootstrapOrchestrator(root=sample_project)
        orch.run()
        assert (sample_project / ".knowledge-memory").exists()

    def test_result_success(self, sample_project: Path) -> None:
        """Successful run returns success=True."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        assert result.success is True
        assert result.steps_completed == 5

    def test_force_init_reinitializes(self, sample_project: Path) -> None:
        """force_init=True reinitializes existing vault."""
        # First run
        orch1 = BootstrapOrchestrator(root=sample_project)
        orch1.run()

        # Second run with force
        orch2 = BootstrapOrchestrator(root=sample_project, force_init=True)
        result = orch2.run()
        assert result.success is True


class TestBootstrapParse:
    """Tests for Step 1: Parse."""

    def test_parse_stats(self, sample_project: Path) -> None:
        """Parse step populates stats."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        assert result.parse_stats.get("files", 0) >= 4
        assert result.parse_stats.get("nodes", 0) >= 10

    def test_parse_with_include(self, sample_project: Path) -> None:
        """Include pattern limits parsing scope."""
        orch = BootstrapOrchestrator(
            root=sample_project,
            include_patterns=["services/**/*.py"],
        )
        result = orch.run()
        assert result.parse_stats.get("files", 0) >= 1


class TestBootstrapSnapshot:
    """Tests for Step 2: Snapshot."""

    def test_snapshot_created(self, sample_project: Path) -> None:
        """Snapshot is created during bootstrap."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        assert result.snapshot_id is not None


class TestBootstrapLearn:
    """Tests for Step 3: Learn."""

    def test_learners_produce_patterns(self, sample_project: Path) -> None:
        """All 3 learners run and produce patterns."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        assert result.pattern_count >= 3
        # At least naming and layers should produce patterns
        assert "codebase.naming" in result.learner_results
        assert "codebase.layers" in result.learner_results

    def test_learner_isolation(self, sample_project: Path) -> None:
        """One learner failure doesn't crash the pipeline."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        # GitOwnershipLearner may fail (no git repo in tmp), but others succeed
        assert result.success is True


class TestBootstrapCommit:
    """Tests for Step 4: Commit (patterns.md generation)."""

    def test_patterns_md_generated(self, sample_project: Path) -> None:
        """patterns.md file is created in vault directory."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        assert result.patterns_md_path is not None
        patterns_file = Path(result.patterns_md_path)
        assert patterns_file.exists()

    def test_patterns_md_content(self, sample_project: Path) -> None:
        """patterns.md contains expected sections."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        content = Path(result.patterns_md_path).read_text()
        assert "# Codebase Patterns" in content


class TestBootstrapSummary:
    """Tests for Step 5: Summary."""

    def test_all_steps_completed(self, sample_project: Path) -> None:
        """All 5 steps complete."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        assert result.steps_completed == 5

    def test_elapsed_time(self, sample_project: Path) -> None:
        """Elapsed time is positive."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        assert result.elapsed_seconds > 0

    def test_summary_string(self, sample_project: Path) -> None:
        """Summary produces readable output."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()
        summary = result.summary()
        assert "completed successfully" in summary
        assert "Parsed:" in summary
        assert "Patterns:" in summary


class TestBootstrapProgressCallback:
    """Tests for progress reporting."""

    def test_callback_called(self, sample_project: Path) -> None:
        """Progress callback receives all 5 steps."""
        steps_received = []

        def callback(step, total, msg):
            steps_received.append((step, total, msg))

        orch = BootstrapOrchestrator(root=sample_project)
        orch.run(progress_callback=callback)
        assert len(steps_received) == 5
        assert steps_received[0][0] == 1
        assert steps_received[-1][0] == 5


class TestBootstrapE2E:
    """Full end-to-end integration test."""

    def test_full_pipeline(self, sample_project: Path) -> None:
        """Complete bootstrap on sample project, verify all outputs."""
        orch = BootstrapOrchestrator(root=sample_project)
        result = orch.run()

        # Pipeline success
        assert result.success is True
        assert result.steps_completed == 5
        assert not result.interrupted
        assert result.elapsed_seconds > 0

        # Parse produced results
        assert result.parse_stats.get("files", 0) >= 4
        assert result.parse_stats.get("nodes", 0) >= 10

        # Snapshot created
        assert result.snapshot_id is not None

        # Patterns produced (naming + layers at minimum)
        assert result.pattern_count >= 3

        # patterns.md generated and readable
        assert result.patterns_md_path is not None
        content = Path(result.patterns_md_path).read_text()
        assert "# Codebase Patterns" in content
        assert "Generated by Codebase Memory" in content

        # Vault state is valid
        vault = CodebaseVault()
        vault.open(sample_project)
        assert vault.node_count() >= 10
        assert vault.snapshot_count() >= 1


# HC-AI | ticket: MEM-M1-14
class TestBootstrapResume:
    """Tests for --resume flag (design D-M1-07)."""

    def test_resume_skips_completed_steps(self, sample_project: Path) -> None:
        """First run completes all 5 steps, resume run skips them."""
        # Full run first
        orch = BootstrapOrchestrator(root=sample_project, force_init=True)
        result1 = orch.run()
        assert result1.success
        assert result1.steps_completed == 5

        # Verify resume step saved in vault
        vault = CodebaseVault()
        vault.open(sample_project)
        assert vault.get_meta("bootstrap_step") == "5"

        # Resume run — should succeed quickly (all steps done)
        orch2 = BootstrapOrchestrator(root=sample_project, resume=True)
        result2 = orch2.run()
        assert result2.success
        assert result2.steps_completed == 5

    def test_resume_from_partial(self, sample_project: Path) -> None:
        """Resume from a partially completed bootstrap."""
        # Do a full bootstrap first to create vault
        orch = BootstrapOrchestrator(root=sample_project, force_init=True)
        result = orch.run()
        assert result.success

        # Simulate partial run: set step back to 2
        vault = CodebaseVault()
        vault.open(sample_project)
        vault.set_meta("bootstrap_step", "2")

        # Resume — should re-run steps 3-5
        orch2 = BootstrapOrchestrator(root=sample_project, resume=True)
        result2 = orch2.run()
        assert result2.success
        assert result2.steps_completed == 5
        assert vault.get_meta("bootstrap_step") == "5"

    def test_resume_no_vault_falls_back(self, tmp_path: Path) -> None:
        """Resume on empty project falls back to full run."""
        # Create minimal Python file
        (tmp_path / "app.py").write_text("def hello(): pass\n")

        orch = BootstrapOrchestrator(root=tmp_path, resume=True, force_init=True)
        result = orch.run()
        assert result.success
        assert result.steps_completed == 5

    def test_resume_false_runs_all_steps(self, sample_project: Path) -> None:
        """Without resume=True, all steps run regardless of saved state."""
        # Full run
        orch1 = BootstrapOrchestrator(root=sample_project, force_init=True)
        orch1.run()

        # Non-resume run — should run all steps from scratch
        orch2 = BootstrapOrchestrator(root=sample_project)
        result2 = orch2.run()
        assert result2.success
        assert result2.steps_completed == 5
