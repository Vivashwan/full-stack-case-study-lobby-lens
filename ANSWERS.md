# Answers

Please include the query or code you used for each data question.

## Part A

### A1

```sql
SELECT COUNT(*) as total, SUM(CASE WHEN show_data=1 THEN 1 ELSE 0 END) as approved
FROM scrape_run
WHERE run_date BETWEEN '2026-08-01' AND '2026-08-31';
```

**1,279** scrape runs in August 2026, of which **989** are approved (`show_data = true`).
Approval rate = 989 / 1279 × 100 = **77.3%**.

(This counts *all* runs, including inactive casinos and failed/duplicate runs, as the
question asks — it is not the same as "counted runs" under R1-R3.)

### A2

```sql
SELECT COUNT(*) as geographies, COUNT(DISTINCT country_code) as countries FROM geography;
```

**6 geographies**, but only **5 countries**. The US is split into two regulated markets
("US - New Jersey", "US - Pennsylvania") that share `country_code = 'US'` — regulation in
the US happens at state level, so one country can be more than one geography. Everything
else (GB, ES, DE, CA) is a 1:1 country-to-geography mapping.

### A3

```sql
SELECT c.id, c.name, g.name as geography
FROM casino c
JOIN geography g ON g.id = c.geography_id
WHERE c.is_active = 1
  AND NOT EXISTS (
    SELECT 1 FROM scrape_run r
    WHERE r.casino_id = c.id
      AND r.show_data = 1
      AND r.run_date BETWEEN '2026-08-01' AND '2026-08-31'
  );
```

**Brightmoor ES** (Spain) is the only active casino with zero approved runs in August.
Looking closer, this is *not* a scraper outage: it has 31 runs in August, almost all
`status = 'success'` with 77-89 tiles recorded, but **every single one has
`show_data = 0`** — none were ever reviewed/approved. So the scraper is working; the
review step never happened for this casino all month.

If nobody noticed: Brightmoor ES would silently vanish from every August report (its
listings, its casino count, its contribution to Spain's provider shares) with no error
or warning anywhere — reports would just look "normal" but be quietly wrong, understating
Spain's total tile counts and skewing Spanish market share among the casinos that *were*
approved. A monthly "active casino with 0 counted runs" check would catch this.

### A4

```sql
SELECT casino_id, run_date, COUNT(*) as n
FROM scrape_run
WHERE show_data = 1 AND run_date BETWEEN '2026-08-01' AND '2026-08-31'
GROUP BY casino_id, run_date
HAVING COUNT(*) > 1;
```

**27 casino-days** in August have more than one approved run (always exactly 2).

Example: **casino_id = 4, 2026-08-09** — runs `id=474` (started 05:51, 78 tiles) and
`id=475` (started 08:46, 84 tiles). Both are `status='success'` and `show_data=1`. The
later run recorded 6 more tiles than the earlier one — plausibly the lobby was updated
between scrapes (a new promo/section added), or the earlier scrape caught the page
mid-load. Under **R2**, only the later run (`id=475`, higher `started_at`) counts.

### A5

See [db/provider_market_share.sql](db/provider_market_share.sql) for the full query (also
used for B1). Top 5, United Kingdom, August 2026:

| provider_id | provider_name | listings | market_share_pct |
|---|---|---|---|
| 1 | Aurora Play | 659 | 40.63 |
| 2 | Red Fox Studios | 254 | 15.66 |
| 3 | Nimbus Gaming | 170 | 10.48 |
| 4 | Blue Harbor Games | 87 | 5.36 |
| 5 | Ironleaf Interactive | 67 | 4.13 |

All 23 providers' shares sum to **99.98%**, not exactly 100. Each provider's percentage is
independently rounded to 2 decimals (`listings / total × 100`, rounded), and rounding 23
separate numbers loses a small amount each time; those roundings don't cancel out to
exactly zero. This is expected rounding drift, not a bug — with 23 providers here it would
take an unlikely coincidence to land on exactly 100.00.

(Note for A9: providers 1 and 25 are both named "Aurora Play" — see B3. The 40.63% above
is understated because 1.66% of listings are still sitting under the duplicate id=25 row.
The true combined Aurora Play share is ~42.29%.)

### A6

Average lobby size (tiles per **counted** run, R1-R3), United Kingdom, August:

```sql
-- tiles_found of the counted runs only (see counted_runs CTE in provider_market_share.sql)
SELECT COUNT(*) as n_runs, ROUND(AVG(tiles_found),2) as avg_tiles FROM counted_runs;
```
→ **226 runs, average 81.13 tiles.**

Ignoring R1-R3 (averaging `tiles_found` over *all* UK runs in August, any status, any
casino, all same-day duplicates included):

```sql
SELECT COUNT(*) as n_runs, ROUND(AVG(tiles_found),2) as avg_tiles
FROM scrape_run r JOIN casino c ON c.id = r.casino_id
WHERE c.geography_id = 1 AND r.run_date BETWEEN '2026-08-01' AND '2026-08-31';
```
→ **299 runs, average 74.65 tiles.**

I'd put **81.13** in front of a client. The raw 74.65 figure is dragged down by runs that
should never be in a client-facing report: failed runs with `tiles_found = 0`, runs from
casinos we've stopped tracking (`is_active = false`), and duplicate same-day runs (which
also double-count some casino-days). None of that reflects what a player actually sees in
a real lobby; the counted-runs figure does.

### A7

Hidden Buffalo Megaways (game_id 305), United Kingdom, August, counted runs only:

```sql
SELECT
  COUNT(*) AS total_tiles,
  SUM(CASE WHEN overall_position IS NOT NULL THEN 1 ELSE 0 END) AS visible_tiles,
  ROUND(100.0 * SUM(CASE WHEN overall_position IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_visible,
  ROUND(AVG(CASE WHEN overall_position IS NOT NULL THEN overall_position END), 2) AS avg_position_when_visible
FROM game_position gp JOIN counted_runs cr ON cr.id = gp.run_id
WHERE gp.game_id = 305;
```

- **203 tiles** recorded in total; **63 of them (31.0%)** were visible without scrolling.
- Average `overall_position` **when visible: 8.6**.
- Replacing `NULL` with `999` and averaging all 203 gives **691.64** — close to the
  colleague's ~692. The bug: `NULL` doesn't mean "very low rank", it means **"not ranked
  at all — only reachable by scrolling a carousel"**. Treating the 69% of tiles that are
  off-screen as if they were rank-999 tiles manufactures a huge, meaningless number that
  makes the game look almost universally buried, when in fact when it *is* on the visible
  first screen, it's usually near the top (average rank 8.6). I would report the two facts
  separately: **"visible without scrolling in 31.0% of listings; when visible, averages
  position 8.6."** Collapsing them into one "average position" number hides the more
  important story (most of the time it isn't on-screen at all).

### A8

**(a)** No. 8% → 10% is a **2 percentage-point** increase, not "2%". A genuine 2% *relative*
increase from 8% would only take it to 8.16%. Correct phrasing: *"share grew by 2
percentage points (from 8% to 10%), a relative increase of 25%."* Both the absolute (pp)
and relative (%) framing are legitimate — the point is not to write "2%" when you mean
"2pp," since a reader will assume the wrong one and the two numbers differ a lot here.

**(b)** 40 casinos ÷ 2 servers = 20 runs per server. 20 × 6 min = **120 minutes = 2 hours**
for the current daily cycle. Adding 60 more casinos → 100 casinos total. To finish within
**3 hours (180 min)**: each server can do 180 / 6 = 30 runs in that window. 100 casinos /
30 runs-per-server = 3.33, so **4 servers** are needed (3 would leave one server with 34
runs = 204 min, over budget).

**(c)** Two likely causes for shares summing to 112% in Spain:
1. **A duplicate provider or duplicate game row** (structurally identical to the Aurora
   Play case in this dataset) — the same underlying game gets counted as if it were two
   providers, or a listing gets double-counted because it matches two provider rows for
   what is really one studio, inflating the total past 100%.
2. **R2 not applied (or applied inconsistently) when the dashboard was built** — if
   same-day duplicate approved runs aren't deduplicated to "latest only," some
   (casino, game) listings get counted twice (once per duplicate run), inflating every
   provider's `listings` and therefore every share, without necessarily changing which
   provider comes out on top.

(Rounding drift, per A5, could realistically add or subtract a few *hundredths* of a
percent, not 12 percentage points — so it's very unlikely to be the explanation on its
own here.)

### A9

Data-quality issues I noticed, and how I'd handle each:

1. **Duplicate provider row** — `provider.id = 1` and `id = 25` are both "Aurora Play"
   (87 games vs 6 games; one game, "Royal Safari", exists identically under both — same
   name, `game_type`, and `release_date`). *Handling:* fix the data — merge it
   permanently at the source (see [db/merge_duplicate_provider.sql](db/merge_duplicate_provider.sql)),
   since as long as it exists every market-share report for every geography silently
   understates Aurora Play's true share and shows a spurious 24th "provider" in the list.

2. **Approved-review backlog** — 214 runs are `status='success'` (scraper worked fine)
   but `show_data=0` (never reviewed/approved), concentrated enough on some casinos
   (e.g. Brightmoor ES, all 31 August runs unapproved) that the casino disappears from
   reports entirely with no visible error (see A3). *Handling:* flag it to whoever owns
   the review queue/SLA — this is a process gap, not something to silently filter around
   in code (filtering it out is *already* R1's job; the point is someone should notice
   when a whole casino has gone dark for a month).

3. **`overall_position = NULL` is easy to misinterpret** — it means "exists, but only
   visible after scrolling," not "worst possible rank" or "missing data." A naive
   `COALESCE(overall_position, some_big_number)` (as in A7) silently produces a nonsense
   metric. *Handling:* this is a filter-it-out-in-code (and document-it-clearly) issue —
   any position-based average must explicitly restrict to `WHERE overall_position IS NOT
   NULL` and separately report visibility rate; I'd add a code comment/docstring wherever
   this column is aggregated to prevent the mistake being repeated (I did so in
   `services.py` and the SQL files here).

4. **Per-provider rounding drift** — market shares are rounded independently per row, so
   they don't sum to exactly 100% (A5: 99.98%). *Handling:* not a bug to fix — just worth
   a one-line footnote wherever the numbers are shown (the frontend summary line in D2
   states the actual sum so a reader isn't confused by "99.98%" or "112%"-style totals).

## Part B

### B1
See [db/provider_market_share.sql](db/provider_market_share.sql). Verified to produce the
same top-5 and same `market_share_pct` values as A5 (ran with
`python run_sql.py ../db/provider_market_share.sql`).

### B2

Plan before (no index beyond Django's auto FK indexes):

```
SEARCH c USING COVERING INDEX casino_geography_id_2d3aa729 (geography_id=?)
SEARCH r USING INDEX scrape_run_casino_id_8bd50b5f (casino_id=?)
SEARCH gp USING COVERING INDEX game_position_run_id_dae7b9aa (run_id=?)
USE TEMP B-TREE FOR GROUP BY
```

What the plan does, table by table:
- **casino**: cheap — uses the FK index on `geography_id` to jump straight to the ~9 UK
  casinos. Not the bottleneck.
- **scrape_run**: for *each* of those casinos, it searches the FK index on `casino_id`
  only — meaning it reads **every run that casino has ever had**, of any status, any
  `show_data`, any date — and only *after* fetching each row does it check
  `show_data = 1` and the date range in a filter step. In production (~40M rows across
  many casinos over a long history) this means reading and discarding the large majority
  of each casino's run history just to keep one August's worth of approved runs.
- **game_position**: for each surviving run it does a covering-index lookup on `run_id`.
  This part isn't wasteful *given* the runs found above — every position row read here
  belongs to a run that already passed the filters, so nothing is thrown away at this
  step. At ~3B rows in production this is still the most expensive step in absolute
  I/O, but it's proportional to genuinely-needed rows, not wasted work.
- **GROUP BY** materializes a temp B-tree to sort/group by `run_date` — fine at this
  scale; would only be worth avoiding via an already-sorted index if `run_date` grouping
  itself became a bottleneck, which it isn't here relative to the scan above.

Index added (as a Django migration, `ScrapeRun.Meta.indexes`):

```python
models.Index(fields=["casino", "run_date", "show_data"], name="scraperun_casino_date_show_idx")
```

Column choice/order: `casino_id` first because that's how the plan already arrives at
`scrape_run` (one casino at a time, driven by the outer loop over casinos) — matching the
existing access path rather than fighting it. `run_date` second because a `BETWEEN` range
scan needs to be the next-most-selective, equality-or-range column immediately after the
leading equality column for SQLite to use it as a genuine range seek rather than a
post-filter. `show_data` last: it's a low-cardinality boolean so it doesn't help narrow
the *seek*, but putting it in the index still makes the whole index **covering** for this
query's WHERE clause, so SQLite can check it during the index scan instead of fetching
the full row for every candidate.

Plan after (`python manage.py migrate` applied, same `EXPLAIN QUERY PLAN` re-run):

```
SEARCH c USING COVERING INDEX casino_geography_id_2d3aa729 (geography_id=?)
SEARCH r USING COVERING INDEX scraperun_casino_date_show_idx (casino_id=? AND run_date>? AND run_date<?)
SEARCH gp USING COVERING INDEX game_position_run_id_dae7b9aa (run_id=?)
USE TEMP B-TREE FOR GROUP BY
```

The `scrape_run` step now seeks directly on `casino_id=? AND run_date>? AND run_date<?`
(with `show_data` filtered within the same covering index) instead of scanning every run
of the casino — the exact waste identified above is gone.

**Index on `game_position.overall_position`?** No. Nothing in this query (or in the
market-share metric, or in the `services.py` KPIs) filters or sorts by
`overall_position` — it's only ever *read* for rows that are already narrowed down by
`run_id` (A7's visibility %/average-position calculation happens after the row set is
fixed). An index only pays for itself when it lets the database seek/sort on that column;
here it would add write overhead to every tile insert on a 3-billion-row table (in
production) for a column that's never used to filter or order rows — pure cost, no
benefit for this access pattern.

### B3
See [db/merge_duplicate_provider.sql](db/merge_duplicate_provider.sql). Summary: provider
`id=25` is a duplicate of `id=1` (both "Aurora Play"). One of its 6 games ("Royal Safari",
`id=408`) is itself a duplicate of an existing game (`id=3`, same name/type/release date)
under provider 1 — so its `game_position` history (168 rows) is re-pointed onto the
original game_id before the duplicate game row is deleted; the other 5 games are simply
re-pointed to provider 1. Both `game.provider_id` and `game_position.game_id` are
`ON DELETE PROTECT`, so the script updates children before deleting parents (a wrong
order would raise `IntegrityError` immediately rather than silently orphaning data, but I
still wrote it in the correct dependency order rather than relying on that). Tested against
the real database (168 + 5 rows moved as expected, both duplicate rows cleanly removed),
then restored with `python manage.py load_data` before continuing.
