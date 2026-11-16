# HC-AI | ticket: FDD-TOOL-CODEMAP
"""Tests for VIBE-102: content fingerprints."""

from __future__ import annotations

from codebase_map.fingerprint import (
    HASH_LENGTH,
    exclusive_hashes,
    lines_hash,
    module_level_hash,
    named_hashes,
    text_hash,
)

OUTER_WITH_INNER = [
    "class Shop:",  # 1
    "    name = 'Moc'",  # 2
    "    def open(self):",  # 3
    "        return 9",  # 4
    "    closed = False",  # 5
]


def _edited(lines: list[str], number: int, text: str) -> list[str]:
    copy = list(lines)
    copy[number - 1] = text
    return copy


class TestTextHash:
    def test_indentation_blank_lines_and_trailing_space_do_not_matter(self) -> None:
        assert text_hash("  a = 1  \n\n\tb = 2") == text_hash("a = 1\nb = 2")

    def test_line_breaks_matter(self) -> None:
        """In JavaScript `return` on its own line returns nothing."""
        assert text_hash("return a + b;") != text_hash("return\n  a + b;")

    def test_spaces_inside_a_line_matter(self) -> None:
        """They may be inside a string."""
        assert text_hash('say("xin  chào")') != text_hash('say("xin chào")')

    def test_python_keeps_indentation_relative_to_the_block(self) -> None:
        inside = "if vip:\n    discount()\n    log()"
        outside = "if vip:\n    discount()\nlog()"
        shifted = "    if vip:\n        discount()\n        log()"
        assert text_hash(inside, True) != text_hash(outside, True)
        assert text_hash(inside, True) == text_hash(shifted, True)
        # without keep_indent the two cannot be told apart
        assert text_hash(inside) == text_hash(outside)

    def test_any_token_change_matters(self) -> None:
        assert text_hash("return 24 * 60") != text_hash("return 12 * 60")
        assert text_hash('say("xin chào")') != text_hash('say("xin chao")')

    def test_length_is_fixed(self) -> None:
        assert len(text_hash("")) == HASH_LENGTH
        assert len(text_hash("x" * 10_000)) == HASH_LENGTH

    def test_lines_hash_covers_an_inclusive_range(self) -> None:
        lines = ["one", "two", "three", "four"]
        assert lines_hash(lines, 2, 3) == text_hash("two\nthree")
        # An unknown end line (0) means "just the first line"
        assert lines_hash(lines, 2, 0) == text_hash("two")


class TestExclusiveHashes:
    """Each line counts towards the innermost range that contains it."""

    RANGES = [(1, 5), (3, 4)]  # the class, then its method

    def test_editing_the_inner_range_changes_only_the_inner_hash(self) -> None:
        before = exclusive_hashes(OUTER_WITH_INNER, self.RANGES)
        after = exclusive_hashes(
            _edited(OUTER_WITH_INNER, 4, "        return 10"), self.RANGES
        )
        assert before[0] == after[0]
        assert before[1] != after[1]

    def test_editing_the_outer_range_changes_only_the_outer_hash(self) -> None:
        before = exclusive_hashes(OUTER_WITH_INNER, self.RANGES)
        after = exclusive_hashes(
            _edited(OUTER_WITH_INNER, 5, "    closed = True"), self.RANGES
        )
        assert before[0] != after[0]
        assert before[1] == after[1]

    def test_result_follows_input_order(self) -> None:
        forward = exclusive_hashes(OUTER_WITH_INNER, [(1, 5), (3, 4)])
        backward = exclusive_hashes(OUTER_WITH_INNER, [(3, 4), (1, 5)])
        assert forward == list(reversed(backward))


class TestNamedHashes:
    def test_unique_names_get_their_own_fingerprint(self) -> None:
        hashes = named_hashes(OUTER_WITH_INNER, [("Shop", 1, 5), ("Shop.open", 3, 4)])
        assert set(hashes) == {"Shop", "Shop.open"}
        assert hashes["Shop"] != hashes["Shop.open"]

    def test_same_name_twice_reacts_to_an_edit_in_either_one(self) -> None:
        lines = [
            "def a():",
            "    return 1",
            "def a():",
            "    return 2",
            "def b(): pass",
        ]
        items = [("a", 1, 2), ("a", 3, 4), ("b", 5, 5)]
        before = named_hashes(lines, items)

        first_edited = named_hashes(_edited(lines, 2, "    return 100"), items)
        second_edited = named_hashes(_edited(lines, 4, "    return 200"), items)

        assert first_edited["a"] != before["a"]
        assert second_edited["a"] != before["a"]
        assert first_edited["b"] == second_edited["b"] == before["b"]


class TestModuleLevelHash:
    """The fingerprint of everything that is not inside a function or class."""

    LINES = ["LIMIT = 5", "def f():", "    return LIMIT", "", "RATE = 2"]
    COVERED = [(2, 3)]

    def test_changes_when_code_outside_functions_changes(self) -> None:
        before = module_level_hash(self.LINES, self.COVERED)
        after = module_level_hash(_edited(self.LINES, 1, "LIMIT = 6"), self.COVERED)
        assert before != after

    def test_ignores_edits_inside_functions(self) -> None:
        before = module_level_hash(self.LINES, self.COVERED)
        after = module_level_hash(
            _edited(self.LINES, 3, "    return LIMIT + 1"), self.COVERED
        )
        assert before == after
