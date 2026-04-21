# Codebase Map — SaaS Onboarding Pack

Archetype plugin for SaaS B2B engineering teams onboarding new engineers on
CRM, CDP, eCommerce, or multi-tenant platforms.

Gói archetype dành cho team engineering SaaS B2B khi onboard kỹ sư mới vào
nền tảng CRM, CDP, eCommerce, hay multi-tenant.

---

## English

### What ships in this pack

| Component | Purpose |
|-----------|---------|
| Skill `codebase-map-saas` | Auto-triggers on "onboard this SaaS", "what APIs do we expose", "pricing tier logic", "multi-tenant boundaries", "customer flow", "feature gate logic" |
| `/saas-onboard` | 7-bullet onboarding brief — modules, domains, API surface, data models, entry points, tier logic, integrations |
| `/saas-apis [filter]` | API catalog filtered by HTTP method, domain, or path prefix — output is a Markdown table |
| `/saas-tier-logic` | Audit plan/tier/subscription gating — central vs scattered, with tenant-isolation cross-check |

This pack **reuses the main plugin's 5 MCP tools** — no new backend, no new
Python. The value is SaaS-specific domain scanning (6 B2B keyword groups),
API catalog reshaping into team-wiki format, and the tier-logic audit with
multi-tenant isolation flag.

### Prerequisite

This pack depends on `codebase-map[mcp]>=2.4.0`. The post-install hook
installs it automatically via pipx. If you already have the main
`codebase-map` plugin installed, the MCP server is shared.

### Install

In Claude Code:

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map-saas@hypercommerce-vn
```

### First use

```bash
cd /path/to/your/saas-repo
codebase-map generate -c codebase-map.yaml
```

Then in Claude Code:

```
/saas-onboard
```

Claude returns a 7-bullet onboarding brief. From there:

```
/saas-apis POST               # all POST endpoints
/saas-apis customer           # all customer-domain endpoints
/saas-tier-logic              # audit subscription gating
```

### When to use vs main plugin

| Question | Use |
|----------|-----|
| "I just joined this SaaS — what's here?" | `/saas-onboard` |
| "General repo overview" (non-SaaS) | `/cbm-onboard` (main plugin) |
| "What APIs do we expose?" | `/saas-apis` |
| "Is our plan gating safe?" | `/saas-tier-logic` |
| "What breaks if I change X?" | `/cbm-impact` (main plugin) |

### Domains recognized

Customer / CRM · Order / Commerce · Billing / Subscription · Tenant / Multi-tenant · Auth / Access · Integrations (Stripe, Zalo, Facebook)

### Links

- Main repo: https://github.com/hypercommerce-vn/codebase-map
- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
- License: MIT

---

## Tiếng Việt

### Nội dung pack

| Thành phần | Mục đích |
|------------|----------|
| Skill `codebase-map-saas` | Tự kích hoạt khi gặp "onboard SaaS này", "các API chúng ta expose", "logic pricing tier", "ranh giới multi-tenant", "luồng khách hàng", "logic feature gate" |
| `/saas-onboard` | Brief onboarding 7 gạch đầu dòng — module, domain, bề mặt API, data model, entry point, logic tier, integration |
| `/saas-apis [filter]` | Catalog API lọc theo HTTP method, domain, hay path prefix — output bảng Markdown |
| `/saas-tier-logic` | Audit gating plan/tier/subscription — tập trung vs phân tán, kèm cross-check tenant-isolation |

Pack này **tái sử dụng 5 MCP tool của plugin chính** — không có backend
mới, không có Python mới. Giá trị nằm ở việc scan domain chuyên cho SaaS
(6 nhóm keyword B2B), reshape catalog API thành format dùng được cho team
wiki, và audit tier-logic kèm flag tenant-isolation.

### Điều kiện tiên quyết

Pack này phụ thuộc `codebase-map[mcp]>=2.4.0`. Post-install hook tự cài
qua pipx. Nếu bạn đã cài plugin `codebase-map` chính, MCP server dùng chung.

### Cài đặt

Trong Claude Code:

```
/plugin marketplace add hypercommerce-vn/claude-plugins
/plugin install codebase-map-saas@hypercommerce-vn
```

### Dùng lần đầu

```bash
cd /path/to/your/saas-repo
codebase-map generate -c codebase-map.yaml
```

Sau đó trong Claude Code:

```
/saas-onboard
```

Claude trả về brief onboarding 7 gạch đầu dòng. Từ đó:

```
/saas-apis POST               # tất cả endpoint POST
/saas-apis customer           # tất cả endpoint domain customer
/saas-tier-logic              # audit gating subscription
```

### Khi nào dùng pack này vs plugin chính

| Câu hỏi | Dùng |
|---------|------|
| "Tôi mới vào SaaS này — có gì?" | `/saas-onboard` |
| "Overview repo chung" (không phải SaaS) | `/cbm-onboard` (plugin chính) |
| "Chúng ta expose API nào?" | `/saas-apis` |
| "Plan gating có an toàn không?" | `/saas-tier-logic` |
| "Đổi X cái gì vỡ?" | `/cbm-impact` (plugin chính) |

### Domain được nhận diện

Customer / CRM · Order / Commerce · Billing / Subscription · Tenant / Multi-tenant · Auth / Access · Integration (Stripe, Zalo, Shopify, Facebook)

### Liên kết

- Repo chính: https://github.com/hypercommerce-vn/codebase-map
- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
- License: MIT
