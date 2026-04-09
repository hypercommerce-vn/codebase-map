"""Tests for BaseLearner ABC (KMP-M0-02)."""

# HC-AI | ticket: KMP-M0-02

import pytest

from knowledge_memory.core.learners import BaseLearner, Pattern


def test_base_learner_is_abstract():
    with pytest.raises(TypeError):
        BaseLearner()  # type: ignore[abstract]


def test_base_learner_concrete_subclass_works():
    class DummyLearner(BaseLearner):
        LEARNER_NAME = "dummy"
        LEARNER_CATEGORY = "test"
        MIN_EVIDENCE_COUNT = 1
        MIN_CONFIDENCE = 50.0

        def extract_evidence(self, vault):
            return [1, 2, 3]

        def cluster(self, evidences):
            return [evidences]

        def calculate_confidence(self, cluster):
            return 90.0

        def cluster_to_pattern(self, cluster):
            return Pattern(name="dummy::one", category="test")

    learner = DummyLearner()
    assert learner.LEARNER_NAME == "dummy"
    assert learner.describe()["category"] == "test"
    ev = learner.extract_evidence(vault=None)
    clusters = learner.cluster(ev)
    assert learner.calculate_confidence(clusters[0]) == 90.0
    pat = learner.cluster_to_pattern(clusters[0])
    assert isinstance(pat, Pattern)


def test_base_learner_requires_all_abstracts():
    class Partial(BaseLearner):
        def extract_evidence(self, vault):
            return []

    with pytest.raises(TypeError):
        Partial()  # type: ignore[abstract]
