## Import Database (Wajib Sebelum Menjalankan Proyek)

Sebelum menjalankan layanan frontend atau backend, **database PostgreSQL harus di-restore terlebih dahulu**.

Proyek ini bergantung pada skema database dan data spasial yang telah ditentukan (PostgreSQL + PostGIS).  
Jika database tidak di-import, aplikasi backend akan gagal dijalankan karena tabel, ekstensi, dan kolom geometri belum tersedia.

---

### Prasyarat

- Docker sudah berjalan
- Container PostgreSQL + PostGIS sudah berjalan
- pgAdmin dapat diakses (misalnya http://localhost:5050)
- Direktori backup database tersedia di komputer Anda:
  

> **Penting**  
> Backup dibuat dalam **format directory**, bukan sebagai satu file `.sql`.  
> Backup tersebut **harus di-restore sebagai Directory backup** di pgAdmin.

---

### Langkah 1: Membuat Database

1. Buka **pgAdmin**
2. Hubungkan ke server PostgreSQL
3. Klik kanan **Databases** → **Create** → **Database**
4. Atur:
   - **Nama database**: `sentinel`
   - **Owner**: `postgres` (atau user database yang digunakan)
5. Klik **Save**

---

### Langkah 2: Restore dari Backup (`sentinel_backup`)

1. Klik kanan pada database **`sentinel`**
2. Pilih **Restore…**
3. Konfigurasikan opsi restore:
   - **Format**: `Directory`
   - **Folder**: pilih direktori `sentinel_backup`
4. (Disarankan)
   - Aktifkan **Clean before restore**
   - Aktifkan **Create database objects**
5. Klik **Restore**
6. Tunggu hingga proses selesai dengan sukses

---

### Langkah 3: Verifikasi Import Database

Setelah proses restore selesai, pastikan bahwa:

- Tabel-tabel sudah tersedia (misalnya `projects`, `sampling_points`, `surveys`)
- Ekstensi PostGIS sudah terpasang
- Tidak ada error yang muncul pada log restore

Jika semua sudah terverifikasi, maka setup database telah selesai.

---

# Cara Menjalankan Proyek

FRONT END :
python -m http.server 3000

BACKEND :
python -m uvicorn app.main:app --reload


# AOI Sentinel Survey System

Sistem manajemen project, sampling, dan survey lapangan berbasis peta untuk studi biomassa pohon.

---

## 1. Tujuan Sistem

Sistem ini digunakan untuk:
- Mengelola project berbasis Area of Interest (AOI)
- Membuat titik sampling
- Surveyor mengambil titik survey
- Input data lapangan dan foto
- Menghitung biomassa pohon

---

## 2. Peran Pengguna

### Admin
- Membuat dan mengelola project
- Menentukan AOI
- Generate titik sampling
- Melihat seluruh data
- Mengelola master data pohon

### Surveyor
- Login
- Melihat project
- Mengambil titik sampling
- Mengisi survey lapangan
- Upload foto

---

## 3. Alur Sistem

### Project
1. Admin login
2. Buat project
3. Tentukan AOI
4. Generate sampling
5. Project aktif

### Survey
1. Surveyor login
2. Pilih project
3. Ambil titik sampling
4. Isi data survey

---

## 4. Status Titik Sampling

- open
- partial
- full
- done

---

## 5. Aturan

- Maksimal 5 surveyor per titik
- Surveyor hanya bisa edit datanya sendiri
- Minimal 1 foto wajib

---

## 6. Struktur Project

SENTINEL/
- BACKEND/
- FRONTEND/
- README.md

---

## 7. Entitas Database

- projects
- sampling_points
- surveys
- users
- survey_assignments
- tree_species

---

## 8. MVP

- Login admin & surveyor
- Project & AOI
- Sampling
- Survey input
- Biomassa

---

## 9. Pengembangan

- Export data
- Validasi survey
- NDVI
- Dashboard

---

## 10. Lisensi

Untuk penelitian dan non-komersial.

## Lisensi & Hak Cipta

© 2026 I Wayan Pio Pratama. Seluruh Hak Dilindungi.

Perangkat lunak ini beserta seluruh dokumentasi, struktur basis data,
algoritma, metodologi, dan turunannya merupakan kekayaan intelektual
milik **I Wayan Pio Pratama (2026)** dan dilindungi oleh undang-undang
hak cipta yang berlaku.

Proyek ini tidak diperkenankan untuk digunakan, direproduksi,
didistribusikan, dimodifikasi, maupun dijadikan dasar karya turunan
untuk kepentingan akademik, penelitian, publikasi, maupun komersial
tanpa mencantumkan sitasi yang benar.

Apabila sistem, metodologi, data turunan, maupun hasil analisis dari
perangkat lunak ini digunakan dalam karya ilmiah, publikasi, laporan
penelitian, tesis, disertasi, jurnal, atau bentuk publikasi lainnya,
maka WAJIB mencantumkan sitasi sebagai berikut:

### Format Sitasi APA Edisi ke-7

Pratama, I. W. P. (2026). *Carbon Survey System* [Perangkat Lunak]. GitHub.  
https://github.com/piopratama/carbon-survey

Kegagalan dalam mencantumkan sitasi yang sesuai dapat dianggap sebagai
pelanggaran etika akademik dan pelanggaran hak kekayaan intelektual.
