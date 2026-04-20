# Chiến lược Go-To-Market theo Project Archetype

> **Insight cốt lõi:** User không mua "parser ngôn ngữ X". User mua "tool hiểu codebase của dự án tôi đang làm".
> Vì vậy CBM+KMP cần positioning theo **combo stack** gắn với loại dự án (AI agent, e-commerce, SaaS, enterprise...) thay vì theo từng ngôn ngữ rời rạc.
>
> **Prepared for:** Đoàn Đình Tỉnh — CEO, Hyper Commerce
> **Date:** 2026-04-16
> **Status:** GTM strategy v1.0 — companion của Language_Coverage_Analysis.md

---

## 1. TL;DR — Ngắn cho CEO

| Vấn đề | Giải pháp |
|---|---|
| Bán "CBM support Python + TS" → user không hiểu mình hưởng lợi gì | Bán "CBM hiểu trọn codebase AI Agent / SaaS / E-commerce của bạn" |
| 10+ ngôn ngữ, 10+ framework rời rạc, khó prioritize | Gom thành **7 archetype** chính, mỗi archetype là một GTM segment |
| Không biết user đang ở phase nào của dự án | Archetype giúp CBM pitch đúng pain point: "bạn vừa mới join team AI agent 5 repos?" |

### Khuyến nghị top-line

**Phase 1 (ngay — v2.2.x launch):** Dùng archetype **#1 AI Agent** + **#2 SaaS B2B** làm ngòi nổ → 2 combo này CBM đã 100% cover (Python + TS) → messaging và demo tập trung vào đây.

**Phase 2 (v2.3 — 6 tuần):** Mở rộng thêm archetype **#3 E-commerce (thêm PHP)** + **#4 Enterprise Java (thêm Java)** → cover 4/7 archetype chính → ~75% Claude Code user có "home" trong CBM.

**Phase 3 (v2.5 — Q3/2026):** **#5 Cloud-Native (Go)** + **#6 Mobile cross-platform (Kotlin + Swift + Dart)** → cover 6/7 archetype.

---

## 2. Bối cảnh — Tại sao xoay trục sang Archetype?

### 2.1. Tech-marketing vs Use-case-marketing

| Tiêu chí | Tech-marketing (hiện tại) | Use-case-marketing (đề xuất) |
|---|---|---|
| Hook | "Support 10 ngôn ngữ" | "Hiểu codebase AI agent của bạn" |
| Reader's reaction | "OK thế rồi sao?" | "Ồ đúng cái tôi đang build!" |
| Competitor | Dễ bị so bảng feature | Khác biệt bằng empathy |
| Adoption driver | Spec | Câu chuyện |
| Measurable | Downloads | Downloads × retention × NPS |

### 2.2. User segment thật sự của Claude Code (đo theo pain, không đo theo ngôn ngữ)

Dev dùng Claude Code thường rơi vào 1 trong các khối công việc:
- Xây AI agent / LLM app (đang bùng nổ 2025-2026)
- Xây SaaS B2B (thị trường lớn, ổn định)
- Xây e-commerce / marketplace (VN + SEA mass market)
- Duy trì enterprise internal system (Java/C#)
- Xây cloud-native infra (Go, K8s)
- Xây mobile app (React Native / Flutter / native)
- Xây data platform (Python + Scala + SQL)

Khi CBM/KMP pitch theo archetype, user **tự nhận ra mình** và click ngay.

---

## 3. 7 Project Archetype chính của Claude Code users

### 3.1. Tóm tắt 7 archetype

| # | Archetype | Est. share | Growth | Persona |
|---|---|---|---|---|
| 1 | **AI Agent / LLM App** | 18% | 🔥🔥🔥 | Startup 2-20 dev, LLM-native |
| 2 | **SaaS B2B Web** | 22% | 🔥🔥 | SaaS 5-50 dev, Next.js + Django/FastAPI |
| 3 | **E-commerce / Marketplace** | 15% | 🔥 | Agency + SME, Shopify/WooCommerce/Medusa |
| 4 | **Enterprise Internal Tool** | 14% | ổn định | Bank, telco, corp — Java/Spring |
| 5 | **Cloud-Native / DevOps** | 10% | 🔥 | Infra team, Go + K8s |
| 6 | **Mobile Cross-platform** | 9% | ổn định | Product team, RN/Flutter + native |
| 7 | **Data Platform / ML Ops** | 8% | 🔥 | Data team, Python + SQL + Scala |
| — | Khác (game, blockchain, embedded) | 4% | biến động | Niche |

> Tỷ lệ này ước lượng dựa trên kết hợp: Stack Overflow Survey 2025, GitHub Octoverse 2025, Anthropic Economic Index 3/2026 (coding task pattern), và benchmark 13-language Claude Code. Cần validate bằng user survey thật sau khi launch PyPI.

### 3.2. Chi tiết từng archetype

#### Archetype #1 — AI Agent / LLM App 🔥🔥🔥

| Field | Detail |
|---|---|
| Stack chính | **Python** (FastAPI, LangChain, LangGraph, LlamaIndex, Pydantic) + **TypeScript** (Next.js, Vercel AI SDK) |
| Stack phụ trợ | Rust (inference infra, vLLM binding) · SQL (pgvector) · YAML (prompt templates) |
| Typical repo | monorepo hoặc 2-3 repo: `agent-core` (Py), `web` (TS), `infra` (Terraform/YAML) |
| Codebase pain | RAG chain phức tạp, tool-calling graph khó trace, prompt scatter nhiều file |
| CBM value prop | "Draw agent graph + impact khi đổi prompt/tool" |
| KMP value prop | "Ask Claude: tool này được gọi ở chain nào?" |
| **CBM coverage hiện tại** | **✅ 100% (Python + TS)** |
| GTM ưu tiên | ⭐⭐⭐ Tier 1 — launch trước |

#### Archetype #2 — SaaS B2B Web 🔥🔥

| Field | Detail |
|---|---|
| Stack chính | **TypeScript** (Next.js, NestJS, Remix) + **Python** (Django, FastAPI) hoặc **Node.js** (Express) |
| Stack phụ trợ | SQL (PostgreSQL) · Redis · tRPC/GraphQL schema |
| Typical repo | Monorepo Turbo/Nx với `apps/web`, `apps/api`, `packages/shared` |
| Codebase pain | API contract giữa FE-BE dễ vỡ, domain service chồng chéo, cross-cutting concerns |
| CBM value prop | "Show API catalog + impact khi rename endpoint" |
| KMP value prop | "Onboard dev mới trong 1 ngày thay vì 2 tuần" |
| **CBM coverage hiện tại** | **✅ 100% (Python + TS)** — cần thêm JS để cover Node.js thuần |
| GTM ưu tiên | ⭐⭐⭐ Tier 1 — launch trước |

#### Archetype #3 — E-commerce / Marketplace 🔥

| Field | Detail |
|---|---|
| Stack chính | **TypeScript** (Shopify Hydrogen, Medusa, Next.js) + **PHP** (WooCommerce, Magento, Laravel) + **Python** (recommendation engine) |
| Stack phụ trợ | Ruby (Shopify backend legacy) · SQL · Elasticsearch config |
| Typical repo | Tách shop-frontend, shop-backend, admin panel, recommender |
| Codebase pain | Plugin hell (WooCommerce), theme customization, pricing rule engine |
| CBM value prop | "Trace flow checkout từ FE đến payment gateway" |
| KMP value prop | "Ask Claude: logic giảm giá áp cho combo SKU ở đâu?" |
| **CBM coverage hiện tại** | ⚠️ 60% (thiếu PHP — chiếm phần lớn mảng SME shop) |
| GTM ưu tiên | ⭐⭐ Tier 2 — cần thêm PHP parser |

#### Archetype #4 — Enterprise Internal Tool

| Field | Detail |
|---|---|
| Stack chính | **Java** (Spring Boot, Spring Cloud) + **TypeScript** (React/Angular admin) + **SQL** (Oracle, SQL Server) |
| Stack phụ trợ | Kotlin (microservice mới) · C# (.NET legacy) · YAML (K8s Helm) |
| Typical repo | Multi-module Maven/Gradle, mono hoặc micro-services |
| Codebase pain | Codebase 10+ năm, Spring annotation dày đặc, dependency khó trace |
| CBM value prop | "Impact analysis khi modify service method — trước khi merge" |
| KMP value prop | "Ask Claude: controller X gọi repository Y qua mấy layer?" |
| **CBM coverage hiện tại** | ❌ 40% (chỉ cover FE TS, thiếu Java + C#) |
| GTM ưu tiên | ⭐⭐ Tier 2 — high-ticket enterprise |

#### Archetype #5 — Cloud-Native / DevOps 🔥

| Field | Detail |
|---|---|
| Stack chính | **Go** (K8s operator, Helm generator, backend) + **Python** (ops scripts, Ansible) + **TypeScript** (dashboard) |
| Stack phụ trợ | YAML (K8s, ArgoCD) · HCL (Terraform) · Rust (performance infra) |
| Typical repo | `cmd/`, `internal/`, `pkg/` pattern + infra-as-code repo riêng |
| Codebase pain | Controller reconcile loop khó trace, infra drift, YAML spread |
| CBM value prop | "Show K8s resource graph + service call graph cùng chỗ" |
| KMP value prop | "Ask Claude: service mesh config ảnh hưởng endpoint nào?" |
| **CBM coverage hiện tại** | ❌ 30% (cần Go) |
| GTM ưu tiên | ⭐ Tier 3 — niche nhưng high-value |

#### Archetype #6 — Mobile Cross-platform

| Field | Detail |
|---|---|
| Stack chính | **TypeScript** (React Native) hoặc **Dart** (Flutter) + **Kotlin** (Android native) + **Swift** (iOS native) + **Python/Node** (backend) |
| Stack phụ trợ | Objective-C (legacy iOS) · Java (legacy Android) |
| Typical repo | Mono `app/` + `backend/` hoặc tách native modules |
| Codebase pain | Native bridge code fragile, platform-specific logic lan man |
| CBM value prop | "Show cross-platform component graph + native bridge usage" |
| **CBM coverage hiện tại** | ⚠️ 40% (cover RN qua TS, thiếu Flutter/Kotlin/Swift) |
| GTM ưu tiên | ⭐ Tier 3 — fan-out khi có budget |

#### Archetype #7 — Data Platform / ML Ops 🔥

| Field | Detail |
|---|---|
| Stack chính | **Python** (Pandas, Airflow, dbt, PySpark, scikit-learn, MLflow) + **SQL** (dbt models) + **Scala** (Spark jobs) |
| Stack phụ trợ | TypeScript (Streamlit/dashboard) · YAML (Airflow DAG config) |
| Typical repo | `dags/`, `models/`, `transformations/`, `notebooks/` |
| Codebase pain | DAG dependency invisible, dbt lineage khó trace cross-project |
| CBM value prop | "Combine code dependency + data lineage (dbt) trong 1 graph" |
| **CBM coverage hiện tại** | ⚠️ 70% (Python OK, SQL cần thêm, Scala là nice-to-have) |
| GTM ưu tiên | ⭐⭐ Tier 2 — data community dễ viral |

---

## 4. Bảng tổng hợp Coverage hiện tại theo Archetype

| Archetype | Share | CBM Coverage hiện tại | Gap | GTM Tier |
|---|---|---|---|---|
| #1 AI Agent | 18% | ✅ 100% | — | **T1 — LAUNCH NGAY** |
| #2 SaaS B2B | 22% | ✅ 95% (thêm JS để hoàn thiện) | JS | **T1 — LAUNCH NGAY** |
| #3 E-commerce | 15% | ⚠️ 60% | **PHP** | T2 — Q2/2026 |
| #4 Enterprise Internal | 14% | ❌ 40% | **Java, C#** | T2 — Q2/2026 |
| #5 Cloud-Native | 10% | ❌ 30% | **Go** | T3 — Q3/2026 |
| #6 Mobile | 9% | ⚠️ 40% | Kotlin, Swift, Dart | T3 — Q3/2026 |
| #7 Data Platform | 8% | ⚠️ 70% | SQL parser sâu | T2 — Q2/2026 |

**Công thức tổng coverage theo archetype (trọng số = share):**

- **Hiện tại (Python+TS):** 0.18×1.00 + 0.22×0.95 + 0.15×0.60 + 0.14×0.40 + 0.10×0.30 + 0.09×0.40 + 0.08×0.70 = **~64%**
- **Sau v2.3 (+JS+PHP+Java+SQL):** ~0.80 = **~80%** coverage theo use-case
- **Sau v2.5 (+Go+Kotlin+Swift+Dart):** ~0.92 = **~92%** coverage

> Ghi chú: coverage theo archetype *cao hơn* coverage theo language (ở báo cáo trước) vì 1 ngôn ngữ có thể phục vụ nhiều archetype đồng thời (VD: TS phục vụ AI, SaaS, E-com, Mobile). Vì vậy tiếp cận "archetype combo" hiệu quả hơn về adoption.

---

## 5. Roadmap GTM theo Archetype

### 5.1. Phase 1 — "AI Agent + SaaS B2B" Launch (Q2/2026, ngay sau PyPI publish)

**Mục tiêu:** CBM ra mắt với 2 use-case mass-appeal nhất, coverage 100%, tất cả demo và material tập trung vào 2 archetype này.

**Deliverable:**

- Landing page `/ai-agent`: video 60s, demo graph trên LangChain agent repo, quote "hiểu RAG chain của bạn trong 5 giây"
- Landing page `/saas`: demo graph trên Next.js + FastAPI SaaS sample, impact analysis khi rename API endpoint
- 2 fixture repo trong `examples/`:
  - `examples/ai-agent-demo/` — Python + TS (FastAPI + Next.js + LangChain)
  - `examples/saas-demo/` — Python + TS (Django + Next.js)
- Blog: "Understanding your AI agent codebase with CBM" (+ 1 blog SaaS tương tự)
- Video 3-5 phút cho mỗi archetype

### 5.2. Phase 2 — "E-commerce + Enterprise + Data" Expansion (Q2-Q3/2026)

**Mục tiêu:** Add PHP + Java + SQL deep parser → mở 3 archetype mới.

**Deliverable:**

- Sprint CBM-LANG-P1 (theo Language_Coverage_Analysis.md): +JS, +Java — 13 SP
- Sprint CBM-LANG-P1b: +PHP (5 SP) + SQL parser cho dbt/Airflow (4 SP)
- Landing page `/ecommerce`: demo WooCommerce + Shopify Hydrogen
- Landing page `/enterprise-java`: demo Spring Pet Clinic repo
- Landing page `/data-platform`: demo dbt + Airflow repo
- Case study 1: một agency VN dùng CBM để onboard dev vào repo WooCommerce cũ
- Case study 2: một ngân hàng/fintech dùng CBM review PR trước merge Spring Boot service

### 5.3. Phase 3 — "Cloud-Native + Mobile" Complete Coverage (Q3-Q4/2026)

**Mục tiêu:** Cover 6/7 archetype, đạt ~92% Claude Code user base.

**Deliverable:**

- Sprint CBM-LANG-P2: +Go (4 SP) + Kotlin/Swift/Dart (10 SP)
- Landing page `/cloud-native`: demo K8s operator repo
- Landing page `/mobile`: demo React Native + Flutter app
- Integration với Anthropic MCP catalog dưới tên CBM → auto-listed trong Claude Desktop

### 5.4. Timeline visual

```
Q2/2026 ─────────────────────────────────────────
│
├── Apr: PyPI launch (v2.2.1) · AI Agent + SaaS pages
├── May: JS + Java parsers (v2.3)
├── Jun: Enterprise + E-commerce pages
│
Q3/2026 ─────────────────────────────────────────
│
├── Jul: PHP + SQL parsers (v2.4)
├── Aug: Data Platform page + case studies
├── Sep: Go parser (v2.5) · Cloud-Native page
│
Q4/2026 ─────────────────────────────────────────
│
├── Oct: Kotlin + Swift + Dart (v2.6)
├── Nov: Mobile page
└── Dec: KMP public beta (RAG layer trên CBM)
```

---

## 6. Messaging mẫu cho từng Archetype

### 6.1. Landing page AI Agent

**Headline:** "Claude biết code. CBM biết codebase AI agent của bạn."

**Sub:** Xây LangChain multi-tool agent 3 tháng nay và không nhớ được chain nào đang gọi tool nào? CBM vẽ graph toàn bộ agent flow + RAG chain + tool registry trong 10 giây, và đưa thẳng vào Claude Code qua MCP.

**CTA:** `pipx install codebase-map && cbm generate` → mở graph.html

**Demo nội dung:**
- Graph zoom-in vào `agent.run()` → show tất cả tool được gọi
- Click tool → show impact khi rename
- Ask Claude trong terminal: "tool `search_product` được dùng ở chain nào?" → MCP trả lời

### 6.2. Landing page SaaS B2B

**Headline:** "Onboard dev mới vào SaaS của bạn trong 1 ngày, không phải 2 tuần."

**Sub:** SaaS của bạn có 50k LOC TypeScript + Python? Dev mới mất 2 tuần chỉ để hiểu flow request → API → service → DB. CBM + KMP đưa họ đến đích trong 1 buổi.

**CTA:** Try demo với Next.js + FastAPI template

### 6.3. Landing page E-commerce

**Headline:** "WooCommerce plugin hell? CBM map hết dependency cho bạn."

**Sub:** 30 plugin trong WooCommerce, không ai biết plugin nào override hook nào. CBM scan toàn bộ PHP hook + filter + action → vẽ graph. Không còn break production khi update plugin.

### 6.4. Landing page Enterprise Java

**Headline:** "Review PR Spring Boot trong 1 phút, không phải 1 buổi."

**Sub:** Service method có 20 consumer? Repository bị gọi từ 15 controller? CBM impact analysis nói thẳng: "PR này chạm đến 47 call site, 12 test, 3 external API." Merge hay không — 5 giây quyết định.

### 6.5. Landing page Cloud-Native

**Headline:** "Reconcile loop của bạn gọi những gì? Ask CBM."

**Sub:** Controller Kubernetes của bạn gọi 5 service, mỗi service tạo 3 CR mới, mỗi CR trigger 2 webhook. CBM + KMP map toàn bộ dependency code + K8s resource graph cùng một chỗ.

### 6.6. Landing page Mobile

**Headline:** "Native bridge đang vỡ mỗi lần update? CBM chỉ chỗ."

**Sub:** React Native của bạn có 40 native module. Nửa số đó là Kotlin, nửa là Swift. Khi BE đổi API, không ai nhớ module nào cần update. CBM map cross-platform dependency — một graph duy nhất.

### 6.7. Landing page Data Platform

**Headline:** "dbt lineage + Airflow DAG + code dependency — cùng một màn hình."

**Sub:** DAG breakdown 3 ngày trước merge vì một model dbt đổi schema? CBM combine data lineage (dbt manifest) với code graph (Python DAG code) → nhìn thấy end-to-end lineage.

---

## 7. Marketing Funnel mapping theo Archetype

| Funnel stage | Archetype AI Agent | Archetype SaaS | Archetype E-com |
|---|---|---|---|
| **Awareness** | Dev.to blog "CBM for LangChain devs" | "Onboard dev in 1 day" Twitter thread | "Survive WooCommerce hell" blog |
| **Interest** | YouTube demo 3 phút | YouTube demo 3 phút | YouTube demo 3 phút |
| **Consideration** | Landing + fixture repo | Landing + fixture repo | Landing + fixture repo |
| **Trial** | `pipx install` + `cbm generate` | Same | Same |
| **Retention** | Auto Claude Code MCP integration | Same | Same |
| **Advocacy** | Case study (startup LLM) | Case study (SaaS scale-up) | Case study (agency VN) |

---

## 8. Cross-sell CBM + KMP theo Archetype

CBM + KMP là cặp đôi: CBM làm **graph**, KMP làm **RAG/MCP** trên graph đó. Bundle theo archetype:

| Archetype | CBM feature key | KMP feature key | Combined pitch |
|---|---|---|---|
| AI Agent | Chain + Tool graph | "Ask: tool X called where?" | **AI Agent Knowledge Pack** (CBM Agent plan + KMP Chain Navigator) |
| SaaS B2B | API catalog + impact | "Ask: impact of removing endpoint?" | **SaaS Onboarding Pack** |
| E-commerce | Plugin hook graph | "Ask: price rule precedence?" | **E-com Audit Pack** |
| Enterprise | Spring layer graph | "Ask: service call depth?" | **Enterprise Review Pack** |
| Cloud-Native | Reconcile graph + K8s | "Ask: what CR this controller creates?" | **Cloud-Native Ops Pack** |
| Mobile | Cross-platform bridge | "Ask: native modules touched?" | **Mobile Bridge Pack** |
| Data Platform | Code + data lineage | "Ask: dbt model impact?" | **Data Lineage Pack** |

Mỗi pack có thể **bán riêng** với pricing khác nhau (free OSS tier + paid enterprise tier), hoặc free all-in cho dev, paid cho team có KMP hosted.

---

## 9. Đo lường thành công (KPI theo Archetype)

### 9.1. KPI Phase 1 (AI Agent + SaaS)

| KPI | Target 30 ngày | Target 90 ngày |
|---|---|---|
| `pipx install codebase-map` downloads | 500 | 3.000 |
| GitHub stars | 200 | 1.000 |
| Landing `/ai-agent` visits | 2.000 | 10.000 |
| Landing `/saas` visits | 2.500 | 12.000 |
| Demo repo clones | 100 | 600 |
| MCP tool calls (Phase 2 tracking) | n/a | 5.000/tuần |

### 9.2. KPI Phase 2 (E-commerce + Enterprise + Data)

| KPI | Target 90 ngày sau launch |
|---|---|
| Enterprise case study | 2 case |
| Java/PHP parser adoption rate | 25% của toàn user base |
| Paid KMP enterprise contract | 3 contract ($5k+ ARR mỗi) |

### 9.3. KPI Phase 3 (Full coverage)

| KPI | Target EOY 2026 |
|---|---|
| Coverage archetype (weighted) | ≥ 90% |
| Tổng CBM downloads | 50.000 |
| Tổng dev dùng MCP hàng tuần | 3.000 |
| KMP enterprise customer | 15 |

---

## 10. Rủi ro và Counter-move

| # | Rủi ro | Counter-move |
|---|---|---|
| R1 | Chia archetype quá thô, user không nhận ra mình | A/B test 2 archetype labels (VD: "AI Agent" vs "LLM App") và chọn click-through cao |
| R2 | Demo repo không đại diện → user thấy lạc lõng | Mỗi archetype có 2-3 demo repo: toy (nhỏ, dễ hiểu) + realistic (đủ phức tạp) |
| R3 | Archetype overlap (SaaS có AI, AI là SaaS...) | Chấp nhận overlap, focus trên pain chính của từng archetype |
| R4 | Chi phí maintain 7 landing page + 7 demo | Template hóa landing page, mỗi archetype reuse structure |
| R5 | Coverage báo cáo theo archetype cao hơn theo language — có overstate? | Rõ ràng trong footer: "coverage = archetype có ít nhất 80% language stack support" |

---

## 11. 3 Câu hỏi quyết định cho CEO

| # | Câu hỏi | Em khuyến nghị |
|---|---|---|
| Q1 | Phase 1 launch với 2 archetype (AI + SaaS) hay 3 (thêm Data)? | **2 archetype** — focus hẹp để ngấm, Data Q2 thêm sau |
| Q2 | Có build CBM + KMP bundle riêng theo archetype (pack) không? | **Có** — đóng gói pricing theo pack là đòn bẩy enterprise |
| Q3 | Ngôn ngữ ưu tiên: Java (enterprise) hay PHP (e-com VN) trước? | **Java trước** — enterprise có budget, paid conversion cao hơn |

---

## 12. Kết luận

Xoay trục từ **"support nhiều ngôn ngữ"** sang **"hiểu trọn codebase theo loại dự án"** giúp CBM+KMP:

1. **Gây cộng hưởng mạnh hơn** với user (họ thấy mình trong description)
2. **Tối ưu coverage mà không cần thêm ngôn ngữ ngay** — Python+TS đã cover 2 archetype hot nhất (AI Agent + SaaS B2B = 40% market)
3. **Tạo cross-sell tự nhiên** giữa CBM (graph) và KMP (RAG) theo pack
4. **Tách pricing tier** theo archetype → mở đường enterprise ARR
5. **Tập trung marketing** — mỗi archetype là 1 GTM motion riêng, dễ đo dễ tối ưu

Kết hợp với Language_Coverage_Analysis.md đã có: **Phase 1 launch NGAY với AI Agent + SaaS** (coverage 100%), không đợi thêm ngôn ngữ. Java + PHP bổ sung ở v2.3 mở thêm Enterprise + E-com. Toàn bộ roadmap 3 phase đạt 92% coverage weighted vào cuối 2026.

---

## Liên kết tài liệu

- [Strategy_Memo_CBM_Claude_Integration.md](./Strategy_Memo_CBM_Claude_Integration.md) — Strategy memo Claude integration
- [Technical_Plan_CBM_Claude_Integration.md](./Technical_Plan_CBM_Claude_Integration.md) — Technical plan 3 phase
- [Language_Coverage_Analysis.md](./Language_Coverage_Analysis.md) — Phân tích coverage theo ngôn ngữ (companion của file này)

---

*Project_Archetype_GTM_Strategy.md v1.0 — GTM strategy theo archetype · Codebase Map project · 16/04/2026*
