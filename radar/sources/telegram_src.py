import logging

from radar import config
from radar.models import Record

log = logging.getLogger(__name__)


class TelegramSource:
    """`client` exposes iter_messages(channel, min_id=..., limit=...) like Telethon (injectable).
    Last seen ids persist in source_state when `conn` is given. fetch() is a generator: a channel's
    last id is saved only after the consumer has taken all of that channel's records."""

    name = "telegram"

    def __init__(self, channels=None, client=None, conn=None):
        self.channels = config.TELEGRAM_CHANNELS if channels is None else channels
        self._client, self.conn = client, conn

    def _tg(self):
        if self._client is None:
            import os
            from telethon.sync import TelegramClient  # lazy
            self._client = TelegramClient(os.environ.get("RADAR_TG_SESSION", "radar"), int(os.environ["TG_API_ID"]), os.environ["TG_API_HASH"])
            self._client.start()
        return self._client

    def _last(self, ch):
        if not self.conn:
            return 0
        r = self.conn.execute("SELECT value FROM source_state WHERE name=?", (f"tg:{ch}",)).fetchone()
        return int(r[0]) if r else 0

    def _save(self, ch, mid):
        if self.conn:
            self.conn.execute("INSERT OR REPLACE INTO source_state(name, value) VALUES(?,?)", (f"tg:{ch}", str(mid)))
            self.conn.commit()

    def fetch(self):
        if not self.channels:
            return
        tg = self._tg()
        for ch in self.channels:
            try:
                top = last = self._last(ch)
                kwargs = {"min_id": last}
                if last == 0:
                    kwargs["limit"] = config.TELEGRAM_FIRST_RUN_LIMIT
                for m in tg.iter_messages(ch, **kwargs):
                    top = max(top, m.id)
                    if m.text:  # sender fields deliberately ignored
                        yield Record(self.name, "news", f"https://t.me/{ch}/{m.id}", m.text, m.date)
                self._save(ch, top)
            except Exception:
                log.exception("telegram channel %s failed", ch)
