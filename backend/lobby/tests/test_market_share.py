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

    # ------------------------------------------------------------------
    # TODO (task C2): add tests for the business rules, e.g. which runs
    # count and which don't. Name them so we can tell what they check.
    # ------------------------------------------------------------------
