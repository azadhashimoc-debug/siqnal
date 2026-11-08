import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from radar import config
from radar.models import Record
from radar.normalize import clean_html


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def _parse_date(s):
    try:
        return parsedate_to_datetime(s)
    except Exception:
        return datetime.now(timezone.utc)


class RssSource:
    def __init__(self, name: str, url: str, http_get=_http_get):
        self.name, self.url, self._get = name, url, http_get

    def fetch(self):
        root = ET.fromstring(self._get(self.url))
        out = []
        for item in root.iter("item"):
            title = clean_html(item.findtext("title") or "")
            desc = clean_html(item.findtext("description") or "")
            link = (item.findtext("link") or "").strip()
            if not link or not (title or desc):
                continue
            out.append(Record(self.name, "news", link, f"{title}. {desc}".strip(". "),
                              _parse_date(item.findtext("pubDate"))))
        return out


def default_sources(http_get=_http_get):
    return [RssSource(f["source"], f["url"], http_get) for f in config.FEEDS]
