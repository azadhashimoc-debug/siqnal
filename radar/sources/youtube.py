import logging
from datetime import datetime, timedelta, timezone

from radar import config
from radar.models import Record

log = logging.getLogger(__name__)


class YoutubeSource:
    """`client` is a googleapiclient-style resource (injectable); built lazily from env key."""

    name = "youtube"

    def __init__(self, channels=None, client=None, days=7, api_key=None):
        self.channels = config.YOUTUBE_CHANNELS if channels is None else channels
        self._client, self.days, self._key = client, days, api_key

    def _yt(self):
        if self._client is None:
            import os
            from googleapiclient.discovery import build  # lazy
            self._client = build("youtube", "v3", developerKey=self._key or os.environ["YOUTUBE_API_KEY"])
        return self._client

    def fetch(self):
        if not self.channels:
            return []
        yt = self._yt()
        since = (datetime.now(timezone.utc) - timedelta(days=self.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        out = []
        for ch in self.channels:
            try:
                vids = yt.search().list(part="id", channelId=ch, type="video", order="date",
                                        publishedAfter=since, maxResults=25).execute().get("items", [])
            except Exception:
                log.exception("youtube channel %s failed", ch)
                continue
            for v in vids:
                try:
                    vid = v["id"]["videoId"]
                    url = f"https://www.youtube.com/watch?v={vid}"
                    threads = yt.commentThreads().list(part="snippet", videoId=vid, maxResults=100,
                                                       textFormat="plainText").execute().get("items", [])
                    for t in threads:
                        sn = t["snippet"]["topLevelComment"]["snippet"]  # author fields deliberately ignored
                        out.append(Record(self.name, "comment", f"{url}&lc={t['id']}", sn["textDisplay"],
                                          datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")),
                                          parent_url=url))
                except Exception:
                    log.exception("youtube video failed (comments disabled?)")
        return out
