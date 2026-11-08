import hashlib
import sqlite3
from typing import Optional

from radar.models import Record

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    kind TEXT NOT NULL,
    url TEXT NOT NULL,
    url_norm TEXT NOT NULL,
    text TEXT NOT NULL,
    text_hash TEXT NOT NULL,
    published TEXT,
    parent_url TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(url_norm, text_hash)
);
CREATE TABLE IF NOT EXISTS classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id INTEGER NOT NULL REFERENCES records(id),
    category TEXT,
    label TEXT,
    score REAL,
    data TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    summary TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS topic_days (
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    day TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (topic_id, day)
);
CREATE TABLE IF NOT EXISTS validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER REFERENCES topics(id),
    idea TEXT,
    result TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    validation_id INTEGER REFERENCES validations(id),
    voter TEXT,
    vote INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sources (
    name TEXT PRIMARY KEY,
    disabled INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS source_state (
    name TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS idea_status (
    validation_id INTEGER PRIMARY KEY REFERENCES validations(id),
    status TEXT NOT NULL,
    note TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS apify_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    run_id TEXT,
    status TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


MIGRATIONS = [
    ("classifications", "topic_id", "INTEGER REFERENCES topics(id)"),
    ("topics", "candidate_at", "TEXT"),
    ("topic_days", "distinct_voices", "INTEGER NOT NULL DEFAULT 0"),
    ("topic_days", "distinct_sources", "INTEGER NOT NULL DEFAULT 0"),
    ("topic_days", "avg_score", "REAL"),
    ("validations", "decision", "TEXT"),
    ("validations", "data", "TEXT"),
]


def migrate(conn: sqlite3.Connection) -> None:
    """Idempotently add columns missing from tables created by older schema versions."""
    for table, col, decl in MIGRATIONS:
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if col not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")
    conn.commit()


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=DELETE")  # WAL sidecar files break Volume commits
    conn.executescript(SCHEMA)
    migrate(conn)
    return conn


def text_hash(text: str) -> str:
    norm = " ".join(text.lower().split())
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()


def insert_record(conn: sqlite3.Connection, rec: Record, url_norm: Optional[str] = None) -> bool:
    cur = conn.execute(
        "INSERT OR IGNORE INTO records (source, kind, url, url_norm, text, text_hash, published, parent_url)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (rec.source, rec.kind, rec.url, url_norm or rec.url, rec.text, text_hash(rec.text),
         rec.published.isoformat() if rec.published else None, rec.parent_url),
    )
    conn.commit()
    return cur.rowcount == 1
