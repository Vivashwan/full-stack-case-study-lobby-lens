-- Task B2.
-- This query sits at the heart of the market-share report. Locally it is fast because the
-- dataset is tiny. In production scrape_run has ~40 million rows and game_position ~3 billion.
--
-- 1. Get the query plan by putting EXPLAIN QUERY PLAN in front of the query, e.g.
--        cd backend
--        python run_sql.py -c "EXPLAIN QUERY PLAN SELECT ..."
--    (or edit a copy of this file). Paste the plan into ANSWERS.md.
-- 2. Explain, in your own words, what the plan is doing, table by table. Which rows does the
--    database have to read and then throw away?
-- 3. Add the index(es) you would create - as a Django migration (Meta.indexes) - and explain
--    your column choice and order. Run the migration and paste the plan again.
--
-- SQLite docs on reading plans: https://www.sqlite.org/eqp.html

SELECT r.run_date, COUNT(*) AS tiles
FROM game_position gp
JOIN scrape_run r ON r.id = gp.run_id
JOIN casino c     ON c.id = r.casino_id
WHERE c.geography_id = 1
  AND r.show_data = 1
  AND r.run_date BETWEEN '2026-08-01' AND '2026-08-31'
GROUP BY r.run_date
ORDER BY r.run_date;
