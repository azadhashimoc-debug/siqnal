from radar import db, bot, report
from radar import validate as V


def mk(score=7, decision="gec", title="Online növbə SaaS"):
    dim = {"score": score, "claims": [{"text": "iddia", "url": "https://ex.az/a"}]}
    sols = [V.Solution(title, "necə", "B2B", c, 2, "ilk", ["https://c.az"]) for c in ("orta", "az", "yuksek")]
    sols[1].title = "Klinikalara növbə xidməti"
    return V.Validation(topic_id=1, problem="Növbə problemi", sub_pains=["a"], demand=dim,
                        competition=dict(dim), willingness_to_pay=dict(dim), timing=dict(dim),
                        decision=decision, solutions=sols, risks=["risk1"],
                        market_size={"estimate": "10k", "url": None}, unverified_claims=["10k bazar"])


def test_report_empty_week():
    assert report.weekly_message([]) == "Bu həftə güclü fürsət yoxdur."
    assert report.weekly_message([(1, mk(decision="izle"))]) == "Bu həftə güclü fürsət yoxdur."


def test_max_five():
    items = [(i, mk(score=i)) for i in range(1, 9)]
    msg = report.weekly_message(items)
    assert msg.count("\n") + 1 - msg.count("\n\n") >= 5
    assert sum(1 for i in range(1, 9) if f"{i}-" in msg) == 5
    assert "8-" in msg and "4-" in msg and "3-" not in msg  # top by score
    assert len(msg) <= 4096


def test_message_truncates():
    v = mk()
    v.problem = "x" * 2000
    assert len(report.weekly_message([(i, v) for i in range(1, 6)])) <= 4096


def test_render_sections():
    md = report.render_report(mk(), [("sübut mətni", "https://e.az/1")])
    for h in ("Problem", "Kanıtlar", "Talep", "Ödəmə gücü", "Həll yolları", "Risklər", "Doğrulanmadı"):
        assert h in md
    assert "https://e.az/1" in md and "10k bazar" in md


def test_vote_callback_saves():
    conn = db.connect(":memory:")
    assert bot.handle_callback(conn, "vote:3:up", "u1") is False  # unknown id
    conn.execute("INSERT INTO validations(id, topic_id, idea) VALUES(3, NULL, 'x')")
    assert bot.handle_callback(conn, "vote:3:up", "u1") is True
    assert conn.execute("SELECT vote FROM votes WHERE validation_id=3").fetchall() == [(1,)]
    assert bot.handle_callback(conn, "vote:3:down", "u1") is True  # replaces
    assert conn.execute("SELECT vote FROM votes WHERE validation_id=3").fetchall() == [(-1,)]
    for bad in ("vote:3:sideways", "vote:x:up", "foo", "vote:3", ""):
        assert bot.handle_callback(conn, bad, "u1") is False


def test_send_weekly(tmp_path):
    conn = db.connect(":memory:")
    calls = []
    bot.send_weekly(conn, lambda m, p, files=None: calls.append((m, p, files)), 42,
                    [(5, mk())], str(tmp_path))
    assert [c[0] for c in calls] == ["sendDocument", "sendMessage"]
    assert any(tmp_path.glob("5-*.md"))
    msg = calls[1][1]
    kb = msg["reply_markup"]["inline_keyboard"][0]
    assert [b["callback_data"] for b in kb] == ["vote:5:up", "vote:5:down"]
    assert "parse_mode" not in msg
