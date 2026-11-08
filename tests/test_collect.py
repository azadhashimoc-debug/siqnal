from datetime import datetime

from radar.collect import collect, source_yield, disable_low_yield
from radar.db import connect, insert_record
from radar.models import Record
from radar.sources.apify_src import ApifySource


def rec(src, n):
    return Record(src, "news", f"https://x.az/{src}/{n}?utm_a=1", f"text {src} {n}", datetime(2026, 1, 1))


class Good:
    name = "good"
    def fetch(self):
        return [rec("good", 1), rec("good", 2)]


class Bad:
    name = "bad"
    def fetch(self):
        raise RuntimeError("boom")


def test_collect_survives_failing_adapter():
    conn = connect(":memory:")
    res = collect(conn, [Bad(), Good()])
    assert res == {"bad": -1, "good": 2}
    assert conn.execute("select count(*) from records").fetchone()[0] == 2
    assert collect(conn, [Good()]) == {"good": 0}


def test_collect_skips_bad_record_and_disabled():
    conn = connect(":memory:")

    class Mixed:
        name = "mixed"
        def fetch(self):
            return [rec("mixed", 1), Record("mixed", "news", None, "t", None), rec("mixed", 2)]

    assert collect(conn, [Mixed()]) == {"mixed": 2}
    conn.execute("INSERT INTO sources(name, disabled) VALUES('good', 1)")
    assert "good" not in collect(conn, [Good()])


def test_apify_cap():
    conn = connect(":memory:")
    for i in range(3):
        conn.execute("INSERT INTO apify_runs(actor, run_id, status) VALUES('a', ?, 'ok')", (str(i),))
    conn.commit()

    class Client:
        calls = 0
        def run(self, *a, **k):
            Client.calls += 1
            return []

    src = ApifySource(conn, actors=["a"], client=Client(), max_runs=3)
    assert list(src.fetch()) == []
    assert Client.calls == 0


def test_apify_runs_under_cap_and_records_run():
    conn = connect(":memory:")

    class Client:
        def run(self, actor):
            return [{"text": "hello", "url": "https://fb.com/p/1", "author": "x"}]

    src = ApifySource(conn, actors=["a"], client=Client(), max_runs=3)
    out = list(src.fetch())
    assert len(out) == 1 and out[0].text == "hello"
    assert conn.execute("select count(*) from apify_runs").fetchone()[0] == 1


def test_low_yield_source_disabled():
    conn = connect(":memory:")
    for s, n_cls in [("a", 5), ("b", 5), ("c", 5), ("d", 5), ("e", 0)]:
        for i in range(5):
            insert_record(conn, rec(s, i))
        for i in range(n_cls):
            rid = conn.execute("select id from records where source=? limit 1 offset ?", (s, i)).fetchone()[0]
            conn.execute("insert into classifications(record_id, category) values(?, 'x')", (rid,))
    conn.commit()
    y = source_yield(conn, weeks=4)
    assert y["e"] == 0 and y["a"] == 1.0
    assert disable_low_yield(conn, min_records=5) == ["e"]
    assert conn.execute("select disabled from sources where name='e'").fetchone()[0] == 1
