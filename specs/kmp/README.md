# KMP — Knowledge Memory Platform Specs
> **Phase 2 Foundation** · Created: 08/04/2026 · CEO approved: 08/04/2026

---

## 🎯 Context

**KMP (Knowledge Memory Platform)** là nền tảng lõi mà mọi vertical Memory của Hyper Commerce kế thừa. Codebase Memory là **vertical đầu tiên** — rebuild từ Codebase Map v1.1 theo kiến trúc platform-first.

**Quyết định pivot:** CEO confirm Phương án B+ (08/04/2026) — rebuild từ đầu theo platform architecture thay vì addendum v1.2. Không có sunk cost cần bảo vệ vì Codebase Memory chưa bắt đầu code.

**Định vị công ty:** Hyper Commerce = "Knowledge OS company VN" — mở rộng từ 1 vertical (Codebase) sang 8+ vertical tương lai (Legal, Sales, Research, Curriculum, Manufacturing, Medical, Design System, Accounting).

---

## 📚 Tài liệu trong thư mục này

| File | Mô tả | Owner |
|------|-------|-------|
| [`architecture.md`](./architecture.md) | KMP Core architecture — 5 design principles, package layout, 6 core services, abstract base classes, extension contract, Hello vertical, dependency rule, CEO sign-off 5/5 decisions | @CTO |
| [`fdd-v2.md`](./fdd-v2.md) | FDD v2.0 rewrite — 99 SP / 9 tuần (M0→M4), NFRs, risk register R-T1→R-T6, DoD, sign-off | @CTO + @BA |
| [`user-stories-m0-m1.md`](./user-stories-m0-m1.md) | 6 M0 stories + 14 M1 stories — GIVEN/WHEN/THEN, business rules, edge cases, 32 SP total | @BA |
| [`jd-platform-engineer.md`](./jd-platform-engineer.md) | JD Knowledge OS Platform Engineer — contractor part-time 6 tuần, 4-5h/ngày, 350K-600K VND/h | @BA + @PO |
| [`SESSION-STATE.md`](./SESSION-STATE.md) | Session state file — B+ decision, deliverables, pending actions, resume protocol | @PM |

---

## 🗺️ Resume protocol — đọc theo thứ tự

1. [`architecture.md`](./architecture.md) — hiểu kiến trúc lõi trước
2. [`fdd-v2.md`](./fdd-v2.md) — chi tiết requirements + sprint plan
3. [`user-stories-m0-m1.md`](./user-stories-m0-m1.md) — user stories implement được ngay
4. [`SESSION-STATE.md`](./SESSION-STATE.md) — trạng thái hiện tại + pending actions
5. [`jd-platform-engineer.md`](./jd-platform-engineer.md) — JD tuyển contractor

---

## 🗓️ Roadmap KMP MVP (99 SP / 9 tuần)

| Sprint | Tuần | Focus | SP |
|--------|------|-------|----|
| **M0** | 1 | KMP Core skeleton + Hello vertical + LICENSE + vault-format-spec | **8** *(CEO +2)* |
| **M1** | 2-3 | Codebase Vault + Quick Win Mode | 26 |
| **M2** | 4-5 | Ask + MCP + Multi-LLM | 28 |
| **M3** | 6-7 | Onboarding + Insights dashboard | 21 |
| **M4** | 8-9 | Drift + License + Soft launch | 18 |

**Task board Sprint M0:** [`../../project/CM-MEM-M0-TASK-BOARD.md`](../../project/CM-MEM-M0-TASK-BOARD.md)

---

## ⚖️ CEO Sign-off (08/04/2026)

**5/5 Open Decisions duyệt** (xem chi tiết ở `architecture.md` section 9.bis):

- ✅ **D-1** Package name: `knowledge_memory`
- ✅ **D-2** Monorepo
- ✅ **D-3** MIT Core + Proprietary Pro feature
- ✅ **D-4** Public vault format spec ("open vault, closed engine" moat)
- ✅ **D-5** Hello vertical ship cùng v1.0

**3 yêu cầu bổ sung CEO → merge vào M0:**

1. **KMP-M0-07** — `docs/vault-format-spec.md` ≤ 5 trang (CTO)
2. **KMP-M0-08** — `LICENSE` (MIT) + `LICENSE-PRO` template + CI lint check
3. **KMP-M0-05 update** — `verticals/hello/README.md` cho dev mới đọc 5 phút

---

## 🔗 Liên kết ngoài thư mục

- **Task board M0:** [`../../project/CM-MEM-M0-TASK-BOARD.md`](../../project/CM-MEM-M0-TASK-BOARD.md)
- **BRIEF tổng:** [`../../BRIEF.md`](../../BRIEF.md) — section "KMP PIVOT"
- **CLAUDE.md orchestrator:** [`../../CLAUDE.md`](../../CLAUDE.md)
- **Sales script Codebase Map:** [`../sales/sales-script-codebase-map.md`](../sales/sales-script-codebase-map.md)

---

*specs/kmp/README.md — Phase 2 Foundation Index · @PM · 08/04/2026*
