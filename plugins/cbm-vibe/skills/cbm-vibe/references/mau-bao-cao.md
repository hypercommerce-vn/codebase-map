# Mẫu câu và một ví dụ đầy đủ

Ví dụ dùng một ứng dụng sổ đặt lịch của tiệm tóc. Chủ tiệm không rành kỹ
thuật. Xưng hô theo cách người dùng tự xưng; ở đây là "anh". Bố cục theo bản
thiết kế đã duyệt (`CBM-VIBE-Design-Preview.html`); giữ đúng tên các mục.

## Mục lục

- [Khoảnh khắc 1: chốt yêu cầu](#khoảnh-khắc-1-chốt-yêu-cầu)
- [Khoảnh khắc 2: báo cáo thay đổi](#khoảnh-khắc-2-báo-cáo-thay-đổi)
- [Khoảnh khắc 3: bản đồ ứng dụng](#khoảnh-khắc-3-bản-đồ-ứng-dụng)
- [Khi người dùng hỏi "chi tiết"](#khi-người-dùng-hỏi-chi-tiết)
- [Những câu không được viết](#những-câu-không-được-viết)

## Khoảnh khắc 1: chốt yêu cầu

Người dùng: "Cho khách tự huỷ lịch được không em, miễn là báo trước 2 tiếng."

> **Em hiểu yêu cầu của anh như sau.** Làm xong thì phải đúng 3 điều này:
>
> 1. Ở màn hình "Lịch của tôi", mỗi lịch hẹn sắp tới có nút **Huỷ lịch**.
> 2. Còn hơn 2 tiếng trước giờ hẹn: bấm huỷ được, và khung giờ đó trống trở
>    lại cho khách khác.
> 3. Còn dưới 2 tiếng: không huỷ được, và khách thấy lời giải thích.
>
> **Việc này liên quan tới đâu trong ứng dụng**
> - **Sẽ đụng tới** Đặt lịch: màn hình "Lịch của tôi".
> - **Có thể bị ảnh hưởng theo** Nhắc lịch, vì chạy chung phần xử lý lịch
>   hẹn. Sửa xong em sẽ báo anh kiểm lại.
> - **Không đụng tới** Danh sách khách, Báo cáo doanh thu, Đăng nhập.
>
> Anh chốt ba điều này chứ, hay cần sửa câu nào?

Sau khi người dùng chốt và bạn đã chụp trạng thái "trước":

> Em đã lưu lại trạng thái ứng dụng trước khi sửa, để so sánh sau. Em bắt
> đầu làm đây.

Đặc điểm cần giữ: mỗi câu tự bấm thử được; có một câu về tình huống không
được phép (câu 3); không có tên file hay thuật ngữ; ba dòng "liên quan tới
đâu" lấy từ công cụ (dòng giữa là trường `affects`); kết thúc bằng một câu
hỏi và dừng lại chờ.

Phạm vi của yêu cầu này là phần **Đặt lịch**. Ở khoảnh khắc 2, việc sửa phần
Đặt lịch không bị coi là "ngoài yêu cầu".

Nếu đây là lần đầu dùng với ứng dụng này, thêm một dòng trước các tiêu chí:

> Em đã ghi lại ứng dụng của anh gồm 5 phần: Đặt lịch, Danh sách khách, Nhắc
> lịch, Báo cáo doanh thu và Đăng nhập. Tên nào chưa đúng ý anh thì nói em sửa.

## Khoảnh khắc 2: báo cáo thay đổi

Kết quả `features impact` của ví dụ này: Đặt lịch `direct` (trong phạm vi
yêu cầu); Nhắc lịch `direct` dù không được yêu cầu, hai tiêu chí của nó
chuyển từ `verified` sang `needs_recheck`; ba tính năng còn lại `none`; một
file dùng chung bị đổi (`unowned_changes`, với `behaviour_changed` là
`false` vì chỉ thêm một khai báo kiểu). Dự án có kiểm thử tự động cho hai
tiêu chí đầu, đã chạy đạt và đã ghi bằng chứng loại `test`.

> **Còn 3 việc cần kiểm.** Làm xong cả 3 thì dùng tiếp được.
>
> **AI đã làm gì**
> Sửa 4 chỗ trong 2 tính năng.
> - **Đặt lịch:** thêm nút Huỷ lịch ở màn hình "Lịch của tôi"; thêm quy tắc
>   2 tiếng; trả khung giờ về trống khi huỷ.
> - **Nhắc lịch:** sửa phần gửi tin nhắc. Anh không yêu cầu việc này.
>
> **Đúng yêu cầu chưa**
> - Có nút Huỷ lịch ở "Lịch của tôi" — **Có bằng chứng** (kiểm thử tự động:
>   đạt)
> - Huỷ được khi còn hơn 2 tiếng, khung giờ trống trở lại — **Có bằng
>   chứng** (kiểm thử tự động: đạt)
> - Dưới 2 tiếng thì không huỷ được, có lời giải thích — **Chưa kiểm** (chưa
>   có bằng chứng nào)
>
> *Tự kiểm trong 1 phút*
> 1. Đặt thử một lịch bắt đầu sau 1 tiếng nữa.
> 2. Mở "Lịch của tôi", bấm Huỷ lịch.
> 3. Phải thấy thông báo không huỷ được, kèm lý do.
>
> Anh thử rồi báo em "đạt" hay "không đạt". Hoặc để em viết kiểm thử tự động
> cho điều này.
>
> **Có đụng gì ngoài yêu cầu không**
> - **Nhắc lịch:** em đã sửa phần gửi tin nhắc dù anh không yêu cầu. Tin
>   nhắc giờ gửi trước **12 tiếng** thay vì 24 tiếng, và lời nhắn có thêm
>   câu về việc huỷ lịch. Hai điều từng được kiểm, nay **cần kiểm lại** vì
>   code đã đổi: "Khách nhận tin nhắc trước giờ hẹn 24 tiếng" và "Tin nhắc
>   có tên khách và giờ hẹn". Anh muốn giữ thay đổi này hay để em hoàn lại?
> - Danh sách khách, Báo cáo doanh thu, Đăng nhập: không bị đụng tới.
> - Phần dùng chung: em thêm trạng thái "Đã huỷ" vào danh sách trạng thái
>   của một lịch hẹn. Chưa phần nào khác dùng tới trạng thái này.
>
> *Phần "Đúng yêu cầu chưa" và "Có đụng gì ngoài yêu cầu không" do công cụ
> đối chiếu code trước và sau khi sửa. Phần "AI đã làm gì" là em tóm tắt.*

Cách đếm dòng kết luận ở ví dụ này: 1 tiêu chí vừa chốt chưa có bằng chứng,
cộng 2 tiêu chí của Nhắc lịch vừa chuyển sang cần kiểm lại, là 3.

Khi không có gì ngoài yêu cầu, mục cuối chỉ còn một dòng:

> **Có đụng gì ngoài yêu cầu không**
> Không đụng tới phần nào khác.

Khi một tính năng khác chỉ bị ảnh hưởng gián tiếp (`indirect`):

> **Có đụng gì ngoài yêu cầu không**
> - **Nhắc lịch** chạy chung một đoạn xử lý với phần Đặt lịch, và đoạn đó
>   vừa đổi. Em không sửa gì trong phần Nhắc lịch, nhưng hai điều anh đã
>   kiểm ở đó giờ **cần kiểm lại**: …

Khi mọi thứ đã có bằng chứng:

> **Dùng tiếp được.**

Khi một bài kiểm thử không đạt, hoặc người dùng báo "không đạt":

> **Có thứ đang hỏng:** bấm huỷ lịch sát giờ vẫn huỷ được. Em sửa ngay rồi
> báo lại.

Khi người dùng báo đã thử:

> Em đã ghi nhận anh thử và thấy đúng. Điều thứ ba giờ **có bằng chứng**.
> Còn 2 việc cần kiểm, đều ở phần Nhắc lịch.

## Khoảnh khắc 3: bản đồ ứng dụng

> **Ứng dụng của anh hiện có 5 phần**
>
> 1. **Đặt lịch** — 2 màn hình (đặt lịch, lịch của tôi). 3 điều có bằng
>    chứng.
> 2. **Danh sách khách** — 1 màn hình. 2 điều có bằng chứng.
> 3. **Nhắc lịch** — chạy ngầm, không có màn hình. 2 điều **cần kiểm lại**.
> 4. **Báo cáo doanh thu** — 1 màn hình. 1 điều chưa kiểm.
> 5. **Đăng nhập** — 1 màn hình. 1 điều có bằng chứng.
>
> **Chưa thuộc phần nào:** trang chủ và phần kết nối dữ liệu dùng chung.
>
> Anh muốn xem kỹ phần nào thì nói tên, em liệt kê từng điều đã chốt.

## Khi người dùng hỏi "chi tiết"

Lúc này mới được nêu tên file và đoạn xử lý, mỗi cái kèm một câu giải thích:

> Ở phần Nhắc lịch em đã đổi hai chỗ trong file `lib/reminders.ts` (nơi chứa
> phần gửi tin nhắc):
> - Con số quy định gửi trước bao lâu: từ 24 tiếng xuống 12 tiếng.
> - Đoạn soạn nội dung tin nhắn (`buildReminderMessage`): thêm một câu về
>   việc huỷ lịch.

## Những câu không được viết

| Đừng viết | Vì sao | Viết thế này |
|---|---|---|
| "Tính năng đã chạy đúng." | Chưa ai kiểm | "Điều này hiện **chưa kiểm**; cách thử như sau…" |
| "Thay đổi này an toàn." | Công cụ chỉ đối chiếu code | "Không đụng tới phần nào khác." |
| "Hoàn thành 80%." | Dòng kết luận chỉ có ba mức | "Còn 2 việc cần kiểm." |
| "Em đã refactor `cancelBooking` trong `lib/bookings.ts`." | Thuật ngữ và tên file | "Em đã thêm phần xử lý huỷ lịch." |
| "Impact zone: 3 node, độ phủ 82%." | Số liệu kỹ thuật | Bỏ hẳn, trừ khi được hỏi chi tiết |
| "Anh chạy `npm test` giúp em." | Người dùng không chạy lệnh | Tự chạy, rồi báo kết quả |
