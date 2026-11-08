"""Read-only dashboard: query layer (stdlib only) + FastAPI app factory."""
import hmac
import json
import os
import sqlite3
from datetime import date, timedelta

from radar import config

DIMENSIONS = ("demand", "competition", "willingness_to_pay", "timing")


def open_ro(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args)]


def overall(data: dict) -> float:
    return round(sum((data.get(d) or {}).get("score", 0) for d in DIMENSIONS) / len(DIMENSIONS), 1)


def overview(conn) -> dict:
    since = (date.today() - timedelta(days=7)).isoformat()
    one = lambda sql, a=(): conn.execute(sql, a).fetchone()[0]
    return {
        "records": one("SELECT COUNT(*) FROM records"),
        "records_7d": one("SELECT COUNT(*) FROM records WHERE date(created_at) >= ?", (since,)),
        "classified": one("SELECT COUNT(*) FROM classifications"),
        "topics": one("SELECT COUNT(*) FROM topics"),
        "candidates": one("SELECT COUNT(*) FROM topics WHERE candidate_at IS NOT NULL"),
        "last_record": one("SELECT MAX(created_at) FROM records"),
        "decisions": {r["decision"] or "?": r["n"] for r in _rows(
            conn, "SELECT decision, COUNT(*) n FROM validations GROUP BY decision")},
        "validations_7d": one("SELECT COUNT(*) FROM validations WHERE date(created_at) >= ?", (since,)),
        "max_validations_per_week": config.MAX_VALIDATIONS_PER_WEEK,
        "apify_runs_7d": one("SELECT COUNT(*) FROM apify_runs WHERE date(created_at) >= ?", (since,)),
        "max_apify_runs_per_week": config.MAX_APIFY_RUNS_PER_WEEK,
    }


def ideas(conn, decision=None, q=None, min_score=0.0, sort="score") -> list:
    out = []
    for r in conn.execute(
            "SELECT v.id, v.topic_id, v.idea, v.decision, v.created_at, v.data, t.name topic, "
            "COALESCE((SELECT SUM(vote) FROM votes WHERE validation_id=v.id), 0) votes "
            "FROM validations v LEFT JOIN topics t ON t.id=v.topic_id ORDER BY v.id DESC"):
        try:
            d = json.loads(r["data"] or "{}")
        except ValueError:
            d = {}
        item = {"id": r["id"], "topic": r["topic"], "idea": r["idea"], "decision": r["decision"],
                "created_at": r["created_at"], "votes": r["votes"], "score": overall(d),
                "problem": d.get("problem") or r["topic"] or "",
                "cost": (d.get("solutions") or [{}])[0].get("start_cost")}
        hay = f"{item['problem']} {item['idea']} {item['topic']}".lower()
        if decision and item["decision"] != decision:
            continue
        if q and q.lower() not in hay:
            continue
        if item["score"] < min_score:
            continue
        out.append(item)
    key = {"score": lambda x: -x["score"], "votes": lambda x: -x["votes"],
           "date": lambda x: -x["id"]}.get(sort, lambda x: -x["score"])
    return sorted(out, key=key)


def idea(conn, vid: int):
    r = conn.execute("SELECT id, topic_id, idea, decision, created_at, data FROM validations WHERE id=?",
                     (vid,)).fetchone()
    if r is None:
        return None
    try:
        d = json.loads(r["data"] or "{}")
    except ValueError:
        d = {}
    ev = _rows(conn,
               "SELECT r.text, r.url, r.source, COALESCE(r.published, r.created_at) at FROM classifications c "
               "JOIN records r ON r.id=c.record_id WHERE c.topic_id=? GROUP BY r.text_hash "
               "ORDER BY MAX(COALESCE(r.published, r.created_at)) DESC LIMIT 20", (r["topic_id"],))
    for e in ev:
        e["text"] = (e["text"] or "")[:400]
    votes = _rows(conn, "SELECT voter, vote, created_at FROM votes WHERE validation_id=?", (vid,))
    return {"id": r["id"], "decision": r["decision"], "created_at": r["created_at"],
            "score": overall(d), "data": d, "evidence": ev, "votes": votes}


def topics(conn, days: int = 14) -> list:
    start = (date.today() - timedelta(days=days - 1)).isoformat()
    spark = {}
    for r in conn.execute("SELECT topic_id, day, count FROM topic_days WHERE day >= ?", (start,)):
        spark.setdefault(r["topic_id"], {})[r["day"]] = r["count"]
    labels = [(date.today() - timedelta(days=days - 1 - i)).isoformat() for i in range(days)]
    out = []
    for t in conn.execute(
            "SELECT t.id, t.name, t.candidate_at, "
            "(SELECT COUNT(*) FROM classifications WHERE topic_id=t.id) total, "
            "(SELECT MAX(id) FROM validations WHERE topic_id=t.id) validation_id FROM topics t"):
        s = [spark.get(t["id"], {}).get(d, 0) for d in labels]
        out.append({**dict(t), "series": s, "recent": sum(s[-7:]), "prev": sum(s[:-7])})
    out.sort(key=lambda x: (-x["recent"], -x["total"]))
    return out[:100]


def sources(conn) -> list:
    since = (date.today() - timedelta(days=7)).isoformat()
    disabled = {r["name"]: r["disabled"] for r in conn.execute("SELECT name, disabled FROM sources")}
    rows = _rows(conn,
                 "SELECT source, COUNT(*) total, "
                 "SUM(CASE WHEN date(created_at) >= ? THEN 1 ELSE 0 END) last7, MAX(created_at) last_at "
                 "FROM records GROUP BY source ORDER BY total DESC", (since,))
    for r in rows:
        r["disabled"] = bool(disabled.get(r["source"], 0))
    return rows


def search(conn, q="", source=None, kind=None, limit=50) -> list:
    sql = ("SELECT r.id, r.source, r.kind, r.url, r.text, COALESCE(r.published, r.created_at) at, "
           "c.category, c.score FROM records r LEFT JOIN classifications c ON c.record_id=r.id WHERE 1=1")
    args = []
    if q:
        sql += " AND r.text LIKE ? ESCAPE '\\'"
        args.append("%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    if source:
        sql += " AND r.source=?"
        args.append(source)
    if kind:
        sql += " AND r.kind=?"
        args.append(kind)
    sql += " ORDER BY r.id DESC LIMIT ?"
    args.append(max(1, min(int(limit), 200)))
    rows = _rows(conn, sql, args)
    for r in rows:
        r["text"] = (r["text"] or "")[:400]
    return rows


def create_app(open_conn, add_vote=None, pending_votes=None, refresh=None):
    """open_conn() -> read-only sqlite connection. add_vote(vid, direction, voter) queues a vote
    (applied at the next job run); pending_votes() -> {key: dir}. refresh() reloads the volume."""
    from fastapi import Depends, FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse

    from radar.dashboard_page import PAGE

    app = FastAPI(title="Fürsət Radarı", docs_url=None, redoc_url=None, openapi_url=None)

    def auth(request: Request):
        token = os.environ.get("DASHBOARD_TOKEN", "")
        got = request.headers.get("X-Token", "")
        if not token or not hmac.compare_digest(got, token):
            raise HTTPException(status_code=401, detail="unauthorized")

    def db():
        if refresh:
            try:
                refresh()
            except Exception as e:
                print("volume reload failed:", e)
        try:
            return open_conn()
        except sqlite3.Error:
            raise HTTPException(status_code=503, detail="DB hələ yoxdur - collect işləməyib")

    def run(fn, *a, **kw):
        conn = db()
        try:
            return fn(conn, *a, **kw)
        except sqlite3.OperationalError as e:
            raise HTTPException(status_code=503, detail=f"DB hazır deyil: {e}")
        finally:
            conn.close()

    @app.get("/", response_class=HTMLResponse)
    def page():
        return PAGE

    @app.get("/api/overview", dependencies=[Depends(auth)])
    def api_overview():
        return run(overview)

    @app.get("/api/ideas", dependencies=[Depends(auth)])
    def api_ideas(decision: str = "", q: str = "", min_score: float = 0.0, sort: str = "score"):
        return run(ideas, decision or None, q or None, min_score, sort)

    @app.get("/api/ideas/{vid}", dependencies=[Depends(auth)])
    def api_idea(vid: int):
        r = run(idea, vid)
        if r is None:
            raise HTTPException(status_code=404, detail="tapılmadı")
        return r

    @app.get("/api/topics", dependencies=[Depends(auth)])
    def api_topics():
        return run(topics)

    @app.get("/api/sources", dependencies=[Depends(auth)])
    def api_sources():
        return run(sources)

    @app.get("/api/search", dependencies=[Depends(auth)])
    def api_search(q: str = "", source: str = "", kind: str = "", limit: int = 50):
        return run(search, q, source or None, kind or None, limit)

    @app.get("/api/votes/pending", dependencies=[Depends(auth)])
    def api_pending():
        return dict(pending_votes()) if pending_votes else {}

    @app.post("/api/ideas/{vid}/vote/{direction}", dependencies=[Depends(auth)])
    def api_vote(vid: int, direction: str):
        if direction not in ("up", "down") or add_vote is None:
            raise HTTPException(status_code=400, detail="yanlış səs")
        if run(lambda c: c.execute("SELECT 1 FROM validations WHERE id=?", (vid,)).fetchone()) is None:
            raise HTTPException(status_code=404, detail="tapılmadı")
        add_vote(vid, direction, "dashboard")
        return {"ok": True, "note": "Səs növbəti işləmədə (≤3 saat) tətbiq olunacaq"}

    return app
