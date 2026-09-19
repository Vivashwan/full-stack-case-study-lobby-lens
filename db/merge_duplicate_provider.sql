-- Task B3.
-- The `provider` table contains a duplicate: id=1 "Aurora Play" (87 games) and
-- id=25 "Aurora Play" (6 games) are the same studio, entered twice.
--
-- Before writing this script the games under id=25 were inspected:
--   408 Royal Safari           <- COLLIDES with game id=3 "Royal Safari" (provider 1),
--                                  same game_type ('slots') and same release_date
--                                  (2022-02-16) -> this is the SAME game, duplicated
--                                  along with the provider, not a coincidence.
--   409 Jade Wolves Hold & Win  \
--   410 Wild Tigers 2            > no name clash under provider 1 - safe to move as-is
--   411 Golden Riches           |
--   412 Cosmic Pharaoh          |
--   413 Golden Lotus           /
-- All 6 games have real game_position rows (scraped tile history) pointing at them,
-- so we must re-point that history rather than just deleting the rows.
--
-- Risk this script is careful about: game.provider_id and game_position.game_id are
-- both ON DELETE PROTECT (see lobby/models.py), so provider 25 cannot be deleted while
-- any game still points at it, and game 408 cannot be deleted while any game_position
-- still points at it. Doing the DELETEs before the UPDATEs would fail loudly (good -
-- PROTECT stops us from silently orphaning data) rather than silently losing rows, but
-- we still want the statements in the correct order rather than relying on trial and
-- error. Run inside a transaction so a mistake can be rolled back.
--
-- To try it: `python run_sql.py ../db/merge_duplicate_provider.sql`, inspect the
-- results, then `python manage.py load_data` to restore the original data before
-- continuing with the rest of the case study (this script's changes are meant to be
-- disposable in this environment).

BEGIN TRANSACTION;

-- 1. The duplicated "Royal Safari" tile history (game 408) is folded into the
--    original game (game 3) BEFORE anything is deleted, so no game_position row is
--    ever left pointing at a game_id that ceases to exist.
UPDATE game_position
SET game_id = 3
WHERE game_id = 408;

-- 2. Everything else under provider 25 is not a naming collision - just move it to
--    the correct provider.
UPDATE game
SET provider_id = 1
WHERE provider_id = 25
  AND id != 408;

-- 3. Game 408 no longer has any game_position rows pointing at it (step 1 moved them
--    all to game 3), so it is now safe to delete without violating PROTECT.
DELETE FROM game
WHERE id = 408;

-- 4. Provider 25 no longer has any games pointing at it (step 2 moved the rest,
--    step 3 removed the one collision), so it is now safe to delete.
DELETE FROM provider
WHERE id = 25;

COMMIT;

-- Sanity checks (run separately, or uncomment and run with -c):
-- SELECT COUNT(*) FROM provider WHERE name = 'Aurora Play';           -- expect 1
-- SELECT COUNT(*) FROM game WHERE provider_id = 25;                    -- expect 0
-- SELECT COUNT(*) FROM game_position WHERE game_id = 408;              -- expect 0
-- SELECT COUNT(*) FROM game_position WHERE game_id = 3;                -- should have grown by the 168 rows moved
