# Panduan Deployment Mobius Dashboard ke VPS Docker

Dokumentasi ini menjelaskan langkah-langkah menjalankan seluruh sistem Mobius Dashboard di VPS menggunakan Docker & Nginx Reverse Proxy, lengkap dengan **Simulator Otomatis Penghasil Data Harian/Jam**.

- **IP VPS:** `110.232.92.134`
- **Port:** `3006`
- **URL Akses:** `http://110.232.92.134:3006`

---

## 1. Arsitektur Kontainer

Sistem terdiri dari 4 kontainer independen yang saling terhubung dalam jaringan internal (`mobius_network`):

| Nama Kontainer | Deskripsi & Port | Tugas |
|---|---|---|
| **`mobius_backend`** | Internal: `8000` | Django 5 + Gunicorn (3 workers) + SQLite Database (`/app/data`) |
| **`mobius_simulator`** | Background Worker | Layanan otomatis yang berjalan terus-menerus menghasilkan pembacaan energi berkala untuk setiap site dan melakukan *auto-backfill* jika ada jam/hari yang tertinggal |
| **`mobius_frontend`** | Internal: `80` | React (Vite build) disajikan oleh Nginx internal |
| **`mobius_nginx`** | Host: **`3006:80`** | Gateway Reverse Proxy utama yang mengarahkan trafik: <br>• `/api/` ➔ `mobius_backend` <br>• `/admin/` ➔ `mobius_backend` <br>• `/static/` ➔ Django staticfiles volume <br>• `/` ➔ `mobius_frontend` |

---

## 2. Persiapan di VPS

Pastikan Docker dan Docker Compose telah terpasang di VPS `110.232.92.134`:

```bash
docker --version
docker compose version
```

Pastikan port **3006** sudah dibuka di firewall VPS:
```bash
sudo ufw allow 3006/tcp
sudo ufw status
```

---

## 3. Langkah Menjalankan Aplikasi di VPS

### A. Salin Berkas Proyek ke VPS
Anda dapat menggunakan `git clone` atau menyalin berkas via `scp`/`rsync`:
```bash
# Contoh menggunakan rsync dari lokal ke VPS:
rsync -avz --exclude 'node_modules' --exclude '.venv' --exclude 'staticfiles' ./ user@110.232.92.134:/home/user/mobius-dashboard/
```

### B. Jalankan dengan Docker Compose
Masuk ke direktori proyek di VPS:
```bash
cd /home/user/mobius-dashboard

# Build image dan jalankan seluruh kontainer (backend, simulator, frontend, nginx)
docker compose up -d --build
```

### C. Cek Status Kontainer
Periksa apakah seluruh kontainer sudah berjalan dengan baik:
```bash
docker ps
```
Hasil yang diharapkan:
```
CONTAINER ID   IMAGE                               STATUS         PORTS                  NAMES
xxxxxxxxxxxx   nginx:alpine                        Up x minutes   0.0.0.0:3006->80/tcp   mobius_nginx
xxxxxxxxxxxx   mobius-dashboard-mobius_frontend    Up x minutes   80/tcp                 mobius_frontend
xxxxxxxxxxxx   mobius-dashboard-mobius_backend     Up x minutes   8000/tcp               mobius_backend
xxxxxxxxxxxx   mobius-dashboard-mobius_simulator   Up x minutes                          mobius_simulator
```

---

## 4. Pengelolaan Simulator Data

Layanan `mobius_simulator` otomatis mengecek dan menambahkan data energi baru secara kontinu.
- **Logika Generator:** Membentuk kurva beban (*load curve*) realistis (sinusoidal di siang hari, variasi acak, dan kontribusi Mobius).
- **Auto-Backfill:** Jika server sempat mati atau ada rentang waktu yang terlewat, simulator secara cerdas melengkapi semua jam yang belum tercatat hingga waktu saat ini.

### Memantau Log Simulator
```bash
docker logs -f mobius_simulator
```
Contoh log:
```text
Starting Mobius Data Simulator (interval=300s, once=False)...
[2026-10-22 08:35:00] Simulator: Added 8 new readings across 8 sites.
[2026-10-22 08:40:00] Simulator: All 8 sites are up-to-date (cutoff 08:00).
```

### Menjalankan Sinkronisasi Manual (Sekali Jalan)
Jika Anda ingin men-trigger generasi data secara instan tanpa menunggu interval:
```bash
docker exec -it mobius_backend python manage.py run_simulator --once
```

### Mengubah Interval Pengecekan
Di `docker-compose.yml`, Anda dapat menyesuaikan variabel `SIMULATOR_INTERVAL_SECONDS` (default: 300 detik / 5 menit):
```yaml
environment:
  - SIMULATOR_INTERVAL_SECONDS=300
```
Lalu jalankan `docker compose up -d mobius_simulator`.

---

## 5. Menjalankan Sebagai Linux Systemd Service (Alternatif Tanpa Docker)

Jika di kemudian hari ingin menjalankan simulator langsung di OS VPS (menggunakan virtualenv Python lokal):

1. Salin berkas unit ke systemd:
   ```bash
   sudo cp services/mobius-simulator.service /etc/systemd/system/
   ```
2. Edit path direktori di `/etc/systemd/system/mobius-simulator.service`:
   ```ini
   WorkingDirectory=/home/user/mobius-dashboard/backend
   ExecStart=/home/user/mobius-dashboard/.venv/bin/python manage.py run_simulator --interval 300
   ```
3. Aktifkan dan jalankan service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now mobius-simulator
   sudo systemctl status mobius-simulator
   ```

---

## 6. Perintah Berguna Lainnya

### Membuat Akun Admin Django di Kontainer
```bash
docker exec -it mobius_backend python manage.py createsuperuser
```

### Melihat Log Seluruh Layanan
```bash
docker compose logs -f
```

### Menghentikan / Merestart Layanan
```bash
docker compose restart
docker compose down
```

---

## 7. Verifikasi Akses

Buka browser dan akses URL berikut:
- **Dashboard Utama:** [http://110.232.92.134:3006/](http://110.232.92.134:3006/)
- **Detail Site:** [http://110.232.92.134:3006/sites/CLG002](http://110.232.92.134:3006/sites/CLG002)
- **Django Admin:** [http://110.232.92.134:3006/admin/](http://110.232.92.134:3006/admin/)
- **API Status:** [http://110.232.92.134:3006/api/sites/](http://110.232.92.134:3006/api/sites/)
