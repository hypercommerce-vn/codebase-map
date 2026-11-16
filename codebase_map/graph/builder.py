# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Graph Builder — orchestrates parsers and builds the complete graph."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import posixpath
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from codebase_map import __version__
from codebase_map.config import Config, SourceConfig
from codebase_map.fingerprint import HASH_LENGTH, module_level_hash
from codebase_map.graph.cache import BuildCache, CacheStats
from codebase_map.graph.models import Edge, EdgeType, Graph, Node
from codebase_map.parsers.base import BaseParser, decode_source
from codebase_map.parsers.python_parser import PythonParser
from codebase_map.parsers.typescript_parser import TypeScriptParser

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Build a complete function dependency graph from config."""

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S3-06: Register TypeScript parser alongside Python
    PARSERS: dict[str, type[BaseParser]] = {
        "python": PythonParser,
        "typescript": TypeScriptParser,
        "javascript": TypeScriptParser,
    }

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CBM-P1-01/02: Accept optional label for snapshot metadata
    def __init__(self, config: Config, use_cache: bool = True, label: str = "") -> None:
        self.config = config
        self.use_cache = use_cache
        self._label = label
        self.graph = Graph(
            project=config.project,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S2-02: Incremental cache setup
        self._cache = BuildCache(cache_dir=config.project_root if use_cache else None)
        self._cache_stats = CacheStats()
        self._all_files: set[str] = set()
        # VIBE-102: {posix path: {"hash": ..., "module_hash": ...}} per source file
        self._files: dict[str, dict[str, Any]] = {}
        # VIBE-103: {module id: posix path} of the Python files, to resolve imports
        self._python_modules: dict[str, str] = {}

    @property
    def cache_stats(self) -> CacheStats:
        """Get cache statistics from the last build."""
        return self._cache_stats

    def build(self) -> Graph:
        """Parse all sources and build the graph."""
        start_time = time.monotonic()

        # Load existing cache
        if self.use_cache:
            self._cache.load(project=self.config.project)

        for source in self.config.sources:
            self._process_source(source)

        # Remove stale cache entries (deleted files)
        if self.use_cache:
            removed = self._cache.remove_stale(self._all_files)
            self._cache_stats.removed_files = removed

        self._resolve_self_references()
        self._resolve_typescript_calls()
        self._resolve_python_calls()
        self._resolve_file_imports()
        self._collect_module_level_calls()
        self._deduplicate_edges()
        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CM-S3-04: Apply YAML-defined business flow patterns
        self._apply_flow_patterns()
        # CM-S4-01: Apply YAML-defined domain overrides (after flows, before save)
        self._apply_domain_overrides()

        # Save updated cache
        if self.use_cache:
            self._cache.save()

        # Compute cache stats
        total = self._cache_stats.total_files
        if total > 0:
            self._cache_stats.cache_hit_rate = (
                self._cache_stats.cached_files / total * 100
            )

        elapsed = time.monotonic() - start_time

        # HC-AI | ticket: FDD-TOOL-CODEMAP
        # CBM-P1-01: Build full snapshot metadata (v2.1 schema)
        git_info = _collect_git_info(self.config.project_root)
        label = self._label or _auto_label(git_info)
        graph_stats = self.graph.stats()

        self.graph.metadata = {
            "version": "2.1",
            "generated_at": self.graph.generated_at,
            "commit_sha": git_info.get("commit_sha", ""),
            "branch": git_info.get("branch", ""),
            "label": label,
            "generator_version": __version__,
            "source_paths": [s.path for s in self.config.sources],
            "stats": {
                "total_functions": graph_stats["total_nodes"],
                "total_files": self._cache_stats.total_files,
                "total_edges": graph_stats["total_edges"],
            },
            "build_time_ms": round(elapsed * 1000),
            "cache_stats": {
                "total_files": self._cache_stats.total_files,
                "cached": self._cache_stats.cached_files,
                "parsed": self._cache_stats.parsed_files,
                "removed": self._cache_stats.removed_files,
                "hit_rate": round(self._cache_stats.cache_hit_rate, 1),
            },
            # VIBE-102: content fingerprints, compared by `snapshot-diff`
            "files": dict(sorted(self._files.items())),
        }

        return self.graph

    def _process_source(self, source: SourceConfig) -> None:
        """Process a single source configuration."""
        parser_cls = self.PARSERS.get(source.language)
        if not parser_cls:
            print(f"[WARN] No parser for language: {source.language}")
            return

        parser = parser_cls()
        source_path = self.config.project_root / source.path

        if not source_path.exists():
            print(f"[WARN] Source path not found: {source_path}")
            return

        extensions = parser.supported_extensions()
        files = self._collect_files(
            source_path, extensions, source.exclude, source.exclude_dirs
        )

        for file_path in sorted(files):
            rel = file_path.relative_to(self.config.project_root)
            rel_path = str(rel)
            self._all_files.add(rel_path)
            self._cache_stats.total_files += 1
            if rel.suffix == ".py":
                module = parser.module_id(rel, source.base_module)
                self._python_modules.setdefault(module, rel.as_posix())

            # HC-AI | ticket: FDD-TOOL-CODEMAP
            # VIBE-102: read each file once. The hash drives the cache and is
            # stored in the snapshot so two snapshots can be compared by content.
            file_hash, lines = _read_source(file_path)

            # CM-S2-02: Check cache before parsing
            if self.use_cache and not self._cache.is_changed(rel_path, file_hash):
                cached = self._cache.get_cached(rel_path)
                if cached is not None:
                    cached_nodes, cached_edges = cached
                    for node in cached_nodes:
                        self.graph.add_node(node)
                    for edge in cached_edges:
                        self.graph.add_edge(edge)
                    self._cache_stats.cached_files += 1
                    self._record_file(rel, file_hash, lines, cached_nodes, parser)
                    continue

            # Cache miss or no cache — parse file. The project-relative path is
            # passed so node ids do not depend on where the project sits on disk.
            nodes, edges = parser.parse_file(file_path, source.base_module, rel)

            for node in nodes:
                # Override file_path to be relative
                node.file_path = rel_path
                self.graph.add_node(node)

            for edge in edges:
                self.graph.add_edge(edge)

            # Update cache with fresh parse results
            if self.use_cache:
                # Nodes already have rel_path set
                self._cache.update(rel_path, file_hash, nodes, edges)

            self._cache_stats.parsed_files += 1
            self._record_file(rel, file_hash, lines, nodes, parser)

    def _record_file(
        self,
        rel: Path,
        file_hash: str,
        lines: list[str],
        nodes: list[Node],
        parser: BaseParser,
    ) -> None:
        """Remember the file's fingerprints for the snapshot metadata.

        ``module_hash`` covers the code outside functions that runs: constants
        and top-level statements. Imports and type declarations are left out
        (VIBE-103) — an import is recorded as a dependency instead, and a type
        cannot change behaviour.
        """
        covered = [(n.line_start, n.line_end or n.line_start) for n in nodes]
        covered.extend(parser.non_runtime_ranges(lines))
        self._files[rel.as_posix()] = {
            "hash": file_hash[:HASH_LENGTH],
            "module_hash": module_level_hash(lines, covered, parser.indent_matters),
        }

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-101: walk with directory pruning instead of rglob-then-filter, so a
    # project with a large node_modules/ is not traversed file by file.
    def _collect_files(
        self,
        root: Path,
        extensions: list[str],
        excludes: list[str],
        exclude_dirs: list[str] | None = None,
    ) -> list[Path]:
        """Collect all files matching extensions, respecting excludes.

        ``excludes`` are substrings of the path relative to ``root``.
        ``exclude_dirs`` are directory names matched as whole path segments.
        """
        suffixes = tuple(extensions)
        skip_dirs = set(exclude_dirs or ())
        files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(root):
            # A directory whose name contains an exclude substring can only
            # hold excluded files, so skipping it does not change the result.
            dirnames[:] = [
                d
                for d in dirnames
                if d not in skip_dirs and not any(exc in d for exc in excludes)
            ]
            for filename in filenames:
                if not filename.endswith(suffixes):
                    continue
                file_path = Path(dirpath) / filename
                rel = str(file_path.relative_to(root))
                if any(exc in rel for exc in excludes):
                    continue
                files.append(file_path)
        return files

    def _resolve_self_references(self) -> None:
        """Resolve self.method() calls to actual class method nodes."""
        for edge in self.graph.edges:
            if edge.target.startswith("self."):
                method_name = edge.target.split("self.", 1)[1]
                # Find the caller's parent class
                caller = self.graph.get_node(edge.source)
                if caller and caller.parent_class:
                    resolved = f"{caller.parent_class}.{method_name}"
                    if resolved in self.graph.nodes:
                        edge.target = resolved

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-102: the TypeScript/JavaScript parser records calls as bare names.
    # Point each one at the function it refers to — through the caller's
    # imports, or a function of the same file — so impact analysis works for
    # these languages. Calls to built-ins and packages keep their bare name.
    def _resolve_typescript_calls(self) -> None:
        resolver = self._ts_resolver()
        if not resolver:
            return

        # functions and classes by (file, name); methods are reached by name
        # only through their class, so they are left out
        declared: dict[tuple[str, str], str] = {}
        default_export: dict[str, str] = {}  # file -> node id
        for node in self.graph.nodes.values():
            if node.metadata.get("language") != "typescript" or node.parent_class:
                continue
            path = _posix(node.file_path)
            declared.setdefault((path, node.name), node.id)
            if node.metadata.get("export_default"):
                default_export[path] = node.id

        # What each file imports by name, and what it passes on (re-exports)
        imports: dict[str, dict[str, tuple[str, str]]] = {}
        reexports: dict[str, list[tuple[str, dict[str, str] | None]]] = {}
        for edge in self.graph.edges:
            importer = edge.metadata.get("file")
            if edge.edge_type is not EdgeType.IMPORTS or not importer:
                continue
            names = edge.metadata.get("names")
            if edge.metadata.get("reexport"):
                if edge.metadata.get("star"):
                    reexports.setdefault(importer, []).append((edge.target, None))
                elif isinstance(names, dict):
                    reexports.setdefault(importer, []).append((edge.target, names))
            elif isinstance(names, dict):
                table = imports.setdefault(importer, {})
                for local, exported in names.items():
                    table[local] = (edge.target, exported)

        def find_export(path: str, name: str, depth: int = 0) -> str | None:
            """What a file exports as ``name``, followed through re-exports."""
            if name == "default":
                found = default_export.get(path)
            else:
                found = declared.get((path, name))
            if found or depth >= _MAX_REEXPORT_DEPTH:
                return found
            hops: list[tuple[str, str]] = []
            for source, names in reexports.get(path, []):
                if names is None:
                    hops.append((source, name))
                elif name in names:
                    hops.append((source, names[name]))
            # imported here and exported again without `from`
            if name in imports.get(path, {}):
                hops.append(imports[path][name])
            for source, original in hops:
                target = resolver.resolve(source, path)
                if target and target != path:
                    found = find_export(target, original, depth + 1)
                    if found:
                        return found
            return None

        def resolve_name(path: str, name: str) -> str | None:
            imported = imports.get(path, {}).get(name)
            if not imported:
                return declared.get((path, name))
            source, exported = imported
            target = resolver.resolve(source, path)
            if target is None:
                return None
            found = find_export(target, exported)
            if not found and exported == "default":
                # `export default memo(...)` of something the parser did not
                # mark: fall back to a declaration with the imported name
                found = find_export(target, name)
            return found

        for edge in self.graph.edges:
            if edge.edge_type not in (EdgeType.CALLS, EdgeType.INHERITS):
                continue
            if edge.target in self.graph.nodes:
                continue
            path = edge.metadata.get("module_level", "")
            if not path:
                caller = self.graph.nodes.get(edge.source)
                if caller is None or caller.metadata.get("language") != "typescript":
                    continue
                path = _posix(caller.file_path)
            elif not path.endswith(_TS_EXTENSIONS):
                continue
            resolved = resolve_name(path, edge.target)
            if resolved:
                edge.target = resolved

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-103: a Python call target is spelled the way the import spells it
    # (`app.services.create`), which is not the node id when the package sits
    # in a subfolder or a `src` layout (`backend.app.services.create`). Match
    # by the tail of the id when exactly one node ends that way.
    def _resolve_python_calls(self) -> None:
        tails: dict[str, str | None] = {}
        for node in self.graph.nodes.values():
            if not node.file_path.endswith(_PY_EXTENSION):
                continue
            parts = node.id.split(".")
            for start in range(1, len(parts) - 1):
                tail = ".".join(parts[start:])
                tails[tail] = node.id if tails.get(tail, node.id) == node.id else None
        if not tails:
            return
        for edge in self.graph.edges:
            if edge.edge_type is EdgeType.IMPORTS or edge.target in self.graph.nodes:
                continue
            origin = edge.metadata.get("module_level", "")
            if not origin:
                caller = self.graph.nodes.get(edge.source)
                origin = caller.file_path if caller else ""
            if not origin.endswith(_PY_EXTENSION):
                continue
            resolved = tails.get(edge.target)
            if resolved:
                edge.target = resolved

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-103: which project files each file imports at runtime. Stored per
    # file as ``imports`` in the snapshot metadata, so a change to a constant
    # in one file can be traced to the code that uses it. Type-only imports
    # are left out; packages and built-ins match no project file.
    def _resolve_file_imports(self) -> None:
        resolver = self._ts_resolver()
        imported: dict[str, set[str]] = {}
        for edge in self.graph.edges:
            importer = edge.metadata.get("file")
            if edge.edge_type is not EdgeType.IMPORTS or not importer:
                continue
            if importer not in self._files or edge.metadata.get("type_only"):
                continue
            if importer.endswith(_PY_EXTENSION):
                target = self._python_import_file(edge.target, importer)
            else:
                target = resolver.resolve(edge.target, importer)
            if target and target != importer:
                imported.setdefault(importer, set()).add(target)
        for path, targets in imported.items():
            self._files[path]["imports"] = sorted(targets)

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # VIBE-103: calls made by a file's top-level code — an inline route
    # handler, `export const POST = withAuth(...)`, `ITEMS = seed()` — have no
    # node to start from. They are stored per file as ``calls`` and leave the
    # edge list, so the graph still holds only node-to-node calls.
    def _collect_module_level_calls(self) -> None:
        kept: list[Edge] = []
        calls: dict[str, set[str]] = {}
        for edge in self.graph.edges:
            path = edge.metadata.get("module_level")
            if not path:
                kept.append(edge)
            elif edge.target in self.graph.nodes:
                calls.setdefault(path, set()).add(edge.target)
        self.graph.edges = kept
        for path, targets in calls.items():
            if path in self._files:
                self._files[path]["calls"] = sorted(targets)

    def _ts_resolver(self) -> "_TsImportResolver":
        return _TsImportResolver(self.config.project_root, self._files)

    def _python_import_file(self, target: str, importer: str) -> str | None:
        """The project file a dotted import target lives in, if any.

        Tries the target and its parents as module ids, then the same below
        the importing file's packages (relative imports, ``src`` layouts).
        """
        parts = target.split(".")
        importer_parts = _strip_extension(importer).split("/")[:-1]
        for cut in range(len(importer_parts), -1, -1):
            prefix = importer_parts[:cut]
            for end in range(len(parts), 0, -1):
                module = ".".join(prefix + parts[:end])
                for candidate in (module, f"{module}.__init__"):
                    path = self._python_modules.get(candidate)
                    if path:
                        return path
            if cut == 0:
                break
        # the same search with the absolute form last, for ids trimmed by base_module
        for end in range(len(parts), 0, -1):
            module = ".".join(parts[:end])
            for candidate in (module, f"{module}.__init__"):
                path = self._python_modules.get(candidate)
                if path:
                    return path
        return None

    # HC-AI | ticket: FDD-TOOL-CODEMAP
    # CM-S3-04: Match nodes against config.flows patterns (fnmatch on node id)
    def _apply_flow_patterns(self) -> None:
        if not self.config.flows:
            return
        import fnmatch

        for flow_name, patterns in self.config.flows.items():
            for node in self.graph.nodes.values():
                for pat in patterns:
                    if fnmatch.fnmatch(node.id, pat) or fnmatch.fnmatch(node.name, pat):
                        existing = node.metadata.get("flows", [])
                        if flow_name not in existing:
                            node.metadata["flows"] = existing + [flow_name]
                        break

    # CM-S4-01: Override node domains from config.domains patterns.
    # Patterns are fnmatch globs tested against the node's file path (posix,
    # relative to project root) and the node id. First matching domain in the
    # config's insertion order wins; nodes with no match keep the parser's guess.
    def _apply_domain_overrides(self) -> None:
        if not self.config.domains:
            return
        import fnmatch

        for node in self.graph.nodes.values():
            path = (node.file_path or "").replace("\\", "/")
            for domain, patterns in self.config.domains.items():
                matched = False
                for pat in patterns:
                    if fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(node.id, pat):
                        node.module_domain = domain
                        matched = True
                        break
                if matched:
                    break

    def _deduplicate_edges(self) -> None:
        """Remove duplicate edges."""
        seen: set[tuple[str, str, str]] = set()
        unique: list[Edge] = []
        for edge in self.graph.edges:
            key = (edge.source, edge.target, edge.edge_type.value)
            if key not in seen:
                seen.add(key)
                unique.append(edge)
        self.graph.edges = unique


# HC-AI | ticket: FDD-TOOL-CODEMAP
# VIBE-102: helpers for content fingerprints and TypeScript import resolution
_TS_EXTENSIONS = (".tsx", ".ts", ".jsx", ".js", ".mjs", ".cjs", ".mts", ".cts")
_PY_EXTENSION = ".py"
# `export * from` chains longer than this are not followed
_MAX_REEXPORT_DEPTH = 5


def _read_source(file_path: Path) -> tuple[str, list[str]]:
    """Return (sha256 of the bytes, text lines); empty values if unreadable."""
    try:
        raw = file_path.read_bytes()
    except OSError:
        return "", []
    try:
        text = decode_source(raw)
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest(), text.splitlines()


def _posix(path: str) -> str:
    return path.replace("\\", "/")


def _strip_extension(path: str) -> str:
    for extension in _TS_EXTENSIONS + (_PY_EXTENSION,):
        if path.endswith(extension):
            return path[: -len(extension)]
    return path


def _ancestors(folder: str) -> list[str]:
    """``a/b/c`` → ``["a/b/c", "a/b", "a", ""]``."""
    parts = [part for part in folder.split("/") if part and part != "."]
    return ["/".join(parts[:end]) for end in range(len(parts), -1, -1)]


def _strip_json_comments(text: str) -> str:
    """JSON text without `//` and `/* */` comments and trailing commas."""
    out: list[str] = []
    index = 0
    in_string = False
    while index < len(text):
        char = text[index]
        if in_string:
            out.append(char)
            if char == "\\" and index + 1 < len(text):
                out.append(text[index + 1])
                index += 1
            elif char == '"':
                in_string = False
            index += 1
        elif char == '"':
            in_string = True
            out.append(char)
            index += 1
        elif text.startswith("//", index):
            end = text.find("\n", index)
            index = len(text) if end < 0 else end
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = len(text) if end < 0 else end + 2
        else:
            out.append(char)
            index += 1
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


class _TsImportResolver:
    """Find the project file a TypeScript/JavaScript import refers to.

    In order: a relative path; the ``paths`` of the nearest ``tsconfig.json``
    or ``jsconfig.json`` above the importing file; then the usual root aliases
    (``@/x``, ``~/x``) and bare root-relative paths, tried against every
    folder above the importing file, nearest first, with and without ``src``.
    The last step is what makes an app that sits in a subfolder of the scanned
    project resolve. A package import simply matches no file.
    """

    def __init__(self, project_root: Path, files: object) -> None:
        self._root = project_root
        self._stems = {
            _strip_extension(path): path
            for path in files  # type: ignore[attr-defined]
            if path.endswith(_TS_EXTENSIONS)
        }
        self._configs: dict[str, tuple[str, dict[str, list[str]]] | None] = {}

    def __bool__(self) -> bool:
        return bool(self._stems)

    def resolve(self, source: str, importer: str) -> str | None:
        for stem in self._candidates(source, posixpath.dirname(importer)):
            path = self._stems.get(stem) or self._stems.get(f"{stem}/index")
            if path:
                return path
        return None

    def _candidates(self, source: str, folder: str) -> list[str]:
        if source.startswith("."):
            joined = posixpath.normpath(posixpath.join(folder, source))
            return [_strip_extension(joined)]
        stems = self._from_config(source, folder)
        rest = source[2:] if source.startswith(("@/", "~/")) else source
        for base in _ancestors(folder):
            for prefix in (base, posixpath.join(base, "src")):
                stems.append(_strip_extension(posixpath.join(prefix, rest)))
        return stems

    def _from_config(self, source: str, folder: str) -> list[str]:
        config = None
        for base in _ancestors(folder):
            if base not in self._configs:
                self._configs[base] = self._read_config(base)
            if self._configs[base]:
                config = self._configs[base]
                break
        if not config:
            return []
        base_url, paths = config
        stems: list[str] = []
        for pattern, targets in paths.items():
            head, star, tail = pattern.partition("*")
            if star:
                if not (source.startswith(head) and source.endswith(tail)):
                    continue
                if len(source) < len(head) + len(tail):
                    continue
                middle = source[len(head) : len(source) - len(tail)]
            elif source == pattern:
                middle = ""
            else:
                continue
            for target in targets:
                joined = posixpath.join(base_url, target.replace("*", middle))
                stems.append(_strip_extension(posixpath.normpath(joined)))
        return stems

    def _read_config(self, folder: str) -> tuple[str, dict[str, list[str]]] | None:
        for name in ("tsconfig.json", "jsconfig.json"):
            path = self._root / folder / name
            if not path.is_file():
                continue
            try:
                text = decode_source(path.read_bytes())
                options = json.loads(_strip_json_comments(text)).get(
                    "compilerOptions", {}
                )
                paths = options.get("paths")
                base_url = options.get("baseUrl")
            except (OSError, ValueError, AttributeError):
                continue
            if not isinstance(paths, dict):
                if not isinstance(base_url, str):
                    continue
                paths = {"*": ["*"]}  # baseUrl alone: bare imports start there
            base = posixpath.normpath(posixpath.join(folder, base_url or "."))
            cleaned = {
                key: [item for item in value if isinstance(item, str)]
                for key, value in paths.items()
                if isinstance(value, list)
            }
            return ("" if base == "." else base), cleaned
        return None


# HC-AI | ticket: FDD-TOOL-CODEMAP
# CBM-P1-01: Git info helpers for snapshot metadata
def _collect_git_info(project_root: Path) -> dict[str, str]:
    """Collect git commit SHA and branch from the project root.

    Returns dict with ``commit_sha`` and ``branch`` keys.
    Falls back gracefully if git is unavailable or detached HEAD.
    """
    info: dict[str, str] = {"commit_sha": "", "branch": ""}
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=5,
        )
        if sha.returncode == 0:
            info["commit_sha"] = sha.stdout.strip()

        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=5,
        )
        if branch.returncode == 0:
            info["branch"] = branch.stdout.strip() or "detached"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.debug("git not available, metadata will have empty git fields")
    return info


def _auto_label(git_info: dict[str, str]) -> str:
    """Generate automatic label from branch + short SHA + timestamp.

    Format: ``{branch}_{sha}_{YYYYMMDD_HHMM}`` (e.g. ``main_a7bd55e_20260412_1430``).
    """
    branch = git_info.get("branch", "unknown") or "unknown"
    sha = git_info.get("commit_sha", "unknown") or "unknown"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
    # Sanitize branch name for filesystem safety
    safe_branch = branch.replace("/", "_").replace("\\", "_")
    return f"{safe_branch}_{sha}_{ts}"
