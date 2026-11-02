from rest_framework import serializers
from .models import Site, Region, UserProfile


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["code", "name"]


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    region = RegionSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ["username", "role", "region"]


class SiteListSerializer(serializers.ModelSerializer):
    region = serializers.CharField(source="region.name")
    region_code = serializers.CharField(source="region.code")

    class Meta:
        model = Site
        fields = ["code", "region", "region_code", "status", "area", "latitude", "longitude"]


class SiteDetailSerializer(serializers.ModelSerializer):
    region = serializers.CharField(source="region.name")
    region_code = serializers.CharField(source="region.code")

    class Meta:
        model = Site
        fields = [
            "code",
            "region",
            "region_code",
            "status",
            "area",
            "latitude",
            "longitude",
            "mobius_unit",
            "rated_load_kw",
            "tariff_per_kwh",
            "installed_at",
        ]
