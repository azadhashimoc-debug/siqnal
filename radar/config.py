import os

DB_PATH = os.environ.get("RADAR_DB_PATH", "radar.db")
MAX_VALIDATIONS_PER_WEEK = 15
MAX_APIFY_RUNS_PER_WEEK = 10

# Live-checked 2026-11-08 (see docs/sources.md). Dead: oxu.az/rss, marja.az/rss, stat.gov.az/rss/en.
FEEDS = [
    {"source": "Oxu.az", "url": "https://oxu.az/feed"},
    {"source": "Qafqazinfo", "url": "https://qafqazinfo.az/rss"},
    {"source": "APA", "url": "https://apa.az/rss"},
    {"source": "Modern.az", "url": "https://modern.az/rss"},
    {"source": "Sia.az", "url": "https://sia.az/feed.php"},
    {"source": "AzerNews", "url": "https://www.azernews.az/feed.php"},
]

SIGNAL_PATTERNS = {
    "PROBLEM_SIKAYET": [
        "bahalaşma", "qiymət artımı", "bahalaşdı", "narazılıq", "şikayət",
        "növbə", "problem", "cərimə", "cərimələnəcək", "qıtlıq", "təmir",
        "tıxac", "çatışmazlıq", "ləğv edildi",
    ],
    "REGULYASIYA_QANUN": [
        "qanun", "qərar", "yeni qayda", "vergi", "rüsum", "gömrük",
        "lisenziya", "icazə", "cərimə qərarı", "standart", "nazirlər kabineti",
        "məcburidir", "tələb olunacaq", "qadağan edildi",
    ],
    "BIZNES_TREND": [
        "investisiya", "idxal", "ixrac", "kredit", "startap", "subsidiya",
        "qrant", "yeni zavod", "istehsal", "müqavilə", "tərəfdaşlıq",
        "süni intellekt", "e-ticarət", "satışlar artdı",
    ],
    "GUVEN_DELEDUZLUQ": [
        "aldat", "saxta", "fırıldaq", "dələduz", "beh pulu", "bloka atdı",
        "pulunu qaytarmır", "makler",
    ],
    "BILGI_BOSLUGU": [
        "pulsuz", "hüququ var", "bilmirlər", "xəbərsizdir", "necə müraciət",
        "icbari sığorta", "güzəşt",
    ],
}

USER_AGENT = "Mozilla/5.0 (compatible; firsat-radari/0.1)"

# {domain: css-class selector}. Empty: comment HTML not confirmed server-rendered (see docs/sources.md).
NEWS_COMMENT_SITES = {}
# TODO: discovery for these needs API keys (Telegram/YouTube/Apify); not done in Task 3.
YOUTUBE_CHANNELS = []
TELEGRAM_CHANNELS = []
APIFY_ACTORS = []

MIN_RECORDS_FOR_YIELD = 50
MIN_SOURCES_FOR_DISABLE = 5
TELEGRAM_FIRST_RUN_LIMIT = 200

# Trend detection (radar/trends.py)
TOPIC_MATCH_THRESHOLD = 80
TREND_RECENT_DAYS = 7
TREND_BASELINE_DAYS = 21
TREND_GROWTH_FACTOR = 2.0
MIN_NEW_TOPIC_VOICES = 5
MIN_TREND_SOURCES = 2
MIN_TREND_AVG_SCORE = 60
