# Codebase Map — AI Agent Team
# HC-AI | ticket: FDD-TOOL-CODEMAP
**7 AI Agents · 4-Layer Org Structure · CEO: Đoàn Đình Tỉnh**

> Mỗi agent có một SKILL.md định nghĩa role, trách nhiệm, template và KPIs.
> Kích hoạt agent bằng cách đọc file SKILL.md tương ứng trước khi bắt đầu hội thoại.
> Adapted from Hyper Commerce Agent Team (12 roles → 7 roles cho dev tool).

---

## Cơ Cấu Tổ Chức (4 Lớp)

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 0 — CEO                                              │
│  👤 Đoàn Đình Tỉnh — Quyết định cuối cùng, approve PR      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 1 — STRATEGY                                         │
│  💻 CTO       — Code quality, architecture, security        │
└────────┬────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────┐
│  LAYER 2 — PRODUCT                                           │
│  📅 Project Manager  — Sprint tracking, risk, velocity       │
│  📋 Product Owner    — Backlog, scope, user stories          │
│  📊 Business Analyst — Spec, business rules, flow analysis   │
└────────┬────────────────────────────────────────────────────┘
         │
┌────────▼────────────────────────────────────────────────────┐
│  LAYER 3 — DELIVERY                                          │
│  🏗️ Tech Lead   — Architecture, code review, implementation  │
│  🎨 Designer    — D3.js/HTML design review, visual accuracy  │
│  🧪 Tester      — Functional test, regression, DoD verify    │
└─────────────────────────────────────────────────────────────┘
```

---

## Danh Sách Agents (7 roles)

| # | Agent | Layer | Skill File | Mindset |
|---|-------|-------|-----------|---------|
| - | 👤 **CEO** | 0 | *(Đoàn Đình Tỉnh)* | Visionary · Decisive · Quality-first |
| 1 | 💻 **CTO** | 1 — Strategy | `cto/SKILL.md` | "Code quality is the product." |
| 2 | 📅 **Project Manager** | 2 — Product | `project-manager/SKILL.md` | "Delivery is a habit." |
| 3 | 📋 **Product Owner** | 2 — Product | `product-owner/SKILL.md` | "User value first." |
| 4 | 📊 **Business Analyst** | 2 — Product | `business-analyst/SKILL.md` | "Every ambiguity is a future bug." |
| 5 | 🏗️ **Tech Lead** | 3 — Delivery | `techlead/SKILL.md` | "Make it work, make it right." |
| 6 | 🎨 **Designer** | 3 — Delivery | `designer/SKILL.md` | "Design solves problems." |
| 7 | 🧪 **Tester** | 3 — Delivery | `tester/SKILL.md` | "Ship fast, break nothing." |

---

## Collaboration Map

```
CEO ──► CTO        : Architecture decisions, quality standards
CEO ──► PM         : Sprint status, risk escalation

CTO ──► TechLead   : Code review, implementation guidance
CTO ──► Designer   : Design review standards

PM  ──► PO         : Sprint execution, scope management
PM  ──► TechLead   : Velocity, blockers
PM  ──► Tester     : QA gate, DoD verification

PO  ──► BA         : Requirements breakdown, business rules
PO  ──► Designer   : Design requirements
PO  ──► TechLead   : Feasibility check, effort estimate

BA  ──► Designer   : Functional flow → visual design
BA  ──► TechLead   : Spec → implementation
BA  ──► Tester     : Business rules → test scenarios
```

---

## Cách Sử Dụng

```
"Hãy đóng vai [Agent Name]. Đọc file agents/[agent-dir]/SKILL.md và
hoạt động theo đúng skill đó. Nhiệm vụ của tôi là: [mô tả nhiệm vụ]"
```

---

*Codebase Map Agent Team v1.0 — Adapted from HC v2.0 | 06/04/2026*
*7 AI Agents · CEO: Đoàn Đình Tỉnh · hypercdp@gmail.com*
