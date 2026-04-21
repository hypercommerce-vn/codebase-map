---
name: codebase-map-saas
description: >
  SaaS B2B Onboarding — onboard new engineers to CRM, CDP, eCommerce, or
  multi-tenant SaaS platforms. Maps modules, domain clusters, API surface,
  data models, entry points, tier/plan gating logic.
  Gói SaaS B2B Onboarding — onboard kỹ sư mới vào nền tảng CRM, CDP, eCommerce,
  hay SaaS multi-tenant. Map module, cụm domain, bề mặt API, data model,
  entry point, logic cổng gói/tier.
  Triggers: "onboard this SaaS", "onboard SaaS này", "what APIs do we expose",
  "các API chúng ta expose", "pricing tier logic", "logic pricing tier",
  "multi-tenant boundaries", "ranh giới multi-tenant", "customer flow",
  "luồng khách hàng", "feature gate logic", "logic feature gate".
---

# Codebase Map — SaaS Onboarding Pack

## Purpose / Mục đích

**EN:** SaaS B2B codebases share a recognizable shape — HTTP routes grouped
by domain (customers, orders, billing, tenants), a subscription/tier module
that gates features, data models with tenant-scoped keys, and integrations
with external systems (Stripe, Zalo, Shopify, etc.). This pack reuses the
`codebase-map` MCP tools with SaaS-aware framing so new engineers can
onboard in one pass instead of a week of tribal knowledge.

**VI:** Các codebase SaaS B2B có cấu trúc nhận biết được — HTTP route nhóm
theo domain (customer, order, billing, tenant), một module subscription/tier
quản lý cổng tính năng, data model có key theo tenant, và các integration
với hệ thống ngoài (Stripe, Zalo, Shopify, v.v.). Pack này tái sử dụng các
MCP tool của `codebase-map` với khung nhìn SaaS-aware để kỹ sư mới onboard
trong một lần chạy thay vì một tuần tra cứu kiến thức tribal.

## Prerequisite / Điều kiện tiên quyết

**EN:** Requires `codebase-map >= 2.4.0` with MCP extras. A `graph.json` file
must exist at `docs/function-map/graph.json` (run `codebase-map generate`
first, or use `/cbm-onboard` from the main plugin).

**VI:** Cần `codebase-map >= 2.4.0` với MCP extras. File `graph.json` phải
tồn tại tại `docs/function-map/graph.json` (chạy `codebase-map generate`
trước, hoặc dùng `/cbm-onboard` từ plugin chính).

```bash
codebase-map --version  # should be 2.4.0+
ls docs/function-map/graph.json 2>/dev/null || echo "RUN /cbm-onboard FIRST"
```

## Domains this pack recognizes / Các domain pack này nhận diện

**EN:** The skill probes for common SaaS domain keywords. Typical clusters:

**VI:** Skill tìm các keyword domain SaaS phổ biến. Các cụm điển hình:

| Domain | Keywords searched |
|--------|-------------------|
| **Customer / CRM** | `customer`, `contact`, `lead`, `account` |
| **Order / Commerce** | `order`, `cart`, `invoice`, `product`, `catalog` |
| **Billing / Subscription** | `subscription`, `plan`, `tier`, `billing`, `payment`, `stripe` |
| **Tenant / Multi-tenant** | `tenant`, `workspace`, `org`, `organization` |
| **Auth / Access** | `auth`, `login`, `session`, `role`, `permission`, `policy` |
| **Integration** | `webhook`, `zalo`, `shopify`, `facebook`, `oauth` |

## Workflow — Three questions this skill answers / Ba câu hỏi skill này trả lời

### 1. "I just joined. What's this codebase?" / "Tôi mới vào. Codebase này là gì?"

**EN:** Use `/saas-onboard` (slash command in this pack). It runs
`cbm_search` across the 6 SaaS domain keyword groups above, calls
`cbm_api_catalog` for the HTTP surface, and returns a 7-bullet onboarding
brief covering scale, domains, API count, entry points, data models,
tier/subscription module, and integration points.

**VI:** Dùng `/saas-onboard`. Nó chạy `cbm_search` qua 6 nhóm keyword SaaS
bên trên, gọi `cbm_api_catalog` cho bề mặt HTTP, và trả về brief onboarding
7 gạch đầu dòng gồm scale, domain, số API, entry point, data model, module
tier/subscription, và integration.

### 2. "What APIs do we expose?" / "Chúng ta expose những API nào?"

**EN:** Use `/saas-apis`. Wraps `cbm_api_catalog` with filter flags (by HTTP
method, by domain). Output is a grouped Markdown table ready to paste into
API docs or a Swagger-checklist.

**VI:** Dùng `/saas-apis`. Bọc `cbm_api_catalog` với cờ filter (theo HTTP
method, theo domain). Output là bảng Markdown nhóm sẵn, paste được vào doc
API hay checklist Swagger.

### 3. "Where's the tier/plan gating?" / "Logic cổng tier/plan nằm đâu?"

**EN:** Use `/saas-tier-logic`. Searches for `tier`, `plan`, `subscription`
patterns, then runs `cbm_impact` on each match to show which features are
gated behind which plan. Output flags any function that reads plan/tier
without a centralized policy call — usually a bug pattern in B2B SaaS.

**VI:** Dùng `/saas-tier-logic`. Tìm pattern `tier`, `plan`, `subscription`,
rồi chạy `cbm_impact` trên từng match để hiện tính năng nào bị gate bởi
plan nào. Output đánh dấu function nào đọc plan/tier mà không gọi policy
tập trung — thường là pattern bug trong SaaS B2B.

## MCP tools used / Các MCP tool được sử dụng

**EN:** This pack does NOT register new MCP tools. It reuses the 5 from the
main `codebase-map` plugin:

**VI:** Pack này KHÔNG đăng ký MCP tool mới. Nó tái sử dụng 5 tool từ plugin
`codebase-map` chính:

- `cbm_search "<domain>"` — discover domain modules (customer, order, billing…)
- `cbm_query "<model>"` — expose a data model's shape + callers
- `cbm_impact "<name>"` — blast radius for a tier/plan logic change
- `cbm_api_catalog(method=, domain=)` — filtered API listing
- `cbm_snapshot_diff` — compare domain structure across refactors

## Rules / Quy tắc

**EN:**

- **Always run `/saas-onboard` first** on a new SaaS repo. It establishes
  scale + domain clusters before you dive into specifics.
- **Tenant isolation is sacred.** If `/saas-tier-logic` finds a plan check
  that does not also check `tenant_id` / `org_id`, flag it — multi-tenant
  SaaS bug pattern.
- **API catalog != spec.** `/saas-apis` lists what is coded, not what is
  documented. Use it to find undocumented endpoints and close the doc gap.
- **Webhook and integration handlers count as public APIs** — they are
  callable from outside. `/saas-apis` includes them.

**VI:**

- **Luôn chạy `/saas-onboard` trước** trên một SaaS repo mới. Nó xác lập
  scale + cụm domain trước khi bạn đào chi tiết.
- **Tenant isolation là thiêng liêng.** Nếu `/saas-tier-logic` tìm ra một
  check plan mà không đồng thời check `tenant_id` / `org_id`, đánh dấu nó
  ngay — đây là pattern bug multi-tenant SaaS.
- **API catalog không phải là spec.** `/saas-apis` liệt kê cái đang code,
  không phải cái đã document. Dùng nó để tìm endpoint chưa có doc và đóng
  gap doc.
- **Webhook và integration handler cũng là API public** — gọi được từ
  ngoài. `/saas-apis` bao gồm luôn.

## When not to use / Khi nào không dùng

**EN:**

- The repo is not a SaaS product (library, CLI tool, static site) — use the
  main `codebase-map` skill instead.
- You only need a single function's blast radius — `/cbm-impact` from the
  main plugin is faster.
- The question is about product positioning, not code — this skill maps
  code, not market.

**VI:**

- Repo không phải sản phẩm SaaS (library, CLI tool, static site) — dùng
  skill `codebase-map` chính.
- Chỉ cần blast radius một function — `/cbm-impact` của plugin chính nhanh hơn.
- Câu hỏi về định vị sản phẩm, không phải code — skill này map code, không
  map market.

## Links / Liên kết

- Main plugin: [`codebase-map`](https://github.com/hypercommerce-vn/codebase-map)
- GTM brief: [Project Archetype GTM Strategy](https://github.com/hypercommerce-vn/codebase-map/tree/main/docs/active/cbm-claude-integration)
- Issues: https://github.com/hypercommerce-vn/codebase-map/issues
