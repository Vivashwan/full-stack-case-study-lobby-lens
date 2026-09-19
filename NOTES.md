# Notes

## How to run
Nothing changed from README.md. One addition: `npm test` (Vitest + Testing Library)
now exists for the frontend, alongside `npm run dev`/`npm run build`.

## Decisions and trade-offs

- **B2 index** — added a single composite index,
  `scrape_run(casino_id, run_date, show_data)`, as a Django migration
  (`0002_scraperun_scraperun_casino_date_show_idx.py`) rather than several
  single-column indexes. Column order matches the access path the query planner
  already uses (casino-by-casino, then a date range, then a boolean), and putting
  `show_data` last still makes the index covering for this query without helping the
  seek itself. See `ANSWERS.md` -> B2 for the before/after `EXPLAIN QUERY PLAN`. I
  decided *against* an index on `game_position.overall_position` - nothing in the
  metric or the slow query filters/sorts on it, so an index there would only add
  write cost on a very large table for no read benefit.

- **C2 implementation** — did the "latest run per casino-day" (R2) with a SQL window
  function (`Window(RowNumber(), partition_by=..., order_by=...)`), then materialised
  the distinct (casino, game) listing pairs in Python before aggregating per provider.
  I tried doing the whole thing as one chained ORM queryset
  (`.values(...).distinct().annotate(Count(...))`) first, but that doesn't compose the
  way it looks like it should: the `annotate` re-joins against the un-distincted rows
  and silently inflates every count (I caught this by comparing the endpoint's numbers
  against the SQL query I'd already validated for A5/B1 - they didn't match until I
  switched to two explicit steps). The final version's numbers match A5 and B1
  exactly for United Kingdom/2026-08.

- **C3 fix** — `select_related("operator", "geography")` plus one
  `annotate(approved_runs_count=Count("runs", filter=Q(runs__show_data=True)))` on the
  queryset, instead of the three per-row lookups (`operator.name`, `geography.name`,
  `.runs.filter(...).count()`) the serializer used to do. Query count is now constant
  regardless of page size (verified by the existing
  `test_query_count_does_not_grow_with_page_size` test, and manually with
  `SQL_DEBUG=1`).

- **D1 bug 2, root cause** — my first fix (a second `useEffect` that reset `page` to 1
  whenever `geography` changed) looked right but still had a race: React runs the
  casinos-fetch effect and the page-reset effect in the same commit, so on a geography
  change the fetch effect could still fire once with the *old* page number paired with
  the *new* geography (a real request that could 404) before the reset effect's
  re-render corrected it. I caught this with a scripted browser check (Playwright + a
  local Chrome), not just by reading the code. Fixed by resetting `page` directly in
  the `onChange` handler that also sets `geography`, so React batches both into one
  render and the fetch effect only ever sees the new page/geography pair together.

- **D2 scope** — implemented all "must have" items plus all three "nice to have"
  items (URL query-string sync, provider name filter, Vitest component tests) since
  time allowed. Kept styling plain CSS (a small addition to `styles.css` for the
  sortable headers and inline share bar) to match the existing Overview page rather
  than introducing a chart/UI library.

## D1: root causes

1. **KPI cards don't update on geography change.** The `useEffect` that fetches
   `/api/summary/` had an empty dependency array (`[]`), so it only ran once on mount
   and never re-ran when `geography` changed - only the casinos-list effect (which
   *did* depend on `[geography, page]`) re-ran, so only the table updated. Fix: added
   `geography` to that effect's dependency array.
2. **Switching geography while on casino-list page 2+ throws an error.** `page` was
   never reset when `geography` changed, so picking a smaller geography while on, say,
   page 2 could request `/api/casinos/?geography=<new>&page=2` for a filter that only
   has 1 page, which the backend correctly rejects (404, "invalid page"). Fix: reset
   `page` to 1 in the same handler that changes `geography`, so both update in one
   render and the casinos fetch never runs with a stale page number for the new
   geography (see the trade-offs note above for why a second `useEffect` alone wasn't
   quite enough).

## What I'd do next with more time

- **Data quality**: fix the "Aurora Play" duplicate provider permanently (the merge
  script in `db/merge_duplicate_provider.sql` is written and tested, but reverted via
  `load_data` per the task instructions - in a real environment I'd run it against
  production once and retire it) and raise the Brightmoor ES review backlog (A3/A9)
  with whoever owns the approval queue.
- **Alerting**: a scheduled check for "active casino with 0 counted runs in the
  trailing N days" would have caught the Brightmoor ES situation automatically
  instead of it surfacing only because I went looking for A3.
- **API**: paginate/cap `provider-market-share` results if a geography ever has many
  more providers than the ~20-25 in this dataset (currently returns the full list -
  fine at this scale, not necessarily at real scale).
- **Frontend**: a component test for `Overview.jsx` covering the two D1 regressions
  (I added a Vitest suite for `MarketShare.jsx` but ran out of budget to also cover
  Overview); a loading skeleton instead of a bare "Loading…" line; debounce the
  provider name filter if the list ever gets large enough for it to matter.
- **B2**: I'd also want to see the production query plan (40M/3B rows) rather than
  reasoning from the shape of the local dataset - the local SQLite optimizer's choices
  are a reasonable proxy but not a guarantee of what a larger, PostgreSQL-shaped
  production table would do.

## Tools / AI used

Used **Claude Code (Claude Sonnet 5)** as an interactive pair throughout, plus two
supporting tools it drove. Breakdown by part:

- **Part A** — ran the actual SQL for every question against `backend/db.sqlite3`
  (via `run_sql.py`) and read back the results; nothing in `ANSWERS.md` is a guess or
  a memorised number. For A9 it also ran extra exploratory queries (duplicate games,
  position collisions, `tiles_found` vs. actual tile-row counts) to find data-quality
  issues beyond the ones the questions point at directly.
- **Part B** — wrote the B1/B3 SQL files, ran `EXPLAIN QUERY PLAN` before and after
  adding the B2 index and generated the Django migration for it, and actually executed
  the B3 merge script against the real database (checking row counts moved) before
  restoring the original data with `load_data`, rather than writing untested SQL.
- **Part C** — wrote the `month_bounds`/approval-rate fixes (C1), the
  `provider_market_share` service + view + tests (C2), and the `select_related`/
  annotation fix for the casino N+1 (C3); ran `manage.py test lobby` after each change
  to confirm the fix and check nothing else broke.
- **Part D** — wrote the Overview fixes (D1) and the `MarketShare.jsx` page (D2).
  Used **Playwright, driving a local headless Chrome**, to actually click through the
  running app (switch geography, page through the casino list, sort/filter the market
  share table) rather than trusting a code read alone - this is how the D1-bug-2 race
  condition (see "Decisions and trade-offs" above) was caught: my first fix looked
  correct on paper but still 404'd in the browser. Also used it to confirm the fixed
  version has no console/page errors and no failed requests. Wrote the Vitest +
  Testing Library suite for `MarketShare.jsx` and ran it (and `npm run build`) to
  confirm the page renders and builds cleanly.
- **Part E** — this file.

I reviewed and understand every change - happy to walk through and modify any of it
live on the call.
