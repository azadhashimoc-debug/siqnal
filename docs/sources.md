# Source List (v1 seed)

Status: **D** = URL confirmed by web search. **Y** = must be checked during Task 3.
Selection rule: we pick sources with **complaints and comments**. Pure official announcements are less useful. Regulation channels are the exception, because new laws are a signal.

## RSS news
| Source | URL | Status | Why |
|---|---|---|---|
| Oxu.az | https://oxu.az/feed | D | High traffic, social and price news |
| Sia.az | https://sia.az/feed.php | D | Social problems, complaint news |
| AzerNews | https://www.azernews.az/feed.php | D | Business/economy (EN) |
| stat.gov.az | https://stat.gov.az/rss/en | D | Price and market statistics |
| Report.az | economy section, feed TBD | Y | Economy/regulation |
| APA.az | feed TBD | Y | Main news agency |
| Qafqazinfo.az | feed TBD | Y | Social news, active comments |
| Azertac | feed TBD | Y | Regulation, decrees |
| Trend.az | feed TBD | Y | Business |

### User's existing feeds (from the legacy script)
| Source | URL | Note |
|---|---|---|
| Oxu.az | https://oxu.az/rss | Directory shows `/feed`. Test both and keep the working one |
| Qafqazinfo | https://qafqazinfo.az/rss | Y |
| APA | https://apa.az/rss | Y |
| Marja.az | https://marja.az/rss | Y, new candidate |
| Modern.az | https://modern.az/rss | Y |

The user's existing `SIGNAL_PATTERNS` (3 categories, 42 words) stay as the prefilter. Task 4 adds suffix tolerance (stem matching, for example `bahalaş`) so Azerbaijani word endings still match.

## News comment pages
Candidates: Qafqazinfo, Oxu.az, Sia.az, Modern.az. For each site, Task 3 checks whether comments are in HTML. If comments load through JS or Facebook plugin, drop the site.

## Telegram (public)
- `@economy_az`: Ministry of Economy (regulation, subsidies). D
- `@economy_azru`: same ministry, Russian. D
- Popular news and complaint channels: pick the top 10 AZ channels from TGStat/Telemetr. Filter by country=AZ and category news/economy. Y

## YouTube
Seed: AZ economy and social channels, plus channels where citizens' problems get covered and comments are active. Use `search.list` with `regionCode=AZ` and the queries "qiymət", "vergi", "problem", "şikayət". From the videos of the last 30 days, take the 15 channels with the most comments. Y

## Instagram / Facebook (Apify)
Use the top 10 AZ news pages by followers (news pages have the busiest comment sections). Find them once with the Apify search actor and freeze the list in `config.APIFY_PAGES`. Y

## Google Maps reviews (Apify)
For Baku, use categories with high complaint potential: courier/delivery, private clinic, auto service, bank branch, internet provider, real estate agency. Take 1–3 star reviews only.

## Automatic source quality
Every 4 weeks, compute `yield = number of classifications that fed a candidate topic / number of records` for each source. Mark sources in the bottom 20% as `disabled`. The list then cleans itself.

## Task 3 live check results (2026-11-08)
RSS URLs were fetched with a 8s timeout and parsed as XML.

| Source | URL | Result |
|---|---|---|
| Oxu.az | https://oxu.az/feed | working (50 items). Kept. |
| Oxu.az | https://oxu.az/rss | dead: HTTP 404. Dropped. |
| Qafqazinfo | https://qafqazinfo.az/rss | working (100 items). Kept. |
| APA | https://apa.az/rss | working (50 items). Kept. |
| Modern.az | https://modern.az/rss | working (30 items). Kept. |
| Sia.az | https://sia.az/feed.php | working (25 items). Kept. |
| AzerNews | https://www.azernews.az/feed.php | working (25 items). Kept. |
| Marja.az | https://marja.az/rss | dead: HTTP 404. Dropped. |
| stat.gov.az | https://stat.gov.az/rss/en | dead: connection reset by server. Dropped (may be blocking scripted clients; retry later). |
| Report.az, Azertac, Trend.az | feed TBD | not checked: no candidate URL known. |

Not done in Task 3 (need API keys or manual discovery); config lists are empty with a TODO:
- Telegram channel discovery (`TELEGRAM_CHANNELS`), YouTube channel discovery (`YOUTUBE_CHANNELS`), Apify actors and pages (`APIFY_ACTORS`).
- News comment selectors (`NEWS_COMMENT_SITES`): not filled. Server-rendered comments were not confirmed from fetched article HTML, so no site is enabled. The adapter works once a `{domain: class}` pair is added.
