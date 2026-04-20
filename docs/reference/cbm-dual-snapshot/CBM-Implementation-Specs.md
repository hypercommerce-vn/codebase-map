# Implementation Specs — Dual-Snapshot CBM (v2.1 + v2.2)

> **Authors:** @CTO + @TechLead · **Date:** 10/04/2026
> **Purpose:** Spec kỹ thuật chi tiết để TechLead implement ngay khi CEO ra lệnh
> **Reference:** Proposal_Dual_Snapshot_CBM.md · CTO_Review_Dual_Snapshot.md · CTO_CI_Integration_Proposal.md

---

## 1. GRAPH METADATA SCHEMA (Phase 1 — CBM-P1-01)

### 1.1 Thay đổi Graph dataclass

**File:** `codebase_map/graph/models.py`

Thêm field `metadata` vào `Graph`:

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP

@dataclass
class Graph:
    nodes: list[Node]
    edges: list[Edge]
    metadata: dict = field(default_factory=dict)  # NEW in v2.1

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata,  # NEW — đặt đầu tiên
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Graph":
        metadata = data.get("metadata", {})
        if not metadata:
            # Backward compat: graph v1.x không có metadata
            metadata = {
                "version": "1.x-legacy",
                "generated_at": None,
                "commit_sha": None,
                "branch": None,
                "label": "unknown",
                "generator_version": "unknown",
                "source_paths": [],
                "stats": {}
            }
            import logging
            logging.warning("Legacy graph format (v1.x). Metadata empty.")
        return cls(
            nodes=[Node.from_dict(n) for n in data.get("nodes", [])],
            edges=[Edge.from_dict(e) for e in data.get("edges", [])],
            metadata=metadata,
        )
```

### 1.2 Metadata Collection

**File:** `codebase_map/graph/builder.py` — thêm helper

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
import subprocess
from datetime import datetime, timezone

def _collect_git_info(project_root: str) -> dict:
    """Thu thập git info từ project root. Fallback nếu không phải git repo."""
    def _run(cmd):
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=project_root, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            return None

    return {
        "commit_sha": _run(["git", "rev-parse", "HEAD"]) or "unknown",
        "branch": _run(["git", "branch", "--show-current"]) or "detached",
    }

def build_metadata(
    graph: Graph,
    label: str,
    project_root: str,
    source_paths: list[str],
    generator_version: str,
) -> dict:
    """Build metadata dict cho graph."""
    git_info = _collect_git_info(project_root)
    return {
        "version": "2.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": git_info["commit_sha"],
        "branch": git_info["branch"],
        "label": label,
        "generator_version": generator_version,
        "source_paths": source_paths,
        "stats": {
            "total_functions": len(graph.nodes),
            "total_files": len(set(n.file_path for n in graph.nodes)),
            "total_edges": len(graph.edges),
        },
    }
```

### 1.3 Auto-label Logic

```python
def generate_auto_label(branch: str, sha: str) -> str:
    """Sinh label tự động khi --label không được truyền."""
    safe_branch = branch.replace("/", "-")[:20]
    short_sha = sha[:7]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    return f"{safe_branch}_{short_sha}_{timestamp}"
    # Example: "develop_a7bd55e_20260410-1000"
```

---

## 2. SNAPSHOT MANAGER (Phase 1 — CBM-P1-03, P1-04, P1-05)

### 2.1 Module mới

**File:** `codebase_map/snapshot.py`

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from codebase_map.graph.models import Graph


@dataclass
class SnapshotInfo:
    """Thông tin 1 snapshot."""
    label: str
    date: str
    branch: str
    sha: str
    nodes: int
    edges: int
    file_path: Path
    file_size: int  # bytes


class SnapshotManager:
    """Quản lý snapshot files trong .codebase-map-cache/snapshots/."""

    DEFAULT_DIR = ".codebase-map-cache/snapshots"
    DEFAULT_MAX = 10

    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or self.DEFAULT_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save(self, graph: Graph, output_path: Optional[str] = None) -> Path:
        """
        Lưu graph vào snapshot file.
        Naming: graph_{label}_{short_sha}.json
        Returns: path của file đã lưu.
        """
        meta = graph.metadata
        label = meta.get("label", "unknown")
        sha = meta.get("commit_sha", "unknown")[:7]
        filename = f"graph_{label}_{sha}.json"

        if output_path:
            save_path = Path(output_path)
        else:
            save_path = self.cache_dir / filename

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(graph.to_dict(), f, indent=2, ensure_ascii=False)

        return save_path

    def list_snapshots(self) -> list[SnapshotInfo]:
        """List tất cả snapshots, sorted by date desc."""
        snapshots = []
        for fp in self.cache_dir.glob("graph_*.json"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                meta = data.get("metadata", {})
                snapshots.append(SnapshotInfo(
                    label=meta.get("label", "unknown"),
                    date=meta.get("generated_at", "unknown"),
                    branch=meta.get("branch", "unknown"),
                    sha=meta.get("commit_sha", "unknown")[:7],
                    nodes=meta.get("stats", {}).get("total_functions", 0),
                    edges=meta.get("stats", {}).get("total_edges", 0),
                    file_path=fp,
                    file_size=fp.stat().st_size,
                ))
            except (json.JSONDecodeError, KeyError):
                continue
        return sorted(snapshots, key=lambda s: s.date or "", reverse=True)

    def clean(self, keep: int = DEFAULT_MAX) -> tuple[int, int]:
        """
        Xoá snapshots cũ, giữ N mới nhất.
        Returns: (removed_count, kept_count)
        """
        snapshots = self.list_snapshots()
        if len(snapshots) <= keep:
            return 0, len(snapshots)

        to_remove = snapshots[keep:]
        for s in to_remove:
            s.file_path.unlink(missing_ok=True)

        return len(to_remove), keep

    def load(self, label_or_path: str) -> Graph:
        """
        Load graph từ label hoặc file path.
        Nếu là label → tìm snapshot mới nhất có label đó.
        Nếu là path → load trực tiếp.
        """
        path = Path(label_or_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return Graph.from_dict(json.load(f))

        # Tìm by label
        for s in self.list_snapshots():
            if s.label == label_or_path:
                with open(s.file_path, "r", encoding="utf-8") as f:
                    return Graph.from_dict(json.load(f))

        raise FileNotFoundError(
            f"Snapshot '{label_or_path}' not found. "
            f"Run 'codebase-map snapshots list' to see available snapshots."
        )
```

---

## 3. SNAPSHOT DIFF ENGINE (Phase 2 — CBM-P2-01 → P2-04)

### 3.1 Core Diff Class

**File:** `codebase_map/graph/snapshot_diff.py`

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP
from dataclasses import dataclass, field
from typing import Optional

from codebase_map.graph.models import Graph, Node, Edge


@dataclass
class NodeChange:
    change_type: str          # "added" | "removed" | "modified" | "renamed"
    node: Node
    old_node: Optional[Node] = None
    modifications: list[str] = field(default_factory=list)
    rename_from_file: Optional[str] = None  # for renamed nodes


@dataclass
class EdgeChange:
    change_type: str          # "added" | "removed"
    edge: Edge
    is_cascade: bool = False  # True if caused by node add/remove


@dataclass
class AffectedCaller:
    name: str
    file_path: str
    domain: str               # module_domain / layer
    reason: str               # "calls X (modified)" etc.
    depth: int                # 1, 2, or 3
    source_changes: list[str] # node names that caused this


@dataclass
class DiffResult:
    baseline_meta: dict
    current_meta: dict
    nodes_added: list[NodeChange] = field(default_factory=list)
    nodes_removed: list[NodeChange] = field(default_factory=list)
    nodes_modified: list[NodeChange] = field(default_factory=list)
    nodes_renamed: list[NodeChange] = field(default_factory=list)
    edges_added: list[EdgeChange] = field(default_factory=list)
    edges_removed: list[EdgeChange] = field(default_factory=list)
    affected_callers: list[AffectedCaller] = field(default_factory=list)

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

    def has_changes(self) -> bool:
        return any(v > 0 for v in self.summary.values())
```

### 3.2 Thuật toán Diff Nodes

```python
class SnapshotDiff:

    def __init__(self, baseline: Graph, current: Graph):
        self.baseline = baseline
        self.current = current
        # Build lookup maps — O(N)
        self._b_by_id = {n.id: n for n in baseline.nodes}
        self._c_by_id = {n.id: n for n in current.nodes}
        # Name+file lookup cho fallback matching
        self._b_by_name_file = {(n.name, n.file_path): n for n in baseline.nodes}
        self._c_by_name_file = {(n.name, n.file_path): n for n in current.nodes}
        # Name-only lookup cho rename detection
        self._b_by_name = {}
        for n in baseline.nodes:
            self._b_by_name.setdefault(n.name, []).append(n)
        self._c_by_name = {}
        for n in current.nodes:
            self._c_by_name.setdefault(n.name, []).append(n)

    def compute(self, depth: int = 1, include_renames: bool = True) -> DiffResult:
        result = DiffResult(
            baseline_meta=self.baseline.metadata,
            current_meta=self.current.metadata,
        )

        # Step 1: Node diff
        added_ids, removed_ids, modified = self._diff_nodes()
        result.nodes_added = [NodeChange("added", self._c_by_id[i]) for i in added_ids]
        result.nodes_removed = [NodeChange("removed", self._b_by_id[i]) for i in removed_ids]
        result.nodes_modified = modified

        # Step 2: Rename detection (reduces false removed+added pairs)
        if include_renames:
            renames = self._detect_renames(
                [c.node for c in result.nodes_removed],
                [c.node for c in result.nodes_added],
            )
            rename_removed_ids = {r.old_node.id for r in renames}
            rename_added_ids = {r.node.id for r in renames}
            result.nodes_removed = [c for c in result.nodes_removed if c.node.id not in rename_removed_ids]
            result.nodes_added = [c for c in result.nodes_added if c.node.id not in rename_added_ids]
            result.nodes_renamed = renames

        # Step 3: Edge diff
        result.edges_added, result.edges_removed = self._diff_edges()

        # Step 4: Affected callers
        changed_node_ids = (
            {c.node.id for c in result.nodes_modified} |
            {c.node.id for c in result.nodes_removed}
        )
        result.affected_callers = self._find_affected_callers(changed_node_ids, depth)

        return result
```

### 3.3 Thuật toán Rename Detection (Signature Matching)

```python
    def _detect_renames(
        self, removed: list[Node], added: list[Node]
    ) -> list[NodeChange]:
        """
        Detect renamed/moved functions bằng signature matching.
        CEO + CTO decision: name + params + return_type (KHÔNG body matching).
        """
        renames = []
        used_added = set()

        for r_node in removed:
            for a_node in added:
                if a_node.id in used_added:
                    continue
                if self._signature_match(r_node, a_node):
                    renames.append(NodeChange(
                        change_type="renamed",
                        node=a_node,
                        old_node=r_node,
                        modifications=["file_moved"],
                        rename_from_file=r_node.file_path,
                    ))
                    used_added.add(a_node.id)
                    break  # 1 removed → 1 added match

        return renames

    @staticmethod
    def _signature_match(a: Node, b: Node) -> bool:
        """
        Match 2 nodes bằng signature: name + params + return_type.
        Phải cùng tên, cùng params, cùng return_type, KHÁC file.
        """
        return (
            a.name == b.name
            and a.params == b.params
            and a.return_type == b.return_type
            and a.file_path != b.file_path
        )
```

### 3.4 Thuật toán Affected Callers

```python
    def _find_affected_callers(
        self, changed_ids: set[str], max_depth: int
    ) -> list[AffectedCaller]:
        """
        Tìm callers bị ảnh hưởng bởi nodes thay đổi.
        Transitive tối đa max_depth cấp (default 1, max 3).
        """
        # Build reverse edge map từ CURRENT graph (ai gọi ai)
        callers_of = {}  # target_id -> list[source_node]
        for edge in self.current.edges:
            if edge.edge_type in ("CALLS", "IMPORTS"):
                callers_of.setdefault(edge.target, []).append(edge.source)

        # Cũng check BASELINE cho removed nodes
        for edge in self.baseline.edges:
            if edge.edge_type in ("CALLS", "IMPORTS"):
                callers_of.setdefault(edge.target, []).append(edge.source)

        affected = {}  # node_id -> AffectedCaller (dedup)
        frontier = [(nid, 1) for nid in changed_ids]
        visited = set(changed_ids)

        while frontier:
            target_id, depth = frontier.pop(0)
            if depth > max_depth:
                continue

            for caller_id in callers_of.get(target_id, []):
                if caller_id in visited or caller_id in changed_ids:
                    continue
                visited.add(caller_id)

                # Tìm node info (từ current hoặc baseline)
                caller_node = self._c_by_id.get(caller_id) or self._b_by_id.get(caller_id)
                if not caller_node:
                    continue

                # Tìm tên node bị thay đổi mà caller này gọi đến
                target_node = self._c_by_id.get(target_id) or self._b_by_id.get(target_id)
                target_name = target_node.name if target_node else target_id

                if caller_id not in affected:
                    affected[caller_id] = AffectedCaller(
                        name=caller_node.name,
                        file_path=caller_node.file_path,
                        domain=caller_node.layer or caller_node.module_domain or "UNKNOWN",
                        reason=f"calls {target_name} (changed)",
                        depth=depth,
                        source_changes=[target_name],
                    )
                else:
                    # Dedup: thêm reason
                    affected[caller_id].source_changes.append(target_name)

                # Tiếp tục BFS cho depth+1
                if depth + 1 <= max_depth:
                    frontier.append((caller_id, depth + 1))

        return sorted(affected.values(), key=lambda a: (a.depth, a.domain, a.name))
```

---

## 4. OUTPUT FORMATTERS (Phase 2 — CBM-P2-05, P2-06, P2-07, P2-08)

### 4.1 Markdown Formatter

**File:** `codebase_map/formatters/markdown_formatter.py`

```python
# HC-AI | ticket: FDD-TOOL-CODEMAP

def format_diff_markdown(result: DiffResult) -> str:
    """Format DiffResult thành markdown cho PR body."""
    lines = []
    b = result.baseline_meta
    c = result.current_meta
    s = result.summary

    # Header (always visible in PR)
    lines.append("## 🗺️ Codebase-Map Impact Analysis\n")
    lines.append(f"**Baseline:** `{b.get('label')}` ({b.get('branch')}, "
                 f"`{b.get('commit_sha','')[:7]}`, {_fmt_date(b.get('generated_at'))})")
    lines.append(f"**Post-dev:** `{c.get('label')}` ({c.get('branch')}, "
                 f"`{c.get('commit_sha','')[:7]}`, {_fmt_date(c.get('generated_at'))})\n")

    # Summary table (always visible)
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| Functions added | **{s['functions_added']}** |")
    lines.append(f"| Functions removed | **{s['functions_removed']}** |")
    lines.append(f"| Functions modified | **{s['functions_modified']}** |")
    if s['functions_renamed'] > 0:
        lines.append(f"| Functions renamed | {s['functions_renamed']} |")
    lines.append(f"| ⚠️ Affected callers | **{s['affected_callers']}** |\n")

    # Collapsible details (CEO decision: <details>)
    lines.append("<details>")
    lines.append("<summary>📋 Full Diff Details (click to expand)</summary>\n")

    # Added
    if result.nodes_added:
        lines.append("### Added Functions")
        lines.append("| Function | File | Layer | Called by |")
        lines.append("|----------|------|-------|----------|")
        for c in result.nodes_added[:50]:
            lines.append(f"| `{c.node.name}` | {c.node.file_path} | "
                         f"{c.node.layer or '-'} | - |")

    # Removed
    if result.nodes_removed:
        lines.append("\n### Removed Functions")
        lines.append("| Function | File | Was called by (⚠️ IMPACT) |")
        lines.append("|----------|------|--------------------------|")
        for c in result.nodes_removed[:50]:
            lines.append(f"| `{c.node.name}` | {c.node.file_path} | - |")

    # Modified
    if result.nodes_modified:
        lines.append("\n### Modified Functions")
        lines.append("| Function | File | Changes | Affected callers |")
        lines.append("|----------|------|---------|-----------------|")
        for c in result.nodes_modified[:50]:
            changes = ", ".join(c.modifications) if c.modifications else "content"
            lines.append(f"| `{c.node.name}` | {c.node.file_path} | {changes} | - |")

    # Renamed
    if result.nodes_renamed:
        lines.append("\n### 🔄 Renamed Functions")
        lines.append("| Function | Old File | New File | Match |")
        lines.append("|----------|----------|----------|-------|")
        for c in result.nodes_renamed:
            lines.append(f"| `{c.node.name}` | {c.rename_from_file} | "
                         f"{c.node.file_path} | ✅ signature |")

    # Affected callers
    if result.affected_callers:
        lines.append("\n### 🧪 Affected Callers (Tester Focus)")
        lines.append("| Caller | File | Domain | Reason |")
        lines.append("|--------|------|--------|--------|")
        for a in result.affected_callers[:50]:
            lines.append(f"| `{a.name}` | {a.file_path} | {a.domain} | {a.reason} |")

    lines.append("\n</details>\n")
    lines.append("🤖 Auto-generated by [codebase-map]"
                 "(https://github.com/hypercommerce-vn/codebase-map) CI")

    return "\n".join(lines)
```

### 4.2 Breaking-only Filter

```python
def filter_breaking_only(result: DiffResult) -> DiffResult:
    """Chỉ giữ changes có affected callers (breaking changes)."""
    affected_names = {a.name for ac in result.affected_callers for a in [ac]}
    changed_with_callers = set()

    # Tìm node IDs mà có callers bị ảnh hưởng
    for ac in result.affected_callers:
        changed_with_callers.update(ac.source_changes)

    return DiffResult(
        baseline_meta=result.baseline_meta,
        current_meta=result.current_meta,
        nodes_added=[],  # Added = never breaking
        nodes_removed=[c for c in result.nodes_removed
                       if c.node.name in changed_with_callers],
        nodes_modified=[c for c in result.nodes_modified
                        if c.node.name in changed_with_callers],
        nodes_renamed=result.nodes_renamed,
        edges_added=[],
        edges_removed=[],
        affected_callers=result.affected_callers,
    )
```

### 4.3 Test Plan Formatter

```python
def format_test_plan(result: DiffResult) -> str:
    """Format affected callers grouped by domain thành test plan."""
    lines = ["## 🧪 Suggested Test Plan\n"]

    # Group by domain
    by_domain = {}
    for ac in result.affected_callers:
        by_domain.setdefault(ac.domain, []).append(ac)

    for domain in sorted(by_domain.keys()):
        callers = by_domain[domain]
        lines.append(f"### Domain: {domain} ({len(callers)} functions affected)")
        for ac in callers:
            reasons = ", ".join(ac.source_changes)
            lines.append(f"- [ ] Test `{ac.name}` — caller of {ac.reason}")
            lines.append(f"  _{ac.file_path}_")
        lines.append("")

    total = len(result.affected_callers)
    domains = len(by_domain)
    lines.append(f"**Total: {total} functions need testing across {domains} domains**")

    # Warning cho removed dependencies
    removed_callers = [ac for ac in result.affected_callers
                       if "removed" in ac.reason]
    if removed_callers:
        lines.append(f"\n⚠️ **{len(removed_callers)} functions call REMOVED "
                     f"dependencies — likely will break!**")

    return "\n".join(lines)
```

---

## 5. CLI INTEGRATION (Phase 1 + Phase 2)

### 5.1 Thay đổi trong cli.py

**Thêm flags cho generate:**
```python
# Trong _cmd_generate():
parser.add_argument("--label", default="auto",
                    help="Snapshot label (default: auto-generate)")
```

**Thêm subcommands:**
```python
# Phase 1:
subparsers.add_parser("snapshots", help="Manage snapshots")
# → snapshots list
# → snapshots clean --keep N

# Phase 2:
# Extend _cmd_diff():
parser.add_argument("--baseline", help="Baseline graph file or label")
parser.add_argument("--current", help="Current graph file or label")
parser.add_argument("--format", choices=["text", "markdown", "json"], default="text")
parser.add_argument("--breaking-only", action="store_true")
parser.add_argument("--test-plan", action="store_true")
parser.add_argument("--depth", type=int, default=1, choices=[1, 2, 3])
```

### 5.2 Thay đổi trong json_exporter.py

Minimal change — `graph.to_dict()` đã bao gồm metadata tự động.

---

## 6. NODE ID STRATEGY

**Vấn đề:** Node ID hiện tại dùng format `file:function:line`. Nếu function dịch xuống 1 dòng (thêm comment phía trên) → ID thay đổi → diff sẽ báo "removed + added" thay vì "unchanged".

**Giải pháp cho Phase 2:**
- Primary match: by `node.id` (exact)
- Fallback match: by `(node.name, node.file_path)` — nếu chỉ line thay đổi
- Cả 2 match failed: coi là removed/added

Implement trong `SnapshotDiff._diff_nodes()`:
```python
def _diff_nodes(self):
    # Step 1: Match by ID
    matched_by_id = self._b_by_id.keys() & self._c_by_id.keys()
    unmatched_b = set(self._b_by_id.keys()) - matched_by_id
    unmatched_c = set(self._c_by_id.keys()) - matched_by_id

    # Step 2: Fallback match by (name, file) cho unmatched
    fallback_matched = set()
    for b_id in list(unmatched_b):
        b_node = self._b_by_id[b_id]
        key = (b_node.name, b_node.file_path)
        if key in self._c_by_name_file:
            c_node = self._c_by_name_file[key]
            if c_node.id in unmatched_c:
                # Match! Chỉ line thay đổi
                fallback_matched.add((b_id, c_node.id))
                unmatched_b.discard(b_id)
                unmatched_c.discard(c_node.id)

    # Remaining unmatched = truly added/removed
    added_ids = unmatched_c
    removed_ids = unmatched_b

    # Check modified trong matched nodes
    modified = []
    for b_id in matched_by_id:
        b_node = self._b_by_id[b_id]
        c_node = self._c_by_id[b_id]
        mods = _detect_modifications(b_node, c_node)
        if mods:
            modified.append(NodeChange("modified", c_node, b_node, mods))

    # Check modified trong fallback matched
    for b_id, c_id in fallback_matched:
        b_node = self._b_by_id[b_id]
        c_node = self._c_by_id[c_id]
        mods = _detect_modifications(b_node, c_node)
        if mods:
            modified.append(NodeChange("modified", c_node, b_node, mods))

    return added_ids, removed_ids, modified


def _detect_modifications(old: Node, new: Node) -> list[str]:
    """So sánh 2 nodes để phát hiện thay đổi."""
    mods = []
    if old.params != new.params:
        mods.append("params_changed")
    if old.return_type != new.return_type:
        mods.append("return_type_changed")
    if old.decorators != new.decorators:
        mods.append("decorators_changed")
    if old.line_start != new.line_start or old.line_end != new.line_end:
        mods.append("lines_changed")
    if old.parent_class != new.parent_class:
        mods.append("parent_class_changed")
    return mods
```

---

## 7. FILE STRUCTURE SAU IMPLEMENT

```
codebase_map/
├── __init__.py                    (update version → 2.1.0 / 2.2.0)
├── __main__.py
├── cli.py                         (MODIFIED: --label, snapshots subcommand, diff flags)
├── config.py
├── snapshot.py                    (NEW: SnapshotManager)
├── parsers/
│   ├── base.py
│   └── python_parser.py
├── graph/
│   ├── models.py                  (MODIFIED: Graph.metadata field)
│   ├── builder.py                 (MODIFIED: build_metadata(), _collect_git_info())
│   ├── query.py
│   ├── diff.py                    (EXISTING: DiffAnalyzer — giữ nguyên)
│   └── snapshot_diff.py           (NEW: SnapshotDiff, DiffResult)
├── exporters/
│   ├── json_exporter.py           (MINIMAL CHANGE: metadata auto-included)
│   ├── html_exporter.py
│   └── d3.v7.min.js
├── formatters/                    (NEW directory)
│   ├── __init__.py
│   ├── markdown_formatter.py      (NEW: PR Impact block)
│   ├── json_formatter.py          (NEW: DiffResult → JSON)
│   └── test_plan_formatter.py     (NEW: grouped test plan)
└── tests/                         (NEW/EXPANDED)
    ├── test_graph_metadata.py
    ├── test_snapshot_manager.py
    ├── test_snapshot_diff.py
    ├── test_rename_detection.py
    ├── test_markdown_output.py
    ├── test_breaking_only.py
    ├── test_affected_callers.py
    └── test_backward_compat.py
```

---

## 8. TESTING STRATEGY

### 8.1 Unit Tests (Phase 1)

| Test file | Test cases |
|-----------|-----------|
| `test_graph_metadata.py` | to_dict includes metadata, from_dict parses metadata, from_dict handles v1.x (no metadata), roundtrip to_dict → from_dict |
| `test_snapshot_manager.py` | save creates correct filename, list returns sorted by date, clean removes oldest, load by label, load by path, load missing → FileNotFoundError |
| `test_backward_compat.py` | Load v2.0.1 graph (no metadata), load v1.0 graph, metadata injected correctly |

### 8.2 Unit Tests (Phase 2)

| Test file | Test cases |
|-----------|-----------|
| `test_snapshot_diff.py` | Identical graphs → no changes, added nodes, removed nodes, modified nodes (params changed), modified nodes (lines changed only → NOT modified), mixed changes |
| `test_rename_detection.py` | Same name + params + different file → rename, Same name + different params → NOT rename, Ambiguous (1 name matches 2) → first match wins, No matches → stays removed+added |
| `test_affected_callers.py` | Depth 1 (default), depth 2 transitive, depth 3 max, dedup when caller affected by 2 changes, no callers → empty list |
| `test_markdown_output.py` | Summary table correct, details tag present, tables formatted correctly, empty diff → "No changes" message |
| `test_breaking_only.py` | Filter removes non-impactful, keeps only changes with callers |

### 8.3 Integration Test

```bash
# Self-test: diff 2 versions of codebase-map itself
git stash
codebase-map generate --label before -o /tmp/before.json
git stash pop
codebase-map generate --label after -o /tmp/after.json
codebase-map diff --baseline /tmp/before.json --current /tmp/after.json --format markdown
```

---

*Implementation Specs v1.0 · 10/04/2026 · @CTO + @TechLead*
*Ready for implement khi CEO ra lệnh*
