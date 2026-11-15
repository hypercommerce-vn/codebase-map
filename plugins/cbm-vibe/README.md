# CBM-VIBE

Dành cho người tự làm ứng dụng bằng cách nhờ Claude viết code mà không rành
kỹ thuật. Sau mỗi lần nhờ sửa, bạn biết ba điều bằng tiếng Việt thường:
**Claude đã làm gì**, **có đúng điều bạn yêu cầu không**, và **có đụng tới
thứ đang chạy không**.

## Nó làm gì

| Khi nào | Bạn thấy gì |
|---|---|
| Trước khi Claude sửa | Claude nhắc lại yêu cầu thành 2–4 điều phải đúng khi làm xong, và chờ bạn chốt |
| Ngay sau khi sửa | Báo cáo: đã làm gì; từng điều đã chốt đang "có bằng chứng", "cần kiểm lại" hay "chưa kiểm"; có đụng tới phần nào bạn không yêu cầu |
| Bất cứ lúc nào bạn hỏi | Ứng dụng có những phần nào, mỗi phần gồm màn hình nào, đã kiểm tới đâu |

Claude không tự nói một điều là "đúng". Một điều chỉ được ghi "có bằng
chứng" khi bạn đã tự bấm thử và xác nhận, hoặc một bài kiểm thử tự động đã
chạy đạt. Khi phần code liên quan thay đổi, bằng chứng cũ tự hết hạn và điều
đó chuyển sang "cần kiểm lại".

## Cách dùng

Không có lệnh nào phải nhớ. Cứ nói với Claude như bình thường:

- "Cho khách tự huỷ lịch được không, miễn là báo trước 2 tiếng."
- "Em vừa sửa những gì vậy?"
- "Ứng dụng của anh giờ có những phần nào?"

## Cài đặt

Không cần mở terminal.

1. Mở **Customize > Plugins** trong Claude (trên web hoặc ứng dụng máy tính).
2. Chọn **Add > Upload plugin** và chọn file `cbm-vibe-plugin.zip`.
3. Mở một cuộc trò chuyện mới và nhờ Claude sửa ứng dụng của bạn.

Trong Claude Code có thể thử nhanh bằng `claude --plugin-dir <thư mục plugin>`.

## Cần gì trên máy

Python 3.9 trở lên (máy Mac thường có sẵn sau khi cài Command Line Tools;
Windows cần cài thêm). Không cần cài gói nào khác: công cụ đối chiếu code nằm
sẵn trong plugin. Khi máy không có Python, Claude vẫn chốt yêu cầu và viết
báo cáo, nhưng ghi rõ là chưa đối chiếu bằng máy.

Đọc được mã nguồn TypeScript, JavaScript và Python. Nhận ra màn hình và điểm
nhận dữ liệu theo quy ước của Next.js.

## Dữ liệu

Plugin không gửi code hay dữ liệu của bạn đi đâu. Công cụ chạy ngay trên máy
(hoặc trong môi trường chạy code của Claude) và chỉ ghi vào thư mục dự án:

- `.cbm/features.json` — các phần của ứng dụng, những điều đã chốt, bằng chứng
- `.codebase-map-cache/` — ảnh chụp code trước và sau mỗi lần sửa
- `docs/function-map/` — sơ đồ ứng dụng dạng trang web

Hãy giữ thư mục `.cbm/` cùng với dự án.

## Giới hạn hiện tại

- Công cụ đọc code, không chạy ứng dụng. Nó biết phần nào bị sửa và phần nào
  phụ thuộc phần đó; nó không biết ứng dụng chạy có đúng không.
- Nó không thấy hai phần cùng dùng chung một bảng dữ liệu, và không thấy
  thay đổi ở file kiểu dáng, hình ảnh hay dữ liệu.
- Bản này trình bày bằng chữ trong cuộc trò chuyện. Báo cáo tự động sau mỗi
  lượt và khung bản đồ bên cạnh cuộc trò chuyện là các bước tiếp theo.

## Dành cho người phát triển

Mã nguồn công cụ là gói `codebase_map` ở gốc repo này. Thư mục plugin trong
repo không chứa bản sao của gói đó; bản phát hành được dựng bằng:

```bash
python3 scripts/build_cbm_vibe.py
```

Lệnh tạo `dist/cbm-vibe/` (plugin hoàn chỉnh), `dist/cbm-vibe-plugin.zip`
(để tải lên ở Customize > Plugins) và `dist/cbm-vibe-skill.zip` (riêng skill,
để tải lên ở Customize > Skills).

Giấy phép: MIT.
