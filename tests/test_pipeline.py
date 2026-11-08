import urllib.error
from datetime import datetime

import pytest

from radar import bot, pipeline, trends, classify
from radar.db import connect
from radar.models import Record


class Fake:
    name = "fake"
    def fetch(self):
        return [Record("fake", "news", "https://x.az/1", "bir xəbər", datetime(2026, 1, 1))]


def test_run_collect_without_key_skips_classify_but_assigns(monkeypatch, tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    calls = []
    monkeypatch.setattr(trends, "assign_pending", lambda c: calls.append("assign") or 0)
    monkeypatch.setattr(trends, "update_topic_days", lambda c, d: calls.append("days"))
    monkeypatch.setattr(classify, "classify_pending", lambda *a, **k: calls.append("classify"))
    res = pipeline.run_collect(conn, env={}, sources=[Fake()])
    assert res["fake"] == 1
    assert "classify" not in calls
    assert calls == ["assign", "days"]


def test_run_collect_with_key_classifies(monkeypatch, tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    calls = []
    monkeypatch.setattr(trends, "assign_pending", lambda c: calls.append("assign") or 0)
    monkeypatch.setattr(trends, "update_topic_days", lambda c, d: None)
    monkeypatch.setattr(classify, "classify_pending", lambda c, cl, **k: calls.append("classify") or 0)
    pipeline.run_collect(conn, env={"ANTHROPIC_API_KEY": "k"}, sources=[Fake()], client=object())
    assert calls == ["classify", "assign"]


def test_default_sources_rss_only_when_no_keys(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    names = [s.name for s in pipeline.build_sources(conn, {})]
    assert "telegram" not in names and "youtube" not in names and "apify" not in names
    assert len(names) >= 1


def test_run_weekly_sends_message(monkeypatch, tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    sent = []
    monkeypatch.setattr(pipeline.validate, "validate_week", lambda cl, c, today=None: [])
    pipeline.run_weekly(conn, object(), lambda m, p, f=None: sent.append((m, p)),
                        {"TELEGRAM_CHAT_ID": "42"}, report_dir=str(tmp_path))
    assert sent[0][0] == "sendMessage" and sent[0][1]["chat_id"] == "42"


def test_telegram_post_redacts_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "SECRET123")
    def boom(req, timeout=0):
        raise urllib.error.URLError("fail https://api.telegram.org/botSECRET123/x")
    monkeypatch.setattr(bot.urllib.request, "urlopen", boom)
    with pytest.raises(RuntimeError) as e:
        bot.telegram_post("sendMessage", {"a": 1})
    assert "SECRET123" not in str(e.value)
    assert e.value.__cause__ is None


def test_build_sources_with_comment_sites(monkeypatch, tmp_path):
    from radar import config
    from radar.db import insert_record
    conn = connect(str(tmp_path / "t.db"))
    insert_record(conn, Record("x", "news", "https://a.az/1", "t", datetime(2026, 1, 1)))
    insert_record(conn, Record("x", "comment", "https://a.az/1#c0", "c", datetime(2026, 1, 1)))
    monkeypatch.setattr(config, "NEWS_COMMENT_SITES", {"a.az": ".c"})
    src = [s for s in pipeline.build_sources(conn, {}) if s.name == "news_comments"]
    assert src and src[0].urls == ["https://a.az/1"]


def test_run_weekly_checks_chat_id_before_validating(monkeypatch, tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    called = []
    monkeypatch.setattr(pipeline.validate, "validate_week", lambda *a, **k: called.append(1) or [])
    with pytest.raises(RuntimeError):
        pipeline.run_weekly(conn, object(), lambda *a: None, {})
    assert not called


def _val(conn):
    conn.execute("INSERT INTO validations(topic_id, idea, result, decision, data) VALUES(1,'i','gec','gec','{}')")
    conn.commit()
    return conn.execute("SELECT id FROM validations").fetchone()[0]


def test_drain_votes(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    vid = _val(conn)
    n = bot.drain_votes(conn, {f"{vid}:7": "up", "999:7": "up", f"{vid}:8": "bad", "junk": "up"})
    assert n == 1
    assert conn.execute("SELECT voter, vote FROM votes").fetchall() == [("7", 1)]
    bot.drain_votes(conn, {f"{vid}:7": "down"})
    assert conn.execute("SELECT voter, vote FROM votes").fetchall() == [("7", -1)]


def test_parse_callback():
    assert bot.parse_callback("vote:3:up") == (3, "up")
    assert bot.parse_callback("x") is None


def test_lock():
    from radar import lock
    d = {}
    assert lock.acquire(d, now=1000, ttl=100)
    assert not lock.acquire(d, now=1050, ttl=100)
    assert lock.acquire(d, now=1101, ttl=100)  # stale
    lock.release(d)
    assert lock.acquire(d, now=1102, ttl=100)


def test_connect_uses_delete_journal(tmp_path):
    conn = connect(str(tmp_path / "t.db"))
    assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "delete"


class Vol:
    def __init__(self, fail=False):
        self.fail, self.calls = fail, []
    def reload(self): self.calls.append("reload")
    def commit(self):
        self.calls.append("commit")
        if self.fail:
            raise RuntimeError("commit failed")


def test_run_locked_order_and_pop(tmp_path):
    from radar import runner
    path = str(tmp_path / "t.db")
    c = connect(path); vid = _val(c); c.close()
    votes, lk, vol = {f"{vid}:7": "up"}, {}, Vol()
    out = runner.run_locked(vol, votes, lk, 100, lambda: connect(path), lambda conn: "ok")
    assert out == "ok" and vol.calls == ["reload", "commit"]
    assert votes == {} and "running" not in lk


def test_run_locked_commit_failure_keeps_votes_and_releases(tmp_path):
    from radar import runner
    path = str(tmp_path / "t.db")
    c = connect(path); vid = _val(c); c.close()
    votes, lk = {f"{vid}:7": "up"}, {}
    with pytest.raises(RuntimeError):
        runner.run_locked(Vol(fail=True), votes, lk, 100, lambda: connect(path), lambda conn: None)
    assert votes == {f"{vid}:7": "up"} and "running" not in lk


def test_run_locked_revote_survives(tmp_path):
    from radar import runner
    path = str(tmp_path / "t.db")
    c = connect(path); vid = _val(c); c.close()
    votes = {f"{vid}:7": "up"}
    runner.run_locked(Vol(), votes, {}, 100, lambda: connect(path),
                      lambda conn: votes.__setitem__(f"{vid}:7", "down"))
    assert votes == {f"{vid}:7": "down"}


def test_run_locked_skips_when_held():
    from radar import runner
    assert runner.run_locked(Vol(), {}, {"running": 10 ** 12}, 100, None, None) is None


def test_modal_app_targets_are_toplevel():
    import ast
    tree = ast.parse(open("modal_app.py", encoding="utf-8").read())
    top = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and any("app.function" in ast.dump(d) for d in n.decorator_list):
            assert n.name in top
    assert not any(isinstance(n, ast.FunctionDef) and n.name == "_locked" for n in ast.walk(tree))


def test_yield_check_runs_once_per_28_days(monkeypatch, tmp_path):
    from datetime import date
    conn = connect(str(tmp_path / "t.db"))
    n = []
    monkeypatch.setattr(pipeline, "disable_low_yield", lambda c: n.append(1))
    monkeypatch.setattr(trends, "assign_pending", lambda c: 0)
    monkeypatch.setattr(trends, "update_topic_days", lambda c, d: None)
    for d in (date(2026, 11, 8), date(2026, 11, 8), date(2026, 11, 20), date(2026, 12, 7)):
        pipeline.run_collect(conn, env={}, sources=[], today=d)
    assert len(n) == 2


def test_run_locked_job_failure_still_commits_keeps_votes(tmp_path):
    from radar import runner
    path = str(tmp_path / "t.db")
    c = connect(path); vid = _val(c); c.close()
    votes, lk, vol = {f"{vid}:7": "up"}, {}, Vol()
    def boom(conn): raise ValueError("x")
    with pytest.raises(ValueError):
        runner.run_locked(vol, votes, lk, 100, lambda: connect(path), boom)
    assert "commit" in vol.calls and votes and "running" not in lk


def test_modal_app_ships_prompts_and_calibration():
    src = open("modal_app.py", encoding="utf-8").read()
    assert '.add_local_dir("radar/prompts"' in src and '.add_local_dir("docs/calibration"' in src
    assert "RADAR_PROMPT_PATH" in src
