import re

from radar.config import SIGNAL_PATTERNS

_WORD = re.compile(r"\w+", re.UNICODE)


def _lower(s: str) -> str:
    # str.lower() maps "I" -> "i" (Turkish would be "ı"); acceptable for prefix matching.
    return s.lower()


def stem(word: str) -> str:
    """Crude Azerbaijani stem: drop the last 2 chars, but never go below 5 chars.

    Words of <= 5 chars are kept whole. "bahalaşma" -> "bahalaş"; "problem" -> "probl".
    """
    word = _lower(word)
    return word[: max(5, len(word) - 2)]


def _keyword_stems():
    out = []
    for kws in SIGNAL_PATTERNS.values():
        for kw in kws:
            out.append([stem(w) for w in _WORD.findall(_lower(kw))])
    return out


_STEMS = _keyword_stems()


def prefilter(text: str) -> bool:
    words = _WORD.findall(_lower(text))
    for stems in _STEMS:
        if stems and all(any(w.startswith(s) for w in words) for s in stems):
            return True
    return False
