import math
import random
from datetime import date, datetime, time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from sites_app.models import Tenant, Site, HourlyReading


class Command(BaseCommand):
    help = "Seed database with demo tenants, sites, and 31 days of hourly readings"

    def handle(self, *args, **options):
        self.stdout.write("Seeding tenants and sites...")

        tenants_data = ["Tsel", "IOH", "XLSMA"]
        tenants = {}
        for t_name in tenants_data:
            tenant, _ = Tenant.objects.get_or_create(name=t_name)
            tenants[t_name] = tenant

        sites_data = [
            {
                "code": "CLG002", "tenant": "Tsel", "status": "Done",
                "area": "Cilegon, Banten", "latitude": -6.0023, "longitude": 106.0111,
                "mobius_unit": "MBX-2002", "rated_load_kw": 5.5, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 1, 15), "scale": 1.05, "eff": 0.18,
            },
            {
                "code": "MGW006", "tenant": "Tsel", "status": "Done",
                "area": "Magelang, Jawa Tengah", "latitude": -7.4797, "longitude": 110.2177,
                "mobius_unit": "MBX-3006", "rated_load_kw": 5.5, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 3, 14), "scale": 1.00, "eff": 0.17,
            },
            {
                "code": "PWK002", "tenant": "Tsel", "status": "Done",
                "area": "Purwakarta, Jawa Barat", "latitude": -6.5569, "longitude": 107.4431,
                "mobius_unit": "MBX-2008", "rated_load_kw": 5.0, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 2, 20), "scale": 0.95, "eff": 0.16,
            },
            {
                "code": "TNG095", "tenant": "Tsel", "status": "On Progress",
                "area": "Tangerang, Banten", "latitude": -6.1783, "longitude": 106.6319,
                "mobius_unit": "MBX-1095", "rated_load_kw": 6.0, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 4, 1), "scale": 1.10, "eff": 0.15,
            },
            {
                "code": "BKS031", "tenant": "IOH", "status": "Done",
                "area": "Bekasi, Jawa Barat", "latitude": -6.2383, "longitude": 106.9756,
                "mobius_unit": "MBX-4031", "rated_load_kw": 5.8, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 1, 5), "scale": 1.15, "eff": 0.19,
            },
            {
                "code": "SMG118", "tenant": "IOH", "status": "On Progress",
                "area": "Semarang, Jawa Tengah", "latitude": -6.9667, "longitude": 110.4167,
                "mobius_unit": "MBX-1118", "rated_load_kw": 5.2, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 3, 28), "scale": 0.98, "eff": 0.16,
            },
            {
                "code": "KRW007", "tenant": "XLSMA", "status": "Done",
                "area": "Karawang, Jawa Barat", "latitude": -6.3015, "longitude": 107.3376,
                "mobius_unit": "MBX-3007", "rated_load_kw": 5.4, "tariff_per_kwh": 1444.70,
                "installed_at": date(2026, 2, 10), "scale": 1.02, "eff": 0.17,
            },
            {
                "code": "BDG204", "tenant": "XLSMA", "status": "Done",
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
                    "tenant": tenants[s["tenant"]],
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
            day_idx = 0
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
                # load(jam) = skala_site * (2.6 + 0.9 * max(0, sin(pi * (jam - 5) / 16))) * acak(0.96 .. 1.04)
                solar_sin = math.sin(math.pi * (hour - 5) / 16.0) if (5 <= hour <= 21) else 0.0
                base_curve = 2.6 + 0.9 * max(0.0, solar_sin)
                load_kwh = site_scale * base_curve * rng.uniform(0.96, 1.04) * day_load_mult

                # Mobius formula:
                # mobius = load * eff_site * acak(0.88 .. 1.12)
                mobius_kwh = load_kwh * site_eff * rng.uniform(0.88, 1.12) * day_mob_mult

                # Ensure mobius does not exceed load
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

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded demo data: 8 sites, {total_readings} hourly readings."))
