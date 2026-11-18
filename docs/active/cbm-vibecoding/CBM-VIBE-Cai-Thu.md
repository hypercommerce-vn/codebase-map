# CBM-VIBE — Cài thử trên ba nơi dùng Claude (VIBE-105)

> **Trạng thái:** phần kiểm được bằng máy đã xong ngày 15/11/2026 và được chạy lại ngày 18/11/2026 trên code đã gộp với `main` (có VIBE-106). Phần bấm trên giao diện chờ CEO làm; bảng kết quả ở cuối còn để trống.
> **Liên quan:** [Concept](CBM-VIBE-Concept.md) · plugin ở `plugins/cbm-vibe/` · bản dựng bằng `python3 scripts/build_cbm_vibe.py`

## Vì sao phần bấm phải do CEO làm

Cài plugin ở Chat và Cowork là cài vào **tài khoản Claude**, và plugin cài vào tài khoản sẽ tự xuất hiện trong Claude Code ở phiên kế tiếp. Skill của CBM-VIBE được viết để bật lên mỗi khi người dùng nhờ thêm hoặc sửa một tính năng. Trên tài khoản của anh, điều đó nghĩa là nó sẽ chen vào cả những phiên anh đang dùng để làm chính repo này và các dự án khác: Claude sẽ đòi chốt tiêu chí trước khi sửa code. Em không tự cài vào tài khoản của anh vì lý do đó.

Hai cách thử mà không ảnh hưởng công việc hằng ngày:

- **Thử một phiên trong Claude Code:** `claude --plugin-dir dist/cbm-vibe`. Plugin chỉ có trong phiên đó.
- **Cài vào tài khoản rồi tắt:** sau khi thử xong, vào **Customize > Plugins** và tắt CBM-VIBE.

## Đã kiểm bằng máy (chạy lại ngày 18/11/2026)

| Việc | Kết quả |
|---|---|
| `claude plugin validate` trên thư mục nguồn và bản dựng (Claude Code 2.1.327) | Đạt. Có một gợi ý không ảnh hưởng kết quả: README chưa có dòng cài từ marketplace, vì plugin chưa nằm trong marketplace nào |
| Bản dựng: 36 file, file nén plugin 218 KB, file nén skill 214 KB | Trong giới hạn 5.000 file và 200 MB |
| Cấu trúc file nén plugin: một thư mục `cbm-vibe/` ở gốc, có `.claude-plugin/plugin.json` | Đúng yêu cầu của "Upload plugin" |
| Cấu trúc file nén skill: `cbm-vibe/SKILL.md` ở gốc | Đúng yêu cầu của "Upload skill" |
| Không có thư mục `bin/` ở gốc plugin | Đúng; nếu có thì Chat và Cowork từ chối cài |
| Phần đầu file skill chỉ dùng 6 khoá được phép khi tải lên | Đúng |
| Chạy công cụ từ bản dựng bằng Python 3.9.6 có sẵn của macOS, chế độ cô lập (`-I`), không cài gì | Chạy trọn vòng trên app mẫu |
| In tiếng Việt khi đầu ra không phải UTF-8 (tình huống trên Windows) | Không lỗi |
| Lệnh mà skill được cấp quyền sẵn chỉ làm được ba việc: đọc dự án, ghi sơ đồ và ảnh chụp vào dự án, giữ kho tính năng | Đạt. Các lệnh khác của Codebase Map bị từ chối: mở máy chủ khung bên cạnh và cài git hook (`mod`), gửi thông báo, ghi file ra đường dẫn tuỳ ý, xoá ảnh chụp. Bản dựng không chứa code của máy chủ đó |
| Cả vòng làm việc của skill chỉ ghi vào bốn chỗ trong dự án: `.cbm/`, `.codebase-map-cache/`, `.codebase-map-cache.json`, `docs/function-map/` | Đạt |
| 62 test tự động cho plugin, gồm việc mọi lệnh ghi trong skill đều là lệnh có thật và được phép chạy | Đạt |

**Thử với Claude thật.** Lệnh `claude -p` trên máy báo phiên đăng nhập đã hết hạn (thử ngày 15/11 và lại ngày 18/11), nên em chưa chạy được Claude Code với plugin. Em thay bằng cách giao thư mục skill của bản dựng cho một agent phụ (model Sonnet) đóng vai Claude nói chuyện với một chủ tiệm tóc, trên bản sao mới của app mẫu. Lần chạy ngày 18/11 dùng bản skill đã theo bố cục báo cáo trong design được duyệt:

- **Lượt 1**, câu "Cho khách tự huỷ lịch được không em, miễn là báo trước 2 tiếng": agent chia ứng dụng thành 6 phần, viết 4 điều phải đúng bằng lời thường (một điều về tình huống không được phép), nêu ba dòng "Sẽ đụng tới", "Có thể bị ảnh hưởng theo", "Không đụng tới", hỏi chốt rồi dừng. Chưa sửa file nào. Không có tên file hay thuật ngữ.
- **Lượt 2**, sau khi chốt: agent ghi 4 tiêu chí vào đúng ba phần, chụp trước, sửa 5 file, chụp sau, đối chiếu, rồi viết báo cáo: dòng kết luận "Còn 4 việc cần kiểm. Làm xong thì dùng tiếp được.", ba mục đúng tên và đúng thứ tự, các bước "Tự kiểm trong 1 phút". Cả 4 điều ghi "Chưa kiểm"; không ghi bằng chứng nào, vì chưa ai thử.
- **Lượt 3**, câu "Ứng dụng của chị giờ có những phần nào?": 6 phần, mỗi phần kèm màn hình và số điều theo trạng thái, và câu "Em chưa nói được là chúng chạy tốt hay không" cho ba phần chưa có điều nào.
- Em tự chạy lại lệnh đối chiếu trên thư mục đó. Kết quả khớp với báo cáo: hai phần bị sửa trực tiếp, "Nhắc lịch" bị ảnh hưởng gián tiếp, ba phần không bị đụng, một file dùng chung chỉ đổi khai báo kiểu.

Sau ba lượt, em hỏi agent ngoài vai: đã chạy những lệnh nào, chỉ dẫn nào khó theo. Bốn điều đáng kể, đã sửa trong PR #151:

| Điều lộ ra | Đã sửa thế nào |
|---|---|
| Hai màn hình của hai phần cùng gọi một điểm nhận dữ liệu; agent chỉ ghi điểm đó vào một phần. Em thử lại: sửa phần xử lý đứng sau thì điều đã kiểm của phần kia **vẫn ghi "Có bằng chứng"**, tức là báo an toàn sai | Skill nói rõ: ghi vào cả hai phần. Có test ghi lại cả lỗ hổng lẫn cách khắc phục |
| Agent kết luận một file dùng chung "không làm đổi cách chạy" từ một trường không đủ để nói vậy (lần này tình cờ đúng) | Công cụ trả thêm trường `behaviour_changed` cho file dùng chung; skill chỉ cho nói câu đó khi trường này là `false` |
| Agent cất lệnh vào biến shell (lỗi trên máy Mac) và nối lệnh bằng dấu gạch đứng. Trong Claude thật, lệnh viết khác mẫu sẽ làm hiện câu hỏi cấp quyền | Skill yêu cầu mỗi lần gọi là một lệnh viết đầy đủ |
| "Sửa 5 chỗ trong 3 phần": skill chưa nói đếm cái gì | Skill định nghĩa cách đếm |

Ba lượt trên chạy trước khi có bốn sửa đổi này; em chưa chạy lại sau khi sửa.

Agent cũng tự nhận ba câu nó viết không dựa trên kết quả công cụ (ví dụ "Nhắc lịch chạy ngầm", trong khi code chỉ ghi tin nhắn ra nhật ký và chưa có gì hẹn giờ chạy), và hai điều nó thấy trong code nhưng không báo người dùng: dữ liệu mất khi khởi động lại, và ai biết mã lịch hẹn cũng huỷ được lịch đó. Skill hiện không yêu cầu báo các rủi ro loại này; đây là việc cần cân nhắc cho tầng sau.

Lần chạy ngày 15–16/11 (bản skill trước) từng lộ một lỗi: mục cuối của báo cáo kể cả phần vốn nằm trong yêu cầu và hỏi "giữ hay hoàn lại". Lỗi đó đã sửa bằng định nghĩa "phạm vi của yêu cầu"; lần chạy ngày 18/11 không lặp lại.

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

**Chuẩn bị (một lần).** Trên máy của anh, ba file sau đã được dựng sẵn ngày 18/11 từ code của PR #151, nằm trong thư mục `dist/` của dự án (thư mục này không đưa lên git):

- `dist/cbm-vibe-plugin.zip` — plugin để tải lên
- `dist/cbm-vibe-skill.zip` — riêng skill, dùng khi chỉ muốn tải skill
- `dist/so-dat-lich-thu.zip` — dự án mẫu sạch

Giải nén dự án mẫu ra thư mục nhà:

```bash
unzip -o /Users/pro/Projects/codebase-map/dist/so-dat-lich-thu.zip -d ~
```

Lệnh này tạo `~/so-dat-lich-thu`. Khi cần dựng lại file nén plugin sau này, chạy lệnh dưới tại thư mục gốc của repo; nó chỉ chạy được khi PR #151 đã vào `main` và thư mục đang ở nhánh `main`:

```bash
python3 scripts/build_cbm_vibe.py
```

**Chat**

1. Vào **Customize > Plugins > Add > Upload plugin**, chọn `dist/cbm-vibe-plugin.zip`.
2. Mở cuộc trò chuyện mới, tải file `dist/so-dat-lich-thu.zip` lên, rồi gõ ba câu ở mục "Ba câu để gõ".

**Cowork**

1. Plugin đã có sẵn sau bước 1 của Chat.
2. Mở một việc mới trong Cowork, chọn thư mục `~/so-dat-lich-thu`, gõ ba câu.

**Tab Code**

1. Mở tab Code tại thư mục `~/so-dat-lich-thu`. Plugin cài vào tài khoản sẽ tự có ở phiên mới.
2. Gõ ba câu.

Thử ở Cowork và tab Code trên cùng một thư mục thì lần sau sẽ thấy các điều đã chốt của lần trước. Muốn bắt đầu lại từ đầu, giải nén file dự án mẫu ra một thư mục khác.

Nếu chỉ muốn thử trong terminal mà không cài vào tài khoản (cần đăng nhập lại bằng `claude` rồi `/login` trước):

```bash
cd ~/so-dat-lich-thu && claude --plugin-dir /Users/pro/Projects/codebase-map/dist/cbm-vibe
```

### Ba câu để gõ

1. `Cho khách tự huỷ lịch được không em, miễn là báo trước 2 tiếng.`
   Mong đợi: Claude **chưa sửa gì**, nêu 2–4 điều phải đúng khi làm xong, nói việc này đụng tới phần nào của ứng dụng, rồi hỏi anh chốt.
2. `Anh chốt. Em làm đi.`
   Mong đợi: sau khi sửa, có báo cáo mở đầu bằng một dòng kết luận ("Dùng tiếp được", "Còn N việc cần kiểm…" hoặc "Có thứ đang hỏng…"), rồi ba mục theo thứ tự: **AI đã làm gì**, **Đúng yêu cầu chưa** (mỗi điều ghi "Có bằng chứng", "Cần kiểm lại" hoặc "Chưa kiểm", kèm các bước "Tự kiểm trong 1 phút"), **Có đụng gì ngoài yêu cầu không**.
3. `Ứng dụng của anh giờ có những phần nào?`
   Mong đợi: danh sách các phần, mỗi phần có số điều theo ba trạng thái.

## Bảng kết quả (CEO điền)

Ghi "Có", "Không", hoặc mô tả ngắn điều đã thấy.

| Câu hỏi | Chat | Cowork | Tab Code |
|---|---|---|---|
| Tải file nén lên có được nhận không? | | | |
| Ở câu 1, Claude có tự dùng skill mà không cần nhắc tên không? | | | |
| Ở câu 1, Claude có dừng lại chờ chốt, chưa sửa code không? | | | |
| Công cụ có chạy được không? (báo cáo có ghi "chưa đối chiếu bằng máy" thì là không) | | | |
| Có bị hỏi quyền chạy lệnh không? Hỏi mấy lần? | | | |
| Ở câu 2, báo cáo có dòng kết luận, đủ ba mục và đúng ba trạng thái không? | | | |
| Ở câu 3, danh sách các phần có ra không? | | | |
| Mở lại sau một lúc, các điều đã chốt có còn không? | | | |
| Có câu nào anh đọc mà không hiểu? Chép lại câu đó | | | |

Điền xong, tầng 1 có kết luận "nơi nào chạy đủ, nơi nào thiếu gì", và danh sách việc cho tầng 2.
