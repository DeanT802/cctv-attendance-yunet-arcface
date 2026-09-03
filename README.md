# Sistem Presensi Mahasiswa

Aplikasi web untuk mengelola presensi mahasiswa menggunakan Python Flask, MySQL, dan Bootstrap 5.

## Fitur

1. **Halaman Login** - Autentikasi pengguna
2. **Dashboard Presensi** dengan:
   - Statistik jumlah mahasiswa
   - Daftar jadwal per kelas  
   - Jumlah mata kuliah
   - Jumlah dosen pengampu
   - Grafik persentase kehadiran per kelas
3. **Manajemen Mahasiswa** dengan:
   - Daftar semua mahasiswa
   - Form tambah mahasiswa baru
   - Hapus data mahasiswa
   - Validasi data dan notifikasi

## Teknologi

- **Backend**: Python Flask
- **Database**: MySQL
- **Frontend**: Bootstrap 5, Chart.js
- **Icons**: Bootstrap Icons

## Struktur Project

```
DEAD/
├── app/
│   ├── __init__.py          # Konfigurasi Flask app
│   ├── routes.py            # Route handlers
│   ├── database.py          # Database connection dan queries
│   ├── templates/           # HTML templates
│   │   ├── base.html        # Base template
│   │   ├── login.html       # Halaman login
│   │   └── dashboard.html   # Dashboard utama
│   └── static/              # Static files (CSS, JS)
├── database/
│   └── schema.sql          # Database schema dan sample data
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables
└── run.py                # Entry point aplikasi
```

## Instalasi

### 1. Clone Repository

```bash
git clone <repository-url>
cd DEAD
```

### 2. Setup Python Environment

```bash
# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup MySQL Database

1. Install MySQL Server
2. Buat database baru:

```sql
CREATE DATABASE student_attendance;
```

3. Import schema dan sample data:

```bash
mysql -u root -p student_attendance < database/schema.sql
```

### 4. Konfigurasi Environment

Edit file `.env` sesuai dengan konfigurasi MySQL Anda:

```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=student_attendance

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 5. Jalankan Aplikasi
 
```bash
python run.py
```

Aplikasi akan berjalan di `http://localhost:5000`

## Login Demo

- **Username**: `admin`
- **Password**: `password`

## Screenshot Dashboard

Dashboard menampilkan:
- **Kartu Statistik**: Total mahasiswa, mata kuliah, dosen, dan jadwal
- **Tabel Jadwal**: Daftar jadwal per kelas dengan detail mata kuliah, waktu, dan dosen
- **Grafik Kehadiran**: Bar chart persentase kehadiran per kelas
- **Tabel Statistik**: Detail statistik kehadiran dengan progress bar

## Database Schema

### Tables:
- `students` - Data mahasiswa
- `teachers` - Data dosen
- `courses` - Data mata kuliah
- `schedules` - Jadwal kuliah
- `class_enrollments` - Pendaftaran mahasiswa ke kelas
- `attendance` - Record presensi
- `users` - User authentication

### Sample Data:
- 10 mahasiswa (TI dan SI)
- 5 dosen
- 7 mata kuliah
- 7 jadwal kelas
- Sample attendance records

## API Endpoints

- `GET /` - Redirect ke dashboard atau login
- `GET /login` - Halaman login
- `POST /login` - Proses login
- `GET /logout` - Logout
- `GET /dashboard` - Dashboard utama
- `GET /mahasiswa` - Halaman daftar mahasiswa
- `GET /mahasiswa/tambah` - Form tambah mahasiswa
- `POST /mahasiswa/tambah` - Proses tambah mahasiswa
- `GET /mahasiswa/hapus/<id>` - Hapus mahasiswa
- `GET /api/attendance-chart` - Data untuk grafik kehadiran (JSON)

## Development

### Menambah Route Baru

Edit file `app/routes.py` untuk menambah endpoint baru.

### Menambah Template

Tambahkan file HTML baru di folder `app/templates/` dengan extends `base.html`.

### Database Queries

Edit file `app/database.py` untuk menambah query database baru.

## Troubleshooting

### Database Connection Error
- Pastikan MySQL server berjalan
- Periksa konfigurasi di file `.env`
- Pastikan database `student_attendance` sudah dibuat

### Import Error
- Pastikan virtual environment sudah diaktifkan
- Install ulang dependencies: `pip install -r requirements.txt`

### Port Already in Use
- Ganti port di `run.py`: `app.run(debug=True, port=5001)`

## Benchmark Akurasi (Lighting)

Untuk mengukur akurasi berdasarkan pencahayaan, gunakan script:

```bash
python benchmark_face_recognition.py --dataset datasets/benchmark
```

Panduan lengkap ada di `Doc/ACCURACY_BENCHMARK_GUIDE.md`.

## License

MIT License
