from datetime import date
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Site, Tenant
from .serializers import SiteDetailSerializer, SiteListSerializer
from . import services


@api_view(["GET"])
def tenants(request):
    return Response(list(Tenant.objects.values_list("name", flat=True)))


@api_view(["GET"])
def site_list(request):
    qs = Site.objects.select_related("tenant")

    # Extract tenant params (support both ?tenant=A&tenant=B and ?tenant=A,B)
    raw_tenants = request.query_params.getlist("tenant")
    tenant_filters = []
    for item in raw_tenants:
        tenant_filters.extend([t.strip() for t in item.split(",") if t.strip()])
    if tenant_filters:
        qs = qs.filter(tenant__name__in=tenant_filters)

    # Extract status params (support both ?status=Done&status=On%20Progress and ?status=Done,On%20Progress)
    raw_statuses = request.query_params.getlist("status")
    status_filters = []
    for item in raw_statuses:
        status_filters.extend([s.strip() for s in item.split(",") if s.strip()])
    if status_filters:
        qs = qs.filter(status__in=status_filters)

    return Response(SiteListSerializer(qs, many=True).data)


@api_view(["GET"])
def site_summary(request, code):
    """Dipakai kartu rangkuman di peta: site detail + angka hari ini."""
    site = get_object_or_404(Site.objects.select_related("tenant"), code=code)
    return Response({
        "site": SiteDetailSerializer(site).data,
        "today": services.today_summary(site),
    })


@api_view(["GET"])
def site_hourly(request, code):
    site = get_object_or_404(Site, code=code)
    day = request.query_params.get("date")
    if day:
        try:
            day = date.fromisoformat(day)
        except ValueError:
            day = None
    return Response(services.hourly_series(site, day))


@api_view(["GET"])
def site_daily(request, code):
    site = get_object_or_404(Site, code=code)
    try:
        days = min(int(request.query_params.get("days", 30)), 90)
    except (ValueError, TypeError):
        days = 30
    return Response(services.daily_series(site, days))
