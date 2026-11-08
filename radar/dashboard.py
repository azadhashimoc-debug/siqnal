"""Web dashboard: read-only query layer (stdlib only) + FastAPI app factory.

The DB is never written from here (one SQLite writer: the locked jobs). User actions
(votes, idea status/notes) go into a queue (modal.Dict) that the next job run drains;
until then the dashboard overlays queued values so changes show up immediately.
"""
import csv
import hmac
import io
import json
import os
import sqlite3
import time
from datetime import date, timedelta

from radar import config
from radar.bot import STATUSES, parse_status

DIMENSIONS = ("demand", "competition", "willingness_to_pay", "timing")
CATEGORIES = ("PROBLEM_SIKAYET", "REGULYASIYA_QANUN", "BIZNES_TREND", "GUVEN_DELEDUZLUQ", "BILGI_BOSLUGU")
_DAY = "date(COALESCE(r.published, r.created_at))"


def open_ro(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _rows(conn, sql, args=()):
    return [dict(r) for r in conn.execute(sql, args)]


def _has(conn, table: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def _days(n: int, today=None) -> list:
    today = today or date.today()
    return [(today - timedelta(days=n - 1 - i)).isoformat() for i in range(n)]


def overall(data: dict) -> float:
    return round(sum((data.get(d) or {}).get("score", 0) for d in DIMENSIONS) / len(DIMENSIONS), 1)


def _load(raw) -> dict:
    try:
        d = json.loads(raw or "{}")
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


def _state(conn, name):
    r = conn.execute("SELECT value FROM source_state WHERE name=?", (name,)).fetchone()
    return _load(r[0]) if r else None


def statuses(conn, pending=None) -> dict:
    """{validation_id: {"status", "note", "updated_at", "pending"}} with queued actions overlaid."""
    out = {}
    if _has(conn, "idea_status"):
        for r in conn.execute("SELECT validation_id, status, note, updated_at FROM idea_status"):
            out[r["validation_id"]] = {"status": r["status"], "note": r["note"] or "",
                                       "updated_at": r["updated_at"], "pending": False}
    for key, value in (pending or {}).items():
        kind, _, vid = str(key).partition(":")
        p = parse_status(value)
        if kind == "status" and vid.isdigit() and p:
            out[int(vid)] = {"status": p[0], "note": p[1], "updated_at": None, "pending": True}
    return out


def pending_votes(pending, vid: int):
    v = (pending or {}).get(f"{vid}:dashboard")
    return v if v in ("up", "down") else None


# ---------- overview ----------

def overview(conn, pending=None, today=None) -> dict:
    today = today or date.today()
    since = (today - timedelta(days=7)).isoformat()
    one = lambda sql, a=(): conn.execute(sql, a).fetchone()[0]
    days = _days(30, today)
    daily = {d: {"news": 0, "comment": 0} for d in days}
    for r in conn.execute(f"SELECT {_DAY} d, r.kind, COUNT(*) n FROM records r WHERE {_DAY} >= ? "
                          f"GROUP BY d, r.kind", (days[0],)):
        if r["d"] in daily and r["kind"] in daily[r["d"]]:
            daily[r["d"]][r["kind"]] = r["n"]
    cats = _rows(conn, f"SELECT c.category, COUNT(*) n, ROUND(AVG(c.score)) avg FROM classifications c "
                       f"JOIN records r ON r.id=c.record_id WHERE {_DAY} >= ? AND c.category IS NOT NULL "
                       f"AND c.category != '' GROUP BY c.category ORDER BY n DESC", (days[0],))
    st = statuses(conn, pending)
    st_count = {}
    for v in st.values():
        st_count[v["status"]] = st_count.get(v["status"], 0) + 1
    return {
        "records": one("SELECT COUNT(*) FROM records"),
        "records_7d": one("SELECT COUNT(*) FROM records WHERE date(created_at) >= ?", (since,)),
        "classified": one("SELECT COUNT(*) FROM classifications"),
        "unclassified": one("SELECT COUNT(*) FROM records r WHERE NOT EXISTS "
                            "(SELECT 1 FROM classifications c WHERE c.record_id=r.id)"),
        "topics": one("SELECT COUNT(*) FROM topics"),
        "candidates": one("SELECT COUNT(*) FROM topics WHERE candidate_at IS NOT NULL"),
        "last_record": one("SELECT MAX(created_at) FROM records"),
        "decisions": {r["decision"] or "?": r["n"] for r in _rows(
            conn, "SELECT decision, COUNT(*) n FROM validations GROUP BY decision")},
        "validations_7d": one("SELECT COUNT(*) FROM validations WHERE date(created_at) >= ?", (since,)),
        "max_validations_per_week": config.MAX_VALIDATIONS_PER_WEEK,
        "apify_runs_7d": one("SELECT COUNT(*) FROM apify_runs WHERE date(created_at) >= ?", (since,)),
        "max_apify_runs_per_week": config.MAX_APIFY_RUNS_PER_WEEK,
        "daily": [{"day": d, **daily[d]} for d in days],
        "categories": cats,
        "statuses": st_count,
        "top_ideas": ideas(conn, decision="gec", pending=pending)[:5],
        "top_topics": topics(conn, today=today)[:5],
        "last_collect": _state(conn, "last_collect"),
        "last_weekly": _state(conn, "last_weekly"),
        "pending_actions": len(pending or {}),
    }


# ---------- ideas ----------

def ideas(conn, decision=None, q=None, min_score=0.0, sort="score", status=None, cost=None, pending=None) -> list:
    st = statuses(conn, pending)
    out = []
    for r in conn.execute(
            "SELECT v.id, v.topic_id, v.idea, v.decision, v.created_at, v.data, t.name topic, "
            "COALESCE((SELECT SUM(vote) FROM votes WHERE validation_id=v.id), 0) votes "
            "FROM validations v LEFT JOIN topics t ON t.id=v.topic_id ORDER BY v.id DESC"):
        d = _load(r["data"])
        sols = d.get("solutions") or []
        s = st.get(r["id"], {})
        item = {"id": r["id"], "topic_id": r["topic_id"], "topic": r["topic"], "idea": r["idea"],
                "decision": r["decision"], "created_at": r["created_at"], "votes": r["votes"],
                "score": overall(d), "problem": d.get("problem") or r["topic"] or "",
                "cost": (sols[0] or {}).get("start_cost") if sols else None,
                "costs": sorted({x.get("start_cost") for x in sols if isinstance(x, dict) and x.get("start_cost")}),
                "dims": {k: (d.get(k) or {}).get("score") for k in DIMENSIONS},
                "status": s.get("status", "yeni"), "note": s.get("note", ""),
                "pending": s.get("pending", False), "pending_vote": pending_votes(pending, r["id"])}
        hay = f"{item['problem']} {item['idea']} {item['topic']} {item['note']}".lower()
        if decision and item["decision"] != decision:
            continue
        if status and item["status"] != status:
            continue
        if cost and cost not in item["costs"]:
            continue
        if q and q.lower() not in hay:
            continue
        if item["score"] < min_score:
            continue
        out.append(item)
    key = {"score": lambda x: (-x["score"], -x["id"]), "votes": lambda x: (-x["votes"], -x["id"]),
           "date": lambda x: -x["id"], "demand": lambda x: (-(x["dims"]["demand"] or 0), -x["id"])}
    return sorted(out, key=key.get(sort, key["score"]))


def ideas_csv(rows) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "problem", "idea", "topic", "decision", "score", *DIMENSIONS, "cost", "votes",
                "status", "note", "created_at"])
    for r in rows:
        w.writerow([r["id"], r["problem"], r["idea"], r["topic"], r["decision"], r["score"],
                    *(r["dims"][k] for k in DIMENSIONS), r["cost"], r["votes"], r["status"], r["note"],
                    r["created_at"]])
    return "﻿" + buf.getvalue()  # BOM: Excel opens UTF-8 (ə, ş) correctly


def idea(conn, vid: int, pending=None):
    r = conn.execute("SELECT v.id, v.topic_id, v.idea, v.decision, v.created_at, v.data, t.name topic "
                     "FROM validations v LEFT JOIN topics t ON t.id=v.topic_id WHERE v.id=?", (vid,)).fetchone()
    if r is None:
        return None
    d = _load(r["data"])
    ev = _rows(conn,
               "SELECT r.text, r.url, r.source, COALESCE(r.published, r.created_at) at FROM classifications c "
               "JOIN records r ON r.id=c.record_id WHERE c.topic_id=? GROUP BY r.text_hash "
               "ORDER BY MAX(COALESCE(r.published, r.created_at)) DESC LIMIT 20", (r["topic_id"],))
    for e in ev:
        e["text"] = (e["text"] or "")[:400]
    votes = _rows(conn, "SELECT voter, vote, created_at FROM votes WHERE validation_id=?", (vid,))
    history = _rows(conn, "SELECT id, decision, created_at FROM validations WHERE topic_id=? AND id != ? "
                          "ORDER BY id DESC", (r["topic_id"], vid))
    for h in history:
        h["score"] = overall(_load(conn.execute("SELECT data FROM validations WHERE id=?",
                                                (h["id"],)).fetchone()[0]))
    s = statuses(conn, pending).get(vid, {})
    ids = [x[0] for x in conn.execute("SELECT id FROM validations ORDER BY id")]
    i = ids.index(vid)
    return {"id": r["id"], "topic_id": r["topic_id"], "topic": r["topic"], "decision": r["decision"],
            "created_at": r["created_at"], "score": overall(d), "data": d, "evidence": ev, "votes": votes,
            "vote_sum": sum(v["vote"] for v in votes), "pending_vote": pending_votes(pending, vid),
            "status": s.get("status", "yeni"), "note": s.get("note", ""), "status_pending": s.get("pending", False),
            "status_updated": s.get("updated_at"), "history": history,
            "prev_id": ids[i - 1] if i > 0 else None, "next_id": ids[i + 1] if i + 1 < len(ids) else None}


def idea_markdown(conn, vid: int):
    from radar import report
    from radar.validate import Solution, Validation
    r = conn.execute("SELECT topic_id, data FROM validations WHERE id=?", (vid,)).fetchone()
    if r is None:
        return None
    d = _load(r["data"])
    try:
        fields = set(Validation.__dataclass_fields__)
        sfields = set(Solution.__dataclass_fields__)
        d["solutions"] = [Solution(**{k: v for k, v in s.items() if k in sfields}) for s in d.get("solutions") or []]
        v = Validation(**{k: v for k, v in d.items() if k in fields})
    except TypeError:
        return None
    ev = conn.execute("SELECT r.text, r.url FROM classifications c JOIN records r ON r.id=c.record_id "
                      "WHERE c.topic_id=? GROUP BY r.text_hash LIMIT 20", (r["topic_id"],)).fetchall()
    return report.report_name(vid, v), report.render_report(v, [tuple(e) for e in ev])


# ---------- topics ----------

def topics(conn, days: int = 14, today=None, q=None, only_candidates=False) -> list:
    labels = _days(days, today)
    spark = {}
    for r in conn.execute("SELECT topic_id, day, count FROM topic_days WHERE day >= ?", (labels[0],)):
        spark.setdefault(r["topic_id"], {})[r["day"]] = r["count"]
    out = []
    for t in conn.execute(
            "SELECT t.id, t.name, t.candidate_at, "
            "(SELECT COUNT(*) FROM classifications WHERE topic_id=t.id) total, "
            "(SELECT MAX(id) FROM validations WHERE topic_id=t.id) validation_id FROM topics t"):
        if q and q.lower() not in (t["name"] or "").lower():
            continue
        if only_candidates and not t["candidate_at"]:
            continue
        s = [spark.get(t["id"], {}).get(d, 0) for d in labels]
        recent, prev = sum(s[-7:]), sum(s[:-7])
        growth = None if prev == 0 else round(recent / prev, 1)
        out.append({**dict(t), "series": s, "recent": recent, "prev": prev, "growth": growth})
    out.sort(key=lambda x: (-x["recent"], -x["total"]))
    return out[:200]


def topic(conn, tid: int, today=None):
    t = conn.execute("SELECT id, name, summary, candidate_at, created_at FROM topics WHERE id=?", (tid,)).fetchone()
    if t is None:
        return None
    labels = _days(30, today)
    by_day = {r["day"]: dict(r) for r in conn.execute(
        "SELECT day, count, distinct_voices, distinct_sources, avg_score FROM topic_days "
        "WHERE topic_id=? AND day >= ?", (tid, labels[0]))}
    series = [{"day": d, "count": (by_day.get(d) or {}).get("count", 0)} for d in labels]
    recs = _rows(conn, "SELECT r.id, r.source, r.kind, r.url, r.text, COALESCE(r.published, r.created_at) at, "
                       "c.category, c.score FROM classifications c JOIN records r ON r.id=c.record_id "
                       "WHERE c.topic_id=? ORDER BY at DESC, r.id DESC LIMIT 100", (tid,))
    for r in recs:
        r["text"] = (r["text"] or "")[:400]
    srcs = _rows(conn, "SELECT r.source, COUNT(*) n FROM classifications c JOIN records r ON r.id=c.record_id "
                       "WHERE c.topic_id=? GROUP BY r.source ORDER BY n DESC", (tid,))
    vals = _rows(conn, "SELECT id, decision, created_at, data FROM validations WHERE topic_id=? ORDER BY id DESC", (tid,))
    for v in vals:
        v["score"] = overall(_load(v.pop("data")))
    return {**dict(t), "series": series, "records": recs, "sources": srcs, "validations": vals}


# ---------- sources & search ----------

def sources(conn, today=None) -> list:
    today = today or date.today()
    since = (today - timedelta(days=7)).isoformat()
    labels = _days(14, today)
    disabled = {r["name"]: r["disabled"] for r in conn.execute("SELECT name, disabled FROM sources")}
    rows = _rows(conn,
                 "SELECT r.source, COUNT(*) total, "
                 "SUM(CASE WHEN date(r.created_at) >= ? THEN 1 ELSE 0 END) last7, MAX(r.created_at) last_at, "
                 "COUNT(c.id) classified, ROUND(AVG(c.score)) avg_score "
                 "FROM records r LEFT JOIN classifications c ON c.record_id=r.id "
                 "GROUP BY r.source ORDER BY total DESC", (since,))
    spark = {}
    for r in conn.execute("SELECT source, date(created_at) d, COUNT(*) n FROM records WHERE date(created_at) >= ? "
                          "GROUP BY source, d", (labels[0],)):
        spark.setdefault(r["source"], {})[r["d"]] = r["n"]
    for r in rows:
        r["disabled"] = bool(disabled.get(r["source"], 0))
        r["series"] = [spark.get(r["source"], {}).get(d, 0) for d in labels]
        r["signal_rate"] = round(100 * r["classified"] / r["total"]) if r["total"] else 0
    return rows


def search(conn, q="", source=None, kind=None, category=None, min_score=None, limit=50, offset=0) -> dict:
    where, args = " WHERE 1=1", []
    if q:
        where += " AND r.text LIKE ? ESCAPE '\\'"
        args.append("%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%")
    if source:
        where += " AND r.source=?"
        args.append(source)
    if kind:
        where += " AND r.kind=?"
        args.append(kind)
    if category == "_none":
        where += " AND c.id IS NULL"
    elif category:
        where += " AND c.category=?"
        args.append(category)
    if min_score:
        where += " AND c.score >= ?"
        args.append(float(min_score))
    base = " FROM records r LEFT JOIN classifications c ON c.record_id=r.id LEFT JOIN topics t ON t.id=c.topic_id"
    total = conn.execute("SELECT COUNT(*)" + base + where, args).fetchone()[0]
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    rows = _rows(conn, "SELECT r.id, r.source, r.kind, r.url, r.text, COALESCE(r.published, r.created_at) at, "
                       "c.category, c.score, c.topic_id, t.name topic" + base + where +
                 " ORDER BY r.id DESC LIMIT ? OFFSET ?", args + [limit, offset])
    for r in rows:
        r["text"] = (r["text"] or "")[:400]
    return {"rows": rows, "total": total, "limit": limit, "offset": offset}


# ---------- app ----------

def create_app(open_conn, queue=None, refresh=None, run_state=None, trigger=None):
    """open_conn() -> read-only sqlite connection.
    queue: dict-like action queue (modal.Dict in prod), drained by the next locked job.
    refresh(): reload the volume. run_state() -> {"running": ts|None}. trigger(job) starts a job."""
    from fastapi import Body, Depends, FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, PlainTextResponse, Response

    from radar.dashboard_page import PAGE

    app = FastAPI(title="Fürsət Radarı", docs_url=None, redoc_url=None, openapi_url=None)
    last_refresh = [0.0]

    def auth(request: Request):
        token = os.environ.get("DASHBOARD_TOKEN", "")
        got = request.headers.get("X-Token", "")
        if not token or not hmac.compare_digest(got, token):
            raise HTTPException(status_code=401, detail="unauthorized")

    def pend():
        if queue is None:
            return {}
        try:
            return dict(queue.items())
        except Exception as e:
            print("queue read failed:", e)
            return {}

    def run(fn, *a, **kw):
        if refresh and time.time() - last_refresh[0] > 15:
            try:
                refresh()
                last_refresh[0] = time.time()
            except Exception as e:
                print("volume reload failed:", e)
        try:
            conn = open_conn()
        except sqlite3.Error:
            raise HTTPException(status_code=503, detail="DB hələ yoxdur - collect işləməyib")
        try:
            return fn(conn, *a, **kw)
        except sqlite3.OperationalError as e:
            raise HTTPException(status_code=503, detail=f"DB hazır deyil: {e}")
        finally:
            conn.close()

    def exists(vid):
        if run(lambda c: c.execute("SELECT 1 FROM validations WHERE id=?", (vid,)).fetchone()) is None:
            raise HTTPException(status_code=404, detail="tapılmadı")

    A = [Depends(auth)]

    @app.get("/", response_class=HTMLResponse)
    def page():
        return PAGE

    @app.get("/api/overview", dependencies=A)
    def api_overview():
        o = run(overview, pend())
        st = {}
        if run_state:
            try:
                st = run_state() or {}
            except Exception as e:
                print("run_state failed:", e)
        o["running_since"] = st.get("running")
        o["can_trigger"] = trigger is not None
        return o

    @app.get("/api/meta", dependencies=A)
    def api_meta():
        srcs = run(lambda c: [r[0] for r in c.execute("SELECT DISTINCT source FROM records ORDER BY source")])
        return {"sources": srcs, "categories": CATEGORIES, "statuses": STATUSES}

    def _ideas(decision, q, min_score, sort, status, cost):
        return run(ideas, decision or None, q or None, min_score, sort, status or None, cost or None, pend())

    @app.get("/api/ideas", dependencies=A)
    def api_ideas(decision: str = "", q: str = "", min_score: float = 0.0, sort: str = "score",
                  status: str = "", cost: str = ""):
        return _ideas(decision, q, min_score, sort, status, cost)

    @app.get("/api/ideas.csv", dependencies=A)
    def api_ideas_csv(decision: str = "", q: str = "", min_score: float = 0.0, sort: str = "score",
                      status: str = "", cost: str = ""):
        body = ideas_csv(_ideas(decision, q, min_score, sort, status, cost))
        return Response(body, media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="firsat-ideyalari.csv"'})

    @app.get("/api/ideas/{vid}", dependencies=A)
    def api_idea(vid: int):
        r = run(idea, vid, pend())
        if r is None:
            raise HTTPException(status_code=404, detail="tapılmadı")
        return r

    @app.get("/api/ideas/{vid}/report.md", dependencies=A)
    def api_idea_md(vid: int):
        r = run(idea_markdown, vid)
        if r is None:
            raise HTTPException(status_code=404, detail="tapılmadı")
        return PlainTextResponse(r[1], media_type="text/markdown; charset=utf-8",
                                 headers={"Content-Disposition": f'attachment; filename="{r[0]}"'})

    @app.post("/api/ideas/{vid}/vote/{direction}", dependencies=A)
    def api_vote(vid: int, direction: str):
        if direction not in ("up", "down") or queue is None:
            raise HTTPException(status_code=400, detail="yanlış səs")
        exists(vid)
        queue[f"{vid}:dashboard"] = direction
        return {"ok": True, "note": "Səs növbəyə düşdü, növbəti işləmədə (≤3 saat) bazaya yazılacaq"}

    @app.post("/api/ideas/{vid}/status", dependencies=A)
    def api_status(vid: int, payload: dict = Body(...)):
        value = json.dumps({"status": payload.get("status"), "note": payload.get("note") or ""}, ensure_ascii=False)
        if queue is None or parse_status(value) is None:
            raise HTTPException(status_code=400, detail="yanlış status")
        exists(vid)
        queue[f"status:{vid}"] = value
        return {"ok": True}

    @app.get("/api/topics", dependencies=A)
    def api_topics(q: str = "", candidates: bool = False):
        return run(topics, 14, None, q or None, candidates)

    @app.get("/api/topics/{tid}", dependencies=A)
    def api_topic(tid: int):
        r = run(topic, tid)
        if r is None:
            raise HTTPException(status_code=404, detail="tapılmadı")
        return r

    @app.get("/api/sources", dependencies=A)
    def api_sources():
        return run(sources)

    @app.get("/api/search", dependencies=A)
    def api_search(q: str = "", source: str = "", kind: str = "", category: str = "",
                   min_score: float = 0.0, limit: int = 50, offset: int = 0):
        return run(search, q, source or None, kind or None, category or None, min_score or None, limit, offset)

    @app.post("/api/run/{job}", dependencies=A)
    def api_run(job: str):
        if job not in ("collect", "weekly") or trigger is None:
            raise HTTPException(status_code=400, detail="yanlış iş")
        if run_state and (run_state() or {}).get("running"):
            raise HTTPException(status_code=409, detail="Başqa iş artıq gedir")
        trigger(job)
        return {"ok": True, "note": "İş başladı. Bir neçə dəqiqəyə nəticə burada görünəcək."}

    return app
