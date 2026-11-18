# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Regression tests for the independent review of CBM-VIBE tier 1 (16/11/2026).

Each case below was reproduced by the reviewer as *false reassurance*: an edit
that can change behaviour, after which a feature that depends on the edited
code still showed its evidence as verified. The fixture for most of them is
the same: one feature owns one file, its criterion is verified, something the
file depends on is edited, and the criterion must now need a recheck.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from codebase_map.config import Config, SourceConfig
from codebase_map.features import (
    STATUS_NEEDS_RECHECK,
    STATUS_VERIFIED,
    FeatureMap,
    FeatureStore,
    FeatureStoreError,
    compute_impact,
    pattern_matches,
    web_route,
)
from codebase_map.graph.builder import GraphBuilder
from codebase_map.graph.diff_formatter import format_diff_text
from codebase_map.graph.models import EdgeType, Graph
from codebase_map.graph.snapshot_diff import SnapshotDiff
from codebase_map.parsers.typescript_parser import TypeScriptParser, _CodeLines

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "so-dat-lich"


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _edit(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {rel}"
    path.write_text(text.replace(old, new), encoding="utf-8")


def _build(root: Path) -> Graph:
    return GraphBuilder(Config.auto_detect(root), use_cache=False).build()


def _status_after_edit(root: Path, owned: list[str], edit) -> str:
    """Verify a feature that owns ``owned``, apply ``edit``, return the status."""
    store = FeatureStore()
    store.upsert_feature("f", "Feature", owned)
    store.add_criterion("f", "Works")
    before = _build(root)
    fingerprint = FeatureMap(store, before).scope("f").fingerprint
    store.record_evidence("f-1", "manual", "", fingerprint)
    assert FeatureMap(store, before).status("f", store.feature("f").criteria[0]) == (
        STATUS_VERIFIED
    )
    edit()
    after = _build(root)
    return FeatureMap(store, after).status("f", store.feature("f").criteria[0])


def _parse(tmp_path: Path, source: str, rel: str = "lib/sample.ts"):
    path = tmp_path / Path(rel).name
    path.write_text(source, encoding="utf-8")
    nodes, edges = TypeScriptParser().parse_file(path, "", Path(rel))
    return {node.name: node for node in nodes}, edges


def _targets(edges, source_suffix: str) -> set[str]:
    return {
        edge.target
        for edge in edges
        if edge.edge_type is EdgeType.CALLS and edge.source.endswith(source_suffix)
    }


class TestFinding1ComponentWithPropsOnTheNextLines:
    def test_usage_is_an_edge(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "components/BookingForm.tsx",
            "export default function BookingForm() {\n  const max = 3;\n"
            "  return <form>{max}</form>;\n}\n",
        )
        _write(
            tmp_path,
            "app/page.tsx",
            'import BookingForm from "@/components/BookingForm";\n'
            "export default function Page() {\n  return (\n    <main>\n"
            '      <BookingForm\n        title="Đặt lịch"\n        showNote\n'
            "      />\n    </main>\n  );\n}\n",
        )
        status = _status_after_edit(
            tmp_path,
            ["app/page.tsx"],
            lambda: _edit(
                tmp_path, "components/BookingForm.tsx", "max = 3", "max = 30"
            ),
        )
        assert status == STATUS_NEEDS_RECHECK


class TestFinding2ProjectLayouts:
    def test_app_in_a_subfolder_resolves_like_one_at_the_root(
        self, tmp_path: Path
    ) -> None:
        shutil.copytree(FIXTURE / "base", tmp_path / "web")
        graph = _build(tmp_path)
        files = graph.metadata["files"]
        assert files["web/lib/bookings.ts"]["imports"] == [
            "web/lib/db.ts",
            "web/lib/slots.ts",
        ]
        calls = {(e.source, e.target) for e in graph.edges}
        assert (
            "web.lib.bookings.createBooking",
            "web.lib.slots.isSlotFree",
        ) in calls
        assert web_route("web/app/dat-lich/page.tsx") == ("screen", "/dat-lich")
        assert web_route("apps/web/src/app/api/x/route.ts") == ("api", "/api/x")

    def test_shared_code_edit_reaches_the_features_in_a_subfolder(
        self, tmp_path: Path
    ) -> None:
        shutil.copytree(FIXTURE / "base", tmp_path / "web")
        status = _status_after_edit(
            tmp_path,
            ["web/app/api/bookings", "web/lib/bookings.ts"],
            lambda: _edit(tmp_path, "web/lib/db.ts", ".push(row)", ".unshift(row)"),
        )
        assert status == STATUS_NEEDS_RECHECK

    def test_alias_from_tsconfig_paths(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "tsconfig.json",
            '{\n  // aliases\n  "compilerOptions": {\n    "baseUrl": ".",\n'
            '    "paths": { "@lib/*": ["source/lib/*"], },\n  },\n}\n',
        )
        _write(tmp_path, "source/lib/db.ts", "export function insertRow() {\n}\n")
        _write(
            tmp_path,
            "source/app.ts",
            'import { insertRow } from "@lib/db";\n'
            "export function save() {\n  insertRow();\n}\n",
        )
        graph = _build(tmp_path)
        assert graph.metadata["files"]["source/app.ts"]["imports"] == [
            "source/lib/db.ts"
        ]
        assert ("source.app.save", "source.lib.db.insertRow") in {
            (e.source, e.target) for e in graph.edges
        }

    def test_python_package_below_a_subfolder(self, tmp_path: Path) -> None:
        _write(tmp_path, "backend/app/__init__.py", "")
        _write(
            tmp_path,
            "backend/app/services.py",
            "def create_booking(data):\n    return dict(data)\n",
        )
        _write(
            tmp_path,
            "backend/app/routes.py",
            "from app.services import create_booking\n\n\n"
            "def post_booking(data):\n    return create_booking(data)\n",
        )
        config = Config(
            project="p",
            sources=[SourceConfig(path=".", language="python")],
            project_root=tmp_path,
        )
        graph = GraphBuilder(config, use_cache=False).build()
        assert (
            "backend.app.routes.post_booking",
            "backend.app.services.create_booking",
        ) in {(e.source, e.target) for e in graph.edges}


class TestFinding4CallsOutsideFunctions:
    def _auth_project(self, root: Path) -> None:
        _write(
            root,
            "lib/auth.ts",
            "export function withAuth(handler: Handler) {\n"
            "  return async (req: Request) => {\n"
            "    if (!req.headers.get('x-token')) {\n      throw new Error('no');\n"
            "    }\n    return handler(req);\n  };\n}\n",
        )
        _write(
            root,
            "lib/bookings.ts",
            "export function createBooking(data: unknown) {\n"
            "  if (!data) {\n    throw new Error('empty');\n  }\n  return data;\n}\n",
        )

    def test_wrapped_route_handler(self, tmp_path: Path) -> None:
        self._auth_project(tmp_path)
        _write(
            tmp_path,
            "app/api/bookings/route.ts",
            'import { withAuth } from "@/lib/auth";\n'
            'import { createBooking } from "@/lib/bookings";\n\n'
            "export const POST = withAuth(async (req: Request) => {\n"
            "  return Response.json(createBooking(await req.json()));\n});\n",
        )
        graph = _build(tmp_path)
        assert graph.metadata["files"]["app/api/bookings/route.ts"]["calls"] == [
            "lib.auth.withAuth",
            "lib.bookings.createBooking",
        ]
        # the edge list still holds only edges that start at a node
        assert all(
            edge.source in graph.nodes
            for edge in graph.edges
            if edge.edge_type is EdgeType.CALLS
        )
        for rel, old in (("lib/auth.ts", "!req.headers"), ("lib/bookings.ts", "!data")):
            status = _status_after_edit(
                tmp_path,
                ["app/api/bookings"],
                lambda rel=rel, old=old: _edit(tmp_path, rel, old, "false"),
            )
            assert status == STATUS_NEEDS_RECHECK, rel

    def test_express_inline_handler_and_initialiser(self, tmp_path: Path) -> None:
        self._auth_project(tmp_path)
        _write(
            tmp_path,
            "server.js",
            'const { createBooking } = require("./lib/bookings");\n'
            "const app = makeApp();\n"
            'app.post("/api/bookings", async (req, res) => {\n'
            "  res.json(createBooking(req.body));\n});\n",
        )
        status = _status_after_edit(
            tmp_path,
            ["server.js"],
            lambda: _edit(tmp_path, "lib/bookings.ts", "!data", "false"),
        )
        assert status == STATUS_NEEDS_RECHECK

    def test_class_field_and_decorator(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "lib/repo.ts",
            "export function createRepo() {\n  return new Map();\n}\n"
            "export function Roles(role: string) {\n  return role;\n}\n",
        )
        nodes, edges = _parse(
            tmp_path,
            'import { createRepo, Roles } from "./repo";\n'
            "export class BookingService {\n"
            "  repo = createRepo();\n\n"
            '  @Roles("admin")\n'
            "  remove(id: string) {\n    return this.repo.delete(id);\n  }\n}\n",
            "lib/service.ts",
        )
        assert "createRepo" in _targets(edges, ".BookingService")
        assert "Roles" in _targets(edges, ".BookingService.remove")

    def test_python_top_level_call_and_decorator(self, tmp_path: Path) -> None:
        _write(tmp_path, "shop/__init__.py", "")
        _write(
            tmp_path,
            "shop/seed.py",
            "def seed():\n    return [1]\n\n\ndef admin_only(fn):\n    return fn\n",
        )
        _write(
            tmp_path,
            "shop/items.py",
            "from shop.seed import admin_only, seed\n\nITEMS = seed()\n\n\n"
            "@admin_only\ndef remove(item):\n    ITEMS.remove(item)\n",
        )
        config = Config(
            project="p",
            sources=[SourceConfig(path=".", language="python")],
            project_root=tmp_path,
        )
        graph = GraphBuilder(config, use_cache=False).build()
        assert graph.metadata["files"]["shop/items.py"]["calls"] == ["shop.seed.seed"]
        assert ("shop.items.remove", "shop.seed.admin_only") in {
            (e.source, e.target) for e in graph.edges
        }


class TestFinding5CallSyntax:
    def test_type_arguments_and_optional_call(self, tmp_path: Path) -> None:
        _, edges = _parse(
            tmp_path,
            "export function listBookings() {\n"
            '  const cache = new Cache<string>();\n  track?.("list");\n'
            '  return getJson<Booking[]>("/api/bookings");\n}\n',
        )
        assert {"Cache", "track", "getJson"} <= _targets(edges, ".listBookings")


class TestFinding6OtherWaysToImport:
    def test_require_and_dynamic_import(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "lib/bookings.js",
            "const MAX_PER_DAY = 10;\nfunction createBooking() {\n"
            "  return MAX_PER_DAY;\n}\nmodule.exports = { createBooking };\n",
        )
        _write(tmp_path, "lib/chart.mjs", "export default function Chart() {\n}\n")
        _write(
            tmp_path,
            "routes/bookings.js",
            'const { createBooking: create } = require("../lib/bookings");\n'
            'const Chart = lazy(() => import("../lib/chart.mjs"));\n'
            "function handler() {\n  return create();\n}\n",
        )
        graph = _build(tmp_path)
        assert graph.metadata["files"]["routes/bookings.js"]["imports"] == [
            "lib/bookings.js",
            "lib/chart.mjs",
        ]
        assert ("routes.bookings.handler", "lib.bookings.createBooking") in {
            (e.source, e.target) for e in graph.edges
        }
        status = _status_after_edit(
            tmp_path,
            ["routes"],
            lambda: _edit(tmp_path, "lib/bookings.js", "= 10", "= 1"),
        )
        assert status == STATUS_NEEDS_RECHECK


class TestFinding7StringsAndComments:
    """`//` in a URL is not a comment; "{" in a string is not a block."""

    def test_url_in_a_template_literal(self, tmp_path: Path) -> None:
        nodes, edges = _parse(
            tmp_path,
            "export async function cancelBooking(id: string) {\n"
            "  const res = await fetch(`https://api.example.com/bookings/${id}`, {\n"
            '    method: "DELETE",\n  });\n  await notifyCustomer(id);\n'
            "  return res.ok;\n}\n\nexport function next() {\n  return 1;\n}\n",
        )
        assert (nodes["cancelBooking"].line_start, nodes["cancelBooking"].line_end) == (
            1,
            7,
        )
        assert "notifyCustomer" in _targets(edges, ".cancelBooking")
        assert "nested_in" not in nodes["next"].metadata

    def test_regex_with_slashes_and_brace_in_a_string(self, tmp_path: Path) -> None:
        nodes, edges = _parse(
            tmp_path,
            "export function normalise(url: string) {\n"
            "  if (/^https?:\\/\\//.test(url)) {\n    return save(url);\n  }\n"
            "  return url;\n}\n\n"
            "export function looksLikeJson(text: string) {\n"
            '  return text.startsWith("{");\n}\n\n'
            "export function after() {\n  return 2;\n}\n",
        )
        spans = {name: (n.line_start, n.line_end) for name, n in nodes.items()}
        assert spans == {
            "normalise": (1, 6),
            "looksLikeJson": (8, 10),
            "after": (12, 14),
        }
        assert "save" in _targets(edges, ".normalise")

    def test_jsx_link_with_a_url(self, tmp_path: Path) -> None:
        nodes, _ = _parse(
            tmp_path,
            "export function ZaloLink({ phone }: Props) {\n"
            "  return <a href={`https://zalo.me/${phone}`}>Zalo</a>;\n}\n\n"
            "export function PhoneLink({ phone }: Props) {\n"
            "  return <a href={`tel:${phone}`}>Gọi</a>;\n}\n",
            "components/links.tsx",
        )
        assert (nodes["ZaloLink"].line_start, nodes["ZaloLink"].line_end) == (1, 3)
        assert "nested_in" not in nodes["PhoneLink"].metadata

    def test_code_view_of_a_line(self) -> None:
        cleaner = _CodeLines()
        code, calls = cleaner.clean('const a = "{"; // {{{ not code')
        assert code.rstrip() == 'const a = " ";'
        code, calls = cleaner.clean("log(`total ${sum(x)} {`); /* { */ done();")
        assert "{" not in code and "sum(x)" in calls and "done()" in code
        assert "{" not in cleaner.clean("/* opens {")[0]
        assert cleaner.in_block_comment
        assert cleaner.clean("still { inside */ real();")[0].strip() == "real();"
        # an apostrophe in text is not the start of a string
        assert "}" in cleaner.clean("{open && <p>Don't</p>}")[0]

    def test_template_literal_over_several_lines(self, tmp_path: Path) -> None:
        nodes, _ = _parse(
            tmp_path,
            "const QUERY = `\n  type Query {\n    bookings: [Booking]\n  }\n`;\n\n"
            "export function run() {\n  return send(QUERY);\n}\n",
        )
        assert (nodes["run"].line_start, nodes["run"].line_end) == (7, 9)


class TestFinding8TypeDeclarationsDoNotHideCode:
    @pytest.mark.parametrize(
        ("type_line", "edit"),
        [
            ("type ApiUrl = `https://${string}`;", ("api.example.com", "evil.test")),
            ('export type Opener = "(" | "[";', ("api.example.com", "evil.test")),
            (
                "interface Customer {\n  /** Số điện thoại (10 chữ số */\n"
                "  phone: string;\n}",
                ("api.example.com", "evil.test"),
            ),
        ],
    )
    def test_constant_after_a_type_is_still_tracked(
        self, tmp_path: Path, type_line: str, edit: tuple[str, str]
    ) -> None:
        _write(
            tmp_path,
            "lib/config.ts",
            f"{type_line}\n"
            'export const API_BASE = "https://api.example.com";\n\n'
            "export function url() {\n  return API_BASE;\n}\n",
        )
        before = _build(tmp_path)
        _edit(tmp_path, "lib/config.ts", *edit)
        change = SnapshotDiff(before, _build(tmp_path)).compute().files_changed[0]
        assert change.module_level_changed is True

    def test_type_only_edit_is_still_not_runtime(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "lib/config.ts",
            'export type Status =\n  | "booked"\n  | "done";\n\n'
            "export const LIMIT = 5;\n",
        )
        before = _build(tmp_path)
        _edit(tmp_path, "lib/config.ts", '| "done"', '| "done"\n  | "cancelled"')
        change = SnapshotDiff(before, _build(tmp_path)).compute().files_changed[0]
        assert change.module_level_changed is False


class TestFinding9NamesThatDidNotResolve:
    def test_import_then_export_without_from(self, tmp_path: Path) -> None:
        _write(tmp_path, "lib/bookings.ts", "export function createBooking() {\n}\n")
        _write(
            tmp_path,
            "lib/index.ts",
            'import { createBooking } from "./bookings";\nexport { createBooking };\n',
        )
        _write(
            tmp_path,
            "app/page.tsx",
            'import { createBooking } from "@/lib";\n'
            "export default function Page() {\n  return createBooking();\n}\n",
        )
        assert ("app.page.Page", "lib.bookings.createBooking") in {
            (e.source, e.target) for e in _build(tmp_path).edges
        }

    def test_wrapped_default_export(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "components/Chart.tsx",
            "function Chart() {\n  return null;\n}\nexport default memo(Chart);\n",
        )
        _write(
            tmp_path,
            "app/page.tsx",
            'import RevenueChart from "@/components/Chart";\n'
            "export default function Page() {\n  return <RevenueChart />;\n}\n",
        )
        assert ("app.page.Page", "components.Chart.Chart") in {
            (e.source, e.target) for e in _build(tmp_path).edges
        }

    def test_base_class_in_another_file(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "lib/base.ts",
            "export class BaseRepo {\n  limit = 10;\n"
            "  all() {\n    return [];\n  }\n}\n",
        )
        _write(
            tmp_path,
            "lib/bookings.ts",
            'import { BaseRepo } from "./base";\n'
            "export class BookingRepo extends BaseRepo {\n"
            "  upcoming() {\n    return this.all();\n  }\n}\n",
        )
        status = _status_after_edit(
            tmp_path,
            ["lib/bookings.ts"],
            lambda: _edit(tmp_path, "lib/base.ts", "limit = 10", "limit = 1"),
        )
        assert status == STATUS_NEEDS_RECHECK


class TestFinding10ByteOrderMark:
    def test_typescript_file_saved_with_a_bom(self, tmp_path: Path) -> None:
        _write(tmp_path, "lib/db.ts", "export function insertRow() {\n}\n")
        (tmp_path / "lib" / "bookings.ts").write_bytes(
            b"\xef\xbb\xbf" + 'import { insertRow } from "./db";\n'
            "export function createBooking() {\n  insertRow();\n}\n".encode()
        )
        graph = _build(tmp_path)
        assert graph.metadata["files"]["lib/bookings.ts"]["imports"] == ["lib/db.ts"]
        assert ("lib.bookings.createBooking", "lib.db.insertRow") in {
            (e.source, e.target) for e in graph.edges
        }

    def test_python_file_saved_with_a_bom(self, tmp_path: Path) -> None:
        (tmp_path / "main.py").write_bytes(
            b"\xef\xbb\xbfdef handler():\n    return 1\n"
        )
        config = Config(
            project="p",
            sources=[SourceConfig(path=".", language="python")],
            project_root=tmp_path,
        )
        graph = GraphBuilder(config, use_cache=False).build()
        assert list(graph.nodes) == ["main.handler"]

    def test_feature_store_in_another_encoding(self, tmp_path: Path) -> None:
        path = tmp_path / "features.json"
        path.write_text('{"version": 1, "features": []}', encoding="utf-16")
        with pytest.raises(FeatureStoreError, match="Cannot read"):
            FeatureStore.load(path)


class TestSmallerItems:
    @pytest.mark.parametrize(
        ("pattern", "text", "expected"),
        [
            ("lib/**/*.ts", "lib/db.ts", True),
            ("lib/**/*.ts", "lib/deep/er/db.ts", True),
            ("**/components/**", "components/BookingForm.tsx", True),
            ("components/*.{ts,tsx}", "components/BookingForm.tsx", True),
            ("components/*.{ts,tsx}", "components/BookingForm.css", False),
            ("./lib/db.ts", "lib/db.ts", True),
            ("lib/**/*.ts", "app/db.ts", False),
        ],
    )
    def test_glob_forms(self, pattern: str, text: str, expected: bool) -> None:
        assert pattern_matches(pattern, text) is expected

    def test_a_file_glob_does_not_match_function_names(self, tmp_path: Path) -> None:
        shutil.copytree(FIXTURE / "base", tmp_path / "app")
        store = FeatureStore()
        store.upsert_feature("booking", "Booking", ["*Booking*"])
        scope = FeatureMap(store, _build(tmp_path / "app")).scope("booking")
        assert scope.owned_files == [
            "components/BookingForm.tsx",
            "components/BookingList.tsx",
        ]
        assert all(
            node.startswith("components.Booking") for node in scope.owned_nodes
        ), scope.owned_nodes

    def test_unrelated_handlers_are_not_a_rename(self, tmp_path: Path) -> None:
        _write(
            tmp_path,
            "app/api/reports/route.ts",
            "export function GET() {\n  return report();\n}\n",
        )
        before = _build(tmp_path)
        (tmp_path / "app/api/reports/route.ts").unlink()
        _write(
            tmp_path,
            "app/api/export/route.ts",
            "export function GET() {\n  return exportAll();\n}\n",
        )
        result = SnapshotDiff(before, _build(tmp_path)).compute()
        assert result.nodes_renamed == []
        assert [c.node.id for c in result.nodes_removed] == [
            "app.api.reports.route.GET"
        ]
        assert [c.node.id for c in result.nodes_added] == ["app.api.export.route.GET"]

    def test_moved_unchanged_function_is_still_a_rename(self, tmp_path: Path) -> None:
        body = "export function helper() {\n  return 42;\n}\n"
        _write(tmp_path, "lib/a.ts", body)
        before = _build(tmp_path)
        (tmp_path / "lib/a.ts").unlink()
        _write(tmp_path, "lib/b.ts", body)
        result = SnapshotDiff(before, _build(tmp_path)).compute()
        assert [c.node.id for c in result.nodes_renamed] == ["lib.b.helper"]

    def test_long_lists_say_how_much_is_left_out(self, tmp_path: Path) -> None:
        names = [f"fn{number:02d}" for number in range(30)]
        source = "".join(f"export function {n}() {{\n  return 1;\n}}\n" for n in names)
        _write(tmp_path, "lib/many.ts", source)
        before = _build(tmp_path)
        _write(tmp_path, "lib/many.ts", source.replace("return 1;", "return 2;"))
        text = format_diff_text(SnapshotDiff(before, _build(tmp_path)).compute())
        assert "Bodies changed: 30" in text
        assert "… and 10 more" in text

    def test_cache_does_not_keep_flows_removed_from_the_config(
        self, tmp_path: Path
    ) -> None:
        _write(tmp_path, "lib/bookings.ts", "export function createBooking() {\n}\n")

        def build(flows: dict) -> Graph:
            config = Config.auto_detect(tmp_path)
            config.flows = flows
            return GraphBuilder(config, use_cache=True).build()

        with_flow = build({"dat-lich": ["*createBooking"]})
        assert with_flow.nodes["lib.bookings.createBooking"].metadata["flows"] == [
            "dat-lich"
        ]
        without = build({})
        assert "flows" not in without.nodes["lib.bookings.createBooking"].metadata


class TestImpactWording:
    """The impact report agrees with the fingerprint in the cases above."""

    def test_wrapped_handler_dependency_is_reported_as_indirect(
        self, tmp_path: Path
    ) -> None:
        _write(tmp_path, "lib/bookings.ts", "export function createBooking() {\n}\n")
        _write(
            tmp_path,
            "app/api/bookings/route.ts",
            'import { createBooking } from "@/lib/bookings";\n'
            "export const POST = wrap(async () => {\n  return createBooking();\n});\n",
        )
        store = FeatureStore()
        store.upsert_feature("api", "API", ["app/api"])
        before = _build(tmp_path)
        _edit(tmp_path, "lib/bookings.ts", "{\n}", "{\n  return 1;\n}")
        impact = compute_impact(store, before, _build(tmp_path))
        assert impact["summary"]["touched_indirect"] == ["api"]
        assert impact["features"][0]["indirect"]["functions"][0]["id"] == (
            "lib.bookings.createBooking"
        )
