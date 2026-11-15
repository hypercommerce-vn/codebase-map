<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate: PR #152 Round 1

- Ngày: 2026-11-15
- Mode: Remote Full (sau push + CI)
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/152
- Branch: `feat/cbm-website` → `main`, head review `cd75fc9`
- Title: feat(website): bilingual project website with live demo and VPS deploy
- PR class: **Feature (HTML only)**, không đụng `codebase_map/` → Tester + CTO A+B+E + Designer 5D
- Reviewer: CTO và Designer là hai agent độc lập, chạy song song sau khi Tester PASS, không thấy kết luận của tác giả
- Báo cáo trước: `ReviewGate_Local_feat-cbm-website_2026-11-15.md` (Local Pre-flight, CTO local 96.7%, GO)

---

## Tầng 1: Tester

| Check | Kết quả |
|---|---|
| CI trên `cd75fc9`: lint, test 3.10/3.11/3.12, generate, impact, snapshot-impact | PASS |
| Lint bản CI pin trên `codebase_map/ tests/ website/` | PASS |
| `pytest tests/ -q` | PASS: 174 passed |
| Self-test generate | 200 node, 992 edge; `summary` / `impact` đúng |
| Build site, Docker nginx (`nginx -t`, route, CSP, gzip, 404) | PASS |
| Trình duyệt qua nginx có CSP: `/`, `/en/`, `/demo/` | 0 lỗi console, link nội bộ 200, demo 200 node, 0 chip flow giả |
| Mobile 375 px | không tràn ngang, menu thu gọn hoạt động |

**Tester: PASS** → chuyển CTO + Designer.

## Tầng 2a: CTO (A + B + E)

| Dim | Điểm |
|---|---|
| A. Logic & Correctness | 20/25 |
| B. Architecture & Structure | 23/25 |
| E. Production Readiness | 9/10 |
| **Tổng** | **52/60 = 86.7%** |

Lỗi tìm thấy (không có blocker):

| # | Mức | Vấn đề |
|---|---|---|
| 1 | should-fix | `deploy.sh`: regex `WEBROOT` nhận `//`, `/etc`, `/var/www`; kết hợp `rsync --delete` có thể xoá file ngoài site |
| 2 | should-fix | Chạy lại `--setup` sau certbot ghi đè config, mất khối HTTPS |
| 3 | should-fix | Site được bật trước `nginx -t`; test lỗi thì config hỏng vẫn bật |
| 4 | should-fix | `nginx:1.27-alpine` hết được vá |
| 5 | should-fix | Câu "code không rời khỏi máy" quá mức khi trang cũng giới thiệu MCP |
| 6 | should-fix | CI không build `website/` |
| 7 | nit | `build.py` nuốt stderr khi lệnh `impact` lỗi |
| 8 | nit | `DEPLOY_HOST` không validate (có thể bị đọc thành option ssh) |
| 9 | nit | Đường dẫn cố định `/tmp/codebase-map.nginx` trên VPS dùng chung |
| 10 | nit | favicon cache 30 ngày không có hash; thiếu HSTS |
| 11 | nit | Tên tầng trên trang (route…) lệch với model (router, core…) |
| 12 | nit | Chép thất bại không có phản hồi; aria-label menu không đổi |
| 13 | nit | Demo nhúng tên nhánh + SHA lúc build; `generated_at` làm build không tái lập từng byte |

## Tầng 2b: Designer (5D)

| Dim | Điểm |
|---|---|
| A. Layout & Structure | 22/25 |
| B. Visual Accuracy | 22/25 |
| C. Interactive | 16/20 |
| D. Data Display | 14/20 |
| E. Offline & Compat | 9/10 |
| **Tổng** | **83/100** |

Màu brand và màu tầng khớp `codebase-map-v2-design.html`. Lỗi tìm thấy (không có blocker):

| # | Mức | Vấn đề |
|---|---|---|
| D1 | should-fix | 700–959 px: terminal che node trung tâm của hình minh hoạ hero |
| D2 | should-fix | Tương phản dưới WCAG AA: số thứ tự "Sắp tới" và skip link |
| D3 | should-fix | Trang hứa "nhóm theo module" nhưng demo chỉ có 1 domain "other" |
| D4 | should-fix | Trong demo, toolbar/minimap che legend và panel (layout của exporter) |
| D5 | should-fix | "edges" mang hai con số (992 và 165), nhãn dài |
| D6 | should-fix | Nút chép 32 px, nút ngôn ngữ 36 px trên màn cảm ứng |
| D7 | nit | Số "992" lệch dòng khi nhãn xuống dòng |
| D8 | nit | Demo ghi "v2.0" cứng, "1 domains", dòng Flows trống (exporter) |
| D9 | nit | Mở menu bằng bàn phím, Tab không vào được link |
| D10 | nit | Chữ trên nav khác tiêu đề section |
| D11 | nit | Tên tầng lệch model (trùng CTO 11) |
| D12 | nit | Không có `aria-live` khi chép; EN ghi "Click" trên màn cảm ứng |
| D13 | nit | `color-mix()` không có fallback |
| D14 | nit | 375 px: dòng "Impact Zone" trong terminal bị cắt |

## Impact Analysis

| Metric | Value |
|---|---|
| Changed nodes (so với `origin/main`) | 0 |
| Impact zone | 0 |
| Risk | 🟢 Low |

## Score & Verdict

Final = CTO 86.7 × 0.6 + Designer 83 × 0.4 = **85.2%**

⚠️ **Chưa SHIPIT, vòng 1/3.** Không có blocker và CTO Dim C không áp dụng (không đổi parser). Sửa toàn bộ lỗi trong phạm vi `website/` rồi review vòng 2.

Ngoài phạm vi PR này (thuộc exporter/parser, đề xuất ticket riêng): D4, D8, cách nhận diện domain phía sau D3, màu xanh lá mang hai nghĩa (service ở hero, method ở demo).
