# firsat-radari

Azərbaycan xəbər/şərhləri -> SQLite -> təsnifat -> trendlər -> yoxlama agenti -> həftəlik Telegram hesabatı.

## Env dəyişənləri
| Ad | Məqsəd |
|---|---|
| ANTHROPIC_API_KEY | təsnifat + yoxlama (yoxdursa təsnifat atlanır) |
| TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID | həftəlik hesabat |
| TELEGRAM_WEBHOOK_SECRET | webhook başlığının yoxlanması |
| TG_API_ID, TG_API_HASH | Telethon mənbəyi |
| YOUTUBE_API_KEY | YouTube mənbəyi |
| APIFY_TOKEN | Apify mənbəyi |
| RADAR_DB_PATH, RADAR_REPORT_DIR | DB / hesabat qovluğu (Modal: /data/...) |
| RADAR_TG_SESSION | Telethon session faylı (Modal: /data/radar) |
| RADAR_CALIBRATION_DIR | docs/calibration yolu (Modal: /root/docs/calibration) |

## Lokal
```
pip install -e .[dev]
python -m pytest
python -m radar collect     # yalnız RSS, açar yoxdursa digərləri atlanır
python -m radar weekly      # ANTHROPIC_API_KEY, TELEGRAM_* lazımdır
```

## Modal
```
pip install modal && modal setup
modal volume create radar-data
modal secret create radar-secrets ANTHROPIC_API_KEY=... TELEGRAM_BOT_TOKEN=... \
  TELEGRAM_CHAT_ID=... TELEGRAM_WEBHOOK_SECRET=... TG_API_ID=... TG_API_HASH=... \
  YOUTUBE_API_KEY=... APIFY_TOKEN=...
modal deploy modal_app.py
```
Cron: `collect` 3 saatdan bir; `weekly` bazar ertəsi 05:00 UTC (09:00 Bakı). `max_containers=1` - SQLite-a eyni anda bir yazıcı.

Webhook (bir dəfə; URL `modal deploy` çıxışından):
```
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook" \
  -d url="https://<workspace>--firsat-radari-webhook.modal.run" \
  -d secret_token="$TELEGRAM_WEBHOOK_SECRET" -d allowed_updates='["callback_query"]'
```

Telethon: ilk giriş interaktivdir. Lokalda `RADAR_TG_SESSION` ilə session yaradıb `modal volume put radar-data radar.session /radar.session` ilə yükləyin.

## Mənbə əlavə etmək
`radar/config.py`:
- Telegram: `TELEGRAM_CHANNELS = ["kanal_adi"]` + TG_API_ID/HASH.
- YouTube: `YOUTUBE_CHANNELS = ["UC..."]` (kanal id) + YOUTUBE_API_KEY.
- Apify: `APIFY_ACTORS = ["user/actor"]` + APIFY_TOKEN (həftədə `MAX_APIFY_RUNS_PER_WEEK`).
- Xəbər şərhləri: `NEWS_COMMENT_SITES = {"site.az": "comment-css-class"}` - yalnız şərhlər server tərəfindən render olunursa (bax docs/sources.md). Son 3 günün xəbər linkləri yoxlanır.
