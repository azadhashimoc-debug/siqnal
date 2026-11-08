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
