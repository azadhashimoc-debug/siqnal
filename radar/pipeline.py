import logging
import os
from datetime import date

from radar import bot, classify, config, trends, validate
from radar.collect import collect, disable_low_yield
from radar.sources import rss

log = logging.getLogger(__name__)


def build_sources(conn, env) -> list:
    """RSS always; others only when their lists/keys are configured."""
    sources = list(rss.default_sources())
    if config.NEWS_COMMENT_SITES:
        from radar.sources.news_comments import NewsCommentsSource
        urls = [r[0] for r in conn.execute(
            "SELECT url FROM records WHERE kind='news' ORDER BY id DESC LIMIT 200")]
        sources.append(NewsCommentsSource("news_comments", urls))
    else:
        log.info("news_comments skipped: NEWS_COMMENT_SITES empty")
    if config.YOUTUBE_CHANNELS and env.get("YOUTUBE_API_KEY"):
        from radar.sources.youtube import YoutubeSource
        sources.append(YoutubeSource(api_key=env["YOUTUBE_API_KEY"]))
    else:
        log.info("youtube skipped: channels or YOUTUBE_API_KEY missing")
    if config.TELEGRAM_CHANNELS and env.get("TG_API_ID") and env.get("TG_API_HASH"):
        from radar.sources.telegram_src import TelegramSource
        sources.append(TelegramSource(conn=conn))
    else:
        log.info("telegram skipped: channels or TG_API_ID/TG_API_HASH missing")
    if config.APIFY_ACTORS and env.get("APIFY_TOKEN"):
        from radar.sources.apify_src import ApifySource
        sources.append(ApifySource(conn))
    else:
        log.info("apify skipped: actors or APIFY_TOKEN missing")
    return sources


def make_client():
    import anthropic  # lazy
    return anthropic.Anthropic()


def run_collect(conn, env=os.environ, sources=None, client=None, today=None) -> dict:
    sources = build_sources(conn, env) if sources is None else sources
    result = collect(conn, sources)
    log.info("collected: %s", result)
    if env.get("ANTHROPIC_API_KEY"):
        classify.classify_pending(conn, client or make_client())
    else:
        log.info("classify skipped: ANTHROPIC_API_KEY unset")
    trends.assign_pending(conn)
    trends.update_topic_days(conn, today or date.today())
    _maybe_disable_low_yield(conn, today or date.today())
    return result


YIELD_CHECK_DAYS = 28


def _maybe_disable_low_yield(conn, today) -> None:
    row = conn.execute("SELECT value FROM source_state WHERE name='last_yield_check'").fetchone()
    if row:
        try:
            if (today - date.fromisoformat(row[0])).days < YIELD_CHECK_DAYS:
                return
        except ValueError:
            pass
    disable_low_yield(conn)
    conn.execute("INSERT OR REPLACE INTO source_state(name, value) VALUES('last_yield_check', ?)",
                 (today.isoformat(),))
    conn.commit()


def run_weekly(conn, client, http_post, env=os.environ, report_dir=None, today=None) -> list:
    chat_id = env.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise RuntimeError("TELEGRAM_CHAT_ID unset")
    validations = validate.validate_week(client, conn, today)
    gec = [(vid, v) for vid, v in _with_ids(conn, validations) if v.decision == "gec"]
    bot.send_weekly(conn, http_post, chat_id, gec, report_dir)
    return gec


def _with_ids(conn, validations):
    out = []
    for v in validations:
        row = conn.execute("SELECT id FROM validations WHERE topic_id=? ORDER BY id DESC LIMIT 1",
                           (v.topic_id,)).fetchone()
        if row:
            out.append((row[0], v))
    return out
