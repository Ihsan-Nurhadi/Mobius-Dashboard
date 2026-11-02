from django.contrib import admin
from .models import Region, UserProfile, Site, HourlyReading


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "region", "role")
    list_filter = ("region", "role")
    search_fields = ("user__username",)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("code", "region", "status", "area", "mobius_unit", "rated_load_kw", "tariff_per_kwh")
    list_filter = ("region", "status")
    search_fields = ("code", "area", "mobius_unit")


@admin.register(HourlyReading)
class HourlyReadingAdmin(admin.ModelAdmin):
    list_display = ("site", "ts", "pln_kwh", "mobius_kwh", "load_kwh")
    list_filter = ("site__region", "site")
    search_fields = ("site__code",)
    date_hierarchy = "ts"
