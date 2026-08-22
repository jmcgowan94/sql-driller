import sqlite3
from pathlib import Path

PROGRESS_DB_PATH = Path(__file__).resolve().parent.parent / "progress.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS topic_level (
    topic TEXT PRIMARY KEY,
    level INTEGER NOT NULL DEFAULT 1,
    streak_correct INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty INTEGER NOT NULL,
    correct INTEGER NOT NULL,
    submitted_sql TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(PROGRESS_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
