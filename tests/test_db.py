from datetime import datetime

from radar import db
from radar.models import Record


def make_rec(**kw):
    base = dict(source="s", kind="news", url="https://x.az/a", text="Salam  Dünya",
                published=datetime(2026, 1, 1), parent_url=None)
    base.update(kw)
    return Record(**base)


def test_insert_duplicate_returns_false():
    conn = db.connect(":memory:")
    assert db.insert_record(conn, make_rec()) is True
    assert db.insert_record(conn, make_rec(text="salam dünya")) is False


def test_tables_exist_and_utf8():
    conn = db.connect(":memory:")
    names = {r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
    assert {"records", "classifications", "topics", "topic_days", "validations", "votes", "apify_runs"} <= names
    db.insert_record(conn, make_rec(text="Əhməd şəhər"))
    assert conn.execute("select text, status from records").fetchone() == ("Əhməd şəhər", "new")
