from django.urls import path
from . import views

urlpatterns = [
    path("tenants/", views.tenants, name="tenants"),
    path("sites/", views.site_list, name="site_list"),
    path("sites/<str:code>/summary/", views.site_summary, name="site_summary"),
    path("sites/<str:code>/hourly/", views.site_hourly, name="site_hourly"),
    path("sites/<str:code>/daily/", views.site_daily, name="site_daily"),
]
