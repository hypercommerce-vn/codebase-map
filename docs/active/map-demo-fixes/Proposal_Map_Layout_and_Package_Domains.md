# Đề xuất — Bố cục đáy canvas & domain theo package

> **Ticket:** FDD-TOOL-CODEMAP · **Nguồn:** review gate PR #152 (CBM-WEB, trang `/demo/`)
> **Ngày:** 16/11/2026 · **Trạng thái:** ⏳ Chờ CEO duyệt (chưa code)
> **Liên quan:** PR sửa lỗi 1-3 (badge version, "1 domains", hàng Flows rỗng) — đã có trong cùng PR với tài liệu này.

Hai việc dưới đây **chưa được code**. Việc 4 đổi bố cục HTML, nên theo rule "No Design = No Implementation" cần design được duyệt trước. Việc 5 đổi cách parser gán domain, có ảnh hưởng tới PR #145 và nhóm PR VIBE đang mở.

---

## 4. Toolbar, legend, minimap và detail panel chồng lên nhau

### Hiện trạng (đo trên `docs/function-map/index.html`, self-scan CBM)

Cả 3 khối cùng nằm ở đáy canvas: toolbar bên trái, legend ở giữa, minimap bên phải. Lỗi đến từ hai nguồn:

- **Toolbar che legend là lỗ hổng của design.** Design `design-preview/active/codebase-map-v2-design.html` cũng xếp 3 khối chung một hàng đáy.
- **Minimap che panel node là code làm lệch design.** Trong design, detail panel có z-index 20 (nằm trên minimap z 15), top/right 12 px, bo góc 12. Exporter lại dùng z 10, 16 px, bo góc 8. Legend trong design là z 15, bottom 12; exporter dùng z 5, bottom 16.

| Khối | Kích thước | Vị trí trong exporter |
|------|-----------|--------|
| Toolbar | 342 × 36 px (8 nút + 2 vạch chia) | `bottom 12, left 12`, z 15 |
| Legend | 591 × 31 px (nhóm Type 330 + nhóm Edge 217) | `bottom 16`, căn giữa, z 5 |
| Minimap | 180 × 120 px | `bottom 12, right 12`, z 15 |
| Detail panel | rộng 380, `max-height: 80vh` | `top 16, right 16`, z 10 |

Số đo: lần đầu đo trên bản `main` trước PR #155 (hàng Flows còn hiện); CTO và Designer đo lại sau PR #155. Khoảng giá trị là chênh lệch giữa các lần đo.

| Viewport | Canvas | Toolbar ↔ Legend | Minimap ↔ Legend | Minimap ↔ Detail panel |
|----------|--------|------------------|------------------|------------------------|
| 1440 × 900 | 1100 px | chồng **99 px**, che chữ "TYPE" | không chồng | che **36 px** đáy panel (tới ~102–124 px khi panel cao tối đa) |
| 1094 × 800 | 754 px | chồng **~272–280 px** | chồng **~110–118 px**, che nhóm "EDGE" | che **~116–136 px** đáy panel |
| 820 × 800 | 540 px | chồng | chồng | — ; thêm: **toolbar chồng minimap 6 px** (ở 769 px là ~57 px) |

Muốn cả 3 khối nằm vừa một hàng mà legend vẫn căn giữa thì canvas phải rộng ≥ 1323 px, tức viewport ≥ ~1663 px (sidebar 340 px). Màn laptop phổ biến (1280–1536) đều dính lỗi.
Ngoài ra `80vh` không trừ phần header. Header cao ~127–131 px (topbar 48 + tab 43 + breadcrumb 36), hoặc ~155 px khi hàng Flows hiện. Vì vậy panel tràn khỏi màn hình khi màn thấp hơn ~715–735 px, hoặc ~885 px khi có hàng Flows. Bản `main` trước PR #155 luôn hiện hàng Flows (lỗi 3), nên ở 1094 × 800 panel tràn ra ngoài; sau PR #155 thì không tràn ở kích thước này nữa.
Ở ≤ 768 px, design ẩn các badge thống kê trên topbar (`.topbar-stats{display:none}`), nhưng exporter không ẩn. Kết quả: ở 375 px topbar rộng 579 px và trang bị cuộn ngang.

### Phương án

**A — Xếp chồng góc trái + chừa cột minimap (khuyến nghị)**

```
┌──────────────────────────── canvas ────────────────────────────┐
│                                          ┌── detail panel ──┐  │
│                                          │ max-height:      │  │
│                                          │ 100% − 164px     │  │
│                                          └──────────────────┘  │
│  ┌ Legend: TYPE ● ● ● ● ● ●  ┐                                 │
│  └ EDGE ── ┄┄ ━━  (tự xuống dòng) ┘                ┌─minimap─┐ │
│  [+][−][▢] | [T][↔][▦] | [📷][⛶]                   │         │ │
└────────────────────────────────────────────────────┴─────────┴─┘
```

- Legend chuyển từ giữa đáy sang góc trái, nằm ngay trên toolbar (`left 12px; bottom 56px`).
- Legend có `flex-wrap: wrap` và `max-width: calc(100% − 228px)` (chừa cột minimap). Khi canvas hẹp, Type và Edge xuống 2 dòng, không bao giờ chạm minimap.
- Detail panel đổi `max-height: 80vh` thành `calc(100% − 164px)` (= 16 top + 120 minimap + 12 + 16 khoảng cách). Đáy panel luôn nằm trên minimap và trong màn hình; nội dung dài thì cuộn trong panel.
- Mobile ≤ 768 px (minimap đã ẩn, toolbar đã căn giữa): legend căn giữa phía trên toolbar, `left/right 12px`.
- Chỉ sửa CSS (~15 dòng), không thêm tương tác mới, không bỏ khối nào.

Designer (review PR #155) đồng ý hướng A và yêu cầu bổ sung khi vẽ lại design:

1. Từng nhóm legend cũng phải xuống dòng (`.legend-group{flex-wrap:wrap}`). Riêng nhóm Type đã rộng 330 px; ở viewport 820 px, `max-width` chỉ còn 312 px.
2. Ở 769–837 px (sidebar 280 px), toolbar chồng minimap. Cần ẩn minimap ở ≤ 900 px, hoặc nâng mốc căn giữa toolbar.
3. Bỏ `transform: translateX(-50%)` khi dời legend sang trái, và viết lại rule mobile cho legend.
4. Trả detail panel về z-order của design (z 20, nằm trên minimap).
5. `max-height` của panel cần mức sàn, ví dụ `max(200px, calc(100% − 164px))`. Trên mobile không cần chừa 164 px vì minimap đã ẩn.
6. Gộp vào cùng đợt: ẩn badge thống kê topbar ở ≤ 768 px theo design, để hết cuộn ngang ở 375 px.
7. Nút "Fit to screen" phải chừa chỗ cho cụm legend + toolbar ở góc trái dưới (cao ~90–120 px), để không che node.
8. Bộ ảnh chụp design: 1440 / 1094 / 820 / 768 / 375.

**B — Legend thu vào nút trên toolbar**
Thêm nút "ⓘ Legend" vào toolbar để bật/tắt legend (popover phía trên toolbar). Canvas thoáng nhất, nhưng thêm 1 thao tác và cần design tương tác mới: nút có `aria-expanded`, Esc để đóng, focus quay về nút. Designer khuyên không mặc định đóng ở < 1440 px, vì phần lớn laptop nằm dưới mốc này và người mới cần legend để hiểu màu.

**C — Ẩn minimap khi mở detail panel**
Giữ panel cao tối đa, minimap tạm ẩn khi đang xem node. Đơn giản, nhưng mất minimap đúng lúc người dùng đang điều hướng. Vẫn phải xử lý riêng chuyện toolbar chồng legend.

### Bước tiếp theo nếu CEO chọn A

1. Cập nhật `design-preview/active/codebase-map-v2-design.html` theo phương án A, gồm 8 điểm bổ sung ở trên, chụp 1440 / 1094 / 820 / 768 / 375.
2. Designer review → CEO duyệt design.
3. PR riêng: sửa CSS trong `html_exporter.py` (cùng phần Fit chừa chỗ cho overlay), thêm test kiểm tra rule CSS, kiểm tra lại trong trình duyệt ở 5 độ rộng. Ước tính **1–1.5 SP**.

---

## 5. Domain chỉ biết tên domain của Hyper Commerce

### Hiện trạng

`_detect_domain()` (`codebase_map/parsers/python_parser.py`) chỉ nhận các thư mục `crm, cdp, ecommerce, private_traffic, auth, admin, billing`, sau đó tới `core / workers / models`, còn lại đều là `"other"`. TypeScript (`_infer_domain` trong `typescript_parser.py`) có danh sách tương tự nhưng không giống hẳn: không có `admin`, không có rule worker/model, so khớp theo nguyên một thành phần đường dẫn chứ không theo chuỗi con, và fallback về `base_module` hoặc `"core"`.
Hệ quả: mọi repo không phải HC chỉ có **1 domain**. Self-scan của CBM: 200/200 node là `other`, nên Executive view chỉ có 1 thẻ, sidebar chỉ có 1 nhóm và cluster chỉ có 1 khối.

### Đề xuất

Khi không khớp tên domain nào đã biết, lấy **package đầu tiên bên dưới gốc source** làm domain.

Thứ tự ưu tiên (cao → thấp):

1. `domains:` trong `codebase-map.yaml` — **PR #145** (builder ghi đè sau khi parse)
2. Tên domain HC có sẵn + `core/worker/model` — giữ nguyên để HC không bị đổi
3. **Mới:** thư mục cấp 1 bên dưới gốc source. Ví dụ `codebase_map/parsers/python_parser.py` → `parsers`.
   - Có `base_module`: lấy thành phần đầu tiên của `module_id` sau `base_module`.
   - Không có `base_module`: lấy thư mục đầu tiên của đường dẫn **tương đối với `sources[].path`**. Trường hợp này rất quan trọng: chế độ zero-config của VIBE (`Config.auto_detect`, PR #147 trở đi) tạo `SourceConfig(path=".")` không có `base_module`. Hiện `_file_to_module_id` trả về cả đường dẫn tuyệt đối khi thiếu `base_module`, nên nếu chỉ dựa vào `module_id` thì rule mới không có tác dụng với đúng nhóm người dùng vibecoding. Builder cần truyền gốc source (hoặc đường dẫn tương đối với source) cho parser.
4. File nằm thẳng ở gốc source (vd. `codebase_map/cli.py`) → tên `base_module` (`codebase_map`); không có `base_module` thì `other`.

Mô phỏng trên self-scan CBM (200 node): `graph` 125 · `parsers` 36 · `codebase_map` 35 · `exporters` 4, tức **4 domain thay cho 1**.

### Không xung đột với PR đang mở

- **PR #145 (config domains):** sửa `config.py` và `builder.py`, chạy *sau* parser, chỉ ghi đè node khớp pattern; node không khớp "giữ nguyên domain parser đoán". Đề xuất này chỉ làm cho phần "đoán" đó tốt hơn, nên hai việc bổ sung cho nhau. Không đụng cùng file.
- **Nhóm PR VIBE (#147, #149, #150, #151, #153):** #147 không đụng parser; từ #149 trở đi, `parse_file()` gọi `_detect_domain(rule_path)` bằng đường dẫn tương đối với project. Nhóm VIBE cũng đã chứa sẵn thay đổi `config.py`/`builder.py` của #145. Rule mới tính theo `module_id` khi có `base_module` và theo đường dẫn tương đối với source khi không có (xem bước 3), nên chạy đúng cả trước và sau nhóm VIBE. Để tránh conflict ở dòng gọi hàm, nên **làm sau khi #145 và nhóm VIBE đã merge**.
- **Snapshot diff:** `_detect_modifications()` không so sánh domain, nên lần chạy đầu sau khi nâng cấp **không** bị báo "modified" hàng loạt. Báo cáo `diff` theo domain và Executive view sẽ hiện tên package thay cho `other`.
- **Màu:** `DOMAIN_COLORS` chỉ có màu cho domain HC; domain mới dùng màu xám mặc định. Nên gán màu theo bảng màu xoay vòng, việc nhỏ đi kèm (thuộc phần design của việc 4 hoặc làm riêng).

### Cần CEO quyết

- **Q5a:** Đồng ý thêm rule "package cấp 1" làm fallback (bước 3)?
- **Q5b:** File ở gốc source hiển thị là tên package (`codebase_map`) hay `other`?
- **Q5c:** Làm sau khi #145 và nhóm VIBE merge (khuyến nghị), hay làm ngay rồi để PR sau rebase?

Ước tính: **1 SP** (Python + TypeScript parser, khoảng 8 test mới, self-scan trước/sau).

---

## Ghi nhận thêm (ngoài phạm vi, chưa sửa)

- Badge "edges" trên header chỉ đếm cạnh có đủ 2 đầu là node trong graph (self-scan: **165**), trong khi CLI và `graph.json` báo **992** trên `main` (**993** sau PR #155, vì dòng import `__version__` mới cũng được quét), gồm cả cạnh tới module/hàm bên ngoài. Hai con số khác nhau dễ gây hiểu nhầm.
- `project_name` được chèn thẳng vào `<title>` mà không escape. Rủi ro thấp (giá trị lấy từ config của chính người dùng), nhưng nên `html.escape` cho chắc.
- Auto-fit chạy theo hẹn giờ cố định 3 giây. Nếu lúc đó graph đang ẩn (đang ở tab khác, hoặc trang mở trong tab nền) thì canvas có thể trống, hoặc console báo `translate(NaN,NaN)`. Lỗi đã có từ trước PR #155. Nên fit lại khi `simulation.on('end')` xảy ra, và khi quay về tab Graph. Điều này quan trọng với trang `/demo/` của website.
- Chip flow: các chip dính sát nhau (gap 0 px), không dùng được bàn phím (`<span>` thay vì `<button aria-pressed>`). Badge version tương phản thấp (~1.8:1, khớp token design nhưng dưới chuẩn AA).
