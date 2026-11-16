# HC-AI | ticket: VIBE-106
"""Claude Replay — parse Claude Code session JSONL into step-by-step events.

Each session file at ``~/.claude/projects/<encoded-path>/<session-uuid>.jsonl``
is a stream of mixed events (user prompts, assistant messages, tool calls,
file-history deltas, API metadata). This module turns one of those files
into a flat ``list[Step]`` that the pane can scrub through, plus a session
summary used in the Timeline-style list.

Day 4 keeps the parser pure (no HTTP) and privacy-light (no secret
redaction yet — that lands with the player UI on Day 5).
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

DEFAULT_PROJECTS_DIR = Path.home() / ".claude" / "projects"


# ─── Data models ──────────────────────────────────────────────────────────


@dataclass
class Step:
    """One readable step in a replay: a user prompt, Claude reply, or tool call."""

    index: int
    timestamp: str
    kind: str  # "user" | "claude" | "tool"
    text: str
    tool_name: Optional[str] = None
    tool_input_summary: Optional[str] = None
    files_touched: list[str] = field(default_factory=list)
    message_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        # Drop None/empty fields to keep the JSON lean.
        return {k: v for k, v in d.items() if v not in (None, [], "")}


@dataclass
class SessionSummary:
    id: str
    path: str
    title: str
    started_at: str
    ended_at: str
    step_count: int
    file_count: int
    total_lines: int

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Encoding helpers ─────────────────────────────────────────────────────


def encode_project_dir(repo: Path) -> str:
    """Project dirs under ~/.claude/projects/ encode absolute paths by
    replacing ``/`` with ``-``. Return the encoded form for ``repo``.
    """
    return "-" + str(repo.resolve()).replace("/", "-").lstrip("-")


def project_sessions_dir(repo: Path, root: Optional[Path] = None) -> Path:
    # Resolve at call time so tests can monkey-patch DEFAULT_PROJECTS_DIR.
    if root is None:
        root = DEFAULT_PROJECTS_DIR
    return root / encode_project_dir(repo)


# ─── Session listing ──────────────────────────────────────────────────────


def list_sessions(repo: Path, root: Optional[Path] = None) -> list[SessionSummary]:
    """List all session JSONL files for the given repo, newest first.

    Returns an empty list if the project has never been opened in Claude
    Code (no encoded dir yet).
    """
    sdir = project_sessions_dir(repo, root)
    if not sdir.is_dir():
        return []
    out: list[SessionSummary] = []
    for jsonl in sdir.glob("*.jsonl"):
        summary = summarise_session(jsonl)
        if summary is not None:
            out.append(summary)
    out.sort(key=lambda s: s.started_at, reverse=True)
    return out


def summarise_session(jsonl_path: Path) -> Optional[SessionSummary]:
    """Cheap one-pass summary: first/last timestamps, kind counts, title."""
    if not jsonl_path.is_file():
        return None
    first_ts = ""
    last_ts = ""
    step_count = 0
    file_touched: set[str] = set()
    total_lines = 0
    title: Optional[str] = None
    first_user_text: Optional[str] = None

    for e in _iter_events(jsonl_path):
        total_lines += 1
        t = e.get("type")
        ts = e.get("timestamp") or ""
        if ts:
            if not first_ts or ts < first_ts:
                first_ts = ts
            if ts > last_ts:
                last_ts = ts
        if t == "user":
            step_count += 1
            if first_user_text is None:
                first_user_text = _extract_user_text(e)
        elif t == "assistant":
            step_count += 1
            # tool_use blocks count as their own steps
            blocks = _assistant_blocks(e)
            step_count += sum(1 for b in blocks if b.get("type") == "tool_use")
        elif t == "file-history-delta":
            tp = e.get("trackingPath")
            if tp:
                file_touched.add(tp)
        elif t == "custom-title":
            v = e.get("title") or e.get("value")
            if isinstance(v, str) and v.strip():
                title = v.strip()

    if not first_ts:
        return None  # no readable events

    return SessionSummary(
        id=jsonl_path.stem,
        path=str(jsonl_path),
        title=(title or _shorten(first_user_text) or jsonl_path.stem[:8]),
        started_at=first_ts,
        ended_at=last_ts,
        step_count=step_count,
        file_count=len(file_touched),
        total_lines=total_lines,
    )


# ─── Full session parse ───────────────────────────────────────────────────


def parse_session(jsonl_path: Path) -> list[Step]:
    """Return the ordered list of replay steps for a session file."""
    if not jsonl_path.is_file():
        return []

    steps: list[Step] = []
    # Map Claude assistant messageId → index of the step so later
    # file-history-delta events can attach their trackingPath.
    message_to_step: dict[str, int] = {}

    index = 0

    for e in _iter_events(jsonl_path):
        t = e.get("type")
        ts = e.get("timestamp") or ""

        if t == "user":
            text = _extract_user_text(e)
            if not text:
                continue
            steps.append(
                Step(
                    index=index,
                    timestamp=ts,
                    kind="user",
                    text=_shorten(text, 2000),
                )
            )
            index += 1

        elif t == "assistant":
            msg_id = (e.get("message") or {}).get("id")
            blocks = _assistant_blocks(e)
            text = _extract_assistant_text(blocks)
            if text:
                steps.append(
                    Step(
                        index=index,
                        timestamp=ts,
                        kind="claude",
                        text=_shorten(text, 2000),
                        message_id=msg_id,
                    )
                )
                if msg_id:
                    message_to_step[msg_id] = index
                index += 1
            for b in blocks:
                if b.get("type") != "tool_use":
                    continue
                steps.append(
                    Step(
                        index=index,
                        timestamp=ts,
                        kind="tool",
                        text="",
                        tool_name=b.get("name"),
                        tool_input_summary=_summarise_tool_input(
                            b.get("name") or "", b.get("input") or {}
                        ),
                        message_id=msg_id,
                    )
                )
                if msg_id and msg_id not in message_to_step:
                    message_to_step[msg_id] = index
                index += 1

        elif t == "file-history-delta":
            tp = e.get("trackingPath")
            if not tp:
                continue
            mid = e.get("messageId")
            target = message_to_step.get(mid) if mid else None
            if target is not None and 0 <= target < len(steps):
                if tp not in steps[target].files_touched:
                    steps[target].files_touched.append(tp)
            else:
                # No matching assistant step — attach to the last step we have
                # so the file never gets dropped entirely.
                if steps and tp not in steps[-1].files_touched:
                    steps[-1].files_touched.append(tp)

    return steps


# ─── Helpers ──────────────────────────────────────────────────────────────


def _iter_events(jsonl_path: Path) -> Iterator[dict]:
    """Yield parsed events; skip lines that fail to decode."""
    with jsonl_path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _extract_user_text(event: dict) -> str:
    msg = event.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if b.get("type") == "text":
                    parts.append(b.get("text") or "")
                elif b.get("type") == "tool_result":
                    # Keep tool_result summaries out of the user's visible text.
                    continue
        return "\n".join(p for p in parts if p)
    return ""


def _assistant_blocks(event: dict) -> list[dict]:
    msg = event.get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def _extract_assistant_text(blocks: list[dict]) -> str:
    parts = []
    for b in blocks:
        if b.get("type") == "text":
            txt = b.get("text") or ""
            if txt:
                parts.append(txt)
    return "\n\n".join(parts)


def _summarise_tool_input(name: str, inp: dict) -> str:
    """Pick the single field that best identifies what a tool call did.

    Day 5 adds proper redaction; for now we keep inputs short and avoid
    dumping full command bodies / file contents into the replay feed.
    """
    if not isinstance(inp, dict):
        return ""
    if name in {"Read", "Edit", "Write", "Glob"}:
        return str(inp.get("file_path") or inp.get("path") or inp.get("pattern") or "")
    if name == "Bash":
        cmd = str(inp.get("command") or "")
        return _shorten(cmd.splitlines()[0] if cmd else "", 160)
    if name == "Grep":
        return str(inp.get("pattern") or "")
    if name == "WebFetch" or name == "WebSearch":
        return str(inp.get("url") or inp.get("query") or "")
    # Generic fallback: pick the first short string field.
    for k in ("name", "query", "subject", "title", "description"):
        v = inp.get(k)
        if isinstance(v, str):
            return _shorten(v, 160)
    return ""


_WS = re.compile(r"\s+")


def _shorten(text: Optional[str], limit: int = 120) -> str:
    if not text:
        return ""
    # Normalise whitespace and NFC so tests over unicode stay predictable.
    text = unicodedata.normalize("NFC", _WS.sub(" ", text)).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


# ─── CLI helper (used by the mod subcommand for debugging) ────────────────


def main(argv: Optional[list[str]] = None) -> dict[str, Any]:
    """Return a compact JSON-ready view of a session (for `cbm mod replay`)."""
    import argparse

    p = argparse.ArgumentParser("cbm-replay")
    p.add_argument("--repo", default=".", help="Repository root")
    p.add_argument("--session", help="Session id (uuid stem)")
    args = p.parse_args(argv)

    repo = Path(args.repo).resolve()
    if args.session is None:
        return {"sessions": [s.to_dict() for s in list_sessions(repo)]}
    sdir = project_sessions_dir(repo)
    steps = parse_session(sdir / f"{args.session}.jsonl")
    return {"session": args.session, "steps": [s.to_dict() for s in steps]}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, ensure_ascii=False))
