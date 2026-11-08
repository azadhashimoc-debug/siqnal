from datetime import datetime, timezone

from radar import config
from radar.models import Record


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
            items = self._cl().run(actor)
            self.conn.execute("INSERT INTO apify_runs(actor, run_id, status) VALUES(?,?,?)", (actor, "", "ok"))
            self.conn.commit()
            for it in items:
                text, url = it.get("text") or it.get("message"), it.get("url") or it.get("postUrl")
                if text and url:  # author/profile fields deliberately dropped
                    out.append(Record(self.name, "comment", url, text, datetime.now(timezone.utc),
                                      parent_url=it.get("postUrl")))
        return out
