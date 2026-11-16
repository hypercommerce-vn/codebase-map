# HC-AI | ticket: VIBE-106
"""Tests for codebase_map.mod.replay — JSONL → Step parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codebase_map.mod.replay import (
    Step,
    _shorten,
    _summarise_tool_input,
    encode_project_dir,
    list_sessions,
    parse_session,
    project_sessions_dir,
    summarise_session,
)


def _write_session(path: Path, events: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in events))


def _user(text: str, ts: str) -> dict:
    return {
        "type": "user",
        "timestamp": ts,
        "message": {"role": "user", "content": text},
    }


def _assistant(text: str, ts: str, mid: str, tools: list[dict] | None = None) -> dict:
    blocks: list[dict] = []
    if text:
        blocks.append({"type": "text", "text": text})
    for t in tools or []:
        blocks.append({"type": "tool_use", **t})
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {"role": "assistant", "id": mid, "content": blocks},
    }


def _fhd(ts: str, mid: str, file: str) -> dict:
    return {
        "type": "file-history-delta",
        "timestamp": ts,
        "messageId": mid,
        "trackingPath": file,
    }


def _mktitle(value: str) -> dict:
    return {"type": "custom-title", "title": value}


# ─── encode_project_dir ──────────────────────────────────────────────────


class TestEncoding:
    def test_encode_path(self):
        p = Path("/Users/foo/code/project-a")
        assert encode_project_dir(p) == "-Users-foo-code-project-a"

    def test_project_sessions_dir_under_root(self, tmp_path: Path):
        d = project_sessions_dir(Path("/x/y"), root=tmp_path)
        assert d == tmp_path / "-x-y"


# ─── list_sessions ──────────────────────────────────────────────────────


class TestListSessions:
    def test_empty_when_no_dir(self, tmp_path: Path):
        assert list_sessions(Path("/no/such/repo"), root=tmp_path) == []

    def test_returns_newest_first(self, tmp_path: Path):
        repo = tmp_path / "project"
        repo.mkdir()
        sdir = tmp_path / encode_project_dir(repo)
        sdir.mkdir()
        _write_session(
            sdir / "old.jsonl",
            [
                _user("first", "2026-11-14T10:00:00Z"),
                _assistant("ok", "2026-11-14T10:00:05Z", "m1"),
            ],
        )
        _write_session(
            sdir / "new.jsonl",
            [
                _user("later", "2026-11-15T10:00:00Z"),
                _assistant("ok", "2026-11-15T10:00:05Z", "m2"),
            ],
        )
        sessions = list_sessions(repo, root=tmp_path)
        assert [s.id for s in sessions] == ["new", "old"]


# ─── summarise_session ──────────────────────────────────────────────────


class TestSummarise:
    def test_none_for_missing_file(self, tmp_path: Path):
        assert summarise_session(tmp_path / "nope.jsonl") is None

    def test_counts_steps_and_files(self, tmp_path: Path):
        p = tmp_path / "s.jsonl"
        _write_session(
            p,
            [
                _user("do X", "2026-11-15T10:00:00Z"),
                _assistant(
                    "ok",
                    "2026-11-15T10:00:05Z",
                    "m1",
                    tools=[{"name": "Bash", "input": {"command": "ls"}}],
                ),
                _fhd("2026-11-15T10:00:07Z", "m1", "a.py"),
                _fhd("2026-11-15T10:00:08Z", "m1", "b.py"),
            ],
        )
        s = summarise_session(p)
        assert s is not None
        # 1 user + 1 claude + 1 tool = 3 steps
        assert s.step_count == 3
        assert s.file_count == 2
        assert s.started_at == "2026-11-15T10:00:00Z"
        assert s.ended_at == "2026-11-15T10:00:08Z"

    def test_custom_title_wins(self, tmp_path: Path):
        p = tmp_path / "s.jsonl"
        _write_session(
            p,
            [
                _user("first msg", "2026-11-15T10:00:00Z"),
                _mktitle("My session"),
                _assistant("ok", "2026-11-15T10:00:05Z", "m1"),
            ],
        )
        s = summarise_session(p)
        assert s.title == "My session"

    def test_title_falls_back_to_first_user(self, tmp_path: Path):
        p = tmp_path / "s.jsonl"
        _write_session(
            p,
            [
                _user("Hello world", "2026-11-15T10:00:00Z"),
                _assistant("hi", "2026-11-15T10:00:05Z", "m1"),
            ],
        )
        s = summarise_session(p)
        assert s.title == "Hello world"


# ─── parse_session ──────────────────────────────────────────────────────


class TestParseSession:
    def test_returns_empty_for_missing(self, tmp_path: Path):
        assert parse_session(tmp_path / "nope.jsonl") == []

    def test_user_assistant_tool_order(self, tmp_path: Path):
        p = tmp_path / "s.jsonl"
        _write_session(
            p,
            [
                _user("run ls", "2026-11-15T10:00:00Z"),
                _assistant(
                    "Em chạy ls.",
                    "2026-11-15T10:00:05Z",
                    "m1",
                    tools=[{"name": "Bash", "input": {"command": "ls -la"}}],
                ),
            ],
        )
        steps = parse_session(p)
        assert [s.kind for s in steps] == ["user", "claude", "tool"]
        assert steps[0].text == "run ls"
        assert steps[1].text == "Em chạy ls."
        assert steps[2].tool_name == "Bash"
        assert steps[2].tool_input_summary == "ls -la"

    def test_file_history_attaches_to_assistant(self, tmp_path: Path):
        p = tmp_path / "s.jsonl"
        _write_session(
            p,
            [
                _user("edit a.py", "2026-11-15T10:00:00Z"),
                _assistant(
                    "Em sửa.",
                    "2026-11-15T10:00:05Z",
                    "m1",
                    tools=[{"name": "Edit", "input": {"file_path": "a.py"}}],
                ),
                _fhd("2026-11-15T10:00:07Z", "m1", "a.py"),
                _fhd("2026-11-15T10:00:08Z", "m1", "b.py"),
            ],
        )
        steps = parse_session(p)
        # file-history-delta attaches to the Claude step (first one with mid=m1)
        claude_step = next(s for s in steps if s.kind == "claude")
        assert claude_step.files_touched == ["a.py", "b.py"]

    def test_skips_empty_user_messages(self, tmp_path: Path):
        p = tmp_path / "s.jsonl"
        _write_session(
            p,
            [
                _user("", "2026-11-15T10:00:00Z"),
                _user("real msg", "2026-11-15T10:00:01Z"),
                _assistant("ok", "2026-11-15T10:00:05Z", "m1"),
            ],
        )
        steps = parse_session(p)
        user_texts = [s.text for s in steps if s.kind == "user"]
        assert user_texts == ["real msg"]

    def test_assistant_without_text_still_emits_tool(self, tmp_path: Path):
        """Pure tool-call assistant turn (no text) must still produce the tool step."""
        p = tmp_path / "s.jsonl"
        _write_session(
            p,
            [
                _user("search", "2026-11-15T10:00:00Z"),
                _assistant(
                    "",
                    "2026-11-15T10:00:05Z",
                    "m1",
                    tools=[{"name": "Grep", "input": {"pattern": "needle"}}],
                ),
            ],
        )
        steps = parse_session(p)
        assert [s.kind for s in steps] == ["user", "tool"]
        assert steps[1].tool_name == "Grep"
        assert steps[1].tool_input_summary == "needle"

    def test_malformed_lines_skipped(self, tmp_path: Path):
        p = tmp_path / "s.jsonl"
        p.write_text(
            "not json\n"
            + json.dumps(_user("ok", "2026-11-15T10:00:00Z"))
            + "\n{broken\n"
            + json.dumps(_assistant("hi", "2026-11-15T10:00:05Z", "m1"))
            + "\n"
        )
        steps = parse_session(p)
        assert len(steps) == 2  # 1 user + 1 claude


# ─── helpers ────────────────────────────────────────────────────────────


class TestShorten:
    def test_passes_short(self):
        assert _shorten("short") == "short"

    def test_truncates_with_ellipsis(self):
        out = _shorten("x" * 300, limit=50)
        assert len(out) == 50
        assert out.endswith("…")

    def test_handles_empty(self):
        assert _shorten("") == ""
        assert _shorten(None) == ""

    def test_collapses_whitespace(self):
        assert _shorten("  a   b\n\nc  ") == "a b c"


class TestSummariseToolInput:
    @pytest.mark.parametrize(
        "name,inp,expected",
        [
            ("Read", {"file_path": "x.py"}, "x.py"),
            ("Edit", {"file_path": "y.py"}, "y.py"),
            ("Write", {"file_path": "z.py"}, "z.py"),
            ("Bash", {"command": "ls -la"}, "ls -la"),
            ("Grep", {"pattern": "foo"}, "foo"),
            ("Glob", {"pattern": "*.py"}, "*.py"),
            ("WebFetch", {"url": "https://x"}, "https://x"),
            ("Unknown", {"description": "do thing"}, "do thing"),
            ("Unknown", {"random": 123}, ""),
        ],
    )
    def test_picks_identifying_field(self, name, inp, expected):
        assert _summarise_tool_input(name, inp) == expected

    def test_bash_strips_multiline(self):
        out = _summarise_tool_input("Bash", {"command": "ls\nrm -rf /"})
        assert out == "ls"

    def test_handles_non_dict_input(self):
        assert _summarise_tool_input("Bash", "oops") == ""  # type: ignore[arg-type]


# ─── Step ──────────────────────────────────────────────────────────────


class TestStep:
    def test_to_dict_drops_empty_fields(self):
        s = Step(index=0, timestamp="t", kind="user", text="hi")
        d = s.to_dict()
        assert d == {"index": 0, "timestamp": "t", "kind": "user", "text": "hi"}

    def test_to_dict_keeps_populated(self):
        s = Step(
            index=1,
            timestamp="t",
            kind="tool",
            text="",
            tool_name="Bash",
            tool_input_summary="ls",
            files_touched=["a.py"],
            message_id="m1",
        )
        d = s.to_dict()
        assert d["tool_name"] == "Bash"
        assert d["files_touched"] == ["a.py"]
        assert "text" not in d  # empty string dropped
