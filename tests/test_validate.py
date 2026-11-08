import json
from types import SimpleNamespace

from radar import db
from radar import validate as V


def dim(urls=True, score=7):
    u = "https://ex.az/a" if urls else None
    return {"score": score, "claims": [{"text": "iddia", "url": u}, {"text": "b", "url": "https://ex.az/b" if urls else ""}]}


def sol(cost="orta", title="Bot"):
    return {"title": title, "how_it_works": "x", "business_model": "B2C 2 AZN", "start_cost": cost,
            "difficulty": 2, "first_step": "y", "competitor_urls": ["https://c.az"]}


def payload(decision="gec", demand_urls=True, solutions=None, **over):
    d = {"problem": "p", "sub_pains": ["a"], "demand": dim(demand_urls), "competition": dim(),
         "willingness_to_pay": dim(), "timing": dim(), "decision": decision,
         "solutions": solutions if solutions is not None else [sol("az"), sol(), sol("yuksek")],
         "risks": ["r"], "market_size": {"estimate": "10k", "url": None}, "unverified_claims": []}
    d.update(over)
    return json.dumps(d, ensure_ascii=False)


class Stub:
    def __init__(self, *texts, fail=False):
        self.texts, self.calls, self.fail = list(texts), 0, fail
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kw):
        self.calls += 1
        if self.fail:
            raise RuntimeError("boom")
        t = self.texts[min(self.calls - 1, len(self.texts) - 1)]
        return SimpleNamespace(content=[SimpleNamespace(type="server_tool_use"),
                                        SimpleNamespace(type="text", text="```json\n" + t + "\n```")])


def mkdb(n_topics=1):
    conn = db.connect(":memory:")
    for i in range(n_topics):
        conn.execute("INSERT INTO topics(name) VALUES(?)", (f"t{i}",))
    conn.commit()
    return conn


def test_claims_without_url_dropped():
    v = V.validate_topic(Stub(payload()), mkdb(), 1)
    assert [c["url"] for c in v.competition["claims"]] == ["https://ex.az/a", "https://ex.az/b"]
    v = V.validate_topic(Stub(payload(competition={"score": 5, "claims": [{"text": "x", "url": "https://a"}, {"text": "y"}]})), mkdb(), 1)
    assert len(v.competition["claims"]) == 1


def test_no_evidence_downgrades_gec():
    v = V.validate_topic(Stub(payload(demand_urls=False)), mkdb(), 1)
    assert v.demand["claims"] == []
    assert v.decision == "izle"
    assert V.validate_topic(Stub(payload()), mkdb(), 1).decision == "gec"


def test_solutions_count_and_cheap_option():
    two = payload(solutions=[sol("az"), sol()])
    s = Stub(two)
    v = V.validate_topic(s, mkdb(), 1)
    assert s.calls == 2 and v.decision == "izle"
    s = Stub(payload(solutions=[sol(), sol(), sol("yuksek")]))
    assert V.validate_topic(s, mkdb(), 1).decision == "izle" and s.calls == 2
    s = Stub(two, payload())  # retry succeeds
    assert V.validate_topic(s, mkdb(), 1).decision == "gec" and s.calls == 2


def test_weekly_cap(monkeypatch):
    conn = mkdb(20)
    monkeypatch.setattr(V.trends, "candidates", lambda c, today: list(range(1, 21)))
    s = Stub(payload())
    out = V.validate_week(s, conn)
    assert s.calls <= 15 and len(out) == 15
    assert conn.execute("SELECT COUNT(*) FROM validations WHERE decision='gec'").fetchone()[0] == 15
    # validated within 28 days -> skipped
    s2 = Stub(payload())
    V.validate_week(s2, conn)
    assert s2.calls == 5


def test_api_errors_stop_after_three(monkeypatch):
    conn = mkdb(10)
    monkeypatch.setattr(V.trends, "candidates", lambda c, today: list(range(1, 11)))
    s = Stub(fail=True)
    assert V.validate_week(s, conn) == []
    assert s.calls == 3


def test_prompt_includes_calibration_and_evidence():
    conn = mkdb()
    conn.execute("INSERT INTO records(source,kind,url,url_norm,text,text_hash) VALUES('s','news','https://n.az/1','u','şikayət mətni','h')")
    conn.execute("INSERT INTO classifications(record_id, topic_id) VALUES(1,1)")
    p = V.build_prompt(conn, 1)
    assert "Smart Customs" in p and "https://n.az/1" in p and "şikayət mətni" in p
