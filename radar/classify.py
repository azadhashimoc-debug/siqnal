import json
import re
from dataclasses import dataclass, asdict
from typing import Optional

from radar.prefilter import prefilter

MODEL = "claude-haiku-5-5"
CATEGORIES = {"PROBLEM_SIKAYET", "REGULYASIYA_QANUN", "BIZNES_TREND",
              "GUVEN_DELEDUZLUQ", "BILGI_BOSLUGU"}

PROMPT = """Aşağıdakı Azərbaycan dilində mətni təhlil et və YALNIZ JSON qaytar (izahat, markdown yox).
Sahələr:
- category: {cats} birindən
- is_problem: bool
- affected_group: kim təsirlənir (qısa mətn)
- urgency: tam ədəd 1-5
- willingness_to_pay: tam ədəd 1-5
- score: tam ədəd 0-100 (biznes fürsəti potensialı)
- topic_label: qısa Azərbaycan dilində isim birləşməsi
- evidence: mətndən qısa sitat

Mətn:
{text}"""


@dataclass
class Classification:
    category: str
    is_problem: bool
    affected_group: str
    urgency: int
    willingness_to_pay: int
    score: int
    topic_label: str
    evidence: str


def _int(v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise ValueError
    return v


def _parse(raw: str) -> Optional[Classification]:
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    try:
        d = json.loads(s)
        if not isinstance(d, dict) or d.get("category") not in CATEGORIES:
            return None
        if not isinstance(d.get("is_problem"), bool):
            return None
        strs = {}
        for k in ("affected_group", "topic_label", "evidence"):
            if not isinstance(d.get(k), str):
                return None
            strs[k] = d[k]
        return Classification(
            category=d["category"], is_problem=d["is_problem"],
            urgency=_int(d.get("urgency"), 1, 5),
            willingness_to_pay=_int(d.get("willingness_to_pay"), 1, 5),
            score=_int(d.get("score"), 0, 100), **strs)
    except (ValueError, TypeError):
        return None


def classify(client, rec_text: str) -> Optional[Classification]:
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=500,
            messages=[{"role": "user", "content": PROMPT.format(
                cats=", ".join(sorted(CATEGORIES)), text=rec_text[:4000])}])
        return _parse(resp.content[0].text)
    except Exception:
        return None


def classify_pending(conn, client, limit: int = 200) -> int:
    rows = conn.execute(
        "SELECT id, text FROM records WHERE status='new' ORDER BY id LIMIT ?", (limit,)).fetchall()
    done = 0
    for rid, text in rows:
        if not prefilter(text):
            conn.execute("UPDATE records SET status='prefiltered_out' WHERE id=?", (rid,))
            continue
        c = classify(client, text)
        if c is None:
            conn.execute("UPDATE records SET status='classify_failed' WHERE id=?", (rid,))
        else:
            conn.execute(
                "INSERT INTO classifications (record_id, category, label, score, data) VALUES (?,?,?,?,?)",
                (rid, c.category, c.topic_label, c.score, json.dumps(asdict(c), ensure_ascii=False)))
            conn.execute("UPDATE records SET status='classified' WHERE id=?", (rid,))
            done += 1
    conn.commit()
    return done
