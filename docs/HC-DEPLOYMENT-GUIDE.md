# Hyper Commerce — CBM & KMP Deployment Guide

> **For:** CEO Đoàn Đình Tỉnh
> **Date:** 14/04/2026
> **Version:** CBM v2.2 + KMP v1.0
> **Project:** Hyper Commerce (HC)

---

## Quick Start (5 phút)

```bash
# 1. Install codebase-map (CBM)
cd /path/to/HyperCommerce
pipx install "git+ssh://git@github.com/hypercommerce-vn/codebase-map.git"

# 2. Generate function graph
codebase-map generate -c codebase-map.yaml

# 3. Install KMP (cùng repo)
pip install -e "/path/to/codebase-map[dev]"

# 4. Init vault
codebase-memory init

# 5. Bootstrap — learn patterns
codebase-memory bootstrap

# 6. Ask a question
export ANTHROPIC_API_KEY="sk-ant-..."
codebase-memory ask "How is customer authentication handled?"
```

---

## Phần 1: Codebase Map (CBM) trên HC

### 1.1 Config file

Tạo `codebase-map.yaml` tại HC repo root:

```yaml
# HC-AI | Codebase Map config for Hyper Commerce
project: "hypercommerce"
sources:
  - path: "app"
    language: python
    base_module: "app"
    exclude:
      - "__pycache__"
      - "migrations"
      - "*.pyc"
  - path: "workers"
    language: python
    base_module: "workers"
output:
  dir: "docs/function-map"
  formats: [json, html]
graph:
  depth: 3
  group_by: module
```

### 1.2 Generate graph

```bash
# Full generate (JSON + interactive HTML)
codebase-map generate -c codebase-map.yaml

# Verify output
codebase-map summary -f docs/function-map/graph.json
# Expected: ~1,386 nodes · ~8,285 edges · 7 domains
```

### 1.3 Dual-Snapshot Diff (v2.2)

```bash
# Create baseline snapshot
codebase-map generate -c codebase-map.yaml --label "baseline"

# ... make code changes ...

# Create post-dev snapshot
codebase-map generate -c codebase-map.yaml --label "post-dev"

# Compare
codebase-map snapshot-diff \
  --baseline baseline \
  --current post-dev \
  --format markdown \
  -c codebase-map.yaml
```

### 1.4 CI Integration (đã có sẵn)

HC repo đã có 4 workflows:
- `ci.yml` — lint + test + generate + notify
- `cbm-baseline.yml` — auto-generate baseline on push to main
- `cbm-post-merge.yml` — rotate baseline after PR merge
- `cbm-pr-impact.yml` — auto-post Impact Analysis vào PR comment

> **Không cần config thêm.** CI tự chạy khi push/PR.

---

## Phần 2: Knowledge Memory Platform (KMP) trên HC

### 2.1 Init vault

```bash
cd /path/to/HyperCommerce
codebase-memory init
```

Output:
```
✓ Created .knowledge-memory/
✓ Created .knowledge-memory/core.db
✓ Created .knowledge-memory/config.yaml
✓ Registered vertical: codebase
✓ Added .knowledge-memory/ to .gitignore
```

### 2.2 Configure LLM provider

Edit `.knowledge-memory/config.yaml`:

```yaml
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  api_key_env: "ANTHROPIC_API_KEY"
  max_tokens: 1024
  temperature: 0.3

  # Fallback (optional)
  fallback:
    provider: "openai"
    model: "gpt-4o-mini"
    api_key_env: "OPENAI_API_KEY"

rag:
  max_chunks: 5
  bm25_weight: 0.6
  graph_weight: 0.4
  min_score: 0.3
```

Set API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
# Optional fallback:
export OPENAI_API_KEY="sk-..."
```

### 2.3 Bootstrap (first time)

```bash
codebase-memory bootstrap
```

Expected output:
```
[1/5] Parse      120/120 files  2.3s
[2/5] Snapshot    ✓ saved       0.4s
[3/5] Learn       6 learners
  ▶ NamingLearner          done  12 patterns
  ▶ LayerLearner           done  8 patterns
  ▶ GitOwnershipLearner    done  5 patterns
  ▶ ErrorHandlingLearner   done  6 patterns
  ▶ DependencyInjLearner   done  4 patterns
  ▶ TestPatternsLearner    done  3 patterns
[4/5] Commit      38 patterns committed
[5/5] Quick Wins  10 insights generated

✓ Bootstrap complete!  Total: 5.7s
```

### 2.4 Daily commands

#### Hỏi về codebase
```bash
codebase-memory ask "How is customer authentication handled?"
codebase-memory ask "What is the billing flow for subscription renewal?"
codebase-memory ask "Which services handle inventory management?"
```

#### Hiểu dependency
```bash
codebase-memory why "OrderService calls BillingService"
codebase-memory why "CustomerService calls AuthService"
```

#### Phân tích impact trước khi sửa code
```bash
codebase-memory impact "auth/service.py:authenticate"
codebase-memory impact "order/service.py:submit_order" --depth 2
```

#### Kiểm tra chi phí LLM
```bash
codebase-memory usage
codebase-memory roi
```

### 2.5 Onboarding new developer

```bash
# Generate personalized onboarding guide
codebase-memory onboard

# View glossary
codebase-memory glossary

# Export insights dashboard
codebase-memory insights --html
```

Share `onboarding-report.md` với developer mới.
Open `insights.html` trong browser.

### 2.6 MCP Server cho Claude Code

Thêm vào `.claude/settings.json` (hoặc MCP config):

```json
{
  "mcpServers": {
    "knowledge-memory": {
      "command": "python",
      "args": ["-m", "knowledge_memory.core.mcp.server"],
      "cwd": "/path/to/HyperCommerce"
    }
  }
}
```

Claude Code sẽ có 4 tools:
- `find_function` — tìm function theo tên
- `explain_module` — giải thích module
- `pattern_check` — kiểm tra convention
- `impact` — phân tích ảnh hưởng

### 2.7 User Hints

Bất kỳ lúc nào cần hướng dẫn:

```python
from knowledge_memory.core.hints import get_hint, format_hint

hint = get_hint("ask")
print(format_hint(hint))
```

Hoặc xem toàn bộ:
```python
from knowledge_memory.core.hints import format_all_hints_summary
print(format_all_hints_summary())
```

---

## Phần 3: Quy trình hàng ngày

### 3.1 Developer workflow

```
Morning:
  1. git pull origin develop
  2. codebase-memory bootstrap          # refresh patterns
  3. codebase-memory ask "What changed?" # quick context

During development:
  4. codebase-memory impact "function"   # before modifying
  5. codebase-memory why "A calls B"     # understand deps

Before PR:
  6. codebase-map generate --label "post-dev"
  7. codebase-map snapshot-diff --baseline baseline --current post-dev --format markdown
  8. Copy impact block vào PR body

Weekly:
  9. codebase-memory insights --html     # team dashboard
  10. codebase-memory roi                 # track value
```

### 3.2 New developer onboarding (Day 1)

```bash
# Step 1: Clone + install
git clone git@github.com:hypercommerce-vn/HyperCommerce.git
cd HyperCommerce
pip install -r requirements.txt

# Step 2: Setup KMP
codebase-memory init
codebase-memory bootstrap

# Step 3: Read onboarding guide
codebase-memory onboard
# Open onboarding-report.md in VSCode

# Step 4: Explore
codebase-memory ask "What are the main domains?"
codebase-memory glossary
codebase-memory ask "How is auth handled?"

# Step 5: Setup AI agent
# Configure MCP server in Claude Code / Cursor
```

### 3.3 Code review workflow

```bash
# Reviewer checks impact
codebase-memory impact "changed_function" --depth 2

# Reviewer checks convention compliance
# (via MCP tool in Claude Code)
# Claude calls: pattern_check("new_function_name")

# Reviewer checks structural changes
codebase-map snapshot-diff --baseline main --current feature-branch --format text
```

---

## Phần 4: Troubleshooting

| Problem | Solution |
|---------|----------|
| `codebase-map: command not found` | `pipx install "git+ssh://..."` hoặc `pip install -e .` |
| `Vault not initialized` | Run `codebase-memory init` |
| `No LLM provider configured` | Set `llm.provider` in config.yaml + export API key |
| `0 patterns after bootstrap` | Check scan scope in config.yaml, ensure Python files exist |
| `Rate limit exceeded` | Configure fallback provider in config.yaml |
| `bootstrap > 10 min` | Narrow scan scope, exclude test files or migrations |
| `MCP connection refused` | Check stdio transport config in AI tool settings |
| `snapshot-diff: baseline not found` | Run `codebase-map snapshots list` to see available labels |

---

## Phần 5: Quick Reference

### CBM Commands

| Command | Description |
|---------|-------------|
| `codebase-map generate -c config.yaml` | Generate graph |
| `codebase-map generate --label "name"` | Generate with snapshot label |
| `codebase-map summary -f graph.json` | Graph statistics |
| `codebase-map query "function" -f graph.json` | Query function details |
| `codebase-map impact "Class" -f graph.json` | Impact analysis |
| `codebase-map search "keyword" -f graph.json` | Search functions |
| `codebase-map snapshot-diff --baseline A --current B` | Compare snapshots |
| `codebase-map snapshots list` | List saved snapshots |

### KMP Commands

| Command | Description |
|---------|-------------|
| `codebase-memory init` | Initialize vault |
| `codebase-memory bootstrap` | Scan + learn patterns |
| `codebase-memory bootstrap --resume` | Resume after Ctrl+C |
| `codebase-memory summary` | Vault status |
| `codebase-memory ask "question"` | AI Q&A |
| `codebase-memory why "A calls B"` | Explain dependency |
| `codebase-memory impact "function"` | Change impact |
| `codebase-memory impact "func" --depth 3` | Deep impact |
| `codebase-memory onboard` | Generate onboarding guide |
| `codebase-memory glossary` | Domain vocabulary |
| `codebase-memory insights --html` | Export dashboard |
| `codebase-memory roi` | ROI metrics |
| `codebase-memory usage` | LLM cost tracking |
| `codebase-memory mcp serve` | Start MCP server |

---

*HC Deployment Guide v1.0 · 14/04/2026 · CBM v2.2 + KMP v1.0*
*Author: PM Agent · Reviewed: CTO Agent*
