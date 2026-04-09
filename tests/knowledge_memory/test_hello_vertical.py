# HC-AI | ticket: KMP-M0-05
"""Smoke + e2e tests for the Hello vertical — Day 3 unit + Day 4 runtime."""

from pathlib import Path
from typing import Iterator, List, Optional

import pytest

from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.learners.runtime import LearnerRuntime
from knowledge_memory.core.parsers.evidence import Evidence
from knowledge_memory.core.vault.base import BaseVault
from knowledge_memory.verticals.hello import VERTICAL_NAME
from knowledge_memory.verticals.hello.hello_learner import HelloLearner
from knowledge_memory.verticals.hello.hello_parser import HelloParser

# -- Fixtures ----------------------------------------------------------------


class _StubVault(BaseVault):
    """Minimal vault stub that yields Evidence from in-memory lines."""

    VERTICAL_NAME = "hello_test"

    def __init__(self, evidences: Optional[List[Evidence]] = None) -> None:
        self._evidences = evidences or []
        self._committed: List[Pattern] = []

    def init(self, root: Path, force: bool = False) -> None:
        pass  # pragma: no cover

    def snapshot(self) -> object:
        return {}  # pragma: no cover

    def get_corpus_iterator(self) -> Iterator[Evidence]:
        yield from self._evidences

    def schema_extension_sql(self) -> str:
        return ""  # pragma: no cover

    def commit_pattern(self, pattern: Pattern) -> None:
        """Record committed patterns for assertion."""
        self._committed.append(pattern)


@pytest.fixture()
def sample_txt(tmp_path: Path) -> Path:
    """Create a sample .txt file with repeated words."""
    p = tmp_path / "sample.txt"
    p.write_text("hello world\nhello python\nhello world\n")
    return p


@pytest.fixture()
def empty_txt(tmp_path: Path) -> Path:
    """Create an empty .txt file."""
    p = tmp_path / "empty.txt"
    p.write_text("")
    return p


# -- HelloParser tests -------------------------------------------------------


class TestHelloParser:
    """Tests for HelloParser."""

    def test_instantiates(self) -> None:
        """HelloParser is not abstract — can be instantiated."""
        parser = HelloParser()
        assert parser.PARSER_NAME == "hello_txt"

    def test_parse_yields_evidence(self, sample_txt: Path) -> None:
        """parse() yields Evidence objects for non-empty lines."""
        parser = HelloParser()
        results = list(parser.parse(sample_txt))
        assert len(results) == 3
        assert all(isinstance(e, Evidence) for e in results)
        assert results[0].data["text"] == "hello world"

    def test_parse_empty_file(self, empty_txt: Path) -> None:
        """parse() yields nothing for an empty file."""
        parser = HelloParser()
        results = list(parser.parse(empty_txt))
        assert results == []

    def test_parse_nonexistent_file(self, tmp_path: Path) -> None:
        """parse() yields nothing for a nonexistent file."""
        parser = HelloParser()
        results = list(parser.parse(tmp_path / "nope.txt"))
        assert results == []

    def test_parse_non_txt_file(self, tmp_path: Path) -> None:
        """parse() yields nothing for a non-.txt file."""
        p = tmp_path / "readme.md"
        p.write_text("# Hello")
        parser = HelloParser()
        results = list(parser.parse(p))
        assert results == []

    def test_supports(self) -> None:
        """supports() returns True for .txt, False for others."""
        parser = HelloParser()
        assert parser.supports(Path("file.txt")) is True
        assert parser.supports(Path("file.py")) is False

    def test_line_range_set(self, sample_txt: Path) -> None:
        """Evidence line_range is set correctly."""
        parser = HelloParser()
        results = list(parser.parse(sample_txt))
        assert results[0].line_range == (1, 1)
        assert results[2].line_range == (3, 3)


# -- HelloLearner tests ------------------------------------------------------


class TestHelloLearner:
    """Tests for HelloLearner."""

    def test_instantiates(self) -> None:
        """HelloLearner is not abstract — can be instantiated."""
        learner = HelloLearner()
        assert learner.LEARNER_NAME == "hello.word_count"

    def test_extract_evidence_from_vault(self) -> None:
        """extract_evidence returns all evidence from vault."""
        ev = [Evidence(source="a.txt", data={"text": "hello"})]
        vault = _StubVault(ev)
        learner = HelloLearner()
        result = learner.extract_evidence(vault)
        assert len(result) == 1

    def test_cluster_groups_words(self) -> None:
        """cluster() groups evidence by word."""
        evs = [
            Evidence(source="a.txt", data={"text": "hello world"}),
            Evidence(source="b.txt", data={"text": "hello python"}),
        ]
        learner = HelloLearner()
        clusters = learner.cluster(evs)
        words = {c["word"] for c in clusters}
        assert "hello" in words

    def test_calculate_confidence(self) -> None:
        """confidence scales with evidence count."""
        learner = HelloLearner()
        cluster = {"word": "test", "evidences": [None, None, None]}
        assert learner.calculate_confidence(cluster) == 60.0

    def test_calculate_confidence_capped(self) -> None:
        """confidence is capped at 100."""
        learner = HelloLearner()
        cluster = {"word": "test", "evidences": [None] * 10}
        assert learner.calculate_confidence(cluster) == 100.0

    def test_cluster_to_pattern_returns_pattern(self) -> None:
        """cluster_to_pattern returns a Pattern instance."""
        learner = HelloLearner()
        cluster = {
            "word": "hello",
            "evidences": [Evidence(source="a.txt", data={"text": "hello"})],
        }
        pattern = learner.cluster_to_pattern(cluster)
        assert isinstance(pattern, Pattern)
        assert pattern.name == "frequent_word::hello"
        assert pattern.category == "stats"


# -- Vertical registration ---------------------------------------------------


class TestHelloVertical:
    """Tests for vertical registration and integration."""

    def test_vertical_name(self) -> None:
        """VERTICAL_NAME is set correctly."""
        assert VERTICAL_NAME == "hello"

    def test_learner_with_parser_end_to_end(self, sample_txt: Path) -> None:
        """HelloParser + HelloLearner work together end-to-end."""
        parser = HelloParser()
        evidences = list(parser.parse(sample_txt))
        vault = _StubVault(evidences)
        learner = HelloLearner()
        extracted = learner.extract_evidence(vault)
        clusters = learner.cluster(extracted)
        patterns = []
        for cluster in clusters:
            conf = learner.calculate_confidence(cluster)
            if conf >= learner.MIN_CONFIDENCE:
                p = learner.cluster_to_pattern(cluster)
                p.confidence = conf
                patterns.append(p)
        assert len(patterns) >= 1
        assert all(isinstance(p, Pattern) for p in patterns)
        assert all(p.confidence >= 50.0 for p in patterns)


# -- E2E via LearnerRuntime (Day 4) -----------------------------------------


class TestHelloE2E:
    """Full pipeline: LearnerRuntime + HelloLearner + HelloParser + StubVault."""

    def test_runtime_full_pipeline(self, sample_txt: Path) -> None:
        """LearnerRuntime.run() with Hello components produces patterns."""
        # HC-AI | ticket: KMP-M0-05
        parser = HelloParser()
        evidences = list(parser.parse(sample_txt))
        vault = _StubVault(evidences)

        runtime = LearnerRuntime()
        runtime.register_learner(HelloLearner())
        runtime.register_parser(parser)

        patterns = runtime.run(vault)

        assert len(patterns) >= 1
        assert all(isinstance(p, Pattern) for p in patterns)
        assert all(p.confidence >= 50.0 for p in patterns)
        # "hello" appears 3 times → confidence = 60.0
        hello_patterns = [p for p in patterns if "hello" in p.name]
        assert len(hello_patterns) == 1
        assert hello_patterns[0].confidence == 60.0

    def test_runtime_commits_to_vault(self, sample_txt: Path) -> None:
        """LearnerRuntime.run() calls vault.commit_pattern for each emitted."""
        parser = HelloParser()
        evidences = list(parser.parse(sample_txt))
        vault = _StubVault(evidences)

        runtime = LearnerRuntime(vault=vault, learners=[HelloLearner()])
        patterns = runtime.run()

        assert len(vault._committed) == len(patterns)
        assert len(vault._committed) >= 1

    def test_runtime_sets_vertical_name(self, sample_txt: Path) -> None:
        """LearnerRuntime sets pattern.vertical from vault.VERTICAL_NAME."""
        parser = HelloParser()
        evidences = list(parser.parse(sample_txt))
        vault = _StubVault(evidences)

        runtime = LearnerRuntime()
        runtime.register_learner(HelloLearner())
        patterns = runtime.run(vault)

        for p in patterns:
            assert p.vertical == "hello_test"

    def test_runtime_empty_corpus_no_patterns(self) -> None:
        """LearnerRuntime with empty vault yields no patterns."""
        vault = _StubVault([])
        runtime = LearnerRuntime(vault=vault, learners=[HelloLearner()])
        patterns = runtime.run()
        assert patterns == []

    def test_runtime_confidence_filter(self) -> None:
        """Only patterns above MIN_CONFIDENCE are emitted."""
        # Single evidence → one word "x" → confidence = 20.0 < 50.0
        vault = _StubVault([Evidence(source="a.txt", data={"text": "x"})])
        runtime = LearnerRuntime(vault=vault, learners=[HelloLearner()])
        patterns = runtime.run()
        assert patterns == []

    def test_runtime_multi_word_corpus(self, tmp_path: Path) -> None:
        """Corpus with repeated words produces correct pattern names."""
        txt = tmp_path / "words.txt"
        txt.write_text(
            "alpha beta\nalpha gamma\nalpha delta\n" "beta gamma\nbeta delta\n"
        )
        parser = HelloParser()
        evidences = list(parser.parse(txt))
        vault = _StubVault(evidences)

        runtime = LearnerRuntime()
        runtime.register_learner(HelloLearner())
        patterns = runtime.run(vault)

        names = {p.name for p in patterns}
        # "alpha" appears 3× → conf 60, "beta" 3× → conf 60,
        # "gamma" 2× → conf 40 (below 50), "delta" 2× → conf 40 (below 50)
        assert "frequent_word::alpha" in names
        assert "frequent_word::beta" in names
        assert "frequent_word::gamma" not in names
        assert "frequent_word::delta" not in names

    def test_parser_describe(self) -> None:
        """HelloParser.describe() returns expected metadata."""
        desc = HelloParser().describe()
        assert desc["name"] == "hello_txt"
        assert ".txt" in desc["extensions"]

    def test_learner_describe(self) -> None:
        """HelloLearner.describe() returns expected metadata."""
        desc = HelloLearner().describe()
        assert desc["name"] == "hello.word_count"
        assert desc["category"] == "stats"
