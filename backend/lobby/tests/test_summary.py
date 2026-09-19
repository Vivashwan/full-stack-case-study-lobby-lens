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

    def test_february_does_not_error(self):
        """Regression test for task C1: month_bounds used to build date(year, 2, 30),
        which doesn't exist and raised ValueError."""
        resp = self.get(month="2026-02", geography=self.geo.id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["total_runs"], 0)

    def test_31_day_month_includes_the_31st(self):
        """Regression test for task C1: date(year, mon, 30) truncated the last day of
        any 31-day month, silently dropping the 31st from the range."""
        body = self.get(month="2026-08", geography=self.geo.id).json()
        self.assertEqual(body["total_runs"], 4)  # includes the run on 2026-08-31

    def test_approval_rate_is_not_truncated_to_zero(self):
        """Regression test for task C1: `approved // total` (integer division) rounded
        every non-100% approval rate down to 0."""
        body = self.get(month="2026-08", geography=self.geo.id).json()
        self.assertNotEqual(body["approval_rate_pct"], 0)
