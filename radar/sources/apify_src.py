import logging
from datetime import datetime, timezone

from radar import config
from radar.models import Record

log = logging.getLogger(__name__)


class ApifySource:
    """`client.run(actor)` returns dataset items (list of dicts). Injectable; real client built lazily."""

    name = "apify"

    def __init__(self, conn, actors=None, client=None, max_runs=None):
        self.conn = conn
        self.actors = config.APIFY_ACTORS if actors is None else actors
        self._client = client
        self.max_runs = config.MAX_APIFY_RUNS_PER_WEEK if max_runs is None else max_runs

    def _runs_this_week(self):
        return self.conn.execute(
            "SELECT COUNT(*) FROM apify_runs WHERE created_at >= datetime('now','-7 days')").fetchone()[0]

    def _cl(self):
        if self._client is None:
            import os
            from apify_client import ApifyClient  # lazy
            c = ApifyClient(os.environ["APIFY_TOKEN"])

            class _Wrap:
                def run(self, actor):
                    run = c.actor(actor).call()
                    return list(c.dataset(run["defaultDatasetId"]).iterate_items())

            self._client = _Wrap()
        return self._client

    def fetch(self):
        out = []
        for actor in self.actors:
            if self._runs_this_week() >= self.max_runs:
                break
            try:
                items = list(self._cl().run(actor))
                status = "ok"
            except Exception:
                log.exception("apify actor %s failed", actor)
                items, status = [], "failed"
            # failed runs are recorded too, so they count toward the weekly cap
            self.conn.execute("INSERT INTO apify_runs(actor, run_id, status) VALUES(?,?,?)", (actor, "", status))
            self.conn.commit()
            for it in items:
                post = it.get("postUrl") or it.get("url")
                text = it.get("text") or it.get("message")
                if not (text and post):
                    continue
                # Dedupe key is (url_norm, text_hash), so distinct comment texts under one post do not
                # collapse. A per-comment id, when present, is appended to keep identical texts apart.
                cid = it.get("id")
                url = f"{post}#{cid}" if cid else post
                # author/profile fields deliberately dropped
                out.append(Record(self.name, "comment", url, text, datetime.now(timezone.utc), parent_url=post))
        return out
