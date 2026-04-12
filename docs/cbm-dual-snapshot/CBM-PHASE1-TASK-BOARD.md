# Sprint Task Board — CBM Phase 1 (v2.1)
# Graph Metadata + Snapshot Versioning

> **Sprint:** CBM-P1 · **Total:** 7 SP · **Duration:** 5 ngày (1 tuần)
> **Start condition:** KMP M1 done + CEO duyệt plan
> **Status:** 🔥 ACTIVE — CEO approved 12/04/2026 · Day 1
> **Branch:** `feat/cbm-phase1-metadata`
> **Release:** codebase-map **v2.1.0**
> **Created:** 10/04/2026 · @PM + @CTO

---

## TASK BOARD

| Task ID | Task | SP | Assignee | Status | Day | Dependencies |
|---------|------|----|----------|--------|-----|-------------|
| CBM-P1-01 | Thêm `metadata` dict vào `Graph` dataclass + `to_dict()` + `from_dict()` | 1 | TechLead | ✅ Done | D1 | — |
| CBM-P1-02 | CLI flag `generate --label <name>` | 1 | TechLead | ✅ Done | D1 | P1-01 |
| CBM-P1-03 | Snapshot naming: `graph_{label}_{short_sha}.json` + save vào `.codebase-map-cache/snapshots/` | 1 | TechLead | ⬜ TODO | D2 | P1-01, P1-02 |
| CBM-P1-04 | Command `snapshots list` — hiển thị table snapshots | 1 | TechLead | ⬜ TODO | D3 | P1-03 |
| CBM-P1-05 | Command `snapshots clean --keep N` (default 10) | 0.5 | TechLead | ⬜ TODO | D3 | P1-03 |
| CBM-P1-06 | Backward compat: đọc graph v1.x (không metadata) → inject empty metadata | 1 | TechLead | ✅ Done | D1 | P1-01 |
| CBM-P1-07 | CI workflow: `cbm-baseline.yml` — auto-generate baseline + artifact upload | 1.5 | TechLead | ⬜ TODO | D4-D5 | P1-02, P1-03 |
| — | Unit tests + lint gate | — | TechLead | ⬜ TODO | D5 | All |
| — | PR → /review-gate → CEO approve | — | Team | ⬜ TODO | D5 | All |

---

## DAILY PLAN

### Day 1 — Foundation (2 SP)

**CBM-P1-01: Graph Metadata** (1 SP)
- Mở `codebase_map/graph/models.py`
- Thêm field `metadata: dict` vào `Graph` dataclass (default `{}`)
- Update `Graph.to_dict()`: output `{"metadata": {...}, "nodes": [...], "edges": [...]}`
- Update `Graph.from_dict()`: parse metadata, fallback `{}` nếu không có
- Metadata schema:
  ```python
  metadata = {
      "version": "2.1",
      "generated_at": "2026-04-10T14:30:00+07:00",  # ISO 8601
      "commit_sha": "a7bd55e",                        # git rev-parse HEAD
      "branch": "develop",                             # git branch --show-current
      "label": "baseline",                             # from --label flag
      "generator_version": "2.1.0",                    # from __init__.py
      "source_paths": ["backend/app/"],                # from config
      "stats": {
          "total_functions": 847,
          "total_files": 234,
          "total_edges": 1523
      }
  }
  ```
- Thêm helper `_collect_git_info()` trong `graph/builder.py` (sử dụng `subprocess.run`)

**CBM-P1-02: CLI --label Flag** (1 SP)
- Mở `codebase_map/cli.py`
- Thêm `--label` argument vào `_cmd_generate()` (default: `"auto"`)
- Khi label = `"auto"` → sinh tự động: `{branch}_{short_sha}_{timestamp}`
- Truyền label vào `GraphBuilder` → inject metadata khi build xong

### Day 2 — Snapshot Storage (1 SP)

**CBM-P1-03: Snapshot Naming + Save** (1 SP)
- Tạo module mới: `codebase_map/snapshot.py`
- Class `SnapshotManager`:
  ```python
  class SnapshotManager:
      def __init__(self, cache_dir=".codebase-map-cache/snapshots"):
          ...
      def save(self, graph, label, output_dir=None) -> Path:
          """Save graph with naming: graph_{label}_{short_sha}.json"""
          ...
      def list_snapshots(self) -> list[SnapshotInfo]:
          """List all saved snapshots, sorted by date desc"""
          ...
      def clean(self, keep=10):
          """Remove old snapshots, keep N newest"""
          ...
      def load(self, label_or_path) -> Graph:
          """Load graph from label name or file path"""
          ...
  ```
- Naming convention: `graph_{label}_{short_sha}.json`
- Save location: `.codebase-map-cache/snapshots/` (trong project root)
- Update `_cmd_generate()`: sau khi generate → auto-save snapshot

### Day 3 — CLI Commands (1.5 SP)

**CBM-P1-04: snapshots list** (1 SP)
- Thêm subcommand `snapshots list` vào CLI
- Output format (bảng):
  ```
  SNAPSHOTS (5 found)
  ┌──────────┬─────────────────────┬──────────┬─────────┬───────┬───────┐
  │ Label    │ Date                │ Branch   │ SHA     │ Nodes │ Edges │
  ├──────────┼─────────────────────┼──────────┼─────────┼───────┼───────┤
  │ baseline │ 2026-04-10 10:00:00 │ develop  │ a7bd55e │ 847   │ 1523  │
  │ post-dev │ 2026-04-10 14:30:00 │ feat/xyz │ 1207b8d │ 859   │ 1541  │
  │ ...      │ ...                 │ ...      │ ...     │ ...   │ ...   │
  └──────────┴─────────────────────┴──────────┴─────────┴───────┴───────┘
  ```

**CBM-P1-05: snapshots clean** (0.5 SP)
- Thêm subcommand `snapshots clean --keep N`
- Default `--keep 10`
- Xoá snapshots cũ nhất trước, giữ N mới nhất
- Confirm message: "Removed X snapshots, kept Y"

### Day 4 — Backward Compat + CI (2.5 SP)

**CBM-P1-06: Backward Compatibility** (1 SP)
- Khi `Graph.from_dict()` nhận data không có key `"metadata"` (graph v1.x):
  - Inject empty metadata: `{"version": "1.x-legacy", "generated_at": null, ...}`
  - Log warning: "Legacy graph format detected. Metadata will be empty."
- Khi `SnapshotManager.load()` nhận graph v1.x → same behavior
- Test: load graph file từ v2.0.1 hiện tại → verify parse thành công

**CBM-P1-07: CI Workflow — Baseline Generator** (1.5 SP)
- Tạo file `.github/workflows/cbm-baseline.yml` (draft từ CTO CI Proposal section 5.1)
- Adjust cho codebase-map v2.1 features (`--label`, artifact upload)
- Tạo file `.github/workflows/cbm-post-merge.yml` (section 5.3)
- Verify: workflow syntax check (`actionlint` nếu có)
- **Note:** Workflow 2 (PR Impact) thuộc Phase 2 (cần diff engine)

### Day 5 — Quality Gate + Ship

- Unit tests cho tất cả new features:
  - `test_graph_metadata.py`: metadata inject/parse, to_dict/from_dict roundtrip
  - `test_snapshot_manager.py`: save/list/clean/load
  - `test_backward_compat.py`: load v1.x graph → verify
  - `test_cli_label.py`: --label flag, auto-label generation
- Lint gate: `black --check . && isort --check . && flake8`
- Self-test: chạy `codebase-map generate --label test` trên chính repo
- Tạo PR → /review-gate (Tester → CTO → Designer) → CEO approve

---

## DEFINITION OF DONE

1. ✅ `codebase-map generate` output JSON có `metadata` block đầy đủ
2. ✅ `--label` flag hoạt động, auto-label khi không truyền
3. ✅ Snapshots lưu vào `.codebase-map-cache/snapshots/` đúng naming
4. ✅ `snapshots list` hiển thị table đầy đủ thông tin
5. ✅ `snapshots clean --keep N` xoá đúng, không lỗi
6. ✅ Graph v1.x (không metadata) vẫn đọc được — backward compat
7. ✅ CI workflow files có sẵn (chưa enable, chờ Phase 2 + CEO duyệt)
8. ✅ Unit tests pass, lint clean, CI green
9. ✅ PR approved qua 3-tier review gate

---

## RISK REGISTER

| Risk | Impact | Likelihood | Mitigation |
|------|--------|:----------:|-----------|
| Git subprocess fail (bare repo, detached HEAD) | Medium | Medium | Try/except + fallback: commit_sha="unknown", branch="detached" |
| Snapshot directory permission error | Low | Low | Tạo directory với `os.makedirs(exist_ok=True)` |
| Graph v1.x format variations | Medium | Low | Test với 3+ graph files từ v1.0, v2.0, v2.0.1 |
| CI workflow syntax error | Low | Medium | Validate với `actionlint` + dry-run trước khi ship |

---

## ACCEPTANCE CRITERIA (CEO Review)

Khi CEO review, cần demo:

1. **Generate baseline:** `codebase-map generate -c codebase-map.yaml --label baseline` → file `graph_baseline_{sha}.json` có metadata đầy đủ
2. **Generate post-dev:** `codebase-map generate --label post-dev` → file riêng, không overwrite baseline
3. **List snapshots:** `codebase-map snapshots list` → bảng rõ ràng, dễ đọc
4. **Backward compat:** Load graph cũ (v2.0.1) → không lỗi, warning hợp lý
5. **CI ready:** File YAML có sẵn, chỉ cần copy vào HC repo khi cần

---

*CBM Phase 1 Task Board v1.0 · Created 10/04/2026 · @PM + @CTO*
*Codebase-Map Dual-Snapshot · Sprint 1 of 2*
