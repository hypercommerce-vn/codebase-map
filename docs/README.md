# docs/ — Codebase Map Documentation

> Cấu trúc chia 2 nhóm: **active** (đang dev, cần tham chiếu thường xuyên) và **reference** (đã ship hoặc lịch sử).

---

## 📂 Cấu trúc

```
docs/
├── README.md                      ← File này
├── active/                        ← Đang dev / cần cho phát triển hiện tại
│   ├── ONBOARDING.md              ← Hướng dẫn người mới vào dự án
│   └── cbm-claude-integration/    ← Initiative 2026-04-16 (7 docs, pending CEO D1-D7)
│       ├── Strategy_Memo_CBM_Claude_Integration.md
│       ├── Technical_Plan_CBM_Claude_Integration.md
│       ├── Language_Coverage_Analysis.md
│       ├── Project_Archetype_GTM_Strategy.md
│       ├── CBM_UI_Preview_Integration.md
│       ├── Open_Source_Publishing_Strategy.md
│       └── Phase2_MCP_Explainer.md
├── reference/                     ← Đã ship / lịch sử tham chiếu
│   ├── cbm-dual-snapshot/         ← v2.1 (CBM-P1) + v2.2 (CBM-P2) — đã ship 12/04/2026
│   ├── releases/                  ← Release notes
│   └── reviews/                   ← Review gate reports (Tester/CTO/Designer)
└── function-map/                  ← Generated output (chạy `codebase-map generate`)
    ├── graph.json
    └── index.html
```

---

## 🔎 Khi nào đọc gì

| Nếu bạn là... | Đọc |
|---------------|-----|
| Người mới join dự án | `active/ONBOARDING.md` |
| CEO/PO cần review initiative | `active/cbm-claude-integration/Strategy_Memo_CBM_Claude_Integration.md` |
| Dev triển khai Claude Integration | `active/cbm-claude-integration/Technical_Plan_CBM_Claude_Integration.md` |
| Hiểu Dual-Snapshot design đã ship | `reference/cbm-dual-snapshot/Proposal_Dual_Snapshot_CBM.md` |
| Kiểm tra lịch sử review PR | `reference/reviews/ReviewGate_PR*.md` |
| Xem graph CBM hiện tại | Mở `function-map/index.html` trong browser |

---

## 📜 Quy ước đặt file

1. **Đang active** → `docs/active/<topic>/`
2. **Đã ship v/sprint** → chuyển sang `docs/reference/<topic>/` (giữ nguyên nội dung, chỉ đổi path)
3. **Review gate reports** → `docs/reference/reviews/ReviewGate_<PR>_Round<N>_<date>.md`
4. **Release notes** → `docs/reference/releases/<version>-<target>.md`
5. **Generated outputs** → `docs/function-map/` (không commit `graph.json` nếu đã .gitignore)

---

## 🔁 Khi ship 1 initiative

Sau khi feature/phase được ship lên production:
1. Di chuyển docs của initiative từ `docs/active/<topic>/` sang `docs/reference/<topic>/`
2. Update link trong `CLAUDE.md`, `BRIEF.md`, `project/board.html`
3. Giữ nguyên nội dung file — chỉ đổi path

---

*docs/README.md v1.0 — Created 18/04/2026*
