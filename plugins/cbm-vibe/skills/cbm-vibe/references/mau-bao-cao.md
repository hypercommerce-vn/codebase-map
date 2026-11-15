# Mẫu câu và một ví dụ đầy đủ

Ví dụ dùng một ứng dụng sổ đặt lịch của tiệm tóc. Chủ tiệm không rành kỹ
thuật. Xưng hô theo cách người dùng tự xưng; ở đây là "anh".

## Mục lục

- [Khoảnh khắc 1: chốt yêu cầu](#khoảnh-khắc-1-chốt-yêu-cầu)
- [Khoảnh khắc 2: báo cáo thay đổi](#khoảnh-khắc-2-báo-cáo-thay-đổi)
- [Khoảnh khắc 3: bản đồ ứng dụng](#khoảnh-khắc-3-bản-đồ-ứng-dụng)
- [Khi người dùng hỏi "chi tiết"](#khi-người-dùng-hỏi-chi-tiết)
- [Những câu không được viết](#những-câu-không-được-viết)

## Khoảnh khắc 1: chốt yêu cầu

Người dùng: "Cho khách tự huỷ lịch được không em, miễn là báo trước 2 tiếng."

> Em hiểu yêu cầu của anh như sau. Làm xong thì ba điều này phải đúng:
>
> 1. Trong màn hình "Lịch của tôi", mỗi lịch sắp tới có nút **Huỷ lịch**.
> 2. Bấm huỷ khi còn hơn 2 tiếng trước giờ hẹn thì lịch chuyển sang "Đã
>    huỷ", và giờ đó trống lại cho khách khác đặt.
> 3. Còn dưới 2 tiếng thì không huỷ được, và khách thấy thông báo vì sao.
>
> Việc này thuộc phần **Đặt lịch**. Màn hình "Lịch của tôi" sẽ thay đổi;
> màn hình đặt lịch mới thì không.
>
> Anh chốt ba điều này chứ, hay cần sửa câu nào?

Đặc điểm cần giữ: mỗi câu tự bấm thử được; có một câu về tình huống không
được phép (câu 3); không có tên file hay thuật ngữ; kết thúc bằng một câu
hỏi và dừng lại chờ.

Phạm vi của yêu cầu này là phần **Đặt lịch**. Ở khoảnh khắc 2, việc sửa phần
Đặt lịch không được nêu trong mục "Ngoài yêu cầu".

Nếu đây là lần đầu dùng với ứng dụng này, thêm một dòng trước các tiêu chí:

> Em đã ghi lại ứng dụng của anh gồm 5 phần: Đặt lịch, Danh sách khách, Nhắc
> lịch, Báo cáo doanh thu và Đăng nhập. Tên nào chưa đúng ý anh thì nói em sửa.

## Khoảnh khắc 2: báo cáo thay đổi

Kết quả `features impact` của ví dụ này: Đặt lịch `direct` (trong phạm vi
yêu cầu, nên không nêu ở mục "Ngoài yêu cầu"); Nhắc lịch `direct` dù không
được yêu cầu; ba tính năng còn lại `none`; một file dùng chung bị đổi
(`unowned_changes`).

> **Đã làm**
> Khách giờ huỷ được lịch của mình trong màn hình "Lịch của tôi". Khi huỷ,
> giờ đó trống lại. Lịch còn dưới 2 tiếng thì không huỷ được.
>
> **Tiêu chí anh đã chốt**
> Ba điều anh đã kiểm trước đây ở phần Đặt lịch giờ **cần kiểm lại**, vì
> phần này vừa được sửa theo yêu cầu. Ba điều mới:
> - **Chưa kiểm** — Mỗi lịch sắp tới có nút Huỷ lịch. *Cách thử:* mở "Lịch
>   của tôi", xem lịch nào cũng có nút.
> - **Chưa kiểm** — Huỷ khi còn hơn 2 tiếng thì lịch thành "Đã huỷ" và giờ
>   trống lại. *Cách thử:* đặt một lịch cho ngày mai, huỷ nó, rồi vào màn
>   hình đặt lịch xem giờ đó chọn lại được không.
> - **Chưa kiểm** — Còn dưới 2 tiếng thì không huỷ được. *Cách thử:* đặt một
>   lịch cách bây giờ 1 tiếng, bấm huỷ, xem có thông báo không.
>
> **Ngoài yêu cầu**
> - **Nhắc lịch:** em đã sửa cả phần này dù anh không yêu cầu. Tin nhắc giờ
>   gửi trước **12 tiếng** thay vì 24 tiếng, và lời nhắn có thêm câu về việc
>   huỷ lịch. Anh muốn giữ thay đổi này hay để em hoàn lại như cũ?
> - Hai điều anh đã kiểm trước đây ở phần Nhắc lịch giờ **cần kiểm lại**:
>   "Khách nhận tin nhắc trước giờ hẹn 24 tiếng" và "Tin nhắc có tên khách
>   và giờ hẹn".
> - Danh sách khách, Báo cáo doanh thu và Đăng nhập: không bị đụng tới.
> - Phần dùng chung: em thêm trạng thái "Đã huỷ" vào danh sách trạng thái
>   của một lịch hẹn. Chưa phần nào khác dùng tới trạng thái này.
>
> **Việc của anh**
> Thử ba điểm ở trên rồi báo em điểm nào thấy đúng, và cho em biết giữ hay
> hoàn lại thay đổi ở phần Nhắc lịch.
>
> *Phần "Tiêu chí" và "Ngoài yêu cầu" do công cụ đối chiếu code trước và sau
> khi sửa. Phần "Đã làm" là em tóm tắt.*

Khi không có gì ngoài yêu cầu, phần đó chỉ còn một dòng:

> **Ngoài yêu cầu**
> Không đụng tới phần nào khác.

Khi một tính năng khác chỉ bị ảnh hưởng gián tiếp (`indirect`):

> **Ngoài yêu cầu**
> - **Nhắc lịch** dùng chung một đoạn xử lý với phần Đặt lịch, và đoạn đó
>   vừa đổi. Em không sửa gì trong phần Nhắc lịch, nhưng hai điều anh đã
>   kiểm ở đó giờ **cần kiểm lại**: …

Khi người dùng báo đã thử:

> Em đã ghi nhận anh thử hai điểm đầu và thấy đúng. Hai tiêu chí đó giờ
> **có bằng chứng**. Điểm thứ ba vẫn **chưa kiểm**.

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
> Ngoài ra có trang chủ và phần kết nối dữ liệu dùng chung, chưa xếp vào
> phần nào.
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
| "Tính năng đã chạy đúng." | Chưa ai kiểm | "Ba điều anh chốt hiện **chưa kiểm**; cách thử như sau…" |
| "Thay đổi này an toàn." | Công cụ chỉ đối chiếu code | "Không đụng tới phần nào khác." |
| "Em đã refactor `cancelBooking` trong `lib/bookings.ts`." | Thuật ngữ và tên file | "Em đã thêm phần xử lý huỷ lịch." |
| "Impact zone: 3 node, độ phủ 82%." | Số liệu kỹ thuật | Bỏ hẳn, trừ khi được hỏi chi tiết |
| "Anh chạy `npm test` giúp em." | Người dùng không chạy lệnh | Tự chạy, rồi báo kết quả |
