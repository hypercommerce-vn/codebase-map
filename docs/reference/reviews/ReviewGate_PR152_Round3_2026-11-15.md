<!-- HC-AI | ticket: FDD-TOOL-CODEMAP -->
# Review Gate: PR #152 Round 3 (vòng cuối)

- Ngày: 2026-11-15
- Mode: Remote Full, vòng 3/3
- PR: https://github.com/hypercommerce-vn/codebase-map/pull/152
- Head review: `31982c8` (sửa lỗi vòng 2: `ee3ff05`, `31982c8`)
- Sửa sau review (Tester verify): `5f8d0df`, `4cb8ef3`
- Vòng trước: Round 1 85.2% → Round 2 93.0%

---

## Tầng 1: Tester

| Check | Kết quả |
|---|---|
| Lint bản CI pin, `pytest` | PASS, 174 passed |
| `deploy.sh --setup` trong container nginx:1.30, 9 kịch bản: cài mới · chạy lại không FORCE · FORCE + config hỏng · FORCE + config tốt · web root lạ có file (700) · cài mới + config hỏng · `WEBROOT` là file · thư mục rỗng có sẵn · `WEBROOT` là symlink | đúng cả 9; file upload luôn được dọn |
| nginx 1.30: `/.well-known/security.txt` 200; `/.codebase-map-webroot`, `/.git/config` 404 | PASS |
| Trình duyệt: chép thất bại hiện trạng thái trung tính (viền nét đứt), số liệu thẳng hàng ở 640/768/1440 px, VI + EN | PASS |

**Tester: PASS.**

## Tầng 2a: CTO

Các mục vòng 2 đều đã sửa: N1 (thư mục không đọc được), N2 (`WEBROOT` là file), rollback, dọn upload, cảnh báo build không phải `main` sạch, `/.well-known/`, kiểu chép thất bại, câu MCP. CTO kiểm bằng user không quyền root, sudo thật và rsync thật trong container Debian dùng dash.

| Dim | Vòng 1 | Vòng 2 | Vòng 3 |
|---|---|---|---|
| A. Logic & Correctness | 20 | 23 | 24 |
| B. Architecture | 23 | 24 | 24 |
| E. Production Readiness | 9 | 10 | 10 |
| **Tổng** | 86.7% | 95.0% | **58/60 = 96.7%** |

Lỗi mới: **N3 (should-fix).** `WEBROOT` là symlink trỏ tới thư mục có file thì lọt kiểm "đã có file", vì `find` không đi theo symlink ở điểm bắt đầu, còn `chown` thì có, rồi `rsync --delete` xoá file. → **Đã sửa ở `5f8d0df`**: `--setup` từ chối khi `WEBROOT` là symlink. Tester verify: file trong thư mục đích còn nguyên, chủ sở hữu vẫn là root, nginx không bị đụng tới.

B5 còn trừ 1 điểm: `content.py` (dữ liệu chữ) và `styles.css` dài hơn 300 dòng.

## Tầng 2b: Designer

Các nit vòng 2 đã sửa: chép thất bại không còn giống thành công (tương phản 17.85:1 sáng, 14.64:1 tối), feature 1 ghi "thanh bên tìm node", nhãn số cạnh đúng với dữ liệu (634 lời gọi + 170 import trong 827 cạnh không vẽ), câu MCP.

| Dim | Vòng 1 | Vòng 2 | Vòng 3 |
|---|---|---|---|
| A. Layout | 22 | 25 | 25 |
| B. Visual | 22 | 23 | 23 |
| C. Interactive | 16 | 17 | 18 |
| D. Data | 14 | 16 | 16 |
| E. Offline & Compat | 9 | 9 | 9 |
| **Tổng** | 83 | 90 | **91/100** |

Nit mới: ở 768 px, nhãn EN dài đẩy số liệu thứ ba xuống hàng riêng. → **Đã sửa ở `4cb8ef3`**: từ 640 px dùng lưới 3 cột co theo khung; Tester verify thẳng hàng ở 640/768/1440 px.

Điểm còn thiếu nằm ở các mục của exporter (không thuộc PR này) và việc chỉ test trên Chromium.

## Score & Verdict

Final = 96.7 × 0.6 + 91 × 0.4 = **94.4%** (85.2% → 93.0% → 94.4%)

✅ **SHIPIT + NOTE** (≥ 90% ở vòng 3) → chuyển CEO review.

**NOTE cho CEO:**

1. Chưa deploy lên VPS thật. Phần `--setup` mới chỉ chạy trong container giả lập; lần chạy thật đầu tiên cần tên miền + VPS.
2. Đã tách ra làm ticket riêng (exporter/parser, không thuộc website):
   - demo bị toolbar/minimap che legend và panel;
   - badge "v2.0" viết cứng ở `html_exporter.py:552`;
   - "1 domains" và dòng Flows trống;
   - `_detect_domain` chỉ nhận tên domain của Hyper Commerce, nên bản đồ CBM chỉ có 1 nhóm "other";
   - màu xanh lá mang hai nghĩa (service ở hero, method ở demo).
3. Chỉ test trên Chromium; Firefox và Safari chưa kiểm.
