import math
import random
from datetime import date, datetime, time, timedelta
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from sites_app.models import Region, UserProfile, Site, HourlyReading


class Command(BaseCommand):
    help = "Seed database with demo regions, users, sites, and 31 days of hourly readings"

    def handle(self, *args, **options):
        self.stdout.write("Seeding regions...")

        regions_data = [
            {"code": "JABODETABEK", "name": "Jabodetabek"},
            {"code": "JABAR", "name": "Jawa Barat"},
            {"code": "JATENG", "name": "Jawa Tengah"},
        ]
        regions = {}
        for r_info in regions_data:
            region, _ = Region.objects.get_or_create(code=r_info["code"], defaults={"name": r_info["name"]})
            region.name = r_info["name"]
            region.save()
            regions[r_info["code"]] = region

        self.stdout.write("Seeding users per region and superadmin...")
        users_data = [
            {
                "username": "user_jabodetabek",
                "password": "mobius123",
                "region": regions["JABODETABEK"],
                "role": UserProfile.Role.REGIONAL_USER,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "user_jabar",
                "password": "mobius123",
                "region": regions["JABAR"],
                "role": UserProfile.Role.REGIONAL_USER,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "user_jateng",
                "password": "mobius123",
                "region": regions["JATENG"],
                "role": UserProfile.Role.REGIONAL_USER,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "username": "admin_nasional",
                "password": "mobius123",
                "region": None,
                "role": UserProfile.Role.NATIONAL_ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        ]

        for u in users_data:
            user, created = User.objects.get_or_create(username=u["username"])
            user.set_password(u["password"])
            user.is_staff = u["is_staff"]
            user.is_superuser = u["is_superuser"]
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.region = u["region"]
            profile.role = u["role"]
            profile.save()

        self.stdout.write("Seeding sites assigned to regions...")
        sites_data = [
            {
                "code": "CLG002", "region": "JABAR", "status": "Done",
                "area": "Cilegon, Banten", "latitude": -6.0023, "longitude": 106.0111,
                "mobius_unit": "MBX-2002", "rated_load_kw": 5.5, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 1, 15), "scale": 1.05, "eff": 0.18,
            },
            {
                "code": "MGW006", "region": "JATENG", "status": "Done",
                "area": "Magelang, Jawa Tengah", "latitude": -7.4797, "longitude": 110.2177,
                "mobius_unit": "MBX-3006", "rated_load_kw": 5.5, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 3, 14), "scale": 1.00, "eff": 0.17,
            },
            {
                "code": "PWK002", "region": "JABAR", "status": "Done",
                "area": "Purwakarta, Jawa Barat", "latitude": -6.5569, "longitude": 107.4431,
                "mobius_unit": "MBX-2008", "rated_load_kw": 5.0, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 2, 20), "scale": 0.95, "eff": 0.16,
            },
            {
                "code": "TNG095", "region": "JABODETABEK", "status": "On Progress",
                "area": "Tangerang, Banten", "latitude": -6.1783, "longitude": 106.6319,
                "mobius_unit": "MBX-1095", "rated_load_kw": 6.0, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 4, 1), "scale": 1.10, "eff": 0.15,
            },
            {
                "code": "BKS031", "region": "JABODETABEK", "status": "Done",
                "area": "Bekasi, Jawa Barat", "latitude": -6.2383, "longitude": 106.9756,
                "mobius_unit": "MBX-4031", "rated_load_kw": 5.8, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 1, 5), "scale": 1.15, "eff": 0.19,
            },
            {
                "code": "SMG118", "region": "JATENG", "status": "On Progress",
                "area": "Semarang, Jawa Tengah", "latitude": -6.9667, "longitude": 110.4167,
                "mobius_unit": "MBX-1118", "rated_load_kw": 5.2, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 3, 28), "scale": 0.98, "eff": 0.16,
            },
            {
                "code": "KRW007", "region": "JABAR", "status": "Done",
                "area": "Karawang, Jawa Barat", "latitude": -6.3015, "longitude": 107.3376,
                "mobius_unit": "MBX-3007", "rated_load_kw": 5.4, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 2, 10), "scale": 1.02, "eff": 0.17,
            },
            {
                "code": "BDG204", "region": "JABAR", "status": "Done",
                "area": "Bandung, Jawa Barat", "latitude": -6.9175, "longitude": 107.6191,
                "mobius_unit": "MBX-5204", "rated_load_kw": 5.6, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 2, 18), "scale": 1.08, "eff": 0.18,
            },
        ]

        site_objects = []
        for s in sites_data:
            site, _ = Site.objects.update_or_create(
                code=s["code"],
                defaults={
                    "region": regions[s["region"]],
                    "status": s["status"],
                    "area": s["area"],
                    "latitude": s["latitude"],
                    "longitude": s["longitude"],
                    "mobius_unit": s["mobius_unit"],
                    "rated_load_kw": s["rated_load_kw"],
                    "tariff_per_kwh": s["tariff_per_kwh"],
                    "installed_at": s["installed_at"],
                },
            )
            site_objects.append((site, s["scale"], s["eff"]))

        self.stdout.write("Generating hourly readings (31 days back up to 17:00 cut-off)...")

        # Today cutoff at 17:00 local time
        now_local = timezone.localtime(timezone.now())
        cutoff_today = now_local.replace(hour=17, minute=0, second=0, microsecond=0)
        start_day = (cutoff_today - timedelta(days=31)).replace(hour=0, minute=0, second=0, microsecond=0)

        total_readings = 0
        readings_to_create = []

        for site, site_scale, site_eff in site_objects:
            rng = random.Random(site.code)
            # Pick 2 random dip days in the past 30 days (excluding today)
            dip_days = set(rng.sample(range(1, 30), 2))

            curr_ts = start_day
            while curr_ts <= cutoff_today:
                hour = curr_ts.hour
                day_offset = (curr_ts.date() - start_day.date()).days

                # Dip day multiplier
                if day_offset in dip_days:
                    day_load_mult = 0.60 * rng.uniform(0.95, 1.05)
                    day_mob_mult = 0.75 * rng.uniform(0.95, 1.05)
                else:
                    day_load_mult = 1.0
                    day_mob_mult = 1.0

                # Hourly load formula:
                solar_sin = math.sin(math.pi * (hour - 5) / 16.0) if (5 <= hour <= 21) else 0.0
                base_curve = 2.6 + 0.9 * max(0.0, solar_sin)
                load_kwh = site_scale * base_curve * rng.uniform(0.96, 1.04) * day_load_mult

                # Mobius formula:
                mobius_kwh = load_kwh * site_eff * rng.uniform(0.88, 1.12) * day_mob_mult

                if mobius_kwh > load_kwh:
                    mobius_kwh = load_kwh * 0.95

                pln_kwh = load_kwh - mobius_kwh

                readings_to_create.append(
                    HourlyReading(
                        site=site,
                        ts=curr_ts,
                        pln_kwh=round(pln_kwh, 3),
                        mobius_kwh=round(mobius_kwh, 3),
                    )
                )

                if len(readings_to_create) >= 2000:
                    HourlyReading.objects.bulk_create(readings_to_create, ignore_conflicts=True)
                    total_readings += len(readings_to_create)
                    readings_to_create = []

                curr_ts += timedelta(hours=1)

        if readings_to_create:
            HourlyReading.objects.bulk_create(readings_to_create, ignore_conflicts=True)
            total_readings += len(readings_to_create)

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded demo data: 8 sites, {total_readings} hourly readings across 3 regions."))
