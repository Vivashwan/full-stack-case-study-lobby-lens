# LobbyLens — Full Stack Developer Case Study (IGamingCompass)

Welcome, and thanks for taking the time.

**IGamingCompass** tracks online casinos. Every day our scrapers open each casino's lobby
page and record which games are shown, in which section, and in what order. Game studios
(providers) use this to see how visible their games are in each market.

This repo, **LobbyLens**, is a small, simplified slice of that platform: a Django API, a
React front end, a local SQLite database and one month of made-up data. Every casino,
operator, provider and game name is fictional.

We want to see how you:

1. **work with numbers**: do the figures make sense, and do you notice when they don't?
2. **handle a database**: SQL, data quality, indexes
3. **write backend code**: Django REST, tests
4. **write frontend code**: React, state, and loading/empty/error states

## Practicalities

| | |
|---|---|
| Time budget | About **5 hours** of focused work. Please don't spend more than 6. You have **3 calendar days**. |
| Unfinished work | That's fine. Tell us in `NOTES.md` what you would do next. We'd rather see 4 tasks done well than 6 rushed. |
| AI tools / Google / docs | Allowed. Say what you used in `NOTES.md`. In the review call we will ask you to explain and change your code live, so make sure you understand every line. |
| Submission | A private Git repo (share it with us) or a zip. Please commit as you go; we read the history. |
| Review call | 45 minutes. You walk us through your work, then we make one small change together. |

Setup instructions are in [`README.md`](README.md). **Get the app running first.** If you
get stuck on setup for more than 30 minutes, email us. We'd rather help than lose your time.

---

## The data

```
geography ─┐
operator ──┴─ casino ── scrape_run ── game_position ── game ── provider
```

| Table | One row per… | Notes |
|---|---|---|
| `geography` | regulated market | Usually a country, but not always. See `country_code`. |
| `operator` | company running casino brands | |
| `casino` | operator × geography | `is_active = false` means we have stopped tracking it. |
| `provider` | game studio | |
| `game` | game | Belongs to one provider. |
| `scrape_run` | one scraper visit to one casino's lobby | `status` = did the scraper finish; `show_data` = has a reviewer approved this run's data for clients; `tiles_found` = number of tiles recorded. |
| `game_position` | one game tile seen during a run | `section_name` (e.g. "Popular"), `position_in_section` (1-based), `overall_position` (1-based order among tiles visible **without scrolling**; `NULL` = the tile is there but only visible after scrolling a carousel). |

The data covers **29 July – 2 September 2026**. All the questions below are about
**August 2026**.

## Metric definitions (company rules)

These rules apply to **every** report, API and question below unless a question says otherwise.

- **R1 – Approved data only.** Reports use only runs with `show_data = true`.
- **R2 – One run per casino per day.** A casino is sometimes scraped more than once on the
  same day. Only the **latest** approved run of that day counts (latest `started_at`; if tied,
  highest `id`).
- **R3 – Active casinos only.** Casinos with `is_active = false` are excluded from reports.
- **Counted runs** = runs that pass R1–R3.

**Provider Market Share** for a geography *G* and a month *M*:

- A **listing** is a distinct *(casino, game)* pair seen at least once in a counted run of a
  casino in *G* during *M*.
- For each provider:
  - `listings` = number of listings whose game belongs to the provider
  - `unique_games` = distinct games of the provider among those listings
  - `unique_casinos` = distinct casinos among those listings
  - `market_share_pct` = `listings / total listings in G for M × 100`, rounded to 2 decimals
- Providers with no listings are left out.

---

## Part A — Sense of numbers (≈ 60 min)

Answer in **`ANSWERS.md`**. For every data question, include the SQL (or pandas) you used.
Short answers are fine. We care about *why* as much as *what*.

**A1.** For August 2026: how many scrape runs are there, how many are approved, and what is
the approval rate (1 decimal)? Count all runs here, regardless of casino status.

**A2.** How many geographies does the dataset cover? How many countries?

**A3.** Which **active** casino(s) had no approved run at all in August? What would that do to
a report if nobody noticed?

**A4.** On how many casino-days in August is there **more than one approved** run? Pick one
example and describe what looks different between the two runs.

**A5.** Using the Market Share definition, list the **top 5 providers in United Kingdom for
August 2026** with their `listings` and `market_share_pct`. What do all the providers' shares
add up to, and why might that not be exactly 100?

**A6.** What is the **average lobby size** (tiles per counted run) for United Kingdom in
August? Then work out the figure you would get if you ignored R1–R3 and averaged
`tiles_found` over *all* UK runs in August. Which number would you put in front of a client,
and why?

**A7.** For the game **"Hidden Buffalo Megaways"** in United Kingdom, August, counted runs only:

- How many tiles of it were recorded, and what % of them were visible without scrolling?
- What is its average `overall_position` when it *is* visible?
- A colleague replaced `NULL` with `999` and reported an "average position" of about 692.
  Explain what is wrong with that and what you would report instead.

**A8.** No data needed. Show your working.

- (a) A provider's share in Germany went from **8%** in week 1 to **10%** in week 4. A sales
  deck says *"share grew by 2%"*. Is that correct? How would you phrase it?
- (b) We scrape **40 casinos** a day. Each run takes about **6 minutes**, and **2 servers**
  run in parallel. How long does a daily cycle take? If we add **60 more casinos** and want
  the cycle to finish within **3 hours**, how many servers do we need?
- (c) A dashboard shows Spain's provider shares adding up to **112%**. Give two likely causes.

**A9.** List the data-quality issues you noticed while working. For each one, say how you
would handle it (fix the data, filter it out in code, or flag it to someone).

---

## Part B — Database (≈ 45 min)

Files are in `db/`. Run them from `backend/` with `python run_sql.py ../db/<file>.sql`
(other options are in README.md).

**B1.** In `db/provider_market_share.sql`, write **one SQL query** that returns the full
Market Share table for United Kingdom, August 2026 (columns and order are listed in the
file). Its numbers should match your A5 answer.

**B2.** Follow the instructions in `db/slow_query.sql`: read the query plan (SQLite
`EXPLAIN QUERY PLAN`), explain it, and add the index(es) you would use in production
**as a Django migration**. In `ANSWERS.md`, also say whether you would add an index on
`game_position.overall_position`, and why or why not.

**B3.** The `provider` table contains a duplicate. In `db/merge_duplicate_provider.sql`,
write a script that merges it into the correct provider safely. Before you write it, look
at the games involved.

---

## Part C — Backend (≈ 90 min)

Run the tests with `python manage.py test lobby`. Several are failing right now; some are
bugs and some are features you need to build. **Fix the code, not the tests.** (You may
*add* tests.)

**C1. Bug: the Overview numbers are wrong.** Our ops team says: *"The August run count on
the Overview page looks low, and the approval rate always shows 0%. Also, February gives an
error."* Find and fix the cause(s) in `lobby/services.py`.

**C2. Build the Provider Market Share endpoint.**

```
GET /api/provider-market-share/?geography=<id>&month=YYYY-MM
```

- `400` if `geography` or `month` is missing or invalid; `404` if the geography doesn't exist.
- `200` response:

```json
{
  "geography": {"id": 1, "name": "United Kingdom"},
  "month": "2026-08",
  "total_listings": 1234,
  "results": [
    {
      "provider_id": 3,
      "provider_name": "Nimbus Gaming",
      "unique_games": 12,
      "unique_casinos": 7,
      "listings": 80,
      "market_share_pct": 6.48
    }
  ]
}
```

- `results` are sorted by `market_share_pct` descending, then `provider_name` ascending.
- The logic goes in `services.provider_market_share`. You can use the ORM or raw SQL.
- `tests/test_market_share.py` checks the shape. **Add tests for R1, R2 and R3.**
- Its numbers for United Kingdom / 2026-08 should match A5 and B1.

**C3. Performance: `/api/casinos/` is slow.** Our logs show that a single page of casinos
runs dozens of SQL queries (tip: `SQL_DEBUG=1 python manage.py runserver`). Fix it so the
number of queries doesn't grow with the number of casinos on the page.

---

## Part D — Frontend (≈ 90 min)

**D1. Two bugs on the Overview page** (`src/pages/Overview.jsx`). Users report:

1. *"When I change the geography, the KPI cards don't change. Only the table does."*
2. *"If I go to page 2 of the casino list and then pick United Kingdom, I get an error."*

Fix both. In `NOTES.md`, explain the root cause of each in a sentence or two.

**D2. Build the Provider Market Share page** (`src/pages/MarketShare.jsx`), using your C2
endpoint.

Must have:

- a geography dropdown (reuse `GeographySelect`) and a month picker (default `2026-08`)
- a table with Provider, Games, Casinos, Listings and Share %
- sorting when a column header is clicked (click again to reverse the order); default is Share % high → low
- a simple visual cue for share, such as an inline bar (plain CSS is fine; no chart library needed)
- clear **loading**, **empty** ("no data for this selection") and **error** states
- a summary line or footer that helps a reader sanity-check the table: e.g. number of
  providers, total listings, sum of shares, and the combined share of the top 5

Nice to have (only if you have time):

- the selection is kept in the URL query string, so a link can be shared
- a text box to filter providers by name
- a component test (Vitest + Testing Library)

We are not judging visual polish. We are looking at clean components, sensible state, and
whether the numbers on screen are correct and easy to read.

---

## Part E — Notes (≈ 15 min)

Fill in `NOTES.md`:

- how to run your solution, if anything changed
- the decisions you made and why
- what you would do next with more time
- what tools/AI you used and for what

---

## How we'll assess

| Area | Weight |
|---|---|
| Part A – numbers & reasoning | 25% |
| Part B – database | 20% |
| Part C – backend | 25% |
| Part D – frontend | 20% |
| Communication (notes, commits, review call) | 10% |

We look at correctness first, then clarity. Good luck, and enjoy it.
