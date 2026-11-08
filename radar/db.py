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
CREATE TABLE IF NOT EXISTS apify_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor TEXT,
    run_id TEXT,
    status TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
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
