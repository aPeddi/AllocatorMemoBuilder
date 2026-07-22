"""Export a memo to Markdown + a machine-readable JSON audit artifact."""
from __future__ import annotations

from pathlib import Path

from .memo import render_markdown
from .models import Memo


def write_markdown(memo: Memo, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_markdown(memo))
    return p


def write_json(memo: Memo, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(memo.model_dump_json(indent=2))
    return p
