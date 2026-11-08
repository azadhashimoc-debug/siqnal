import json
import os
import re
import urllib.request

from radar import config, report

_CB = re.compile(r"^vote:(\d+):(up|down)$")


def handle_callback(conn, data: str, voter: str) -> bool:
    m = _CB.match(data or "")
    if not m:
        return False
    vid = int(m.group(1))
    if conn.execute("SELECT 1 FROM validations WHERE id=?", (vid,)).fetchone() is None:
        return False
    vote = 1 if m.group(2) == "up" else -1
    conn.execute("DELETE FROM votes WHERE validation_id=? AND voter=?", (vid, voter))
    conn.execute("INSERT INTO votes(validation_id, voter, vote) VALUES(?,?,?)", (vid, voter, vote))
    conn.commit()
    return True


def _evidence(conn, topic_id) -> list:
    return conn.execute(
        "SELECT r.text, r.url FROM classifications c JOIN records r ON r.id = c.record_id "
        "WHERE c.topic_id=? GROUP BY r.text_hash LIMIT 20", (topic_id,)).fetchall()


def telegram_post(method: str, payload: dict, files=None):
    """Real transport. files: {field: (filename, bytes)} -> multipart; else JSON."""
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{method}"
    if files:
        b = "----radar" + os.urandom(8).hex()
        body = b""
        for k, val in payload.items():
            val = val if isinstance(val, str) else json.dumps(val)
            body += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{val}\r\n'.encode()
        for k, (name, data) in files.items():
            body += (f'--{b}\r\nContent-Disposition: form-data; name="{k}"; filename="{name}"\r\n'
                     f'Content-Type: text/markdown\r\n\r\n').encode() + data + b"\r\n"
        body += f"--{b}--\r\n".encode()
        req = urllib.request.Request(url, body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    else:
        req = urllib.request.Request(url, json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def send_weekly(conn, http_post, chat_id, validations, report_dir=None) -> None:
    """validations: list of (validation_id, Validation). Plain text, no parse_mode."""
    top = report.top_ideas(validations)
    for vid, v in top:
        path = report.write_report(vid, v, _evidence(conn, v.topic_id), report_dir or config.REPORT_DIR)
        http_post("sendDocument", {"chat_id": chat_id}, {"document": (path.name, path.read_bytes())})
    payload = {"chat_id": chat_id, "text": report.weekly_message(validations)}
    if top:
        payload["reply_markup"] = {"inline_keyboard": [
            [{"text": f"👍 {report.CIRCLED[n]}", "callback_data": f"vote:{vid}:up"},
             {"text": f"👎 {report.CIRCLED[n]}", "callback_data": f"vote:{vid}:down"}]
            for n, (vid, _) in enumerate(top)]}
    http_post("sendMessage", payload)
