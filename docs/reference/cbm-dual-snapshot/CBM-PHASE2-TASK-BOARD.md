# Sprint Task Board — CBM Phase 2 (v2.2)
# Dual-Snapshot Diff Engine

> **Sprint:** CBM-P2 · **Total:** 12 SP · **Duration:** 10 ngày (2 tuần)
> **Prerequisite:** CBM Phase 1 (v2.1) shipped + merged
> **Status:** ✅ COMPLETE — 12/04/2026 · 12/12 SP · 3 PRs (#71 #72 #74) · 582 tests
> **Branch:** `feat/cbm-phase2-diff-engine`
> **Release:** codebase-map **v2.2.0**
> **Created:** 10/04/2026 · @PM + @CTO

---

## TASK BOARD

| Task ID | Task | SP | Assignee | Status | Day | Dependencies |
|---------|------|----|----------|--------|-----|-------------|
| CBM-P2-01 | `SnapshotDiff` class: load 2 graphs → compute node diff | 3 | TechLead | ✅ Done | D1 | Phase 1 done |
| CBM-P2-02 | Edge diff: new/removed caller relationships | 2 | TechLead | ✅ Done | D1 | P2-01 |
| CBM-P2-03 | Affected callers: transitive 1-level, `--depth N` max 3 | 2 | TechLead | ✅ Done | D1 | P2-01, P2-02 |
| CBM-P2-04 | Rename detection: signature matching (name + params + return_type) | 2 | TechLead | ✅ Done | D1 | P2-01 |
| CBM-P2-05 | `--format markdown` output (PR Impact block) | 1 | TechLead | ✅ Done | D2 | P2-01, P2-02, P2-03 |
| CBM-P2-06 | `--format json` output | 0.5 | TechLead | ✅ Done | D2 | P2-01 |
| CBM-P2-07 | `--breaking-only` filter | 0.5 | TechLead | ✅ Done | D2 | P2-01, P2-03 |
| CBM-P2-08 | `--test-plan` output (affected callers grouped by domain) | 1 | TechLead | ✅ Done | D2 | P2-03 |
| CBM-P2-09 | CI workflow: `cbm-pr-impact.yml` — auto diff + PR comment | 1 | TechLead | ✅ Done | D3 | P2-05 |
| CBM-P2-10 | Integration tests (26 tests: pipeline + CLI + edge cases + CI YAML) | 2 | TechLead | ✅ Done | D3 | All |
| — | PR → /review-gate → CEO approve | — | Team | ✅ Done | D3 | All |

---

## DAILY PLAN

### Week 1 — Core Diff Engine

#### Day 1-2 — SnapshotDiff Core (3 SP)

**CBM-P2-01: SnapshotDiff Class**

Tạo module mới: `codebase_map/graph/snapshot_diff.py`

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP

@dataclass
class NodeChange:
    """Đại diện 1 thay đổi node."""
    change_type: str          # "added" | "removed" | "modified" | "renamed"
    node: Node                # node hiện tại (hoặc node mới nếu added)
    old_node: Node | None     # node cũ (nếu modified/renamed)
    modifications: list[str]  # ["signature_changed", "file_moved", ...]

@dataclass
class EdgeChange:
    """Đại diện 1 thay đổi edge."""
    change_type: str          # "added" | "removed"
    edge: Edge
    source_node: str          # node name
    target_node: str          # node name

@dataclass
class DiffResult:
    """Kết quả diff giữa 2 snapshots."""
    baseline_meta: dict       # metadata từ baseline graph
    current_meta: dict        # metadata từ current graph
    nodes_added: list[NodeChange]
    nodes_removed: list[NodeChange]
    nodes_modified: list[NodeChange]
    nodes_renamed: list[NodeChange]
    edges_added: list[EdgeChange]
    edges_removed: list[EdgeChange]
    affected_callers: list[dict]  # populated by P2-03
    
    @property
    def summary(self) -> dict:
        return {
            "functions_added": len(self.nodes_added),
            "functions_removed": len(self.nodes_removed),
            "functions_modified": len(self.nodes_modified),
            "functions_renamed": len(self.nodes_renamed),
            "edges_added": len(self.edges_added),
            "edges_removed": len(self.edges_removed),
            "affected_callers": len(self.affected_callers),
        }

class SnapshotDiff:
    """So sánh 2 graph snapshots."""
    
    def __init__(self, baseline: Graph, current: Graph):
        self.baseline = baseline
        self.current = current
        self._baseline_map = {n.id: n for n in baseline.nodes}
        self._current_map = {n.id: n for n in current.nodes}
    
    def compute(self, depth=1, include_renames=True) -> DiffResult:
        """Chạy diff đầy đủ."""
        ...
    
    def _diff_nodes(self) -> tuple[list, list, list]:
        """So sánh nodes: added, removed, modified."""
        ...
    
    def _diff_edges(self) -> tuple[list, list]:
        """So sánh edges: added, removed."""
        ...
```

**Thuật toán diff nodes:**
1. Build dict `baseline_nodes = {node.id: node for node in baseline.nodes}`
2. Build dict `current_nodes = {node.id: node for node in current.nodes}`
3. `added = current_nodes.keys() - baseline_nodes.keys()`
4. `removed = baseline_nodes.keys() - current_nodes.keys()`
5. `common = baseline_nodes.keys() & current_nodes.keys()`
6. Cho mỗi node trong `common`: so sánh signature (params, return_type, decorators, line_start/end) → nếu khác → modified
7. Performance: O(N) — dict lookup, không cần sort

#### Day 3 — Edge Diff (2 SP)

**CBM-P2-02: Edge Diff**
- So sánh edges giữa 2 graphs
- Edge identity: `(source_id, target_id, edge_type)` tuple
- Build set baseline_edges, current_edges
- `added = current_edges - baseline_edges`
- `removed = baseline_edges - current_edges`
- Cross-reference: nếu edge removed do node removed → tag "cascade_remove" (không phải independent change)

#### Day 4-5 — Affected Callers (2 SP)

**CBM-P2-03: Affected Callers**
- Input: list modified/removed nodes từ P2-01
- Cho mỗi modified/removed node N:
  - Tìm tất cả nodes X mà có edge `X → N` (CALLS/IMPORTS)
  - X = "affected caller level 1"
  - Nếu `--depth 2`: tìm tiếp nodes Y → X
  - Max depth = 3 (configurable, default 1)
- Output: list `{caller, file, reason, depth}`
- **Dedup:** nếu X affected bởi cả node A lẫn node B → chỉ list 1 lần, ghi cả 2 reasons
- Group by domain (module_domain) cho `--test-plan` output

### Week 2 — Rename + Output Formats + CI

#### Day 5-6 — Rename Detection (2 SP)

**CBM-P2-04: Rename Detection (Signature Matching)**

CEO + CTO đã quyết: dùng signature matching (KHÔNG body matching) cho v2.x.

**Thuật toán:**
1. Lấy danh sách `removed_nodes` và `added_nodes` từ P2-01
2. Cho mỗi pair (removed R, added A):
   - Match nếu: `R.name == A.name AND R.params == A.params AND R.return_type == A.return_type`
   - Và: `R.file_path != A.file_path` (khác file = rename/move)
3. Nếu match → chuyển từ "removed + added" → "renamed" (1 change thay vì 2)
4. Nếu ambiguous (1 removed match nhiều added) → report "possible rename" + list candidates

**Edge cases:**
- Function cùng tên nhưng khác params → KHÔNG phải rename → giữ "removed + added"
- Function move file VÀ sửa signature → "modified + moved" (2 changes)
- Overloaded functions → match bằng full signature (name + params), không chỉ tên

#### Day 7 — Output Formats (1.5 SP)

**CBM-P2-05: --format markdown** (1 SP)

Output markdown block cho PR body, format đã CEO duyệt:

```markdown
## 🗺️ Codebase-Map Impact Analysis

**Baseline:** {baseline.label} ({baseline.branch}, {baseline.sha}, {baseline.date})
**Post-dev:** {current.label} ({current.branch}, {current.sha}, {current.date})

| Metric | Count |
|--------|-------|
| Functions added | {n_added} |
| Functions removed | {n_removed} |
| Functions modified | {n_modified} |
| Affected callers | {n_affected} |

<details>
<summary>📋 Full Diff Details (click to expand)</summary>

### Added Functions
| Function | File | Layer | Called by |
|----------|------|-------|----------|
| `{name}` | {file} | {layer} | {callers} |

### Removed Functions
| Function | File | Was called by (⚠️ IMPACT) |
|----------|------|--------------------------|
| `{name}` | {file} | {callers} |

### Modified Functions
| Function | File | Change | Affected callers |
|----------|------|--------|-----------------|
| `{name}` | {file} | {change_desc} | {callers} |

### Affected Callers (🧪 Tester Focus)
| Caller | File | Domain | Reason |
|--------|------|--------|--------|
| `{name}` | {file} | {domain} | {reason} |

</details>

🤖 Auto-generated by [codebase-map](https://github.com/hypercommerce-vn/codebase-map) CI
```

**CBM-P2-06: --format json** (0.5 SP)
- `DiffResult.to_dict()` → JSON dump
- Schema: `{baseline_meta, current_meta, summary, nodes_added, nodes_removed, nodes_modified, nodes_renamed, edges_added, edges_removed, affected_callers}`

#### Day 8 — Filters + Test Plan (1.5 SP)

**CBM-P2-07: --breaking-only** (0.5 SP)
- Filter: chỉ hiện nodes bị remove/modify MÀ có `affected_callers.length > 0`
- Ẩn added nodes (không breaking)
- Ẩn modified nodes không ai gọi (no impact)
- Mục đích: CTO review nhanh — chỉ xem "cái gì có thể vỡ?"

**CBM-P2-08: --test-plan** (1 SP)
- Input: affected callers từ P2-03
- Group by `module_domain` (layer)
- Output format:
  ```markdown
  ## 🧪 Suggested Test Plan

  ### Domain: SERVICE (3 functions affected)
  - [ ] Test `CustomerService.create()` — caller of modified `validate_email()`
  - [ ] Test `OrderService.submit()` — caller of removed `legacy_check()`
  - [ ] Test `AlertService.dispatch()` — caller of modified `channel_factory()`

  ### Domain: ROUTER (1 function affected)
  - [ ] Test `POST /api/customers` — endpoint using `CustomerService.create()`

  Total: 4 functions need testing across 2 domains
  ```

#### Day 9 — CI + Integration (included in sprint)

**CI Workflow: cbm-pr-impact.yml**
- Tạo file `.github/workflows/cbm-pr-impact.yml` (từ CTO CI Proposal section 5.2)
- Trigger: `pull_request: [opened, synchronize]`
- Steps: download baseline artifact → generate post-dev → diff → post PR comment
- Sử dụng `marocchino/sticky-pull-request-comment@v2` cho auto-update comment

**Integration Tests:**
- `test_snapshot_diff.py`: 2 known graphs → verify diff output chính xác
- `test_rename_detection.py`: cases: rename, overload, move+modify
- `test_markdown_output.py`: verify format đúng template
- `test_breaking_only.py`: filter works correctly
- `test_affected_callers.py`: depth 1, 2, 3, dedup

#### Day 10 — Quality Gate + Ship

- Full lint gate: `black --check . && isort --check . && flake8`
- Self-test: chạy diff trên chính codebase-map repo (2 commits khác nhau)
- PR → /review-gate (Tester → CTO → Designer) → CEO approve
- Tag v2.2.0, update CHANGELOG

---

## DEFINITION OF DONE

1. ✅ `codebase-map diff --baseline <file1> --current <file2>` chạy đúng
2. ✅ Output hiện: added, removed, modified, renamed nodes + edges
3. ✅ Affected callers tính đúng (depth 1 default, max 3)
4. ✅ Rename detection signature matching hoạt động, không false positive
5. ✅ `--format markdown` output đúng template (summary visible + details collapsible)
6. ✅ `--format json` output machine-readable, parseable
7. ✅ `--breaking-only` filter chỉ hiện impactful changes
8. ✅ `--test-plan` output grouped by domain, actionable
9. ✅ CI workflow `cbm-pr-impact.yml` auto-post PR comment (tested)
10. ✅ All tests pass, lint clean, CI green
11. ✅ PR approved qua 3-tier review gate
12. ✅ Performance: diff < 5s cho 2 graphs × 10K functions (NFR-002)

---

## RISK REGISTER

| Risk | Impact | Likelihood | Mitigation |
|------|--------|:----------:|-----------|
| Rename detection false positive | Medium | Medium | Conservative matching: exact name + params + return_type. Ambiguous → "possible rename" |
| Large graph diff performance | Medium | Low | Dict-based O(N) lookup. Benchmark với 10K nodes |
| PR comment too long (GitHub limit 65536 chars) | Low | Medium | Truncate full diff nếu > 50K chars + "See artifact for complete diff" |
| Parallel PRs diff baseline stale | Medium | Medium | Baseline auto-rotate on merge. PR comment note "baseline may be outdated if other PRs merged recently" |
| Edge diff false changes do node ID change | High | Low | Node ID = file:function:line → nếu line thay đổi → ID thay đổi → phải dùng name+file fallback |

---

## ACCEPTANCE CRITERIA (CEO Review)

Demo khi CEO review:

1. **Basic diff:** 2 graph files (trước/sau 1 PR) → `codebase-map diff` → hiện đúng changes
2. **PR Impact block:** `--format markdown` → copy-paste vào PR → render đẹp trên GitHub
3. **Breaking only:** `--breaking-only` → chỉ hiện dangerous changes
4. **Test plan:** `--test-plan` → output actionable test checklist
5. **Rename:** Di chuyển function sang file khác → detect "renamed" thay vì "removed + added"
6. **CI auto:** Tạo PR trên test repo → CI tự post Impact Analysis comment
7. **Performance:** Diff 2 graphs lớn (HC project ~800 functions) → < 2 giây

---

*CBM Phase 2 Task Board v1.0 · Created 10/04/2026 · @PM + @CTO*
*Codebase-Map Dual-Snapshot · Sprint 2 of 2*
*Prerequisite: Phase 1 (v2.1) shipped*
