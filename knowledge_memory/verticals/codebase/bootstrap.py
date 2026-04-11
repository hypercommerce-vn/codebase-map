# HC-AI | ticket: MEM-M1-09
"""Bootstrap orchestrator — 5-step pipeline for codebase analysis.

Pipeline: Parse → Snapshot → Learn → Commit → Summary
Design ref: kmp-M1-design.html Screen B (bootstrap progress).
"""

import logging
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.learners.runtime import LearnerRuntime
from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.verticals.codebase.codebase_parser import PythonASTParser
from knowledge_memory.verticals.codebase.git_ownership_learner import (
    GitOwnershipLearner,
)
from knowledge_memory.verticals.codebase.layer_learner import LayerLearner
from knowledge_memory.verticals.codebase.naming_learner import NamingLearner
from knowledge_memory.verticals.codebase.patterns_generator import (
    generate_patterns_md,
)
from knowledge_memory.verticals.codebase.vault import CodebaseVault

logger = logging.getLogger("codebase-memory.bootstrap")

# HC-AI | ticket: MEM-M1-09
# Default configuration
_DEFAULT_CONFIDENCE_THRESHOLD = 60.0
_DEFAULT_MAX_GIT_COMMITS = 1000


class BootstrapResult:
    """Result of a bootstrap run."""

    def __init__(self) -> None:
        self.success: bool = False
        self.interrupted: bool = False
        self.steps_completed: int = 0
        self.total_steps: int = 5
        self.parse_stats: Dict[str, int] = {}
        self.snapshot_id: Optional[int] = None
        self.patterns: List[Pattern] = []
        self.learner_results: Dict[str, int] = {}
        self.patterns_md_path: Optional[str] = None
        self.elapsed_seconds: float = 0.0
        self.errors: List[str] = []

    @property
    def pattern_count(self) -> int:
        return len(self.patterns)

    def summary(self) -> str:
        """Human-readable summary of the bootstrap result."""
        lines = []
        if self.interrupted:
            lines.append(f"Bootstrap interrupted after step {self.steps_completed}/5")
        elif self.success:
            lines.append("Bootstrap completed successfully")
        else:
            lines.append("Bootstrap failed")

        lines.append(f"  Steps: {self.steps_completed}/{self.total_steps}")
        if self.parse_stats:
            lines.append(
                f"  Parsed: {self.parse_stats.get('files', 0)} files, "
                f"{self.parse_stats.get('nodes', 0)} nodes"
            )
        lines.append(f"  Patterns: {self.pattern_count}")
        if self.learner_results:
            parts = [f"{name}: {count}" for name, count in self.learner_results.items()]
            lines.append(f"  Learners: {', '.join(parts)}")
        lines.append(f"  Time: {self.elapsed_seconds:.1f}s")
        if self.errors:
            lines.append(f"  Errors: {len(self.errors)}")
            for err in self.errors[:3]:
                lines.append(f"    - {err}")
        return "\n".join(lines)


# HC-AI | ticket: MEM-M1-09
class BootstrapOrchestrator:
    """5-step pipeline: Parse → Snapshot → Learn → Commit → Summary.

    Graceful Ctrl+C: saves partial state. Learner isolation:
    one learner crash → log + continue rest.

    Design ref: kmp-M1-design.html Screen B.
    """

    def __init__(
        self,
        root: Path,
        confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
        max_git_commits: int = _DEFAULT_MAX_GIT_COMMITS,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        force_init: bool = False,
    ) -> None:
        self._root = root
        self._confidence_threshold = confidence_threshold
        self._max_git_commits = max_git_commits
        self._include = include_patterns or ["**/*.py"]
        self._exclude = exclude_patterns
        self._force_init = force_init
        self._interrupted = False

        # Components
        self._vault: Optional[CodebaseVault] = None
        self._parser = PythonASTParser()
        self._result = BootstrapResult()

    @property
    def result(self) -> BootstrapResult:
        return self._result

    def run(self, progress_callback=None) -> BootstrapResult:
        """Execute the 5-step bootstrap pipeline.

        Args:
            progress_callback: Optional callable(step, total, message)
                for progress reporting (e.g. rich progress bars).

        Returns:
            BootstrapResult with full details.
        """
        start = time.time()
        self._result = BootstrapResult()

        # Install Ctrl+C handler
        original_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._handle_interrupt)

        try:
            self._run_pipeline(progress_callback)
        except _BootstrapInterrupt:
            self._result.interrupted = True
            logger.warning(
                "Bootstrap interrupted. %d patterns saved.",
                self._result.pattern_count,
            )
        except Exception as exc:
            self._result.errors.append(f"Fatal: {exc}")
            logger.error("Bootstrap fatal error: %s", exc)
        finally:
            signal.signal(signal.SIGINT, original_handler)
            self._result.elapsed_seconds = time.time() - start

        return self._result

    def _run_pipeline(self, progress_callback=None) -> None:
        """Internal pipeline execution."""

        def _progress(step: int, msg: str) -> None:
            if progress_callback:
                progress_callback(step, 5, msg)
            logger.info("[%d/5] %s", step, msg)

        # --- Step 1: Parse ---
        _progress(1, "Parsing codebase...")
        self._step_parse()
        self._check_interrupt()

        # --- Step 2: Snapshot ---
        _progress(2, "Saving snapshot...")
        self._step_snapshot()
        self._check_interrupt()

        # --- Step 3: Learn ---
        _progress(3, "Running learners...")
        self._step_learn()
        self._check_interrupt()

        # --- Step 4: Commit ---
        _progress(4, "Generating patterns.md...")
        self._step_commit()
        self._check_interrupt()

        # --- Step 5: Summary ---
        _progress(5, "Finalizing...")
        self._step_summary()

        self._result.success = True

    # HC-AI | ticket: MEM-M1-09
    def _step_parse(self) -> None:
        """Step 1: Init vault + parse Python files."""
        vault = CodebaseVault()

        # Init or open vault
        vault_dir = self._root / ".knowledge-memory"
        if vault_dir.exists() and not self._force_init:
            vault.open(self._root)
        else:
            vault.init(self._root, force=self._force_init)

        self._vault = vault

        # Parse directory
        evidences: List[Evidence] = list(
            self._parser.parse_directory(
                self._root,
                include=self._include,
                exclude=self._exclude,
            )
        )

        # Load into vault corpus
        vault.load_evidences(evidences)

        # Store nodes into SQLite for query-based learners
        nodes = []
        edges = []
        for ev in evidences:
            node_type = ev.data.get("type", "function")
            if node_type in ("function", "method", "class"):
                nodes.append(
                    {
                        "name": ev.data.get("name", ""),
                        "file_path": ev.source,
                        "node_type": node_type,
                        "layer": ev.data.get("layer", "unknown"),
                        "line_start": (ev.line_range[0] if ev.line_range else 0),
                        "line_end": (ev.line_range[1] if ev.line_range else 0),
                    }
                )
            # Extract call edges
            calls = ev.data.get("calls", [])
            if isinstance(calls, list):
                for call in calls:
                    edges.append(
                        {
                            "source": ev.data.get("name", ""),
                            "target": call,
                            "type": "calls",
                            "file_path": ev.source,
                        }
                    )

        if nodes:
            vault.store_nodes(nodes)
        if edges:
            vault.store_edges(edges)

        # Stats
        stats = self._parser.scan_stats(
            self._root,
            include=self._include,
            exclude=self._exclude,
        )
        self._result.parse_stats = stats
        self._result.steps_completed = 1

    # HC-AI | ticket: MEM-M1-09
    def _step_snapshot(self) -> None:
        """Step 2: Save corpus snapshot with rotation."""
        assert self._vault is not None
        snap = self._vault.snapshot(label="bootstrap")
        self._result.snapshot_id = snap.get("id")
        self._result.steps_completed = 2

    # HC-AI | ticket: MEM-M1-09
    def _step_learn(self) -> None:
        """Step 3: Run all learners with isolation.

        Each learner runs independently. If one crashes, log the error
        and continue with the remaining learners (design decision D-M1-05).
        """
        assert self._vault is not None

        learners = [
            NamingLearner(),
            LayerLearner(),
            GitOwnershipLearner(
                repo_path=str(self._root),
                max_commits=self._max_git_commits,
            ),
        ]

        runtime = LearnerRuntime(vault=self._vault, learners=[])
        all_patterns: List[Pattern] = []

        for learner in learners:
            name = learner.LEARNER_NAME
            try:
                runtime._learners = [learner]
                patterns = runtime.run()
                all_patterns.extend(patterns)
                self._result.learner_results[name] = len(patterns)
                logger.info("Learner %s: %d patterns", name, len(patterns))
            except Exception as exc:
                self._result.errors.append(f"Learner {name} failed: {exc}")
                self._result.learner_results[name] = 0
                logger.error("Learner %s crashed: %s", name, exc)

            self._check_interrupt()

        self._result.patterns = all_patterns
        self._result.steps_completed = 3

    # HC-AI | ticket: MEM-M1-08
    def _step_commit(self) -> None:
        """Step 4: Generate patterns.md from committed patterns."""
        assert self._vault is not None

        generate_patterns_md(
            self._vault,
            confidence_threshold=self._confidence_threshold,
        )

        # Record path
        vert_dir = self._vault.vault_dir / "verticals" / "codebase"
        self._result.patterns_md_path = str(vert_dir / "patterns.md")
        self._result.steps_completed = 4

    def _step_summary(self) -> None:
        """Step 5: Final summary — log completion stats."""
        self._result.steps_completed = 5

    def _handle_interrupt(self, signum, frame) -> None:
        """Ctrl+C handler: set flag for graceful shutdown."""
        self._interrupted = True
        logger.warning("Ctrl+C received. Finishing current step...")

    def _check_interrupt(self) -> None:
        """Check if interrupted and raise if so."""
        if self._interrupted:
            raise _BootstrapInterrupt()


class _BootstrapInterrupt(Exception):
    """Internal signal for graceful Ctrl+C interruption."""

    pass
