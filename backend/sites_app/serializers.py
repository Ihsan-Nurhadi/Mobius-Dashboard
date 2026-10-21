from rest_framework import serializers
from .models import Site


class SiteListSerializer(serializers.ModelSerializer):
    tenant = serializers.CharField(source="tenant.name")

    class Meta:
        model = Site
        fields = ["code", "tenant", "status", "area", "latitude", "longitude"]


class SiteDetailSerializer(serializers.ModelSerializer):
    tenant = serializers.CharField(source="tenant.name")

    class Meta:
        model = Site
        fields = [
            "code",
            "tenant",
            "status",
            "area",
            "latitude",
            "longitude",
            "mobius_unit",
            "rated_load_kw",
            "tariff_per_kwh",
            "installed_at",
        ]
