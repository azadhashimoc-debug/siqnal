import json
import sqlite3
from dataclasses import asdict
from datetime import date

import pytest

from radar import bot, db, runner
from radar import dashboard as D
from tests.test_report import mk

TODAY = date(2026, 11, 8)


def seed(path):
    c = db.connect(str(path))
    c.execute("INSERT INTO topics(name, candidate_at) VALUES('Növbə', '2026-11-05')")
    c.execute("INSERT INTO records(source,kind,url,url_norm,text,text_hash,published,created_at) VALUES"
              "('Oxu.az','news','https://a.az/1','a.az/1','Növbə çox uzundur','h1','2026-11-06','2026-11-06'),"
              "('APA','comment','https://b.az/1','b.az/1','100% yalan_xəbər','h2','2026-11-07','2026-11-07')")
    c.execute("INSERT INTO classifications(record_id,category,label,score,topic_id) VALUES(1,'PROBLEM_SIKAYET','n',70,1)")
    c.execute("INSERT INTO topic_days(topic_id,day,count) VALUES(1,'2026-11-06',1)")
    for dec, sc in (("gec", 8), ("izle", 5)):
        c.execute("INSERT INTO validations(topic_id,idea,result,decision,data) VALUES(1,?,?,?,?)",
                  (f"idea-{dec}", dec, dec, json.dumps(asdict(mk(score=sc, decision=dec)))))
    c.execute("INSERT INTO votes(validation_id,voter,vote) VALUES(1,'a',1)")
    c.commit()
    c.close()


@pytest.fixture
def path(tmp_path):
    p = tmp_path / "r.db"
    seed(p)
    return p


@pytest.fixture
def conn(path):
    c = D.open_ro(str(path))
    yield c
    c.close()


def test_overview(conn):
    o = D.overview(conn, today=TODAY)
    assert o["records"] == 2 and o["unclassified"] == 1 and o["decisions"] == {"gec": 1, "izle": 1}
    assert len(o["daily"]) == 30 and o["daily"][-3] == {"day": "2026-11-06", "news": 1, "comment": 0}
    assert o["categories"][0]["category"] == "PROBLEM_SIKAYET"
    assert o["top_ideas"][0]["id"] == 1 and o["top_topics"][0]["name"] == "Növbə"
    assert o["last_collect"] is None


def test_ideas_filter_sort(conn):
    assert [i["id"] for i in D.ideas(conn)] == [1, 2]
    assert [i["id"] for i in D.ideas(conn, decision="izle")] == [2]
    assert [i["id"] for i in D.ideas(conn, min_score=7)] == [1]
    assert D.ideas(conn, q="zzz") == []
    assert D.ideas(conn)[0]["votes"] == 1 and D.ideas(conn)[0]["status"] == "yeni"
    assert [i["id"] for i in D.ideas(conn, cost="az")] == [1, 2] and D.ideas(conn, cost="nope") == []
    assert D.ideas(conn)[0]["dims"]["demand"] == 8


def test_pending_status_overlay(conn):
    q = {"status:2": json.dumps({"status": "basladim", "note": "zəng etdim"}), "2:dashboard": "up",
         "status:1": "garbage"}
    rows = D.ideas(conn, status="basladim", pending=q)
    assert [r["id"] for r in rows] == [2] and rows[0]["pending"] and rows[0]["pending_vote"] == "up"
    assert D.ideas(conn, q="zəng", pending=q)[0]["id"] == 2


def test_idea_detail(conn):
    r = D.idea(conn, 1)
    assert r["data"]["problem"] == "Növbə problemi" and r["evidence"] and r["vote_sum"] == 1
    assert r["next_id"] == 2 and r["prev_id"] is None and [h["id"] for h in r["history"]] == [2]
    assert D.idea(conn, 99) is None


def test_idea_markdown(conn):
    name, md = D.idea_markdown(conn, 1)
    assert name.startswith("1-") and "## Həll yolları" in md and D.idea_markdown(conn, 99) is None


def test_csv(conn):
    out = D.ideas_csv(D.ideas(conn))
    assert out.startswith("﻿id,problem") and "Növbə problemi" in out


def test_topics_and_topic(conn):
    t = D.topics(conn, today=TODAY)[0]
    assert t["name"] == "Növbə" and t["recent"] == 1 and t["growth"] is None and len(t["series"]) == 14
    assert D.topics(conn, today=TODAY, q="yox") == [] and len(D.topics(conn, only_candidates=True)) == 1
    d = D.topic(conn, 1, today=TODAY)
    assert len(d["series"]) == 30 and d["records"][0]["source"] == "Oxu.az" and len(d["validations"]) == 2
    assert D.topic(conn, 9) is None


def test_sources(conn):
    s = {r["source"]: r for r in D.sources(conn, today=TODAY)}
    assert s["Oxu.az"]["signal_rate"] == 100 and s["APA"]["signal_rate"] == 0 and len(s["APA"]["series"]) == 14


def test_search(conn):
    assert D.search(conn, "uzun")["total"] == 1
    assert D.search(conn, "%")["total"] == 1  # literal %, not wildcard
    assert D.search(conn, "_")["total"] == 1
    assert D.search(conn, category="_none")["rows"][0]["source"] == "APA"
    assert D.search(conn, category="PROBLEM_SIKAYET", min_score=60)["total"] == 1
    assert D.search(conn, min_score=80)["total"] == 0
    assert D.search(conn, source="APA", kind="comment")["total"] == 1
    p = D.search(conn, limit=1, offset=1)
    assert p["total"] == 2 and len(p["rows"]) == 1


def test_readonly(conn):
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM records")


def test_drain_status(path):
    c = db.connect(str(path))
    n = bot.drain_status(c, {"status:1": json.dumps({"status": "baxildi", "note": "ok"}),
                             "status:99": json.dumps({"status": "baxildi"}),
                             "status:2": json.dumps({"status": "bad"}), "1:7": "up"})
    assert n == 1
    bot.drain_status(c, {"status:1": json.dumps({"status": "imtina", "note": ""})})
    assert c.execute("SELECT status, note FROM idea_status").fetchall() == [("imtina", "")]


def test_runner_drains_status_and_pops(path):
    class Vol:
        def reload(self): pass
        def commit(self): pass
    q = {"status:1": json.dumps({"status": "basladim", "note": "x"})}
    runner.run_locked(Vol(), q, {}, 100, lambda: db.connect(str(path)), lambda conn: None)
    assert q == {}
    c = D.open_ro(str(path))
    assert D.statuses(c)[1]["status"] == "basladim"


def test_record_run(path):
    from radar import pipeline
    c = db.connect(str(path))
    pipeline.record_run(c, "last_collect", {"result": {"rss": 3}})
    c.close()
    c = D.open_ro(str(path))
    assert D.overview(c)["last_collect"]["result"] == {"rss": 3}


def test_app(path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    queue, started, state = {}, [], {"running": None}
    monkeypatch.setenv("DASHBOARD_TOKEN", "s3")
    app = D.create_app(lambda: D.open_ro(str(path)), queue=queue, run_state=lambda: state,
                       trigger=started.append)
    t = TestClient(app)
    assert t.get("/").status_code == 200
    assert t.get("/api/overview").status_code == 401
    assert t.get("/api/overview", headers={"X-Token": "wrong"}).status_code == 401
    h = {"X-Token": "s3"}
    o = t.get("/api/overview", headers=h).json()
    assert o["can_trigger"] and o["running_since"] is None
    assert t.get("/api/meta", headers=h).json()["sources"] == ["APA", "Oxu.az"]
    assert t.post("/api/ideas/1/vote/up", headers=h).status_code == 200 and queue == {"1:dashboard": "up"}
    assert t.post("/api/ideas/9/vote/up", headers=h).status_code == 404
    assert t.post("/api/ideas/1/vote/sideways", headers=h).status_code == 400
    assert t.post("/api/ideas/1/status", headers=h, json={"status": "baxildi", "note": "n"}).status_code == 200
    assert json.loads(queue["status:1"]) == {"status": "baxildi", "note": "n"}
    assert t.post("/api/ideas/1/status", headers=h, json={"status": "hack"}).status_code == 400
    assert t.get("/api/ideas?status=baxildi", headers=h).json()[0]["id"] == 1
    r = t.get("/api/ideas.csv", headers=h)
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    assert t.get("/api/ideas/1/report.md", headers=h).status_code == 200
    assert t.get("/api/topics/1", headers=h).status_code == 200
    assert t.get("/api/search?q=uzun", headers=h).json()["total"] == 1
    assert t.post("/api/run/collect", headers=h).status_code == 200 and started == ["collect"]
    assert t.post("/api/run/rm", headers=h).status_code == 400
    state["running"] = 123
    assert t.post("/api/run/weekly", headers=h).status_code == 409
    monkeypatch.delenv("DASHBOARD_TOKEN")
    assert t.get("/api/overview", headers={"X-Token": ""}).status_code == 401
