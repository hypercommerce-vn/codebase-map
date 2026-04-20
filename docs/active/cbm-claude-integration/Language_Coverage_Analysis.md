# Phân tích Ngôn ngữ Lập trình — Coverage Roadmap cho CBM

> **Mục tiêu:** Xác định CBM cần support những ngôn ngữ nào để phục vụ >70% user của Claude Code.
> **Author:** Claude (AI Assistant)
> **Prepared for:** Đoàn Đình Tỉnh — CEO, Hyper Commerce
> **Date:** 2026-04-16
> **Status:** Research report cho quyết định roadmap v2.3+

---

## 1. TL;DR — Kết luận nhanh

| Hạng mục | Giá trị |
|---|---|
| **CBM hiện support** | Python + TypeScript |
| **Coverage ước tính hiện tại** | ~38% developer (primary language) |
| **Khuyến nghị để đạt >70%** | Thêm **JavaScript + Java** (và mở rộng cho Go ở Phase 2) |
| **Coverage sau khi thêm JS + Java** | ~75% |
| **Effort ước tính** | ~13 SP (JS: 3 SP reuse TS parser · Java: 8 SP parser mới · QA: 2 SP) |
| **Timeline đề xuất** | Sprint CBM-LANG-P1 (2 tuần) ngay sau CBM-INT-P1 |

**Quyết định mấu chốt:** JavaScript gần như miễn phí (TS parser cover được JS với < 3 SP tweak), nhưng Java mới là mảnh ghép để **Claude Code for Enterprise** (segment đang tăng mạnh nhất). Không có Java = mất mảng enterprise Java/Spring Boot đang dùng Claude Code để scale.

---

## 2. Bối cảnh — Claude Code users là ai?

### 2.1. Quy mô thị trường Claude Code (Q1/2026)

| Metric | Giá trị | Nguồn |
|---|---|---|
| Annualized revenue | ~$2.5B | Pragmatic Engineer Survey 2/2026 |
| Developer dùng AI agent coding | 73% eng teams (daily) | Same |
| Thị phần trong AI agent coding | 71% dùng Claude Code | Same |
| Business customer | 300,000+ | Anthropic, 10/2025 |
| Enterprise adoption | Java/Spring Boot mạnh | javatechonline.com, 2026 |

Claude Code **vượt GitHub Copilot + Cursor** trong 8 tháng, trở thành AI coding agent được dùng nhiều nhất. Đây là **tệp người dùng mục tiêu chính** của CBM khi phát hành MCP + Plugin.

### 2.2. Loại task coding (Anthropic Economic Index 3/2026)

- "Modifying software to correct errors": **10% enterprise API usage** (cao nhất trong nhóm coding)
- Software dev task trung bình cần **13.8 năm education** (so với 9.1 năm cho non-coding)
- Trend: coding task dịch chuyển từ augment (Claude.ai) → automate (API) → ưu tiên tool có **MCP tích hợp được agent** (chính là điểm mạnh CBM đang làm ở CBM-INT-P2)

---

## 3. Thống kê ngôn ngữ lập trình — 2025/2026

### 3.1. Stack Overflow Developer Survey 2025 (49,000+ dev · 177 nước)

| Ngôn ngữ | % dev sử dụng (all respondents) | Ghi chú |
|---|---|---|
| **JavaScript** | **66%** | #1 overall (web + script) |
| HTML/CSS | 62% | — |
| SQL | 59% | — |
| **Python** | **~58%** | +7pp YoY (dẫn đầu AI/data) |
| **TypeScript** | **~40%** | Tăng ổn định |
| **Java** | **~30%** | Enterprise anchor |
| C# | ~25% | .NET + Unity |
| Bash/Shell | ~28% | Ops + scripting |
| PHP | ~18% | Web legacy + WordPress |
| Go | ~15% | Cloud + microservices |
| Rust | ~13% | Systems, most admired (72%) |
| Ruby | ~5% | Startup legacy |

> Ghi chú: một dev thường dùng **đa ngôn ngữ** nên tổng > 100%. Trên thực tế để đo coverage ta cần nhìn ngôn ngữ **primary** (ngôn ngữ chính dev dùng để build product).

### 3.2. GitHub Octoverse 2025 — ranking theo contributor

| Rank | Ngôn ngữ | Contributor (M) | YoY Growth | Ghi chú |
|---|---|---|---|---|
| **1** | **TypeScript** | **2.64** | **+66.6%** | Lần đầu vượt Python nhờ AI-coding + type strict |
| **2** | **Python** | **2.60** | **+48%** | AI/data science nuôi growth |
| **3** | **JavaScript** | ~2.5 | ổn định | Web dominant |
| **4** | Java | ~1.5 | ổn định | Enterprise |
| **5** | C# | ~0.75 | **+22.2%** | +136k contributors mới |
| 6 | C++ | ~0.7 | nhẹ | Systems, gaming |
| 7 | Go | ~0.6 | tăng | Cloud-native |
| 8 | PHP | ~0.55 | giảm nhẹ | WordPress anchor |
| 9 | Rust | ~0.4 | tăng mạnh | Infra, Linux kernel |
| 10 | Ruby | ~0.3 | giảm | Startup legacy |

> Insight cốt lõi: **TypeScript vừa lên #1** là tín hiệu mạnh cho CBM — ta đã có TS parser rồi, đúng thời điểm vàng.

### 3.3. Language-specific adoption cho Claude Code

Theo benchmark 13-language (InfoQ/ai-coding-lang-bench 4/2026):

| Ngôn ngữ | Cost/run | Time/run | Pass tests | Claude Code "xài tốt" |
|---|---|---|---|---|
| Ruby | $0.36 | 73s | ✅ | Best |
| **Python** | $0.38 | 75s | ✅ | Best |
| **JavaScript** | $0.39 | 81s | ✅ | Best |
| Go | $0.50 | 102s | ✅ | OK |
| Rust | $0.54 | 110s | ❌ (1 fail) | Yếu |
| TypeScript (strict) | +1.6–2.6x Python | — | ✅ | Tốt nhưng chậm |

**Claude Code best-fit** theo benchmark: Python, JS, Ruby (dynamic, prototype-friendly). TS/Java/C# cost cao hơn nhưng là lựa chọn **enterprise production**.

---

## 4. Ước tính Primary-Language Distribution của Claude Code users

Kết hợp Stack Overflow + Octoverse + Claude benchmark + enterprise adoption pattern, em ước lượng phân bố **ngôn ngữ chính** (primary) của dev dùng Claude Code:

| Ngôn ngữ | % primary | Lý do ước lượng |
|---|---|---|
| **JavaScript** | **~25%** | Frontend + Node backend chiếm khối lượng lớn nhất |
| **Python** | **~20%** | AI/ML/data + backend Flask/FastAPI/Django |
| **TypeScript** | **~18%** | Fullstack modern (Next.js, NestJS) — đang tăng |
| **Java** | **~12%** | Enterprise (Spring Boot, Kafka, Android) |
| **C#** | **~7%** | .NET enterprise + Unity game |
| **Go** | **~5%** | Cloud-native infra (K8s operators, backend services) |
| **PHP** | **~4%** | WordPress/Laravel (SMB, e-commerce) |
| **Rust** | **~3%** | Systems, blockchain, WASM |
| **C/C++** | **~3%** | Embedded, game engine |
| **Ruby** | **~2%** | Startup legacy, Rails |
| Khác (Kotlin, Swift, Dart...) | ~3% | Mobile + niche |
| **Tổng** | **100%** | — |

> Phân bố trên nhằm ước lượng thị phần *primary language* cho mỗi dev, không phải tần suất sử dụng. Một dev có thể dùng 3-5 ngôn ngữ/ngày nhưng chỉ coi 1 là "nhà".

---

## 5. Coverage Analysis — CBM hiện tại vs. mục tiêu

### 5.1. Coverage CBM hiện tại (Python + TypeScript)

| Ngôn ngữ đã support | % primary users |
|---|---|
| Python | 20% |
| TypeScript | 18% |
| **Tổng coverage hiện tại** | **~38%** |

⚠️ **Gap:** 62% dev dùng Claude Code không được CBM phục vụ trực tiếp. Đây là lý do chính khiến PyPI launch (CBM-INT-P1) có thể đạt adoption dưới expectation nếu không mở rộng ngôn ngữ.

### 5.2. Các phương án đạt >70%

**Phương án A — Add JavaScript only (tận dụng TS parser):**

| Ngôn ngữ | % |
|---|---|
| Python | 20% |
| TypeScript | 18% |
| **+ JavaScript** | **+25%** |
| **Tổng** | **63%** ⚠️ gần 70% nhưng chưa đạt |

**Phương án B — Add JavaScript + Java ⭐ KHUYẾN NGHỊ:**

| Ngôn ngữ | % |
|---|---|
| Python | 20% |
| TypeScript | 18% |
| + JavaScript | +25% |
| **+ Java** | **+12%** |
| **Tổng** | **75%** ✅ vượt mục tiêu |

**Phương án C — Add JavaScript + Go + C#:**

| Ngôn ngữ | % |
|---|---|
| Python + TypeScript (hiện có) | 38% |
| + JavaScript | +25% |
| + C# | +7% |
| + Go | +5% |
| **Tổng** | **75%** ✅ |

**Phương án D — Aggressive (JS + Java + Go + C#):**

| Tổng | **87%** ✅✅ (phủ gần full stack mass market) |

### 5.3. So sánh 4 phương án

| Tiêu chí | A (JS) | **B (JS+Java)** ⭐ | C (JS+Go+C#) | D (JS+Java+Go+C#) |
|---|---|---|---|---|
| Coverage | 63% | **75%** | 75% | 87% |
| Đạt mục tiêu ≥70% | ❌ | ✅ | ✅ | ✅ |
| Effort | 3 SP | **13 SP** | 15 SP | 23 SP |
| Timeline | 3 ngày | **2 tuần** | 2.5 tuần | 4 tuần |
| Strategic fit | Thấp | **Enterprise-ready** | Infra/K8s focus | Full market |
| Rủi ro | Không đạt KPI | **Balanced** | Bỏ lỡ Java enterprise | Scope creep |
| **Xếp hạng** | ❌ | ⭐ **#1** | #3 | #2 (nếu có budget) |

---

## 6. Chi tiết effort cho từng ngôn ngữ

### 6.1. JavaScript — 3 SP (extend TS parser)

- JS gần như là **subset** của TypeScript về AST structure (ES2022+).
- Reuse `typescript_parser.py` với: skip type annotations, skip TS-only syntax (interfaces, generics).
- Thách thức: JSX support (React) — cần toggle parser config.
- Test: 20 fixture files từ Node.js, Express, Vue.

### 6.2. Java — 8 SP (new parser)

- Dùng **javalang** hoặc **tree-sitter-java** làm AST backend.
- Map Java concept → CBM Node/Edge:
  - `class` → Node (LayerType=model/service theo naming)
  - `method` → Node (NodeType=function)
  - `interface` → Node (NodeType=interface)
  - `extends/implements` → Edge (inheritance)
  - `method call` → Edge (call)
- Classifier rule mới cho Spring: `@Controller` → router, `@Service` → service, `@Repository` → repository, `@Entity` → model.
- Test: Spring Pet Clinic + 2 open-source Java repos.

### 6.3. Go — 4 SP (optional Phase 2)

- Dùng **go/ast** package via subprocess hoặc **tree-sitter-go**.
- Map: `func` → function, `struct` → model, `interface` → interface.
- Layer rule: `cmd/*` → entry, `internal/handler` → router, `internal/service` → service.
- Test: Kubernetes controller sample + Echo framework app.

### 6.4. C# — 5 SP (optional Phase 2)

- Dùng **tree-sitter-c-sharp** hoặc Roslyn via subprocess.
- Map: gần như Java (class/method/namespace).
- Classifier: ASP.NET Core attribute (`[ApiController]`, `[Route]`) → router; `IService` → service.
- Test: ASP.NET Core Web API + Clean Architecture sample.

---

## 7. Roadmap đề xuất

### Sprint CBM-LANG-P1 (2 tuần — Phương án B)

| Task ID | Mô tả | SP | Owner |
|---|---|---|---|
| CBM-LANG-101 | JavaScript parser (extend TS) + JSX | 3 | TechLead |
| CBM-LANG-102 | Java parser (javalang + Spring classifier) | 8 | TechLead |
| CBM-LANG-103 | Integration test + fixture repos | 2 | Tester |
| **Tổng** | | **13** | |

### Sprint CBM-LANG-P2 (2 tuần — tùy chọn, +12% coverage → 87%)

| Task ID | Mô tả | SP |
|---|---|---|
| CBM-LANG-201 | Go parser (tree-sitter-go) | 4 |
| CBM-LANG-202 | C# parser (tree-sitter-c-sharp) | 5 |
| CBM-LANG-203 | Integration test | 2 |
| **Tổng** | | **11** |

### Thứ tự khuyến nghị với CBM-INT

- **Q2/2026:** CBM-INT-P1 (PyPI publish) → CBM-LANG-P1 (JS+Java) → CBM-INT-P2 (MCP)
  - Lý do: publish PyPI trước với Python+TS để có bản v2.2.1 ra sớm. Rồi mở rộng ngôn ngữ cho v2.3 (JS+Java). Khi MCP ra mắt (v2.4), CBM đã cover 75% market.
- **Q3/2026:** CBM-INT-P3 (Plugin Marketplace) + CBM-LANG-P2 (Go+C#) → v2.5 cover 87%.

---

## 8. Rủi ro và Giả định

| # | Rủi ro | Xác suất | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Parser Java chậm với repo lớn (>100k LOC) | Trung bình | Trung bình | Dùng `javalang` (nhanh hơn tree-sitter-java); cache AST |
| R2 | JSX classifier mis-label component types | Thấp | Thấp | Fallback về filename heuristic `*.jsx` → UI component |
| R3 | Ước lượng primary-language distribution sai | Trung bình | Cao | Validate bằng early-adopter survey (5 user PyPI → thu thập repo language stats) |
| R4 | Claude Code user distribution khác Stack Overflow | Trung bình | Trung bình | Tracking telemetry (opt-in) trong MCP để thu dữ liệu real |
| R5 | Tác động enterprise adoption nếu thiếu Java | Cao | Cao | **Đây là lý do Phương án B khuyến nghị** |

**Giả định chính:**
- Primary-language distribution của Claude Code user *tương đối* khớp với Stack Overflow + Octoverse. Có thể lệch 5–10pp nhưng thứ hạng không đổi.
- Người dùng CBM là **working developer** có repo source (không phải học sinh làm bài tập).
- Enterprise Java users ở VN và Đông Nam Á có xu hướng sớm thử MCP Vietnamese-friendly, tạo lợi thế cạnh tranh cho CBM.

---

## 9. 3 Câu hỏi cho CEO quyết định

| # | Câu hỏi | Option |
|---|---|---|
| Q1 | Mục tiêu coverage là 70% (đủ) hay 85%+ (ambitious)? | 70% (B) / 85% (D) |
| Q2 | Ưu tiên Java (enterprise) hay Go (infra/cloud-native)? | Java / Go / Cả hai |
| Q3 | Timing: làm LANG trước INT-P2 (MCP) hay song song? | Trước / Song song |

Em khuyến nghị: **Q1=70% (B) · Q2=Java trước · Q3=Sau CBM-INT-P1, trước CBM-INT-P2** — vì MCP ra mắt với coverage 75% sẽ có adoption tốt hơn là ra với 38%.

---

## 10. Kết luận

CBM đang cover ~38% primary-language của Claude Code users (Python + TypeScript). Để vượt mốc 70%, **chỉ cần thêm 2 ngôn ngữ: JavaScript (3 SP) và Java (8 SP) — tổng 13 SP trong 2 tuần**, đạt coverage 75%. Đây là đòn bẩy quan trọng trước khi publish MCP, đảm bảo CBM đến tay đa số developer Claude Code với trải nghiệm "nó hiểu codebase của tôi" ngay lập tức.

Nếu có ngân sách mở rộng, thêm Go + C# ở Phase 2 sẽ đẩy coverage lên **87%**, gần như phủ full mass-market Claude Code users.

---

## Nguồn tham khảo

- [2025 Stack Overflow Developer Survey — Technology](https://survey.stackoverflow.co/2025/technology)
- [Stack Overflow 2025 Survey Insights — trytami.com](https://www.trytami.com/p/most-popular-technologies-in-2025)
- [GitHub Octoverse 2025: TypeScript rises to #1](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)
- [TypeScript Tops GitHub Octoverse — Visual Studio Magazine](https://visualstudiomagazine.com/articles/2025/10/31/typescript-tops-github-octoverse-as-ai-era-reshapes-language-choices.aspx)
- [Dynamic Languages Faster in 13-Language Claude Code Benchmark — InfoQ](https://www.infoq.com/news/2026/04/ai-coding-language-benchmark/)
- [ai-coding-lang-bench — GitHub (mame)](https://github.com/mame/ai-coding-lang-bench)
- [Which Programming Languages Work Best with Claude Code — ClaudeLog](https://claudelog.com/faqs/what-programming-languages-work-best-with-claude-code/)
- [Claude for Java Developers and Architects 2026](https://javatechonline.com/claude-for-java-developers-and-architects/)
- [Anthropic Economic Index report: Learning curves (3/2026)](https://www.anthropic.com/research/economic-index-march-2026-report)
- [Claude Code Enterprise](https://claude.com/product/claude-code/enterprise)

---

*Language_Coverage_Analysis.md v1.0 — Research report cho CEO decision · Codebase Map project · 16/04/2026*
