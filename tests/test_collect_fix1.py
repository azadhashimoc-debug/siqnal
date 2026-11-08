from datetime import datetime

from radar.collect import collect, disable_low_yield
from radar.db import connect, insert_record
from radar.models import Record
from radar.sources.apify_src import ApifySource


def rec(src, n):
    return Record(src, "news", f"https://x.az/{src}/{n}", f"text {src} {n}", datetime(2026, 1, 1))


def _seed(conn, ys, n=5):
    for s, n_cls in ys:
        for i in range(n):
            insert_record(conn, rec(s, i))
        for i in range(n_cls):
            rid = conn.execute("select id from records where source=? limit 1 offset ?", (s, i)).fetchone()[0]
            conn.execute("insert into classifications(record_id, category) values(?, 'x')", (rid,))
    conn.commit()


def test_disable_low_yield_guards():
    conn = connect(":memory:")
    _seed(conn, [("a", 5)])
    assert disable_low_yield(conn, min_records=5) == []  # one source
    conn = connect(":memory:")
    _seed(conn, [(c, 3) for c in "abcde"])
    assert disable_low_yield(conn, min_records=5) == []  # all equal
    conn = connect(":memory:")
    _seed(conn, [("a", 5), ("b", 5), ("c", 5), ("d", 5), ("e", 0)])
    assert disable_low_yield(conn) == []  # default min record count not met
    conn.execute("INSERT INTO sources(name, disabled) VALUES('e', 1)")
    assert disable_low_yield(conn, min_records=5) == []  # disabled excluded -> 4 eligible


def test_comments_void_tags():
    from radar.sources.news_comments import NewsCommentsSource
    html = '<div class="c">one<br>two<img src="x"></div><p>page</p><div class="c">second</div>'
    src = NewsCommentsSource("n", ["https://a.az/x"], sites={"a.az": ".c"}, http_get=lambda u: html)
    assert [r.text for r in src.fetch()] == ["one two", "second"]


class Msg:
    def __init__(self, i):
        self.id, self.text, self.date = i, f"m{i}", datetime(2026, 1, 1)


class FakeTg:
    def __init__(self, msgs, fail=()):
        self.msgs, self.fail, self.calls = msgs, fail, []

    def iter_messages(self, ch, min_id=0, limit=None):
        self.calls.append((ch, min_id, limit))
        if ch in self.fail:
            raise RuntimeError("x")
        return [m for m in self.msgs.get(ch, []) if m.id > min_id]


def test_telegram_last_id_and_isolation():
    from radar.sources.telegram_src import TelegramSource
    conn = connect(":memory:")
    tg = FakeTg({"good": [Msg(1), Msg(2)]}, fail={"bad"})
    src = TelegramSource(["bad", "good"], client=tg, conn=conn)
    assert collect(conn, [src]) == {"telegram": 2}
    assert tg.calls[1] == ("good", 0, 200)
    tg.msgs["good"].append(Msg(3))
    assert collect(conn, [src]) == {"telegram": 1}
    assert tg.calls[-1] == ("good", 2, None)


def test_apify_failure_counts_and_isolated():
    conn = connect(":memory:")

    class C:
        def run(self, actor):
            if actor == "bad":
                raise RuntimeError("x")
            return [{"text": "t", "postUrl": "https://f.com/p", "id": "9"}]

    out = list(ApifySource(conn, actors=["bad", "ok"], client=C(), max_runs=5).fetch())
    assert len(out) == 1 and out[0].url.endswith("#9")
    assert conn.execute("select count(*) from apify_runs where status='failed'").fetchone()[0] == 1


def test_youtube_comments_disabled_isolated():
    from radar.sources.youtube import YoutubeSource

    class Req:
        def __init__(self, fn):
            self.fn = fn

        def execute(self):
            return self.fn()

    class YT:
        def search(self):
            class S:
                def list(s, **k):
                    return Req(lambda: {"items": [{"id": {"videoId": "v1"}}, {"id": {"videoId": "v2"}}]})
            return S()

        def commentThreads(self):
            class T:
                def list(s, videoId, **k):
                    def run():
                        if videoId == "v1":
                            raise RuntimeError("403")
                        return {"items": [{"id": "c1", "snippet": {"topLevelComment": {"snippet": {
                            "textDisplay": "hi", "publishedAt": "2026-01-01T00:00:00Z"}}}}]}
                    return Req(run)
            return T()

    assert [r.text for r in YoutubeSource(["ch"], client=YT()).fetch()] == ["hi"]
