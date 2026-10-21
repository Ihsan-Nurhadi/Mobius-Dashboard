from datetime import date, timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import HourlyReading, Site, Tenant
from .services import calc, daily_series, today_summary


class MobiusCalcTests(TestCase):
    def test_calc_zero_load_and_pln(self):
        res = calc(0.0, 0.0, 1444.70)
        self.assertEqual(res["load_kwh"], 0.0)
        self.assertEqual(res["contribution_pct"], 0.0)
        self.assertEqual(res["lift_pct"], 0.0)
        self.assertEqual(res["saving_rp"], 0)

    def test_calc_normal(self):
        # pln = 46.25, mobius = 11.80
        res = calc(46.25, 11.80, 1444.70)
        self.assertAlmostEqual(res["load_kwh"], 58.05, places=2)
        self.assertEqual(res["contribution_pct"], round(11.80 / 58.05 * 100, 2))
        self.assertEqual(res["lift_pct"], round(11.80 / 46.25 * 100, 2))
        self.assertEqual(res["saving_rp"], round(11.80 * 1444.70))


class MobiusApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.t_tsel = Tenant.objects.create(name="Tsel")
        self.t_ioh = Tenant.objects.create(name="IOH")

        self.site_clg = Site.objects.create(
            code="CLG002",
            tenant=self.t_tsel,
            status=Site.Status.DONE,
            area="Cilegon, Banten",
            latitude=-6.0023,
            longitude=106.0111,
            mobius_unit="MBX-2002",
            rated_load_kw=5.5,
            tariff_per_kwh=1444.70,
            installed_at=date(2026, 1, 15),
        )

        self.site_tng = Site.objects.create(
            code="TNG095",
            tenant=self.t_tsel,
            status=Site.Status.ON_PROGRESS,
            area="Tangerang, Banten",
            latitude=-6.1783,
            longitude=106.6319,
            mobius_unit="MBX-1095",
            rated_load_kw=6.0,
            tariff_per_kwh=1444.70,
            installed_at=date(2026, 4, 1),
        )

        self.site_bks = Site.objects.create(
            code="BKS031",
            tenant=self.t_ioh,
            status=Site.Status.DONE,
            area="Bekasi, Jawa Barat",
            latitude=-6.2383,
            longitude=106.9756,
            mobius_unit="MBX-4031",
            rated_load_kw=5.8,
            tariff_per_kwh=1444.70,
            installed_at=date(2026, 1, 5),
        )

        # Create readings across 35 days
        now_local = timezone.localtime(timezone.now())
        cutoff = now_local.replace(hour=17, minute=0, second=0, microsecond=0)
        start = cutoff - timedelta(days=34)

        curr = start
        readings = []
        while curr <= cutoff:
            readings.append(
                HourlyReading(
                    site=self.site_clg,
                    ts=curr,
                    pln_kwh=3.0,
                    mobius_kwh=1.0,
                )
            )
            curr += timedelta(hours=1)
        HourlyReading.objects.bulk_create(readings)

    def test_daily_series_limits_and_excludes_today(self):
        series = daily_series(self.site_clg, days=30)
        self.assertLessEqual(len(series), 30)

        # Check today date is NOT in daily_series (today is reference day)
        today_iso = timezone.localtime(timezone.now()).date().isoformat()
        dates = [item["date"] for item in series]
        self.assertNotIn(today_iso, dates)

        # Check formula consistency: load = pln + mobius
        for item in series:
            self.assertAlmostEqual(item["load_kwh"], item["pln_kwh"] + item["mobius_kwh"], places=3)

    def test_filter_sites_by_tenant_and_status(self):
        resp = self.client.get("/api/sites/?tenant=Tsel&status=Done")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["code"], "CLG002")
        self.assertEqual(data[0]["tenant"], "Tsel")
        self.assertEqual(data[0]["status"], "Done")

    def test_site_summary_and_404(self):
        resp = self.client.get("/api/sites/CLG002/summary/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("site", data)
        self.assertIn("today", data)
        self.assertAlmostEqual(
            data["today"]["load_kwh"],
            data["today"]["pln_kwh"] + data["today"]["mobius_kwh"],
            places=2,
        )

        resp_404 = self.client.get("/api/sites/NONEXISTENT/summary/")
        self.assertEqual(resp_404.status_code, 404)
