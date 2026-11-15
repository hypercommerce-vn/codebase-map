# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for VIBE-104: the cbm-vibe plugin and its build.

The plugin has to load on claude.ai chat, Cowork and Claude Code, so these
tests pin the rules the three surfaces share: where the manifest sits, which
frontmatter keys a skill may carry, and how the archives are laid out. They
also run the bundled tool the way the skill runs it — from the built plugin,
with a bare interpreter and nothing installed.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from codebase_map.cli import build_parser

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN = REPO_ROOT / "plugins" / "cbm-vibe"
SKILL = PLUGIN / "skills" / "cbm-vibe"
SKILL_MD = SKILL / "SKILL.md"
RUNNER = SKILL / "scripts" / "cbm.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "so-dat-lich"

# The keys claude.ai accepts when a skill is uploaded; any other key is a
# hard error there, although Claude Code would ignore it.
UPLOADABLE_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
RUNNER_CALL = 'python3 "${CLAUDE_SKILL_DIR}/scripts/cbm.py"'


def _load_build_script():
    spec = importlib.util.spec_from_file_location(
        "build_cbm_vibe", REPO_ROOT / "scripts" / "build_cbm_vibe.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frontmatter() -> dict[str, str]:
    """Top-level frontmatter keys of SKILL.md and their raw values."""
    text = SKILL_MD.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    block = text.split("---\n", 2)[1]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2)
    return fields


def _documented_commands() -> list[tuple[str, list[str]]]:
    """Every tool invocation shown in the skill, as (file name, arguments)."""
    commands: list[tuple[str, list[str]]] = []
    for path in [SKILL_MD, *sorted((SKILL / "references").glob("*.md"))]:
        text = path.read_text(encoding="utf-8").replace("\\\n", " ")
        for line in text.splitlines():
            line = line.strip()
            if line.startswith(RUNNER_CALL):
                rest = line[len(RUNNER_CALL) :]
            elif line.startswith("CBM "):
                rest = line[len("CBM") :]
            else:
                continue
            rest = rest.split("  #", 1)[0]
            if "<" in rest:  # a placeholder such as <lệnh>, not a real command
                continue
            commands.append((path.name, shlex.split(rest)))
    return commands


def _run(args: list[str], cwd: Path, **env: str) -> subprocess.CompletedProcess:
    """Run a command with a clean environment: no PYTHONPATH, nothing extra."""
    environment = {
        key: value for key, value in os.environ.items() if key != "PYTHONPATH"
    }
    environment.update(env)
    return subprocess.run(
        args, cwd=cwd, env=environment, capture_output=True, timeout=120, check=False
    )


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    return _load_build_script().build(tmp_path_factory.mktemp("dist"))


@pytest.fixture()
def app(tmp_path: Path) -> Path:
    root = tmp_path / "so-dat-lich"
    shutil.copytree(FIXTURE / "base", root)
    return root


class TestManifest:
    def test_manifest_is_where_every_surface_looks(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        assert manifest["name"] == "cbm-vibe"
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", manifest["name"])
        for key in ("version", "description", "license"):
            assert manifest[key], key
        assert manifest["author"]["name"]

    def test_only_the_manifest_is_inside_dot_claude_plugin(self) -> None:
        inside = [path.name for path in (PLUGIN / ".claude-plugin").iterdir()]
        assert inside == ["plugin.json"]

    def test_no_top_level_bin_folder(self) -> None:
        """claude.ai and Cowork refuse a plugin that has one."""
        assert not (PLUGIN / "bin").exists()

    def test_no_personal_contact_details(self) -> None:
        for path in PLUGIN.rglob("*"):
            if path.is_file():
                assert "@gmail.com" not in path.read_text(encoding="utf-8"), path

    def test_readme_is_long_enough_for_the_directory(self) -> None:
        text = (PLUGIN / "README.md").read_text(encoding="utf-8")
        prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        assert len(prose.split()) >= 40


class TestSkillFile:
    def test_frontmatter_has_only_uploadable_keys(self) -> None:
        assert set(_frontmatter()) - {"version"} <= UPLOADABLE_KEYS

    def test_name_matches_the_folder(self) -> None:
        name = _frontmatter()["name"]
        assert name == SKILL.name == "cbm-vibe"
        assert re.fullmatch(r"[a-z0-9-]{1,64}", name)

    def test_description_fits_the_limit(self) -> None:
        description = _frontmatter()["description"]
        assert 100 < len(description) <= 1024
        assert "<" not in description and ">" not in description

    def test_instructions_stay_short(self) -> None:
        assert len(SKILL_MD.read_text(encoding="utf-8").splitlines()) < 500

    def test_bundled_script_is_pre_approved_by_its_exact_command(self) -> None:
        allowed = _frontmatter()["allowed-tools"]
        assert f"Bash({RUNNER_CALL} *)" in allowed
        assert RUNNER_CALL in SKILL_MD.read_text(encoding="utf-8")

    def test_every_linked_file_exists(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        links = re.findall(r"\]\(((?:references|scripts)/[^)#]+)", text)
        assert set(links) == {"references/lenh.md", "references/mau-bao-cao.md"}
        for link in links:
            assert (SKILL / link).is_file(), link
        assert RUNNER.is_file()

    def test_long_reference_files_start_with_a_table_of_contents(self) -> None:
        for path in (SKILL / "references").glob("*.md"):
            lines = path.read_text(encoding="utf-8").splitlines()
            if len(lines) > 100:
                assert any("Mục lục" in line for line in lines[:15]), path.name

    def test_the_three_moments_and_three_states_are_covered(self) -> None:
        text = SKILL_MD.read_text(encoding="utf-8")
        for heading in (
            "## Khoảnh khắc 1 — Chốt yêu cầu",
            "## Khoảnh khắc 2 — Báo cáo thay đổi",
            "## Khoảnh khắc 3 — Bản đồ ứng dụng",
            "## Khi công cụ không chạy được",
        ):
            assert heading in text
        for state in ("Có bằng chứng", "Cần kiểm lại", "Chưa kiểm"):
            assert state in text
        for value in ("verified", "needs_recheck", "unchecked"):
            assert f"`{value}`" in text


class TestDocumentedCommands:
    """The commands the skill tells Claude to run are commands that exist."""

    def test_there_are_commands_to_check(self) -> None:
        commands = _documented_commands()
        assert len(commands) >= 12
        assert {name for name, _ in commands} == {"SKILL.md", "lenh.md"}

    @pytest.mark.parametrize(
        ("source", "arguments"),
        _documented_commands(),
        ids=lambda value: " ".join(value)[:60] if isinstance(value, list) else value,
    )
    def test_command_is_accepted_by_the_parser(
        self, source: str, arguments: list[str]
    ) -> None:
        try:
            args = build_parser().parse_args(arguments)
        except SystemExit:  # argparse reports a bad command line this way
            pytest.fail(f"{source}: not a valid command line: {arguments}")
        assert args.command in {"features", "generate"}

    def test_the_flow_in_the_skill_runs_as_written(self, app: Path) -> None:
        """Moment 1 step 5 through moment 2 step 2, with the skill's own lines."""
        flow = [
            ["features", "add", "--id", "dat-lich", "--name", "Đặt lịch"]
            + ["--files", "app/dat-lich", "app/api/bookings", "lib/bookings.ts"],
            ["features", "criterion", "--feature", "dat-lich"]
            + ["--text", "Khách huỷ được lịch khi còn hơn 2 tiếng.", "--json"],
            ["generate", "--label", "truoc-dat-lich-1"],
            ["generate", "--label", "sau-dat-lich-1"],
            ["features", "impact", "--baseline", "truoc-dat-lich-1"]
            + ["--current", "sau-dat-lich-1", "--json"],
            ["features", "add", "--id", "dat-lich", "--append"]
            + ["--files", "app/api/bookings/[id]/route.ts"],
            ["features", "evidence", "--criterion", "dat-lich-1"]
            + ["--kind", "manual", "--note", "Chủ tiệm tự bấm thử"],
            ["features", "status", "--json"],
        ]
        for step in flow:
            if step[:3] == ["generate", "--label", "sau-dat-lich-1"]:
                shutil.copytree(FIXTURE / "change-huy-lich", app, dirs_exist_ok=True)
            result = _run([sys.executable, str(RUNNER), *step], app)
            assert result.returncode == 0, (step, result.stdout, result.stderr)

        status = json.loads(result.stdout.decode("utf-8"))
        feature = status["features"][0]
        assert "app/api/bookings/[id]/route.ts" in feature["files"]["owned"]
        assert feature["criteria"][0]["status"] == "verified"


class TestAppendingFiles:
    def test_append_keeps_the_existing_patterns(self, app: Path) -> None:
        base = [sys.executable, str(RUNNER), "features", "add", "--id", "nhac-lich"]
        first = _run(base + ["--name", "Nhắc lịch", "--files", "lib/reminders.ts"], app)
        second = _run(base + ["--append", "--files", "app/api/reminders"], app)
        again = _run(base + ["--append", "--files", "app/api/reminders"], app)
        assert (first.returncode, second.returncode, again.returncode) == (0, 0, 0)

        store = json.loads((app / ".cbm" / "features.json").read_text(encoding="utf-8"))
        assert store["features"][0]["name"] == "Nhắc lịch"
        assert store["features"][0]["files"] == [
            "lib/reminders.ts",
            "app/api/reminders",
        ]

    def test_new_feature_needs_a_name_and_files(self, app: Path) -> None:
        result = _run(
            [sys.executable, str(RUNNER), "features", "add", "--id", "moi"], app
        )
        assert result.returncode == 1
        assert b"--name and --files" in result.stdout


class TestBuild:
    def test_plugin_carries_the_package(self, built: dict[str, Path]) -> None:
        plugin = built["plugin"]
        vendor = plugin / "skills" / "cbm-vibe" / "scripts" / "vendor"
        assert (plugin / ".claude-plugin" / "plugin.json").is_file()
        assert (vendor / "codebase_map" / "cli.py").is_file()
        assert (vendor / "codebase_map" / "features.py").is_file()
        # the map page needs the bundled chart library
        assert (vendor / "codebase_map" / "exporters" / "d3.v7.min.js").is_file()
        assert "codebase_map" in (vendor / "VERSION").read_text(encoding="utf-8")
        assert (plugin / "LICENSE").is_file()

    def test_no_build_leftovers(self, built: dict[str, Path]) -> None:
        names = {path.name for path in built["plugin"].rglob("*")}
        assert "__pycache__" not in names
        assert not any(name.endswith(".pyc") for name in names)
        assert not (built["plugin"] / "bin").exists()

    def test_within_the_upload_limits(self, built: dict[str, Path]) -> None:
        files = [path for path in built["plugin"].rglob("*") if path.is_file()]
        assert len(files) < 5000
        assert built["plugin_zip"].stat().st_size < 200 * 1024 * 1024

    def test_plugin_archive_has_one_top_level_folder(
        self, built: dict[str, Path]
    ) -> None:
        with zipfile.ZipFile(built["plugin_zip"]) as archive:
            names = archive.namelist()
        assert {name.split("/")[0] for name in names} == {"cbm-vibe"}
        assert "cbm-vibe/.claude-plugin/plugin.json" in names
        assert "cbm-vibe/skills/cbm-vibe/SKILL.md" in names

    def test_skill_archive_has_the_skill_folder_at_the_top(
        self, built: dict[str, Path]
    ) -> None:
        with zipfile.ZipFile(built["skill_zip"]) as archive:
            names = archive.namelist()
        assert {name.split("/")[0] for name in names} == {"cbm-vibe"}
        assert "cbm-vibe/SKILL.md" in names
        assert "cbm-vibe/scripts/vendor/codebase_map/cli.py" in names

    def test_building_twice_replaces_the_previous_build(self, tmp_path: Path) -> None:
        build = _load_build_script().build
        (tmp_path / "cbm-vibe").mkdir()
        (tmp_path / "cbm-vibe" / "stale.txt").write_text("old", encoding="utf-8")
        made = build(tmp_path)
        assert not (made["plugin"] / "stale.txt").exists()


class TestBundledTool:
    """Run the tool as the skill does: a bare interpreter, nothing installed."""

    def _tool(self, built: dict[str, Path]) -> list[str]:
        runner = built["plugin"] / "skills" / "cbm-vibe" / "scripts" / "cbm.py"
        # -I: no PYTHONPATH, no user site-packages, no current folder on the path
        return [sys.executable, "-I", str(runner)]

    def test_version(self, built: dict[str, Path], app: Path) -> None:
        result = _run(self._tool(built) + ["--version"], app)
        assert result.returncode == 0
        assert result.stdout.startswith(b"codebase-map ")

    def test_first_look_at_a_project(self, built: dict[str, Path], app: Path) -> None:
        result = _run(self._tool(built) + ["features", "status", "--json"], app)
        assert result.returncode == 0, result.stderr
        status = json.loads(result.stdout.decode("utf-8"))

        assert status["features"] == []
        screens = {
            item["url"] for item in status["unowned_files"] if item["kind"] == "screen"
        }
        assert {"/dat-lich", "/lich-cua-toi", "/bao-cao"} <= screens
        # nothing is written into the project by just looking
        assert not (app / ".cbm").exists()
        assert not (app / "docs").exists()

    def test_the_package_used_is_the_bundled_copy(
        self, built: dict[str, Path], app: Path
    ) -> None:
        vendor = built["plugin"] / "skills" / "cbm-vibe" / "scripts" / "vendor"
        probe = (
            "import runpy, sys; sys.argv = ['cbm.py', '--version']\n"
            "try:\n"
            f"    runpy.run_path({str(self._tool(built)[2])!r}, run_name='__main__')\n"
            "except SystemExit:\n"
            "    pass\n"
            "import codebase_map; print(codebase_map.__file__)\n"
        )
        result = _run([sys.executable, "-I", "-c", probe], app)
        assert result.returncode == 0, result.stderr
        assert str(vendor) in result.stdout.decode("utf-8")

    def test_runner_without_the_package_says_so(self, tmp_path: Path) -> None:
        lonely = tmp_path / "scripts" / "cbm.py"
        lonely.parent.mkdir()
        shutil.copy(RUNNER, lonely)
        result = _run([sys.executable, "-I", str(lonely), "--version"], tmp_path)
        assert result.returncode == 2
        assert b"package is missing" in result.stdout

    def test_vietnamese_output_survives_a_legacy_console_encoding(
        self, built: dict[str, Path], app: Path
    ) -> None:
        """A redirected stdout on Windows is not UTF-8 by default."""
        (app / ".cbm").mkdir()
        shutil.copy(FIXTURE / "features.json", app / ".cbm" / "features.json")
        # without -I, so that PYTHONIOENCODING is honoured
        tool = [sys.executable, self._tool(built)[2], "features", "status"]
        result = _run(tool, app, PYTHONIOENCODING="ascii")

        assert result.returncode == 0, result.stderr
        assert "Đặt lịch  [dat-lich]" in result.stdout.decode("utf-8")
