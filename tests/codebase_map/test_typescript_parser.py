# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for VIBE-102: what the TypeScript parser extracts.

Covers the parts the snapshot diff and impact analysis rely on: every
function is found, its line range is right, calls and component usage become
edges, and ids do not depend on where the project sits on disk.
"""

from __future__ import annotations

from pathlib import Path

from codebase_map.graph.models import Edge, EdgeType, LayerType, Node, NodeType
from codebase_map.parsers.typescript_parser import TypeScriptParser


def _parse(
    tmp_path: Path, source: str, rel: str = "src/sample.tsx"
) -> tuple[dict[str, Node], list[Edge]]:
    """Parse ``source`` as the project file ``rel``; nodes are keyed by name."""
    path = tmp_path / Path(rel).name
    path.write_text(source, encoding="utf-8")
    nodes, edges = TypeScriptParser().parse_file(path, "", Path(rel))
    return {node.name: node for node in nodes}, edges


def _span(node: Node) -> tuple[int, int]:
    return node.line_start, node.line_end


def _calls(edges: list[Edge], via: str | None = None) -> set[tuple[str, str]]:
    return {
        (edge.source, edge.target)
        for edge in edges
        if edge.edge_type is EdgeType.CALLS and edge.metadata.get("via") == via
    }


FUNCTIONS = """\
export function readAll<T extends Record<string, unknown>>(name: string): T[] {
  return load(name) as T[];
}

export async function createBooking(
  input: BookingInput,
  now: Date = new Date(),
): Promise<Booking> {
  const slot = await findSlot(input.slotId);
  return save(slot);
}
"""

ARROWS = """\
export const one = (x: number) => x + 1;
export const two = (xs: number[]) =>
  xs
    .filter(Boolean)
    .map((x) => double(x));

const Item = ({ x }: Props) => (
  <li>{format(x)}</li>
);

export const obj = () => ({
  a: 1,
  b: make(),
});

export const block = async <T,>(input: T): Promise<T> => {
  await send(input);
  return input;
};
const noSemi = (a: number) =>
  a * 2

export const after = () => 1
"""

COMPONENT = """\
"use client";
import { useState } from "react";
import {
  createBooking,
  type BookingInput,
} from "@/lib/bookings";
import type { Slot } from "@/lib/types";
import SlotPicker from "./SlotPicker";

export default function BookingForm({
  onCreated,
  slots,
}: {
  onCreated: () => void;
  slots: Slot[];
}) {
  const [name, setName] = useState("");
  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await createBooking({ name });
    onCreated();
  };
  return (
    <form onSubmit={handleSubmit}>
      <SlotPicker slots={slots} />
    </form>
  );
}

const LIMIT = 5;
"""

CLASS = """\
@Component({
  selector: "app-root",
  template: "<div></div>",
})
export class AppComponent extends Base {
  constructor(private http: HttpClient) {
    super();
  }

  @Get(":id")
  async findOne(id: string): Promise<Item> {
    if (!id) {
      throw new Error("x");
    }
    return this.service.load(id);
  }

  private helper() { return 1; }
}

export function after() {
  return helper();
}
"""

OVERLOADS = """\
export function pick(a: string): string
export function pick(a: number): number
export function pick(a: any) {
  return a;
}

export function other() {
  return pick(1);
}
"""


MULTILINE_ARROWS = """\
export const BookingCard = ({
  booking,
  onCancel = () => {},
  showCustomer = false,
}: BookingCardProps) => {
  const label = statusLabel(booking.status);
  return <Card title={label} />;
};

export const createBooking = async (
  input: BookingInput,
  now: Date,
): Promise<Booking> => {
  return save(input, now);
};

const pick = (
  a: number,
  b: number,
) => a + b;

const total = (
  price * quantity
);

const later = (
  a: number,
) =>
  compute(a)
    .then(done);

function tail() {
  return pick(1, 2);
}
"""

INLINE_PARAMETER_TYPES = """\
export function configure(
  options: {
    retries: number;
    onFail: () => void;
  },
  extra?: string,
): void {
  apply(options);
}

export function declared(
  a: string,
): void;

export function last() {
  return 1;
}
"""

NO_SEMICOLONS = """\
export function useThing() {
  const double = (x: number) =>
    x * 2
  const names = (xs: Item[]) =>
    xs
      .filter(Boolean)
      .map((x) => x.name)
  const label = (s: Status) =>
    s === "done"
      ? "Xong"
      : "Chờ"
  return { double, names, label }
}

export const after = () => useThing()
"""


class TestFunctionsAreFound:
    def test_generic_function_is_captured(self, tmp_path: Path) -> None:
        nodes, _ = _parse(tmp_path, FUNCTIONS)
        assert set(nodes) == {"readAll", "createBooking"}

    def test_signature_spanning_lines_keeps_the_whole_body(
        self, tmp_path: Path
    ) -> None:
        nodes, edges = _parse(tmp_path, FUNCTIONS)
        assert _span(nodes["readAll"]) == (1, 3)
        assert _span(nodes["createBooking"]) == (5, 11)
        assert ("src.sample.createBooking", "findSlot") in _calls(edges)
        assert ("src.sample.createBooking", "save") in _calls(edges)

    def test_arrow_function_forms(self, tmp_path: Path) -> None:
        nodes, _ = _parse(tmp_path, ARROWS)
        assert {name: _span(node) for name, node in nodes.items()} == {
            "one": (1, 1),
            "two": (2, 5),
            "Item": (7, 9),
            "obj": (11, 14),
            "block": (16, 19),
            "noSemi": (20, 21),
            "after": (23, 23),
        }

    def test_calls_in_an_expression_body_belong_to_that_arrow(
        self, tmp_path: Path
    ) -> None:
        _, edges = _parse(tmp_path, ARROWS)
        calls = _calls(edges)
        assert ("src.sample.two", "double") in calls
        assert ("src.sample.Item", "format") in calls
        assert ("src.sample.obj", "make") in calls
        assert not any(source == "src.sample.one" for source, _ in calls)

    def test_arrow_function_with_parameters_on_several_lines(
        self, tmp_path: Path
    ) -> None:
        nodes, edges = _parse(tmp_path, MULTILINE_ARROWS)
        # `total` is a parenthesised value, not a function
        assert {name: _span(node) for name, node in nodes.items()} == {
            "BookingCard": (1, 8),
            "createBooking": (10, 15),
            "pick": (17, 20),
            "later": (26, 30),
            "tail": (32, 34),
        }
        calls = _calls(edges)
        assert ("src.sample.BookingCard", "statusLabel") in calls
        assert ("src.sample.createBooking", "save") in calls
        assert ("src.sample.later", "compute") in calls
        assert _calls(edges, via="jsx") == {("src.sample.BookingCard", "Card")}

    def test_object_type_in_the_parameters_is_not_the_body(
        self, tmp_path: Path
    ) -> None:
        nodes, edges = _parse(tmp_path, INLINE_PARAMETER_TYPES)
        assert {name: _span(node) for name, node in nodes.items()} == {
            "configure": (1, 9),
            "declared": (11, 13),  # a declaration without a body
            "last": (15, 17),
        }
        assert ("src.sample.configure", "apply") in _calls(edges)
        assert "nested_in" not in nodes["last"].metadata

    def test_code_without_semicolons(self, tmp_path: Path) -> None:
        nodes, edges = _parse(tmp_path, NO_SEMICOLONS)
        assert {name: _span(node) for name, node in nodes.items()} == {
            "useThing": (1, 13),
            "double": (2, 3),
            "names": (4, 7),
            "label": (8, 11),
            "after": (15, 15),
        }
        assert _calls(edges, via="nested") == {
            ("src.sample.useThing", "src.sample.double"),
            ("src.sample.useThing", "src.sample.names"),
            ("src.sample.useThing", "src.sample.label"),
        }
        assert "nested_in" not in nodes["after"].metadata

    def test_overloads_without_a_body_do_not_swallow_what_follows(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "o.ts"
        path.write_text(OVERLOADS, encoding="utf-8")
        nodes, edges = TypeScriptParser().parse_file(path, "", Path("lib/o.ts"))

        assert [(n.name, n.line_start, n.line_end) for n in nodes] == [
            ("pick", 1, 1),
            ("pick", 2, 2),
            ("pick", 3, 5),
            ("other", 7, 9),
        ]
        assert "nested_in" not in nodes[-1].metadata
        assert _calls(edges) == {("lib.o.other", "pick")}


class TestComponents:
    def test_destructured_props_do_not_end_the_component_early(
        self, tmp_path: Path
    ) -> None:
        nodes, _ = _parse(tmp_path, COMPONENT)
        assert _span(nodes["BookingForm"]) == (10, 28)
        assert _span(nodes["handleSubmit"]) == (18, 22)

    def test_nested_handler_is_linked_to_its_component(self, tmp_path: Path) -> None:
        nodes, edges = _parse(tmp_path, COMPONENT)
        assert nodes["handleSubmit"].metadata["nested_in"] == "src.sample.BookingForm"
        assert _calls(edges, via="nested") == {
            ("src.sample.BookingForm", "src.sample.handleSubmit")
        }
        # Calls inside the handler belong to the handler, not the component
        assert ("src.sample.handleSubmit", "createBooking") in _calls(edges)
        assert ("src.sample.BookingForm", "createBooking") not in _calls(edges)

    def test_jsx_usage_of_a_component_is_an_edge(self, tmp_path: Path) -> None:
        _, edges = _parse(tmp_path, COMPONENT)
        assert _calls(edges, via="jsx") == {("src.sample.BookingForm", "SlotPicker")}

    def test_generic_type_arguments_are_not_components(self, tmp_path: Path) -> None:
        source = (
            "function Page() {\n"
            "  const rows: Array<Row> = load<Row>();\n"
            "  return <Layout><Chart data={rows} /></Layout>;\n"
            "}\n"
            "export default Page;\n"
        )
        nodes, edges = _parse(tmp_path, source)
        assert _calls(edges, via="jsx") == {
            ("src.sample.Page", "Layout"),
            ("src.sample.Page", "Chart"),
        }
        assert nodes["Page"].metadata["export_default"] is True

    def test_default_export_in_the_declaration_is_marked(self, tmp_path: Path) -> None:
        nodes, _ = _parse(tmp_path, COMPONENT)
        assert nodes["BookingForm"].metadata["export_default"] is True
        assert "export_default" not in nodes["handleSubmit"].metadata


class TestImports:
    def test_one_edge_per_statement_with_the_imported_names(
        self, tmp_path: Path
    ) -> None:
        _, edges = _parse(tmp_path, COMPONENT)
        imports = {
            edge.target: edge.metadata.get("names")
            for edge in edges
            if edge.edge_type is EdgeType.IMPORTS
        }
        assert imports == {
            "react": {"useState": "useState"},
            # multi-line statement; the inline `type` import is not a value
            "@/lib/bookings": {"createBooking": "createBooking"},
            # `import type` brings no callable names
            "@/lib/types": None,
            "./SlotPicker": {"SlotPicker": "default"},
        }

    def test_renamed_and_side_effect_imports(self, tmp_path: Path) -> None:
        source = (
            'import "./globals.css";\n'
            'import React, { useMemo as memo } from "react";\n'
            "export const x = () => memo();\n"
        )
        _, edges = _parse(tmp_path, source)
        imports = {
            edge.target: edge.metadata.get("names")
            for edge in edges
            if edge.edge_type is EdgeType.IMPORTS
        }
        assert imports == {
            "./globals.css": None,
            "react": {"React": "default", "memo": "useMemo"},
        }


class TestClasses:
    def test_decorator_with_arguments_on_several_lines(self, tmp_path: Path) -> None:
        nodes, _ = _parse(tmp_path, CLASS)
        assert nodes["AppComponent"].decorators == ["Component"]
        assert _span(nodes["AppComponent"]) == (5, 19)

    def test_methods_and_their_ranges(self, tmp_path: Path) -> None:
        nodes, edges = _parse(tmp_path, CLASS)
        assert _span(nodes["constructor"]) == (6, 8)
        assert _span(nodes["findOne"]) == (11, 16)
        assert _span(nodes["helper"]) == (18, 18)
        assert nodes["findOne"].node_type is NodeType.ROUTE
        assert nodes["findOne"].decorators == ["Get"]
        assert nodes["findOne"].parent_class == "src.sample.AppComponent"
        assert ("src.sample.AppComponent.findOne", "load") in _calls(edges)

    def test_code_after_the_class_is_not_part_of_it(self, tmp_path: Path) -> None:
        nodes, edges = _parse(tmp_path, CLASS)
        assert _span(nodes["after"]) == (21, 23)
        assert nodes["after"].parent_class == ""
        assert ("src.sample.after", "helper") in _calls(edges)


class TestBodyFingerprint:
    def test_every_node_has_one(self, tmp_path: Path) -> None:
        for source in (FUNCTIONS, ARROWS, COMPONENT, CLASS):
            nodes, _ = _parse(tmp_path, source)
            assert all(node.metadata.get("body_hash") for node in nodes.values())

    def test_reformatting_does_not_change_it(self, tmp_path: Path) -> None:
        before, _ = _parse(tmp_path, FUNCTIONS)
        after, _ = _parse(tmp_path, FUNCTIONS.replace("  ", "\t\t"))
        assert (
            before["createBooking"].metadata["body_hash"]
            == after["createBooking"].metadata["body_hash"]
        )

    def test_editing_a_handler_leaves_the_component_alone(self, tmp_path: Path) -> None:
        before, _ = _parse(tmp_path, COMPONENT)
        after, _ = _parse(
            tmp_path, COMPONENT.replace("onCreated();", "onCreated(); track();")
        )
        assert (
            before["handleSubmit"].metadata["body_hash"]
            != after["handleSubmit"].metadata["body_hash"]
        )
        assert (
            before["BookingForm"].metadata["body_hash"]
            == after["BookingForm"].metadata["body_hash"]
        )

    def test_editing_a_method_leaves_the_class_alone(self, tmp_path: Path) -> None:
        before, _ = _parse(tmp_path, CLASS)
        after, _ = _parse(tmp_path, CLASS.replace("return 1;", "return 2;"))
        assert (
            before["helper"].metadata["body_hash"]
            != after["helper"].metadata["body_hash"]
        )
        assert (
            before["AppComponent"].metadata["body_hash"]
            == after["AppComponent"].metadata["body_hash"]
        )


class TestProjectRelativePaths:
    """Ids, layer and domain come from the path inside the project."""

    def test_ids_do_not_contain_the_folder_the_project_sits_in(
        self, tmp_path: Path
    ) -> None:
        nodes, _ = _parse(
            tmp_path, "export function isSlotFree() {\n}\n", "lib/slots.ts"
        )
        assert nodes["isSlotFree"].id == "lib.slots.isSlotFree"
        assert nodes["isSlotFree"].metadata["module"] == "lib.slots"

    def test_top_level_folder_matches_the_layer_rules(self, tmp_path: Path) -> None:
        source = "export default function Home() {\n  return null;\n}\n"
        nodes, _ = _parse(tmp_path, source, "pages/index.tsx")
        assert nodes["Home"].layer is LayerType.ROUTER

        nodes, _ = _parse(tmp_path, source, "src/pages/index.tsx")
        assert nodes["Home"].layer is LayerType.ROUTER

    def test_without_a_relative_path_the_given_path_is_used(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "slots.ts"
        path.write_text("export function isSlotFree() {\n}\n", encoding="utf-8")
        nodes, _ = TypeScriptParser().parse_file(path)
        assert nodes[0].name == "isSlotFree"
        assert nodes[0].id.endswith(".slots.isSlotFree")


class TestSkipNotCrash:
    def test_unreadable_file_gives_nothing(self, tmp_path: Path) -> None:
        path = tmp_path / "broken.ts"
        path.write_bytes(b"\xff\xfe\x00 not utf-8 \xff")
        assert TypeScriptParser().parse_file(path, "", Path("broken.ts")) == ([], [])

    def test_unbalanced_braces_still_return_the_functions(self, tmp_path: Path) -> None:
        nodes, _ = _parse(tmp_path, "export function a() {\n  if (x) {\n}\n")
        assert _span(nodes["a"]) == (1, 3)
