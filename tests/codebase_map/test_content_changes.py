# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for VIBE-102: seeing edits that leave every signature alone.

The sample app under tests/fixtures/so-dat-lich comes with one requested
change (customers can cancel a booking) that also edits the reminder module,
which nobody asked for. Before VIBE-102 the snapshot diff could not see that
edit: no signature changed. These tests pin that it is reported now.
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from codebase_map.cli import main
from codebase_map.config import Config, SourceConfig
from codebase_map.graph.builder import GraphBuilder
from codebase_map.graph.diff_formatter import (
    filter_breaking_only,
    format_diff_json,
    format_diff_markdown,
    format_diff_text,
)
from codebase_map.graph.models import EdgeType, Graph, LayerType
from codebase_map.graph.snapshot_diff import DiffResult, SnapshotDiff

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "so-dat-lich"
BASE = FIXTURE / "base"
CHANGE = FIXTURE / "change-huy-lich"


def _build(root: Path, use_cache: bool = False) -> Graph:
    return GraphBuilder(Config.auto_detect(root), use_cache=use_cache).build()


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _python_project(root: Path) -> Config:
    return Config(
        project="shop",
        sources=[SourceConfig(path=".", language="python")],
        project_root=root,
    )


@pytest.fixture()
def app(tmp_path: Path) -> Path:
    """A private copy of the sample app, before the change."""
    root = tmp_path / "so-dat-lich"
    shutil.copytree(BASE, root)
    return root


@pytest.fixture()
def before_after(app: Path) -> tuple[Graph, Graph]:
    """Graphs of the sample app before and after the cancel-booking change."""
    before = _build(app)
    shutil.copytree(CHANGE, app, dirs_exist_ok=True)
    return before, _build(app)


@pytest.fixture()
def diff(before_after: tuple[Graph, Graph]) -> DiffResult:
    before, after = before_after
    return SnapshotDiff(before, after).compute()


class TestSampleAppGraph:
    """The graph of the sample app is complete enough to reason about."""

    def test_ids_are_relative_to_the_project(self, app: Path) -> None:
        graph = _build(app)
        assert app.is_absolute()
        tops = {node_id.split(".")[0] for node_id in graph.nodes}
        assert tops == {"app", "components", "lib"}
        assert all(not Path(n.file_path).is_absolute() for n in graph.nodes.values())

    def test_data_access_functions_are_in_the_graph(self, app: Path) -> None:
        graph = _build(app)
        # Generic functions; the parser used to miss them
        assert "lib.db.readAll" in graph.nodes
        assert "lib.db.insertRow" in graph.nodes

    def test_every_function_has_a_range_and_a_fingerprint(self, app: Path) -> None:
        graph = _build(app)
        assert graph.nodes
        for node in graph.nodes.values():
            assert node.line_end >= node.line_start >= 1, node.id
            assert node.metadata.get("body_hash"), node.id

    def test_calls_point_at_the_function_they_refer_to(self, app: Path) -> None:
        graph = _build(app)
        calls = {
            (e.source, e.target) for e in graph.edges if e.edge_type is EdgeType.CALLS
        }
        # through an `@/` alias import
        assert ("lib.bookings.createBooking", "lib.slots.isSlotFree") in calls
        assert ("app.api.bookings.route.POST", "lib.bookings.createBooking") in calls
        # a function of the same file
        assert ("lib.reminders.sendReminders", "lib.reminders.sendSms") in calls
        # a component used in JSX, imported as a default export
        assert (
            "app.dat-lich.page.BookingPage",
            "components.BookingForm.BookingForm",
        ) in calls
        # a handler declared inside its component
        assert (
            "components.BookingForm.BookingForm",
            "components.BookingForm.submitBooking",
        ) in calls

    def test_impact_analysis_follows_the_resolved_calls(self, app: Path) -> None:
        graph = _build(app)
        assert graph.impact_analysis("lib.slots.isSlotFree", depth=3) == {
            "lib.bookings.createBooking",
            "app.api.bookings.route.POST",
        }
        affected = graph.impact_analysis("lib.bookings.listUpcomingBookings", depth=3)
        assert "lib.reminders.sendReminders" in affected
        assert "app.api.reminders.route.POST" in affected

    def test_file_fingerprints_are_in_the_metadata(self, app: Path) -> None:
        files = _build(app).metadata["files"]
        assert "lib/reminders.ts" in files
        assert "app/api/bookings/route.ts" in files
        assert set(files["lib/reminders.ts"]) == {"hash", "module_hash"}
        assert list(files) == sorted(files)

    def test_same_content_gives_the_same_fingerprints_anywhere(
        self, app: Path, tmp_path: Path
    ) -> None:
        elsewhere = tmp_path / "deep" / "er" / "copy"
        shutil.copytree(BASE, elsewhere)
        here, there = _build(app), _build(elsewhere)
        assert here.metadata["files"] == there.metadata["files"]
        assert set(here.nodes) == set(there.nodes)
        assert {n.id: n.metadata["body_hash"] for n in here.nodes.values()} == {
            n.id: n.metadata["body_hash"] for n in there.nodes.values()
        }


class TestUnrequestedEditIsReported:
    """The change edits lib/reminders.ts although only cancelling was asked."""

    def test_reminders_file_is_reported_as_modified(self, diff: DiffResult) -> None:
        assert diff.content_tracking is True
        by_path = {change.path: change for change in diff.files_changed}
        assert by_path["lib/reminders.ts"].change_type == "modified"
        # the reminder window is a constant outside every function
        assert by_path["lib/reminders.ts"].module_level_changed is True

    def test_reworded_message_is_a_body_change(self, diff: DiffResult) -> None:
        changed = {change.node.id for change in diff.nodes_body_changed}
        assert "lib.reminders.buildReminderMessage" in changed
        # signatures are the same, so the signature diff alone sees nothing
        assert diff.nodes_modified == []
        assert all(c.change_type == "body_changed" for c in diff.nodes_body_changed)
        assert all(c.old_node is not None for c in diff.nodes_body_changed)

    def test_untouched_functions_are_not_reported(self, diff: DiffResult) -> None:
        changed = {change.node.id for change in diff.nodes_body_changed}
        assert "lib.reminders.sendReminders" not in changed
        assert "lib.reminders.dueReminders" not in changed
        assert "lib.customers.findCustomer" not in changed

    def test_the_requested_change_is_reported_too(self, diff: DiffResult) -> None:
        added = {change.node.id for change in diff.nodes_added}
        assert {
            "lib.bookings.cancelBooking",
            "lib.bookings.canCancel",
            "lib.slots.releaseSlot",
            "app.api.bookings.[id].route.DELETE",
        } <= added
        by_path = {change.path: change for change in diff.files_changed}
        assert by_path["app/api/bookings/[id]/route.ts"].change_type == "added"
        # only new functions were added to lib/slots.ts
        assert by_path["lib/slots.ts"].module_level_changed is False

    def test_exactly_the_edited_files_are_listed(self, diff: DiffResult) -> None:
        overlay = sorted(
            path.relative_to(CHANGE).as_posix()
            for path in CHANGE.rglob("*")
            if path.is_file()
        )
        assert [change.path for change in diff.files_changed] == overlay
        assert diff.summary["files_changed"] == len(overlay)

    def test_report_is_the_same_every_time(
        self, before_after: tuple[Graph, Graph]
    ) -> None:
        before, after = before_after
        first = format_diff_json(SnapshotDiff(before, after).compute())
        second = format_diff_json(SnapshotDiff(before, after).compute())
        assert first == second

    def test_added_functions_are_listed_in_file_order(self, diff: DiffResult) -> None:
        keys = [(c.node.file_path, c.node.line_start) for c in diff.nodes_added]
        assert keys == sorted(keys)


class TestBodyChangeRules:
    def test_no_change_means_nothing_to_report(self, app: Path) -> None:
        result = SnapshotDiff(_build(app), _build(app)).compute()
        assert result.content_tracking is True
        assert result.nodes_body_changed == []
        assert result.files_changed == []
        assert not result.has_changes()

    def test_reformatting_changes_the_file_but_no_body(self, app: Path) -> None:
        before = _build(app)
        path = app / "lib" / "slots.ts"
        path.write_text(
            path.read_text(encoding="utf-8").replace("  ", "    "), encoding="utf-8"
        )
        result = SnapshotDiff(before, _build(app)).compute()

        assert [change.path for change in result.files_changed] == ["lib/slots.ts"]
        assert result.files_changed[0].module_level_changed is False
        assert result.nodes_body_changed == []

    def test_a_body_only_edit_counts_as_a_change(self, app: Path) -> None:
        before = _build(app)
        path = app / "lib" / "slots.ts"
        text = path.read_text(encoding="utf-8")
        assert "s.startsAt === startsAt && s.taken" in text
        path.write_text(
            text.replace("s.startsAt === startsAt && s.taken", "s.taken"), "utf-8"
        )
        result = SnapshotDiff(before, _build(app)).compute()

        assert [c.node.id for c in result.nodes_body_changed] == [
            "lib.slots.isSlotFree"
        ]
        assert result.summary["functions_body_changed"] == 1
        assert result.summary["functions_modified"] == 0
        assert result.has_changes()

    def test_signature_change_is_reported_once(self, tmp_path: Path) -> None:
        _write(tmp_path, "shop.py", "def price(item):\n    return 1\n")
        before = GraphBuilder(_python_project(tmp_path), use_cache=False).build()
        _write(tmp_path, "shop.py", "def price(item, tax):\n    return 1 + tax\n")
        after = GraphBuilder(_python_project(tmp_path), use_cache=False).build()
        result = SnapshotDiff(before, after).compute()

        assert [c.node.name for c in result.nodes_modified] == ["price"]
        assert result.nodes_body_changed == []

    def test_python_method_edit_does_not_flag_the_class(self, tmp_path: Path) -> None:
        source = (
            "RATE = 2\n\n\n"
            "class Shop:\n"
            "    def price(self, item):\n"
            "        return item * RATE\n\n"
            "    def name(self):\n"
            "        return 'Moc'\n"
        )
        _write(tmp_path, "shop.py", source)
        before = GraphBuilder(_python_project(tmp_path), use_cache=False).build()
        _write(tmp_path, "shop.py", source.replace("item * RATE", "item * RATE + 1"))
        after = GraphBuilder(_python_project(tmp_path), use_cache=False).build()
        result = SnapshotDiff(before, after).compute()

        assert [c.node.id for c in result.nodes_body_changed] == ["shop.Shop.price"]
        assert result.files_changed[0].module_level_changed is False

    def test_python_module_level_edit_is_reported(self, tmp_path: Path) -> None:
        source = "RATE = 2\n\n\ndef price(item):\n    return item * RATE\n"
        _write(tmp_path, "shop.py", source)
        before = GraphBuilder(_python_project(tmp_path), use_cache=False).build()
        _write(tmp_path, "shop.py", source.replace("RATE = 2", "RATE = 3"))
        after = GraphBuilder(_python_project(tmp_path), use_cache=False).build()
        result = SnapshotDiff(before, after).compute()

        assert result.nodes_body_changed == []
        assert [(c.path, c.module_level_changed) for c in result.files_changed] == [
            ("shop.py", True)
        ]

    def test_removed_file_is_reported(self, app: Path) -> None:
        before = _build(app)
        (app / "lib" / "reports.ts").unlink()
        result = SnapshotDiff(before, _build(app)).compute()

        assert [(c.path, c.change_type) for c in result.files_changed] == [
            ("lib/reports.ts", "removed")
        ]
        removed = {c.node.id for c in result.nodes_removed}
        assert "lib.reports.revenueByDay" in removed


class TestOlderSnapshots:
    """A snapshot written before VIBE-102 has no fingerprints."""

    @staticmethod
    def _without_fingerprints(graph: Graph) -> Graph:
        data = copy.deepcopy(graph.to_dict())
        data["metadata"].pop("files")
        for node in data["nodes"]:
            node["metadata"].pop("body_hash", None)
        return Graph.from_dict(data)

    def test_content_is_reported_as_not_tracked(
        self, before_after: tuple[Graph, Graph]
    ) -> None:
        before, after = before_after
        result = SnapshotDiff(self._without_fingerprints(before), after).compute()

        assert result.content_tracking is False
        assert result.nodes_body_changed == []
        assert result.files_changed == []
        # the structural diff still works
        assert "lib.bookings.cancelBooking" in {c.node.id for c in result.nodes_added}

    def test_reports_say_so(self, before_after: tuple[Graph, Graph]) -> None:
        before, after = before_after
        result = SnapshotDiff(self._without_fingerprints(before), after).compute()

        assert "not tracked" in format_diff_text(result)
        assert "not tracked" in format_diff_markdown(result)
        assert "Bodies changed" not in format_diff_text(result)
        assert json.loads(format_diff_json(result))["content_tracking"] is False

    def test_snapshot_round_trip_keeps_the_fingerprints(
        self, before_after: tuple[Graph, Graph]
    ) -> None:
        before, after = before_after
        reloaded = [
            Graph.from_dict(json.loads(json.dumps(g.to_dict())))
            for g in (before, after)
        ]
        direct = format_diff_json(SnapshotDiff(before, after).compute())
        via_json = format_diff_json(SnapshotDiff(*reloaded).compute())
        assert direct == via_json


class TestReports:
    def test_text_report(self, diff: DiffResult) -> None:
        text = format_diff_text(diff)
        assert "Bodies changed: 2" in text
        assert "Files changed:  6" in text
        assert "[BODY CHANGED]" in text
        assert "~ buildReminderMessage  (lib/reminders.ts:13-16)" in text
        assert "M lib/reminders.ts  (code outside functions changed)" in text
        assert "A app/api/bookings/[id]/route.ts" in text
        assert "M lib/slots.ts\n" in text + "\n"
        assert "not tracked" not in text

    def test_markdown_report(self, diff: DiffResult) -> None:
        markdown = format_diff_markdown(diff)
        assert "| Function bodies changed | **2** |" in markdown
        assert "| Files changed | **6** |" in markdown
        assert "### Body Changes (signature unchanged)" in markdown
        assert "| `buildReminderMessage` | lib/reminders.ts | 13-16 |" in markdown
        assert "### Changed Files" in markdown
        assert "| lib/reminders.ts | modified | changed |" in markdown
        assert "| lib/slots.ts | modified | unchanged |" in markdown
        assert "| app/api/bookings/[id]/route.ts | added | - |" in markdown

    def test_json_report(self, diff: DiffResult) -> None:
        data = json.loads(format_diff_json(diff))
        assert data["content_tracking"] is True
        assert data["summary"]["functions_body_changed"] == 2
        assert data["summary"]["files_changed"] == 6
        assert {
            "path": "lib/reminders.ts",
            "change_type": "modified",
            "module_level_changed": True,
        } in data["files_changed"]
        reminder = next(
            item
            for item in data["nodes_body_changed"]
            if item["id"] == "lib.reminders.buildReminderMessage"
        )
        assert reminder["file_path"] == "lib/reminders.ts"
        assert reminder["lines"] == "13-16"
        # the per-file fingerprint table stays out of the report
        assert "files" not in data["baseline_meta"]
        assert "files" not in data["current_meta"]

    def test_no_change_report_mentions_files(self, app: Path) -> None:
        result = SnapshotDiff(_build(app), _build(app)).compute()
        assert "no source file changed" in format_diff_text(result)
        assert "no source file changed" in format_diff_markdown(result)

    def test_breaking_only_view_has_no_content_rows(self, diff: DiffResult) -> None:
        filtered = filter_breaking_only(diff)
        text = format_diff_text(filtered)
        assert filtered.nodes_body_changed == []
        assert "Bodies changed" not in text
        # both snapshots do have fingerprints, so no "not tracked" note either
        assert "not tracked" not in text


class TestCache:
    """A build that reuses cached files reports the same fingerprints."""

    def test_cached_build_matches_a_fresh_one(self, app: Path) -> None:
        first = GraphBuilder(Config.auto_detect(app), use_cache=True)
        fresh = first.build()
        second = GraphBuilder(Config.auto_detect(app), use_cache=True)
        cached = second.build()

        assert first.cache_stats.cached_files == 0
        assert second.cache_stats.cached_files == second.cache_stats.total_files > 0
        assert cached.metadata["files"] == fresh.metadata["files"]
        assert {n.id: n.metadata["body_hash"] for n in cached.nodes.values()} == {
            n.id: n.metadata["body_hash"] for n in fresh.nodes.values()
        }
        assert {n.id: n.line_end for n in cached.nodes.values()} == {
            n.id: n.line_end for n in fresh.nodes.values()
        }
        assert not SnapshotDiff(fresh, cached).compute().has_changes()

    def test_cached_build_sees_an_edit(self, app: Path) -> None:
        before = GraphBuilder(Config.auto_detect(app), use_cache=True).build()
        shutil.copytree(CHANGE, app, dirs_exist_ok=True)
        builder = GraphBuilder(Config.auto_detect(app), use_cache=True)
        after = builder.build()

        assert builder.cache_stats.cached_files > 0
        assert builder.cache_stats.parsed_files == 6
        result = SnapshotDiff(before, after).compute()
        assert "lib/reminders.ts" in [change.path for change in result.files_changed]


class TestLayerRulesOnTopLevelFolders:
    """A folder at the project root is classified like a nested one."""

    def test_python(self, tmp_path: Path) -> None:
        _write(tmp_path, "models/user.py", "class User:\n    pass\n")
        _write(tmp_path, "src/models/order.py", "class Order:\n    pass\n")
        graph = GraphBuilder(_python_project(tmp_path), use_cache=False).build()
        assert graph.nodes["models.user.User"].layer is LayerType.MODEL
        assert graph.nodes["src.models.order.Order"].layer is LayerType.MODEL

    def test_typescript(self, tmp_path: Path) -> None:
        page = "export default function Home() {\n  return null;\n}\n"
        _write(tmp_path, "pages/index.tsx", page)
        graph = _build(tmp_path)
        assert graph.nodes["pages.index.Home"].layer is LayerType.ROUTER


class TestCommandLine:
    """generate twice, then snapshot-diff — the path a skill would take."""

    def test_snapshot_diff_reports_the_unrequested_edit(
        self,
        app: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(app)
        assert main(["generate", "--label", "truoc"]) == 0
        shutil.copytree(CHANGE, app, dirs_exist_ok=True)
        assert main(["generate", "--label", "sau"]) == 0
        capsys.readouterr()

        code = main(
            ["snapshot-diff", "--baseline", "truoc", "--current", "sau"]
            + ["--format", "json"]
        )
        data = json.loads(capsys.readouterr().out)

        assert code == 0
        assert data["content_tracking"] is True
        assert "lib/reminders.ts" in [item["path"] for item in data["files_changed"]]
        assert "lib.reminders.buildReminderMessage" in [
            item["id"] for item in data["nodes_body_changed"]
        ]
