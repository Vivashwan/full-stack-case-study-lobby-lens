from datetime import date

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from . import factories as f


class CasinoApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.geo = f.geography()
        other = f.geography("Otherland", "OL")
        for i in range(15):
            c = f.casino(cls.geo, name=f"Casino {i:02d}", is_active=(i != 0))
            f.run(c, date(2026, 8, 1), show_data=True)
            f.run(c, date(2026, 8, 2), show_data=False)
        f.casino(other, name="Elsewhere")

    def test_filter_by_geography(self):
        body = self.client.get("/api/casinos/", {"geography": self.geo.id}).json()
        self.assertEqual(body["count"], 15)

    def test_filter_by_active(self):
        body = self.client.get("/api/casinos/", {"geography": self.geo.id, "is_active": "false"}).json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["results"][0]["name"], "Casino 00")

    def test_approved_runs(self):
        body = self.client.get("/api/casinos/", {"geography": self.geo.id}).json()
        self.assertTrue(all(c["approved_runs"] == 1 for c in body["results"]))

    def test_query_count_does_not_grow_with_page_size(self):
        """A page of 15 casinos should not need 30+ queries."""
        with CaptureQueriesContext(connection) as ctx:
            resp = self.client.get("/api/casinos/", {"geography": self.geo.id})
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 3, [q["sql"] for q in ctx.captured_queries])
