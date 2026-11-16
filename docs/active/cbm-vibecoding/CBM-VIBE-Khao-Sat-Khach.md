# CBM-VIBE — Khảo sát khách (3 câu, 1 phút)

> **Mục đích:** biết khách đang làm app bằng Claude ở đâu, để quyết định đầu tư tầng nào trước (skill, hook hay mod).
> **Cách dùng:** dán nguyên phần "Nội dung gửi khách" vào Google Forms, Zalo hoặc email. Ba câu đầu là bắt buộc, hai câu sau là tuỳ chọn.

## Nội dung gửi khách

**Bạn đang làm app bằng Claude như thế nào?**

Chúng tôi đang làm một công cụ giúp bạn biết AI vừa sửa gì trong app và có làm hỏng thứ đang chạy không. Ba câu hỏi dưới đây giúp chúng tôi làm đúng thứ bạn cần. Trả lời mất khoảng một phút.

**1. Bạn làm app bằng Claude ở đâu là chính?** (chọn một)

- Trò chuyện thường trên claude.ai hoặc app Claude
- Cowork trong app Claude trên máy tính
- Tab Code trong app Claude trên máy tính
- Claude Code trong cửa sổ dòng lệnh (terminal)
- Công cụ khác: ……

**2. App của bạn hiện gồm bao nhiêu file?** (chọn một)

- Một file (ví dụ một trang HTML hoặc một artifact)
- Vài file đến vài chục file
- Rất nhiều file, tôi không đếm được
- Tôi không biết

**3. Bạn làm việc trên máy gì?** (chọn một)

- Windows
- Mac
- Khác: ……

**4. (Tuỳ chọn) Lần gần nhất AI sửa app làm hỏng một thứ đang chạy, bạn phát hiện bằng cách nào?**

……

**5. (Tuỳ chọn) Bạn có sẵn lòng thử một báo cáo mẫu trong 20 phút không?** Nếu có, xin để lại Zalo hoặc email: ……

## Đọc kết quả

| Câu | Nếu đa số trả lời | Thì ưu tiên |
|---|---|---|
| 1 | Chat | Tầng 1 (skill); báo cáo tự động chưa làm được ở Chat |
| 1 | Cowork hoặc tab Code | Tầng 2 (hook) ngay sau tầng 1 |
| 1 | Terminal | Giữ nguyên thứ tự; nhóm này cài được mọi tầng |
| 2 | Một file | Giá trị của CBM thấp; cân nhắc lại nhóm mục tiêu |
| 2 | Vài file trở lên | Đúng nhóm CBM-VIBE nhắm tới |
| 3 | Windows | Phải giải bài toán máy không có Python trước khi phát hành |

Câu 5 dùng để chọn 5 người cho phép thử báo cáo mẫu (xem mục "Giả định rủi ro nhất" trong [bản concept](CBM-VIBE-Concept.md)).
