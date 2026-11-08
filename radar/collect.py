import logging
import sqlite3

from radar import config
from radar.db import insert_record
from radar.normalize import normalize_url

log = logging.getLogger(__name__)


def collect(conn: sqlite3.Connection, sources) -> dict:
    disabled = {r[0] for r in conn.execute("SELECT name FROM sources WHERE disabled=1")}
    result = {}
    for src in sources:
        if src.name in disabled:
            continue
        try:
            n = 0
            for rec in src.fetch():
                try:
                    if insert_record(conn, rec, url_norm=normalize_url(rec.url)):
                        n += 1
                except Exception:
                    log.exception("skipping bad record from %s", src.name)
            result[src.name] = n
        except Exception:
            log.exception("source %s failed", src.name)
            result[src.name] = -1
    return result


def source_yield(conn: sqlite3.Connection, weeks: int = 4) -> dict:
    rows = conn.execute(
        "SELECT r.source, COUNT(DISTINCT c.record_id) * 1.0 / COUNT(DISTINCT r.id) FROM records r "
        "LEFT JOIN (SELECT c2.record_id FROM classifications c2 JOIN topics t ON t.id = c2.topic_id "
        "WHERE t.candidate_at IS NOT NULL) c ON c.record_id = r.id "
        "WHERE r.created_at >= datetime('now', ?) GROUP BY r.source", (f"-{weeks * 7} days",)).fetchall()
    return {s: y for s, y in rows}


def disable_low_yield(conn: sqlite3.Connection, weeks: int = 4, min_records: int = None) -> list:
    min_records = config.MIN_RECORDS_FOR_YIELD if min_records is None else min_records
    disabled = {r[0] for r in conn.execute("SELECT name FROM sources WHERE disabled=1")}
    counts = dict(conn.execute(
        "SELECT source, COUNT(*) FROM records WHERE created_at >= datetime('now', ?) GROUP BY source",
        (f"-{weeks * 7} days",)).fetchall())
    y = {s: v for s, v in source_yield(conn, weeks).items()
         if s not in disabled and counts.get(s, 0) >= min_records}
    if len(y) < config.MIN_SOURCES_FOR_DISABLE or len(set(y.values())) == 1:
        return []
    k = max(1, int(len(y) * 0.2))
    worst = [s for s, _ in sorted(y.items(), key=lambda kv: (kv[1], kv[0]))[:k]]
    for s in worst:
        conn.execute("INSERT INTO sources(name, disabled) VALUES(?,1) "
                     "ON CONFLICT(name) DO UPDATE SET disabled=1", (s,))
    conn.commit()
    return worst
