"""Markdown -> sanitized HTML (D4: must never execute in admin preview or export)."""
from __future__ import annotations

import nh3
from markdown_it import MarkdownIt

_md = MarkdownIt("commonmark")


def render_markdown(body_md: str) -> str:
    return nh3.clean(_md.render(body_md))
