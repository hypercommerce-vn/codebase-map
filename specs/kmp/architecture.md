# KMP — Knowledge Memory Platform Architecture
> **Tài liệu kiến trúc nền tảng** · **Author:** @CTO · **Version:** 1.0 · **07/04/2026**
> **Định vị:** Core platform mà mọi vertical (Codebase Memory, Legal Memory, Sales Memory, …) kế thừa
> **Liên quan:** `specs/memory-fdd-v2.md`, `specs/memory-cto-feasibility.md` mục 6-12

---

## 0. Mục đích tài liệu

Tài liệu này định nghĩa **kiến trúc lõi** của Knowledge Memory Platform — nền tảng chia sẻ giữa mọi vertical Memory mà HC sẽ build. Mục tiêu là:

1. Cung cấp **abstraction stable** ngay từ M0, không phải refactor sau
2. Định nghĩa **boundary** Core ↔ Vertical rõ ràng (Core không bao giờ import vertical)
3. Cung cấp **extension points** chuẩn để vertical mới chỉ phải build 2 thứ: Parser + Learner
4. Chứng minh khả thi qua **reference vertical "hello"** 50 dòng

Tài liệu này **không** bàn business model, pricing, marketing — chỉ kiến trúc kỹ thuật.

---

## 1. Triết lý thiết kế

### 1.1 Five Principles of KMP

| # | Nguyên tắc | Hệ quả thiết kế |
|---|-----------|----------------|
| 1 | **Local-first, always** | Mọi storage là SQLite/file hệ thống local. Không có cloud dependency cho core feature. |
| 2 | **BYOK & multi-LLM** | LLM là plugin, không phải dependency cứng. Thay provider không phải refactor app. |
| 3 | **Vertical = Plugin** | Core không bao giờ import vertical. Vertical đăng ký capability qua registry. |
| 4 | **Open vault, closed engine** | Vault format mở (Markdown/SQLite schema) để cộng đồng dùng. Engine có thể obfuscate cho Pro. |
| 5 | **Pattern over data** | Ưu tiên trích pattern (compact, có ý nghĩa) hơn lưu raw data. |

### 1.2 Anti-principles (cái KMP **không** làm)

- **Không** build cloud sync trong v1 (sẽ có trong KMP Cloud Lite phase 2, opt-in)
- **Không** build vector embedding pipeline (theo Aider insight: BM25 + AST đủ tốt)
- **Không** build IDE plugin riêng (đi qua MCP)
- **Không** lock vào 1 LLM provider
- **Không** tự host LLM (BYOK forever)

---

## 2. High-level Architecture

```
                ┌────────────────────────────────────────────┐
                │           USER INTERFACES                   │
                │  ┌─────────┐  ┌─────────┐  ┌────────────┐  │
                │  │  CLI    │  │  MCP    │  │  HTML View │  │
                │  └─────────┘  └─────────┘  └────────────┘  │
                └────────────────┬───────────────────────────┘
                                 │
                ┌────────────────▼───────────────────────────┐
                │       VERTICAL PLUGINS (registered)         │
                │  ┌─────────┐  ┌─────────┐  ┌────────────┐  │
                │  │Codebase │  │  Legal  │  │   Sales    │  │
                │  │  Memory │  │  Memory │  │   Memory   │  │
                │  │         │  │         │  │            │  │
                │  │ Parser  │  │ Parser  │  │  Parser    │  │
                │  │ Learner │  │ Learner │  │  Learner   │  │
                │  │MCP Tool │  │MCP Tool │  │  MCP Tool  │  │
                │  └─────────┘  └─────────┘  └────────────┘  │
                └────────────────┬───────────────────────────┘
                                 │ uses
                ┌────────────────▼───────────────────────────┐
                │              KMP CORE                       │
                │  ┌──────────────────────────────────────┐  │
                │  │ 1. Vault Service (storage + index)   │  │
                │  ├──────────────────────────────────────┤  │
                │  │ 2. Learner Runtime (orchestrator)    │  │
                │  ├──────────────────────────────────────┤  │
                │  │ 3. AI Gateway (multi-LLM + BYOK)     │  │
                │  ├──────────────────────────────────────┤  │
                │  │ 4. MCP Hub (tool registry + server)  │  │
                │  ├──────────────────────────────────────┤  │
                │  │ 5. Licensing (Ed25519 offline)       │  │
                │  ├──────────────────────────────────────┤  │
                │  │ 6. CLI Framework (rich + click)      │  │
                │  └──────────────────────────────────────┘  │
                └─────────────────────────────────────────────┘
```

**Quy tắc dòng phụ thuộc:**
```
Vertical → Core      ✅ allowed
Core → Vertical      ❌ forbidden (sẽ enforce bằng import-linter)
Vertical → Vertical  ⚠️ chỉ qua Core API, không bao giờ direct import
```

---

## 3. Package Layout

```
knowledge_memory/                        # ← top-level package, neutral name
├── __init__.py                          # __version__
├── __main__.py                          # python -m knowledge_memory
│
├── core/                                # ★ KMP CORE (vertical-agnostic)
│   ├── __init__.py
│   │
│   ├── vault/                           # 1. Vault Service
│   │   ├── base.py                      #   - BaseVault (ABC)
│   │   ├── manager.py                   #   - VaultManager (file system + lock)
│   │   ├── index.py                     #   - SQLite + FTS5 wrapper
│   │   ├── snapshot.py                  #   - Snapshot rotation
│   │   └── schema.sql                   #   - Core schema (vertical extends)
│   │
│   ├── learners/                        # 2. Learner Runtime
│   │   ├── base.py                      #   - BaseLearner (ABC)
│   │   ├── runtime.py                   #   - LearnerRuntime (orchestrate)
│   │   ├── confidence.py                #   - ConfidenceCalculator
│   │   └── pattern.py                   #   - Pattern dataclass + serializer
│   │
│   ├── parsers/                         # Parser abstraction
│   │   ├── base.py                      #   - BaseParser (ABC)
│   │   ├── evidence.py                  #   - Evidence dataclass
│   │   └── corpus.py                    #   - Corpus iterator
│   │
│   ├── ai/                              # 3. AI Gateway
│   │   ├── providers/
│   │   │   ├── base.py                  #   - LLMProvider (ABC)
│   │   │   ├── anthropic.py
│   │   │   ├── openai.py
│   │   │   └── gemini.py
│   │   ├── client.py                    #   - factory + fallback
│   │   ├── rag.py                       #   - BM25 + graph proximity
│   │   ├── context_builder.py
│   │   └── cost.py                      #   - cost calculator per provider
│   │
│   ├── mcp/                             # 4. MCP Hub
│   │   ├── adapter.py                   #   - wrap Anthropic MCP SDK
│   │   ├── server.py                    #   - MCP server bootstrap
│   │   ├── registry.py                  #   - @register decorator
│   │   ├── tool_base.py                 #   - BaseMCPTool (ABC)
│   │   └── resource_base.py             #   - BaseMCPResource (ABC)
│   │
│   ├── licensing/                       # 5. Licensing
│   │   ├── verifier.py                  #   - Ed25519 verify
│   │   ├── public_key.py
│   │   ├── fingerprint.py
│   │   ├── storage.py
│   │   └── gate.py                      #   - feature gate decorator
│   │
│   ├── cli/                             # 6. CLI Framework
│   │   ├── base.py                      #   - BaseCLI (rich console)
│   │   ├── progress.py                  #   - shared progress bar
│   │   ├── theme.py                     #   - color scheme
│   │   └── formatter.py                 #   - output formatter
│   │
│   ├── telemetry/                       # 7. Local telemetry (privacy-safe)
│   │   ├── logger.py
│   │   └── roi.py
│   │
│   └── config/                          # 8. Config loader
│       ├── loader.py                    #   - YAML safe_load
│       └── schema.py                    #   - Pydantic config schema
│
├── verticals/                           # ★ VERTICAL PLUGINS
│   ├── __init__.py                      #   - vertical registry
│   │
│   ├── codebase/                        # ★ FIRST VERTICAL
│   │   ├── __init__.py                  #   - VERTICAL_NAME = "codebase"
│   │   ├── parsers/
│   │   │   ├── python_ast.py            #   - PythonASTParser(BaseParser)
│   │   │   └── ts_parser.py             #   - (later sprint)
│   │   ├── learners/
│   │   │   ├── naming.py                #   - NamingLearner(BaseLearner)
│   │   │   ├── layers.py
│   │   │   ├── git_ownership.py
│   │   │   ├── error_handling.py
│   │   │   ├── dependency_injection.py
│   │   │   └── test_patterns.py
│   │   ├── vault.py                     #   - CodebaseVault(BaseVault)
│   │   ├── mcp_tools.py                 #   - @register(...) tool plugins
│   │   ├── cli.py                       #   - codebase-memory CLI
│   │   └── schema_extension.sql         #   - extra tables (nodes, edges)
│   │
│   ├── hello/                           # ★ REFERENCE 50-line vertical
│   │   ├── __init__.py
│   │   ├── parsers.py                   #   - HelloParser (read .txt)
│   │   ├── learners.py                  #   - HelloLearner (count words)
│   │   └── cli.py                       #   - hello-memory CLI
│   │
│   └── (future)
│       ├── legal/
│       ├── sales/
│       └── research/
│
└── tools/                               # Dev tools
    ├── generate_license.py              # CEO sign license
    ├── lint_imports.py                  # check Core ↛ Vertical
    └── benchmark.py                     # perf regression
```

**Distribution wheel:**

```
knowledge-memory-core==1.0.0             # Core only, free, OSS
knowledge-memory-codebase==1.0.0         # Vertical Codebase, free + paid
knowledge-memory-legal==1.0.0            # Vertical Legal (future)
```

CLI binary alias:
- `knowledge-memory` → entrypoint chính
- `codebase-memory` → alias cho `knowledge-memory codebase`
- `legal-memory` → (future) alias cho `knowledge-memory legal`

---

## 4. Core Service Specifications

### 4.1 Vault Service

**Mục đích:** Quản lý storage local-first cho mọi vertical.

**Abstract base:**
```python
# core/vault/base.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

class BaseVault(ABC):
    """Mọi vertical vault kế thừa class này."""

    VERTICAL_NAME: str  # bắt buộc override

    @abstractmethod
    def init(self, root: Path, force: bool = False) -> None:
        """Tạo .knowledge-memory/<vertical>/ structure."""

    @abstractmethod
    def snapshot(self) -> "Snapshot":
        """Tạo snapshot mới của corpus."""

    @abstractmethod
    def get_corpus_iterator(self) -> Iterator["Evidence"]:
        """Yield evidence cho learners."""

    @abstractmethod
    def schema_extension_sql(self) -> str:
        """SQL bổ sung cho vertical (extra tables)."""

    # Concrete methods (Core cung cấp sẵn):
    def index_db_path(self) -> Path: ...
    def patterns_md_path(self) -> Path: ...
    def commit_pattern(self, pattern: "Pattern") -> None: ...
    def query_patterns(self, category: str = None) -> list["Pattern"]: ...
```

**Folder layout vault:**
```
.knowledge-memory/
├── config.yaml                          # llm provider, project metadata
├── core.db                              # core SQLite (patterns, _meta, telemetry)
├── verticals/
│   └── codebase/                        # mỗi vertical 1 thư mục con
│       ├── vault.db                     # vertical-specific data (nodes, edges)
│       ├── snapshots/
│       │   └── <timestamp>.json
│       ├── patterns.md                  # human-readable patterns
│       └── quick-wins.md                # bootstrap insights
└── .gitignore                           # bỏ qua *.lock, *.tmp
```

**SQLite core schema (vertical kế thừa thêm bảng riêng):**
```sql
-- core/vault/schema.sql
CREATE TABLE IF NOT EXISTS _meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS patterns (
    id INTEGER PRIMARY KEY,
    vertical TEXT NOT NULL,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_patterns_vertical ON patterns(vertical, category);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY,
    vertical TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    file_path TEXT NOT NULL,
    summary_json TEXT
);

CREATE TABLE IF NOT EXISTS usage_log (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    vertical TEXT NOT NULL,
    command TEXT NOT NULL,
    duration_ms INTEGER,
    tokens_used INTEGER,
    success BOOLEAN
);
```

### 4.2 Learner Runtime

**Mục đích:** Orchestrate việc chạy learner song song, gom evidence, tính confidence, commit pattern.

**Abstract base:**
```python
# core/learners/base.py
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

E = TypeVar("E", bound="Evidence")
C = TypeVar("C", bound="Cluster")

class BaseLearner(ABC, Generic[E, C]):
    LEARNER_NAME: str
    LEARNER_CATEGORY: str
    MIN_EVIDENCE_COUNT: int = 5
    MIN_CONFIDENCE: float = 60.0  # %

    @abstractmethod
    def extract_evidence(self, vault: "BaseVault") -> list[E]:
        """Trích evidence từ vault."""

    @abstractmethod
    def cluster(self, evidences: list[E]) -> list[C]:
        """Group evidence thành cluster."""

    @abstractmethod
    def calculate_confidence(self, cluster: C) -> float:
        """Tính confidence 0-100."""

    @abstractmethod
    def cluster_to_pattern(self, cluster: C) -> "Pattern":
        """Convert cluster sang Pattern object."""
```

**Runtime orchestrator:**
```python
# core/learners/runtime.py
class LearnerRuntime:
    def __init__(self, vault: BaseVault, learners: list[BaseLearner]):
        self.vault = vault
        self.learners = learners

    def run_all(self, parallel: bool = True) -> list[Pattern]:
        """Chạy mọi learner, gom pattern qua confidence threshold."""
        results = []
        for learner in self.learners:
            evidence = learner.extract_evidence(self.vault)
            if len(evidence) < learner.MIN_EVIDENCE_COUNT:
                continue
            clusters = learner.cluster(evidence)
            for cluster in clusters:
                conf = learner.calculate_confidence(cluster)
                if conf >= learner.MIN_CONFIDENCE:
                    pattern = learner.cluster_to_pattern(cluster)
                    pattern.confidence = conf
                    results.append(pattern)
                    self.vault.commit_pattern(pattern)
        return results
```

### 4.3 AI Gateway

**Mục đích:** Multi-LLM provider, BYOK, cost tracking, fallback.

**Provider abstraction:**
```python
# core/ai/providers/base.py
class LLMProvider(ABC):
    PROVIDER_NAME: str

    @abstractmethod
    def chat(self, messages: list[dict], **kwargs) -> "ChatResponse": ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float: ...

    def supports(self, feature: str) -> bool:
        """E.g. 'streaming', 'tools', 'vision'."""
        return False
```

**Factory:**
```python
# core/ai/client.py
def get_provider(config: dict) -> LLMProvider:
    name = config["llm"]["provider"]
    return {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }[name](config["llm"])
```

### 4.4 MCP Hub

**Mục đích:** Cho phép vertical đăng ký tool/resource qua decorator, server tự discover.

**Registry pattern:**
```python
# core/mcp/registry.py
TOOLS: dict[str, "BaseMCPTool"] = {}
RESOURCES: dict[str, "BaseMCPResource"] = {}

def register_tool(name: str):
    def deco(cls):
        TOOLS[name] = cls()
        return cls
    return deco

def register_resource(uri: str):
    def deco(cls):
        RESOURCES[uri] = cls()
        return cls
    return deco
```

**Vertical sử dụng:**
```python
# verticals/codebase/mcp_tools.py
from knowledge_memory.core.mcp.registry import register_tool
from knowledge_memory.core.mcp.tool_base import BaseMCPTool

@register_tool("find_function")
class FindFunctionTool(BaseMCPTool):
    description = "Find a Python function by name in the codebase vault"

    def execute(self, name: str) -> dict:
        ...
```

**Server bootstrap:**
```python
# core/mcp/server.py
def start_server(verticals: list[str]):
    # Import vertical packages → triggers @register_tool decorators
    for v in verticals:
        importlib.import_module(f"knowledge_memory.verticals.{v}.mcp_tools")
    # Server now serves all registered tools
    server = MCPServer(tools=TOOLS, resources=RESOURCES)
    server.run()
```

### 4.5 Licensing

**Mục đích:** Verify Ed25519 signed license offline, gate Pro feature.

**Feature gate decorator:**
```python
# core/licensing/gate.py
def require_license(feature: str):
    def deco(fn):
        def wrapper(*args, **kwargs):
            if not LicenseStorage().has_feature(feature):
                raise LicenseRequiredError(feature)
            return fn(*args, **kwargs)
        return wrapper
    return deco

# Sử dụng trong vertical
@require_license("codebase.drift")
def run_drift_scan(...):
    ...
```

### 4.6 CLI Framework

**Base CLI cho mọi vertical:**
```python
# core/cli/base.py
class BaseCLI:
    VERTICAL_NAME: str

    def cmd_init(self, force: bool = False): ...
    def cmd_bootstrap(self): ...   # Quick Win Mode
    def cmd_ask(self, question: str): ...
    def cmd_insights(self, period: str = "weekly"): ...
```

Vertical override `cmd_bootstrap` để chạy parser + learner riêng.

---

## 5. Extension Contract — How to Build a Vertical

Để build 1 vertical mới (Legal, Sales, …), developer chỉ cần làm 6 việc:

| Bước | File cần tạo | LOC ước tính |
|------|-------------|:-----------:|
| 1 | `verticals/<name>/__init__.py` (set `VERTICAL_NAME`) | 5 |
| 2 | `verticals/<name>/parsers/<corpus>.py` kế thừa `BaseParser` | 100-300 |
| 3 | `verticals/<name>/learners/*.py` ≥ 3 learners kế thừa `BaseLearner` | 150-500 |
| 4 | `verticals/<name>/vault.py` kế thừa `BaseVault` | 50-100 |
| 5 | `verticals/<name>/mcp_tools.py` ≥ 3 tool dùng `@register_tool` | 100-200 |
| 6 | `verticals/<name>/cli.py` kế thừa `BaseCLI` | 50-100 |

**Tổng:** ~500-1200 LOC cho 1 vertical mới (so với 5000+ LOC nếu build từ 0).

### Reference vertical "Hello" — proof of concept

```python
# verticals/hello/__init__.py
VERTICAL_NAME = "hello"

# verticals/hello/parsers.py
from knowledge_memory.core.parsers.base import BaseParser, Evidence

class HelloParser(BaseParser):
    def parse(self, vault):
        for txt in vault.root.glob("*.txt"):
            for line in txt.read_text().splitlines():
                yield Evidence(source=str(txt), data={"text": line})

# verticals/hello/learners.py
from knowledge_memory.core.learners.base import BaseLearner

class WordCountLearner(BaseLearner):
    LEARNER_NAME = "word_count"
    LEARNER_CATEGORY = "stats"

    def extract_evidence(self, vault):
        return list(HelloParser().parse(vault))

    def cluster(self, evidences):
        words = {}
        for e in evidences:
            for w in e.data["text"].split():
                words.setdefault(w, []).append(e)
        return [{"word": w, "evidences": es} for w, es in words.items() if len(es) >= 5]

    def calculate_confidence(self, cluster):
        return min(100.0, len(cluster["evidences"]) * 10)

    def cluster_to_pattern(self, cluster):
        from knowledge_memory.core.learners.pattern import Pattern
        return Pattern(
            name=f"frequent_word::{cluster['word']}",
            category="stats",
            confidence=0,  # set by runtime
            evidence=cluster["evidences"][:20],
        )
```

Nếu **HelloVertical** chạy được trong 50 dòng → abstraction OK. Đây là acceptance test cho M0.

---

## 6. Dependency Rule Enforcement

Em (CTO) sẽ enforce qua **import-linter** trong CI:

```ini
# .importlinter
[importlinter]
root_package = knowledge_memory

[importlinter:contract:core-purity]
name = Core never imports vertical
type = forbidden
source_modules =
    knowledge_memory.core
forbidden_modules =
    knowledge_memory.verticals
```

CI fail nếu commit nào vi phạm. Đây là **moat kỹ thuật** quan trọng nhất của KMP — bảo vệ Core khỏi bị nhiễm vertical-specific code.

---

## 7. Migration Strategy — From Codebase Map v1.1

| Component cũ (codebase_map) | Component mới (knowledge_memory) | Effort |
|----------------------------|---------------------------------|:------:|
| `parsers/python_parser.py` | `verticals/codebase/parsers/python_ast.py` | Move + adapt BaseParser |
| `graph/models.py` | `verticals/codebase/models.py` | Move |
| `graph/builder.py` | `verticals/codebase/builder.py` | Move |
| `exporters/html_exporter.py` | `verticals/codebase/exporters/html.py` | Move |
| `licensing/*` | `core/licensing/*` | Move (đã có sẵn) |
| `cli.py` | `core/cli/base.py` + `verticals/codebase/cli.py` | Split |

**Estimate refactor:** ~25 SP / 1.5 tuần. Nhưng vì Codebase Memory M0 chưa start, ta **không refactor codebase_map** — ta build knowledge_memory mới và codebase_map vẫn tồn tại như tool standalone (free, OSS, không thay đổi).

Long-term sau v1.0 KMP launch, codebase_map sẽ deprecated, redirect users sang `knowledge-memory codebase`.

---

## 8. Sprint M0 — Core Skeleton (1 tuần, 6 SP)

| Task | SP | Owner | Acceptance |
|------|:--:|------|------------|
| KMP-M0-01: Tạo package `knowledge_memory/core/` skeleton (mọi `__init__.py`, abstract base files rỗng) | 1 | TechLead | `python -c "import knowledge_memory.core"` pass |
| KMP-M0-02: Implement `BaseVault`, `BaseLearner`, `BaseParser`, `Pattern`, `Evidence` dataclass | 2 | TechLead | Type-check pass với mypy |
| KMP-M0-03: Implement `core/learners/runtime.py` orchestrator | 1 | TechLead | Unit test với mock learner pass |
| KMP-M0-04: Setup import-linter CI rule (Core ↛ Vertical) | 0.5 | TechLead | CI fail khi cố ý vi phạm |
| KMP-M0-05: Build `verticals/hello/` reference (≤ 50 LOC) + `verticals/hello/README.md` *(CEO req #3)* | 1 | TechLead | Hello vertical chạy end-to-end, sinh patterns.md; README ≤ 5 phút đọc |
| KMP-M0-06: CTO architecture review + sign-off | 0.5 | CTO | Review ≤ 1 ngày |
| **KMP-M0-07** *(CEO add)*: Viết `docs/vault-format-spec.md` (≤ 5 trang) — public spec cho vault format | 1 | CTO | Đủ để dev ngoài tự build vault tương thích |
| **KMP-M0-08** *(CEO add)*: Add `LICENSE` (MIT) root + template `LICENSE-PRO` + CI lint check 2 file tồn tại | 0.5 | TechLead | CI fail nếu thiếu LICENSE |

**Total M0:** **8 SP / 1 tuần** *(updated từ 6 SP — CEO bổ sung KMP-M0-07 và KMP-M0-08 ngày 08/04/2026)*

---

## 9.bis CEO Sign-off (08/04/2026)

**CEO Đoàn Đình Tỉnh đã APPROVE toàn bộ tài liệu này.**

**5/5 Open Decisions duyệt:**

| ID | Decision | CEO duyệt |
|----|---------|-----------|
| D-1 | Tên package top-level | ✅ `knowledge_memory` (rõ nghĩa, SEO tốt) |
| D-2 | Monorepo vs Multi-repo | ✅ Monorepo (team nhỏ, dễ refactor cross-package) |
| D-3 | License Core | ✅ MIT cho Core + Proprietary cho Pro feature |
| D-4 | Open source vault format spec | ✅ Yes — moat "open vault, closed engine" |
| D-5 | Hello vertical ship cùng v1.0 | ✅ Ship cùng v1.0 — living documentation |

**3 yêu cầu bổ sung từ CEO (đã merge vào M0):**

1. **D-4 → KMP-M0-07:** CTO viết `docs/vault-format-spec.md` ngay trong M0 (không để sau) — tài liệu marketing kỹ thuật thu hút dev OSS.
2. **D-3 → KMP-M0-08:** Add `LICENSE` (MIT) root + `LICENSE-PRO` template + CI lint check 2 file phải tồn tại.
3. **D-5 → KMP-M0-05 update:** `verticals/hello/README.md` ngắn — dev mới đọc 5 phút là copy folder build vertical riêng.

**Quyết định kèm theo:** CTO được phép kickoff Sprint M0 NGAY (1 tuần, 8 SP, deadline 15/04/2026).

**Sign-off:**
- ✅ **CEO** Đoàn Đình Tỉnh — 08/04/2026
- ✅ **CTO** — 07/04/2026 (author)
- ✅ **PO/BA** — co-reviewed

---

---

## 9. Open Decisions cần CEO xác nhận

| ID | Decision | Đề xuất CTO |
|----|---------|-------------|
| D-1 | Tên package top-level: `knowledge_memory` hay `kmp`? | `knowledge_memory` (rõ nghĩa) |
| D-2 | Distribute monorepo hay multi-repo? | Monorepo (1 repo, multi-package wheel) |
| D-3 | License KMP Core: MIT hay AGPL? | **MIT** cho Core (kéo cộng đồng), proprietary cho vertical Pro features |
| D-4 | Open source vault format spec? | **Yes**, publish ở `docs/vault-format-spec.md` |
| D-5 | Hello vertical ship cùng v1.0 hay tách riêng? | Ship cùng v1.0 như tutorial cho dev |

---

## 10. Glossary

| Thuật ngữ | Ý nghĩa |
|----------|---------|
| **KMP** | Knowledge Memory Platform — nền tảng lõi |
| **Core** | Mọi thứ trong `knowledge_memory/core/`, không vertical-specific |
| **Vertical** | Plugin trong `knowledge_memory/verticals/`, build cho 1 domain cụ thể |
| **Vault** | Folder `.knowledge-memory/` chứa storage local của 1 project |
| **Pattern** | Quy luật lặp lại được learner phát hiện, có confidence score |
| **Evidence** | Đơn vị dữ liệu thô từ corpus mà learner dùng để tính pattern |
| **MCP** | Model Context Protocol — giao thức Anthropic chuẩn cho tool |
| **BYOK** | Bring Your Own Key — user tự cung cấp API key LLM |

---

*KMP Architecture v1.0 — 07/04/2026 — by @CTO*
*Co-reviewed: @PO @BA @TechLead*
