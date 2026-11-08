from datetime import date, timedelta

from radar import config
from radar.prefilter import _lower

_DAY = "date(COALESCE(r.published, r.created_at))"


def assign_topic(conn, label: str) -> int:
    from rapidfuzz import fuzz  # lazy import

    norm = _lower(label.strip())
    best_id, best = None, 0.0
    for tid, name in conn.execute("SELECT id, name FROM topics ORDER BY id"):
        sc = fuzz.token_set_ratio(norm, _lower(name))
        if sc >= config.TOPIC_MATCH_THRESHOLD and sc > best:
            best_id, best = tid, sc
    if best_id is not None:
        return best_id
    cur = conn.execute("INSERT INTO topics(name) VALUES(?)", (label.strip(),))
    conn.commit()
    return cur.lastrowid


def assign_pending(conn) -> int:
    """Give every classification without a topic one, from its label."""
    rows = conn.execute(
        "SELECT id, label FROM classifications WHERE topic_id IS NULL AND label IS NOT NULL AND label != ''"
    ).fetchall()
    for cid, label in rows:
        conn.execute("UPDATE classifications SET topic_id=? WHERE id=?", (assign_topic(conn, label), cid))
    conn.commit()
    return len(rows)


def update_topic_days(conn, day: date) -> None:
    conn.execute("DELETE FROM topic_days WHERE day=?", (day.isoformat(),))
    conn.execute(
        f"INSERT INTO topic_days(topic_id, day, count, distinct_voices, distinct_sources, avg_score) "
        f"SELECT c.topic_id, ?, COUNT(*), COUNT(DISTINCT r.text_hash), COUNT(DISTINCT r.source), AVG(c.score) "
        f"FROM classifications c JOIN records r ON r.id = c.record_id "
        f"WHERE c.topic_id IS NOT NULL AND {_DAY} = ? GROUP BY c.topic_id",
        (day.isoformat(), day.isoformat()))
    conn.commit()


def _window(conn, tid, start: date, end: date):
    """(distinct voices, distinct sources, avg score) for days start..end inclusive."""
    return conn.execute(
        f"SELECT COUNT(DISTINCT r.text_hash), COUNT(DISTINCT r.source), AVG(c.score) "
        f"FROM classifications c JOIN records r ON r.id = c.record_id "
        f"WHERE c.topic_id=? AND {_DAY} BETWEEN ? AND ?",
        (tid, start.isoformat(), end.isoformat())).fetchone()


def candidates(conn, today: date) -> list:
    rd, bd = config.TREND_RECENT_DAYS, config.TREND_BASELINE_DAYS
    r_start = today - timedelta(days=rd - 1)
    b_end = r_start - timedelta(days=1)
    b_start = b_end - timedelta(days=bd - 1)
    found = []
    for (tid,) in conn.execute("SELECT id FROM topics").fetchall():
        voices, sources, avg = _window(conn, tid, r_start, today)
        if not voices or sources < config.MIN_TREND_SOURCES or (avg or 0) < config.MIN_TREND_AVG_SCORE:
            continue
        prev = _window(conn, tid, b_start, b_end)[0]
        if prev == 0:
            if voices < config.MIN_NEW_TOPIC_VOICES:
                continue
            ratio = float("inf")
        else:
            ratio = (voices / rd) / (prev / bd)
            if ratio < config.TREND_GROWTH_FACTOR:
                continue
        found.append((tid, ratio, voices))
    found.sort(key=lambda t: (-t[1], -t[2], t[0]))
    ids = [t[0] for t in found]
    for tid in ids:
        conn.execute("UPDATE topics SET candidate_at=COALESCE(candidate_at, CURRENT_TIMESTAMP) WHERE id=?", (tid,))
    conn.commit()
    return ids
