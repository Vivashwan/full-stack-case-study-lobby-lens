from datetime import date

from django.test import TestCase

from . import factories as f


class SummaryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.geo = f.geography()
        other_geo = f.geography("Otherland", "OL")
        cas = f.casino(cls.geo)
        other = f.casino(other_geo, name="Other Casino")

        # August 2026 in Testland: 4 runs, 3 approved, 1 failed
        f.run(cas, date(2026, 8, 1), show_data=True)
        f.run(cas, date(2026, 8, 15), show_data=True)
        f.run(cas, date(2026, 8, 20), show_data=False, status="failed")
        f.run(cas, date(2026, 8, 31), show_data=True)
        # outside August - must never be counted
        f.run(cas, date(2026, 7, 31), show_data=True)
        f.run(cas, date(2026, 9, 1), show_data=True)
        # another geography
        f.run(other, date(2026, 8, 10), show_data=False)

    def get(self, **params):
        return self.client.get("/api/summary/", params)

    def test_month_is_required(self):
        self.assertEqual(self.get().status_code, 400)

    def test_bad_month_is_rejected(self):
        self.assertEqual(self.get(month="August").status_code, 400)

    def test_counts_the_whole_month(self):
        body = self.get(month="2026-08", geography=self.geo.id).json()
        self.assertEqual(body["total_runs"], 4)
        self.assertEqual(body["approved_runs"], 3)
        self.assertEqual(body["failed_runs"], 1)

    def test_approval_rate(self):
        body = self.get(month="2026-08", geography=self.geo.id).json()
        self.assertEqual(body["approval_rate_pct"], 75.0)

    def test_all_geographies(self):
        body = self.get(month="2026-08").json()
        self.assertEqual(body["total_runs"], 5)
        self.assertEqual(body["active_casinos"], 2)
