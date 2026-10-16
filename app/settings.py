"""Configuration, read from the environment (never hard-code secrets)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
SITE = ROOT / "site"


def _load_dotenv(path: Path) -> None:
    """Read KEY=value lines from .env into os.environ. Real environment
    variables win, so CI and tests can override. No dependency needed."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]  # only a matched pair of quotes, never one stray
        os.environ.setdefault(key.strip(), value)


_load_dotenv(ROOT / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default) or default


SECRET_KEY = env("CMS_SECRET_KEY", "dev-only-not-for-production")
DATABASE_PATH = ROOT / env("CMS_DATABASE", "cms.db")  # relative paths resolve from the repo root
SITE_TITLE = env("CMS_SITE_TITLE", "inkadmissions")
# Set this to your Pages URL once you deploy, e.g.
# https://yourname.github.io/iphs400-mp2-cms/
BASE_PATH = env("CMS_BASE_PATH")
