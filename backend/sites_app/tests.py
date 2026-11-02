from datetime import date, timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import HourlyReading, Region, Site, UserProfile
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

        self.region_jabar = Region.objects.create(code="JABAR", name="Jawa Barat")
        self.region_jabo = Region.objects.create(code="JABODETABEK", name="Jabodetabek")

        # Users
        self.user_jabo = User.objects.create_user(username="user_jabo", password="password123")
        UserProfile.objects.create(user=self.user_jabo, region=self.region_jabo, role=UserProfile.Role.REGIONAL_USER)
        self.token_jabo = Token.objects.create(user=self.user_jabo)

        self.user_jabar = User.objects.create_user(username="user_jabar", password="password123")
        UserProfile.objects.create(user=self.user_jabar, region=self.region_jabar, role=UserProfile.Role.REGIONAL_USER)
        self.token_jabar = Token.objects.create(user=self.user_jabar)

        self.admin_user = User.objects.create_superuser(username="admin_nasional", password="password123")
        UserProfile.objects.create(user=self.admin_user, region=None, role=UserProfile.Role.NATIONAL_ADMIN)
        self.token_admin = Token.objects.create(user=self.admin_user)

        self.site_clg = Site.objects.create(
            code="CLG002",
            region=self.region_jabar,
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
            region=self.region_jabo,
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
            region=self.region_jabo,
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

    def test_login_and_me_endpoint(self):
        # Invalid login
        resp_fail = self.client.post("/api/auth/login/", {"username": "user_jabo", "password": "wrong"})
        self.assertEqual(resp_fail.status_code, 401)

        # Valid login
        resp_ok = self.client.post("/api/auth/login/", {"username": "user_jabo", "password": "password123"})
        self.assertEqual(resp_ok.status_code, 200)
        data = resp_ok.json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["username"], "user_jabo")
        self.assertEqual(data["user"]["region"]["code"], "JABODETABEK")

        # Test auth/me with token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {data['token']}")
        resp_me = self.client.get("/api/auth/me/")
        self.assertEqual(resp_me.status_code, 200)
        self.assertEqual(resp_me.json()["user"]["username"], "user_jabo")

    def test_region_scoped_site_list(self):
        # Jabodetabek user only sees Jabodetabek sites (TNG095, BKS031)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_jabo.key}")
        resp = self.client.get("/api/sites/")
        self.assertEqual(resp.status_code, 200)
        codes = [s["code"] for s in resp.json()]
        self.assertIn("TNG095", codes)
        self.assertIn("BKS031", codes)
        self.assertNotIn("CLG002", codes)

        # Jawa Barat user only sees Jabar site (CLG002)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_jabar.key}")
        resp = self.client.get("/api/sites/")
        self.assertEqual(resp.status_code, 200)
        codes = [s["code"] for s in resp.json()]
        self.assertEqual(codes, ["CLG002"])

        # Superadmin / National admin sees all
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_admin.key}")
        resp = self.client.get("/api/sites/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 3)

    def test_cross_region_access_prevented(self):
        # Jabar user tries to access Jabodetabek site summary -> should 404
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_jabar.key}")
        resp_404 = self.client.get("/api/sites/TNG095/summary/")
        self.assertEqual(resp_404.status_code, 404)

        # Jabar user accesses own site summary -> should 200
        resp_200 = self.client.get("/api/sites/CLG002/summary/")
        self.assertEqual(resp_200.status_code, 200)

    def test_daily_series_limits_and_excludes_today(self):
        series = daily_series(self.site_clg, days=30)
        self.assertLessEqual(len(series), 30)

        today_iso = timezone.localtime(timezone.now()).date().isoformat()
        dates = [item["date"] for item in series]
        self.assertNotIn(today_iso, dates)

        for item in series:
            self.assertAlmostEqual(item["load_kwh"], item["pln_kwh"] + item["mobius_kwh"], places=3)


    def test_export_performance_endpoint(self):
        # Authenticated user in Jabar can export CLG002
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_jabar.key}")
        resp = self.client.get("/api/sites/CLG002/export-performance/?start_date=2026-03-01&end_date=2026-03-31")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.headers["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn("attachment; filename=", resp.headers["Content-Disposition"])
        self.assertGreater(len(resp.content), 1000)

        # Cross-region access prevented (Jabar user cannot export Jabodetabek site)
        resp_blocked = self.client.get("/api/sites/TNG095/export-performance/")
        self.assertEqual(resp_blocked.status_code, 404)
