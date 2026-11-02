from django.contrib.auth.models import User
from django.db import models


class Region(models.Model):
    code = models.CharField(max_length=50, unique=True)   # JABODETABEK, JABAR, JATENG
    name = models.CharField(max_length=100)               # Jabodetabek, Jawa Barat, Jawa Tengah

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class Role(models.TextChoices):
        REGIONAL_USER = "regional_user", "Regional User"
        NATIONAL_ADMIN = "national_admin", "National Admin"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REGIONAL_USER)

    def __str__(self):
        region_label = self.region.name if self.region else "Nasional"
        return f"{self.user.username} - {region_label} ({self.role})"


class Site(models.Model):
    class Status(models.TextChoices):
        DONE = "Done", "Done"
        ON_PROGRESS = "On Progress", "On Progress"

    code = models.CharField(max_length=20, unique=True)             # CLG002
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="sites", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ON_PROGRESS)
    area = models.CharField(max_length=120)                         # "Cilegon, Banten"
    latitude = models.FloatField()
    longitude = models.FloatField()
    mobius_unit = models.CharField(max_length=30, blank=True)       # MBX-2002
    rated_load_kw = models.FloatField(default=0)
    tariff_per_kwh = models.FloatField(default=1444.70)             # Rupiah
    installed_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class HourlyReading(models.Model):
    """Satu baris = energi satu jam, dimulai dari `ts` (jam awal, timezone-aware)."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="readings")
    ts = models.DateTimeField(db_index=True)
    pln_kwh = models.FloatField()
    mobius_kwh = models.FloatField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["site", "ts"], name="uniq_site_ts")]
        indexes = [models.Index(fields=["site", "ts"])]
        ordering = ["ts"]

    @property
    def load_kwh(self):
        return self.pln_kwh + self.mobius_kwh

    def __str__(self):
        return f"{self.site.code} @ {self.ts}"
