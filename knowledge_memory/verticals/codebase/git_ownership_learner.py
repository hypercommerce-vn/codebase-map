# HC-AI | ticket: MEM-M1-07
"""GitOwnershipLearner — detect author attribution and bus factor risks."""

import subprocess
from collections import Counter, defaultdict
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Dict, List, Optional

from knowledge_memory.core.learners.base import BaseLearner
from knowledge_memory.core.learners.pattern import Pattern
from knowledge_memory.core.parsers.evidence import Evidence

if TYPE_CHECKING:
    from knowledge_memory.core.vault.base import BaseVault


# HC-AI | ticket: MEM-M1-07
# Default git log depth limit (risk mitigation R-M1-2)
_DEFAULT_MAX_COMMITS = 1000


def _parse_git_log(
    repo_path: str,
    max_commits: int = _DEFAULT_MAX_COMMITS,
) -> List[Dict[str, str]]:
    """Parse git log to extract per-file author commit counts.

    Args:
        repo_path: Path to the git repository root.
        max_commits: Maximum number of commits to analyze.

    Returns:
        List of dicts with ``file_path``, ``author``, ``commits``.
        Each dict represents one author's contribution to one file.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                repo_path,
                "log",
                f"--max-count={max_commits}",
                "--format=%aN",
                "--name-only",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return []

    # Parse output: author line followed by file paths, separated by blank lines
    file_author_counts: Dict[str, Counter] = defaultdict(Counter)
    lines = result.stdout.strip().split("\n")

    current_author = ""
    for line in lines:
        line = line.strip()
        if not line:
            current_author = ""
            continue
        if not current_author:
            current_author = line
        else:
            # This is a file path
            file_author_counts[line][current_author] += 1

    # Convert to flat list
    records: List[Dict[str, str]] = []
    for file_path, authors in file_author_counts.items():
        total = sum(authors.values())
        for author, count in authors.items():
            pct = round((count / total) * 100, 1) if total else 0.0
            records.append(
                {
                    "file_path": file_path,
                    "author": author,
                    "commits": count,
                    "pct": pct,
                }
            )

    return records


def _extract_domain_from_path(file_path: str) -> str:
    """Extract domain/module name from file path for grouping."""
    parts = PurePosixPath(file_path).parts
    for i, part in enumerate(parts):
        if part.lower() in ("modules", "apps", "components", "domains", "packages"):
            if i + 1 < len(parts):
                return parts[i + 1]

    # Fallback: first meaningful directory
    skip = {"src", "app", "lib", ".", "knowledge_memory", "codebase_map"}
    for part in parts:
        lower = part.lower()
        if lower not in skip and not lower.startswith(".") and part != parts[-1]:
            return part

    return "root"


# HC-AI | ticket: MEM-M1-07
class GitOwnershipLearner(BaseLearner[Evidence, Dict]):
    """Detect author ownership patterns and bus factor risks.

    Produces patterns for:
    - Single-owner files (>80% commits by one author)
    - Single-owner domains (critical modules owned by one person)
    - Author distribution (top contributors across codebase)
    - Bus factor risk (domains with bus factor = 1)
    - Knowledge concentration (author specialization ratio)

    Design ref: kmp-M1-design.html GitOwnershipLearner section.
    Risk ref: R-M1-2 — limit to last 1000 commits, configurable depth.
    """

    LEARNER_NAME = "codebase.git_ownership"
    LEARNER_CATEGORY = "ownership"
    MIN_EVIDENCE_COUNT = 5
    MIN_CONFIDENCE = 60.0

    # Configurable thresholds
    SINGLE_OWNER_PCT = 80.0  # % commits to classify as single-owner
    BUS_FACTOR_THRESHOLD = 1  # bus factor ≤ this triggers risk pattern

    def __init__(
        self,
        repo_path: Optional[str] = None,
        max_commits: int = _DEFAULT_MAX_COMMITS,
    ) -> None:
        self._repo_path = repo_path
        self._max_commits = max_commits

    # HC-AI | ticket: MEM-M1-07
    def extract_evidence(self, vault: "BaseVault") -> List[Evidence]:
        """Pull file ownership evidence from vault or git log.

        Tries vault-stored ownership first; falls back to parsing
        git log if repo_path is set.
        """
        results: List[Evidence] = []

        # Prefer stored ownership data
        if hasattr(vault, "query_ownership"):
            try:
                stored = vault.query_ownership()
                if stored:
                    for rec in stored:
                        results.append(
                            Evidence(
                                source=rec.get("file_path", ""),
                                data={
                                    "file_path": rec.get("file_path", ""),
                                    "author": rec.get("author", ""),
                                    "commits": rec.get("commits", 0),
                                    "pct": rec.get("pct", 0.0),
                                },
                                metadata={"source": "vault"},
                            )
                        )
                    if results:
                        return results
            except Exception:
                pass

        # Fallback: parse git log
        if self._repo_path:
            records = _parse_git_log(self._repo_path, self._max_commits)
            for rec in records:
                results.append(
                    Evidence(
                        source=rec.get("file_path", ""),
                        data=rec,
                        metadata={"source": "git_log"},
                    )
                )

        # Last resort: in-memory corpus
        if not results:
            for ev in vault.get_corpus_iterator():
                if ev.data.get("author"):
                    results.append(ev)

        return results

    # HC-AI | ticket: MEM-M1-07
    def cluster(self, evidences: List[Evidence]) -> List[Dict]:
        """Group ownership evidence into risk pattern clusters.

        Produces clusters for:
        1. Single-owner files — files where one author has >80% commits
        2. Author distribution — top contributors by total commits
        3. Domain ownership — bus factor per domain/module
        4. Knowledge concentration — how specialized authors are
        """
        clusters: List[Dict] = []

        # --- Aggregate per-file ownership ---
        # file_path → {author: commits}
        file_owners: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        author_total: Counter = Counter()
        all_files: set = set()

        for ev in evidences:
            fp = ev.data.get("file_path", "")
            author = ev.data.get("author", "")
            commits = ev.data.get("commits", 0)
            if not fp or not author:
                continue
            file_owners[fp][author] += commits
            author_total[author] += commits
            all_files.add(fp)

        total_files = len(all_files)

        # --- Cluster 1: Single-owner files ---
        single_owner_files: List[Dict] = []
        multi_owner_files: List[Dict] = []

        for fp, authors in file_owners.items():
            total_commits = sum(authors.values())
            if total_commits == 0:
                continue
            top_author = max(authors, key=authors.get)
            top_pct = round((authors[top_author] / total_commits) * 100, 1)

            entry = {
                "file_path": fp,
                "top_author": top_author,
                "top_pct": top_pct,
                "total_commits": total_commits,
                "author_count": len(authors),
            }

            if top_pct >= self.SINGLE_OWNER_PCT:
                single_owner_files.append(entry)
            else:
                multi_owner_files.append(entry)

        if total_files > 0:
            single_pct = round((len(single_owner_files) / total_files) * 100, 1)
            clusters.append(
                {
                    "pattern_type": "single_owner_files",
                    "single_owner_files": single_owner_files,
                    "multi_owner_files": multi_owner_files,
                    "total_files": total_files,
                    "single_owner_count": len(single_owner_files),
                    "single_owner_pct": single_pct,
                    "evidences": evidences,
                }
            )

        # --- Cluster 2: Author distribution (top contributors) ---
        if author_total:
            total_commits_all = sum(author_total.values())
            top_authors: List[Dict] = []
            for author, commits in author_total.most_common(10):
                top_authors.append(
                    {
                        "author": author,
                        "commits": commits,
                        "pct": round((commits / total_commits_all) * 100, 1),
                    }
                )

            clusters.append(
                {
                    "pattern_type": "author_distribution",
                    "top_authors": top_authors,
                    "total_authors": len(author_total),
                    "total_commits": total_commits_all,
                    "evidences": evidences,
                }
            )

        # --- Cluster 3: Domain ownership + bus factor ---
        domain_authors: Dict[str, Counter] = defaultdict(Counter)
        domain_files: Dict[str, set] = defaultdict(set)

        for fp, authors in file_owners.items():
            domain = _extract_domain_from_path(fp)
            for author, commits in authors.items():
                domain_authors[domain][author] += commits
            domain_files[domain].add(fp)

        if domain_authors:
            domain_risks: List[Dict] = []
            for domain, authors in domain_authors.items():
                total_domain_commits = sum(authors.values())
                sorted_authors = authors.most_common()

                # Bus factor = number of authors needed to cover 50% of commits
                bus_factor = 0
                running_sum = 0
                half = total_domain_commits / 2.0
                for auth, cnt in sorted_authors:
                    running_sum += cnt
                    bus_factor += 1
                    if running_sum >= half:
                        break

                top_author = sorted_authors[0][0] if sorted_authors else ""
                top_pct = (
                    round(
                        (sorted_authors[0][1] / total_domain_commits) * 100,
                        1,
                    )
                    if sorted_authors and total_domain_commits
                    else 0
                )

                domain_risks.append(
                    {
                        "domain": domain,
                        "bus_factor": bus_factor,
                        "total_authors": len(authors),
                        "total_commits": total_domain_commits,
                        "file_count": len(domain_files[domain]),
                        "top_author": top_author,
                        "top_author_pct": top_pct,
                        "is_risk": bus_factor <= self.BUS_FACTOR_THRESHOLD,
                    }
                )

            # Sort by risk (lowest bus factor first)
            domain_risks.sort(key=lambda d: d["bus_factor"])
            risk_domains = [d for d in domain_risks if d["is_risk"]]

            clusters.append(
                {
                    "pattern_type": "domain_bus_factor",
                    "domains": domain_risks,
                    "total_domains": len(domain_risks),
                    "risk_domain_count": len(risk_domains),
                    "risk_domains": risk_domains,
                    "evidences": evidences,
                }
            )

        # --- Cluster 4: Knowledge concentration ---
        # How specialized are authors? (do they touch many domains or few?)
        author_domains: Dict[str, set] = defaultdict(set)
        for fp, authors in file_owners.items():
            domain = _extract_domain_from_path(fp)
            for author in authors:
                author_domains[author].add(domain)

        if author_domains and len(domain_authors) >= 2:
            specialists: List[Dict] = []  # Touch only 1 domain
            generalists: List[Dict] = []  # Touch 3+ domains

            for author, domains in author_domains.items():
                entry = {
                    "author": author,
                    "domain_count": len(domains),
                    "domains": sorted(domains),
                    "total_commits": author_total.get(author, 0),
                }
                if len(domains) == 1:
                    specialists.append(entry)
                elif len(domains) >= 3:
                    generalists.append(entry)

            total_authors = len(author_domains)
            clusters.append(
                {
                    "pattern_type": "knowledge_concentration",
                    "specialists": specialists,
                    "generalists": generalists,
                    "total_authors": total_authors,
                    "specialist_count": len(specialists),
                    "generalist_count": len(generalists),
                    "specialist_pct": (
                        round((len(specialists) / total_authors) * 100, 1)
                        if total_authors
                        else 0
                    ),
                    "evidences": evidences,
                }
            )

        return clusters

    # HC-AI | ticket: MEM-M1-07
    def calculate_confidence(self, cluster: Dict) -> float:
        """Calculate confidence based on cluster type."""
        pattern_type = cluster.get("pattern_type", "")

        if pattern_type == "single_owner_files":
            total = cluster.get("total_files", 0)
            if total == 0:
                return 0.0
            single_pct = cluster.get("single_owner_pct", 0)
            # High single-owner ratio → high confidence in the risk signal
            # Even 30% single-owner files is a meaningful finding
            return min(100.0, max(60.0, single_pct + 30))

        if pattern_type == "author_distribution":
            total_authors = cluster.get("total_authors", 0)
            total_commits = cluster.get("total_commits", 0)
            if total_authors == 0 or total_commits == 0:
                return 0.0
            # More commits analyzed → higher confidence
            if total_commits >= 100:
                return 95.0
            if total_commits >= 50:
                return 85.0
            if total_commits >= 20:
                return 75.0
            return 65.0

        if pattern_type == "domain_bus_factor":
            total_domains = cluster.get("total_domains", 0)
            risk_count = cluster.get("risk_domain_count", 0)
            if total_domains == 0:
                return 0.0
            # Risk domains drive confidence
            if risk_count > 0:
                return min(100.0, 70.0 + (risk_count * 5))
            # No risk → still valid pattern (healthy bus factor)
            return 65.0

        if pattern_type == "knowledge_concentration":
            total = cluster.get("total_authors", 0)
            if total == 0:
                return 0.0
            specialist_pct = cluster.get("specialist_pct", 0)
            # High specialization → meaningful finding
            return min(100.0, max(60.0, specialist_pct + 20))

        return 0.0

    # HC-AI | ticket: MEM-M1-07
    def cluster_to_pattern(self, cluster: Dict) -> Pattern:
        """Convert an ownership cluster into a Pattern."""
        pattern_type = cluster.get("pattern_type", "")

        if pattern_type == "single_owner_files":
            single_files = cluster.get("single_owner_files", [])
            return Pattern(
                name="ownership::single_owner_files",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "total_files": cluster.get("total_files", 0),
                    "single_owner_count": cluster.get("single_owner_count", 0),
                    "single_owner_pct": cluster.get("single_owner_pct", 0),
                    "top_single_owner_files": [
                        {
                            "file": f["file_path"],
                            "author": f["top_author"],
                            "pct": f["top_pct"],
                        }
                        for f in sorted(
                            single_files,
                            key=lambda x: x["top_pct"],
                            reverse=True,
                        )[:10]
                    ],
                },
            )

        if pattern_type == "author_distribution":
            return Pattern(
                name="ownership::author_distribution",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "top_authors": cluster.get("top_authors", []),
                    "total_authors": cluster.get("total_authors", 0),
                    "total_commits": cluster.get("total_commits", 0),
                },
            )

        if pattern_type == "domain_bus_factor":
            risk_domains = cluster.get("risk_domains", [])
            return Pattern(
                name="ownership::domain_bus_factor",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "total_domains": cluster.get("total_domains", 0),
                    "risk_domain_count": cluster.get("risk_domain_count", 0),
                    "risk_domains": [
                        {
                            "domain": d["domain"],
                            "bus_factor": d["bus_factor"],
                            "top_author": d["top_author"],
                            "top_author_pct": d["top_author_pct"],
                            "file_count": d["file_count"],
                        }
                        for d in risk_domains[:10]
                    ],
                    "healthy_domains": [
                        {
                            "domain": d["domain"],
                            "bus_factor": d["bus_factor"],
                            "total_authors": d["total_authors"],
                        }
                        for d in cluster.get("domains", [])
                        if not d["is_risk"]
                    ][:10],
                },
            )

        if pattern_type == "knowledge_concentration":
            return Pattern(
                name="ownership::knowledge_concentration",
                category=self.LEARNER_CATEGORY,
                evidence=cluster.get("evidences", [])[:20],
                metadata={
                    "total_authors": cluster.get("total_authors", 0),
                    "specialist_count": cluster.get("specialist_count", 0),
                    "generalist_count": cluster.get("generalist_count", 0),
                    "specialist_pct": cluster.get("specialist_pct", 0),
                    "specialists": [
                        {"author": s["author"], "domain": s["domains"][0]}
                        for s in cluster.get("specialists", [])[:10]
                    ],
                    "generalists": [
                        {
                            "author": g["author"],
                            "domain_count": g["domain_count"],
                        }
                        for g in cluster.get("generalists", [])[:10]
                    ],
                },
            )

        # Fallback
        return Pattern(
            name=f"ownership::{pattern_type}",
            category=self.LEARNER_CATEGORY,
        )
