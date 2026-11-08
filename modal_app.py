"""Modal deployment. Only this file imports `modal`."""
import modal

try:  # present in the container; optional locally
    from fastapi import HTTPException, Request
except ImportError:
    HTTPException = Request = None

app = modal.App("firsat-radari")
volume = modal.Volume.from_name("radar-data", create_if_missing=True)
secrets = [modal.Secret.from_name("radar-secrets")]

image = (
    modal.Image.debian_slim()
    .pip_install_from_pyproject("pyproject.toml")
    .pip_install("fastapi[standard]")
    .env({
        "RADAR_DB_PATH": "/data/radar.db",
        "RADAR_REPORT_DIR": "/data/reports",
        "RADAR_TG_SESSION": "/data/radar",
        "RADAR_PROMPT_PATH": "/root/radar/prompts/validate.md",
        "RADAR_CALIBRATION_DIR": "/root/docs/calibration",
    })
    .add_local_python_source("radar")
    .add_local_dir("radar/prompts", "/root/radar/prompts")
    .add_local_dir("docs/calibration", "/root/docs/calibration")
)

COMMON = dict(image=image, secrets=secrets, volumes={"/data": volume}, max_containers=1)


def _conn():
    from radar import config, db
    conn = db.connect(config.DB_PATH)
    db.migrate(conn)
    return conn


def _run_locked(job, ttl):
    from radar import runner
    runner.run_locked(volume, modal.Dict.from_name("radar-votes", create_if_missing=True),
                      modal.Dict.from_name("radar-lock", create_if_missing=True), ttl, _conn, job)


def _collect_job(conn):
    from radar import pipeline
    return pipeline.run_collect(conn)


def _weekly_job(conn):
    from radar import bot, pipeline
    return pipeline.run_weekly(conn, pipeline.make_client(), bot.telegram_post)


@app.function(schedule=modal.Cron("0 */3 * * *"), timeout=1800, **COMMON)
def collect():
    _run_locked(_collect_job, 1800)


@app.function(schedule=modal.Cron("0 5 * * 1"), timeout=3600, **COMMON)
def weekly():
    _run_locked(_weekly_job, 3600)


@app.function(**COMMON)
@modal.fastapi_endpoint(method="POST")
def webhook(update: dict, request: Request):
    import hmac
    import os
    from radar import bot

    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
    got = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secret or not hmac.compare_digest(got, secret):
        raise HTTPException(status_code=403, detail="forbidden")
    cb = update.get("callback_query")
    if not cb:
        return {"ok": True}
    parsed = bot.parse_callback(cb.get("data", ""))
    if parsed:
        votes = modal.Dict.from_name("radar-votes", create_if_missing=True)
        votes[f"{parsed[0]}:{cb['from']['id']}"] = parsed[1]
    try:
        bot.telegram_post("answerCallbackQuery", {
            "callback_query_id": cb["id"], "text": "Səs qeydə alındı" if parsed else "Keçərsiz"})
    except Exception as e:
        print("answerCallbackQuery failed:", e)
    return {"ok": True}
