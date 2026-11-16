# HC-AI | ticket: FDD-TOOL-CODEMAP
"""VIBE-103: features, acceptance criteria and evidence.

A *feature* is a named part of the product ("Booking") together with the
files that implement it and the acceptance criteria its owner agreed to.
The store is one JSON file inside the project, ``.cbm/features.json``.

From a graph this module works out, for every feature:

* what it **owns** — the files and functions its patterns match;
* what it **reaches** — the functions its own code calls, directly or not,
  and the files whose top-level code those functions run with;
* a **fingerprint** of all that code.

Evidence for a criterion stores the fingerprint the feature had when the
check was made. When any code the feature owns or reaches changes, the
fingerprint changes and the evidence is reported as ``needs_recheck``. The
module never says a criterion is met — only whether evidence exists and
whether the code has changed since.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from codebase_map.fingerprint import text_hash
from codebase_map.graph.models import Graph, Node
from codebase_map.graph.snapshot_diff import DiffResult, SnapshotDiff

STORE_RELATIVE_PATH = ".cbm/features.json"
STORE_VERSION = 1

STATUS_VERIFIED = "verified"
STATUS_NEEDS_RECHECK = "needs_recheck"
STATUS_UNCHECKED = "unchecked"
STATUSES = (STATUS_VERIFIED, STATUS_NEEDS_RECHECK, STATUS_UNCHECKED)

EVIDENCE_KINDS = ("manual", "test")

TOUCHED_DIRECT = "direct"
TOUCHED_INDIRECT = "indirect"
TOUCHED_NONE = "none"

_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_FINGERPRINT_SCHEME = "feature-v1"

# Next.js conventions, used to tell screens and API endpoints from other files
_APP_ROUTER = re.compile(
    r"^(?:.*?/)?(?:src/)?app/(?:(?P<dir>.*)/)?(?P<file>page|route)\.(?:tsx|jsx|ts|js)$"
)
_PAGES_ROUTER = re.compile(r"^(?:src/)?pages/(?P<rest>.+)\.(?:tsx|jsx|ts|js)$")
_HTTP_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS")


class FeatureStoreError(ValueError):
    """The feature store, or a request against it, is not valid."""


# ─────────────────────────────────────────────────────────────────────
# Store
# ─────────────────────────────────────────────────────────────────────
@dataclass
class Evidence:
    """Proof that a criterion was checked, and against which code."""

    kind: str  # "manual" (a person tried it) | "test" (an automated test passed)
    note: str
    checked_at: str  # ISO 8601
    fingerprint: str  # the feature's fingerprint when the check was made

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "note": self.note,
            "checked_at": self.checked_at,
            "fingerprint": self.fingerprint,
        }


@dataclass
class Criterion:
    """One acceptance criterion of a feature."""

    id: str
    text: str
    evidence: Optional[Evidence] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "evidence": self.evidence.to_dict() if self.evidence else None,
        }


@dataclass
class Feature:
    """A named part of the product and the code that implements it.

    ``files`` holds patterns matched against a file path or a node id: an
    exact path, a folder (everything below it), or a glob with ``*`` and
    ``?``. Square brackets are literal, so ``app/api/bookings/[id]/route.ts``
    means that file.
    """

    id: str
    name: str
    files: list[str]
    summary: str = ""
    criteria: list[Criterion] = field(default_factory=list)

    def owns_path(self, path: str) -> bool:
        return any(pattern_matches(pattern, path) for pattern in self.files)

    def owns_node(self, node: Node) -> bool:
        path = _posix(node.file_path)
        return any(
            pattern_matches(pattern, path)
            or (_is_id_pattern(pattern) and pattern_matches(pattern, node.id))
            for pattern in self.files
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "summary": self.summary,
            "files": list(self.files),
            "criteria": [criterion.to_dict() for criterion in self.criteria],
        }


class FeatureStore:
    """The features of one project, as kept in ``.cbm/features.json``."""

    def __init__(self, features: Optional[list[Feature]] = None) -> None:
        self.features: list[Feature] = features or []

    # ── reading and writing ──────────────────────────────────────────
    @staticmethod
    def default_path(project_root: Path) -> Path:
        return project_root / STORE_RELATIVE_PATH

    @classmethod
    def load(cls, path: Path) -> "FeatureStore":
        """Read the store; a missing file is an empty store."""
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise FeatureStoreError(f"Cannot read {path}: {exc}") from exc
        return cls.from_dict(data)

    def save(self, path: Path) -> None:
        """Write the store, replacing the file in one step."""
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n"
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": STORE_VERSION,
            "features": [feature.to_dict() for feature in self.features],
        }

    @classmethod
    def from_dict(cls, data: Any) -> "FeatureStore":
        if not isinstance(data, dict):
            raise FeatureStoreError("The feature store must be a JSON object.")
        version = data.get("version", STORE_VERSION)
        if not isinstance(version, int) or version > STORE_VERSION:
            raise FeatureStoreError(
                f"Feature store version {version!r} is newer than this tool "
                f"understands ({STORE_VERSION}). Update codebase-map."
            )
        raw_features = data.get("features", [])
        if not isinstance(raw_features, list):
            raise FeatureStoreError('"features" must be a list.')

        store = cls()
        for raw in raw_features:
            if not isinstance(raw, dict):
                raise FeatureStoreError("Each feature must be a JSON object.")
            if any(f.id == raw.get("id") for f in store.features):
                raise FeatureStoreError(f"Feature id {raw.get('id')!r} is used twice.")
            feature = store.upsert_feature(
                _text(raw, "id", "feature"),
                _text(raw, "name", "feature"),
                raw.get("files"),
                str(raw.get("summary") or ""),
            )
            for raw_criterion in raw.get("criteria") or []:
                if not isinstance(raw_criterion, dict):
                    raise FeatureStoreError("Each criterion must be a JSON object.")
                criterion = store.add_criterion(
                    feature.id,
                    _text(raw_criterion, "text", "criterion"),
                    _text(raw_criterion, "id", "criterion"),
                )
                criterion.evidence = _evidence_from(raw_criterion.get("evidence"))
        return store

    # ── lookups ──────────────────────────────────────────────────────
    def feature(self, feature_id: str) -> Feature:
        for feature in self.features:
            if feature.id == feature_id:
                return feature
        known = ", ".join(f.id for f in self.features) or "none yet"
        raise FeatureStoreError(f"No feature with id {feature_id!r} (known: {known}).")

    def criterion(self, criterion_id: str) -> tuple[Feature, Criterion]:
        for feature in self.features:
            for criterion in feature.criteria:
                if criterion.id == criterion_id:
                    return feature, criterion
        raise FeatureStoreError(f"No criterion with id {criterion_id!r}.")

    # ── changes ──────────────────────────────────────────────────────
    def upsert_feature(
        self, feature_id: str, name: str, files: Any, summary: str = ""
    ) -> Feature:
        """Add a feature, or update the name, files and summary of an existing one."""
        _check_id(feature_id, "feature")
        if not name.strip():
            raise FeatureStoreError(f"Feature {feature_id!r} needs a name.")
        if (
            not isinstance(files, list)
            or not files
            or not all(isinstance(item, str) and item.strip() for item in files)
        ):
            raise FeatureStoreError(
                f"Feature {feature_id!r} needs a non-empty list of file patterns."
            )
        patterns = [_posix(item.strip()) for item in files]
        for feature in self.features:
            if feature.id == feature_id:
                feature.name, feature.files, feature.summary = name, patterns, summary
                return feature
        feature = Feature(feature_id, name, patterns, summary)
        self.features.append(feature)
        return feature

    def add_criterion(
        self, feature_id: str, text: str, criterion_id: Optional[str] = None
    ) -> Criterion:
        """Add a criterion; without an id the next free ``<feature>-<n>`` is used."""
        feature = self.feature(feature_id)
        if not text.strip():
            raise FeatureStoreError("A criterion needs a text.")
        taken = {c.id for f in self.features for c in f.criteria}
        if criterion_id is None:
            number = len(feature.criteria) + 1
            while f"{feature_id}-{number}" in taken:
                number += 1
            criterion_id = f"{feature_id}-{number}"
        _check_id(criterion_id, "criterion")
        if criterion_id in taken:
            raise FeatureStoreError(f"Criterion id {criterion_id!r} is already used.")
        criterion = Criterion(criterion_id, text.strip())
        feature.criteria.append(criterion)
        return criterion

    def record_evidence(
        self,
        criterion_id: str,
        kind: str,
        note: str,
        fingerprint: str,
        checked_at: Optional[str] = None,
    ) -> Criterion:
        """Attach evidence to a criterion, replacing any earlier evidence."""
        if kind not in EVIDENCE_KINDS:
            allowed = ", ".join(EVIDENCE_KINDS)
            raise FeatureStoreError(f"Evidence kind must be one of: {allowed}.")
        _, criterion = self.criterion(criterion_id)
        criterion.evidence = Evidence(
            kind=kind,
            note=note.strip(),
            checked_at=checked_at or _now(),
            fingerprint=fingerprint,
        )
        return criterion


def pattern_matches(pattern: str, text: str) -> bool:
    """True when ``text`` (a file path or a node id) falls under ``pattern``.

    A pattern is an exact value, a folder (matches everything below it), or a
    glob: ``*`` and ``?`` are wildcards and ``*`` also crosses ``/``; ``**/``
    also matches no folder at all; ``{a,b}`` is either. Square brackets are
    literal, because Next.js puts them in folder names. A leading ``./`` is
    ignored.
    """
    pattern = pattern.rstrip("/")
    if pattern.startswith("./"):
        pattern = pattern[2:]
    if text == pattern or text.startswith(pattern + "/"):
        return True
    if not any(char in pattern for char in "*?{"):
        return False
    return any(_glob_matches(option, text) for option in _expand_braces(pattern))


def _expand_braces(pattern: str) -> list[str]:
    """``a.{ts,tsx}`` → ``["a.ts", "a.tsx"]`` (one level, repeated)."""
    match = re.search(r"\{([^{}]*)\}", pattern)
    if not match:
        return [pattern]
    options: list[str] = []
    for choice in match.group(1).split(","):
        expanded = pattern[: match.start()] + choice + pattern[match.end() :]
        options.extend(_expand_braces(expanded))
    return options


def _glob_matches(pattern: str, text: str) -> bool:
    regex = ""
    index = 0
    while index < len(pattern):
        if pattern.startswith("**/", index):
            regex += "(?:.*/)?"
            index += 3
        elif pattern[index] == "*":
            regex += ".*"
            index += 1
        elif pattern[index] == "?":
            regex += "."
            index += 1
        else:
            regex += re.escape(pattern[index])
            index += 1
    return re.fullmatch(regex, text) is not None


def _is_id_pattern(pattern: str) -> bool:
    """A pattern meant for node ids: dotted, with no path separator.

    ``lib.reports.*`` is one. ``*Booking*`` is not: without a dot it reads as
    a file name, and matching it against ids would pull in functions that
    merely contain the word.
    """
    return "/" not in pattern and "." in pattern.strip("*?")


def web_route(path: str) -> Optional[tuple[str, str]]:
    """``("screen" | "api", url)`` for a Next.js page or endpoint file, else None."""
    match = _APP_ROUTER.match(path)
    if match:
        segments = [
            part
            for part in (match.group("dir") or "").split("/")
            # route groups "(shop)" and parallel routes "@modal" are not in the URL
            if part and not (part.startswith("(") and part.endswith(")"))
            if not part.startswith("@")
        ]
        kind = "screen" if match.group("file") == "page" else "api"
        return kind, "/" + "/".join(segments)
    match = _PAGES_ROUTER.match(path)
    if match:
        segments = match.group("rest").split("/")
        if segments[-1].startswith("_"):
            return None  # _app, _document
        if segments[-1] == "index":
            segments = segments[:-1]
        kind = "api" if segments[:1] == ["api"] else "screen"
        return kind, "/" + "/".join(segments)
    return None


# ─────────────────────────────────────────────────────────────────────
# Mapping features onto a graph
# ─────────────────────────────────────────────────────────────────────
@dataclass
class FeatureScope:
    """The code of one feature in one graph."""

    feature: Feature
    owned_files: list[str]
    owned_nodes: list[str]
    reached_nodes: list[str]  # called from the feature's code, owned elsewhere
    context_files: list[str]  # not owned; their top-level code is depended on
    fingerprint: str


class FeatureMap:
    """Which code belongs to which feature, for one graph."""

    def __init__(self, store: FeatureStore, graph: Graph) -> None:
        files = graph.metadata.get("files")
        if not isinstance(files, dict):
            raise FeatureStoreError(
                "This graph has no content fingerprints (it was generated by an "
                "older codebase-map). Run `codebase-map generate` again."
            )
        self.store = store
        self.graph = graph
        self._files: dict[str, dict[str, Any]] = files
        self._node_file = {
            node.id: _posix(node.file_path) for node in graph.nodes.values()
        }
        self._names_in_file: dict[str, set[str]] = {}
        for node in graph.nodes.values():
            self._names_in_file.setdefault(_posix(node.file_path), set()).add(node.name)
        self._uses = self._dependencies()
        self.scopes: dict[str, FeatureScope] = {
            feature.id: self._scope(feature) for feature in store.features
        }
        self._scope_files = {
            feature_id: set(scope.owned_files) | set(scope.context_files)
            for feature_id, scope in self.scopes.items()
        }

    def _dependencies(self) -> dict[str, set[str]]:
        """{node id: ids of the nodes it uses}, from edges that point at a node."""
        nodes = self.graph.nodes
        uses: dict[str, set[str]] = {}
        for edge in self.graph.edges:
            if edge.source in nodes and edge.target in nodes:
                uses.setdefault(edge.source, set()).add(edge.target)
        for node in nodes.values():
            # a method runs with its class's attributes
            if node.parent_class in nodes:
                uses.setdefault(node.id, set()).add(node.parent_class)
        return uses

    def _scope(self, feature: Feature) -> FeatureScope:
        owned_files = sorted(path for path in self._files if feature.owns_path(path))
        owned_nodes = sorted(
            node.id for node in self.graph.nodes.values() if feature.owns_node(node)
        )

        # Grow two sets together until neither changes:
        #   nodes — the feature's functions and everything they call;
        #   files — the files whose top-level code runs with the feature:
        #           its own, those holding its functions, and what they import.
        # A file's top-level code makes calls too (an inline route handler,
        # an initialiser); those functions are reached as well.
        nodes: set[str] = set()
        files: set[str] = set()
        pending_nodes = list(owned_nodes)
        pending_files = list(owned_files)
        while pending_nodes or pending_files:
            while pending_nodes:
                node_id = pending_nodes.pop()
                if node_id in nodes:
                    continue
                nodes.add(node_id)
                pending_nodes.extend(self._uses.get(node_id, ()))
                pending_files.append(self._node_file[node_id])
            while pending_files:
                path = pending_files.pop()
                if path in files:
                    continue
                files.add(path)
                info = self._files.get(path, {})
                pending_files.extend(info.get("imports", ()))
                pending_nodes.extend(
                    target
                    for target in info.get("calls", ())
                    if target in self.graph.nodes
                )

        return FeatureScope(
            feature=feature,
            owned_files=owned_files,
            owned_nodes=owned_nodes,
            reached_nodes=sorted(nodes - set(owned_nodes)),
            context_files=sorted(files - set(owned_files)),
            fingerprint=self._fingerprint(nodes, files),
        )

    def _fingerprint(self, node_ids: set[str], files: set[str]) -> str:
        parts = [_FINGERPRINT_SCHEME]
        for node_id in sorted(node_ids):
            body = self.graph.nodes[node_id].metadata.get("body_hash", "")
            parts.append(f"n:{node_id}:{body}")
        for path in sorted(files):
            module = self._files.get(path, {}).get("module_hash", "")
            parts.append(f"f:{path}:{module}")
        return text_hash("\n".join(parts))

    # ── queries ──────────────────────────────────────────────────────
    def scope(self, feature_id: str) -> FeatureScope:
        self.store.feature(feature_id)  # raises a clear error for an unknown id
        return self.scopes[feature_id]

    def status(self, feature_id: str, criterion: Criterion) -> str:
        """``verified`` | ``needs_recheck`` | ``unchecked`` for one criterion."""
        if criterion.evidence is None:
            return STATUS_UNCHECKED
        if criterion.evidence.fingerprint == self.scopes[feature_id].fingerprint:
            return STATUS_VERIFIED
        return STATUS_NEEDS_RECHECK

    def owners_of_file(self, path: str) -> list[str]:
        return [f.id for f in self.store.features if f.owns_path(path)]

    def users_of_file(self, path: str) -> list[str]:
        """Ids of the features that own the file or depend on its code."""
        return [
            feature_id
            for feature_id, files in self._scope_files.items()
            if path in files
        ]

    def affected_by(self, feature_id: str) -> list[str]:
        """Ids of the other features that depend on this feature's code.

        These are the features to warn about before this one is edited: they
        own nothing that changes, but they run code that will.
        """
        scope = self.scope(feature_id)
        owned_nodes = set(scope.owned_nodes)
        owned_files = set(scope.owned_files)
        affected = []
        for other_id, other in self.scopes.items():
            if other_id == feature_id:
                continue
            if owned_nodes & set(other.reached_nodes) or (
                owned_files & self._scope_files[other_id]
            ):
                affected.append(other_id)
        return affected

    @property
    def unowned_files(self) -> list[str]:
        return sorted(path for path in self._files if not self.owners_of_file(path))

    def describe_file(self, path: str) -> dict[str, Any]:
        """Path plus, for a Next.js page or endpoint, its kind, URL and methods."""
        info: dict[str, Any] = {"path": path, "kind": "other"}
        route = web_route(path)
        if route:
            info["kind"], info["url"] = route
            if route[0] == "api":
                names = self._names_in_file.get(path, set())
                info["methods"] = [m for m in _HTTP_METHODS if m in names]
        return info

    def to_dict(self) -> dict[str, Any]:
        """Everything the "application map" needs, ready for JSON."""
        totals = {status: 0 for status in STATUSES}
        features: list[dict[str, Any]] = []
        for feature in self.store.features:
            scope = self.scopes[feature.id]
            criteria = []
            counts = {status: 0 for status in STATUSES}
            for criterion in feature.criteria:
                status = self.status(feature.id, criterion)
                counts[status] += 1
                totals[status] += 1
                criteria.append({**criterion.to_dict(), "status": status})
            described = [self.describe_file(path) for path in scope.owned_files]
            features.append(
                {
                    "id": feature.id,
                    "name": feature.name,
                    "summary": feature.summary,
                    "fingerprint": scope.fingerprint,
                    "screens": [d for d in described if d["kind"] == "screen"],
                    "apis": [d for d in described if d["kind"] == "api"],
                    "files": {
                        "owned": scope.owned_files,
                        "shared": scope.context_files,
                    },
                    "functions": {
                        "owned": len(scope.owned_nodes),
                        "reached": len(scope.reached_nodes),
                    },
                    # other features that depend on this one's code
                    "affects": self.affected_by(feature.id),
                    "criteria": criteria,
                    "counts": counts,
                }
            )
        unowned = []
        for path in self.unowned_files:
            unowned.append(
                {**self.describe_file(path), "used_by": self.users_of_file(path)}
            )
        return {
            "features": features,
            "unowned_files": unowned,
            "summary": {
                "features": len(features),
                "criteria": totals,
                "unowned_files": len(unowned),
            },
        }


# ─────────────────────────────────────────────────────────────────────
# Impact of a change on the features
# ─────────────────────────────────────────────────────────────────────
def compute_impact(store: FeatureStore, baseline: Graph, current: Graph) -> dict:
    """Map the differences between two snapshots onto the features.

    For each feature: what was edited in its own files (``direct``), what
    changed in code it depends on (``indirect``), whether its fingerprint —
    and so its behaviour — may have changed, and the status of every
    criterion before and after.
    """
    before = FeatureMap(store, baseline)
    after = FeatureMap(store, current)
    diff = SnapshotDiff(baseline, current).compute()
    node_changes = _node_changes(diff)

    features: list[dict[str, Any]] = []
    direct_ids: list[str] = []
    indirect_ids: list[str] = []
    recheck = 0
    for feature in store.features:
        scope_before, scope_after = before.scopes[feature.id], after.scopes[feature.id]
        owned_nodes = set(scope_before.owned_nodes) | set(scope_after.owned_nodes)
        reached = set(scope_before.reached_nodes) | set(scope_after.reached_nodes)
        context = set(scope_before.context_files) | set(scope_after.context_files)

        direct_files = [
            {"path": change.path, "change": change.change_type}
            for change in diff.files_changed
            if feature.owns_path(change.path)
        ]
        direct_functions = [
            entry for entry in node_changes if entry["id"] in owned_nodes
        ]
        indirect_functions = [
            {**entry, "owners": after.owners_of_file(entry["file"])}
            for entry in node_changes
            if entry["id"] in reached and entry["id"] not in owned_nodes
        ]
        indirect_files = [
            {
                "path": change.path,
                "change": change.change_type,
                "owners": after.owners_of_file(change.path),
            }
            for change in diff.files_changed
            if change.path in context
            and change.module_level_changed
            and not feature.owns_path(change.path)
        ]

        behaviour_changed = scope_before.fingerprint != scope_after.fingerprint
        if direct_files or direct_functions:
            touched = TOUCHED_DIRECT
            direct_ids.append(feature.id)
        elif indirect_functions or indirect_files or behaviour_changed:
            touched = TOUCHED_INDIRECT
            indirect_ids.append(feature.id)
        else:
            touched = TOUCHED_NONE

        criteria = []
        for criterion in feature.criteria:
            status_before = before.status(feature.id, criterion)
            status_after = after.status(feature.id, criterion)
            if status_after == STATUS_NEEDS_RECHECK:
                recheck += 1
            criteria.append(
                {
                    "id": criterion.id,
                    "text": criterion.text,
                    "status_before": status_before,
                    "status_after": status_after,
                }
            )

        features.append(
            {
                "id": feature.id,
                "name": feature.name,
                "touched": touched,
                "behaviour_changed": behaviour_changed,
                "direct": {"files": direct_files, "functions": direct_functions},
                "indirect": {"files": indirect_files, "functions": indirect_functions},
                "criteria": criteria,
            }
        )

    unowned = [
        {
            "path": change.path,
            "change": change.change_type,
            "module_level_changed": change.module_level_changed,
            "used_by": after.users_of_file(change.path)
            or before.users_of_file(change.path),
        }
        for change in diff.files_changed
        if not after.owners_of_file(change.path)
    ]

    return {
        "baseline": _snapshot_label(baseline),
        "current": _snapshot_label(current),
        "features": features,
        "unowned_changes": unowned,
        "summary": {
            "files_changed": len(diff.files_changed),
            "touched_direct": direct_ids,
            "touched_indirect": indirect_ids,
            "criteria_to_recheck": recheck,
        },
    }


def _node_changes(diff: DiffResult) -> list[dict[str, str]]:
    """Every added, removed or edited function of a diff, as plain entries."""
    entries: list[dict[str, str]] = []

    def add(node: Node, change: str) -> None:
        entries.append(
            {
                "id": node.id,
                "name": node.name,
                "file": _posix(node.file_path),
                "change": change,
            }
        )

    for item in diff.nodes_added:
        add(item.node, "added")
    for item in diff.nodes_removed:
        add(item.node, "removed")
    for item in diff.nodes_modified:
        add(item.node, "signature")
    for item in diff.nodes_body_changed:
        add(item.node, "body")
    for item in diff.nodes_renamed:
        if item.old_node is not None:
            add(item.old_node, "removed")
        add(item.node, "added")
    return sorted(entries, key=lambda entry: (entry["file"], entry["id"]))


# ─────────────────────────────────────────────────────────────────────
# Plain-text rendering (the JSON form is what tools should read)
# ─────────────────────────────────────────────────────────────────────
def format_status_text(data: dict[str, Any]) -> str:
    lines: list[str] = []
    for feature in data["features"]:
        counts = feature["counts"]
        lines.append(
            f"{feature['name']}  [{feature['id']}]  "
            f"verified {counts[STATUS_VERIFIED]} · "
            f"needs recheck {counts[STATUS_NEEDS_RECHECK]} · "
            f"unchecked {counts[STATUS_UNCHECKED]}"
        )
        for screen in feature["screens"]:
            lines.append(f"  screen  {screen['url']}  ({screen['path']})")
        for api in feature["apis"]:
            methods = " ".join(api.get("methods", [])) or "-"
            lines.append(f"  api     {methods} {api['url']}  ({api['path']})")
        for criterion in feature["criteria"]:
            lines.append(
                f"  [{criterion['status']}] {criterion['id']}: {criterion['text']}"
            )
        lines.append("")
    if not data["features"]:
        lines.append("No features defined yet (see `codebase-map features add`).")
        lines.append("")
    unowned = data["unowned_files"]
    if unowned:
        lines.append(f"Files that belong to no feature ({len(unowned)}):")
        for item in unowned:
            used = ", ".join(item["used_by"]) or "nothing"
            lines.append(f"  {item['path']}  (used by: {used})")
    return "\n".join(lines).rstrip()


def format_impact_text(data: dict[str, Any]) -> str:
    lines = [f"Baseline: {data['baseline']}", f"Current:  {data['current']}", ""]
    for feature in data["features"]:
        if feature["touched"] == TOUCHED_NONE:
            continue
        note = "" if feature["behaviour_changed"] else "  (no behaviour change)"
        lines.append(
            f"{feature['name']}  [{feature['id']}]  {feature['touched']}{note}"
        )
        for item in feature["direct"]["files"]:
            lines.append(f"  edited   {item['path']}  ({item['change']})")
        for item in feature["direct"]["functions"]:
            lines.append(
                f"  edited   {item['name']}  ({item['change']}, {item['file']})"
            )
        for item in feature["indirect"]["files"]:
            lines.append(f"  depends  {item['path']}  (code outside functions)")
        for item in feature["indirect"]["functions"]:
            lines.append(
                f"  depends  {item['name']}  ({item['change']}, {item['file']})"
            )
        for criterion in feature["criteria"]:
            if criterion["status_after"] == STATUS_NEEDS_RECHECK:
                lines.append(f"  recheck  {criterion['id']}: {criterion['text']}")
        lines.append("")
    untouched = [f["name"] for f in data["features"] if f["touched"] == TOUCHED_NONE]
    if untouched:
        lines.append("Not touched: " + ", ".join(untouched))
    for item in data["unowned_changes"]:
        used = ", ".join(item["used_by"]) or "nothing"
        lines.append(
            f"Changed, in no feature: {item['path']}  ({item['change']}; "
            f"used by: {used})"
        )
    summary = data["summary"]
    lines.append(f"Criteria to recheck: {summary['criteria_to_recheck']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────
def _posix(path: str) -> str:
    return path.replace("\\", "/")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _check_id(value: str, what: str) -> None:
    if not isinstance(value, str) or not _ID_PATTERN.match(value):
        raise FeatureStoreError(
            f"A {what} id uses lowercase letters, digits and hyphens "
            f"(got {value!r})."
        )


def _text(raw: dict[str, Any], key: str, what: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise FeatureStoreError(f'Each {what} needs a non-empty "{key}".')
    return value.strip()


def _evidence_from(raw: Any) -> Optional[Evidence]:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise FeatureStoreError('"evidence" must be an object or null.')
    kind = raw.get("kind")
    if kind not in EVIDENCE_KINDS:
        allowed = ", ".join(EVIDENCE_KINDS)
        raise FeatureStoreError(f"Evidence kind must be one of: {allowed}.")
    return Evidence(
        kind=kind,
        note=str(raw.get("note") or ""),
        checked_at=str(raw.get("checked_at") or ""),
        fingerprint=str(raw.get("fingerprint") or ""),
    )


def _snapshot_label(graph: Graph) -> str:
    return str(graph.metadata.get("label") or graph.generated_at or "?")
