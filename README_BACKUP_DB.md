# Database Backup Guide (pgAdmin + Docker)

---

## 🇮🇩 VERSI INDONESIA

### Latar Belakang

Pada setup ini, **PostgreSQL + PostGIS** dan **pgAdmin** dijalankan menggunakan **Docker container**.
Hal penting yang perlu dipahami:

- pgAdmin **tidak menyimpan file backup di database**
- pgAdmin **tidak menyediakan fitur download file**
- Backup dibuat di **filesystem tempat pgAdmin berjalan**
- Jika pgAdmin berjalan di Docker, maka file backup berada **di dalam container**, bukan di Windows

Karena itu, diperlukan langkah tambahan untuk **mengambil file backup dari container ke host**.

---

## Langkah-langkah Backup Database

### 1️ Backup melalui pgAdmin

1. Buka pgAdmin (http://localhost:5050)
2. Klik kanan pada:
   - Database (`sentinel`) → **Backup**
3. Atur:
   - **Format**: Custom atau Directory (default)
   - **Filename**: biarkan default
4. Klik **Backup**
5. Tunggu hingga status **Finished**

Catatan:
pgAdmin **tidak menampilkan lokasi file backup secara eksplisit setelah selesai**.

---

### 2️ Cek lokasi storage pgAdmin di Docker

Buka PowerShell:

```powershell
docker ps
```

Pastikan container pgAdmin aktif, lalu:

```powershell
docker exec -it sentinel-pgadmin ls /var/lib/pgadmin/storage
```

Output contoh:
```
admin_local.dev
```

Folder tersebut berasal dari **email login pgAdmin**.

---

### 3️ Lihat isi storage user

```powershell
docker exec -it sentinel-pgadmin ls /var/lib/pgadmin/storage/admin_local.dev
```

Contoh output:
```
sentinel
sentinel-postgis
```

- `sentinel` → Backup database
- `sentinel-postgis` → Backup server

---

### 4️ Ambil file backup ke Windows

Backup dibuat dalam **format directory**, jadi harus disalin sebagai folder.

```powershell
docker cp sentinel-pgadmin:/var/lib/pgadmin/storage/admin_local.dev/sentinel C:\Users\<username>\sentinel_backup
```

Hasil di Windows:
```
sentinel_backup/
├── toc.dat
├── *.dat
└── ...
```

Backup berhasil disalin

---

### 5️ (Opsional) Masuk ke container dengan bash

Untuk eksplorasi langsung:

```powershell
docker exec -it sentinel-pgadmin bash
```

Di dalam container:
```bash
cd /var/lib/pgadmin/storage/admin_local.dev/sentinel
ls -lh
```

Keluar:
```bash
exit
```

---

### 6️ Restore dari backup directory

```bash
pg_restore -h localhost -p 5432 -U postgres -d sentinel -Fd sentinel_backup
```

---

## Rekomendasi Best Practice

Tambahkan volume mount agar file backup langsung muncul di host:

```yaml
volumes:
  - ./pgadmin_data:/var/lib/pgadmin
```

Dengan ini:
- Tidak perlu `docker cp`
- Backup langsung tersedia di filesystem lokal

---

## 🇬🇧 ENGLISH VERSION

### Background

In this setup, **PostgreSQL + PostGIS** and **pgAdmin** are running inside **Docker containers**.

Important facts:
- pgAdmin does **not store backups inside the database**
- pgAdmin has **no download button**
- Backups are written to the **OS filesystem**
- When pgAdmin runs in Docker, backups are stored **inside the container**, not on Windows

Therefore, manual steps are required to retrieve the backup file.

---

## Database Backup Steps

### 1️ Backup using pgAdmin

1. Open pgAdmin (http://localhost:5050)
2. Right-click:
   - Database (`sentinel`) → **Backup**
3. Configure:
   - **Format**: Custom or Directory (default)
   - **Filename**: leave default
4. Click **Backup**
5. Wait until status is **Finished**

Note:
pgAdmin does **not show the actual file location after completion**.

---

### 2️⃣ Locate pgAdmin storage in Docker

Open PowerShell:

```powershell
docker ps
```

Ensure pgAdmin container is running, then:

```powershell
docker exec -it sentinel-pgadmin ls /var/lib/pgadmin/storage
```

Example output:
```
admin_local.dev
```

This folder corresponds to the **pgAdmin login email**.

---

### 3️ Inspect user storage

```powershell
docker exec -it sentinel-pgadmin ls /var/lib/pgadmin/storage/admin_local.dev
```

Example:
```
sentinel
sentinel-postgis
```

- `sentinel` → Database backup
- `sentinel-postgis` → Server backup

---

### 4️ Copy backup to host (Windows)

The backup is created in **directory format**, so copy the entire folder:

```powershell
docker cp sentinel-pgadmin:/var/lib/pgadmin/storage/admin_local.dev/sentinel C:\Users\<username>\sentinel_backup
```

Result:
```
sentinel_backup/
├── toc.dat
├── *.dat
└── ...
```

Backup successfully copied

---

### 5️ (Optional) Enter container using bash

```powershell
docker exec -it sentinel-pgadmin bash
```

Inside container:
```bash
cd /var/lib/pgadmin/storage/admin_local.dev/sentinel
ls -lh
```

Exit:
```bash
exit
```

---

### 6️ Restore from directory backup

```bash
pg_restore -h localhost -p 5432 -U postgres -d sentinel -Fd sentinel_backup
```

---

## Best Practice Recommendation

Mount pgAdmin storage to host filesystem:

```yaml
volumes:
  - ./pgadmin_data:/var/lib/pgadmin
```

Benefits:
- No need for `docker cp`
- Backups instantly accessible on host

---

End of document.
