# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for VIBE-103: features, acceptance criteria and evidence.

The acceptance case is the sample app under tests/fixtures/so-dat-lich: the
owner asked for "customers can cancel a booking"; the change also edits the
reminder module. The feature layer has to say that Booking and Reminders
were touched, that the other three features were not, and which criteria
need to be checked again.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from codebase_map.cli import main
from codebase_map.config import Config, SourceConfig
from codebase_map.features import (
    STATUS_NEEDS_RECHECK,
    STATUS_UNCHECKED,
    STATUS_VERIFIED,
    FeatureMap,
    FeatureStore,
    FeatureStoreError,
    compute_impact,
    format_impact_text,
    format_status_text,
    pattern_matches,
    web_route,
)
from codebase_map.graph.builder import GraphBuilder
from codebase_map.graph.models import Graph

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "so-dat-lich"
BASE = FIXTURE / "base"
CHANGE = FIXTURE / "change-huy-lich"
FEATURES = FIXTURE / "features.json"

ALL_CRITERIA = [
    "dat-lich-1",
    "dat-lich-2",
    "dat-lich-3",
    "khach-hang-1",
    "khach-hang-2",
    "nhac-lich-1",
    "nhac-lich-2",
    "bao-cao-1",
    "dang-nhap-1",
]


def _build(root: Path) -> Graph:
    return GraphBuilder(Config.auto_detect(root), use_cache=False).build()


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _edit(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {rel}"
    path.write_text(text.replace(old, new), encoding="utf-8")


def _verify_everything(store: FeatureStore, graph: Graph) -> None:
    """Record evidence for every criterion against ``graph``."""
    feature_map = FeatureMap(store, graph)
    for feature in store.features:
        for criterion in feature.criteria:
            store.record_evidence(
                criterion.id,
                "manual",
                "Bấm thử",
                feature_map.scope(feature.id).fingerprint,
            )


def _statuses(store: FeatureStore, graph: Graph) -> dict[str, str]:
    feature_map = FeatureMap(store, graph)
    return {
        criterion.id: feature_map.status(feature.id, criterion)
        for feature in store.features
        for criterion in feature.criteria
    }


@pytest.fixture()
def app(tmp_path: Path) -> Path:
    root = tmp_path / "so-dat-lich"
    shutil.copytree(BASE, root)
    return root


@pytest.fixture()
def store() -> FeatureStore:
    return FeatureStore.load(FEATURES)


class TestPatterns:
    def test_exact_path_and_folder(self) -> None:
        assert pattern_matches("lib/slots.ts", "lib/slots.ts")
        assert pattern_matches("app/dat-lich", "app/dat-lich/page.tsx")
        assert pattern_matches("app/dat-lich/", "app/dat-lich/page.tsx")
        assert not pattern_matches("app/dat", "app/dat-lich/page.tsx")
        assert not pattern_matches("lib/slots.ts", "lib/slots.tsx")

    def test_wildcards(self) -> None:
        assert pattern_matches("components/Booking*", "components/BookingForm.tsx")
        assert pattern_matches("app/api/*/route.ts", "app/api/slots/route.ts")
        assert pattern_matches("*.test.ts", "lib/deep/slots.test.ts")
        assert not pattern_matches("components/Booking*", "components/SlotPicker.tsx")

    def test_square_brackets_are_literal(self) -> None:
        path = "app/api/bookings/[id]/route.ts"
        assert pattern_matches(path, path)
        assert pattern_matches("app/api/bookings/[id]", path)
        assert pattern_matches("app/api/*/[id]/route.ts", path)
        assert not pattern_matches(
            "app/api/bookings/[id]/route.ts", "app/api/bookings/i/route.ts"
        )

    def test_node_id(self) -> None:
        assert pattern_matches(
            "app.api.bookings.route.GET", "app.api.bookings.route.GET"
        )
        assert pattern_matches("lib.reports.*", "lib.reports.revenueByDay")


class TestWebRoute:
    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("app/page.tsx", ("screen", "/")),
            ("app/dat-lich/page.tsx", ("screen", "/dat-lich")),
            ("src/app/(shop)/dat-lich/page.tsx", ("screen", "/dat-lich")),
            ("app/@modal/login/page.tsx", ("screen", "/login")),
            ("app/api/bookings/route.ts", ("api", "/api/bookings")),
            ("app/api/bookings/[id]/route.ts", ("api", "/api/bookings/[id]")),
            ("pages/index.tsx", ("screen", "/")),
            ("pages/khach/[id].tsx", ("screen", "/khach/[id]")),
            ("src/pages/api/bookings.ts", ("api", "/api/bookings")),
            ("pages/_app.tsx", None),
            ("app/layout.tsx", None),
            ("components/BookingForm.tsx", None),
            ("lib/pages/helper.py", None),
        ],
    )
    def test_next_js_conventions(self, path: str, expected) -> None:
        assert web_route(path) == expected


class TestStore:
    def test_missing_file_is_an_empty_store(self, tmp_path: Path) -> None:
        assert FeatureStore.load(tmp_path / "nope.json").features == []

    def test_round_trip_keeps_everything(
        self, tmp_path: Path, store: FeatureStore
    ) -> None:
        store.record_evidence("dat-lich-1", "manual", "Anh Tỉnh bấm thử", "abc123")
        path = tmp_path / ".cbm" / "features.json"
        store.save(path)

        text = path.read_text(encoding="utf-8")
        assert "Đặt lịch" in text  # readable, not \\u escapes
        assert not (path.parent / "features.json.tmp").exists()
        reloaded = FeatureStore.load(path)
        assert reloaded.to_dict() == store.to_dict()
        evidence = reloaded.criterion("dat-lich-1")[1].evidence
        assert evidence is not None
        assert (evidence.kind, evidence.note, evidence.fingerprint) == (
            "manual",
            "Anh Tỉnh bấm thử",
            "abc123",
        )
        assert evidence.checked_at

    def test_add_feature_then_update_it(self) -> None:
        store = FeatureStore()
        store.upsert_feature("booking", "Booking", ["app/booking"])
        store.upsert_feature("booking", "Đặt lịch", ["app/dat-lich", "lib\\slots.ts"])
        assert len(store.features) == 1
        assert store.feature("booking").name == "Đặt lịch"
        assert store.feature("booking").files == ["app/dat-lich", "lib/slots.ts"]

    def test_criterion_ids_are_generated_and_unique(self) -> None:
        store = FeatureStore()
        store.upsert_feature("booking", "Booking", ["app"])
        first = store.add_criterion("booking", "One")
        second = store.add_criterion("booking", "Two")
        named = store.add_criterion("booking", "Three", "cancel-in-time")
        assert [first.id, second.id, named.id] == [
            "booking-1",
            "booking-2",
            "cancel-in-time",
        ]
        with pytest.raises(FeatureStoreError, match="already used"):
            store.add_criterion("booking", "Again", "booking-1")

    @pytest.mark.parametrize(
        ("data", "message"),
        [
            ([], "JSON object"),
            ({"version": 99, "features": []}, "newer"),
            ({"features": {}}, "must be a list"),
            (
                {"features": [{"id": "Bad Id", "name": "x", "files": ["a"]}]},
                "lowercase",
            ),
            ({"features": [{"id": "a", "name": "", "files": ["a"]}]}, "name"),
            ({"features": [{"id": "a", "name": "A", "files": []}]}, "file patterns"),
            ({"features": [{"id": "a", "name": "A"}]}, "file patterns"),
            (
                {
                    "features": [
                        {"id": "a", "name": "A", "files": ["x"]},
                        {"id": "a", "name": "B", "files": ["y"]},
                    ]
                },
                "used twice",
            ),
            (
                {
                    "features": [
                        {
                            "id": "a",
                            "name": "A",
                            "files": ["x"],
                            "criteria": [{"id": "a-1", "text": ""}],
                        }
                    ]
                },
                "text",
            ),
            (
                {
                    "features": [
                        {
                            "id": "a",
                            "name": "A",
                            "files": ["x"],
                            "criteria": [
                                {
                                    "id": "a-1",
                                    "text": "t",
                                    "evidence": {"kind": "vibes"},
                                }
                            ],
                        }
                    ]
                },
                "kind",
            ),
        ],
    )
    def test_invalid_store_is_rejected_with_a_reason(self, data, message: str) -> None:
        with pytest.raises(FeatureStoreError, match=message):
            FeatureStore.from_dict(data)

    def test_broken_json_is_reported(self, tmp_path: Path) -> None:
        path = tmp_path / "features.json"
        path.write_text("{ not json", encoding="utf-8")
        with pytest.raises(FeatureStoreError, match="Cannot read"):
            FeatureStore.load(path)

    def test_unknown_ids_and_kinds(self, store: FeatureStore) -> None:
        with pytest.raises(FeatureStoreError, match="No feature"):
            store.add_criterion("nope", "text")
        with pytest.raises(FeatureStoreError, match="No criterion"):
            store.record_evidence("nope-1", "manual", "", "f")
        with pytest.raises(FeatureStoreError, match="one of"):
            store.record_evidence("dat-lich-1", "guess", "", "f")


class TestFeatureScope:
    def test_owned_files_follow_the_patterns(
        self, app: Path, store: FeatureStore
    ) -> None:
        scopes = FeatureMap(store, _build(app)).scopes
        assert scopes["nhac-lich"].owned_files == [
            "app/api/reminders/route.ts",
            "lib/reminders.ts",
        ]
        assert "app/lich-cua-toi/page.tsx" in scopes["dat-lich"].owned_files
        assert "lib/slots.ts" in scopes["dat-lich"].owned_files
        assert "lib.reminders.dueReminders" in scopes["nhac-lich"].owned_nodes

    def test_reached_code_is_what_the_feature_calls(
        self, app: Path, store: FeatureStore
    ) -> None:
        scope = FeatureMap(store, _build(app)).scope("nhac-lich")
        # Reminders read the upcoming bookings and the customer, through the db
        assert scope.reached_nodes == [
            "lib.bookings.listUpcomingBookings",
            "lib.customers.findCustomer",
            "lib.db.readAll",
        ]
        # ...and run with the top-level code of those files and what they import
        assert scope.context_files == [
            "lib/bookings.ts",
            "lib/customers.ts",
            "lib/db.ts",
            "lib/slots.ts",
        ]

    def test_files_in_no_feature(self, app: Path, store: FeatureStore) -> None:
        feature_map = FeatureMap(store, _build(app))
        assert feature_map.unowned_files == [
            "app/layout.tsx",
            "app/page.tsx",
            "lib/db.ts",
            "lib/types.ts",
        ]
        assert feature_map.users_of_file("lib/db.ts") == [
            "dat-lich",
            "khach-hang",
            "nhac-lich",
            "bao-cao",
        ]
        # only types are imported from it, so nothing depends on it at runtime
        assert feature_map.users_of_file("lib/types.ts") == []

    def test_a_file_can_belong_to_two_features(self, app: Path) -> None:
        store = FeatureStore()
        store.upsert_feature(
            "booking", "Booking", ["app/api/bookings", "lib/bookings.ts"]
        )
        store.upsert_feature(
            "my-bookings", "My bookings", ["app.api.bookings.route.GET"]
        )
        feature_map = FeatureMap(store, _build(app))

        assert feature_map.scope("my-bookings").owned_nodes == [
            "app.api.bookings.route.GET"
        ]
        assert feature_map.scope("my-bookings").owned_files == []
        assert (
            "app/api/bookings/route.ts"
            in feature_map.scope("my-bookings").context_files
        )
        assert "app.api.bookings.route.GET" in feature_map.scope("booking").owned_nodes

    def test_unknown_feature(self, app: Path, store: FeatureStore) -> None:
        with pytest.raises(FeatureStoreError, match="No feature"):
            FeatureMap(store, _build(app)).scope("nope")

    def test_graph_without_fingerprints_is_refused(
        self, app: Path, store: FeatureStore
    ) -> None:
        graph = _build(app)
        graph.metadata.pop("files")
        with pytest.raises(FeatureStoreError, match="generate"):
            FeatureMap(store, graph)


class TestApplicationMap:
    def test_screens_and_endpoints(self, app: Path, store: FeatureStore) -> None:
        data = FeatureMap(store, _build(app)).to_dict()
        booking = data["features"][0]

        assert booking["id"] == "dat-lich"
        assert [(s["url"], s["path"]) for s in booking["screens"]] == [
            ("/dat-lich", "app/dat-lich/page.tsx"),
            ("/lich-cua-toi", "app/lich-cua-toi/page.tsx"),
        ]
        assert [(a["url"], a["methods"]) for a in booking["apis"]] == [
            ("/api/bookings", ["GET", "POST"]),
            ("/api/slots", ["GET"]),
        ]
        assert booking["functions"]["owned"] > 0
        assert "lib/db.ts" in booking["files"]["shared"]

    def test_counts(self, app: Path, store: FeatureStore) -> None:
        graph = _build(app)
        store.record_evidence(
            "dat-lich-1",
            "test",
            "pytest",
            FeatureMap(store, graph).scope("dat-lich").fingerprint,
        )
        data = FeatureMap(store, graph).to_dict()

        assert data["features"][0]["counts"] == {
            STATUS_VERIFIED: 1,
            STATUS_NEEDS_RECHECK: 0,
            STATUS_UNCHECKED: 2,
        }
        assert data["summary"] == {
            "features": 5,
            "criteria": {
                STATUS_VERIFIED: 1,
                STATUS_NEEDS_RECHECK: 0,
                STATUS_UNCHECKED: 8,
            },
            "unowned_files": 4,
        }
        unowned = {item["path"]: item for item in data["unowned_files"]}
        assert unowned["app/page.tsx"]["kind"] == "screen"
        assert unowned["app/page.tsx"]["url"] == "/"
        assert unowned["lib/db.ts"]["used_by"] == [
            "dat-lich",
            "khach-hang",
            "nhac-lich",
            "bao-cao",
        ]

    def test_text_form(self, app: Path, store: FeatureStore) -> None:
        text = format_status_text(FeatureMap(store, _build(app)).to_dict())
        assert "Đặt lịch  [dat-lich]" in text
        assert "screen  /dat-lich  (app/dat-lich/page.tsx)" in text
        assert "api     GET POST /api/bookings" in text
        assert "[unchecked] nhac-lich-1" in text
        assert "lib/db.ts  (used by: dat-lich, khach-hang, nhac-lich, bao-cao)" in text

    def test_empty_store(self, app: Path) -> None:
        data = FeatureMap(FeatureStore(), _build(app)).to_dict()
        assert data["features"] == []
        assert data["summary"]["unowned_files"] == 26
        assert "No features defined yet" in format_status_text(data)


class TestEvidenceExpires:
    """Evidence holds until code the feature owns or reaches changes."""

    def test_three_states(self, app: Path, store: FeatureStore) -> None:
        graph = _build(app)
        assert set(_statuses(store, graph).values()) == {STATUS_UNCHECKED}

        _verify_everything(store, graph)
        assert set(_statuses(store, graph).values()) == {STATUS_VERIFIED}

        _edit(
            app, "lib/reports.ts", 'readAll("bookings")', 'readAll("bookings").slice()'
        )
        statuses = _statuses(store, _build(app))
        assert statuses["bao-cao-1"] == STATUS_NEEDS_RECHECK
        del statuses["bao-cao-1"]
        assert set(statuses.values()) == {STATUS_VERIFIED}

    def test_same_code_elsewhere_keeps_the_evidence(
        self, app: Path, tmp_path: Path, store: FeatureStore
    ) -> None:
        _verify_everything(store, _build(app))
        elsewhere = tmp_path / "another" / "place"
        shutil.copytree(app, elsewhere)
        assert set(_statuses(store, _build(elsewhere)).values()) == {STATUS_VERIFIED}

    def test_reformatting_keeps_the_evidence(
        self, app: Path, store: FeatureStore
    ) -> None:
        _verify_everything(store, _build(app))
        path = app / "lib" / "bookings.ts"
        path.write_text(
            path.read_text(encoding="utf-8").replace("  ", "      "), encoding="utf-8"
        )
        assert set(_statuses(store, _build(app)).values()) == {STATUS_VERIFIED}

    def test_type_only_and_import_only_edits_keep_the_evidence(
        self, app: Path, store: FeatureStore
    ) -> None:
        _verify_everything(store, _build(app))
        _edit(
            app, "lib/types.ts", '"booked" | "done"', '"booked" | "done" | "cancelled"'
        )
        _edit(
            app,
            "lib/bookings.ts",
            'import { isSlotFree, takeSlot } from "@/lib/slots";',
            'import { isSlotFree, listSlots, takeSlot } from "@/lib/slots";',
        )
        assert set(_statuses(store, _build(app)).values()) == {STATUS_VERIFIED}

    def test_edit_in_shared_code_expires_every_feature_that_uses_it(
        self, app: Path, store: FeatureStore
    ) -> None:
        _verify_everything(store, _build(app))
        _edit(app, "lib/db.ts", "export function readAll", "export function  readAll")
        assert set(_statuses(store, _build(app)).values()) == {STATUS_VERIFIED}

        _edit(
            app, "lib/db.ts", "return tables[table];", "return tables[table].slice();"
        )
        statuses = _statuses(store, _build(app))

        # every feature that reads data goes stale; login does not use the db
        assert statuses["dang-nhap-1"] == STATUS_VERIFIED
        del statuses["dang-nhap-1"]
        assert set(statuses.values()) == {STATUS_NEEDS_RECHECK}

    def test_constant_in_an_imported_file_counts(
        self, app: Path, store: FeatureStore
    ) -> None:
        """Opening hours live outside any function, in a file Booking owns."""
        _verify_everything(store, _build(app))
        _edit(app, "lib/slots.ts", "const OPEN_HOUR = 9;", "const OPEN_HOUR = 8;")
        statuses = _statuses(store, _build(app))

        assert statuses["dat-lich-1"] == STATUS_NEEDS_RECHECK
        # Reminders reach lib/bookings.ts, which imports lib/slots.ts
        assert statuses["nhac-lich-1"] == STATUS_NEEDS_RECHECK
        assert statuses["khach-hang-1"] == STATUS_VERIFIED
        assert statuses["bao-cao-1"] == STATUS_VERIFIED

    def test_new_evidence_replaces_the_old(
        self, app: Path, store: FeatureStore
    ) -> None:
        _verify_everything(store, _build(app))
        _edit(app, "lib/auth.ts", "token !== null &&", "!!token &&")
        graph = _build(app)
        assert _statuses(store, graph)["dang-nhap-1"] == STATUS_NEEDS_RECHECK

        store.record_evidence(
            "dang-nhap-1",
            "manual",
            "Thử lại",
            FeatureMap(store, graph).scope("dang-nhap").fingerprint,
        )
        assert _statuses(store, graph)["dang-nhap-1"] == STATUS_VERIFIED


class TestImpactOfTheSampleChange:
    """The acceptance case of VIBE-103."""

    @pytest.fixture()
    def impact(self, app: Path, store: FeatureStore) -> dict:
        before = _build(app)
        _verify_everything(store, before)
        shutil.copytree(CHANGE, app, dirs_exist_ok=True)
        return compute_impact(store, before, _build(app))

    def test_booking_and_reminders_are_touched(self, impact: dict) -> None:
        assert impact["summary"]["touched_direct"] == ["dat-lich", "nhac-lich"]
        assert impact["summary"]["touched_indirect"] == []
        touched = {f["id"]: f["touched"] for f in impact["features"]}
        assert touched == {
            "dat-lich": "direct",
            "khach-hang": "none",
            "nhac-lich": "direct",
            "bao-cao": "none",
            "dang-nhap": "none",
        }

    def test_criteria_to_check_again(self, impact: dict) -> None:
        after = {
            criterion["id"]: criterion["status_after"]
            for feature in impact["features"]
            for criterion in feature["criteria"]
        }
        stale = sorted(
            cid for cid, status in after.items() if status == STATUS_NEEDS_RECHECK
        )
        assert stale == [
            "dat-lich-1",
            "dat-lich-2",
            "dat-lich-3",
            "nhac-lich-1",
            "nhac-lich-2",
        ]
        assert impact["summary"]["criteria_to_recheck"] == 5
        before = {
            criterion["id"]: criterion["status_before"]
            for feature in impact["features"]
            for criterion in feature["criteria"]
        }
        assert set(before.values()) == {STATUS_VERIFIED}
        assert sorted(before) == sorted(ALL_CRITERIA)

    def test_what_was_edited_in_reminders(self, impact: dict) -> None:
        reminders = next(f for f in impact["features"] if f["id"] == "nhac-lich")
        assert reminders["behaviour_changed"] is True
        assert reminders["direct"]["files"] == [
            {"path": "lib/reminders.ts", "change": "modified"}
        ]
        assert reminders["direct"]["functions"] == [
            {
                "id": "lib.reminders.buildReminderMessage",
                "name": "buildReminderMessage",
                "file": "lib/reminders.ts",
                "change": "body",
            }
        ]
        # it also depends on a file of Booking whose top-level code changed
        assert reminders["indirect"]["files"] == [
            {"path": "lib/bookings.ts", "change": "modified", "owners": ["dat-lich"]}
        ]

    def test_what_was_edited_in_booking(self, impact: dict) -> None:
        booking = next(f for f in impact["features"] if f["id"] == "dat-lich")
        assert [item["path"] for item in booking["direct"]["files"]] == [
            "app/api/bookings/[id]/route.ts",
            "components/BookingList.tsx",
            "lib/bookings.ts",
            "lib/slots.ts",
        ]
        added = {
            item["id"]
            for item in booking["direct"]["functions"]
            if item["change"] == "added"
        }
        assert {
            "lib.bookings.cancelBooking",
            "lib.bookings.canCancel",
            "lib.slots.releaseSlot",
            "app.api.bookings.[id].route.DELETE",
        } <= added

    def test_change_outside_every_feature_is_listed(self, impact: dict) -> None:
        assert impact["unowned_changes"] == [
            {
                "path": "lib/types.ts",
                "change": "modified",
                "module_level_changed": False,
                "used_by": [],
            }
        ]

    def test_text_form(self, impact: dict) -> None:
        text = format_impact_text(impact)
        assert "Đặt lịch  [dat-lich]  direct" in text
        assert "Nhắc lịch  [nhac-lich]  direct" in text
        assert "edited   buildReminderMessage  (body, lib/reminders.ts)" in text
        assert "recheck  nhac-lich-1" in text
        assert "Not touched: Danh sách khách, Báo cáo doanh thu, Đăng nhập" in text
        assert "Changed, in no feature: lib/types.ts" in text
        assert "Criteria to recheck: 5" in text


class TestImpactRules:
    def test_no_change(self, app: Path, store: FeatureStore) -> None:
        graph = _build(app)
        impact = compute_impact(store, graph, _build(app))
        assert impact["summary"] == {
            "files_changed": 0,
            "touched_direct": [],
            "touched_indirect": [],
            "criteria_to_recheck": 0,
        }
        assert all(not f["behaviour_changed"] for f in impact["features"])

    def test_requested_change_alone_still_reaches_reminders(
        self, app: Path, store: FeatureStore
    ) -> None:
        """Without the unrequested edit, Reminders is only touched indirectly."""
        before = _build(app)
        _verify_everything(store, before)
        untouched = (app / "lib" / "reminders.ts").read_text(encoding="utf-8")
        shutil.copytree(CHANGE, app, dirs_exist_ok=True)
        (app / "lib" / "reminders.ts").write_text(untouched, encoding="utf-8")
        impact = compute_impact(store, before, _build(app))

        assert impact["summary"]["touched_direct"] == ["dat-lich"]
        # lib/bookings.ts gained a constant; Reminders call into that file
        assert impact["summary"]["touched_indirect"] == ["nhac-lich"]
        reminders = next(f for f in impact["features"] if f["id"] == "nhac-lich")
        assert reminders["direct"] == {"files": [], "functions": []}
        assert [item["path"] for item in reminders["indirect"]["files"]] == [
            "lib/bookings.ts"
        ]

    def test_edit_inside_a_reached_function_is_indirect(
        self, app: Path, store: FeatureStore
    ) -> None:
        before = _build(app)
        _edit(
            app,
            "lib/customers.ts",
            "find((c) => c.id === id)",
            "find((c) => c.id == id)",
        )
        impact = compute_impact(store, before, _build(app))

        assert impact["summary"]["touched_direct"] == ["khach-hang"]
        assert impact["summary"]["touched_indirect"] == ["nhac-lich"]
        reminders = next(f for f in impact["features"] if f["id"] == "nhac-lich")
        assert reminders["indirect"]["functions"] == [
            {
                "id": "lib.customers.findCustomer",
                "name": "findCustomer",
                "file": "lib/customers.ts",
                "change": "body",
                "owners": ["khach-hang"],
            }
        ]

    def test_edit_that_cannot_change_behaviour(
        self, app: Path, store: FeatureStore
    ) -> None:
        before = _build(app)
        _verify_everything(store, before)
        path = app / "lib" / "auth.ts"
        path.write_text(path.read_text(encoding="utf-8").replace("  ", "    "), "utf-8")
        impact = compute_impact(store, before, _build(app))

        login = next(f for f in impact["features"] if f["id"] == "dang-nhap")
        assert login["touched"] == "direct"
        assert login["behaviour_changed"] is False
        assert login["criteria"][0]["status_after"] == STATUS_VERIFIED
        assert "(no behaviour change)" in format_impact_text(impact)


class TestReExports:
    """A call through an index file that re-exports reaches the real function."""

    def _project(self, root: Path) -> None:
        _write(
            root,
            "lib/bookings.ts",
            "export function createBooking() {\n  return 1;\n}\n",
        )
        _write(
            root,
            "lib/slots.ts",
            "const OPEN = 9;\nexport function isFree() {\n  return OPEN;\n}\n"
            "export default function listSlots() {\n  return [];\n}\n",
        )
        _write(
            root,
            "lib/index.ts",
            'export * from "./bookings";\n'
            'export { isFree as isSlotFree, default as listSlots } from "./slots";\n'
            'export type { Slot } from "./types";\n',
        )
        _write(root, "lib/types.ts", "export type Slot = { at: string };\n")
        _write(
            root,
            "app/page.tsx",
            'import { createBooking, isSlotFree, listSlots } from "@/lib";\n'
            "export default function Page() {\n"
            "  listSlots();\n"
            "  return isSlotFree() ? createBooking() : null;\n"
            "}\n",
        )

    def test_calls_resolve_through_the_index_file(self, tmp_path: Path) -> None:
        self._project(tmp_path)
        graph = _build(tmp_path)
        targets = {e.target for e in graph.edges if e.source == "app.page.Page"}
        assert {
            "lib.bookings.createBooking",
            "lib.slots.isFree",
            "lib.slots.listSlots",
        } <= targets

    def test_file_imports_pass_through_the_index_file(self, tmp_path: Path) -> None:
        self._project(tmp_path)
        files = _build(tmp_path).metadata["files"]
        assert files["app/page.tsx"]["imports"] == ["lib/index.ts"]
        # the type-only re-export is not a runtime dependency
        assert files["lib/index.ts"]["imports"] == ["lib/bookings.ts", "lib/slots.ts"]

    def test_feature_reaches_the_code_behind_the_index_file(
        self, tmp_path: Path
    ) -> None:
        self._project(tmp_path)
        store = FeatureStore()
        store.upsert_feature("home", "Home", ["app"])
        store.add_criterion("home", "Opens")
        before = _build(tmp_path)
        _verify_everything(store, before)

        _edit(tmp_path, "lib/slots.ts", "const OPEN = 9;", "const OPEN = 10;")
        assert _statuses(store, _build(tmp_path)) == {"home-1": STATUS_NEEDS_RECHECK}


class TestPythonProject:
    def _project(self, root: Path) -> Config:
        _write(root, "shop/__init__.py", "")
        _write(root, "shop/settings.py", "TAX = 10\n")
        _write(
            root,
            "shop/pricing.py",
            "from shop.settings import TAX\n\n\n"
            "def price(amount):\n    return amount + TAX\n",
        )
        _write(
            root,
            "shop/api.py",
            "from .pricing import price\n\n\n"
            "def quote(amount):\n    return price(amount)\n",
        )
        _write(root, "shop/other.py", "def unrelated():\n    return 0\n")
        return Config(
            project="shop",
            sources=[SourceConfig(path=".", language="python")],
            project_root=root,
        )

    def test_file_imports_are_resolved(self, tmp_path: Path) -> None:
        config = self._project(tmp_path)
        files = GraphBuilder(config, use_cache=False).build().metadata["files"]
        assert files["shop/pricing.py"]["imports"] == ["shop/settings.py"]
        assert files["shop/api.py"]["imports"] == ["shop/pricing.py"]  # relative
        assert "imports" not in files["shop/other.py"]

    def test_constant_in_another_module_expires_the_evidence(
        self, tmp_path: Path
    ) -> None:
        config = self._project(tmp_path)
        store = FeatureStore()
        store.upsert_feature("quotes", "Quotes", ["shop/api.py"])
        store.upsert_feature("other", "Other", ["shop/other.py"])
        store.add_criterion("quotes", "A quote includes tax")
        store.add_criterion("other", "Still works")
        before = GraphBuilder(config, use_cache=False).build()
        _verify_everything(store, before)

        scope = FeatureMap(store, before).scope("quotes")
        assert scope.reached_nodes == ["shop.pricing.price"]
        assert scope.context_files == ["shop/pricing.py", "shop/settings.py"]

        _write(tmp_path, "shop/settings.py", "TAX = 8\n")
        after = GraphBuilder(config, use_cache=False).build()
        assert _statuses(store, after) == {
            "quotes-1": STATUS_NEEDS_RECHECK,
            "other-1": STATUS_VERIFIED,
        }
        impact = compute_impact(store, before, after)
        assert impact["summary"]["touched_indirect"] == ["quotes"]
        assert impact["unowned_changes"][0]["used_by"] == ["quotes"]

    def test_python_import_statements_are_not_runtime_code(
        self, tmp_path: Path
    ) -> None:
        config = self._project(tmp_path)
        before = GraphBuilder(config, use_cache=False).build().metadata["files"]
        _write(
            tmp_path,
            "shop/pricing.py",
            "import os\nfrom shop.settings import TAX\n\n\ndef price(amount):\n"
            "    return amount + TAX\n",
        )
        after = GraphBuilder(config, use_cache=False).build().metadata["files"]
        assert before["shop/pricing.py"]["hash"] != after["shop/pricing.py"]["hash"]
        assert (
            before["shop/pricing.py"]["module_hash"]
            == after["shop/pricing.py"]["module_hash"]
        )


class TestCommandLine:
    """The commands a skill runs, in the order it runs them."""

    @pytest.fixture()
    def in_app(self, app: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
        monkeypatch.chdir(app)
        return app

    @staticmethod
    def _json(capsys: pytest.CaptureFixture[str], argv: list[str]) -> tuple[int, dict]:
        capsys.readouterr()
        code = main(argv)
        return code, json.loads(capsys.readouterr().out)

    def test_define_check_change_report(
        self, in_app: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        code, feature = self._json(
            capsys,
            ["features", "add", "--id", "nhac-lich", "--name", "Nhắc lịch", "--json"]
            + ["--files", "app/api/reminders", "lib/reminders.ts", "lib/typo.ts"],
        )
        assert code == 0
        assert feature["matched_files"] == [
            "app/api/reminders/route.ts",
            "lib/reminders.ts",
        ]
        assert feature["unmatched_patterns"] == ["lib/typo.ts"]

        code, criterion = self._json(
            capsys,
            ["features", "criterion", "--feature", "nhac-lich", "--json"]
            + ["--text", "Khách nhận tin nhắc trước giờ hẹn 24 tiếng."],
        )
        assert (code, criterion["id"], criterion["evidence"]) == (
            0,
            "nhac-lich-1",
            None,
        )

        code, checked = self._json(
            capsys,
            ["features", "evidence", "--criterion", "nhac-lich-1", "--json"]
            + ["--kind", "manual", "--note", "Chủ tiệm tự thử"],
        )
        assert code == 0
        assert checked["evidence"]["note"] == "Chủ tiệm tự thử"

        code, status = self._json(capsys, ["features", "status", "--json"])
        assert code == 0
        assert status["store"] == ".cbm/features.json"
        assert status["features"][0]["criteria"][0]["status"] == STATUS_VERIFIED
        assert (in_app / ".cbm" / "features.json").exists()

        assert main(["generate", "--label", "truoc"]) == 0
        shutil.copytree(CHANGE, in_app, dirs_exist_ok=True)
        assert main(["generate", "--label", "sau"]) == 0

        code, impact = self._json(
            capsys,
            ["features", "impact", "--baseline", "truoc", "--current", "sau", "--json"],
        )
        assert code == 0
        assert impact["summary"]["touched_direct"] == ["nhac-lich"]
        assert (
            impact["features"][0]["criteria"][0]["status_after"] == STATUS_NEEDS_RECHECK
        )
        assert impact["baseline"] == "truoc"

        code, status = self._json(capsys, ["features", "status", "--json"])
        assert status["features"][0]["criteria"][0]["status"] == STATUS_NEEDS_RECHECK

    def test_json_output_is_only_json(
        self, in_app: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The auto-detect notice must not end up in front of the JSON."""
        capsys.readouterr()
        assert main(["features", "status", "--json"]) == 0
        captured = capsys.readouterr()
        assert captured.out.lstrip().startswith("{")
        assert "[AUTO]" in captured.err

    def test_text_output(
        self, in_app: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        shutil.copytree(
            FEATURES.parent,
            in_app / ".cbm",
            ignore=lambda *_: ["base", "change-huy-lich"],
        )
        capsys.readouterr()
        assert main(["features", "status"]) == 0
        assert "Nhắc lịch  [nhac-lich]" in capsys.readouterr().out

    def test_errors_exit_with_one(
        self, in_app: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert main(["features"]) == 1
        assert main(["features", "criterion", "--feature", "nope", "--text", "x"]) == 1
        assert "No feature" in capsys.readouterr().out

        code, error = self._json(
            capsys,
            ["features", "impact", "--baseline", "a", "--current", "b", "--json"],
        )
        assert code == 1
        assert "Snapshot not found" in error["error"]

        code, error = self._json(
            capsys,
            [
                "features",
                "add",
                "--id",
                "Bad Id",
                "--name",
                "x",
                "--files",
                "a",
                "--json",
            ],
        )
        assert code == 1
        assert "lowercase" in error["error"]

    def test_custom_store_path(
        self, in_app: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        store_path = in_app / "elsewhere.json"
        shutil.copy(FEATURES, store_path)
        code, status = self._json(
            capsys, ["features", "status", "--json", "--store", str(store_path)]
        )
        assert code == 0
        assert status["summary"]["features"] == 5
        assert not (in_app / ".cbm").exists()

    def test_folder_without_source_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        assert main(["features", "status"]) == 1
