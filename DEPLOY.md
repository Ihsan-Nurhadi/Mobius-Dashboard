# Panduan Deployment Mobius Dashboard ke VPS Docker

Dokumentasi ini menjelaskan langkah-langkah menjalankan seluruh sistem Mobius Dashboard di VPS menggunakan Docker & Nginx Reverse Proxy.

- **IP VPS:** `110.232.92.134`
- **Port:** `3006`
- **URL Akses:** `http://110.232.92.134:3006`

---

## 1. Arsitektur Kontainer

Sesuai spesifikasi, terdapat 3 kontainer independen yang saling terhubung dalam jaringan internal (`mobius_network`):

| Nama Kontainer | Deskripsi & Port | Tugas |
|---|---|---|
| **`mobius_backend`** | Internal: `8000` | Django 5 + Gunicorn (3 workers) + SQLite Database (`/app/data`) |
| **`mobius_frontend`** | Internal: `80` | React (Vite build) disajikan oleh Nginx internal |
| **`mobius_nginx`** | Host: **`3006:80`** | Gateway Reverse Proxy utama yang mengarahkan trafik: <br>• `/api/` ➔ `mobius_backend` <br>• `/admin/` ➔ `mobius_backend` <br>• `/static/` ➔ Django staticfiles volume <br>• `/` ➔ `mobius_frontend` |

---

## 2. Persiapan di VPS

Pastikan Docker dan Docker Compose telah terpasang di VPS `110.232.92.134`:

```bash
docker --version
docker compose version
```

Pastikan port **3006** sudah dibuka di firewall VPS (misalnya UFW atau security group provider cloud):
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

# Build image dan jalankan seluruh kontainer di latar belakang
docker compose up -d --build
```

### C. Cek Status Kontainer
Periksa apakah ketiga kontainer sudah berjalan dengan baik:
```bash
docker ps
```
Hasil yang diharapkan:
```
CONTAINER ID   IMAGE                          STATUS         PORTS                  NAMES
xxxxxxxxxxxx   nginx:alpine                   Up x minutes   0.0.0.0:3006->80/tcp   mobius_nginx
xxxxxxxxxxxx   mobius-dashboard-mobius_frontend   Up x minutes   80/tcp                 mobius_frontend
xxxxxxxxxxxx   mobius-dashboard-mobius_backend    Up x minutes   8000/tcp               mobius_backend
```

---

## 4. Perintah Berguna (Maintenance)

### Membuat Akun Admin Django di Kontainer
Untuk login ke halaman admin Django:
```bash
docker exec -it mobius_backend python manage.py createsuperuser
```

### Melihat Log Kontainer
```bash
# Log seluruh layanan
docker compose logs -f

# Log spesifik backend atau nginx
docker logs -f mobius_backend
docker logs -f mobius_nginx
```

### Menghentikan / Merestart Layanan
```bash
# Merestart semua layanan
docker compose restart

# Menghentikan kontainer
docker compose down

# Menghentikan dan menghapus volume data (jika ingin reset penuh):
# docker compose down -v
```

---

## 5. Verifikasi Akses

Buka browser dan akses URL berikut:
- **Dashboard Utama:** [http://110.232.92.134:3006/](http://110.232.92.134:3006/)
- **Detail Site:** [http://110.232.92.134:3006/sites/CLG002](http://110.232.92.134:3006/sites/CLG002)
- **Django Admin:** [http://110.232.92.134:3006/admin/](http://110.232.92.134:3006/admin/)
- **API Status:** [http://110.232.92.134:3006/api/sites/](http://110.232.92.134:3006/api/sites/)
