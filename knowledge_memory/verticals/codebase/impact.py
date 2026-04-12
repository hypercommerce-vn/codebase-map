# HC-AI | ticket: MEM-M2-06
"""Impact command — change impact analysis via vault call graph + CBM v2.2.

Design ref: kmp-M2-design.html Screen C (impact command).
Uses vault's stored edges for caller analysis. Can optionally invoke
CBM snapshot-diff via subprocess for dual-snapshot diff data.

CTO Decision: KMP calls `codebase-map snapshot-diff --format json`
via subprocess — no library import (clean dependency boundary).
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
from collections import deque
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("codebase-memory.impact")


@dataclass
class Caller:
    """A caller affected by a change."""

    name: str
    file_path: str
    domain: str
    depth: int
    risk: str  # "high" | "medium" | "low"


@dataclass
class ImpactResult:
    """Result of an impact analysis."""

    function_name: str
    file_path: str
    layer: str
    domain: str
    direct_callers: list[Caller]
    transitive_callers: list[Caller]
    risk_level: str  # "HIGH" | "MEDIUM" | "LOW"
    recommendation: str
    cbm_diff: dict[str, Any] | None = None
    total_ms: float = 0.0
    error: str = ""


# HC-AI | ticket: MEM-M2-06
class ImpactEngine:
    """Analyze change impact using vault call graph.

    Two modes:
    1. Vault-only: BFS on stored edges (always available)
    2. CBM-enhanced: call `codebase-map snapshot-diff` for structural diff
    """

    MAX_DEPTH = 3

    def __init__(self) -> None:
        self._callers: dict[str, list[str]] = {}  # target → [callers]
        self._node_info: dict[str, dict[str, Any]] = {}

    def load_graph(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, str]],
    ) -> None:
        """Load call graph from vault data."""
        self._callers.clear()
        self._node_info.clear()

        for n in nodes:
            name = n.get("name", "")
            if name:
                self._node_info[name] = n

        for e in edges:
            src = e.get("source_name", "")
            tgt = e.get("target_name", "")
            if src and tgt:
                self._callers.setdefault(tgt, []).append(src)

    def analyze(
        self,
        function_name: str,
        depth: int = 1,
        cbm_baseline: str = "",
        cbm_current: str = "",
        cbm_config: str = "",
    ) -> ImpactResult:
        """Analyze impact of changing a function.

        Args:
            function_name: Function to analyze (exact or fuzzy match).
            depth: Caller traversal depth (1-3).
            cbm_baseline: CBM baseline snapshot label/path (optional).
            cbm_current: CBM current snapshot label/path (optional).
            cbm_config: CBM config file path (optional).

        Returns:
            ImpactResult with callers, risk level, and recommendation.
        """
        start = time.monotonic()
        depth = min(max(depth, 1), self.MAX_DEPTH)

        # Resolve function name
        resolved = self._resolve_name(function_name)
        if not resolved:
            return ImpactResult(
                function_name=function_name,
                file_path="",
                layer="",
                domain="",
                direct_callers=[],
                transitive_callers=[],
                risk_level="LOW",
                recommendation="",
                error=f"Function not found: '{function_name}'",
            )

        info = self._node_info.get(resolved, {})
        file_path = info.get("file_path", "")
        layer = info.get("layer", "unknown")
        domain = self._extract_domain(file_path)

        # BFS to find callers at each depth level
        direct = self._get_callers(resolved, 1)
        transitive = self._get_callers(resolved, depth) if depth > 1 else []
        # Remove direct from transitive to avoid duplication
        direct_names = {c.name for c in direct}
        transitive = [c for c in transitive if c.name not in direct_names]

        # Risk assessment
        total_callers = len(direct) + len(transitive)
        high_risk_count = sum(1 for c in direct if c.risk == "high")
        risk_level = self._assess_risk(total_callers, high_risk_count)
        recommendation = self._generate_recommendation(
            resolved, risk_level, direct, layer
        )

        # Optional CBM diff
        cbm_diff = None
        if cbm_baseline and cbm_current:
            cbm_diff = self._run_cbm_diff(cbm_baseline, cbm_current, cbm_config)

        elapsed = (time.monotonic() - start) * 1000

        return ImpactResult(
            function_name=resolved,
            file_path=file_path,
            layer=layer,
            domain=domain,
            direct_callers=direct,
            transitive_callers=transitive,
            risk_level=risk_level,
            recommendation=recommendation,
            cbm_diff=cbm_diff,
            total_ms=elapsed,
        )

    def _get_callers(self, name: str, max_depth: int) -> list[Caller]:
        """BFS to find callers up to max_depth."""
        result: list[Caller] = []
        visited: set[str] = {name}
        queue: deque[tuple[str, int]] = deque()

        # Seed with direct callers
        for caller in self._callers.get(name, []):
            if caller not in visited:
                queue.append((caller, 1))
                visited.add(caller)

        while queue:
            current, depth = queue.popleft()
            info = self._node_info.get(current, {})
            fpath = info.get("file_path", "")
            layer = info.get("layer", "unknown")
            domain = self._extract_domain(fpath)
            risk = self._classify_risk(layer)

            result.append(
                Caller(
                    name=current,
                    file_path=fpath,
                    domain=domain,
                    depth=depth,
                    risk=risk,
                )
            )

            if depth < max_depth:
                for next_caller in self._callers.get(current, []):
                    if next_caller not in visited:
                        queue.append((next_caller, depth + 1))
                        visited.add(next_caller)

        return result

    def _resolve_name(self, name: str) -> str:
        """Resolve function name (exact or fuzzy match)."""
        if name in self._node_info:
            return name
        lower = name.lower()
        # File:function format (e.g., "auth/service.py:authenticate")
        if ":" in name:
            fpath, fname = name.rsplit(":", 1)
            for n, info in self._node_info.items():
                if n.lower() == fname.lower() and fpath in info.get("file_path", ""):
                    return n

        candidates = [n for n in self._node_info if lower in n.lower()]
        if len(candidates) == 1:
            return candidates[0]
        return candidates[0] if candidates else ""

    def _classify_risk(self, layer: str) -> str:
        """Classify caller risk based on layer."""
        if layer in ("route", "router", "middleware", "api"):
            return "high"  # User-facing
        if layer in ("test", "fixture", "conftest"):
            return "low"  # Test only
        return "medium"  # Service, util, etc.

    def _assess_risk(self, total_callers: int, high_risk_count: int) -> str:
        """Assess overall risk level."""
        if high_risk_count >= 2 or total_callers >= 10:
            return "HIGH"
        if high_risk_count >= 1 or total_callers >= 5:
            return "MEDIUM"
        return "LOW"

    def _generate_recommendation(
        self,
        name: str,
        risk: str,
        direct: list[Caller],
        layer: str,
    ) -> str:
        """Generate actionable recommendation."""
        if risk == "HIGH":
            route_callers = [c.name for c in direct if c.risk == "high"]
            return (
                f"Affects {len(route_callers)} user-facing endpoint(s). "
                "Add integration test covering caller chain before modifying."
            )
        if risk == "MEDIUM":
            return "Review direct callers for side effects before modifying."
        return "Low-risk change. Standard unit test coverage sufficient."

    def _extract_domain(self, file_path: str) -> str:
        """Extract domain from file path."""
        if not file_path or "/" not in file_path:
            return "unknown"
        parts = file_path.split("/")
        return parts[0] if parts else "unknown"

    def _run_cbm_diff(
        self, baseline: str, current: str, config: str
    ) -> dict[str, Any] | None:
        """Run CBM snapshot-diff via subprocess.

        CTO Decision: subprocess call, not library import.
        """
        cmd = [
            "python",
            "-m",
            "codebase_map",
            "snapshot-diff",
            "--baseline",
            baseline,
            "--current",
            current,
            "--format",
            "json",
        ]
        if config:
            cmd.extend(["-c", config])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            logger.warning("CBM diff failed: %s", e)
        except FileNotFoundError:
            logger.warning("codebase-map not found in PATH")

        return None


def format_impact_result(result: ImpactResult) -> str:
    """Format ImpactResult for terminal output.

    Design ref: kmp-M2-design.html Screen C.
    """
    lines: list[str] = []
    lines.append("Knowledge Memory \u2014 Impact Analysis")
    lines.append("")

    if result.error:
        lines.append(f"\u2717 {result.error}")
        return "\n".join(lines)

    lines.append(f"Function: {result.function_name}")
    lines.append(
        f"File:     {result.file_path} \u00b7 "
        f"Layer: {result.layer} \u00b7 Domain: {result.domain}"
    )

    total = len(result.direct_callers) + len(result.transitive_callers)
    lines.append(
        f"Callers:  {len(result.direct_callers)} direct "
        f"\u00b7 {len(result.transitive_callers)} transitive "
        f"(total {total})"
    )
    lines.append("")

    if result.direct_callers:
        lines.append("Direct Callers:")
        for c in result.direct_callers:
            risk_icon = (
                "\u25cf"
                if c.risk == "high"
                else "\u25cb" if c.risk == "low" else "\u25d0"
            )
            lines.append(
                f"  {risk_icon} {c.file_path}:{c.name}  "
                f"\u2014 {c.domain} ({c.risk})"
            )
        lines.append("")

    if result.transitive_callers:
        lines.append(f"Transitive Callers ({len(result.transitive_callers)}):")
        for c in result.transitive_callers[:10]:
            lines.append(f"  \u25cb {c.file_path}:{c.name}  " f"\u2014 depth {c.depth}")
        if len(result.transitive_callers) > 10:
            lines.append(f"  ... {len(result.transitive_callers) - 10} more")
        lines.append("")

    lines.append(f"Risk: {result.risk_level}")
    if result.recommendation:
        lines.append(f"Recommendation: {result.recommendation}")

    if result.cbm_diff:
        lines.append("")
        summary = result.cbm_diff.get("summary", {})
        lines.append("CBM Dual-Snapshot Diff:")
        lines.append(
            f"  Added: {summary.get('functions_added', 0)} "
            f"Removed: {summary.get('functions_removed', 0)} "
            f"Modified: {summary.get('functions_modified', 0)}"
        )

    lines.append("")
    lines.append("Powered by vault call graph + CBM v2.2 dual-snapshot engine")

    return "\n".join(lines)
