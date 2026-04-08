# JD — Knowledge OS Platform Engineer (Part-time Contractor)
> **Tổ chức:** Hyper Commerce · **Sản phẩm:** Knowledge Memory Platform (Codebase Memory v1.0 first)
> **Loại hợp đồng:** Contractor part-time, ~4-5 giờ/ngày
> **Thời hạn:** 6 tuần (Tuần 4 → Tuần 9 của roadmap KMP MVP), có thể gia hạn
> **Báo cáo trực tiếp cho:** CTO + TechLead
> **Author:** @BA + @PO · **Ngày đăng:** 07/04/2026

---

## 1. Về Hyper Commerce

Hyper Commerce (HC) đang xây dựng **Knowledge Memory Platform (KMP)** — hạ tầng "OS cho tri thức tổ chức" mà mọi domain (codebase, hợp đồng pháp lý, tài liệu nghiên cứu, sales playbook) đều plug vào được.

Sản phẩm đầu tiên là **Codebase Memory** — giúp AI coding tool (Claude Code, Cursor) "nhớ" pattern team, chấm dứt hallucination khi sinh code. Sản phẩm pivot từ Codebase Map (free, đã có người dùng) sang model Free Core + Paid Vertical, đặt trong hệ sinh thái KMP rộng hơn.

CEO Đoàn Đình Tỉnh (8 năm PM Samsung, 3 năm CEO startup) trực tiếp dẫn dắt sản phẩm. Team hiện tại: 1 TechLead full-time + AI agents (CTO/PO/BA/PM/Designer/Tester).

---

## 2. Vai trò

Bạn sẽ là **Knowledge OS Platform Engineer** — người thứ 2 trong team kỹ thuật, làm việc cùng TechLead để ship **Codebase Memory v1.0** trong 6 tuần. Bạn KHÔNG phải là Python dev đơn thuần — bạn là người hiểu **kiến trúc plugin/platform** và biết build abstraction sạch để tái dùng được cho vertical thứ 2 trong tương lai.

**Bạn sẽ owns:**
- Multi-LLM Provider layer (Anthropic / OpenAI / Gemini adapter)
- Insights Dashboard (HTML + Python aggregator)
- Landing page tích hợp (`codebase.agentwork.vn`)
- Documentation getting started (PDF + Markdown)

Tổng workload của bạn ~12 SP / 6 tuần, fit với 4-5 giờ/ngày.

---

## 3. Trách nhiệm cụ thể (Tuần-by-Tuần)

### Tuần 4 (Sprint M2 nửa sau)
- Implement `OpenAIProvider(LLMProvider)` — kế thừa từ `core/ai/providers/base.py`
- Implement `GeminiProvider(LLMProvider)` — tương tự
- Cost calculator per provider
- Cross-provider regression test (5 prompt × 3 provider, recall ≥ 75%)

### Tuần 5-6 (Sprint M3)
- Implement `core/telemetry/roi.py` aggregator
- Build `verticals/codebase/insights.html` dashboard cùng Designer agent
- Implement `commands/insights.py` CLI export tool

### Tuần 7-8 (Sprint M4)
- Build landing page `codebase.agentwork.vn` (1 trang, pricing + features + waitlist) cùng Designer
- Viết documentation getting started (Markdown + sinh PDF)
- Hỗ trợ TechLead test pyarmor matrix Python 3.10-3.13 nếu cần

### Tuần 9 (Soft launch)
- Hỗ trợ on-call cho 5 design partner đầu tiên
- Fix bug + iteration nhỏ

---

## 4. Yêu cầu kỹ thuật

### 4.1 Bắt buộc
- **Python ≥ 3.10**, ≥ 3 năm kinh nghiệm production
- **Hiểu OOP + abstract base class** sâu (có thể giải thích vì sao dùng ABC, generic, protocol)
- Đã từng làm việc với **plugin architecture** (Pelican, Pytest plugin, hoặc tương tự)
- Đã từng tích hợp **API LLM** (OpenAI / Anthropic / Gemini) trong production
- Quen với **SQLite, click, rich** Python libs
- Đọc tài liệu kỹ thuật **tiếng Anh** thành thạo
- Quen Git, GitHub Actions CI

### 4.2 Ưu tiên
- Có kinh nghiệm với **MCP (Model Context Protocol)** — nếu chưa biết, sẵn sàng đọc spec trong 1 tuần
- Đã từng build **dev tool / CLI tool** cho cộng đồng
- Có **portfolio open source** (≥ 1 repo public > 50 star càng tốt)
- Quen **typing strict** (mypy --strict, Pydantic)
- Hiểu **frontend cơ bản** (HTML/CSS/JS) đủ để build dashboard tĩnh

### 4.3 Soft skills
- **Tự chủ cao** — không cần micro-manage. CEO + TechLead chỉ check-in 2 lần/tuần.
- **Communication tiếng Việt rõ ràng** trong PR + Slack
- **Mindset platform builder**, không phải feature builder. Biết hỏi "cái này có generalize được không?" trước khi viết
- Sẵn sàng **review code 5-Dimension** của CTO (architecture, parser, performance, security, maintainability)

---

## 5. Bạn KHÔNG cần làm gì

Để rõ ràng từ đầu, bạn **không** phải:
- Tham gia sale, marketing, customer support
- Lead recruiting hay onboarding nhân sự khác
- Code core abstraction (TechLead làm — bạn dùng abstraction đó)
- Code parser AST Python (TechLead làm — đã port từ Codebase Map)
- Train ML model (KMP không dùng vector embedding, không có training)
- Deploy infrastructure (sản phẩm là local-first, không có server-side)

---

## 6. Quyền lợi

| Hạng mục | Chi tiết |
|---------|---------|
| **Mức thù lao** | Thương lượng theo kinh nghiệm (range tham khảo: 350K - 600K VND/giờ) |
| **Hình thức** | Hợp đồng dịch vụ, thanh toán 2 tuần/lần qua chuyển khoản hoặc Wise |
| **Thời gian linh hoạt** | Tự sắp xếp 4-5 giờ/ngày, không cần 9-5. Yêu cầu duy nhất: standup async hàng ngày trong Slack |
| **Equity option** | Sau 6 tuần nếu hai bên hài lòng, có thể đàm phán full-time + equity |
| **Credit** | Tên bạn xuất hiện trong CONTRIBUTORS.md của KMP open source repo |
| **Học hỏi** | Tiếp xúc trực tiếp với CEO + CTO + AI agent workflow của HC, kinh nghiệm hiếm có ở Việt Nam |

---

## 7. Quy trình tuyển

### Bước 1 — Apply (5 phút)
Gửi email đến `hypercdp@gmail.com` với tiêu đề `[KMP Engineer] - <Tên của bạn>` kèm:
- 1 đoạn giới thiệu ≤ 5 câu (bạn là ai, tại sao quan tâm KMP)
- Link GitHub
- Link 1 project Python OOP/plugin architecture mà bạn tự hào nhất

**Không cần CV chính thức ở bước này.**

### Bước 2 — Take-home test (≤ 4 giờ work)
Bạn sẽ nhận 1 task thực tế:
> *"Implement `BaseLearner` subclass đếm tần số từ trong file .txt, kế thừa từ skeleton chúng tôi cung cấp. Viết unit test. Submit PR vào sandbox repo."*

Đánh giá: code quality, OOP discipline, test, README, thời gian deliver.

### Bước 3 — Pair coding 60 phút (live)
Bạn + TechLead pair lên 1 issue thực của KMP. Đánh giá: communication, debug skill, mindset.

### Bước 4 — CEO interview 30 phút
Cultural fit + thảo luận vision Knowledge OS company.

### Bước 5 — Offer
Trong 48 giờ sau bước 4.

**Tổng thời gian quy trình tuyển: ≤ 1 tuần.**

---

## 8. Câu hỏi thường gặp

**Q: Tôi chưa biết MCP, có sao không?**
A: OK. MCP spec chỉ ~30 trang, đọc trong 1 ngày. Quan trọng là bạn biết RPC/JSON-RPC.

**Q: Tôi mạnh backend nhưng yếu frontend, dashboard có khó không?**
A: Dashboard là HTML/CSS đơn giản + Plotly/Chart.js. Designer agent hỗ trợ. Bạn không cần là frontend dev.

**Q: 4-5 giờ/ngày có đủ deliverable 12 SP/6 tuần không?**
A: 12 SP × 8 giờ/SP = 96 giờ. 6 tuần × 5 ngày × 4-5 giờ = 120-150 giờ. Có buffer 25-50% cho overhead.

**Q: Sau 6 tuần thì sao?**
A: 3 kịch bản:
1. Hai bên hài lòng → full-time offer + equity option
2. Hài lòng nhưng bạn bận → tiếp tục contractor cho M5+ (vertical thứ 2)
3. Không hợp → thanh toán đầy đủ, không ràng buộc

**Q: KMP open source toàn bộ không?**
A: Core là **MIT open source**. Một số Pro feature trong vertical là proprietary. Bạn sẽ làm việc cả 2 phần.

**Q: Tôi ở Hà Nội/Đà Nẵng/TP.HCM, có cần lên văn phòng không?**
A: 100% remote. Chỉ cần multi-platform standup async + 1-2 video call/tuần.

---

## 9. Tại sao bạn nên join HC bây giờ

- **Cơ hội build platform from scratch** — không phải maintain legacy
- **Có CEO trực tiếp + AI agent team** — feedback loop nhanh, ít politics
- **Định vị "Knowledge OS company VN"** chưa có ai chiếm — first mover advantage thật
- **Stack hiện đại:** Python 3.10+, mypy strict, MCP, multi-LLM, modern CLI (rich/click)
- **Việc bạn làm sẽ có người dùng thật** trong 6 tuần (không phải project demo)

---

## 10. Liên hệ

**Email:** hypercdp@gmail.com
**Người phụ trách:** Đoàn Đình Tỉnh (CEO)
**Deadline apply:** Ưu tiên 7 ngày đầu, sau đó rolling

---

*JD v1.0 — Knowledge OS Platform Engineer · @BA + @PO · 07/04/2026*
