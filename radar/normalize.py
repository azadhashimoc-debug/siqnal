import html
import re
from urllib.parse import urlsplit, urlunsplit

_TRACKING_PARAMS = {"fbclid", "gclid"}
_TRACKING_PREFIX = "utm_"
_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1\s*>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _is_tracking(segment: str) -> bool:
    key = segment.split("=", 1)[0].lower()
    return key.startswith(_TRACKING_PREFIX) or key in _TRACKING_PARAMS


def _rebuild_netloc(parts) -> str:
    host = parts.hostname or ""
    if ":" in host:  # IPv6 literal needs brackets
        host = f"[{host}]"
    netloc = host
    if parts.port is not None:
        netloc += f":{parts.port}"
    if parts.username is not None:
        userinfo = parts.username
        if parts.password is not None:
            userinfo += f":{parts.password}"
        netloc = f"{userinfo}@{netloc}"
    return netloc


def normalize_url(url: str) -> str:
    """Drop utm_*, fbclid and gclid params, keep the rest in order, drop the fragment,
    and lowercase the host. Query values are left byte-for-byte as they were given."""
    parts = urlsplit(url)
    query = "&".join(seg for seg in parts.query.split("&") if seg and not _is_tracking(seg))
    return urlunsplit((parts.scheme, _rebuild_netloc(parts), parts.path, query, ""))


def clean_html(s: str) -> str:
    """Remove script/style blocks and tags, unescape entities, collapse whitespace.
    Text is kept as UTF-8; characters are never ASCII-folded."""
    text = _SCRIPT_STYLE_RE.sub(" ", s)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()
