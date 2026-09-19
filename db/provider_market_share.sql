-- Task B1.
-- Write ONE query that returns the Provider Market Share table for
-- geography_id = 1 (United Kingdom) and August 2026, following the metric
-- definition in CASE_STUDY.md.
--
-- Expected columns:
--   provider_id, provider_name, unique_games, unique_casinos, listings, market_share_pct
-- Ordered by market_share_pct DESC, provider_name ASC.

WITH counted_runs AS (
  -- R1 (show_data=1) + R3 (active casino), then R2: keep only the latest
  -- approved run per casino-day (highest started_at, ties broken by id).
  SELECT r.id, r.casino_id
  FROM (
    SELECT
      r.id, r.casino_id, r.run_date,
      ROW_NUMBER() OVER (
        PARTITION BY r.casino_id, r.run_date
        ORDER BY r.started_at DESC, r.id DESC
      ) AS rn
    FROM scrape_run r
    JOIN casino c ON c.id = r.casino_id
    WHERE r.show_data = 1
      AND c.is_active = 1
      AND c.geography_id = 1
      AND r.run_date BETWEEN '2026-08-01' AND '2026-08-31'
  ) r
  WHERE r.rn = 1
),
listings AS (
  -- A listing is a distinct (casino, game) pair seen at least once in a counted run.
  SELECT DISTINCT cr.casino_id, gp.game_id
  FROM game_position gp
  JOIN counted_runs cr ON cr.id = gp.run_id
),
total AS (
  SELECT COUNT(*) AS n FROM listings
)
SELECT
  p.id AS provider_id,
  p.name AS provider_name,
  COUNT(DISTINCT l.game_id) AS unique_games,
  COUNT(DISTINCT l.casino_id) AS unique_casinos,
  COUNT(*) AS listings,
  ROUND(COUNT(*) * 100.0 / (SELECT n FROM total), 2) AS market_share_pct
FROM listings l
JOIN game g ON g.id = l.game_id
JOIN provider p ON p.id = g.provider_id
GROUP BY p.id, p.name
ORDER BY market_share_pct DESC, provider_name ASC;
