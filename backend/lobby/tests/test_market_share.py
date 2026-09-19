"""
Contract tests for GET /api/provider-market-share/  (task C2).

These fail until you implement the endpoint. They only check the *shape* of the API.
Add your own tests below for the business rules in CASE_STUDY.md - we read them.
"""
from datetime import date

from django.test import TestCase

from . import factories as f


class MarketShareContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.geo = f.geography()
        cas = f.casino(cls.geo)
        big, small = f.provider("Big Studio"), f.provider("Small Studio")
        g1, g2, g3 = f.game(big, "B1"), f.game(big, "B2"), f.game(small, "S1")
        f.run(cas, date(2026, 8, 3), games=[g1, g2, g3])

    def get(self, **params):
        return self.client.get("/api/provider-market-share/", params)

    def test_geography_is_required(self):
        self.assertEqual(self.get(month="2026-08").status_code, 400)

    def test_month_is_required(self):
        self.assertEqual(self.get(geography=self.geo.id).status_code, 400)

    def test_bad_month(self):
        self.assertEqual(self.get(geography=self.geo.id, month="2026-13").status_code, 400)

    def test_unknown_geography(self):
        self.assertEqual(self.get(geography=999999, month="2026-08").status_code, 404)

    def test_response_shape_and_order(self):
        resp = self.get(geography=self.geo.id, month="2026-08")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertEqual(body["geography"], {"id": self.geo.id, "name": "Testland"})
        self.assertEqual(body["month"], "2026-08")
        self.assertEqual(body["total_listings"], 3)
        rows = body["results"]
        self.assertEqual([r["provider_name"] for r in rows], ["Big Studio", "Small Studio"])
        self.assertEqual(
            set(rows[0]),
            {"provider_id", "provider_name", "unique_games", "unique_casinos", "listings", "market_share_pct"},
        )
        self.assertAlmostEqual(rows[0]["market_share_pct"], 66.67, places=2)

    def test_empty_month_returns_empty_list(self):
        body = self.get(geography=self.geo.id, month="2025-01").json()
        self.assertEqual(body["results"], [])
        self.assertEqual(body["total_listings"], 0)


class MarketShareBusinessRuleTests(TestCase):
    """R1-R3 from CASE_STUDY.md -> 'Metric definitions'."""

    def get(self, **params):
        return self.client.get("/api/provider-market-share/", params)

    def test_r1_unapproved_runs_are_excluded(self):
        """A run with show_data=False must not contribute any listings."""
        geo = f.geography()
        cas = f.casino(geo)
        prov = f.provider("Studio A")
        game = f.game(prov, "Game A")
        f.run(cas, date(2026, 8, 5), show_data=False, games=[game])

        body = self.get(geography=geo.id, month="2026-08").json()
        self.assertEqual(body["total_listings"], 0)
        self.assertEqual(body["results"], [])

    def test_r2_only_latest_run_of_the_day_counts(self):
        """Two approved runs for the same casino on the same day: only the run with
        the latest started_at counts. The earlier run's extra game must not appear."""
        geo = f.geography()
        cas = f.casino(geo)
        prov = f.provider("Studio A")
        early_only_game = f.game(prov, "Early Only")
        shared_game = f.game(prov, "Shared")

        # earlier run: both games
        f.run(cas, date(2026, 8, 5), show_data=True, hour=2, games=[early_only_game, shared_game])
        # later run (same casino, same day): only the shared game
        f.run(cas, date(2026, 8, 5), show_data=True, hour=8, games=[shared_game])

        body = self.get(geography=geo.id, month="2026-08").json()
        self.assertEqual(body["total_listings"], 1)  # only the later run's listing counts
        [row] = body["results"]
        self.assertEqual(row["listings"], 1)
        self.assertEqual(row["unique_games"], 1)

    def test_r2_tie_break_is_highest_id(self):
        """Two approved runs with the identical started_at: the one with the higher
        id (created later) wins the tie-break."""
        geo = f.geography()
        cas = f.casino(geo)
        prov = f.provider("Studio A")
        first_game = f.game(prov, "First")
        second_game = f.game(prov, "Second")

        r1 = f.run(cas, date(2026, 8, 5), show_data=True, hour=2, games=[first_game])
        r2 = f.run(cas, date(2026, 8, 5), show_data=True, hour=2, games=[second_game])
        r1.started_at = r2.started_at
        r1.save(update_fields=["started_at"])
        self.assertGreater(r2.id, r1.id)

        body = self.get(geography=geo.id, month="2026-08").json()
        [row] = body["results"]
        self.assertEqual(row["provider_name"], "Studio A")
        self.assertEqual(row["unique_games"], 1)  # only r2's game ("Second") counts

    def test_r3_inactive_casino_is_excluded(self):
        """An inactive casino's listings must not appear even if its run is approved."""
        geo = f.geography()
        cas = f.casino(geo, is_active=False)
        prov = f.provider("Studio A")
        game = f.game(prov, "Game A")
        f.run(cas, date(2026, 8, 5), show_data=True, games=[game])

        body = self.get(geography=geo.id, month="2026-08").json()
        self.assertEqual(body["total_listings"], 0)
        self.assertEqual(body["results"], [])

    def test_other_geography_is_not_mixed_in(self):
        """Listings from casinos in a different geography must not leak into the result."""
        geo = f.geography("A-land", "AA")
        other_geo = f.geography("B-land", "BB")
        cas = f.casino(geo)
        other_cas = f.casino(other_geo, name="Other Casino")
        prov = f.provider("Studio A")
        game_a = f.game(prov, "Game A")
        game_b = f.game(prov, "Game B")
        f.run(cas, date(2026, 8, 5), show_data=True, games=[game_a])
        f.run(other_cas, date(2026, 8, 5), show_data=True, games=[game_b])

        body = self.get(geography=geo.id, month="2026-08").json()
        self.assertEqual(body["total_listings"], 1)
        self.assertEqual(body["results"][0]["unique_games"], 1)
