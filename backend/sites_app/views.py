from datetime import date
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Site, Region, UserProfile
from .serializers import SiteDetailSerializer, SiteListSerializer, RegionSerializer
from . import services


def serialize_user(user):
    profile = getattr(user, "profile", None)
    region_data = None
    role = "regional_user"

    if user.is_superuser:
        role = "national_admin"
    elif profile:
        role = profile.role
        if profile.region:
            region_data = RegionSerializer(profile.region).data

    return {
        "username": user.username,
        "role": role,
        "region": region_data,
        "is_superuser": user.is_superuser,
    }


def get_scoped_sites(user):
    """Filter queryset site berdasarkan role/region user."""
    if not user or not user.is_authenticated:
        return Site.objects.none()

    if user.is_superuser:
        return Site.objects.all()

    profile = getattr(user, "profile", None)
    if not profile:
        return Site.objects.none()

    if profile.role == UserProfile.Role.NATIONAL_ADMIN:
        return Site.objects.all()

    if profile.region:
        return Site.objects.filter(region=profile.region)

    return Site.objects.none()


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"detail": "Username dan password wajib diisi."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(request, username=username, password=password)
    if not user:
        return Response(
            {"detail": "Username atau password salah."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token": token.key,
        "user": serialize_user(user),
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({"detail": "Berhasil logout."})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def auth_me(request):
    return Response({"user": serialize_user(request.user)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def site_list(request):
    qs = get_scoped_sites(request.user).select_related("region")

    # Filter status params (support both ?status=Done&status=On%20Progress and ?status=Done,On%20Progress)
    raw_statuses = request.query_params.getlist("status")
    status_filters = []
    for item in raw_statuses:
        status_filters.extend([s.strip() for s in item.split(",") if s.strip()])
    if status_filters:
        qs = qs.filter(status__in=status_filters)

    # Optional region filter for national admin
    raw_regions = request.query_params.getlist("region")
    region_filters = []
    for item in raw_regions:
        region_filters.extend([r.strip() for r in item.split(",") if r.strip()])
    if region_filters:
        qs = qs.filter(region__code__in=region_filters)

    return Response(SiteListSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def site_summary(request, code):
    """Dipakai kartu rangkuman di peta: site detail + angka hari ini."""
    site = get_object_or_404(get_scoped_sites(request.user).select_related("region"), code=code)
    return Response({
        "site": SiteDetailSerializer(site).data,
        "today": services.today_summary(site),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def site_hourly(request, code):
    site = get_object_or_404(get_scoped_sites(request.user), code=code)
    day = request.query_params.get("date")
    if day:
        try:
            day = date.fromisoformat(day)
        except ValueError:
            day = None
    return Response(services.hourly_series(site, day))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def site_daily(request, code):
    site = get_object_or_404(get_scoped_sites(request.user), code=code)
    try:
        days = min(int(request.query_params.get("days", 30)), 90)
    except (ValueError, TypeError):
        days = 30
    return Response(services.daily_series(site, days))
