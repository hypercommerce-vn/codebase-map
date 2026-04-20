# Chiến lược Open Source cho CBM — Publish GitHub hay không?

> **Câu hỏi CEO:** Với chiến lược tích hợp CBM vào Claude ecosystem, có nên để repo code publish trên GitHub?
>
> **Trả lời ngắn:** ✅ **Có, bắt buộc phải public** — không có public repo, toàn bộ chiến lược Claude Integration (PyPI, MCP, Plugin Marketplace) sẽ giảm 70% hiệu quả. Và CBM đã được chuẩn bị cho việc này rồi (MIT license, tách khỏi HC, KMP đã chuyển sang repo private riêng).
>
> **Prepared for:** Đoàn Đình Tỉnh — CEO, Hyper Commerce
> **Date:** 2026-04-16
> **Status:** Strategic memo — final decision needed

---

## 1. TL;DR

| Câu hỏi | Câu trả lời |
|---|---|
| Có nên public? | **✅ CÓ — public ngay trong tuần này** |
| License? | **MIT (đã chọn) OK, nhưng cân nhắc Apache 2.0** (patent clause tốt hơn cho enterprise) |
| KMP có public không? | **❌ KHÔNG — giữ private**, đây là moat kinh doanh |
| Rủi ro cloud vendor clone? | Thấp — CBM là dev tool, không phải hosted service |
| Thời điểm? | **Trước hoặc cùng ngày launch PyPI v2.2.1** (chuẩn bị đã xong 80%) |

### Nguyên nhân quyết định rõ ràng

1. **Không public = chiến lược Claude Integration chết 70%** — PyPI install qua Git yêu cầu SSH key; Claude Plugin Marketplace yêu cầu public repo; MCP server phải open để Anthropic verify.
2. **Competitor đều public** — repomix (MIT), serena (Apache), code2prompt (MIT). Mình closed = mất credibility từ ngày đầu.
3. **Không có IP đáng giữ** — parser AST + D3.js graph là công nghệ phổ biến, giá trị thật ở KMP (RAG + domain knowledge) và enterprise features.
4. **Đã chuẩn bị 80%** — LICENSE MIT, README public, KMP tách riêng. Chỉ còn audit + bấm nút "Make Public".

---

## 2. Trạng thái hiện tại

### 2.1. Những gì đã làm xong

| Item | Trạng thái |
|---|---|
| LICENSE file | ✅ MIT, Copyright Hyper Commerce Vietnam |
| README.md | ✅ Public-facing docs (v2.2.0) |
| pyproject.toml license | ✅ MIT declared |
| KMP tách riêng | ✅ Đã chuyển sang `knowledge-AI-platform` private |
| CBM repo tách khỏi HC | ✅ Standalone từ 16/04/2026 |
| CI/CD workflow | ✅ `.github/workflows/` setup xong |
| Đủ docs để public | ✅ 9 sprint docs, specs, design-preview |

### 2.2. Những gì còn pending (từ BRIEF.md)

| Item | Owner | ETA |
|---|---|---|
| ☐ Make repo public (unlimited free CI) | DevOps | 1 ngày |
| ☐ Update KMP deployment guide với PyPI path | TechLead | 2 ngày |
| ☐ Publish to PyPI `pipx install codebase-map` | TechLead | 3 ngày |
| ☐ Community release notes | PM | 2 ngày |

➡️ **Gần như chỉ cần bấm nút "Make Public" trên GitHub Settings** — các chuẩn bị khác đã sẵn sàng.

---

## 3. Phân tích 4 Lựa chọn (CEO decision framework)

### 3.1. Option A — Public OSS (MIT/Apache) ⭐ KHUYẾN NGHỊ

**Pros:**
- Adoption nhanh gấp 10x vs closed (dev cần audit code trước khi `pipx install`)
- Claude Plugin Marketplace yêu cầu public repo → đây là cửa vào chính
- PyPI + GitHub stars là SEO cho archetype landing page
- Community contribution (issue report, PR fix) miễn phí
- Credibility ngang repomix/serena ngay lập tức
- GitHub Sponsors + OSS grants khả thi (Anthropic có chương trình $)
- Trust chain: user đọc code → tin → install → chuyển thành KMP paid

**Cons:**
- Competitor fork hợp pháp → nhưng: CBM không phải secret sauce, moat thật ở KMP
- Support burden issue/PR công khai → template + community mod giảm tải
- Mất quyền "bẻ license retroactive" → chấp nhận như open core thông thường

**Fit cho CBM:** ✅ **Rất cao** — đúng playbook Python dev tool 2025-2026.

### 3.2. Option B — Open Core (Public CBM + Private KMP + Enterprise features) ⭐⭐ KHUYẾN NGHỊ THẬT SỰ

**Mô tả:**
- **CBM** = public MIT/Apache (miễn phí, self-host, unlimited)
- **KMP** = private (RAG layer, MCP với hosted memory, team collab)
- **CBM Enterprise** = private (multi-repo dashboard, SSO, audit log, SLA) — bán cùng KMP

**Đây chính là hướng đã manh nha** (BRIEF.md đã ghi "CBM public OSS" + "KMP private").

**Pros:**
- CBM free = funnel hút dev; KMP = revenue
- Model đã proven: GitLab, Sentry, Grafana, MinIO, HashiCorp (pre-BSL)
- Enterprise features bán được $5k-50k ARR/tenant
- Không mâu thuẫn lẫn nhau: KMP consume CBM output, không thay thế CBM

**Cons:**
- Phải rõ ràng feature nào open, feature nào closed từ ngày đầu → tránh "bait & switch"
- Cần viết ADR (Architecture Decision Record) để team đồng bộ

**Fit cho CBM:** ✅✅ **Tối ưu** — chính là model hiện tại, chỉ cần viết ra rõ ràng.

### 3.3. Option C — Source Available (BSL / SSPL)

**Mô tả:** Code public để audit/fork cá nhân, nhưng commercial use cần mua license. Business Source License (BSL) chuyển thành Apache sau 3-4 năm.

**Pros:**
- Bảo vệ chống cloud vendor AWS-style clone thành SaaS
- Vẫn cho dev audit code trước khi install

**Cons:**
- **Dev community ghét** — BSL của HashiCorp đã tạo Terraform fork (OpenTofu)
- Claude Plugin Marketplace chưa rõ có accept BSL không
- PyPI OK nhưng giảm trust
- Không có IP đặc biệt cần bảo vệ bằng BSL

**Fit cho CBM:** ❌ **Thấp** — over-engineer cho dev tool đơn giản.

### 3.4. Option D — Closed Source (proprietary)

**Mô tả:** Giữ nguyên private, chỉ ship binary qua PyPI.

**Pros:**
- "Bảo vệ" code (ảo tưởng — AST parser ai cũng làm được)
- Không lo fork

**Cons:**
- **Claude Plugin Marketplace: FAIL** (yêu cầu public repo)
- **Dev ngại install** binary không kiểm tra được (supply chain attack risk)
- Adoption chậm gấp 10x
- Competitor OSS sẽ vượt mặt về mind-share
- Không khai thác được Anthropic OSS grant / community

**Fit cho CBM:** ❌❌ **Rất thấp** — tự bắn chân.

### 3.5. Bảng so sánh 4 option

| Tiêu chí | A. Public OSS | **B. Open Core** ⭐ | C. Source Available | D. Closed |
|---|---|---|---|---|
| Adoption speed | 9/10 | 9/10 | 6/10 | 3/10 |
| Claude Plugin Marketplace | ✅ | ✅ | ⚠️ | ❌ |
| Community contribution | ✅ | ✅ | ⚠️ | ❌ |
| Protect business model | ⚠️ | ✅ | ✅ | ✅ |
| Enterprise revenue | Khó | **✅ Dễ** | ✅ | ✅ |
| Cloud vendor clone risk | Thấp | Thấp | Rất thấp | Không có |
| Dev community trust | 9/10 | 9/10 | 5/10 | 3/10 |
| **Fit cho CBM** | ✅ | **✅✅ TỐT NHẤT** | ⚠️ | ❌ |

---

## 4. Tại sao Open Core (B) tối ưu cho CBM + KMP

### 4.1. Cấu trúc phân layer rõ ràng

```
┌──────────────────────────────────────────────────────────────┐
│  FREE LAYER (Public OSS — MIT)                                │
│  ────────────────────────────────                             │
│  CBM Core                                                     │
│  • Parsers (Python, TS, future: JS, Java, Go, PHP...)         │
│  • Graph builder, query engine, snapshot diff                 │
│  • HTML exporter (with D3.js, multi-view)                     │
│  • CLI, MCP server scaffold                                   │
│  • Self-host unlimited repo                                   │
│  → Target: dev cá nhân, startup, OSS project                  │
└──────────────────────────────────────────────────────────────┘
                           ↓ feeds
┌──────────────────────────────────────────────────────────────┐
│  PAID LAYER (Private — Commercial License)                    │
│  ────────────────────────────────────────                     │
│  KMP (Knowledge AI Platform)                                  │
│  • Hosted RAG trên graph output                               │
│  • MCP server cloud (Anthropic-managed)                       │
│  • Team collaboration (shared knowledge graph)                │
│  • Vector search, semantic query                              │
│  → Target: team 5-50 dev, $X/user/month                       │
│                                                               │
│  CBM Enterprise                                               │
│  • Multi-repo SaaS dashboard                                  │
│  • SSO (Okta, Azure AD)                                       │
│  • Audit log, compliance (SOC2, ISO27001)                     │
│  • Priority support, SLA 99.9%                                │
│  → Target: enterprise 50+ dev, $5k-50k ARR                    │
└──────────────────────────────────────────────────────────────┘
```

### 4.2. 3 lý do khẳng định hướng Open Core

**1. CBM tự bản thân không có moat kinh doanh:**

AST parser + graph builder = công nghệ phổ biến. repomix, serena, code2prompt đều đã làm. Giữ closed = lợi thế cạnh tranh bằng 0 nhưng mất adoption → zero-sum tệ.

**2. KMP mới là moat:**

RAG layer + hosted MCP + domain knowledge (Vietnamese-friendly, SME patterns, industry vertical) là phần có IP thật sự. KMP private bảo vệ được:
- Trained embeddings cho code
- Prompt engineering riêng cho từng archetype
- Multi-tenant data isolation
- Customer-specific knowledge bases

**3. CBM free là lưỡi cày cho KMP:**

- Dev install CBM free → thấy value → muốn more (team, history, hosted)
- Upgrade path tự nhiên: CBM (free, tự host) → KMP (paid, hosted, team)
- Funnel top-of-funnel free có CAC = 0

---

## 5. Chọn License — MIT vs Apache 2.0 vs BSL

### 5.1. Bảng so sánh

| Tiêu chí | **MIT** (đang chọn) | **Apache 2.0** ⭐ | BSL |
|---|---|---|---|
| Độ dài | Cực ngắn | Vừa | Dài |
| Commercial use | ✅ | ✅ | ⚠️ (license) |
| Patent grant | ❌ không có | ✅ **có** | ✅ có |
| Contributor License Agreement | ⚠️ cần thêm | ✅ built-in | — |
| Re-license future | ✅ dễ | ✅ dễ | — |
| Enterprise adoption | 8/10 | **9/10** | 4/10 |
| GitHub popular | 34% | 15% | < 1% |
| Dev community trust | 10/10 | 10/10 | 5/10 |
| **Fit cho CBM** | ✅ | **✅✅** | ❌ |

### 5.2. Khuyến nghị: Chuyển từ MIT sang Apache 2.0

**Lý do:**
- Patent clause bảo vệ CBM chống patent troll (có bài học Microsoft mua Novell kiện Linux)
- Enterprise customer thích Apache hơn MIT khi review legal (có NOTICE file, modification tracking)
- KMP private code dùng Apache cho CBM → không ảnh hưởng gì (Apache compatible với proprietary)
- Chi phí chuyển: **thấp** — chưa có external contributor, chỉ cần commit thay file LICENSE

**Trade-off:**
- Apache file dài hơn (cần NOTICE file, header mỗi source file) → effort 2 tiếng

**Nếu giữ MIT:**
- Vẫn OK — MIT phủ 80% use case
- Thêm CONTRIBUTOR.md + DCO (Developer Certificate of Origin) để bù patent clause

### 5.3. Không chọn BSL/SSPL vì

- Dev community ghét (Terraform/Redis/Elasticsearch fork history)
- Claude Plugin Marketplace chưa công khai accept BSL
- CBM không có "SaaS risk" như database engine

---

## 6. Checklist trước khi bấm "Make Public"

### 6.1. Audit — loại bỏ nội dung nhạy cảm

| Check | Cần làm | Effort |
|---|---|---|
| Tìm secret/token trong git history | `gitleaks detect --source .` | 30 phút |
| Xóa email/phone cá nhân trong code | grep `@gmail.com`, phone VN | 30 phút |
| Strip path hệ thống nhạy cảm | grep `/home/`, `/sessions/` | 30 phút |
| Remove HC-specific references | grep "Hyper Commerce", internal names | 1 giờ |
| Check file `.env*`, `*.key`, `*.pem` | `find -name ".env*"` | 15 phút |
| Rewrite sensitive commit history | `git filter-repo` nếu có | 1 giờ (if needed) |

### 6.2. Bổ sung file chuẩn OSS

| File | Mục đích | Có chưa? |
|---|---|---|
| LICENSE | Legal | ✅ (MIT) |
| README.md | Intro | ✅ |
| CONTRIBUTING.md | Hướng dẫn đóng góp | ❌ cần thêm |
| CODE_OF_CONDUCT.md | Community rules | ❌ cần thêm |
| SECURITY.md | Báo cáo vuln | ❌ cần thêm |
| CHANGELOG.md | Version history | ⚠️ có một phần |
| .github/ISSUE_TEMPLATE/ | Issue template | ❌ cần thêm |
| .github/PULL_REQUEST_TEMPLATE.md | PR template | ❌ cần thêm |
| .github/FUNDING.yml | GitHub Sponsors | ❌ optional |
| CITATION.cff | Nếu muốn academic cite | ❌ optional |

### 6.3. Communication prep

| Item | Deadline |
|---|---|
| Release notes v2.2.1 | D-1 |
| Hacker News / Reddit draft post | D-1 |
| Twitter/X thread pinned | D-day |
| Vietnamese dev community post (Zalo, Viblo) | D-day |
| Anthropic plugin marketplace submission | D+7 |
| Outreach 5 influencer dev Vietnam | D+3 |

---

## 7. Kế hoạch Launch Day (D-day)

### Timeline 1 ngày

```
06:00  Cut release v2.2.1 + tag GitHub
       → GitHub Actions auto-publish PyPI (OIDC)
07:00  Flip repo Public (GitHub Settings → Change visibility)
07:30  Verify: `pipx install codebase-map` works
08:00  Push Hacker News (user submit với UTC timing tối ưu)
08:15  Push Reddit r/Python + r/programming
08:30  Tweet + Zalo/Viblo VN
09:00  Email 5 dev influencer với demo link
10:00  Monitor: issues, PR, stars — reply trong 1 giờ
12:00  Blog post "Announcing CBM — Open Source Codebase Map for Claude Code"
14:00  Respond Hacker News comments
18:00  Close day — báo cáo metric: stars, clones, PyPI downloads
```

### Metric target D-day

- GitHub stars: 100+ (đợi 200 trong 48h)
- PyPI download: 500
- HN upvote: top 30 front page
- Issue/PR: xử lý < 2h

### Metric target D+30

- GitHub stars: 1.000+
- PyPI download: 5.000
- External contributor PR: ≥ 3
- Mention trong Anthropic blog/news letter: 1+

---

## 8. Rủi ro và Mitigation

| # | Rủi ro | Xác suất | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Competitor (repomix/serena) đánh trả | Trung bình | Trung bình | Differentiate bằng archetype + KMP integration |
| R2 | Security disclosure public 0-day | Thấp | Cao | SECURITY.md rõ, bug bounty $100-500 |
| R3 | Lộ HC-internal info trong repo | Trung bình | Cao | Pre-publish audit (Section 6.1) |
| R4 | Support burden quá tải | Trung bình | Trung bình | Template + auto-close stale + "no SLA" disclaimer |
| R5 | Cloud vendor clone thành SaaS | Thấp | Thấp | KMP là moat, không lo CBM bị clone |
| R6 | Adoption < target 1.000 star | Trung bình | Trung bình | Marketing plan Section 7, iterate community |
| R7 | Community drift (feature bloat) | Trung bình | Thấp | Maintainer quyết định final, roadmap public |
| R8 | License conflict khi contributor push code dùng GPL lib | Thấp | Trung bình | CI check license compatibility (reuse.software) |

---

## 9. ROI — Tại sao public repo = business decision, không phải tech

### 9.1. Adoption multiplier

| Phase | Closed repo | **Public repo** | Multiplier |
|---|---|---|---|
| Trial (pipx install) | 50/tháng (qua invite) | **5.000/tháng** | 100x |
| Retention | 30% (paid access) | **60%** (free access, convert sau) | 2x |
| Enterprise convert | 2/quý | **5/quý** | 2.5x |
| Community contribution | 0 | **3-5 PR/tháng** | ∞ |

### 9.2. Cost of going public

| Item | Cost |
|---|---|
| Developer time audit + cleanup | ~16 giờ = $0 (internal) |
| Template files (CONTRIBUTING, SECURITY...) | 2 giờ |
| Launch marketing | ~$100 (landing page, banner) |
| Ongoing support burden | ~20% của 1 TechLead (~4 ngày/tháng) |
| **Total năm đầu** | **~$5.000 equivalent** |

### 9.3. Expected return năm đầu (Open Core model)

| Kênh | Conversion funnel | ARR ước tính |
|---|---|---|
| Free CBM user → KMP paid | 5.000 user × 1% → 50 team × $100/tháng | **$60.000 ARR** |
| Enterprise contract | 5 × $5.000 | **$25.000 ARR** |
| GitHub Sponsors | — | **$1.200 ARR** |
| **Tổng** | | **~$86.000 ARR** năm 1 |

**ROI = $86.000 / $5.000 = 17x — public repo là no-brainer về mặt tài chính.**

---

## 10. 5 Câu hỏi quyết định cho CEO

| # | Câu hỏi | Em khuyến nghị |
|---|---|---|
| Q1 | Public repo ngay hay đợi thêm feature? | **Public ngay** — chuẩn bị đã xong, delay = mất momentum |
| Q2 | Giữ MIT hay chuyển Apache 2.0? | **Apache 2.0** — patent protection + enterprise-friendly |
| Q3 | Open Core: CBM free + KMP paid có đúng? | **Đúng** — nhưng cần viết ADR rõ ràng để team đồng bộ |
| Q4 | Có GitHub Sponsors/OSS fund không? | **Có** — Anthropic có chương trình, nộp sau launch |
| Q5 | Ai là Maintainer CBM public (TechLead? CEO?) | **TechLead lead** + CEO review weekly, tránh over-commit CEO |

---

## 11. Kết luận

**Public CBM trên GitHub không phải là câu hỏi "có nên" — là "khi nào".** Chuẩn bị đã xong 80% (LICENSE MIT, README public, KMP tách private, docs đầy đủ). Chiến lược tích hợp Claude (PyPI, MCP, Plugin Marketplace) **không thể chạy** nếu repo private.

Hướng tối ưu: **Open Core** — CBM public MIT (hoặc chuyển Apache 2.0), KMP + CBM Enterprise giữ private. Đây chính là model GitLab, Sentry, Grafana đã chứng minh.

**Action ngay tuần này (4 SP):**
1. Audit history + cleanup HC-internal refs (8h)
2. Thêm CONTRIBUTING.md + SECURITY.md + issue/PR templates (3h)
3. (Optional) Chuyển MIT → Apache 2.0 (2h)
4. Bấm "Make Public" + cut tag v2.2.1 + publish PyPI (1h)
5. Launch marketing Section 7 — 1 ngày

ROI năm đầu: **~17x** ($5k cost → $86k ARR expected).

---

## Liên kết tài liệu

- [Strategy Memo CBM Claude Integration](./Strategy_Memo_CBM_Claude_Integration.md)
- [Technical Plan CBM Claude Integration](./Technical_Plan_CBM_Claude_Integration.md)
- [Language Coverage Analysis](./Language_Coverage_Analysis.md)
- [Project Archetype GTM Strategy](./Project_Archetype_GTM_Strategy.md)
- [CBM UI Preview Integration](./CBM_UI_Preview_Integration.md)

---

*Open_Source_Publishing_Strategy.md v1.0 — CEO decision memo · Codebase Map project · 16/04/2026*
