from __future__ import annotations
from pathlib import Path
from typing import Optional
import pytest


class GoldenSnapshot:
    def __init__(self, path: Path):
        self.path = path

    def assert_match(self, content: str, name: str):
        target = self.path / name
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            pytest.skip(f"Created golden: {name}")
        existing = target.read_text()
        assert existing == content, (
            f"Golden mismatch: {name}\n"
            f"  Expected ({len(existing)} chars) vs Actual ({len(content)} chars)\n"
            f"  To update: rm {target}"
        )

    def assert_match_lines(self, lines: List[str], name: str):
        self.assert_match("\n".join(lines) + "\n", name)

    def update(self, content: str, name: str):
        target = self.path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


from typing import List
