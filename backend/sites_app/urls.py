from django.urls import path
from . import views

urlpatterns = [
    # Auth endpoints
    path("auth/login/", views.auth_login, name="auth_login"),
    path("auth/logout/", views.auth_logout, name="auth_logout"),
    path("auth/me/", views.auth_me, name="auth_me"),

    # Site endpoints
    path("sites/", views.site_list, name="site_list"),
    path("sites/<str:code>/summary/", views.site_summary, name="site_summary"),
    path("sites/<str:code>/hourly/", views.site_hourly, name="site_hourly"),
    path("sites/<str:code>/daily/", views.site_daily, name="site_daily"),
    path("sites/<str:code>/export-performance/", views.site_export_performance, name="site_export_performance"),
]
