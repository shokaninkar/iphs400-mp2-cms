"""SQLite connection and schema. No ORM — raw sqlite3 (ADR-002)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from app import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'editor')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


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
