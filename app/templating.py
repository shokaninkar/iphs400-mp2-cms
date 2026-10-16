"""Single shared Jinja2Templates instance and filters.

T03's code review flagged a latent inconsistency: each route module was
creating its own Jinja2Templates(...) (a separate Environment), registering
the markdown filter on its own copy. One shared instance, one registration.
"""
from __future__ import annotations

import posixpath

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from app import settings
from app.markdown import render_markdown

templates = Jinja2Templates(directory=str(settings.TEMPLATES))
templates.env.filters["markdown"] = render_markdown


@pass_context
def rel(context, target: str) -> str:
    """Admin URL `target` ("/admin/notes/5") relative to the current request,
    so no admin HTML is root-absolute (CLAUDE.md). Computed per request because
    a form can re-render at a different depth than it was served from
    (/admin/notes/5/edit vs. the error re-render at /admin/notes/5).

    Admin templates only: it needs the request, which `cms publish` doesn't
    have. The public site uses `root` instead (templates/base.html)."""
    here = posixpath.dirname(context["request"].url.path)
    folder, name = posixpath.split(target)
    up = posixpath.relpath(folder, here)
    return name if up == "." else f"{up}/{name}"


templates.env.globals["rel"] = rel
