from datetime import date, timedelta

from radar.db import connect
from radar.trends import assign_topic, update_topic_days, candidates

TODAY = date(2026, 11, 8)


def add(conn, topic, i, day, source="s1", text=None, score=80):
    text = text if text is not None else f"text {topic} {i}"
    cur = conn.execute(
        "INSERT INTO records(source, kind, url, url_norm, text, text_hash, published) VALUES(?,?,?,?,?,?,?)",
        (source, "news", f"u{topic}{i}{source}", f"u{topic}{i}{source}{day}", text, text, day.isoformat()))
    conn.execute("INSERT INTO classifications(record_id, category, label, score, topic_id) VALUES(?,?,?,?,?)",
                 (cur.lastrowid, "X", "l", score, topic))
    conn.commit()


def mk(conn):
    return assign_topic(conn, "topic one")


def test_similar_labels_merge():
    conn = connect(":memory:")
    a = assign_topic(conn, "çörək qiyməti artımı")
    b = assign_topic(conn, "çörək qiymətinin artımı")
    c = assign_topic(conn, "avtobus marşrutu")
    assert a == b and c != a


def test_trend_ignores_duplicate_comments():
    conn = connect(":memory:")
    t = mk(conn)
    d = TODAY - timedelta(days=1)
    for i in range(20):
        add(conn, t, i, d, text="same")
    update_topic_days(conn, d)
    assert conn.execute("select distinct_voices from topic_days where topic_id=?", (t,)).fetchone()[0] == 1


def test_candidate_requires_two_sources():
    conn = connect(":memory:")
    t = mk(conn)
    for i in range(10):
        add(conn, t, i, TODAY - timedelta(days=1), source="s1")
    for k in range(7):
        update_topic_days(conn, TODAY - timedelta(days=k))
    assert candidates(conn, TODAY) == []


def test_candidate_happy_path_and_ordering_and_candidate_at():
    conn = connect(":memory:")
    t = mk(conn)
    for i in range(6):
        add(conn, t, i, TODAY - timedelta(days=1), source="s1" if i % 2 else "s2")
    for k in range(30):
        update_topic_days(conn, TODAY - timedelta(days=k))
    assert candidates(conn, TODAY) == [t]
    assert conn.execute("select candidate_at from topics where id=?", (t,)).fetchone()[0]


def test_growth_needs_double_and_low_score_rejected():
    conn = connect(":memory:")
    t = mk(conn)
    for i in range(5):  # prior window: 5 voices over 21d
        add(conn, t, i, TODAY - timedelta(days=10), source="s1")
    for i in range(5, 7):  # last week: 2 voices -> 2/7 < 2*5/21
        add(conn, t, i, TODAY - timedelta(days=1), source=f"s{i}")
    for k in range(30):
        update_topic_days(conn, TODAY - timedelta(days=k))
    assert candidates(conn, TODAY) == []
    conn2 = connect(":memory:")
    t2 = mk(conn2)
    for i in range(6):
        add(conn2, t2, i, TODAY - timedelta(days=1), source=f"s{i % 2}", score=30)
    for k in range(7):
        update_topic_days(conn2, TODAY - timedelta(days=k))
    assert candidates(conn2, TODAY) == []


def test_migration_adds_columns_to_old_db(tmp_path):
    import sqlite3
    p = str(tmp_path / "old.db")
    c = sqlite3.connect(p)
    c.executescript("CREATE TABLE topics(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, summary TEXT,"
                    " created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
                    "CREATE TABLE classifications(id INTEGER PRIMARY KEY, record_id INTEGER, category TEXT,"
                    " label TEXT, score REAL, data TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);"
                    "CREATE TABLE topic_days(topic_id INTEGER, day TEXT, count INTEGER DEFAULT 0,"
                    " PRIMARY KEY(topic_id, day));")
    c.commit(); c.close()
    conn = connect(p)
    cols = {r[1] for r in conn.execute("pragma table_info(topic_days)")}
    assert {"distinct_voices", "distinct_sources", "avg_score"} <= cols
    assert "candidate_at" in {r[1] for r in conn.execute("pragma table_info(topics)")}
    assert "topic_id" in {r[1] for r in conn.execute("pragma table_info(classifications)")}
