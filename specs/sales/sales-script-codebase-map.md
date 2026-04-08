# KỊCH BẢN SALE — Codebase Map cho CTO công ty Software Dev
> **Mục tiêu:** CTO cài Codebase Map free trên ≥ 1 repo trong vòng 48 giờ sau buổi nói chuyện
> **Phụ mục tiêu:** Gieo hạt Codebase Memory (paid) cho vòng sale tiếp theo
> **Độ dài buổi call:** 20-30 phút
> **Người nói:** CEO Đoàn Đình Tỉnh (hoặc Sales Lead)
> **Ngày:** 07/04/2026

---

## 0. Triết lý sale cho hướng này

**KHÔNG bán tool.** Codebase Map là free — không có gì để "bán" theo nghĩa tiền. Thứ anh thật sự sale là:

1. **Thời gian** của CTO (họ đồng ý cài + dùng thử)
2. **Sự tin tưởng** (họ tin HC là người hiểu vấn đề codebase của họ)
3. **Cơ hội vòng 2** (họ sẽ nghe anh pitch Codebase Memory sau 2-4 tuần)

Vì vậy kịch bản này giống **"discovery call"** của consultant hơn là **"sale pitch"** của salesperson. Nguyên tắc vàng: **Hỏi nhiều hơn nói. Để CTO tự nói ra pain, mình chỉ gật đầu và đưa tool.**

---

## 1. Chuẩn bị trước buổi call (5 phút)

### 1.1 Research CTO + công ty
- LinkedIn CTO: vai trò, công ty hiện tại, công ty cũ
- GitHub công ty (nếu có public repo): ngôn ngữ chính, số repo, cỡ codebase lớn nhất
- Website công ty: sản phẩm, số năm hoạt động, estimated team size

### 1.2 3 giả thiết cần validate
Trước buổi call, viết ra 3 giả thiết về pain của họ. Ví dụ với công ty ~50 dev, 8 năm tuổi:
- **GT1:** Có ≥ 1 legacy monolith mà team sợ đụng vào
- **GT2:** Dev mới ramp-up mất ≥ 2 tuần
- **GT3:** PR review chậm vì không ai hiểu hết codebase

Trong buổi call, nhiệm vụ là **validate** 3 giả thiết này, không phải pitch tool.

### 1.3 Mở sẵn demo
- Terminal có Codebase Map đã cài
- 1 repo mẫu public để demo live (Flask source code là tốt)
- HTML preview đã render sẵn 1 tab browser, sẵn sàng share screen

---

## 2. Kịch bản chính (20-30 phút)

### 2.1 Mở đầu (2 phút)

> "Chào anh [Tên], cảm ơn anh dành thời gian. Em xin giới thiệu nhanh: em là Tỉnh, CEO Hyper Commerce. Trước đây em 8 năm PM ở Samsung, giờ em build tool cho engineering team. Hôm nay em không tới để bán gì cho anh — thật. Em muốn nghe về cách team [Tên công ty] đang làm việc với codebase, chia sẻ 1 công cụ free em nghĩ anh sẽ thấy hữu ích, và biết đâu sau này có dịp hợp tác. OK với anh không ạ?"

**Lưu ý:** Câu "em không tới để bán gì" là anchor rất mạnh. CTO nghe câu này sẽ hạ shield ngay. Phải nói thật — vì đúng là hôm nay không bán gì.

### 2.2 Discovery — 5 câu hỏi vàng (10 phút)

Hỏi tuần tự, để CTO nói nhiều. Ghi chú lại câu trả lời.

**Q1 — Context:**
> "Anh có thể kể em nghe qua về codebase chính của team mình không? Cỡ bao nhiêu dòng, bao nhiêu dev đang làm, tuổi repo bao nhiêu năm rồi?"

*(Mục tiêu: Hiểu scale. CTO nói càng chi tiết càng tốt.)*

**Q2 — Onboarding pain:**
> "Khi có 1 dev mới join team, trung bình mất bao lâu để họ làm được task đầu tiên độc lập, không cần senior kèm?"

*(Mục tiêu: Validate GT2. Câu trả lời thường là 2 tuần → 1 tháng. Bất kỳ con số > 1 tuần đều là pain rõ.)*

**Q3 — Legacy fear:**
> "Trong codebase hiện tại, có module nào mà cả team ngại đụng vào không? Kiểu ai sửa vô là bug phát sinh chỗ khác, hoặc không ai hiểu rõ nó làm gì?"

*(Mục tiêu: Validate GT1. 9/10 CTO gật đầu ngay.)*

**Q4 — AI adoption:**
> "Team anh đang dùng Cursor hay Claude Code không? Nếu có thì anh thấy chất lượng code AI sinh ra có đủ đúng convention team mình không, hay thường phải sửa lại nhiều?"

*(Mục tiêu: Gieo hạt Codebase Memory. Câu trả lời thường là "AI không hiểu pattern team" → đây là pain cho vòng sale 2.)*

**Q5 — Visualization:**
> "Hiện tại khi anh muốn hiểu 1 module lạ trong repo, anh làm gì? Đọc code trực tiếp, hỏi tác giả, hay có tool gì hỗ trợ không?"

*(Mục tiêu: Dẫn dắt tự nhiên sang Codebase Map — vì họ thường trả lời "đọc code + hỏi người".)*

### 2.3 Chuyển tiếp — gieo tool (1 phút)

Sau khi CTO trả lời xong 5 câu, anh nói:

> "Cảm ơn anh đã chia sẻ. Những gì anh vừa nói em nghe quen lắm — vì chính HC cũng từng gặp y chang. Team em cũng có 1 module PayGate mà ai cũng ngại. Dev mới cũng mất 2 tuần ramp-up. Em build Codebase Map chính là để giải 1 phần vấn đề đó — nó tự parse toàn bộ Python hoặc soon là TypeScript, vẽ ra graph tương tác, chỉ cho biết ai gọi ai, ai depend vào ai, module nào là trung tâm. Chạy 1 lệnh, 30 giây là ra HTML xem được trên browser. Em demo anh xem nhanh 2 phút nhé?"

### 2.4 Demo (5 phút)

**Nguyên tắc demo:** Không hướng dẫn, không đọc slide. Share screen, chạy thật, nói ngắn.

```bash
# 1. Cài (10 giây)
pip install codebase-map

# 2. Chạy trên repo Flask mẫu (20 giây)
cd flask-sample
codebase-map generate

# 3. Mở HTML (instant)
open graph.html
```

**Kịch bản nói khi demo:**

> "Đây là codebase Flask mẫu. Em chạy `codebase-map generate` — nó vừa scan xong 300 file Python, parse AST, build graph, xuất HTML."

*(Mở HTML)*

> "Ở đây anh thấy mỗi node là 1 function/class, màu theo layer (route/service/model), size theo số connection. Em click 1 node..."

*(Click bất kỳ node nào)*

> "...nó highlight toàn bộ function gọi nó và function nó gọi. Anh có thể search tên, filter theo layer, zoom cluster."

*(Dùng search box gõ tên 1 hàm)*

> "Cái này offline hoàn toàn, không gửi code đi đâu hết. Anh cài xong chạy trên máy anh, file HTML là static, commit vô git hoặc share cho dev mới đều được."

**DỪNG Ở ĐÂY.** Không demo thêm. Demo dài là phản tác dụng — CTO mất hứng.

### 2.5 Đối tượng hóa — "điều này giúp anh thế nào" (3 phút)

Quay lại 5 câu trả lời của CTO ở Discovery, link tool với pain cụ thể của họ:

> "Quay lại chuyện anh nói module PayGate không ai dám đụng — nếu anh chạy Codebase Map trên đó, anh sẽ thấy ngay 3 thứ: ai đang call vào PayGate, PayGate đang call ra đâu, và node nào có degree cao nhất. Dev mới muốn hiểu PayGate chỉ cần mở HTML 5 phút thay vì đọc code 1 tuần."
>
> "Còn chuyện dev mới ramp-up 2 tuần — anh có thể commit file `graph.html` vô repo, ngày đầu bảo họ mở ra nghiên cứu. Em đảm bảo giảm ít nhất 30% thời gian onboard."

**Nguyên tắc:** Dùng **chính ngôn từ** của CTO ở câu trả lời, họ cảm giác anh hiểu họ thật sự.

### 2.6 Call to Action (2 phút)

> "Tool này free forever, không giới hạn project size, không phải đăng ký tài khoản. Em gửi anh 3 thứ sau buổi call:
>
> 1. Link GitHub repo để `pip install`
> 2. 1 file `codebase-map.yaml` em viết sẵn config cho kiểu stack của team anh
> 3. 1 video demo 3 phút để anh chia sẻ lại cho tech lead
>
> Anh commit em 1 việc thôi: **trong 48 giờ chạy thử trên 1 repo bất kỳ của team anh**, rồi cho em feedback 1 dòng qua email hoặc Zalo. Deal không ạ?"

**Đây là CTA quan trọng nhất.** Đừng hỏi "anh có muốn dùng không" — luôn luôn hỏi **"anh có thể cam kết 48 giờ chạy thử không"**. Cam kết cụ thể + thời hạn cụ thể = tỷ lệ thực hiện cao gấp 5 lần.

### 2.7 Gieo hạt Codebase Memory — nếu còn thời gian (3 phút)

**Chỉ làm nếu CTO đã nói "OK 48 giờ em thử" và còn > 5 phút call.** Không ép, không pitch, chỉ gieo:

> "À anh, có 1 chuyện em muốn share thêm vì liên quan tới câu anh nói lúc nãy — chuyện AI sinh code không đúng convention team. Em đang build 1 sản phẩm mới gọi là Codebase Memory, nó học pattern team anh (cách đặt tên service, cách viết error handler, cách wire DI) rồi đưa vô context cho Claude Code qua MCP. Nghĩa là Claude Code của team anh sẽ 'nhớ' team anh viết code kiểu gì, không còn hallucinate nữa.
>
> Cái này em đang trong giai đoạn dogfood ở HC, chưa launch. Em không pitch gì hôm nay, nhưng nếu 48 giờ anh test Codebase Map thấy OK, em muốn mời anh vào **design partner program** cho Memory — anh dùng free trong 3 tháng, đổi lại em xin feedback. Anh có quan tâm không ạ?"

**Nếu CTO gật:** Ghi vào list design partner, follow up sau 2 tuần.
**Nếu CTO lưỡng lự:** "Không sao anh, em ghi chú lại, khi nào gần launch em ping anh." Không ép.

### 2.8 Kết thúc (1 phút)

> "Cảm ơn anh rất nhiều, buổi nói chuyện bổ ích lắm. Em sẽ gửi mail trong 1 giờ tới có đủ 3 link em hứa. Chúc anh team [Tên công ty] build tốt ạ. Hẹn gặp lại anh sau 48 giờ!"

---

## 3. Objection Handling — 8 câu CTO hay hỏi

### O1 — "Sao không dùng Sourcegraph/Glean/IDE plugin có sẵn?"
> "Câu hỏi hay. Sourcegraph tuyệt vời nhưng 2 vấn đề: một là giá $49/dev/tháng, team 50 dev là $2500/tháng, hai là code phải push lên cloud của họ. Codebase Map free, offline hoàn toàn, file HTML commit vô git được. IDE plugin thì chỉ xem được trong IDE, không share cross-team được. Codebase Map xuất ra HTML để cả team không code cũng xem được."

### O2 — "Tool này khác `pyan`, `pydeps` chỗ nào?"
> "Pyan và pydeps xuất ra hình PNG/SVG tĩnh — không click được, không search được. Codebase Map xuất HTML tương tác D3.js, có search, filter theo layer, impact analysis, click vô node highlight dependency. Khác biệt lớn nhất: Codebase Map hiểu layer (route/service/model) theo convention, không chỉ vẽ raw graph."

### O3 — "Team em dùng TypeScript, không phải Python"
> "Thành thật với anh: hiện tại v1.1 mới support Python, TypeScript đang trong sprint CM-S3, dự kiến ship tháng tới. Nếu anh OK em tag anh vô waitlist TS, khi ship em gửi link đầu tiên. Trong lúc chờ, nếu team anh có repo Python nào — như tool internal, script CI — anh chạy thử trước cũng được."

### O4 — "Tôi cài xong nó có đọc code gửi về server anh không?"
> "Tuyệt đối không. Codebase Map là pure Python package, không có network call nào trong code. Anh có thể xem source trên GitHub, grep `requests`, `urllib`, `http` — không có gì. Toàn bộ AST parse + HTML render chạy local trên máy anh. Đây là nguyên tắc em cam kết từ ngày đầu: code là tài sản trí tuệ, không bao giờ rời máy user."

### O5 — "Tool free thì mô hình kinh doanh của anh là gì? Anh sống bằng gì?"
> "Câu hỏi rất thẳng, em cảm ơn. Codebase Map free forever — không có kế hoạch tính tiền bao giờ. Kế hoạch của em là xây 1 sản phẩm paid tên Codebase Memory, cao cấp hơn, học pattern team và tích hợp với AI coding. Codebase Map là wedge tạo niềm tin, Memory là sản phẩm kiếm tiền. Em nói thật luôn với anh để anh thoải mái dùng Codebase Map, không có ràng buộc gì."

### O6 — "Tôi sợ cài rồi codebase bự quá chạy chậm/crash"
> "Tool hiện hỗ trợ tới ~100K dòng Python chạy mượt dưới 1 phút. Codebase 500K+ em đã test trên 1 project của 1 bạn, chạy 3-4 phút. Worst case không chạy được anh chỉ mất 5 phút uninstall — `pip uninstall codebase-map` là xong, không có background service, không có config lưu đâu cả."

### O7 — "Team tôi đang busy, chưa có thời gian thử tool mới"
> "Em hiểu anh. Vì vậy em không xin 1 sprint hay 1 ngày — em xin **đúng 5 phút** của 1 dev nào đó trong team. Chạy 3 lệnh, mở HTML, xem. Nếu không thấy giá trị, uninstall. Nếu thấy giá trị, dev đó sẽ tự viral cho phần còn lại của team. Em thấy 5 phút investment rủi ro thấp nhất quả đất."

### O8 — "Anh có case study nào chưa?"
> "Hiện tại case study chính là chính Hyper Commerce — codebase Python ~80K LOC, em chạy hàng ngày, dev mới của HC onboard trong 3 ngày thay vì 2 tuần. Em đang trong giai đoạn thu thập design partner, đó là lý do em muốn mời anh — nếu anh dùng và có feedback, em sẵn sàng viết 1 case study co-brand miễn phí, vừa là content cho anh vừa là lợi ích cho em. Win-win ạ."

---

## 4. Follow-up sau buổi call

### 4.1 Trong 1 giờ — Email summary
Template:

```
Subject: Codebase Map links + cam kết 48 giờ — [Tên CTO]

Chào anh [Tên],

Cảm ơn anh dành 30 phút buổi sáng. Như đã trao đổi, em gửi:

1. GitHub repo: https://github.com/hypercommerce-vn/codebase-map
2. Config YAML em viết sẵn cho stack team anh: [attach]
3. Video demo 3 phút: [link]

Cam kết của anh: 48 giờ chạy thử trên 1 repo bất kỳ, feedback 1 dòng.
Cam kết của em: Trả lời mọi câu hỏi kỹ thuật trong 2 giờ, bất kể ngày nghỉ.

Em note lại những gì mình thảo luận để anh nhớ lại:
- Pain 1: [copy nguyên văn pain CTO nói]
- Pain 2: [...]
- Pain 3: [...]

Hẹn gặp anh sau 48 giờ.

Tỉnh
Hyper Commerce
```

### 4.2 Sau 48 giờ — Nudge nhẹ
Nếu CTO chưa feedback:
> "Chào anh [Tên], anh đã có dịp chạy thử chưa ạ? Không ép anh feedback dài đâu, 1 dòng thôi: 'OK dùng được', 'bị lỗi X', hay 'chưa có thời gian'. Em muốn biết để improve tool tốt hơn ạ."

### 4.3 Sau 2 tuần — Gieo Memory
Nếu CTO đã dùng Codebase Map và có feedback tích cực:
> "Chào anh [Tên], cảm ơn anh đã dùng và feedback Codebase Map tuần trước. Như em nói buổi call, em đang mở design partner program cho Codebase Memory — cái học pattern team cho AI. Anh có 15 phút tuần này để em demo không ạ? Em không sale, chỉ show thử anh xem có đáng đầu tư 3 tháng dogfood không."

---

## 5. Metric đo hiệu quả sale (cho CEO track)

| Metric | Target tuần đầu | Target tháng đầu |
|--------|:--------------:|:---------------:|
| Buổi call đã thực hiện | 5 | 20 |
| Tỷ lệ cam kết 48 giờ | ≥ 70% | ≥ 70% |
| Tỷ lệ thực sự cài sau 48 giờ | ≥ 50% | ≥ 50% |
| Tỷ lệ feedback tích cực | ≥ 60% của người cài | ≥ 60% |
| Design partner Memory đăng ký | 1-2 | 5-8 |

Nếu metric dưới target → debug: là pitch sai, demo sai, hay target persona sai?

---

## 6. Do's & Don'ts

### ✅ DO
- Hỏi nhiều hơn nói (ratio 60/40 CTO/mình)
- Dùng nguyên văn từ CTO khi phản hồi
- Cam kết cụ thể có thời hạn (48 giờ, 5 phút, 1 dòng)
- Nói thật về business model — CTO ghét mập mờ
- Gieo Memory nhẹ, không ép

### ❌ DON'T
- Không nói "tool của em rất tốt" — để CTO tự khám phá
- Không so sánh dìm đối thủ (Sourcegraph, Glean) — chỉ nói fact
- Không demo quá 5 phút
- Không hứa feature chưa có
- Không xin tiền trong buổi đầu — Codebase Map là free!
- Không gửi PDF/slide deck — tool live demo mạnh hơn deck 10 lần

---

## 7. Cheat sheet 30 giây (in ra để dán bên bàn call)

```
MỞ ĐẦU:  "Em không tới để bán gì" → hạ shield
HỎI:     5 câu — context, onboard, legacy, AI, visualize
DEMO:    3 lệnh, 5 phút, dừng đúng chỗ
LINK:    Quay lại pain CTO, dùng ngôn từ CTO
CTA:     "Cam kết 48 giờ chạy thử, feedback 1 dòng"
GIEO:    Memory design partner — nhẹ, không ép
TIỄN:    Email trong 1 giờ, có đủ 3 link đã hứa
```

---

*Sales Script v1.0 — Codebase Map | 07/04/2026 | For CEO Đoàn Đình Tỉnh*
