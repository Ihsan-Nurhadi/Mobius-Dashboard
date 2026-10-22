import math
import os
import random
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone
from sites_app.models import HourlyReading, Site


def generate_reading_for_site(site, ts):
    """Generate a realistic hourly reading for a site at a given timestamp."""
    hour = ts.hour
    scale = (site.rated_load_kw / 5.5) if site.rated_load_kw else 1.0
    eff = 0.17

    # Use seed derived from site code and date/hour for consistency
    seed_val = f"{site.code}_{ts.strftime('%Y%m%d%H')}"
    rng = random.Random(seed_val)

    # Hourly diurnal curve (load peak during business hours)
    solar_sin = math.sin(math.pi * (hour - 5) / 16.0) if (5 <= hour <= 21) else 0.0
    base_curve = 2.6 + 0.9 * max(0.0, solar_sin)
    load_kwh = scale * base_curve * rng.uniform(0.96, 1.04)

    mobius_kwh = load_kwh * eff * rng.uniform(0.88, 1.12)
    if mobius_kwh > load_kwh:
        mobius_kwh = load_kwh * 0.95

    pln_kwh = max(0.0, load_kwh - mobius_kwh)

    reading, created = HourlyReading.objects.update_or_create(
        site=site,
        ts=ts,
        defaults={
            "pln_kwh": round(pln_kwh, 3),
            "mobius_kwh": round(mobius_kwh, 3),
        },
    )
    return created


def sync_site_readings(site, now=None):
    """
    Ensure the site has continuous hourly readings up to the current hour.
    If the site has missing hours since its last reading, backfills them.
    """
    if now is None:
        now = timezone.localtime(timezone.now())

    current_hour = now.replace(minute=0, second=0, microsecond=0)
    last_ts = site.readings.aggregate(m=Max("ts"))["m"]

    if last_ts is None:
        # If site has no readings at all, backfill past 24 hours
        start_ts = current_hour - timedelta(hours=24)
    else:
        last_local = timezone.localtime(last_ts).replace(minute=0, second=0, microsecond=0)
        start_ts = last_local + timedelta(hours=1)

    created_count = 0
    curr = start_ts
    while curr <= current_hour:
        if generate_reading_for_site(site, curr):
            created_count += 1
        curr += timedelta(hours=1)

    return created_count


class Command(BaseCommand):
    help = "Run the Mobius data simulator service to periodically generate hourly readings for all sites"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=int(os.environ.get("SIMULATOR_INTERVAL_SECONDS", 300)),
            help="Polling interval in seconds (default: 300 seconds / 5 minutes)",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single sync pass for all sites and exit immediately (useful for cron)",
        )

    def handle(self, *args, **options):
        once = options["once"]
        interval = max(10, options["interval"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting Mobius Data Simulator (interval={interval}s, once={once})..."
            )
        )

        while True:
            now = timezone.localtime(timezone.now())
            sites = list(Site.objects.all())

            if not sites:
                self.stdout.write(self.style.WARNING("No sites found in database. Waiting..."))
            else:
                total_created = 0
                for site in sites:
                    count = sync_site_readings(site, now)
                    total_created += count

                now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                if total_created > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"[{now_str}] Simulator: Added {total_created} new readings across {len(sites)} sites."
                        )
                    )
                else:
                    self.stdout.write(
                        f"[{now_str}] Simulator: All {len(sites)} sites are up-to-date (cutoff {now.strftime('%H:00')})."
                    )

            if once:
                break

            try:
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS("\nSimulator stopped by user."))
                break
