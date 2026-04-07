# Codebase Map — Customer Onboarding (1-pager)

> **Standalone function dependency graph generator.** Plug into bất kỳ Python/TypeScript project nào qua YAML config. Output: interactive HTML + JSON. **100% offline · zero CDN.**

---

## 1. Install (30 giây)

```bash
pip install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
```

Yêu cầu: Python 3.10+. Không cần Node, không cần build step.

---

## 2. Config — `codebase-map.yaml`

Đặt file này ở root project:

```yaml
project: my-app

sources:
  - path: ./backend
    language: python
    base_module: app
    exclude: ["__pycache__", ".venv", "migrations", "tests"]

  - path: ./frontend/src
    language: typescript
    exclude: ["node_modules", "dist", "*.spec.ts"]

output:
  dir: docs/function-map
  formats: [json, html]

graph:
  depth: 3
  group_by: module

# Optional: business flow tagging
flows:
  checkout: ["CheckoutService.*", "PaymentGateway.charge", "OrderRepository.create"]
  signup:   ["AuthService.register", "UserRepository.create", "EmailService.welcome"]
```

---

## 3. CLI — 6 commands

| Command | Purpose | Example |
|---------|---------|---------|
| `generate` | Build the map (JSON + HTML) | `codebase-map generate -c codebase-map.yaml` |
| `summary` | Stats by type/layer/domain | `codebase-map summary -f docs/function-map/graph.json` |
| `query` | Show deps + impact for a node | `codebase-map query "CheckoutService" -f graph.json` |
| `impact` | List 2-hop impact zone | `codebase-map impact "PaymentGateway.charge" -f graph.json` |
| `search` | Find functions/classes by name | `codebase-map search "pipeline" -f graph.json` |
| `diff` | Compare against git ref | `codebase-map diff main -f graph.json` |

### Generating PR Diff data for the HTML view
```bash
codebase-map diff main -f docs/function-map/graph.json --json > docs/function-map/pr_diff.json
codebase-map generate -c codebase-map.yaml   # bakes pr_diff.json into HTML
```

---

## 4. View the HTML

```bash
open docs/function-map/index.html              # macOS
xdg-open docs/function-map/index.html          # Linux
start docs/function-map/index.html             # Windows
```

Hoặc serve qua local server:
```bash
python3 -m http.server 8765 --directory docs/function-map
# rồi mở http://localhost:8765
```

### 4 view tabs (top bar)
| Tab | Persona | URL hash |
|-----|---------|----------|
| 🗺️ **Graph** | Developer | `#view=graph` |
| 📊 **Executive** | CEO / PM | `#view=executive` |
| 🔌 **API Catalog** | Product / FE | `#view=api` |
| 🔀 **PR Diff** | Reviewer | `#view=diff` |

### Keyboard shortcuts
- `1` `2` `3` `4` — switch tab
- `Backspace` — breadcrumb up 1 level
- `Esc` — close mobile drawer / detail panel

### Mobile / Tablet
Tự responsive. Mobile (<768px): hamburger drawer. Tablet (<1024px): sidebar collapse. Desktop: full layout.

---

## 5. CI integration (GitHub Actions example)

```yaml
- name: Generate codebase map
  run: |
    pip install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
    codebase-map generate -c codebase-map.yaml
    codebase-map diff origin/main -f docs/function-map/graph.json --json \
      > docs/function-map/pr_diff.json
    codebase-map generate -c codebase-map.yaml   # re-bake with diff
- uses: actions/upload-artifact@v4
  with:
    name: codebase-map
    path: docs/function-map/
```

---

## 6. Annotate code (optional)

```python
# FDD: FDD-CRM-001
def create_customer(...):
    """Service layer for customer onboarding."""

# flow: signup, crm-sync
class CustomerService:
    ...
```

These appear in **Detail Panel ⑤ Metadata** + **Flow filter chips**.

---

## 7. Need help?

- **Repo:** https://github.com/hypercommerce-vn/codebase-map
- **Issues:** https://github.com/hypercommerce-vn/codebase-map/issues
- **Release notes:** https://github.com/hypercommerce-vn/codebase-map/releases/tag/v2.0.0

---

*Codebase Map v2.0 · Hyper Commerce · 2026*
