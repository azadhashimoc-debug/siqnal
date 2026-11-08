import json

import pytest

from radar import dashboard as D
from radar import db
from tests.test_report import mk
from dataclasses import asdict


@pytest.fixture
def conn(tmp_path):
    p = tmp_path / "r.db"
    c = db.connect(str(p))
    c.execute("INSERT INTO topics(name) VALUES('Növbə')")
    c.execute("INSERT INTO records(source,kind,url,url_norm,text,text_hash,published) VALUES"
              "('Oxu.az','news','https://a.az/1','a.az/1','Növbə çox uzundur','h1','2026-11-01')")
    c.execute("INSERT INTO classifications(record_id,category,label,score,topic_id) VALUES(1,'PROBLEM_SIKAYET','n',70,1)")
    for dec, sc in (("gec", 8), ("izle", 5)):
        c.execute("INSERT INTO validations(topic_id,idea,result,decision,data) VALUES(1,?,?,?,?)",
                  (f"idea-{dec}", dec, dec, json.dumps(asdict(mk(score=sc, decision=dec)))))
    c.execute("INSERT INTO votes(validation_id,voter,vote) VALUES(1,'a',1)")
    c.commit()
    c.close()
    return D.open_ro(str(p))


def test_overview(conn):
    o = D.overview(conn)
    assert o["records"] == 1 and o["decisions"] == {"gec": 1, "izle": 1}


def test_ideas_filter_sort(conn):
    assert [i["id"] for i in D.ideas(conn)] == [1, 2]  # by score desc
    assert [i["id"] for i in D.ideas(conn, decision="izle")] == [2]
    assert D.ideas(conn, min_score=7)[0]["id"] == 1 and len(D.ideas(conn, min_score=7)) == 1
    assert D.ideas(conn, q="zzz") == []
    assert D.ideas(conn)[0]["votes"] == 1


def test_idea_detail(conn):
    r = D.idea(conn, 1)
    assert r["data"]["problem"] == "Növbə problemi" and r["evidence"] and D.idea(conn, 99) is None


def test_topics_sources_search(conn):
    assert D.topics(conn)[0]["name"] == "Növbə" and len(D.topics(conn)[0]["series"]) == 14
    assert D.sources(conn)[0]["source"] == "Oxu.az"
    assert len(D.search(conn, "uzun")) == 1 and D.search(conn, "%") == []


def test_readonly(conn):
    import sqlite3
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("DELETE FROM records")


def test_app_auth_and_vote(tmp_path, monkeypatch):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    p = tmp_path / "a.db"
    c = db.connect(str(p))
    c.execute("INSERT INTO validations(topic_id,idea,decision,data) VALUES(1,'x','gec','{}')")
    c.commit(); c.close()
    queued = {}
    monkeypatch.setenv("DASHBOARD_TOKEN", "s3")
    app = D.create_app(lambda: D.open_ro(str(p)), add_vote=lambda v, d, w: queued.update({f"{v}:{w}": d}),
                       pending_votes=lambda: queued)
    t = TestClient(app)
    assert t.get("/").status_code == 200
    assert t.get("/api/overview").status_code == 401
    h = {"X-Token": "wrong"}
    assert t.get("/api/overview", headers=h).status_code == 401
    h = {"X-Token": "s3"}
    assert t.get("/api/overview", headers=h).status_code == 200
    assert t.post("/api/ideas/1/vote/up", headers=h).status_code == 200 and queued == {"1:dashboard": "up"}
    assert t.post("/api/ideas/9/vote/up", headers=h).status_code == 404
    assert t.post("/api/ideas/1/vote/sideways", headers=h).status_code == 400
    monkeypatch.delenv("DASHBOARD_TOKEN")
    assert t.get("/api/overview", headers={"X-Token": ""}).status_code == 401
