# Codebase Map — Customer Onboarding (1-pager)

> **Standalone function dependency graph generator.** Plug into bất kỳ Python/TypeScript project nào qua YAML config. Output: interactive HTML + JSON. **100% offline · zero CDN.**

---

## 1. Install (30 giây)

**Yêu cầu:** Python **3.10+**. Không cần Node, không cần build step.

### 🥇 Cách 1 — `pipx` (khuyến nghị, sạch nhất cho CLI tool)

`pipx` cài mỗi tool vào venv riêng + tự symlink command vào PATH. Không pollute system Python, không bị PEP 668 chặn.

```bash
brew install pipx
pipx ensurepath
# Mở terminal mới (hoặc: source ~/.zshrc)

pipx install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
codebase-map --help
```

### Cách 2 — venv riêng cho từng project

```bash
cd /path/to/your-project
python3.12 -m venv .venv-codemap
source .venv-codemap/bin/activate
pip install --upgrade pip
pip install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
codebase-map --help
```

> Mỗi lần dùng phải `source .venv-codemap/bin/activate` trước.

### Cách 3 — `pip install` thẳng (chỉ khi không có pipx, KHÔNG khuyến nghị)

```bash
python3 -m pip install --upgrade pip
python3 -m pip install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
```

> Trên macOS Python từ Homebrew, lệnh này có thể bị PEP 668 chặn — chuyển sang Cách 1.

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

## 7. Worked example — Hyper Commerce (HC) project

End-to-end 8 bước để dùng Codebase Map cho HC repo.

### Bước 1 — Cài đặt (1 lần)
```bash
brew install pipx && pipx ensurepath
pipx install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
codebase-map --help
```

### Bước 2 — Tạo `codebase-map.yaml` ở root HC repo
```yaml
project: hyper-commerce

sources:
  - path: ./backend
    language: python
    base_module: app
    exclude: ["__pycache__", ".venv", "migrations", "tests", "scripts"]

  - path: ./frontend/src
    language: typescript
    exclude: ["node_modules", "dist", "*.spec.ts", "*.test.tsx"]

output:
  dir: docs/function-map
  formats: [json, html]

graph:
  depth: 3
  group_by: module

# Optional — business flow tagging cho HC
flows:
  signup:    ["AuthService.register", "UserRepository.create"]
  checkout:  ["CheckoutService.*", "PaymentGateway.charge", "OrderRepository.create"]
  bulk_tag:  ["CustomerService.bulk_tag", "BulkTagSchema.*"]
  campaign:  ["CampaignService.*", "EmailWorker.send"]
  cdp_sync:  ["CDPSegment.*", "PipelineService.on_update"]
```

### Bước 3 — Build map lần đầu
```bash
cd ~/Projects/HyperCommerce
codebase-map generate -c codebase-map.yaml
```

Lần đầu ~150–300 ms. Lần sau **<20 ms** nhờ cache.

### Bước 4 — Mở HTML
```bash
open docs/function-map/index.html
```

4 tab top bar — chọn theo persona:

| Tab | Persona | Use case |
|-----|---------|----------|
| 🗺️ Graph | Developer | Debug, tìm dependency |
| 📊 Executive | CEO/PM | Health của 7 domains (CRM, CDP, Ecommerce, …) |
| 🔌 API Catalog | Product/FE | Xem 187+ FastAPI routes group theo domain |
| 🔀 PR Diff | Reviewer | Review tác động PR |

> 💡 CEO mở thẳng tab Executive: thêm `#view=executive` cuối URL.

### Bước 5 — CLI ad-hoc cho HC
```bash
# Tổng quan stats
codebase-map summary -f docs/function-map/graph.json

# "Ai gọi CustomerService.bulk_tag?"
codebase-map query "CustomerService.bulk_tag" -f docs/function-map/graph.json

# "Sửa PaymentGateway.charge ảnh hưởng đến bao nhiêu module?"
codebase-map impact "PaymentGateway.charge" -f docs/function-map/graph.json

# "Tìm hàm liên quan đến pipeline"
codebase-map search "pipeline" -f docs/function-map/graph.json
```

### Bước 6 — Review PR (workflow hằng ngày)
```bash
git fetch origin && git checkout <PR-branch>

codebase-map diff main -f docs/function-map/graph.json --json \
  > docs/function-map/pr_diff.json
codebase-map generate -c codebase-map.yaml   # re-build để bake diff
open docs/function-map/index.html
```

→ Tab **PR Diff** hiện risk banner 🟢/🟡/🔴 + 4 sections (Added/Modified/Removed/Impacted). Click chip → jump sang Graph view.

### Bước 7 — Tích hợp CI HC
Thêm vào `.github/workflows/codemap.yml`:
```yaml
name: Codebase Map
on:
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
      - name: Generate map + diff
        run: |
          codebase-map generate -c codebase-map.yaml
          codebase-map diff origin/main -f docs/function-map/graph.json --json \
            > docs/function-map/pr_diff.json
          codebase-map generate -c codebase-map.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: codebase-map
          path: docs/function-map/
```

### Bước 8 — Annotate code HC (optional, team thực hiện)
```python
# FDD: FDD-CRM-001
# flow: signup, crm-sync
class CustomerService:
    def create(...):
        ...
```

→ Detail Panel ⑤ Metadata hiện FDD link + flow chip.

### 🎯 Cheat-sheet 4 use case CEO hay dùng

| Tình huống | Lệnh / Tab |
|---|---|
| "CRM domain có healthy không?" | Open HTML → tab **Executive** → CRM card |
| "PR này risky không?" | Bước 6 → tab **PR Diff** → check banner color |
| "Sửa hàm X ảnh hưởng đâu?" | `codebase-map impact "X" -f graph.json` |
| "Có function nào tên giống pipeline?" | `codebase-map search "pipeline" -f graph.json` |

---

## 8. Troubleshooting — Gỡ rối lỗi cài đặt thường gặp

### ❌ `Successfully installed UNKNOWN-0.0.0` + `command not found: codebase-map`
**Nguyên nhân:** pip cũ (≤21.x) không đọc được `pyproject.toml` PEP 621 → cài thành package "UNKNOWN" rỗng.

**Fix:**
```bash
python3 -m pip uninstall -y UNKNOWN
python3 -m pip install --upgrade pip   # hoặc dùng pipx (Cách 1 trên)
pipx install git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
```

### ❌ `zsh: command not found: pip`
**Nguyên nhân:** macOS chỉ có `pip3`, không có alias `pip`.

**Fix:** dùng `python3 -m pip ...` hoặc `pip3 ...` thay cho `pip`.

### ❌ `ERROR: Package 'codebase-map' requires a different Python: 3.9.6 not in '>=3.10'`
**Nguyên nhân:** Python hệ thống Mac (Command Line Tools) là 3.9, codebase-map yêu cầu 3.10+.

**Fix:**
```bash
brew install python@3.12          # hoặc python@3.11
brew install pipx && pipx ensurepath
pipx install --python python3.12 git+https://github.com/hypercommerce-vn/codebase-map.git@v2.0.0
```

> Cài Python 3.12 song song **không ảnh hưởng** Python 3.9 hệ thống — Homebrew để ở `/opt/homebrew/bin/python3.12`. Project cũ vẫn dùng `python3` = 3.9 như cũ.

### ❌ `error: externally-managed-environment` (PEP 668)
**Nguyên nhân:** Python từ Homebrew/Linux distro chặn `pip install` thẳng vào system Python để tránh xung đột với package manager.

**Fix:** dùng `pipx` (Cách 1) — đó là use case chính của pipx.

### ❌ `codebase-map: command not found` sau khi pipx install
**Nguyên nhân:** PATH chưa có thư mục bin của pipx.

**Fix:**
```bash
pipx ensurepath
# Mở terminal mới HOẶC chạy:
source ~/.zshrc      # zsh (macOS mặc định)
source ~/.bashrc     # bash
```

### ❌ Build chậm hoặc OOM trên repo lớn
**Fix:** Giảm scope trong `codebase-map.yaml`:
```yaml
sources:
  - path: ./backend/app          # thay vì ./backend
    exclude: ["tests", "scripts", "alembic", "*.bak.py"]
graph:
  depth: 2                       # giảm từ 3
```

### ❌ HTML mở thấy trống / không có graph
**Nguyên nhân:** `graph.json` rỗng (config sai path hoặc exclude quá rộng).

**Fix:**
```bash
codebase-map summary -f docs/function-map/graph.json
# Nếu thấy "0 nodes" → check sources.path trong yaml
```

### ❌ PR Diff tab hiện "No pr_diff.json found"
**Bình thường** — phải bake diff trước:
```bash
codebase-map diff main -f docs/function-map/graph.json --json \
  > docs/function-map/pr_diff.json
codebase-map generate -c codebase-map.yaml
```

### ❌ TypeScript parser miss functions
**Nguyên nhân:** TS parser dùng regex (zero-deps), một số pattern phức tạp (template literals, JSX inline) có thể miss.

**Fix:** Mở issue trên GitHub kèm code snippet → sẽ fix trong hotfix sprint.

---

## 9. Need help?

- **Repo:** https://github.com/hypercommerce-vn/codebase-map
- **Issues:** https://github.com/hypercommerce-vn/codebase-map/issues
- **Release notes:** https://github.com/hypercommerce-vn/codebase-map/releases/tag/v2.0.0

---

*Codebase Map v2.0 · Hyper Commerce · 2026*
