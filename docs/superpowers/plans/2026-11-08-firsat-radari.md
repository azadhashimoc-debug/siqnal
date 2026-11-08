# Fırsat Radarı Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collect Azerbaijani news and comments, detect rising problem topics, have an AI agent validate them, and send a weekly Telegram report of 3–5 validated business ideas with 👍/👎 feedback.

**Architecture:** Source adapters normalize every input into one `Record`. Records go to SQLite, pass a cheap keyword prefilter, and get LLM-classified (Haiku). Topics are clustered and tracked per day; rising topics become candidates. A Sonnet agent with web_search validates each candidate. The weekly report goes to Telegram, and a bot stores the votes.

**Tech Stack:** Python 3.11+, sqlite3 (stdlib), anthropic SDK, feedparser, beautifulsoup4, google-api-python-client (YouTube), telethon, apify-client, python-telegram-bot, rapidfuzz, pytest.

**Spec:** `C:\Users\adem\.claude\plans\elimde-bele-bir-fikir-agile-fiddle.md`

## Global Constraints
- Models: classification `claude-haiku-5-5`, validation `claude-sonnet-5-5` with the server `web_search` tool.
- Store no personal data from comments (author name, profile URL, avatar). Store only the text, link, date and source.
- Weekly validation cap: `MAX_VALIDATIONS_PER_WEEK = 15`. Apify cap: `MAX_APIFY_RUNS_PER_WEEK` (default 10).
- Report: at most 5 ideas, and only ideas with decision `gec`.
- Every claim in a validation must carry at least one URL. If a claim has no URL, drop it.
- The agent stays skeptical. The prompt must say that the default decision is `reddet`.
- Secrets come only from env vars: `ANTHROPIC_API_KEY`, `YOUTUBE_API_KEY`, `TG_API_ID`, `TG_API_HASH`, `APIFY_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- First version sources: RSS news, news comments, Telegram, YouTube, Apify (Instagram/FB/Google Maps). Not in v1: tap.az, boss.az, Reddit.
- Text is Azerbaijani. Keep it UTF-8 everywhere and never ASCII-fold it.

## Review Focus
1. A source fails (timeout, HTTP 403, quota exceeded). The run continues, logs the failure, and the other sources still get collected. This goes in Task 3: `test_collect_survives_failing_adapter`.
2. The same link arrives with `utm_*` or `fbclid` parameters. It becomes one record. This goes in Task 2: `test_normalize_strips_tracking`.
3. The LLM returns invalid JSON or JSON with missing fields. The record is marked `classify_failed` and does not crash the run. This goes in Task 4: `test_classify_bad_json`.
4. One person spams the same complaint 20 times. It must not count as 20 distinct voices. Count distinct `text_hash`, not records. This goes in Task 5: `test_trend_ignores_duplicate_comments`.
5. A week with zero `gec` ideas sends a short "bu hafta güçlü fırsat yok" message and does not crash. This goes in Task 7: `test_report_empty_week`.

---

### Task 1: Project skeleton, config, DB schema

**Files:**
- Create: `radar/config.py`, `radar/db.py`, `radar/models.py`, `pyproject.toml`, `tests/test_db.py`

**Interfaces:**
- Produces: `Record` dataclass with fields `source: str, kind: Literal["news","comment"], url: str, text: str, published: datetime, parent_url: str | None`.
- Produces: `db.connect(path: str) -> sqlite3.Connection`, which creates the tables `records`, `classifications`, `topics`, `topic_days`, `validations`, `votes`, `apify_runs`.
- Produces: `db.insert_record(conn, rec: Record) -> bool`. It returns False when the record is a duplicate. The unique key is `(url_norm, text_hash)`.

- [ ] Test `test_insert_duplicate_returns_false`: insert the same Record twice. Expect `True`, then `False`.
- [ ] Run `pytest tests/test_db.py -v` and check that it FAILS.
- [ ] Implement it. `text_hash` = sha1 of the lowercased, whitespace-collapsed text.
- [ ] Run the test again and check that it PASSES.
- [ ] `git init` and commit with the message `feat: skeleton and db schema`.

### Task 2: Normalization

**Files:** Create `radar/normalize.py` and `tests/test_normalize.py`.

**Interfaces:** Produces `normalize_url(url: str) -> str` and `clean_html(s: str) -> str`.

- [ ] Write the tests:
  - `test_normalize_strips_tracking`: `normalize_url("https://a.az/x?utm_source=fb&id=5&fbclid=z")` returns `"https://a.az/x?id=5"`.
  - `test_clean_html`: `"<p>Qiymət &amp; vergi</p>"` returns `"Qiymət & vergi"`.
- [ ] Run the tests and check that they FAIL. Implement the functions. Run the tests and check that they PASS. Commit.

### Task 3: Source adapters + collect

**Files:**
- Create: `radar/sources/base.py`, `rss.py`, `news_comments.py`, `youtube.py`, `telegram_src.py`, `apify_src.py`, `radar/collect.py`, `tests/test_collect.py`.

**Interfaces:**
- Produces: `class Source(Protocol): name: str; def fetch(self) -> Iterable[Record]`.
- Produces: `collect(conn, sources: list[Source]) -> dict[str, int]`. It returns the count of new records per source, and the count is `-1` for a failed source.
- Migrate `rss.py` from the user's existing script. Reuse `FEEDS`, the User-Agent and `ET` parsing. Move `FEEDS` into `config.py`.
- `news_comments.py`: one CSS selector config per site, stored in `config.NEWS_COMMENT_SITES` as `{domain: selector}`. Comments get `kind="comment"` and `parent_url` set to the article.
- `youtube.py`: use the `YOUTUBE_CHANNELS` list, take the last 7 days of videos, and fetch `commentThreads`.
- `telegram_src.py`: use Telethon to read the `TELEGRAM_CHANNELS` public channels, and for each channel only the messages after the last seen id.
- `apify_src.py`: use the actor IDs in `config.APIFY_ACTORS`. Check `apify_runs` against `MAX_APIFY_RUNS_PER_WEEK` before each run.
- Every adapter drops author fields.
- Seed list: `docs/sources.md`. Check each `Y` row live (feed URL, whether comments are in HTML, Telegram/YouTube/Apify discovery), then freeze the working ones in `config.py`. Drop dead sources and write down why in `docs/sources.md`.
- Add `source_yield(conn, weeks=4) -> dict[str, float]` and `disable_low_yield(conn)` (bottom 20%). Test: `test_low_yield_source_disabled`.

- [ ] Write the tests with fake sources:
  - `test_collect_survives_failing_adapter`: one source raises an error, and the other source's records are still saved. The result has `-1` for the failed source.
  - `test_apify_cap`: when `apify_runs` already holds the cap for this week, `fetch()` returns empty and makes no client call. Use a mock client.
- [ ] Run the tests and check that they FAIL. Implement the code. Run the tests and check that they PASS. Commit.

### Task 4: Prefilter + LLM classification

**Files:** Create `radar/prefilter.py`, `radar/classify.py` and `tests/test_classify.py`.

**Interfaces:**
- Produces: `prefilter(text: str) -> bool`. It reuses the user's `SIGNAL_PATTERNS` (copy from `legacy/signal_pipeline.py`), moved into `config.py`. Match keyword stems so Azerbaijani suffixes still match. Test: `test_prefilter_suffix`: `"çörək bahalaşacaq"` matches the keyword `"bahalaşma"`, because both share the stem `bahalaş`.
- Produces: `classify(client, rec_text: str) -> Classification | None` with the fields `category, is_problem: bool, affected_group: str, urgency: int(1-5), willingness_to_pay: int(1-5), score: int(0-100), topic_label: str, evidence: str`.
- Produces: `classify_pending(conn, client, limit=200) -> int`.
- Use `claude-haiku-5-5` with structured JSON output. The `topic_label` must be a short Azerbaijani noun phrase.

- [ ] Write the tests with a stub client:
  - `test_classify_bad_json`: the stub returns `"not json"`. The function returns `None`, and the row is marked `classify_failed`.
  - `test_score_out_of_range_rejected`: the stub returns `score: 140`. The function returns `None`.
- [ ] Run the tests and check that they FAIL. Implement the code. Run the tests and check that they PASS. Commit.

### Task 5: Topic clustering + trend detection

**Files:** Create `radar/trends.py` and `tests/test_trends.py`.

**Interfaces:**
- Produces: `assign_topic(conn, label: str) -> int`. It uses `rapidfuzz` `token_set_ratio >= 80` against the existing topics. Otherwise it creates a new topic.
- Produces: `update_topic_days(conn, day: date)`, which counts per topic per day: `distinct_voices` (distinct `text_hash`), `distinct_sources`, `avg_score`.
- Produces: `candidates(conn, today: date) -> list[int]`. A topic is a candidate when the last 7 days compared with the previous 21 days show distinct_voices growth `>= 2x`, distinct_sources `>= 2`, and avg_score `>= 60`. Put the thresholds in `config.py`.

- [ ] Write the tests:
  - `test_trend_ignores_duplicate_comments`: 20 records with the same text count as 1 voice.
  - `test_candidate_requires_two_sources`: rising voices from a single source give no candidate.
  - `test_similar_labels_merge`: `"çörək qiyməti artımı"` and `"çörək qiymətinin artımı"` get the same topic id.
- [ ] Run the tests and check that they FAIL. Implement the code. Run the tests and check that they PASS. Commit.

### Task 6: Validation agent

**Files:** Create `radar/validate.py`, `radar/prompts/validate.md` and `tests/test_validate.py`.

**Interfaces:**
- Produces: `validate_topic(client, conn, topic_id: int) -> Validation` with the fields `demand, competition, willingness_to_pay, timing` (each `{score: 0-10, claims: [{text, url}]}`), `decision: Literal["gec","izle","reddet"]`, `problem: str`, `solutions: list[Solution]`, `risks: list[str]`.
- `Solution` fields: `title: str`, `how_it_works: str`, `business_model: str` (who pays and how), `start_cost: Literal["az","orta","yuksek"]` (rough AZN range in text), `difficulty: int(1-5)`, `first_step: str`, `competitor_urls: list[str]`.
- The agent produces **3–5 different solution paths** for each problem. The paths must differ in kind: for example, one digital product, one service or agency, and one physical or reseller model. At least one path must have `start_cost="az"`. The agent ranks the paths by fit, and the best one comes first.
- Produces: `validate_week(client, conn) -> list[Validation]`. It respects `MAX_VALIDATIONS_PER_WEEK` and sorts candidates by trend strength.
- Use `claude-sonnet-5-5` with the `web_search` tool. The input is the topic label plus up to 20 evidence texts and their URLs. Limit votes history to 10 recent 👍/👎 examples, which the prompt receives as calibration.
- The prompt includes every file in `docs/calibration/*.md` as a "target specificity" example. The output must name concrete platforms, user groups and AZN prices, and split the problem into sub-pains. Each sub-pain maps to a solution feature.
- `Validation` adds these fields: `sub_pains: list[str]`, `market_size: {estimate: str, url: str|None}`, `unverified_claims: list[str]`. A number with no URL goes into `unverified_claims`.
- Post-process: drop claims with no URL. If any dimension has 0 claims left, force `decision` to at most `izle`.

- [ ] Write the tests with a stub client:
  - `test_claims_without_url_dropped`.
  - `test_no_evidence_downgrades_gec`: all demand claims have no URL, so the stub's `gec` becomes `izle`.
  - `test_weekly_cap`: with 20 candidates, the agent makes at most 15 calls.
  - `test_solutions_count_and_cheap_option`: when the stub returns 2 solutions or none with `az`, validation fails and retries once, then marks the topic `izle`.
- [ ] Run the tests and check that they FAIL. Implement the code. Run the tests and check that they PASS. Commit.

### Task 7: Report + Telegram bot + votes

**Files:** Create `radar/report.py`, `radar/bot.py` and `tests/test_report.py`.

**Interfaces:**
- Produces: `render_report(v: Validation, evidence) -> str`, a Markdown string with these sections: Problem, Kanıtlar, Talep, Ödəmə gücü, **Həll yolları** (one subsection per solution: how it works, who pays, start cost, difficulty, competitors, first step), Risklər.
- In the Telegram message, each idea shows the problem line plus the solution titles with their cost tag, for example `① Online növbə SaaS (orta) ② Klinikalara növbə operatoru xidməti (az) ③ ...`.
- Produces: `weekly_message(validations) -> str`, which picks the top 5 `gec` ideas. It sends one line per idea: the summary, the score and the report link.
- Write the report files to `REPORT_DIR`, served as static files. They can also be sent as Telegram documents when there is no web host. Default: send as documents.
- `bot.py`: `send_weekly(...)` uses inline buttons `vote:<validation_id>:up|down`. The callback stores the vote in `votes`.

- [ ] Write the tests:
  - `test_report_empty_week`: no `gec` ideas gives the message `"Bu həftə güclü fürsət yoxdur."`.
  - `test_max_five`: with 8 `gec` ideas, the message lists 5.
  - `test_vote_callback_saves`: the callback data `vote:3:up` creates a row in `votes`.
- [ ] Run the tests and check that they FAIL. Implement the code. Run the tests and check that they PASS. Commit.

### Task 8: CLI + Modal deployment

**Files:** Create `radar/__main__.py`, `modal_app.py` and `README.md`.

**Interfaces:** Consumes everything above. Produces the local CLI `python -m radar collect|weekly` and the Modal app `firsat-radari`.
- Hosting is on **Modal** (user decision). It replaces VPS and systemd.
- Image: `modal.Image.debian_slim().pip_install_from_pyproject("pyproject.toml")`.
- Persistence: `modal.Volume.from_name("radar-data", create_if_missing=True)` mounted at `/data`. It holds `radar.db`, the Telethon `.session` and the reports. Call `volume.commit()` at the end of every function.
- Secrets: `modal.Secret.from_name("radar-secrets")` with every env var from Global Constraints.
- `collect`: `@app.function(schedule=modal.Cron("0 */3 * * *"), timeout=1800)`.
- `weekly`: `@app.function(schedule=modal.Cron("0 5 * * 1"), timeout=3600)`. That is 05:00 UTC, which is 09:00 Asia/Baku.
- Votes: there is no long-running bot. Use `@modal.fastapi_endpoint(method="POST")` as the Telegram webhook, and register it once with `setWebhook`. Handle `callback_query` and write to the `votes` table.
- Concurrency: functions use `max_containers=1`, so two writers never touch SQLite at the same time.

- [ ] Run a smoke test with real keys and the RSS source only: `modal run modal_app.py::collect`. Expect `>0` records in `/data/radar.db`.
- [ ] Run `modal run modal_app.py::weekly` against a test chat. Expect a message to arrive.
- [ ] Run `modal deploy modal_app.py`, then set the webhook. A button press must create a vote row.
- [ ] Write the README with the Modal secret and volume setup, the webhook command and the deploy steps. Commit.
