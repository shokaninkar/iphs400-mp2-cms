"""Single shared Jinja2Templates instance and filters.

T03's code review flagged a latent inconsistency: each route module was
creating its own Jinja2Templates(...) (a separate Environment), registering
the markdown filter on its own copy. One shared instance, one registration.
"""
from __future__ import annotations

from fastapi.templating import Jinja2Templates

from app import settings
from app.markdown import render_markdown

templates = Jinja2Templates(directory=str(settings.TEMPLATES))
templates.env.filters["markdown"] = render_markdown
