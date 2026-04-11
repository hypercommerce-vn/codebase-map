# HC-AI | ticket: MEM-M1-06
"""LayerLearner — detect path-based layer patterns from codebase evidence."""

import re
from collections import Counter
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Dict, List, Tuple

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault

# HC-AI | ticket: MEM-M1-06
# Canonical layer keywords — matched against directory/file names.
# Order matters: first match wins.
_LAYER_KEYWORDS: List[Tuple[str, List[str]]] = [
    (
        "route",
        ["route", "router", "routes", "endpoint", "endpoints", "api", "view", "views"],
    ),
    (
        "service",
        ["service", "services", "usecase", "usecases", "use_case", "use_cases"],
    ),
    ("model", ["model", "models", "schema", "schemas", "entity", "entities"]),
    ("repository", ["repository", "repositories", "repo", "repos", "dao", "daos"]),
    (
        "util",
        ["util", "utils", "utility", "utilities", "helper", "helpers", "lib", "libs"],
    ),
    ("config", ["config", "configs", "configuration", "settings", "setting"]),
    ("test", ["test", "tests", "testing", "spec", "specs", "conftest"]),
    ("migration", ["migration", "migrations", "alembic", "versions"]),
    ("worker", ["worker", "workers", "task", "tasks", "celery", "job", "jobs"]),
    ("middleware", ["middleware", "middlewares"]),
]

# Map singular file-name keywords (without extension)
_FILE_LAYER_RE: List[Tuple[str, re.Pattern]] = [
    ("route", re.compile(r"(router|route|endpoint|view)", re.IGNORECASE)),
    ("service", re.compile(r"(service|usecase|use_case)", re.IGNORECASE)),
    ("model", re.compile(r"(model|schema|entity)", re.IGNORECASE)),
    ("repository", re.compile(r"(repository|repo|dao)", re.IGNORECASE)),
    ("util", re.compile(r"(util|helper|lib)", re.IGNORECASE)),
    ("config", re.compile(r"(config|setting)", re.IGNORECASE)),
    ("test", re.compile(r"(test_|_test|conftest)", re.IGNORECASE)),
    ("worker", re.compile(r"(worker|task|job|celery)", re.IGNORECASE)),
    ("middleware", re.compile(r"middleware", re.IGNORECASE)),
]


def _classify_layer(file_path: str) -> str:
    """Classify a file path into a layer based on directory and filename.

    Strategy:
    1. Check directory components against keyword list (bottom-up).
    2. Check filename stem against regex patterns.
    3. Fallback to ``"unknown"``.
    """
    parts = PurePosixPath(file_path).parts
    stem = PurePosixPath(file_path).stem.lower()

    # Check directory components (bottom-up, skip the file itself)
    for part in reversed(parts[:-1]):
        part_lower = part.lower()
        for layer, keywords in _LAYER_KEYWORDS:
            if part_lower in keywords:
                return layer

    # Check filename against regex patterns
    for layer, pattern in _FILE_LAYER_RE:
        if pattern.search(stem):
            return layer

    return "unknown"


def _extract_domain(file_path: str) -> str:
    """Extract domain/module from file path.

    Looks for common patterns like ``modules/<domain>/``,
    ``apps/<domain>/``, or the first meaningful directory after
    the project root.
    """
    parts = PurePosixPath(file_path).parts
    # Look for modules/apps/<domain>
    for i, part in enumerate(parts):
        if part.lower() in ("modules", "apps", "components", "domains", "packages"):
            if i + 1 < len(parts):
                return parts[i + 1]

    # Fallback: first directory that isn't a common root
    skip = {
        "src",
        "app",
        "lib",
        "knowledge_memory",
        "codebase_map",
        "core",
        "verticals",
    }
    for part in parts:
        if part.lower() not in skip and not part.startswith(".") and part != parts[-1]:
            return part

    return "root"


# HC-AI | ticket: MEM-M1-06
class LayerLearner(BaseLearner[Evidence, Dict]):
    """Detect path-based layer patterns from codebase file structure.

    Produces patterns for:
    - Layer distribution (% of code in service/route/model/util layers)
    - Layer compliance (files in correct directories)
    - Cross-layer dependencies (route→service, service→model flow)
    - Domain grouping (files organized by business domain)
    - Layer anomalies (misplaced files)

    Design ref: kmp-M1-design.html Screen C item 8, MEM-M1-06.
    """

    LEARNER_NAME = "codebase.layers"
    LEARNER_CATEGORY = "layers"
    MIN_EVIDENCE_COUNT = 5
    MIN_CONFIDENCE = 60.0

    # HC-AI | ticket: MEM-M1-06
    def extract_evidence(self, vault: "BaseVault") -> List[Evidence]:
        """Pull node evidence with file paths from vault.

        Tries stored nodes first; falls back to corpus iterator.
        """
        results: List[Evidence] = []

        # Prefer stored nodes (populated after store_nodes)
        if hasattr(vault, "query_nodes"):
            try:
                stored = vault.query_nodes()
                if stored:
                    for node in stored:
                        name = node.get("name", "")
                        if not name or name.startswith("__"):
                            continue
                        results.append(
                            Evidence(
                                source=node.get("file_path", ""),
                                data={
                                    "name": name,
                                    "type": node.get("node_type", "function"),
                                    "layer": node.get("layer", "unknown"),
                                    "file_path": node.get("file_path", ""),
                                },
                                metadata={
                                    "layer": node.get("layer", "unknown"),
                                    "line_start": node.get("line_start", 0),
                                    "line_end": node.get("line_end", 0),
                                },
                            )
                        )
                    if results:
                        return results
            except Exception:
                pass

        # Fallback: in-memory corpus
        for ev in vault.get_corpus_iterator():
            name = ev.data.get("name", "")
            if not name or name.startswith("__"):
                continue
            # Ensure file_path available
            file_path = ev.data.get("file_path", "") or ev.source
            results.append(
                Evidence(
                    source=ev.source,
                    data={
                        "name": name,
                        "type": ev.data.get("type", "function"),
                        "layer": ev.data.get("layer", "unknown"),
                        "file_path": file_path,
                    },
                    metadata=ev.metadata,
                )
            )
        return results

    # HC-AI | ticket: MEM-M1-06
    def cluster(self, evidences: List[Evidence]) -> List[Dict]:
        """Group evidence into layer pattern clusters.

        Produces clusters for:
        1. Layer distribution — how code is spread across layers
        2. Layer compliance — files in expected directories
        3. Domain grouping — files organized by business domain
        4. Layer depth — nesting levels per layer
        5. File concentration — hotspot directories with many nodes
        """
        clusters: List[Dict] = []

        # --- Classify each evidence into a layer ---
        classified: List[Dict] = []
        layer_counts: Counter = Counter()
        layer_evidences: Dict[str, List[Evidence]] = {}
        domain_counts: Counter = Counter()
        domain_layer_map: Dict[str, Counter] = {}

        for ev in evidences:
            file_path = ev.data.get("file_path", "") or ev.source
            detected_layer = _classify_layer(file_path)
            domain = _extract_domain(file_path)

            layer_counts[detected_layer] += 1
            layer_evidences.setdefault(detected_layer, []).append(ev)
            domain_counts[domain] += 1
            domain_layer_map.setdefault(domain, Counter())[detected_layer] += 1

            classified.append(
                {
                    "evidence": ev,
                    "detected_layer": detected_layer,
                    "stored_layer": ev.data.get("layer", "unknown"),
                    "domain": domain,
                    "file_path": file_path,
                }
            )

        total = len(classified)

        # --- Cluster 1: Layer distribution ---
        if total > 0:
            distribution: Dict[str, float] = {}
            for layer, count in layer_counts.most_common():
                distribution[layer] = round((count / total) * 100, 1)

            # Count recognized layers (excluding "unknown")
            recognized = sum(
                cnt for lyr, cnt in layer_counts.items() if lyr != "unknown"
            )

            clusters.append(
                {
                    "pattern_type": "layer_distribution",
                    "layer_counts": dict(layer_counts),
                    "layer_pct": distribution,
                    "total": total,
                    "recognized_count": recognized,
                    "recognized_pct": (
                        round((recognized / total) * 100, 1) if total else 0
                    ),
                    "top_layers": layer_counts.most_common(5),
                    "evidences": evidences,
                }
            )

        # --- Cluster 2: Layer compliance ---
        # Compare detected layer vs stored layer (from parser)
        compliant: List[Evidence] = []
        mismatched: List[Dict] = []

        for item in classified:
            detected = item["detected_layer"]
            stored = item["stored_layer"]
            if detected == "unknown" or stored == "unknown":
                continue
            if detected == stored:
                compliant.append(item["evidence"])
            else:
                mismatched.append(
                    {
                        "name": item["evidence"].data.get("name", ""),
                        "file_path": item["file_path"],
                        "detected": detected,
                        "stored": stored,
                    }
                )

        total_classifiable = len(compliant) + len(mismatched)
        if total_classifiable >= 3:
            clusters.append(
                {
                    "pattern_type": "layer_compliance",
                    "total": total_classifiable,
                    "compliant": compliant,
                    "mismatched": mismatched,
                    "compliance_pct": round(
                        (len(compliant) / total_classifiable) * 100, 1
                    ),
                    "evidences": evidences,
                }
            )

        # --- Cluster 3: Domain grouping ---
        if len(domain_counts) >= 2:
            domains_info: List[Dict] = []
            for domain, count in domain_counts.most_common(10):
                layers_in_domain = dict(domain_layer_map.get(domain, {}))
                domains_info.append(
                    {
                        "domain": domain,
                        "node_count": count,
                        "layers": layers_in_domain,
                        "layer_count": len(layers_in_domain),
                    }
                )

            # Multi-layer domains = well-structured (vertical slicing)
            multi_layer_domains = [d for d in domains_info if d["layer_count"] >= 2]
            clusters.append(
                {
                    "pattern_type": "domain_grouping",
                    "domains": domains_info,
                    "total_domains": len(domain_counts),
                    "multi_layer_domains": len(multi_layer_domains),
                    "evidences": evidences,
                }
            )

        # --- Cluster 4: Layer depth ---
        # Analyse nesting depth of files per layer
        layer_depths: Dict[str, List[int]] = {}
        for item in classified:
            layer = item["detected_layer"]
            parts = PurePosixPath(item["file_path"]).parts
            depth = len(parts)
            layer_depths.setdefault(layer, []).append(depth)

        depth_stats: Dict[str, Dict[str, float]] = {}
        for layer, depths in layer_depths.items():
            if depths:
                avg = round(sum(depths) / len(depths), 1)
                depth_stats[layer] = {
                    "avg_depth": avg,
                    "min_depth": min(depths),
                    "max_depth": max(depths),
                    "count": len(depths),
                }

        if depth_stats:
            clusters.append(
                {
                    "pattern_type": "layer_depth",
                    "depth_stats": depth_stats,
                    "total_layers": len(depth_stats),
                    "evidences": evidences,
                }
            )

        # --- Cluster 5: File concentration (hotspot dirs) ---
        dir_counts: Counter = Counter()
        for item in classified:
            parent = str(PurePosixPath(item["file_path"]).parent)
            dir_counts[parent] += 1

        # Only report directories with ≥3 nodes
        hotspots = {d: c for d, c in dir_counts.most_common(10) if c >= 3}
        if hotspots:
            clusters.append(
                {
                    "pattern_type": "file_concentration",
                    "hotspot_dirs": hotspots,
                    "total_dirs": len(dir_counts),
                    "total_nodes": total,
                    "evidences": evidences,
                }
            )

        return clusters

    # HC-AI | ticket: MEM-M1-06
    def calculate_confidence(self, cluster: Dict) -> float:
        """Calculate confidence based on cluster type and data."""
        pattern_type = cluster.get("pattern_type", "")

        if pattern_type == "layer_distribution":
            recognized_pct = cluster.get("recognized_pct", 0)
            total = cluster.get("total", 0)
            if total == 0:
                return 0.0
            # Higher recognition rate → higher confidence
            # 80%+ recognized → 80+ confidence
            return min(100.0, max(0.0, recognized_pct * 1.1))

        if pattern_type == "layer_compliance":
            compliance_pct = cluster.get("compliance_pct", 0)
            total = cluster.get("total", 0)
            if total == 0:
                return 0.0
            # High compliance → high confidence
            return min(100.0, compliance_pct)

        if pattern_type == "domain_grouping":
            total_domains = cluster.get("total_domains", 0)
            multi = cluster.get("multi_layer_domains", 0)
            if total_domains == 0:
                return 0.0
            # Well-structured ratio drives confidence
            ratio = (multi / total_domains) * 100
            return min(100.0, max(60.0, ratio))

        if pattern_type == "layer_depth":
            total_layers = cluster.get("total_layers", 0)
            if total_layers < 2:
                return 0.0
            # Multiple distinct layers → good structure → high confidence
            return min(100.0, 60.0 + (total_layers * 5))

        if pattern_type == "file_concentration":
            hotspots = cluster.get("hotspot_dirs", {})
            total_nodes = cluster.get("total_nodes", 0)
            if not hotspots or total_nodes == 0:
                return 0.0
            # Concentration in hotspots as % of total
            hotspot_sum = sum(hotspots.values())
            coverage = (hotspot_sum / total_nodes) * 100
            return min(100.0, max(60.0, coverage))

        return 0.0

    # HC-AI | ticket: MEM-M1-06
    def cluster_to_pattern(self, cluster: Dict) -> Pattern:
        """Convert a layer cluster into a Pattern."""
        pattern_type = cluster.get("pattern_type", "")

        if pattern_type == "layer_distribution":
            return Pattern(
                name="layers::distribution",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "layer_counts": cluster.get("layer_counts", {}),
                    "layer_pct": cluster.get("layer_pct", {}),
                    "total": cluster.get("total", 0),
                    "recognized_pct": cluster.get("recognized_pct", 0),
                    "top_layers": [
                        {"layer": lyr, "count": cnt}
                        for lyr, cnt in cluster.get("top_layers", [])
                    ],
                },
            )

        if pattern_type == "layer_compliance":
            mismatched = cluster.get("mismatched", [])
            return Pattern(
                name="layers::compliance",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("compliant", [])[:20],
                metadata={
                    "compliance_pct": cluster.get("compliance_pct", 0),
                    "total": cluster.get("total", 0),
                    "mismatch_count": len(mismatched),
                    "mismatched_samples": mismatched[:10],
                },
            )

        if pattern_type == "domain_grouping":
            return Pattern(
                name="layers::domain_grouping",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "total_domains": cluster.get("total_domains", 0),
                    "multi_layer_domains": cluster.get("multi_layer_domains", 0),
                    "domains": cluster.get("domains", [])[:10],
                },
            )

        if pattern_type == "layer_depth":
            return Pattern(
                name="layers::depth_analysis",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "depth_stats": cluster.get("depth_stats", {}),
                    "total_layers": cluster.get("total_layers", 0),
                },
            )

        if pattern_type == "file_concentration":
            return Pattern(
                name="layers::file_concentration",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "hotspot_dirs": cluster.get("hotspot_dirs", {}),
                    "total_dirs": cluster.get("total_dirs", 0),
                    "total_nodes": cluster.get("total_nodes", 0),
                },
            )

        # Fallback
        return Pattern(
            name=f"layers::{pattern_type}",
            category=self.LEARNER_CATEGORY,
        )
