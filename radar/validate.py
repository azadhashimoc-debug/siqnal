import json
import logging
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from radar import config, trends

log = logging.getLogger(__name__)
MODEL = "claude-sonnet-5-5"
TOOLS = [{"type": "web_search_20250305", "name": "web_search", "max_uses": 10}]
MAX_CONSECUTIVE_API_ERRORS = 3
REVALIDATE_DAYS = 28
DIMENSIONS = ("demand", "competition", "willingness_to_pay", "timing")
DECISIONS = ("gec", "izle", "reddet")
COSTS = ("az", "orta", "yuksek")
PROMPT_PATH = Path(os.environ.get("RADAR_PROMPT_PATH")
                   or Path(__file__).resolve().parent / "prompts" / "validate.md")
CALIBRATION_DIR = Path(os.environ.get("RADAR_CALIBRATION_DIR")
                       or Path(__file__).resolve().parent.parent / "docs" / "calibration")
RETRY_NOTE = ("\n\nDİQQƏT: əvvəlki cavab etibarsız idi. Ən azı 3 fərqli növ həll ver "
              "və ən azı biri start_cost=\"az\" olsun.")


class ValidateAPIError(Exception):
    """API failure (network, rate limit, auth)."""


class ValidateParseError(Exception):
    """Model output could not be parsed into a Validation."""


@dataclass
class Solution:
    title: str
    how_it_works: str
    business_model: str
    start_cost: str  # az | orta | yuksek
    difficulty: int  # 1-5
    first_step: str
    competitor_urls: list = field(default_factory=list)
    start_cost_text: str = ""  # rough AZN range


@dataclass
class Validation:
    topic_id: int
    problem: str
    sub_pains: list
    demand: dict
    competition: dict
    willingness_to_pay: dict
    timing: dict
    decision: str  # gec | izle | reddet
    solutions: list
    risks: list
    market_size: dict
    unverified_claims: list
    api_calls: int = 0  # API calls spent producing this result (not persisted semantics)


def extract_json(raw: str):
    """Strip code fences / surrounding prose and parse the outermost JSON object."""
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    try:
        return json.loads(s)
    except ValueError:
        i, j = s.find("{"), s.rfind("}")
        if i < 0 or j <= i:
            raise
        return json.loads(s[i:j + 1])


def _evidence(conn, topic_id: int, limit: int = 20) -> list:
    return conn.execute(
        "SELECT r.text, r.url FROM classifications c JOIN records r ON r.id = c.record_id "
        "WHERE c.topic_id=? GROUP BY r.text_hash "
        "ORDER BY MAX(COALESCE(r.published, r.created_at)) DESC, MAX(r.id) DESC LIMIT ?",
        (topic_id, limit)).fetchall()


def _votes(conn, limit: int = 10) -> list:
    return conn.execute(
        "SELECT v.vote, COALESCE(val.idea, ''), COALESCE(val.decision, '') FROM votes v "
        "JOIN validations val ON val.id = v.validation_id WHERE v.vote IN (1, -1) "
        "ORDER BY v.created_at DESC, v.id DESC LIMIT ?", (limit,)).fetchall()


def build_prompt(conn, topic_id: int) -> str:
    row = conn.execute("SELECT name FROM topics WHERE id=?", (topic_id,)).fetchone()
    topic = row[0] if row else str(topic_id)
    calib = "\n\n---\n\n".join(p.read_text(encoding="utf-8") for p in sorted(CALIBRATION_DIR.glob("*.md")))
    votes = "\n".join(f"{'👍' if v == 1 else '👎'} {idea} ({dec})" for v, idea, dec in _votes(conn)) or "(yoxdur)"
    ev = "\n".join(f"- {t[:500]} — {u}" for t, u in _evidence(conn, topic_id)) or "(yoxdur)"
    tpl = PROMPT_PATH.read_text(encoding="utf-8")
    for k, v in (("CALIBRATION", calib), ("VOTES", votes), ("TOPIC", topic), ("EVIDENCE", ev)):
        tpl = tpl.replace("{{" + k + "}}", v)
    return tpl


def _url_ok(u) -> bool:
    return isinstance(u, str) and u.strip().lower().startswith(("http://", "https://"))


def _dim(d) -> dict:
    d = d if isinstance(d, dict) else {}
    sc = d.get("score")
    sc = sc if isinstance(sc, int) and not isinstance(sc, bool) and 0 <= sc <= 10 else 0
    claims = [{"text": str(c.get("text", "")), "url": c["url"].strip()}
              for c in d.get("claims") or [] if isinstance(c, dict) and _url_ok(c.get("url"))]
    return {"score": sc, "claims": claims}


def _solution(s) -> Optional[Solution]:
    if not isinstance(s, dict) or s.get("start_cost") not in COSTS:
        return None
    diff = s.get("difficulty")
    if isinstance(diff, bool) or not isinstance(diff, int):
        return None
    return Solution(
        title=str(s.get("title", "")), how_it_works=str(s.get("how_it_works", "")),
        business_model=str(s.get("business_model", "")), start_cost=s["start_cost"],
        difficulty=min(5, max(1, diff)), first_step=str(s.get("first_step", "")),
        competitor_urls=[u for u in s.get("competitor_urls") or [] if _url_ok(u)],
        start_cost_text=str(s.get("start_cost_text", "")))


def _strs(v) -> list:
    return [str(x) for x in v] if isinstance(v, list) else []


def _parse(topic_id: int, raw: str) -> Validation:
    try:
        d = extract_json(raw)
    except ValueError as e:
        raise ValidateParseError(str(e)) from e
    if not isinstance(d, dict):
        raise ValidateParseError("not a JSON object")
    ms = d.get("market_size") if isinstance(d.get("market_size"), dict) else {}
    v = Validation(
        topic_id=topic_id, problem=str(d.get("problem", "")), sub_pains=_strs(d.get("sub_pains")),
        **{k: _dim(d.get(k)) for k in DIMENSIONS},
        decision=d.get("decision") if d.get("decision") in DECISIONS else "reddet",
        solutions=[s for s in map(_solution, d.get("solutions") or []) if s][:5],
        risks=_strs(d.get("risks")),
        market_size={"estimate": str(ms.get("estimate", "")),
                     "url": ms["url"].strip() if _url_ok(ms.get("url")) else None},
        unverified_claims=_strs(d.get("unverified_claims")))
    if v.decision == "gec" and any(not getattr(v, k)["claims"] for k in DIMENSIONS):
        v.decision = "izle"
    _flag_unsourced_numbers(v)
    return v


_DIGITS = re.compile(r"\d+")


def _flag_unsourced_numbers(v: Validation) -> None:
    """Heuristic: when market_size has no URL, every market_size/solution text that
    contains a digit sequence is treated as an unverified number and appended to
    unverified_claims (deduplicated). Over-flags rather than under-flags."""
    if v.market_size.get("url"):
        return
    texts = [v.market_size.get("estimate", "")]
    for s in v.solutions:
        texts += [s.title, s.how_it_works, s.business_model, s.start_cost_text, s.first_step]
    for t in texts:
        if t and _DIGITS.search(t) and t not in v.unverified_claims:
            v.unverified_claims.append(t)


def _solutions_ok(v: Validation) -> bool:
    return len(v.solutions) >= 3 and any(s.start_cost == "az" for s in v.solutions)


MAX_CONTINUATIONS = 2


def _call(client, prompt: str, max_calls: int = 1 + MAX_CONTINUATIONS, counter=None) -> str:
    """One logical call; pause_turn is continued up to MAX_CONTINUATIONS times within max_calls.
    counter (list) gets one item appended per API request made."""
    messages = [{"role": "user", "content": prompt}]
    used = 0
    while True:
        try:
            used += 1
            if counter is not None:
                counter.append(1)
            resp = client.messages.create(model=MODEL, max_tokens=8000, tools=TOOLS, messages=messages)
        except Exception as e:  # SDK not imported here; any client exception = API failure
            raise ValidateAPIError(str(e)) from e
        if getattr(resp, "stop_reason", None) != "pause_turn":
            break
        if used > MAX_CONTINUATIONS or used >= max_calls:
            raise ValidateParseError("response still paused after continuations")
        messages = messages + [{"role": "assistant", "content": resp.content}]
    texts = [b.text for b in resp.content
             if getattr(b, "type", "text") == "text" and getattr(b, "text", None)]
    if not texts:
        raise ValidateParseError("no text block in response")
    return texts[-1]


def _cap(v: Validation) -> Validation:
    if v.decision == "gec":
        v.decision = "izle"
    return v


def validate_topic(client, conn, topic_id: int, max_calls: int = 2) -> Validation:
    """Raises ValidateAPIError / ValidateParseError. If the solutions rule fails
    (<3 solutions or none with start_cost "az"), retries once (if max_calls allows),
    then downgrades gec to izle (reddet stays reddet). Result.api_calls = calls used."""
    prompt = build_prompt(conn, topic_id)
    v = None
    n = []
    try:
        v = _parse(topic_id, _call(client, prompt, max_calls, n))
        v.api_calls = len(n)
        if _solutions_ok(v):
            return v
    except (ValidateParseError, ValidateAPIError) as e:
        e.api_calls = len(n)
        if isinstance(e, ValidateAPIError):
            raise
        log.warning("validate parse error for topic %s: %s", topic_id, e)
        if max_calls - len(n) < 1:
            raise ValidateParseError(f"{e} ({len(n)} call(s) used)") from e
    if max_calls - len(n) < 1:
        return _cap(v)
    try:
        v = _parse(topic_id, _call(client, prompt + RETRY_NOTE, max_calls - len(n), n))
    except (ValidateParseError, ValidateAPIError) as e:
        e.api_calls = len(n)
        raise
    v.api_calls = len(n)
    return v if _solutions_ok(v) else _cap(v)


def save(conn, v: Validation) -> int:
    idea = v.solutions[0].title if v.solutions else v.problem
    cur = conn.execute(
        "INSERT INTO validations(topic_id, idea, result, decision, data) VALUES(?,?,?,?,?)",
        (v.topic_id, idea, v.decision, v.decision, json.dumps(asdict(v), ensure_ascii=False)))
    conn.commit()
    return cur.lastrowid


def validate_week(client, conn, today: Optional[date] = None) -> list:
    """MAX_VALIDATIONS_PER_WEEK caps API calls (retries included), not topics."""
    today = today or date.today()
    since = (today - timedelta(days=REVALIDATE_DAYS)).isoformat()
    recent = {r[0] for r in conn.execute(
        "SELECT topic_id FROM validations WHERE date(created_at) >= ?", (since,))}
    todo = [t for t in trends.candidates(conn, today) if t not in recent]
    budget = config.MAX_VALIDATIONS_PER_WEEK
    out, errors = [], 0
    for tid in todo:
        if budget <= 0:
            break
        try:
            v = validate_topic(client, conn, tid, max_calls=min(2, budget))
            budget -= v.api_calls
        except ValidateAPIError as e:
            budget -= getattr(e, "api_calls", 1)
            errors += 1
            log.warning("validate API error for topic %s: %s", tid, e)
            if errors >= MAX_CONSECUTIVE_API_ERRORS:
                log.error("stopping after %d consecutive API errors", errors)
                break
            continue
        except ValidateParseError as e:
            budget -= getattr(e, "api_calls", 1)
            errors = 0
            log.warning("unparseable validation for topic %s: %s", tid, e)
            continue
        errors = 0
        save(conn, v)
        out.append(v)
    return out
