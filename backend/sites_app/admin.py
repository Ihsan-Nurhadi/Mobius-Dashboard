from django.contrib import admin
from .models import Tenant, Site, HourlyReading


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("code", "tenant", "status", "area", "mobius_unit", "rated_load_kw", "tariff_per_kwh")
    list_filter = ("tenant", "status")
    search_fields = ("code", "area", "mobius_unit")


@admin.register(HourlyReading)
class HourlyReadingAdmin(admin.ModelAdmin):
    list_display = ("site", "ts", "pln_kwh", "mobius_kwh", "load_kwh")
    list_filter = ("site__tenant", "site")
    search_fields = ("site__code",)
    date_hierarchy = "ts"
