# Hello Vertical — Reference Implementation

> **Purpose:** Prove the KMP extension contract works in ≤50 LOC.
> Copy this folder as a template to build your own vertical.

---

## What is a Vertical?

A **vertical** is a domain-specific plugin for Knowledge Memory Platform.
It extends Core by providing:

| Component | Base class | Your job |
|-----------|-----------|----------|
| **Parser** | `BaseParser` | Parse domain files → `Evidence` objects |
| **Learner** | `BaseLearner[E, C]` | Cluster evidence → `Pattern` objects |
| **Vault** *(M1)* | `BaseVault` | Storage init, corpus iterator, schema SQL |

Core never imports verticals — the dependency flows one way only.

---

## File Structure

```
verticals/hello/
├── __init__.py          # VERTICAL_NAME = "hello"
├── hello_parser.py      # HelloParser(BaseParser) — 29 LOC
├── hello_learner.py     # HelloLearner(BaseLearner) — 50 LOC
└── README.md            # This file
```

---

## How HelloParser Works

`HelloParser` reads `.txt` files and yields one `Evidence` per non-empty line:

```python
from knowledge_memory.core.parsers.base import BaseParser
from knowledge_memory.core.parsers.evidence import Evidence

class HelloParser(BaseParser):
    PARSER_NAME = "hello_txt"
    SUPPORTED_EXTENSIONS = (".txt",)

    def parse(self, source: Path) -> Iterator[Evidence]:
        for i, line in enumerate(source.read_text().splitlines(), 1):
            if line.strip():
                yield Evidence(
                    source=str(source),
                    data={"text": line.strip()},
                    line_range=(i, i),
                )
```

**Key points:**
- Set `PARSER_NAME` (unique string) and `SUPPORTED_EXTENSIONS` (tuple of suffixes)
- `parse()` yields `Evidence` with `source` (file path) and `data` (dict payload)

---

## How HelloLearner Works

`HelloLearner` counts word frequency and emits `Pattern` for frequent words:

```python
from knowledge_memory.core.learners.base import BaseLearner

class HelloLearner(BaseLearner[Evidence, dict]):
    LEARNER_NAME = "hello.word_count"
    LEARNER_CATEGORY = "stats"
    MIN_EVIDENCE_COUNT = 1    # minimum evidence to proceed
    MIN_CONFIDENCE = 50.0     # minimum confidence to emit pattern

    def extract_evidence(self, vault) -> list[Evidence]:
        return list(vault.get_corpus_iterator())

    def cluster(self, evidences) -> list[dict]:
        # Group by word → [{"word": "hello", "evidences": [...]}]

    def calculate_confidence(self, cluster) -> float:
        return min(100.0, len(cluster["evidences"]) * 20.0)

    def cluster_to_pattern(self, cluster) -> Pattern:
        return Pattern(name=f"frequent_word::{cluster['word']}", ...)
```

**Key points:**
- `BaseLearner[E, C]` — `E` is your evidence type, `C` is your cluster type
- The 4 abstract methods form the **extract → cluster → score → emit** pipeline
- `LearnerRuntime` calls these methods in order and filters by confidence

---

## Running the Full Pipeline

```python
from knowledge_memory.core.learners.runtime import LearnerRuntime
from knowledge_memory.verticals.hello.hello_parser import HelloParser
from knowledge_memory.verticals.hello.hello_learner import HelloLearner

# 1. Register components
runtime = LearnerRuntime()
runtime.register_learner(HelloLearner())
runtime.register_parser(HelloParser())

# 2. Run against a vault (provides corpus iterator)
patterns = runtime.run(vault)

# 3. Each pattern has: name, category, confidence, evidence
for p in patterns:
    print(f"{p.name} (confidence: {p.confidence}%)")
```

---

## Build Your Own Vertical (5-Step Guide)

1. **Create folder:** `verticals/<name>/`
2. **`__init__.py`:** Set `VERTICAL_NAME = "<name>"`
3. **Parser:** Subclass `BaseParser`, implement `parse(source) → Iterator[Evidence]`
4. **Learner:** Subclass `BaseLearner[E, C]`, implement the 4 abstract methods
5. **Register:** Pass instances to `LearnerRuntime` via `register_learner()` / `register_parser()`

**Rule:** Never import from `knowledge_memory.core` into your vertical's `__init__.py` at module level — keep the import-linter CI gate happy.

---

## Tests

Run Hello vertical tests:

```bash
pytest tests/knowledge_memory/test_hello_vertical.py -v
```

The test suite covers:
- Parser: file handling, evidence yield, line ranges, extension filtering
- Learner: extraction, clustering, confidence scoring, pattern conversion
- Integration: parser → learner → patterns end-to-end
- Runtime: full pipeline via `LearnerRuntime.run()`

---

*Hello vertical README · KMP M0 · HC-AI | ticket: KMP-M0-05*
