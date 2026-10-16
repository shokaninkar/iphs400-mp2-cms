"""SQLite connection and schema. No ORM — raw sqlite3 (ADR-002)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from app import settings
from app.security import hash_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK (type IN ('page', 'note')),
    title TEXT NOT NULL,
    slug TEXT NOT NULL,
    body_md TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK (status IN ('draft', 'published')) DEFAULT 'draft',
    author_id INTEGER NOT NULL REFERENCES users(id),
    nav_order INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(type, slug)
);
"""


def is_duplicate_slug(exc: sqlite3.IntegrityError) -> bool:
    """True only for the content table's UNIQUE(type, slug), not other constraints."""
    return "UNIQUE constraint failed: content.type, content.slug" in str(exc)


def get_connection(path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | str | None = None) -> None:
    conn = get_connection(path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def seed_user(conn: sqlite3.Connection, email: str, password: str, role: str) -> None:
    """Idempotent: safe to call every time seed_demo.py or a test fixture runs."""
    conn.execute(
        "INSERT OR IGNORE INTO users (email, password_hash, role) VALUES (?, ?, ?)",
        (email, hash_password(password), role),
    )
    conn.commit()
