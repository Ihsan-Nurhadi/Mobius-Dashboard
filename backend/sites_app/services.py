from datetime import date, datetime, time, timedelta
from django.db.models import Max, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone


def calc(pln, mobius, tariff):
    pln, mobius = pln or 0.0, mobius or 0.0
    load = pln + mobius
    return {
        "pln_kwh": round(pln, 3),
        "mobius_kwh": round(mobius, 3),
        "load_kwh": round(load, 3),
        "contribution_pct": round(mobius / load * 100, 2) if load else 0.0,
        "lift_pct": round(mobius / pln * 100, 2) if pln else 0.0,
        "saving_rp": round(mobius * tariff),
    }


def local_midnight(dt):
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = timezone.make_aware(datetime.combine(dt, time.min))
    return timezone.localtime(dt).replace(hour=0, minute=0, second=0, microsecond=0)


def reference_time(site):
    """Waktu cut-off = pembacaan terakhir site. Fallback ke sekarang."""
    last = site.readings.aggregate(m=Max("ts"))["m"]
    return last or timezone.now()


def today_summary(site):
    ref = reference_time(site)
    start = local_midnight(ref)
    qs = site.readings.filter(ts__gte=start, ts__lte=ref)
    agg = qs.aggregate(pln=Sum("pln_kwh"), mobius=Sum("mobius_kwh"))
    data = calc(agg["pln"], agg["mobius"], site.tariff_per_kwh)
    last_row = qs.order_by("-ts").first()
    data["cutoff"] = timezone.localtime(ref).isoformat()
    data["latest_hour"] = (
        calc(last_row.pln_kwh, last_row.mobius_kwh, site.tariff_per_kwh) if last_row else None
    )
    return data


def hourly_series(site, day=None):
    ref = reference_time(site)
    start = local_midnight(day or ref)
    end = start + timedelta(days=1)
    rows = site.readings.filter(ts__gte=start, ts__lt=end).order_by("ts")
    return [
        {
            "hour": timezone.localtime(r.ts).strftime("%H:00"),
            **calc(r.pln_kwh, r.mobius_kwh, site.tariff_per_kwh),
        }
        for r in rows
    ]


def daily_series(site, days=30):
    """30 hari penuh sebelum hari referensi (hari berjalan tidak ikut)."""
    ref = reference_time(site)
    end = local_midnight(ref)
    start = end - timedelta(days=days)
    rows = (
        site.readings.filter(ts__gte=start, ts__lt=end)
        .annotate(day=TruncDate("ts"))
        .values("day")
        .annotate(pln=Sum("pln_kwh"), mobius=Sum("mobius_kwh"))
        .order_by("day")
    )
    return [
        {"date": r["day"].isoformat(), **calc(r["pln"], r["mobius"], site.tariff_per_kwh)}
        for r in rows
    ]
