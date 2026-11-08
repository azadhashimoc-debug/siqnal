import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit

from radar import config
from radar.models import Record
from radar.normalize import clean_html


class _ClassCollector(HTMLParser):
    """Collects text of elements carrying a given class (simple '.class' selectors only)."""

    def __init__(self, cls):
        super().__init__()
        self.cls, self.depth, self.buf, self.items = cls, 0, [], []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            self.depth += 1
        elif self.cls in (dict(attrs).get("class") or "").split():
            self.depth = 1

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1
            if self.depth == 0:
                self.items.append(clean_html(" ".join(self.buf)))
                self.buf = []

    def handle_data(self, data):
        if self.depth:
            self.buf.append(data)


def _http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", "replace")


class NewsCommentsSource:
    def __init__(self, name, article_urls, sites=None, http_get=_http_get):
        self.name, self.urls = name, article_urls
        self.sites = config.NEWS_COMMENT_SITES if sites is None else sites
        self._get = http_get

    def fetch(self):
        out = []
        for url in self.urls:
            sel = self.sites.get(urlsplit(url).hostname)
            if not sel:
                continue
            p = _ClassCollector(sel.lstrip("."))
            p.feed(self._get(url))
            for i, text in enumerate(t for t in p.items if t):
                out.append(Record(self.name, "comment", f"{url}#c{i}", text,
                                  datetime.now(timezone.utc), parent_url=url))
        return out
