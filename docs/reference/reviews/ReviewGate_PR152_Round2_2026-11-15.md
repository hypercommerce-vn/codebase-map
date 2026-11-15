<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate: PR #152 Round 2

- Ngày: 2026-11-15
- Mode: Remote Full, vòng 2/3
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/152
- Head review: `b29b272` (4 commit sửa lỗi vòng 1: `d0a1768`, `1f23d49`, `7852b0a`, `b29b272`)
- Vòng trước: `ReviewGate_PR152_Round1_2026-11-15.md` (85.2%)

---

## Tầng 1: Tester

| Check | Kết quả |
|---|---|
| CI trên `b29b272`: 9 check, gồm job mới `website` (lint + build + kiểm placeholder + `bash -n deploy.sh`) | PASS |
| Lint bản CI pin, `pytest` | PASS, 174 passed |
| `deploy.sh`: input sai (`WEBROOT=//`, `/etc`, `/var/www`, `/var/www/..`, `DEPLOY_HOST=-oProxyCommand=x`, `DOMAIN=-bad.com`) | đều bị chặn trước khi build |
| `deploy.sh --setup` chạy trong container nginx:1.30 (sudo/systemctl giả lập): cài mới, chạy lại không FORCE, FORCE + config hỏng, FORCE + config tốt, web root lạ, cài mới + config hỏng | đúng ở cả 6 kịch bản; config certbot được giữ hoặc khôi phục |
| Docker nginx 1.30.6: route, CSP, HSTS, dotfile 404, favicon có hash | PASS |
| Trình duyệt: 820 px không che node, số liệu thẳng hàng, tương phản 6.29:1, menu bàn phím, chép thất bại có phản hồi, 375 px terminal không tràn | PASS |

**Tester: PASS.**

## Tầng 2a: CTO

12/12 lỗi vòng 1 đã sửa; #13 (demo ghi nhánh + SHA lúc build) được chấp nhận vì repo public và bản Docker không có `.git`.

| Dim | Vòng 1 | Vòng 2 |
|---|---|---|
| A. Logic & Correctness | 20 | 23 |
| B. Architecture | 23 | 24 |
| E. Production Readiness | 9 | 10 |
| **Tổng** | 52/60 (86.7%) | **57/60 (95.0%)** |

Lỗi mới:

| # | Mức | Vấn đề |
|---|---|---|
| N1 | should-fix | Kiểm "web root đã có file" dùng `ls` không có sudo: thư mục user SSH không đọc được bị coi là rỗng |
| N2 | should-fix | Lỗi xảy ra sau khi đã cài config (ví dụ `WEBROOT` là file) không được rollback |
| nit | | `location ~ /\.` chặn luôn `/.well-known/` |
| nit | | Trạng thái chép thất bại dùng màu xanh của "thành công" |
| nit | | MCP: "kết quả bạn hỏi" chưa đúng khi Claude tự tra cứu |

## Tầng 2b: Designer

D1, D2, D5, D6, D7, D9, D10, D12, D13, D14 đã sửa; D3 và D11 sửa phần nói quá. Đồng ý D4, D8 và nhận diện domain thuộc exporter/parser, làm ticket riêng.

| Dim | Vòng 1 | Vòng 2 |
|---|---|---|
| A. Layout | 22 | 25 |
| B. Visual | 22 | 23 |
| C. Interactive | 16 | 17 |
| D. Data | 14 | 16 |
| E. Offline & Compat | 9 | 9 |
| **Tổng** | 83 | **90/100** |

Nit mới: chép thất bại trông như thành công; feature 1 còn ghi "cây thư mục" trong khi sidebar nhóm theo domain; nhãn số cạnh nên nói rõ import và hàm có sẵn.

## Score & Verdict

Final = 95.0 × 0.6 + 90 × 0.4 = **93.0%** (vòng 1: 85.2%)

⚠️ **Chưa SHIPIT, vòng 2/3.** Không có blocker. Sửa N1, N2 và các nit trong phạm vi website (commit `ee3ff05`, `31982c8`), rồi review vòng 3.
