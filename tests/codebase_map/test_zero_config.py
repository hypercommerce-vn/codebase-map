# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for VIBE-101: run without a config file and without PyYAML."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import codebase_map.config as config_module
from codebase_map.cli import main
from codebase_map.config import Config, SourceConfig, detect_languages
from codebase_map.graph.builder import GraphBuilder

SAMPLE_APP = Path(__file__).resolve().parents[1] / "fixtures" / "so-dat-lich" / "base"


def _write(root: Path, rel: str, text: str = "") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _node_names(config: Config) -> set[str]:
    graph = GraphBuilder(config, use_cache=False).build()
    return {node.name for node in graph.nodes.values()}


class TestAutoDetect:
    """Config.auto_detect builds a config from the files it finds."""

    def test_detects_python_and_typescript(self, tmp_path: Path) -> None:
        _write(tmp_path, "api/main.py", "def handler():\n    return 1\n")
        _write(tmp_path, "web/page.tsx", "export function Page() {\n  return 1;\n}\n")

        assert detect_languages(tmp_path) == ["python", "typescript"]
        config = Config.auto_detect(tmp_path)
        assert [s.language for s in config.sources] == ["python", "typescript"]
        assert _node_names(config) == {"handler", "Page"}

    def test_ignores_dependency_and_build_folders(self, tmp_path: Path) -> None:
        _write(tmp_path, "node_modules/pkg/index.js", "function dep() {}\n")
        _write(tmp_path, ".next/server/app.js", "function built() {}\n")
        _write(tmp_path, "dist/bundle.js", "function bundled() {}\n")
        _write(tmp_path, "venv/lib/mod.py", "def vendored():\n    pass\n")
        assert detect_languages(tmp_path) == []

        _write(tmp_path, "src/real.ts", "export function real() {\n  return 1;\n}\n")
        assert detect_languages(tmp_path) == ["typescript"]
        assert _node_names(Config.auto_detect(tmp_path)) == {"real"}

    def test_excluded_names_match_whole_folders_only(self, tmp_path: Path) -> None:
        _write(tmp_path, "out/gen.ts", "export function generated() {\n}\n")
        _write(tmp_path, "app/layout/page.tsx", "export function Layout() {\n}\n")
        assert _node_names(Config.auto_detect(tmp_path)) == {"Layout"}

    def test_minified_and_declaration_files_are_skipped(self, tmp_path: Path) -> None:
        _write(tmp_path, "public/app.min.js", "function minified() {}\n")
        _write(tmp_path, "types/global.d.ts", "export function declared(): void;\n")
        _write(tmp_path, "lib/util.ts", "export function util() {\n}\n")
        assert _node_names(Config.auto_detect(tmp_path)) == {"util"}

    def test_empty_project_has_no_sources(self, tmp_path: Path) -> None:
        assert Config.auto_detect(tmp_path).sources == []

    def test_project_name_comes_from_the_folder(self, tmp_path: Path) -> None:
        _write(tmp_path, "a.py", "def a():\n    pass\n")
        assert Config.auto_detect(tmp_path).project == tmp_path.name

    def test_sample_next_app(self) -> None:
        config = Config.auto_detect(SAMPLE_APP)
        assert [s.language for s in config.sources] == ["typescript"]
        names = _node_names(config)
        assert {"createBooking", "sendReminders", "BookingForm"} <= names
        assert len(names) >= 35


class TestGenerateWithoutConfig:
    """`codebase-map generate` works in a folder that has no config file."""

    def test_auto_detects_and_writes_graph(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(tmp_path, "svc/orders.py", "def create_order():\n    return 1\n")
        monkeypatch.chdir(tmp_path)

        assert main(["generate", "--no-cache"]) == 0

        out = capsys.readouterr().out
        assert "[AUTO]" in out and "python" in out
        graph = json.loads((tmp_path / "docs/function-map/graph.json").read_text())
        assert [n["name"] for n in graph["nodes"]] == ["create_order"]

    def test_explicit_missing_config_still_fails(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(tmp_path, "svc/orders.py", "def create_order():\n    return 1\n")
        monkeypatch.chdir(tmp_path)

        assert main(["generate", "-c", "missing.yaml"]) == 1
        assert "Config not found: missing.yaml" in capsys.readouterr().out

    def test_empty_folder_fails_with_a_reason(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main(["generate"]) == 1
        assert "No config file" in capsys.readouterr().out

    def test_default_json_config_is_used_when_present(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(tmp_path, "svc/orders.py", "def create_order():\n    return 1\n")
        _write(
            tmp_path,
            "codebase-map.json",
            json.dumps(
                {
                    "project": "from-json",
                    "sources": [{"path": ".", "language": "python"}],
                    "output": {"dir": "graph-out", "formats": ["json"]},
                }
            ),
        )
        monkeypatch.chdir(tmp_path)

        assert main(["generate", "--no-cache"]) == 0
        assert "[AUTO]" not in capsys.readouterr().out
        graph = json.loads((tmp_path / "graph-out/graph.json").read_text())
        assert graph["project"] == "from-json"


class TestWithoutPyYAML:
    """Everything except reading YAML works when PyYAML is not installed."""

    @pytest.fixture(autouse=True)
    def _no_yaml(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(config_module, "yaml", None)

    def test_yaml_config_gives_a_clear_error(self, tmp_path: Path) -> None:
        _write(tmp_path, "codebase-map.yaml", "project: demo\n")
        with pytest.raises(RuntimeError, match="PyYAML is not installed"):
            Config.from_file(tmp_path / "codebase-map.yaml")

    def test_cli_reports_the_missing_dependency(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        _write(tmp_path, "codebase-map.yaml", "project: demo\n")
        monkeypatch.chdir(tmp_path)
        assert main(["generate"]) == 1
        assert "PyYAML is not installed" in capsys.readouterr().out

    def test_json_config_still_loads(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "codebase-map.json",
            json.dumps(
                {
                    "project": "demo",
                    "sources": [
                        {
                            "path": "src",
                            "language": "typescript",
                            "exclude_dirs": ["gen"],
                        }
                    ],
                    "domains": {"dat-lich": ["src/bookings/*"], "khac": "src/misc/*"},
                }
            ),
        )
        config = Config.from_file(tmp_path / "codebase-map.json")
        assert config.project == "demo"
        assert config.project_root == tmp_path
        assert config.sources[0].exclude_dirs == ["gen"]
        assert config.domains == {
            "dat-lich": ["src/bookings/*"],
            "khac": ["src/misc/*"],
        }

    def test_auto_detect_still_builds_a_graph(self, tmp_path: Path) -> None:
        _write(tmp_path, "svc/orders.py", "def create_order():\n    return 1\n")
        assert _node_names(Config.auto_detect(tmp_path)) == {"create_order"}


class TestCollectFiles:
    """The directory walk keeps the old exclude rules and adds exclude_dirs."""

    @staticmethod
    def _collect(
        root: Path, excludes: list[str], exclude_dirs: list[str] | None = None
    ) -> list[str]:
        config = Config(sources=[SourceConfig(path=".")], project_root=root)
        builder = GraphBuilder(config, use_cache=False)
        files = builder._collect_files(root, [".py"], excludes, exclude_dirs)
        return sorted(f.relative_to(root).as_posix() for f in files)

    def test_substring_excludes_behave_as_before(self, tmp_path: Path) -> None:
        for rel in ("legacy/a.py", "src/my_legacy.py", "src/keep.py", "src/deep/b.py"):
            _write(tmp_path, rel)
        assert self._collect(tmp_path, ["legacy"]) == ["src/deep/b.py", "src/keep.py"]

    def test_exclude_with_a_slash_still_filters_files(self, tmp_path: Path) -> None:
        for rel in ("src/gen/a.py", "src/hand/b.py"):
            _write(tmp_path, rel)
        assert self._collect(tmp_path, ["src/gen"]) == ["src/hand/b.py"]

    def test_exclude_dirs_match_whole_segments(self, tmp_path: Path) -> None:
        for rel in ("out/a.py", "layout/b.py", "pkg/out/c.py", "pkg/outer.py"):
            _write(tmp_path, rel)
        assert self._collect(tmp_path, [], ["out"]) == ["layout/b.py", "pkg/outer.py"]

    def test_no_excludes_returns_everything(self, tmp_path: Path) -> None:
        for rel in ("a.py", "pkg/b.py", "pkg/notes.txt"):
            _write(tmp_path, rel)
        assert self._collect(tmp_path, []) == ["a.py", "pkg/b.py"]
