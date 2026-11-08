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


def test_reddet_not_lifted_by_solutions_rule():
    s = Stub(payload(decision="reddet", solutions=[sol("az"), sol()]))
    v = V.validate_topic(s, mkdb(), 1)
    assert v.decision == "reddet" and s.calls == 2


def test_weekly_cap_counts_api_calls_with_retries(monkeypatch):
    conn = mkdb(20)
    monkeypatch.setattr(V.trends, "candidates", lambda c, today: list(range(1, 21)))
    s = Stub(payload(solutions=[sol(), sol()]))  # always triggers retry
    out = V.validate_week(s, conn)
    assert s.calls <= 15
    assert all(v.decision == "izle" for v in out)


def test_revalidate_window_uses_today(monkeypatch):
    from datetime import date
    conn = mkdb(2)
    conn.execute("INSERT INTO validations(topic_id, created_at) VALUES(1, '2026-01-01 10:00:00')")
    conn.execute("INSERT INTO validations(topic_id, created_at) VALUES(2, '2026-01-20 10:00:00')")
    conn.commit()
    monkeypatch.setattr(V.trends, "candidates", lambda c, today: [1, 2])
    s = Stub(payload())
    out = V.validate_week(s, conn, today=date(2026, 2, 1))
    assert [v.topic_id for v in out] == [1]


def test_numbers_without_url_marked_unverified():
    sols = [dict(sol("az"), business_model="ayda 5 AZN abunə"), sol(), sol("yuksek")]
    v = V.validate_topic(Stub(payload(solutions=sols, market_size={"estimate": "120000 istifadəçi", "url": None})), mkdb(), 1)
    assert "120000 istifadəçi" in v.unverified_claims
    assert "ayda 5 AZN abunə" in v.unverified_claims
    v = V.validate_topic(Stub(payload(solutions=sols, market_size={"estimate": "120000", "url": "https://s.az"})), mkdb(), 1)
    assert v.unverified_claims == []


class PauseStub(Stub):
    def __init__(self, pauses, text):
        super().__init__(text)
        self.pauses = pauses

    def _create(self, **kw):
        r = super()._create(**kw)
        if self.calls <= self.pauses:
            r.stop_reason = "pause_turn"
        return r


def _topic_conn(tmp_path):
    conn = db.connect(str(tmp_path / "v.db"))
    conn.execute("INSERT INTO topics(id, name) VALUES(1,'t')")
    conn.commit()
    return conn


def test_pause_turn_continues_and_counts(tmp_path):
    conn = _topic_conn(tmp_path)
    c = PauseStub(1, payload())
    v = V.validate_topic(c, conn, 1)
    assert c.calls == 2 and v.api_calls == 2


def test_pause_turn_still_paused_is_parse_error(tmp_path):
    import pytest
    conn = _topic_conn(tmp_path)
    c = PauseStub(99, payload())
    with pytest.raises(V.ValidateParseError):
        V.validate_topic(c, conn, 1)
    assert c.calls <= 3
