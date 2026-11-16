# CBM-VIBE — Cài thử trên ba nơi dùng Claude (VIBE-105)

> **Trạng thái:** phần kiểm được bằng máy đã xong ngày 15/11/2026. Phần bấm trên giao diện chờ CEO làm; bảng kết quả ở cuối còn để trống.
> **Liên quan:** [Concept](CBM-VIBE-Concept.md) · plugin ở `plugins/cbm-vibe/` · bản dựng bằng `python3 scripts/build_cbm_vibe.py`

## Vì sao phần bấm phải do CEO làm

Cài plugin ở Chat và Cowork là cài vào **tài khoản Claude**, và plugin cài vào tài khoản sẽ tự xuất hiện trong Claude Code ở phiên kế tiếp. Skill của CBM-VIBE được viết để bật lên mỗi khi người dùng nhờ thêm hoặc sửa một tính năng. Trên tài khoản của anh, điều đó nghĩa là nó sẽ chen vào cả những phiên anh đang dùng để làm chính repo này và các dự án khác: Claude sẽ đòi chốt tiêu chí trước khi sửa code. Em không tự cài vào tài khoản của anh vì lý do đó.

Hai cách thử mà không ảnh hưởng công việc hằng ngày:

- **Thử một phiên trong Claude Code:** `claude --plugin-dir dist/cbm-vibe`. Plugin chỉ có trong phiên đó.
- **Cài vào tài khoản rồi tắt:** sau khi thử xong, vào **Customize > Plugins** và tắt CBM-VIBE.

## Đã kiểm bằng máy (15/11/2026)

| Việc | Kết quả |
|---|---|
| `claude plugin validate` trên thư mục nguồn và bản dựng (Claude Code 2.1.284) | Đạt, không cảnh báo |
| Bản dựng: 36 file, file nén plugin 207 KB, file nén skill 203 KB | Trong giới hạn 5.000 file và 200 MB |
| Cấu trúc file nén plugin: một thư mục `cbm-vibe/` ở gốc, có `.claude-plugin/plugin.json` | Đúng yêu cầu của "Upload plugin" |
| Cấu trúc file nén skill: `cbm-vibe/SKILL.md` ở gốc | Đúng yêu cầu của "Upload skill" |
| Không có thư mục `bin/` ở gốc plugin | Đúng; nếu có thì Chat và Cowork từ chối cài |
| Phần đầu file skill chỉ dùng 6 khoá được phép khi tải lên | Đúng |
| Chạy công cụ từ bản dựng bằng Python 3.9.6 có sẵn của macOS, chế độ cô lập (`-I`), không cài gì | Chạy trọn vòng trên app mẫu |
| In tiếng Việt khi đầu ra không phải UTF-8 (tình huống trên Windows) | Không lỗi |
| 43 test tự động cho plugin, gồm việc mọi lệnh ghi trong skill đều là lệnh có thật | Đạt |

**Thử với Claude thật.** Lệnh `claude -p` trên máy báo phiên đăng nhập đã hết hạn, nên em không chạy được Claude Code với plugin. Em thay bằng cách giao file skill cho một agent phụ (model Sonnet) đóng vai Claude nói chuyện với một chủ tiệm tóc, trên bản sao app mẫu:

- Lượt 1, câu "Cho khách tự huỷ lịch được không em, miễn là báo trước 2 tiếng": agent xem ứng dụng, ghi 6 tính năng, viết 4 tiêu chí bằng lời thường có một tiêu chí về tình huống không được phép, nêu phần sẽ bị đụng, hỏi chốt rồi dừng. Không có tên file hay thuật ngữ.
- Lượt 2, sau khi chốt: agent ghi tiêu chí, chụp trước, sửa code, chụp sau, đối chiếu, viết báo cáo bốn phần, không nhận là "đúng".
- Lỗi phát hiện ở lượt 2: mục "Ngoài yêu cầu" kể cả tính năng vốn nằm trong yêu cầu và hỏi "giữ hay hoàn lại". Em đã sửa chỉ dẫn trong skill (thêm định nghĩa "phạm vi của yêu cầu") rồi cho một agent mới viết lại báo cáo từ cùng trạng thái dự án: hai tính năng trong phạm vi không còn bị kể ở mục đó, tính năng bị ảnh hưởng gián tiếp được nêu một dòng, phần dùng chung được nêu một dòng.

Phép thử này cho biết chỉ dẫn trong skill dẫn tới đúng hành vi. Nó **chưa** cho biết Claude có tự bật skill từ lời người dùng hay không; việc đó chỉ kiểm được khi cài thật.

## Dự đoán theo tài liệu của Claude

Tra ngày 15/11/2026: [Plugin feature support across platforms](https://claude.com/docs/plugins/platform-support), [Plugin structure and testing](https://claude.com/docs/plugins/build), [Create custom skills](https://claude.com/docs/skills/how-to).

| | Chat | Cowork | Tab Code và Claude Code |
|---|---|---|---|
| Cài bằng file nén | Customize > Plugins > Add > Upload plugin | Như Chat (chung tài khoản) | `claude --plugin-dir`, hoặc nhận plugin đồng bộ từ tài khoản |
| Skill được nạp | Có | Có | Có |
| Công cụ chạy ở đâu | Trong môi trường chạy code của Claude; cả thư mục skill được chép vào đó | Trên máy người dùng, khi phiên Cowork chạy trên máy | Trên máy người dùng |
| Đọc được dự án | Chỉ những file người dùng tải lên cuộc trò chuyện | Thư mục người dùng chọn | Thư mục dự án |
| Cần Python trên máy | Không, dùng Python của môi trường chạy code | Có | Có |
| `${CLAUDE_SKILL_DIR}` được thay bằng đường dẫn thật | Không; skill đã ghi thêm đường dẫn tương đối `scripts/cbm.py` | Có | Có |
| Trạng thái (`.cbm/`) còn lại sau cuộc trò chuyện | Không tự còn; phải tải về cùng file đã sửa | Có, nằm trong thư mục dự án | Có |
| Hook, khung bên cạnh (tầng 2 và 3) | Không | Hook: có | Có cả hai |

Một điểm cần xem khi thử ở tab Code: quyền chạy công cụ mà skill tự cấp chỉ có hiệu lực trong lượt skill được bật. Ở các lượt sau, Claude Code có thể hỏi lại quyền chạy lệnh `python3 …/cbm.py …`. Với người không rành kỹ thuật, câu hỏi đó khó hiểu; nếu nó xuất hiện, cần ghi lại để xử lý ở tầng 2.

## Các bước thử

Dùng cùng một dự án mẫu cho cả ba nơi: một bản sao mới của app sổ đặt lịch, chưa có thay đổi nào. (Thư mục `/Users/pro/Projects/so-dat-lich-sample` tạo ngày 13/11 đã chứa sẵn bộ thay đổi huỷ lịch, nên không dùng cho phép thử này.)

**Chuẩn bị (một lần),** chạy tại thư mục gốc của repo:

```bash
python3 scripts/build_cbm_vibe.py
```

```bash
cp -R tests/fixtures/so-dat-lich/base ~/so-dat-lich-thu
```

Lệnh đầu tạo `dist/cbm-vibe-plugin.zip` và `dist/cbm-vibe-skill.zip`. Lệnh sau tạo dự án mẫu tại `~/so-dat-lich-thu`.

**Chat**

1. Vào **Customize > Plugins > Add > Upload plugin**, chọn `dist/cbm-vibe-plugin.zip`.
2. Nén thư mục dự án mẫu thành một file zip.
3. Mở cuộc trò chuyện mới, tải file zip dự án lên, rồi gõ ba câu ở mục "Ba câu để gõ".

**Cowork**

1. Plugin đã có sẵn sau bước 1 của Chat.
2. Mở một việc mới trong Cowork, chọn thư mục dự án mẫu, gõ ba câu.

**Tab Code**

1. Mở tab Code tại thư mục dự án mẫu. Plugin cài vào tài khoản sẽ tự có ở phiên mới.
2. Gõ ba câu.

Nếu chỉ muốn thử trong terminal mà không cài vào tài khoản (cần đăng nhập lại bằng `claude` rồi `/login` trước):

```bash
cd ~/so-dat-lich-thu && claude --plugin-dir /Users/pro/Projects/codebase-map/dist/cbm-vibe
```

### Ba câu để gõ

1. `Cho khách tự huỷ lịch được không em, miễn là báo trước 2 tiếng.`
   Mong đợi: Claude **chưa sửa gì**, nêu 2–4 điều phải đúng khi làm xong, hỏi anh chốt.
2. `Anh chốt. Em làm đi.`
   Mong đợi: sau khi sửa, có báo cáo bốn phần: Đã làm, Tiêu chí đã chốt (mỗi điều ghi "Chưa kiểm", "Có bằng chứng" hoặc "Cần kiểm lại"), Ngoài yêu cầu, Việc của anh.
3. `Ứng dụng của anh giờ có những phần nào?`
   Mong đợi: danh sách tính năng, mỗi tính năng có số điều theo ba trạng thái.

## Bảng kết quả (CEO điền)

Ghi "Có", "Không", hoặc mô tả ngắn điều đã thấy.

| Câu hỏi | Chat | Cowork | Tab Code |
|---|---|---|---|
| Tải file nén lên có được nhận không? | | | |
| Ở câu 1, Claude có tự dùng skill mà không cần nhắc tên không? | | | |
| Ở câu 1, Claude có dừng lại chờ chốt, chưa sửa code không? | | | |
| Công cụ có chạy được không? (báo cáo có ghi "chưa đối chiếu bằng máy" thì là không) | | | |
| Có bị hỏi quyền chạy lệnh không? Hỏi mấy lần? | | | |
| Ở câu 2, báo cáo có đủ bốn phần và đúng ba trạng thái không? | | | |
| Ở câu 3, danh sách tính năng có ra không? | | | |
| Mở lại sau một lúc, các điều đã chốt có còn không? | | | |
| Có câu nào anh đọc mà không hiểu? Chép lại câu đó | | | |

Điền xong, tầng 1 có kết luận "nơi nào chạy đủ, nơi nào thiếu gì", và danh sách việc cho tầng 2.
