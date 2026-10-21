# Mobius Service Dashboard: Spesifikasi & Panduan Build

Dokumen ini adalah panduan lengkap untuk membangun dashboard Mobius yang sebenarnya (bukan mockup). Bisa dipakai langsung oleh developer, atau ditempel ke Claude Code sebagai instruksi kerja.

- **Frontend:** React (Vite) + react-leaflet
- **Backend:** Django + Django REST Framework
- **Database:** SQLite
- **Gaya UI:** minimalis, datar, tanpa efek berkilau (tanpa gradasi, bayangan, animasi, glow)

---

## 1. Latar Belakang Produk

Mobius adalah perangkat penghemat listrik yang dipasang di setiap site.

Contoh logika: beban (load) site 10 W, tetapi daya yang tersedia dari PLN hanya 7 W. Mobius membangkitkan tambahan 3 W sehingga total yang diterima beban tetap 10 W.

```
Listrik PLN  ──►  Mobius  ──►  Load
   7 W            +3 W        10 W
```

Aturan hitung (dipakai di seluruh sistem):

| Besaran | Rumus |
|---|---|
| Load (kWh) | `PLN + Mobius` |
| Mobius Contribution (%) | `Mobius / Load × 100` |
| PLN Lifted By (%) | `Mobius / PLN × 100` |
| Est. Saving (Rp) | `Mobius kWh × tarif PLN per kWh` |

Tarif default: **Rp 1.444,70 / kWh** (disimpan per site agar bisa diubah).
Jika `Load = 0` atau `PLN = 0`, persentase ditampilkan `0%`, bukan error.

---

## 2. Alur Pengguna

1. **Landing page**: peta Leaflet layar penuh berisi titik koordinat semua site.
   - Warna titik mengikuti status: `Done` hijau, `On Progress` kuning.
   - Filter sederhana di atas peta: Tenant dan Status.
2. **Klik titik** → muncul **kartu rangkuman** (panel di kanan pada desktop, panel bawah pada HP).
3. **Isi kartu rangkuman:**
   - **Site Detail**: Site ID, Tenant, Lokasi, Status, Mobius Unit, Rated Load.
   - **Ringkasan hari ini**: Mobius Energy, PLN Energy, Load Energy, Mobius Contribution, Est. Saving.
   - Satu baris alur energi: `PLN 46,25 → Mobius +11,80 → Load 58,05 kWh`.
   - Tombol **Buka Dashboard Site**.
4. **Halaman Dashboard Site** (`/sites/:code`): tampilan lengkap seperti desain sebelumnya.
   - Baris KPI hari ini.
   - Energy Flow (PLN → Mobius → Load).
   - Power Performance Today (grafik per jam, 00:00 sampai cut-off).
   - Trend 30 hari terakhir (batang kontribusi, garis kWh, tabel harian).

---

## 3. Struktur Repository

```
mobius-dashboard/
├── backend/
│   ├── manage.py
│   ├── config/                # settings.py, urls.py
│   ├── sites_app/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── services.py        # fungsi hitung & agregasi
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── tests.py
│   │   └── management/commands/seed_demo.py
│   ├── requirements.txt
│   └── db.sqlite3             # jangan di-commit
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js
        ├── format.js
        ├── styles.css
        ├── pages/
        │   ├── MapPage.jsx
        │   └── SitePage.jsx
        └── components/
            ├── FilterBar.jsx
            ├── SiteCard.jsx
            ├── SiteDetail.jsx
            ├── KpiRow.jsx
            ├── EnergyFlow.jsx
            ├── HourlyChart.jsx
            └── TrendChart.jsx
```

---

## 4. Backend (Django + DRF + SQLite)

### 4.1 Setup

```bash
mkdir mobius-dashboard && cd mobius-dashboard
python -m venv .venv && source .venv/bin/activate
pip install "django>=5.0" djangorestframework django-cors-headers
pip freeze > backend/requirements.txt
django-admin startproject config backend
cd backend && python manage.py startapp sites_app
```

`config/settings.py` (bagian yang perlu diubah):

```python
INSTALLED_APPS += ["rest_framework", "corsheaders", "sites_app"]
MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}

TIME_ZONE = "Asia/Jakarta"
USE_TZ = True

CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]   # hanya untuk dev, bisa dilewati jika pakai proxy Vite

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
```

`config/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("sites_app.urls")),
]
```

### 4.2 Model Data

```python
# sites_app/models.py
from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=50, unique=True)   # IOH, Tsel, XLSMA

    def __str__(self):
        return self.name


class Site(models.Model):
    class Status(models.TextChoices):
        DONE = "Done", "Done"
        ON_PROGRESS = "On Progress", "On Progress"

    code = models.CharField(max_length=20, unique=True)             # CLG002
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name="sites")
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
```

Catatan: `load` tidak disimpan, selalu dihitung dari `PLN + Mobius` agar angka tidak pernah tidak konsisten.

`admin.py`: daftarkan `Tenant`, `Site`, `HourlyReading` agar site bisa ditambah dan diedit lewat Django Admin.

### 4.3 Service Hitung

```python
# sites_app/services.py
from datetime import timedelta
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
    rows = site.readings.filter(ts__gte=start, ts__lt=end)
    return [
        {"hour": timezone.localtime(r.ts).strftime("%H:00"),
         **calc(r.pln_kwh, r.mobius_kwh, site.tariff_per_kwh)}
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
    return [{"date": r["day"].isoformat(), **calc(r["pln"], r["mobius"], site.tariff_per_kwh)} for r in rows]
```

### 4.4 Serializer, View, URL

```python
# sites_app/serializers.py
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
        fields = ["code", "tenant", "status", "area", "latitude", "longitude",
                  "mobius_unit", "rated_load_kw", "tariff_per_kwh", "installed_at"]
```

```python
# sites_app/views.py
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
    if t := request.query_params.getlist("tenant"):
        qs = qs.filter(tenant__name__in=t)
    if s := request.query_params.getlist("status"):
        qs = qs.filter(status__in=s)
    return Response(SiteListSerializer(qs, many=True).data)


@api_view(["GET"])
def site_summary(request, code):
    """Dipakai kartu rangkuman di peta: site detail + angka hari ini."""
    site = get_object_or_404(Site.objects.select_related("tenant"), code=code)
    return Response({"site": SiteDetailSerializer(site).data, "today": services.today_summary(site)})


@api_view(["GET"])
def site_hourly(request, code):
    site = get_object_or_404(Site, code=code)
    day = request.query_params.get("date")
    day = date.fromisoformat(day) if day else None
    return Response(services.hourly_series(site, day))


@api_view(["GET"])
def site_daily(request, code):
    site = get_object_or_404(Site, code=code)
    days = min(int(request.query_params.get("days", 30)), 90)
    return Response(services.daily_series(site, days))
```

Catatan: `hourly_series` menerima `date`; pastikan konversinya ke datetime lokal (gunakan `timezone.make_aware(datetime.combine(day, time.min))`) sebelum dipakai di `local_midnight`.

```python
# sites_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("tenants/", views.tenants),
    path("sites/", views.site_list),
    path("sites/<str:code>/summary/", views.site_summary),
    path("sites/<str:code>/hourly/", views.site_hourly),
    path("sites/<str:code>/daily/", views.site_daily),
]
```

### 4.5 Ringkasan Endpoint

| Method | URL | Fungsi |
|---|---|---|
| GET | `/api/tenants/` | Daftar tenant untuk filter |
| GET | `/api/sites/?tenant=Tsel&status=Done` | Daftar site + koordinat (untuk titik peta) |
| GET | `/api/sites/{code}/summary/` | Site detail + angka hari ini (isi kartu) |
| GET | `/api/sites/{code}/hourly/?date=YYYY-MM-DD` | Data per jam (default: hari cut-off) |
| GET | `/api/sites/{code}/daily/?days=30` | Data harian 30 hari terakhir |

Contoh respons `summary`:

```json
{
  "site": {
    "code": "MGW006", "tenant": "Tsel", "status": "Done",
    "area": "Magelang, Jawa Tengah", "latitude": -7.4797, "longitude": 110.2177,
    "mobius_unit": "MBX-3006", "rated_load_kw": 5.5, "tariff_per_kwh": 1444.7,
    "installed_at": "2026-03-14"
  },
  "today": {
    "pln_kwh": 46.25, "mobius_kwh": 11.8, "load_kwh": 58.05,
    "contribution_pct": 20.33, "lift_pct": 25.51, "saving_rp": 17047,
    "cutoff": "2026-10-21T17:00:00+07:00",
    "latest_hour": { "pln_kwh": 2.74, "mobius_kwh": 0.74, "load_kwh": 3.48,
                     "contribution_pct": 21.26, "lift_pct": 27.01, "saving_rp": 1069 }
  }
}
```

### 4.6 Data Demo (`seed_demo`)

Buat management command `seed_demo` agar dashboard langsung terisi saat pengembangan.

Site contoh (koordinat kota, ganti dengan koordinat asli site saat tersedia):

| Code | Tenant | Status | Lokasi | Lat | Lng |
|---|---|---|---|---|---|
| CLG002 | Tsel | Done | Cilegon, Banten | -6.0023 | 106.0111 |
| MGW006 | Tsel | Done | Magelang, Jawa Tengah | -7.4797 | 110.2177 |
| PWK002 | Tsel | Done | Purwakarta, Jawa Barat | -6.5569 | 107.4431 |
| TNG095 | Tsel | On Progress | Tangerang, Banten | -6.1783 | 106.6319 |
| BKS031 | IOH | Done | Bekasi, Jawa Barat | -6.2383 | 106.9756 |
| SMG118 | IOH | On Progress | Semarang, Jawa Tengah | -6.9667 | 110.4167 |
| KRW007 | XLSMA | Done | Karawang, Jawa Barat | -6.3015 | 107.3376 |
| BDG204 | XLSMA | Done | Bandung, Jawa Barat | -6.9175 | 107.6191 |

Aturan generator data (per site, 31 hari ke belakang sampai hari ini jam 17:00):

- `load(jam) = skala_site × (2.6 + 0.9 × max(0, sin(π × (jam − 5) / 16))) × acak(0.96 .. 1.04)` kWh per jam.
- `mobius = load × eff_site × acak(0.88 .. 1.12)`, dengan `eff_site` antara 0.15 dan 0.19.
- `pln = load − mobius`.
- Pakai `random.Random(seed)` dengan seed dari kode site agar data stabil.
- Sisipkan 2 hari "turun" (beban dikali ±0.6, Mobius ×0.75) agar grafik tren terlihat realistis.
- Gunakan `bulk_create(..., ignore_conflicts=True)` supaya command aman dijalankan ulang.

### 4.7 Menjalankan Backend

```bash
python manage.py makemigrations sites_app
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver        # http://localhost:8000
```

---

## 5. Frontend (React + Leaflet)

### 5.1 Setup

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm i react-router-dom @tanstack/react-query leaflet react-leaflet recharts
```

`vite.config.js` (proxy agar tidak perlu CORS saat dev):

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://localhost:8000" } },
});
```

`main.jsx`: impor `leaflet/dist/leaflet.css` dan `./styles.css`, bungkus `<App />` dengan `QueryClientProvider` dan `BrowserRouter`.

### 5.2 Routing

```jsx
// App.jsx
import { Route, Routes } from "react-router-dom";
import MapPage from "./pages/MapPage";
import SitePage from "./pages/SitePage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MapPage />} />
      <Route path="/sites/:code" element={<SitePage />} />
    </Routes>
  );
}
```

### 5.3 API & Format

```js
// api.js
const get = (url) => fetch(url).then((r) => {
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
});

export const getTenants = () => get("/api/tenants/");
export const getSites = (tenants = [], statuses = []) => {
  const q = new URLSearchParams();
  tenants.forEach((t) => q.append("tenant", t));
  statuses.forEach((s) => q.append("status", s));
  return get(`/api/sites/?${q}`);
};
export const getSummary = (code) => get(`/api/sites/${code}/summary/`);
export const getHourly = (code) => get(`/api/sites/${code}/hourly/`);
export const getDaily = (code) => get(`/api/sites/${code}/daily/?days=30`);
```

```js
// format.js  (angka gaya Indonesia: 11,80 dan 1.868,39)
export const num = (n, d = 2) =>
  Number(n ?? 0).toLocaleString("id-ID", { minimumFractionDigits: d, maximumFractionDigits: d });
export const pct = (n, d = 2) => `${num(n, d)}%`;
export const rp = (n) => `Rp ${Math.round(n ?? 0).toLocaleString("id-ID")}`;
```

### 5.4 Landing Page: Peta

Gunakan `CircleMarker` (bukan marker gambar bawaan) agar tidak ada masalah ikon di Vite dan tampilannya tetap datar.

```jsx
// pages/MapPage.jsx
import { useState } from "react";
import { CircleMarker, MapContainer, TileLayer } from "react-leaflet";
import { useQuery } from "@tanstack/react-query";
import { getSites } from "../api";
import FilterBar from "../components/FilterBar";
import SiteCard from "../components/SiteCard";

const STATUS_COLOR = { "Done": "#1b7f4d", "On Progress": "#b7791f" };

export default function MapPage() {
  const [tenants, setTenants] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [selected, setSelected] = useState(null);

  const { data: sites = [] } = useQuery({
    queryKey: ["sites", tenants, statuses],
    queryFn: () => getSites(tenants, statuses),
  });

  return (
    <div className="map-page">
      <FilterBar tenants={tenants} setTenants={setTenants}
                 statuses={statuses} setStatuses={setStatuses} count={sites.length} />
      <MapContainer center={[-6.9, 108.5]} zoom={8} className="map" zoomControl>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap contributors &copy; CARTO'
        />
        {sites.map((s) => (
          <CircleMarker
            key={s.code}
            center={[s.latitude, s.longitude]}
            radius={selected === s.code ? 11 : 8}
            pathOptions={{ color: "#ffffff", weight: 2, fillColor: STATUS_COLOR[s.status], fillOpacity: 1 }}
            eventHandlers={{ click: () => setSelected(s.code) }}
          />
        ))}
      </MapContainer>
      {selected && <SiteCard code={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
```

Perilaku tambahan:
- Saat filter berubah dan site terpilih tidak ada di hasil, tutup kartu.
- Setelah data pertama masuk, sesuaikan peta ke semua titik dengan `map.fitBounds` (komponen kecil memakai `useMap`).
- Legenda kecil di pojok peta: titik hijau = Done, titik kuning = On Progress.
- Tile CARTO "light" dipilih karena bersih dan netral. Pertahankan atribusi OpenStreetMap dan CARTO. Untuk produksi dengan trafik besar, pertimbangkan penyedia tile berlangganan.

### 5.5 Kartu Rangkuman

```jsx
// components/SiteCard.jsx
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getSummary } from "../api";
import SiteDetail from "./SiteDetail";
import { num, pct, rp } from "../format";

export default function SiteCard({ code, onClose }) {
  const { data, isLoading, isError } = useQuery({ queryKey: ["summary", code], queryFn: () => getSummary(code) });

  return (
    <aside className="site-card" aria-label={`Ringkasan site ${code}`}>
      <button className="close" onClick={onClose} aria-label="Tutup">×</button>
      {isLoading && <p className="muted">Memuat data site…</p>}
      {isError && <p className="error">Data site gagal dimuat. Coba klik titik lagi.</p>}
      {data && (
        <>
          <SiteDetail site={data.site} />
          <h3>Hari ini (cut-off {new Date(data.today.cutoff).toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" })})</h3>
          <dl className="kpi-grid">
            <div><dt>Mobius Energy</dt><dd className="c-mob">{num(data.today.mobius_kwh)} kWh</dd></div>
            <div><dt>PLN Energy</dt><dd className="c-pln">{num(data.today.pln_kwh)} kWh</dd></div>
            <div><dt>Load Energy</dt><dd className="c-load">{num(data.today.load_kwh)} kWh</dd></div>
            <div><dt>Mobius Contribution</dt><dd>{pct(data.today.contribution_pct)}</dd></div>
            <div><dt>Est. Saving</dt><dd>{rp(data.today.saving_rp)}</dd></div>
          </dl>
          <p className="flow-line">
            PLN {num(data.today.pln_kwh)} → Mobius +{num(data.today.mobius_kwh)} → Load {num(data.today.load_kwh)} kWh
          </p>
          <Link className="btn" to={`/sites/${code}`}>Buka Dashboard Site</Link>
        </>
      )}
    </aside>
  );
}
```

`SiteDetail.jsx` menampilkan pasangan label/nilai: Site ID, Tenant, Location, Status (pill teks datar), Mobius Unit, Rated Load (kW), Tarif PLN.

### 5.6 Halaman Dashboard Site (`/sites/:code`)

Susunan dari atas ke bawah (satu kolom di HP, grid di desktop):

1. Header: tombol "← Peta", nama site, Site Detail ringkas, teks "Update Cut Off : 21 Oct 2026 | 17:00".
2. `KpiRow`: Mobius Energy Today, PLN Energy Today, Load Energy Today, Mobius Contribution, Est. Saving Today.
3. Dua kolom: `EnergyFlow` | `HourlyChart`.
4. `TrendChart`: ringkasan total 30 hari, grafik, lalu tabel harian.

Spesifikasi komponen:

- **EnergyFlow**: SVG statis, tiga node berurutan `PLN → MOBIUS → LOAD`, garis putus-putus statis dengan panah (tanpa animasi), nilai kWh di bawah node, teks "PLN input lifted by X%". Di bawahnya satu baris persamaan jam terakhir: `Load 3,48 kW = PLN 2,74 kW + Mobius 0,74 kW`.
- **HourlyChart** (Recharts `LineChart`): tiga garis `mobius_kwh`, `pln_kwh`, `load_kwh`, sumbu X jam `00:00`–cut-off, tanpa titik penanda, tooltip standar, legenda teks.
- **TrendChart** (Recharts `ComposedChart`): batang transparan untuk `contribution_pct` (label persen di atas batang), tiga garis kWh per hari, lalu tabel dengan baris `Mobius Contr.`, `MOBIUS (kWh)`, `PLN (kWh)`, `LOAD (kWh)`, `Est. Saving`. Tabel boleh di-scroll horizontal, kolom pertama sticky.
- Hari dengan beban turun diberi warna teks kuning di tabel (tanpa ikon).

### 5.7 Gaya UI (Minimalis, Tanpa Efek Berkilau)

Aturan wajib:

- Tanpa `box-shadow`, `text-shadow`, `linear-gradient`, `blur`, glow, atau animasi/transisi dekoratif.
- Semua permukaan datar: latar putih, border 1 px abu terang, radius maksimal 8 px.
- Satu keluarga huruf sans-serif sistem (mis. `system-ui`), ukuran dasar 14–16 px, angka memakai `font-variant-numeric: tabular-nums`.
- Warna fungsional hanya tiga seri data plus status:
  - Mobius hijau, PLN biru, Load kuning tua.
  - Done hijau, On Progress kuning.
- Tidak ada ikon dekoratif. Teks label cukup.
- Kontras teks minimal WCAG AA, area klik tombol minimal 40 px.
- Dukung mode gelap lewat token warna (`prefers-color-scheme`), tetap datar.

```css
/* styles.css (token dasar) */
:root {
  --bg: #f3f6f7; --surface: #ffffff; --ink: #14272e; --muted: #5b717a; --line: #d6e0e3;
  --brand: #0b5a8f; --mob: #167a4a; --pln: #2559c4; --load: #8f6200;
  --ok: #1b7f4d; --warn: #b7791f;
}
@media (prefers-color-scheme: dark) {
  :root { --bg:#0e171b; --surface:#152329; --ink:#e4eff2; --muted:#8fa7b0; --line:#27393f;
          --brand:#6db6f2; --mob:#36d283; --pln:#6aa2ff; --load:#f3b53a; }
}
body { margin:0; background:var(--bg); color:var(--ink); font:15px/1.45 system-ui, sans-serif; }

.map-page { height:100vh; position:relative; }
.map { height:100%; width:100%; }
.site-card {
  position:absolute; z-index:1000; top:64px; right:16px; width:360px; max-height:calc(100% - 80px);
  overflow:auto; background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:16px;
}
@media (max-width: 700px) {
  .site-card { top:auto; right:0; bottom:0; left:0; width:auto; max-height:60%; border-radius:8px 8px 0 0; }
}
.kpi-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px 14px; margin:0; }
.kpi-grid dt { font-size:11px; letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }
.kpi-grid dd { margin:2px 0 0; font-weight:600; font-variant-numeric:tabular-nums; }
.c-mob { color:var(--mob); } .c-pln { color:var(--pln); } .c-load { color:var(--load); }
.btn { display:inline-block; margin-top:14px; padding:10px 14px; border:1px solid var(--brand);
       border-radius:6px; color:var(--brand); text-decoration:none; font-weight:600; }
```

Status ditampilkan sebagai teks berwarna kecil (mis. "Done" hijau), bukan lencana berkilau.

---

## 6. Menjalankan Seluruh Aplikasi (Dev)

```bash
# terminal 1
cd backend && source ../.venv/bin/activate && python manage.py runserver

# terminal 2
cd frontend && npm run dev     # http://localhost:5173
```

---

## 7. Pengujian

Backend (`tests.py`), minimal:

- `calc()` dengan `load = 0` dan `pln = 0` tidak melempar error.
- `load == pln + mobius` untuk semua respons.
- `daily_series` mengembalikan maksimal 30 hari dan tidak memuat hari berjalan.
- Filter `/api/sites/?tenant=Tsel&status=Done` hanya mengembalikan site yang sesuai.
- `/api/sites/XXX/summary/` mengembalikan 404 untuk kode yang tidak ada.

Frontend, cek manual:

- Peta menampilkan semua titik; filter mengubah jumlah titik.
- Klik titik membuka kartu, klik titik lain mengganti isi kartu, tombol × menutup kartu.
- Di lebar 400 px kartu muncul di bawah dan halaman tidak scroll ke samping.
- Angka kartu sama dengan angka di halaman Dashboard Site untuk site yang sama.

---

## 8. Kriteria Selesai

- [ ] Landing page menampilkan peta dengan titik semua site, warna sesuai status.
- [ ] Klik titik membuka kartu berisi Site Detail dan ringkasan hari ini.
- [ ] Tombol di kartu membuka halaman Dashboard Site lengkap (KPI, Energy Flow, grafik jam, tren 30 hari).
- [ ] Data bersumber dari SQLite lewat API Django, tidak ada angka hardcode di frontend.
- [ ] `Load = PLN + Mobius` konsisten di semua tampilan.
- [ ] UI datar tanpa gradasi, bayangan, atau animasi.
- [ ] Site bisa ditambah dan diedit lewat Django Admin.
- [ ] Layout nyaman di HP dan desktop.

---

## 9. Tahap Lanjutan (di Luar Cakupan Awal)

- **Ingest data perangkat:** endpoint `POST /api/readings/` dengan API key per site, mendukung bulk upsert per jam.
- **Login & hak akses:** tenant hanya melihat site miliknya (Django auth + token).
- **Ekspor:** unduh CSV tren 30 hari.
- **Peringatan:** tandai site yang kontribusi Mobius-nya turun di bawah ambang.
- **Pindah database:** SQLite cukup untuk puluhan site dengan data per jam. Jika site dan frekuensi data bertambah banyak atau banyak penulis bersamaan, pindah ke PostgreSQL (cukup ubah `DATABASES`, model tetap sama).
- **Deploy:** `gunicorn` + `whitenoise` untuk backend, `npm run build` untuk frontend yang disajikan oleh Nginx atau langsung dari Django.

---

## 10. Catatan untuk Developer / Claude Code

- Kerjakan berurutan: model → migrasi → `seed_demo` → endpoint → halaman peta → kartu → halaman Dashboard Site.
- Pertahankan nama field dan endpoint persis seperti dokumen ini agar frontend dan backend cocok.
- Semua istilah di UI memakai bahasa Inggris seperti desain awal (Mobius Energy Today, PLN Energy Today, Load Energy Today, Mobius Contribution, Est. Saving).
- Format angka selalu gaya Indonesia (koma desimal, titik ribuan) lewat `format.js`.
