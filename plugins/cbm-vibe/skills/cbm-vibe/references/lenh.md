# Các lệnh của công cụ và ý nghĩa kết quả

Mọi lệnh chạy tại thư mục gốc của dự án. `CBM` dưới đây là viết tắt của
`python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py"`. Lệnh nào thuộc nhóm
`features` cũng nhận `--json`; khi đó phần in ra chỉ gồm JSON. Lệnh trả mã
thoát khác 0 khi lỗi; với `--json`, lỗi có dạng `{"error": "..."}`.

## Mục lục

- [features status](#features-status) — ứng dụng có gì
- [features add](#features-add) — thêm hoặc sửa một tính năng
- [features criterion](#features-criterion) — thêm tiêu chí
- [features evidence](#features-evidence) — ghi bằng chứng
- [generate --label](#generate---label) — chụp trạng thái code
- [features impact](#features-impact) — thay đổi đụng tới gì
- [Cách công cụ xác định "liên quan"](#cách-công-cụ-xác-định-liên-quan)
- [Những điều công cụ không thấy](#những-điều-công-cụ-không-thấy)

## features status

```bash
CBM features status --json
```

| Trường | Ý nghĩa |
|---|---|
| `features[].id`, `name`, `summary` | Tính năng |
| `features[].screens[]` | Màn hình: `url` (địa chỉ trang, ví dụ `/dat-lich`) và `path` (file) |
| `features[].apis[]` | Điểm nhận dữ liệu: `url`, `methods` (GET, POST…), `path` |
| `features[].criteria[]` | Tiêu chí: `id`, `text`, `status`, `evidence` |
| `features[].counts` | Số tiêu chí theo `verified`, `needs_recheck`, `unchecked` |
| `features[].files.owned` | File thuộc tính năng |
| `features[].files.shared` | File dùng chung mà tính năng phụ thuộc |
| `unowned_files[]` | File chưa thuộc tính năng nào: `path`, `kind` (`screen`, `api`, `other`), `url`, `used_by` (tính năng nào đang dùng) |
| `summary` | Tổng số tính năng, tiêu chí theo trạng thái, file chưa gán |

`features` rỗng nghĩa là chưa ai khai báo tính năng. Màn hình và điểm nhận
dữ liệu được nhận ra theo quy ước của Next.js (`app/**/page.tsx`,
`app/**/route.ts`, `pages/**`); với khung khác, `kind` là `other` và bạn tự
đọc code để biết file nào là màn hình.

## features add

```bash
CBM features add --id dat-lich --name "Đặt lịch" --summary "..." --files <mẫu> [<mẫu> ...]
CBM features add --id dat-lich --append --files <mẫu mới>     # thêm file, giữ phần cũ
```

- `--id`: chữ thường không dấu, số, gạch nối. Dùng lại `id` đã có là sửa
  tính năng đó.
- `--files`: mỗi mẫu là một file, một thư mục (lấy mọi thứ bên trong), hoặc
  mẫu có `*` và `?`. Dấu ngoặc vuông được hiểu nguyên văn, nên
  `"app/api/bookings/[id]/route.ts"` là đúng file đó. Luôn đặt mẫu trong
  dấu nháy.
- Một file được phép thuộc nhiều tính năng.
- Kết quả có `matched_files` (file khớp) và `unmatched_patterns` (mẫu không
  khớp file nào — thường là gõ sai đường dẫn; hãy sửa).

## features criterion

```bash
CBM features criterion --feature dat-lich --text "Giờ đã có người đặt thì không đặt được nữa." --json
```

Trả về `id` của tiêu chí (`dat-lich-1`, `dat-lich-2`…). Ghi nhớ `id` này để
ghi bằng chứng và đặt nhãn ảnh chụp.

## features evidence

```bash
CBM features evidence --criterion dat-lich-1 --kind manual --note "Chủ tiệm tự bấm thử ngày 15/11"
CBM features evidence --criterion dat-lich-2 --kind test --note "tests/booking.test.ts: từ chối giờ đã đặt"
```

- `manual`: một người đã tự thử và thấy đúng. Chỉ ghi khi người dùng nói họ
  đã thử.
- `test`: một bài kiểm thử tự động vừa chạy đạt và nó kiểm đúng tiêu chí đó.
- Bằng chứng gắn với code tại lúc ghi. Ghi lại lần nữa sẽ thay bằng chứng cũ.

## generate --label

```bash
CBM generate --label truoc-dat-lich-4
```

Chụp trạng thái code hiện tại dưới một nhãn. Chụp "trước" khi chốt xong tiêu
chí, chụp "sau" khi sửa xong. Hai nhãn dùng chung đuôi là `id` của tiêu chí
đầu tiên trong lần yêu cầu đó.

## features impact

```bash
CBM features impact --baseline truoc-dat-lich-4 --current sau-dat-lich-4 --json
```

| Trường | Ý nghĩa |
|---|---|
| `features[].touched` | `direct`: file của tính năng bị sửa. `indirect`: code mà nó phụ thuộc bị sửa. `none`: không bị đụng |
| `features[].behaviour_changed` | `false`: có sửa nhưng cách chạy không đổi (chỉ đổi trình bày, dòng import, khai báo kiểu) |
| `features[].direct.files[]` | File của tính năng bị thêm, sửa, xoá (`change`: `added`, `modified`, `removed`) |
| `features[].direct.functions[]` | Đoạn xử lý bị thêm, xoá hoặc sửa (`change`: `added`, `removed`, `body`, `signature`) |
| `features[].indirect.files[]` | File dùng chung có phần ngoài các đoạn xử lý bị đổi (ví dụ một hằng số); `owners` là tính năng sở hữu file |
| `features[].indirect.functions[]` | Đoạn xử lý của tính năng khác mà tính năng này gọi tới, vừa bị sửa |
| `features[].criteria[]` | Từng tiêu chí với `status_before` và `status_after` |
| `unowned_changes[]` | File bị đổi mà không thuộc tính năng nào; `used_by` là các tính năng đang dùng nó |
| `summary.touched_direct`, `touched_indirect` | Danh sách `id` tính năng bị đụng |
| `summary.criteria_to_recheck` | Số tiêu chí đang ở trạng thái cần kiểm lại |

Tên file và tên đoạn xử lý trong kết quả là để **bạn** hiểu chuyện gì đã
xảy ra. Khi nói với người dùng, đổi sang lời thường ("phần gửi tin nhắc",
"màn hình danh sách lịch").

## Cách công cụ xác định "liên quan"

Một tính năng **sở hữu** những file khớp mẫu của nó, và **phụ thuộc** vào
mọi đoạn xử lý mà code của nó gọi tới (kể cả gọi qua nhiều tầng), cùng các
hằng số và lệnh nằm ngoài đoạn xử lý trong những file liên quan. Bằng chứng
của một tiêu chí hết hạn khi bất kỳ phần nào trong số đó thay đổi theo cách
có thể làm đổi cách chạy. Đổi cách trình bày code, dòng import hay khai báo
kiểu thì không làm hết hạn.

## Những điều công cụ không thấy

Nói rõ với người dùng khi những điểm này có thể ảnh hưởng tới kết luận:

- Màn hình gọi điểm nhận dữ liệu qua địa chỉ (`fetch("/api/...")`). Vì vậy
  file của điểm nhận dữ liệu phải được ghi vào cùng tính năng với màn hình.
- Hai tính năng cùng đọc, ghi một bảng dữ liệu. Sửa cách một bên ghi có thể
  ảnh hưởng bên kia mà công cụ không báo.
- File không phải mã nguồn: kiểu dáng (CSS), dữ liệu JSON, hình ảnh.
- Hành vi lúc chạy thật: công cụ đọc code, không chạy ứng dụng. "Có bằng
  chứng" nghĩa là đã có người hoặc bài kiểm thử xác nhận, không phải công cụ
  tự xác nhận.
