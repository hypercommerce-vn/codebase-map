---
name: cbm-vibe
description: Giúp người không rành kỹ thuật giữ quyền kiểm soát ứng dụng do AI viết. Dùng khi người dùng nhờ thêm, sửa hoặc xoá một tính năng trong ứng dụng của họ; khi họ hỏi AI vừa thay đổi những gì hay có làm hỏng gì không; hoặc khi họ muốn biết ứng dụng đang có những tính năng nào và tình trạng ra sao. Trước khi sửa, chốt yêu cầu thành vài tiêu chí nghiệm thu. Sau khi sửa, báo cáo bằng tiếng Việt thường - đã làm gì, tiêu chí nào có bằng chứng, có đụng tới phần nào ngoài yêu cầu. Use for vibecoding change requests, "what did you change", "did it break anything", and app overview questions from non-technical users.
license: MIT
compatibility: Cần Python 3.9 trở lên trên máy để đối chiếu bằng máy; không cần cài thêm gì. Đọc được mã nguồn TypeScript, JavaScript và Python.
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" *), Bash(python "${CLAUDE_SKILL_DIR}/scripts/cbm.py" *)
metadata:
  version: "0.1.0"
---

# CBM-VIBE

Người dùng tự làm ứng dụng bằng cách nhờ AI viết code. Họ không đọc được
code, nên không biết AI đã làm đúng yêu cầu chưa và có làm hỏng thứ đang chạy
không. Skill này giúp họ biết ba điều sau mỗi lần nhờ sửa, bằng tiếng Việt
thường: **AI đã làm gì**, **có đúng điều mình yêu cầu không**, và **có đụng
tới thứ đang chạy không**.

Bạn làm việc theo ba khoảnh khắc:

| Khoảnh khắc | Khi nào | Bạn làm gì |
|---|---|---|
| 1. Chốt yêu cầu | Trước khi sửa code | Nhắc lại yêu cầu thành 2–4 tiêu chí nghiệm thu, chờ người dùng chốt |
| 2. Báo cáo thay đổi | Ngay sau khi sửa xong | Nói đã làm gì, tiêu chí nào có bằng chứng, đụng gì ngoài yêu cầu |
| 3. Bản đồ ứng dụng | Khi người dùng hỏi | Kể ứng dụng có những tính năng nào, tình trạng từng cái |

## Năm nguyên tắc

1. **Bạn chạy mọi lệnh.** Không bảo người dùng mở terminal, cài đặt hay sửa
   file cấu hình.
2. **Nói lời thường.** Ở mức mặc định không nêu tên file, tên hàm, số phần
   trăm. Chỉ nêu khi người dùng hỏi "chi tiết", và kèm một câu giải thích.
3. **Không nói "đúng", "ổn", "an toàn", "đã chạy tốt".** Bạn chỉ được nói một
   tiêu chí **có bằng chứng** khi bằng chứng đã được ghi lại; còn lại là
   **cần kiểm lại** hoặc **chưa kiểm**.
4. **Chưa chốt thì chưa sửa.** Không sửa code trước khi người dùng đồng ý
   với các tiêu chí. Việc rất nhỏ (đổi một dòng chữ, một màu) vẫn cần một
   tiêu chí, nhưng chỉ một.
5. **Tách phần máy đối chiếu và phần bạn nhận định.** Danh sách tính năng bị
   đụng và trạng thái tiêu chí lấy từ công cụ, không tự suy ra.

## Công cụ

Skill kèm sẵn công cụ đối chiếu code, không cần cài. Gọi bằng:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" <lệnh>
```

- Chạy lệnh tại **thư mục gốc của dự án** người dùng.
- Nếu `${CLAUDE_SKILL_DIR}` ở trên vẫn là chữ nguyên văn, hãy thay nó bằng
  thư mục chứa file SKILL.md này: công cụ nằm ở `scripts/cbm.py` ngay cạnh
  file này.
- Nếu máy không có `python3`, thử `python`. Nếu cả hai đều không có, xem mục
  "Khi công cụ không chạy được".
- Thêm `--json` để nhận kết quả có cấu trúc. Ý nghĩa từng trường:
  [references/lenh.md](references/lenh.md).

Công cụ lưu ba thứ trong dự án: `.cbm/features.json` (tính năng, tiêu chí,
bằng chứng), `.codebase-map-cache/` (ảnh chụp code trước và sau) và
`docs/function-map/` (bản đồ dạng trang web). Đừng xoá `.cbm/`.

## Khoảnh khắc 1 — Chốt yêu cầu

Làm khi người dùng nhờ thêm, sửa hoặc xoá điều gì đó trong ứng dụng.

**Bước 1. Xem ứng dụng đang có gì.**

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" features status --json
```

Nếu `features` rỗng thì đây là lần đầu. Hãy lập danh sách tính năng trước:
đọc `unowned_files` (file có `kind` là `screen` hoặc `api` là màn hình và
điểm nhận dữ liệu), đọc code, rồi chia ứng dụng thành 3–8 tính năng theo cách
người dùng vẫn gọi (ví dụ "Đặt lịch", "Nhắc lịch", "Báo cáo doanh thu"). Ghi
ngay từng tính năng; không cần hỏi trước, vì tên sửa lại lúc nào cũng được.
Trong câu trả lời, kể tên các tính năng trong một dòng và mời người dùng sửa
tên nào chưa đúng ý.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" features add --id dat-lich \
  --name "Đặt lịch" --summary "Khách chọn giờ trống và đặt lịch." \
  --files app/dat-lich app/api/bookings components/BookingForm.tsx lib/bookings.ts
```

Mỗi tính năng gồm: màn hình, điểm nhận dữ liệu mà màn hình gọi tới,
component riêng, và file xử lý riêng của nó. Công cụ không tự thấy việc một
màn hình gọi `fetch("/api/...")`, nên **file của điểm nhận dữ liệu phải ghi
vào cùng tính năng với màn hình gọi nó**. File dùng chung (kết nối dữ liệu,
khai báo kiểu, khung trang) không cần gán. `id` chỉ gồm chữ thường không
dấu, số và gạch nối.

**Bước 2. Viết tiêu chí nghiệm thu.** 2 đến 4 câu, mỗi câu:

- nói bằng lời của người dùng, không thuật ngữ;
- kiểm được bằng cách tự bấm thử trên ứng dụng;
- mô tả kết quả nhìn thấy, không mô tả cách làm.

Luôn có ít nhất một câu về tình huống **không được phép** (ví dụ "Còn dưới 2
tiếng thì không huỷ được, và có thông báo vì sao").

**Bước 3. Nói trước phần sẽ bị đụng.** Một hai câu: yêu cầu này cần sửa
những tính năng nào, màn hình nào sẽ thay đổi. Lấy từ kết quả bước 1. Một yêu
cầu có thể cần sửa vài tính năng (huỷ lịch đụng cả "Lịch của tôi" lẫn "Đặt
lịch"); kể hết ra ở đây. Những tính năng bạn kể ở bước này và người dùng đồng
ý chính là **phạm vi của yêu cầu**. Ghi nhớ danh sách này cho khoảnh khắc 2.

**Bước 4. Hỏi chốt và chờ.** Kết thúc bằng câu hỏi rõ ràng, ví dụ "Anh chốt
ba tiêu chí này chứ, hay cần sửa câu nào?". Nếu có công cụ hỏi lựa chọn bằng
nút bấm thì dùng nó. Người dùng sửa câu nào thì cập nhật rồi hỏi lại.

**Bước 5. Ghi lại và chụp trạng thái "trước".** Sau khi người dùng chốt:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" features criterion --feature dat-lich \
  --text "Khách huỷ được lịch khi còn hơn 2 tiếng trước giờ hẹn." --json
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" generate --label truoc-dat-lich-4
```

Ghi mỗi tiêu chí vào đúng tính năng mà nó nói tới; các tiêu chí của một yêu
cầu có thể nằm ở vài tính năng. Lệnh `criterion` trả về `id` của tiêu chí (ví
dụ `dat-lich-4`). Dùng `id` của tiêu chí đầu tiên vừa tạo làm đuôi cho nhãn:
`truoc-dat-lich-4` bây giờ và `sau-dat-lich-4` ở khoảnh khắc 2. Nếu yêu cầu là
một tính năng hoàn toàn mới, dùng `features add` tạo nó trước với những file
bạn dự định tạo.

Chỉ sau bước 5 mới bắt đầu sửa code.

## Khoảnh khắc 2 — Báo cáo thay đổi

Làm ngay khi sửa xong, trước khi nói "xong" với người dùng.

**Bước 1. Chụp trạng thái "sau" và đối chiếu.**

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" generate --label sau-dat-lich-4
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" features impact \
  --baseline truoc-dat-lich-4 --current sau-dat-lich-4 --json
```

**Bước 2. Gán file mới.** Nếu `unowned_changes` có file bạn vừa tạo cho yêu
cầu này, thêm chúng vào tính năng rồi chạy lại lệnh `impact`:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" features add --id dat-lich --append \
  --files "app/api/bookings/[id]/route.ts"
```

**Bước 3. Tìm bằng chứng cho từng tiêu chí vừa chốt.**

- Dự án có kiểm thử tự động chạm đúng tiêu chí: chạy nó. Nếu đạt, ghi bằng
  chứng loại `test`, ghi chú tên bài kiểm thử.
- Không có: viết cho người dùng 1–3 bước bấm thử. **Chưa ghi bằng chứng**;
  chỉ ghi loại `manual` sau khi chính người dùng nói họ đã thử và thấy đúng.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" features evidence --criterion dat-lich-4 \
  --kind manual --note "Chủ tiệm tự bấm thử ngày 15/11"
```

Bằng chứng gắn với code tại thời điểm ghi. Khi code liên quan đổi, công cụ
tự chuyển tiêu chí sang "cần kiểm lại".

**Bước 4. Viết báo cáo** theo đúng bốn phần dưới đây. Mẫu câu và một ví dụ
đầy đủ: [references/mau-bao-cao.md](references/mau-bao-cao.md).

1. **Đã làm** — 2–3 câu lời thường về điều đã thay đổi trên ứng dụng.
2. **Tiêu chí đã chốt** — mỗi tiêu chí một dòng, mở đầu bằng trạng thái:
   **Có bằng chứng**, **Cần kiểm lại** hoặc **Chưa kiểm**; kèm cách tự thử
   nếu chưa có bằng chứng.
3. **Ngoài yêu cầu** — đọc `features` trong kết quả `impact`. Trước hết
   **bỏ ra mọi tính năng thuộc phạm vi của yêu cầu** (đã chốt ở khoảnh khắc
   1, bước 3): sửa chúng là việc được nhờ, không báo ở đây và không hỏi
   "giữ hay hoàn lại". Với các tính năng còn lại, mỗi tính năng đúng một dòng:
   - `touched` là `direct`: bạn đã sửa cả phần đó dù không được yêu cầu. Nói
     thẳng đã sửa gì, và hỏi người dùng muốn giữ hay hoàn lại.
   - `touched` là `indirect`: bạn không sửa phần đó, nhưng nó dùng chung một
     đoạn code vừa đổi. Nếu nó có tiêu chí mang `status_after` là
     `needs_recheck` thì liệt kê các tiêu chí ấy; nếu không có thì chỉ nói
     nó dùng chung phần vừa sửa.
   - `touched` là `none`: gộp tất cả vào một dòng "… không bị đụng tới."
   - `behaviour_changed` là `false`: file có bị sửa nhưng cách chạy không
     đổi (chỉ đổi cách trình bày code); nói vậy, không báo động.
   - Mỗi mục trong `unowned_changes` (phần dùng chung, chưa thuộc tính năng
     nào): một câu nói đã đổi gì và những tính năng nào đang dùng nó.
   - Không có gì ngoài phạm vi bị đụng: viết "Không đụng tới phần nào khác."
4. **Việc của anh/chị** — một câu: cần tự thử những điểm nào rồi báo lại.

Cuối báo cáo ghi một dòng: phần "Tiêu chí" và "Ngoài yêu cầu" do công cụ đối
chiếu code trước và sau; phần "Đã làm" là bạn tóm tắt.

**Bước 5. Khi người dùng báo đã thử.** Ghi bằng chứng `manual` cho đúng các
tiêu chí họ nói đã thử, rồi xác nhận lại một câu. Nếu họ muốn hoàn lại phần
ngoài yêu cầu: hoàn lại, rồi làm lại từ bước 1.

## Khoảnh khắc 3 — Bản đồ ứng dụng

Làm khi người dùng hỏi ứng dụng có gì, phần nào đã kiểm, phần nào chưa.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py" features status --json
```

Trình bày mỗi tính năng một dòng: tên, có mấy màn hình (gọi bằng tên người
dùng hiểu, không dùng đường dẫn file), và số tiêu chí theo ba trạng thái.
Sau đó nêu những phần chưa thuộc tính năng nào, cũng bằng lời thường ("trang
chủ", "phần kết nối dữ liệu dùng chung"). Mời họ nói tên tính năng nếu muốn
xem kỹ hơn; lúc đó mới liệt kê từng tiêu chí và trạng thái.

Nếu người dùng muốn nhìn sơ đồ, chạy `generate` rồi mở
`docs/function-map/index.html`. Đây là mức chi tiết cho người tò mò; đừng
đưa ra khi không được hỏi.

## Cách gọi ba trạng thái

| Công cụ trả về | Nói với người dùng | Nghĩa là |
|---|---|---|
| `verified` | **Có bằng chứng** | Đã kiểm, và code liên quan chưa đổi từ lúc đó |
| `needs_recheck` | **Cần kiểm lại** | Đã từng kiểm, nhưng code liên quan vừa đổi |
| `unchecked` | **Chưa kiểm** | Chưa ai kiểm lần nào |

## Khi công cụ không chạy được

Máy không có Python, hoặc lệnh báo lỗi mà bạn không sửa được:

- Vẫn làm khoảnh khắc 1 bằng lời: viết tiêu chí, chờ chốt.
- Sau khi sửa, vẫn viết báo cáo bốn phần, nhưng mở đầu bằng đúng câu này:
  "Lần này tôi chưa đối chiếu bằng máy được, nên phần dưới là theo những gì
  tôi tự ghi nhận." Mọi tiêu chí khi đó là **Chưa kiểm**.
- Nói một lần, ngắn gọn, lý do và cách khắc phục (ví dụ cần cài Python). Chỉ
  hướng dẫn cài khi người dùng muốn.

## Khi làm việc trên file tải lên

Nếu người dùng tải file hoặc file nén của dự án lên thay vì mở một thư mục
trên máy: giải nén, chạy công cụ trong thư mục đó, và khi trả lại file đã
sửa thì kèm cả thư mục `.cbm/`. Nhắc họ giữ `.cbm/` cùng dự án, vì tiêu chí
và bằng chứng nằm trong đó.
