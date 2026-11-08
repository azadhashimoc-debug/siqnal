import re
from pathlib import Path

from radar import config
from radar.validate import DIMENSIONS

EMPTY_WEEK = "Bu həftə güclü fürsət yoxdur."
MAX_IDEAS = 5
TG_LIMIT = 4096
CIRCLED = "①②③④⑤⑥⑦⑧⑨"
_AZ = str.maketrans("əöüçşğıƏÖÜÇŞĞİ", "eoucsgiEOUCSGI")


def slug(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").translate(_AZ).lower()).strip("-")
    return s[:maxlen].strip("-") or "fürsət".translate(_AZ)


def overall_score(v) -> float:
    return sum(getattr(v, d)["score"] for d in DIMENSIONS) / len(DIMENSIONS)


def report_name(vid: int, v) -> str:
    return f"{vid}-{slug(v.solutions[0].title if v.solutions else v.problem)}.md"


def _claims(d: dict) -> list:
    return [f"- {c['text']} ({c['url']})" for c in d.get("claims", [])]


def render_report(v, evidence) -> str:
    L = [f"# {v.problem}", "", "## Problem", v.problem]
    L += [f"- {p}" for p in v.sub_pains]
    L += ["", "## Kanıtlar"] + [f"- {t[:300]} ({u})" for t, u in evidence]
    L += ["", f"## Talep ({v.demand['score']}/10)"] + _claims(v.demand)
    L += ["", f"## Rəqabət ({v.competition['score']}/10)"] + _claims(v.competition)
    L += ["", f"## Ödəmə gücü ({v.willingness_to_pay['score']}/10)"] + _claims(v.willingness_to_pay)
    L += ["", f"## Vaxtlama ({v.timing['score']}/10)"] + _claims(v.timing)
    ms = v.market_size or {}
    if ms.get("estimate"):
        L += ["", f"Bazar ölçüsü: {ms['estimate']}" + (f" ({ms['url']})" if ms.get("url") else "")]
    L += ["", "## Həll yolları"]
    for i, s in enumerate(v.solutions, 1):
        L += ["", f"### {i}. {s.title} ({s.start_cost})",
              f"- Necə işləyir: {s.how_it_works}",
              f"- Kim ödəyir / gəlir modeli: {s.business_model}",
              f"- Başlanğıc xərci: {s.start_cost}" + (f" ({s.start_cost_text})" if s.start_cost_text else ""),
              f"- Çətinlik: {s.difficulty}/5",
              "- Rəqiblər: " + (", ".join(s.competitor_urls) or "-"),
              f"- İlk addım: {s.first_step}"]
    L += ["", "## Risklər"] + [f"- {r}" for r in v.risks]
    if v.unverified_claims:
        L += ["", "## Doğrulanmadı"] + [f"- Doğrulanmadı: {c}" for c in v.unverified_claims]
    return "\n".join(L) + "\n"


def write_report(vid: int, v, evidence, report_dir=None) -> Path:
    d = Path(report_dir or config.REPORT_DIR)
    d.mkdir(parents=True, exist_ok=True)
    p = d / report_name(vid, v)
    p.write_text(render_report(v, evidence), encoding="utf-8")
    return p


def top_ideas(items) -> list:
    gec = [(i, v) for i, v in items if v.decision == "gec"]
    return sorted(gec, key=lambda x: -overall_score(x[1]))[:MAX_IDEAS]


def _line(n: int, vid: int, v, limit: int) -> str:
    sols = " ".join(f"{CIRCLED[k]} {s.title} ({s.start_cost})" for k, s in enumerate(v.solutions[:9]))
    tail = f" | skor {overall_score(v):.1f} | {report_name(vid, v)}"
    head = f"{CIRCLED[n]} {v.problem}\n   {sols}"
    room = limit - len(tail)
    if len(head) > room:
        head = head[:max(0, room - 1)] + "…"
    return head + tail


def weekly_message(items) -> str:
    top = top_ideas(items)
    if not top:
        return EMPTY_WEEK
    head = "Bu həftənin fürsətləri:\n\n"
    limit = (TG_LIMIT - len(head)) // len(top) - 2
    return head + "\n\n".join(_line(n, i, v, limit) for n, (i, v) in enumerate(top))
