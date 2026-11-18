<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate: Local Pre-flight `feat/cbm-website`

- Ngày: 2026-11-15
- Mode: Local Pre-flight (`/review-gate --local`), chạy trước `git push` / `gh pr create`
- Branch: `feat/cbm-website` → `main` (đã merge `origin/main` = `2d4ff1f`, gồm PR #148)
- Scope: CBM-WEB, website dự án v0.1: landing tĩnh song ngữ, demo `/demo/`, deploy VPS (nginx + `deploy.sh`) hoặc Docker
- Design: CEO duyệt v0.1 ngày 15/11/2026. Trang build ra chính là bản design (rule No Design = No Implementation).
- PR class: **Feature (HTML only)**, không đụng `codebase_map/` → Tester + CTO A+B+E + Designer 5D (Designer chấm ở Remote Full)

---

## 1. Lint gate

| Check | Kết quả |
|---|---|
| `black==24.10.0 --check --target-version py310 codebase_map/ tests/ website/` (bản CI pin) | PASS, 38 file không đổi |
| `isort==5.13.2 --check --profile black codebase_map/ tests/ website/` | PASS |
| `flake8 codebase_map/ tests/ website/` | PASS |

## 2. Self-test generate

| Check | Kết quả |
|---|---|
| `python -m codebase_map generate -c codebase-map-self.yaml` | PASS: 200 node, 992 edge, 73 ms |
| `summary -f docs/function-map/graph.json` | PASS: 37 class · 48 function · 115 method |
| `impact GraphBuilder` | PASS: 4 node bị ảnh hưởng (`__main__`, `cli`, `cli._cmd_generate`, `cli.main`) |
| `pytest tests/ -q` | PASS: 174 passed |

## 3. Impact analysis

`codebase-map diff origin/main -f docs/function-map/graph.json --json`

| Metric | Value |
|---|---|
| Changed files (Python) | `website/build.py`, `website/content.py` (ngoài package `codebase_map/`) |
| Changed nodes trong graph | 0 |
| Impact zone | 0 |
| Risk level | 🟢 Low |

PR không sửa dòng nào trong `codebase_map/`; CLI, parser và exporter giữ nguyên.

## 4. Build và verify site

| Check | Kết quả |
|---|---|
| `python website/build.py` | PASS: `dist/` 636 KB (demo 556 KB, gzip 130 KB), không còn placeholder `{{…}}` |
| Demo dựng trên `main` mới (sau PR #148) | 0 chip flow giả "name1/name2", 200 node render |
| Docker: `docker build -f website/Dockerfile` + `nginx -t` | PASS |
| HTTP: `/`, `/en/`, `/demo/`, CSS, JS, favicon, `robots.txt`, `sitemap.xml` | 200 |
| HTTP: `/en` | 301 → `/en/` (redirect tương đối, giữ port) |
| HTTP: `/nope`, `/404.html` | 404 (trang 404 song ngữ) |
| CSP `/` | `default-src 'self'`, không inline, `frame-ancestors 'none'` |
| CSP `/demo/` | thêm `'unsafe-inline'` cho script/style, `frame-ancestors 'self'` |
| Header khác | `nosniff`, `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-cache` cho HTML |
| Trình duyệt (qua nginx thật, có CSP) | 0 lỗi console ở `/`, `/en/`, `/demo/`; link nội bộ 200 |
| Mobile 375 px | không tràn ngang, menu thu gọn hoạt động |
| Không test | `deploy.sh` trên VPS thật (chưa có tên miền + VPS; chỉ kiểm cú pháp) |

## 5. CTO local (A + B + E, Claude tự chấm trên diff)

| Dim | Điểm | Ghi chú |
|---|---|---|
| A. Logic & Correctness | 25/25 | Build dừng khi thiếu key hoặc hai ngôn ngữ lệch key; `SITE_URL` được validate; số liệu và output terminal lấy từ code thật; `deploy.sh` có `set -euo pipefail` và validate `DOMAIN`/`DEPLOY_HOST` |
| B. Architecture & Structure | 23/25 | Tách content / template / build / deploy rõ. Trừ 2: `styles.css` 585 dòng (> 300) |
| E. Production Readiness | 10/10 | Lint PASS; marker `HC-AI` trên mọi file code (README và `.dockerignore` không phải code) |
| **Tổng** | **58/60 = 96.7%** | |

## Verdict

✅ **GO**: CTO local ≥ 90, lint + self-test PASS, impact 🟢 Low. Push → `gh pr create` → `/review-gate PR #XX` (Remote Full).
