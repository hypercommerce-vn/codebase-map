"""Tests for LearnerRuntime orchestrator (KMP-M0-03)."""

# HC-AI | ticket: KMP-M0-03

from pathlib import Path

import pytest

from knowledge_memory.core.learners import BaseLearner, LearnerRuntime, Pattern
from knowledge_memory.core.parsers import BaseParser, Evidence
from knowledge_memory.core.vault import BaseVault


class FakeVault(BaseVault):
    VERTICAL_NAME = "fake"

    def __init__(self):
        self.committed: list[Pattern] = []

    def init(self, root: Path, force: bool = False) -> None:
        return None

    def snapshot(self):
        return object()

    def get_corpus_iterator(self):
        return iter([])

    def schema_extension_sql(self) -> str:
        return ""

    def commit_pattern(self, pattern: Pattern) -> None:
        self.committed.append(pattern)


class CountingLearner(BaseLearner):
    LEARNER_NAME = "counting"
    LEARNER_CATEGORY = "test"
    MIN_EVIDENCE_COUNT = 2
    MIN_CONFIDENCE = 60.0

    def extract_evidence(self, vault):
        return [1, 2, 3, 4]

    def cluster(self, evidences):
        return [evidences]

    def calculate_confidence(self, cluster):
        return 80.0

    def cluster_to_pattern(self, cluster):
        return Pattern(name="test::all", category="test")


class LowConfLearner(CountingLearner):
    LEARNER_NAME = "lowconf"

    def calculate_confidence(self, cluster):
        return 10.0


class TinyEvidenceLearner(CountingLearner):
    LEARNER_NAME = "tiny"
    MIN_EVIDENCE_COUNT = 99

    def extract_evidence(self, vault):
        return [1]


class DummyParser(BaseParser):
    PARSER_NAME = "dummy"
    SUPPORTED_EXTENSIONS = (".txt",)

    def parse(self, source: Path):
        yield Evidence(source=str(source))


def test_runtime_register_and_run_emits_pattern():
    vault = FakeVault()
    runtime = LearnerRuntime(vault=vault)
    runtime.register_learner(CountingLearner())
    runtime.register_parser(DummyParser())

    assert len(runtime.learners) == 1
    assert len(runtime.parsers) == 1

    patterns = runtime.run()
    assert len(patterns) == 1
    assert patterns[0].confidence == 80.0
    assert patterns[0].vertical == "fake"
    assert vault.committed == patterns


def test_runtime_skips_low_confidence_and_small_evidence():
    vault = FakeVault()
    runtime = LearnerRuntime(
        vault=vault,
        learners=[LowConfLearner(), TinyEvidenceLearner()],
    )
    patterns = runtime.run()
    assert patterns == []
    assert vault.committed == []


def test_runtime_requires_vault():
    runtime = LearnerRuntime()
    with pytest.raises(ValueError):
        runtime.run()


def test_runtime_rejects_non_learner():
    runtime = LearnerRuntime()
    with pytest.raises(TypeError):
        runtime.register_learner(object())  # type: ignore[arg-type]


def test_runtime_rejects_non_parser():
    runtime = LearnerRuntime()
    with pytest.raises(TypeError):
        runtime.register_parser(object())  # type: ignore[arg-type]


def test_runtime_run_accepts_vault_override():
    vault = FakeVault()
    runtime = LearnerRuntime(learners=[CountingLearner()])
    patterns = runtime.run(vault=vault)
    assert len(patterns) == 1
    assert vault.committed == patterns
