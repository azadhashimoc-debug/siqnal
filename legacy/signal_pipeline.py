# Legacy script (user's original), kept as reference for Task 3/4 migration.
# FEEDS and SIGNAL_PATTERNS move to radar/config.py.
import os
import json
import time
import hashlib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

CACHE_FILE = "seen_news_cache.json"

FEEDS = [
    {"source": "Oxu.az", "url": "https://oxu.az/rss"},
    {"source": "Qafqazinfo", "url": "https://qafqazinfo.az/rss"},
    {"source": "APA", "url": "https://apa.az/rss"},
    {"source": "Marja.az", "url": "https://marja.az/rss"},
    {"source": "Modern.az", "url": "https://modern.az/rss"}
]

SIGNAL_PATTERNS = {
    "PROBLEM_SIKAYET": [
        "bahalaşma", "qiymət artımı", "bahalaşdı", "narazılıq", "şikayət",
        "növbə", "problem", "cərimə", "cərimələnəcək", "qıtlıq", "təmir",
        "tıxac", "çatışmazlıq", "ləğv edildi"
    ],
    "REGULYASIYA_QANUN": [
        "qanun", "qərar", "yeni qayda", "vergi", "rüsum", "gömrük",
        "lisenziya", "icazə", "cərimə qərarı", "standart", "nazirlər kabineti",
        "məcburidir", "tələb olunacaq", "qadağan edildi"
    ],
    "BIZNES_TREND": [
        "investisiya", "idxal", "ixrac", "kredit", "startap", "subsidiya",
        "qrant", "yeni zavod", "istehsal", "müqavilə", "tərəfdaşlıq",
        "süni intellekt", "e-ticarət", "satışlar artdı"
    ]
}

# (Remaining functions: load_cache, save_cache, hash_id, fetch_rss,
#  analyze_signals, generate_business_idea, run_signal_pipeline —
#  see the user's original paste; replaced by radar/* modules.)
