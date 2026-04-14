# HC-AI | ticket: MEM-M3-07
"""Glossary extractor — extract business domain terms from codebase.

Extracts terms from: function names, module/file names, class names.
Stores in vault SQLite (glossary table). Used by onboard chapter 8.

Design ref: kmp-M3-design.html Screen D.
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("codebase-memory.glossary")

# HC-AI | ticket: MEM-M3-07
# Common code words to filter out (not business terms)
_CODE_STOPWORDS = {
    "get",
    "set",
    "create",
    "update",
    "delete",
    "list",
    "find",
    "search",
    "init",
    "setup",
    "teardown",
    "test",
    "mock",
    "stub",
    "helper",
    "util",
    "utils",
    "base",
    "abstract",
    "mixin",
    "handler",
    "manager",
    "service",
    "router",
    "route",
    "model",
    "schema",
    "config",
    "main",
    "run",
    "start",
    "stop",
    "process",
    "handle",
    "execute",
    "validate",
    "check",
    "parse",
    "format",
    "convert",
    "build",
    "make",
    "load",
    "save",
    "read",
    "write",
    "open",
    "close",
    "send",
    "receive",
    "log",
    "error",
    "warn",
    "info",
    "debug",
    "str",
    "int",
    "float",
    "bool",
    "dict",
    "list",
    "none",
    "self",
    "cls",
    "args",
    "kwargs",
    "return",
    "result",
    "data",
    "item",
    "items",
    "value",
    "values",
    "key",
    "keys",
    "name",
    "path",
    "file",
    "type",
    "id",
    "index",
}

# Camel/Pascal case splitter
_CAMEL_RE = re.compile(r"(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


@dataclass
class GlossaryTerm:
    """A business domain term extracted from the codebase."""

    term: str
    domain: str
    evidence_count: int
    sources: list[str]
    confidence: float = 0.0


class GlossaryExtractor:
    """Extract business domain terminology from codebase nodes.

    Analyzes function names, class names, and file paths to find
    recurring domain-specific terms that new developers need to know.
    """

    def __init__(self, min_evidence: int = 3) -> None:
        self._min_evidence = min_evidence

    def extract(
        self,
        nodes: list[dict[str, Any]],
    ) -> list[GlossaryTerm]:
        """Extract glossary terms from vault nodes.

        Args:
            nodes: List of node dicts from vault.query_nodes().

        Returns:
            Sorted list of GlossaryTerm (most evidence first).
        """
        # Count term occurrences across all nodes
        term_counter: Counter[str] = Counter()
        term_domains: dict[str, Counter[str]] = {}
        term_sources: dict[str, list[str]] = {}

        for node in nodes:
            name = node.get("name", "")
            fpath = node.get("file_path", "")
            domain = self._extract_domain(fpath)

            # Extract terms from function/class name
            words = self._split_name(name)
            for word in words:
                lower = word.lower()
                if lower in _CODE_STOPWORDS or len(lower) < 3:
                    continue

                term_counter[lower] += 1

                if lower not in term_domains:
                    term_domains[lower] = Counter()
                if domain:
                    term_domains[lower][domain] += 1

                if lower not in term_sources:
                    term_sources[lower] = []
                if fpath and len(term_sources[lower]) < 5:
                    term_sources[lower].append(fpath)

            # Extract terms from file path
            path_parts = fpath.replace("\\", "/").split("/")
            for part in path_parts:
                part_clean = part.replace(".py", "").replace("_", " ")
                for word in part_clean.split():
                    lower = word.lower()
                    if lower in _CODE_STOPWORDS or len(lower) < 3:
                        continue
                    term_counter[lower] += 1
                    if lower not in term_domains:
                        term_domains[lower] = Counter()
                    if domain:
                        term_domains[lower][domain] += 1

        # Filter by minimum evidence and build terms
        terms: list[GlossaryTerm] = []
        for term, count in term_counter.most_common():
            if count < self._min_evidence:
                continue

            # Find primary domain
            domain_counts = term_domains.get(term, Counter())
            primary_domain = (
                domain_counts.most_common(1)[0][0] if domain_counts else "unknown"
            )

            # Confidence based on evidence count
            confidence = min(50.0 + count * 5, 99.0)

            terms.append(
                GlossaryTerm(
                    term=term.capitalize(),
                    domain=primary_domain,
                    evidence_count=count,
                    sources=term_sources.get(term, [])[:5],
                    confidence=confidence,
                )
            )

        return terms

    def format_table(self, terms: list[GlossaryTerm]) -> str:
        """Format glossary as Markdown table."""
        if not terms:
            return "No business terms extracted yet."

        lines = [
            "| Term | Domain | Evidence | Confidence |",
            "|------|--------|----------|------------|",
        ]
        for t in terms[:30]:
            lines.append(
                f"| {t.term} | {t.domain} | "
                f"{t.evidence_count} refs | {t.confidence:.0f}% |"
            )

        if len(terms) > 30:
            lines.append(f"| ... | | {len(terms) - 30} more | |")

        lines.append("")
        lines.append(f"**Total: {len(terms)} terms**")

        return "\n".join(lines)

    def format_terminal(self, terms: list[GlossaryTerm]) -> str:
        """Format glossary for terminal output.

        Design ref: kmp-M3-design.html Screen D.
        """
        lines = [
            "Knowledge Memory \u2014 Domain Glossary",
            "",
        ]

        if not terms:
            lines.append("No business terms extracted yet.")
            lines.append("Run `codebase-memory bootstrap` first.")
            return "\n".join(lines)

        header = (
            f"  {'Term':<20} {'Domain':<14} " f"{'Evidence':>8}  {'Confidence':>10}"
        )
        lines.append(header)

        for t in terms[:15]:
            lines.append(
                f"  {t.term:<20} {t.domain:<14} "
                f"{t.evidence_count:>8}  "
                f"{t.confidence:>9.0f}%"
            )

        if len(terms) > 15:
            lines.append(f"  ... {len(terms) - 15} more terms")

        lines.append("")
        lines.append(
            f"  Total: {len(terms)} terms across "
            f"{len({t.domain for t in terms})} domains"
        )

        return "\n".join(lines)

    @staticmethod
    def _split_name(name: str) -> list[str]:
        """Split function/class name into words."""
        # Handle snake_case
        parts = name.split("_")
        result = []
        for part in parts:
            if not part:
                continue
            # Handle CamelCase within each part
            sub_parts = _CAMEL_RE.split(part)
            result.extend(s for s in sub_parts if s)
        return result

    @staticmethod
    def _extract_domain(file_path: str) -> str:
        """Extract domain from file path."""
        if not file_path or "/" not in file_path:
            return "unknown"
        return file_path.split("/")[0]
