# HC-AI | ticket: KMP-M0-05
"""HelloParser — trivial reference parser that reads .txt files."""

from pathlib import Path
from typing import Iterator

from knowledge_memory.core.parsers.base import BaseParser
from knowledge_memory.core.parsers.evidence import Evidence


class HelloParser(BaseParser):
    """Parse .txt files, yielding one Evidence per non-empty line."""

    PARSER_NAME = "hello_txt"
    SUPPORTED_EXTENSIONS = (".txt",)

    def parse(self, source: Path) -> Iterator[Evidence]:
        """Yield Evidence for each non-empty line in a .txt file."""
        if not source.exists() or source.suffix != ".txt":
            return
        for i, line in enumerate(source.read_text().splitlines(), 1):
            text = line.strip()
            if text:
                yield Evidence(
                    source=str(source),
                    data={"text": text},
                    line_range=(i, i),
                )
