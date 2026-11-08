import json
from types import SimpleNamespace

from radar import db
from radar.classify import classify, classify_pending
from radar.models import Record
from radar.prefilter import prefilter
from datetime import datetime


class Stub:
    def __init__(self, text):
        self.messages = SimpleNamespace(create=lambda **kw: SimpleNamespace(
            content=[SimpleNamespace(text=text)]))


def good(**over):
    d = dict(category="PROBLEM_SIKAYET", is_problem=True, affected_group="sürücülər",
             urgency=4, willingness_to_pay=3, score=70, topic_label="Yol tıxacı", evidence="x")
    d.update(over)
    return json.dumps(d)


def test_prefilter_suffix():
    assert prefilter("çörək bahalaşacaq")
    assert not prefilter("bu gün hava gözəldir")


def test_classify_ok_and_fenced():
    assert classify(Stub(good()), "t").score == 70
    assert classify(Stub("```json\n" + good() + "\n```"), "t").topic_label == "Yol tıxacı"


def test_score_out_of_range_rejected():
    assert classify(Stub(good(score=140)), "t") is None


def test_missing_field_and_bad_category():
    assert classify(Stub(json.dumps({"category": "PROBLEM_SIKAYET"})), "t") is None
    assert classify(Stub(good(category="X")), "t") is None


def test_classify_bad_json_marks_failed(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.insert_record(conn, Record("s", "news", "http://a", "çörək bahalaşacaq", datetime.now()))
    db.insert_record(conn, Record("s", "news", "http://b", "hava gözəldir", datetime.now()))
    assert classify_pending(conn, Stub("not json")) == 0
    st = dict(conn.execute("SELECT url, status FROM records").fetchall())
    assert st == {"http://a": "classify_failed", "http://b": "prefiltered_out"}


def test_classify_pending_success(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    db.insert_record(conn, Record("s", "news", "http://a", "çörək bahalaşacaq", datetime.now()))
    assert classify_pending(conn, Stub(good())) == 1
    assert conn.execute("SELECT status FROM records").fetchone()[0] == "classified"
    assert conn.execute("SELECT category,label,score FROM classifications").fetchone() == ("PROBLEM_SIKAYET", "Yol tıxacı", 70)


class Boom:
    def __init__(self):
        self.calls = 0

        def create(**kw):
            self.calls += 1
            raise RuntimeError("rate limit")
        self.messages = SimpleNamespace(create=create)


def _seed(conn, n):
    for i in range(n):
        db.insert_record(conn, Record("s", "news", f"http://u{i}", f"çörək bahalaşacaq {i}", datetime.now()))


def test_api_error_leaves_row_new(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    _seed(conn, 1)
    assert classify_pending(conn, Boom()) == 0
    assert conn.execute("SELECT status FROM records").fetchone()[0] == "new"


def test_three_consecutive_api_errors_stop_batch(tmp_path):
    conn = db.connect(str(tmp_path / "t.db"))
    _seed(conn, 6)
    c = Boom()
    classify_pending(conn, c)
    assert c.calls == 3
    assert conn.execute("SELECT COUNT(*) FROM records WHERE status='new'").fetchone()[0] == 6


def test_guven_and_bilgi_keywords():
    assert prefilter("saxta makler 100 manat beh pulu aldı")
    assert prefilter("icbari sığorta ilə pulsuz xidmətlər")


def test_prefilter_dotted_capital_i():
    assert prefilter("İcbari sığorta")
