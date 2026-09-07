# Smart Class Attendance System (YuNet + ArcFace)

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/DeanT802/cctv-attendance-yunet-arcface)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/framework-Flask%202.3.3-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/vision-OpenCV%20%7C%20InsightFace-orange.svg)](https://github.com/deepinsight/insightface)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

Sistem presensi mahasiswa otomatis berbasis **Computer Vision** dan **Deep Learning** yang mengintegrasikan streaming kamera jaringan (**RTSP IP Camera CCTV**) dan kamera lokal (**Webcam**). Dirancang khusus untuk ruang perkuliahan modern (*Smart Class*) dengan kemampuan mengenali banyak wajah sekaligus (*Multiple Check-in*), adaptif terhadap variasi pencahayaan dan silau (*backlight*), serta dilengkapi manajemen sesi presensi berkala (*checkpoints*) dan pelaporan akademik komprehensif.

---

## Arsitektur Pipeline Visi Komputer

```text
[ RTSP IP Camera (Ezviz/CCTV) / Webcam ]
                   │
                   ▼
     [ Zero-Latency Frame Buffer ]  <-- Multi-threading Worker (Latest Frame)
                   │
                   ▼
     [ Normalisasi Kontras CLAHE ]  <-- Ekualisasi Adaptif Kanal L (LAB Space)
                   │
                   ▼
     [ Deteksi Wajah CNN YuNet ]    <-- Bounding Box & 5-Point Facial Landmarks
                   │
                   ▼
   [ Face Alignment & Pre-process ]
                   │
                   ▼
     [ Ekstraksi Fitur ArcFace ]    <-- Deep Representation (512-D Embedding Vector)
                   │
                   ▼
   [ Cosine Similarity Matching ]   <-- Threshold Similarity (Cosine >= 0.55)
                   │
                   ▼
   [ Asynchronous Attendance Log ]  <-- Debounce Anti-Duplicate & MySQL Update
```

---

## Fitur Utama

### 1. Computer Vision & Pengenalan Wajah Mutakhir
- **Deteksi Cepat YuNet**: Model CNN ONNX berbobot ringan dengan latensi deteksi < 15 ms per frame.
- **Ekstraksi Biometrik ArcFace**: Representasi fitur fasial 512-dimensi (*ResNet-50 backbone*) dengan variansi pemisah antarkelas yang tinggi.
- **Normalisasi CLAHE**: Mengeliminasi efek *backlight* jendela dan pencahayaan redup, meningkatkan akurasi hingga +26,8% pada kondisi silau ekstrem.
- **Akselerasi Inferensi**: Mendukung eksekusi ONNX Runtime dengan akselerasi GPU (DirectML / CUDA) serta fallback CPU.

### 2. Transmisi Kamera IP & Zero-Latency Buffer
- **Multi-source Support**: Kompatibel dengan RTSP IP Camera (Ezviz C6N, Hikvision, Dahua) maupun webcam lokal.
- **Buffer Management Multi-threading**: Thread latar belakang secara kontinu membuang frame tertumpuk, menjaga latensi video streaming tetap stabil di ~120 ms tanpa video lag.

### 3. Presensi Otomatis & Multiple Check-in
- **Simultaneous Recognition**: Mampu mendeteksi dan mengidentifikasi hingga 5 mahasiswa sekaligus dalam satu frame dengan latensi total < 75 ms (~13–28 FPS).
- **Sesi Presensi Berbasis Checkpoint**: Sesi perkuliahan dapat dibagi menjadi checkpoint berkala untuk memastikan kedisiplinan mahasiswa sepanjang jam kuliah.
- **Status Deteksi Real-Time**: Umpan balik visual interaktif meliputi timer inferensi AI, status verifikasi kehadiran, kartu identitas mahasiswa terverifikasi dengan foto profil dan skor *confidence* (%), serta riwayat presensi harian.
- **Debounce Suppression**: Mencegah pencatatan presensi ganda (*anti-spam*) saat mahasiswa berada di depan kamera dalam durasi lama.

### 4. Manajemen Entitas & Dataset Biometrik
- **Master Data Mahasiswa & Dosen**: Registrasi, pembaruan, dan pemfilteran data akademik lengkap dengan validasi pencegahan duplikasi NIM.
- **Kelola Foto Wajah & Auto-sync**: Antarmuka unggah foto multi-sudut (*dataset* profil) yang otomatis mengekstrak vektor dan menyinkronkan model (`arcface_embeddings.pkl`).
- **Penjadwalan Perkuliahan**: Pemetaan relasi dosen pengajar, mata kuliah, kelas, hari, jam, dan ruang Smart Class.
- **Presensi Bebas / Uji Coba Wajah**: Modul verifikasi mandiri bagi mahasiswa untuk menguji keterbacaan wajah sebelum sesi perkuliahan dimulai.
- **Panel Intervensi Presensi Manual**: Fasilitas korektif bagi dosen pengajar untuk mengubah status kehadiran (Hadir, Tidak Hadir, Terlambat, Izin) jika diperlukan.
- **Pelaporan Akademik Terstandarisasi**: Rekapitulasi presensi semester format cetak resmi (PDF dan lembar kerja Excel) lengkap dengan lembar pengesahan.

### 5. Antarmuka Pengguna Modern (v1.1.0)
- Desain *Claude Warm Editorial* yang nyaman dipandang, elegan, dan bersih.
- Tipografi berkualitas tinggi menggunakan font **Newsreader** (Heading) dan **Plus Jakarta Sans** (Body & UI).
- Tata letak responsif berbasis Bootstrap 5 dengan komponen formulir, kartu analitik, dan tabel interaktif.

---

## Tech Stack

| Komponen | Teknologi / Library |
|---|---|
| **Backend Framework** | Python 3.10+, Flask 2.3.3 |
| **Computer Vision** | OpenCV 4.8+, InsightFace 0.7.3 (ArcFace ResNet-50), YuNet ONNX |
| **Inference Engine** | ONNX Runtime (DirectML / CPU Execution Provider) |
| **Basis Data** | MySQL Server 8.0+ via `mysql-connector-python` |
| **Frontend** | HTML5, Vanilla CSS3 (Custom Design System), Bootstrap 5, Chart.js |
| **Keamanan** | Bcrypt password hashing, session-based authentication |

---

## Struktur Direktori

```text
DEAD/
├── app/
│   ├── __init__.py                 # Inisialisasi Flask application & konfigurasi
│   ├── routes.py                   # Handler rute utama (Auth, Dashboard, Mahasiswa, Jadwal, Laporan)
│   ├── face_recognition_routes.py  # Handler rute presensi, live recognition, stream & polling
│   ├── database.py                 # Abstraksi koneksi dan transaksi basis data MySQL
│   ├── camera_discovery.py         # Utilitas deteksi kamera lokal dan profil RTSP
│   ├── face_recognition/           # Engine Computer Vision
│   │   ├── arcface_recognition.py  # Pipeline ekstraksi ArcFace, CLAHE, dan cosine matching
│   │   ├── yunet_detector.py       # Wrapper deteksi wajah YuNet ONNX
│   │   ├── face_aligner.py         # Normalisasi landmark fasial 5 titik
│   │   └── config.py               # Konfigurasi parameter ambang batas pengenalan
│   ├── static/
│   │   ├── css/styles.css          # Master stylesheet (Claude Warm Editorial design tokens)
│   │   └── js/                     # Skrip interaksi frontend dan polling AJAX
│   └── templates/                  # Template HTML Jinja2
│       ├── base.html               # Master layout
│       ├── login.html              # Halaman login
│       ├── dashboard.html          # Halaman dashboard analitik
│       ├── mahasiswa.html          # Manajemen data mahasiswa & modal kelola foto wajah
│       ├── jadwal.html             # Manajemen penjadwalan kuliah
│       ├── ambil_presensi.html     # Sesi presensi kelas, IP Cam stream, & live detection status
│       ├── presensi_face.html      # Halaman uji coba presensi wajah mandiri
│       └── laporan_presensi.html   # Rekapitulasi dan pratinjau cetak laporan
├── database/
│   └── schema.sql                  # Skema database relasional & data awal
├── models/
│   ├── face_detection_yunet_*.onnx # Model deteksi wajah YuNet
│   └── arcface_embeddings.pkl      # Penyimpanan vektor embedding biometrik mahasiswa
├── uploads/
│   └── faces/                      # Direktori penyimpanan foto dataset per NIM
├── config/                         # File konfigurasi aplikasi
├── requirements.txt                # Dependensi Python utama
├── .env.example                    # Contoh variabel lingkungan
├── run.py                          # Entry point aplikasi Flask
└── README.md                       # Dokumentasi proyek
```

---

## Panduan Instalasi & Menjalankan Sistem

### 1. Prasyarat Sistem
- **Python**: Versi 3.10 atau lebih baru
- **MySQL Server**: Versi 8.0 atau lebih baru
- **Git**: Untuk cloning repositori
- **Kamera**: Webcam USB/bawaan laptop atau Kamera IP dengan protokol RTSP (misal Ezviz C6N) pada jaringan yang sama

### 2. Kloning Repositori & Setup Virtual Environment
```bash
git clone https://github.com/DeanT802/cctv-attendance-yunet-arcface.git
cd cctv-attendance-yunet-arcface/DEAD

# Membuat virtual environment
python -m venv .venv

# Mengaktifkan virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate
```

### 3. Instalasi Dependensi Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **Catatan Dependensi Vision**: Paket `insightface`, `onnxruntime`, dan `opencv-python` akan otomatis mengunduh model pembantu yang dibutuhkan saat pertama kali dieksekusi.

### 4. Konfigurasi Basis Data MySQL
1. Buat database baru di MySQL Server:
   ```sql
   CREATE DATABASE student_attendance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. Impor skema tabel dan data awal:
   ```bash
   mysql -u root -p student_attendance < database/schema.sql
   ```

### 5. Konfigurasi File Environment (`.env`)
Salin file `.env.example` menjadi `.env`, lalu sesuaikan kredensial database dan parameter kamera:
```bash
copy .env.example .env
```

Sesuaikan isi `.env`:
```env
# Database Configuration
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=student_attendance
SECRET_KEY=generate_a_secure_random_key

# Upload Directory
UPLOAD_FOLDER=uploads

# RTSP IP Camera Configuration (Sesuaikan IP & Kredensial Kamera CCTV)
RTSP_URL=rtsp://admin:verification_code@192.168.1.10:554/h264/ch1/main/av_stream

# Face Recognition Parameters
FACE_MATCH_DISTANCE_THRESHOLD=0.55
ARCFACE_EMBEDDINGS_FILE=arcface_embeddings.pkl
```

### 6. Menjalankan Aplikasi
Jalankan server pengembangan Flask:
```bash
python run.py
```

Aplikasi web dapat diakses melalui peramban di:
`http://127.0.0.1:5000`

---

## Kredensial Demo Masuk

| Peran (Role) | Username / Email | Password Default | Hak Akses |
|---|---|---|---|
| **Administrator** | `admin` | `password` | Akses penuh seluruh master data, jadwal, sinkronisasi foto wajah, dan laporan |
| **Dosen Pengajar** | `dosen` | `password` | Inisiasi sesi presensi kelas, koreksi manual, dan unduh rekapitulasi kehadiran |

---

## Parameter Konfigurasi Pengenalan Wajah (`.env`)

| Variabel | Default | Penjelasan |
|---|---|---|
| `FACE_MATCH_DISTANCE_THRESHOLD` | `0.55` | Ambang batas kemiripan kosinus (*Cosine Similarity*). Nilai lebih tinggi meningkatkan ketatnya pencocokan. |
| `RTSP_URL` | - | URL stream video RTSP dari kamera IP CCTV. |
| `RECOGNITION_BURST_ENABLED` | `true` | Mengaktifkan pengambilan beberapa frame untuk verifikasi konsistensi wajah. |
| `ARCFACE_EMBEDDINGS_FILE` | `arcface_embeddings.pkl` | Nama berkas penyimpanan cache vektor biometrik di folder `models/`. |

---

## Catatan Rilis

### Versi 1.1.0 (Terbaru)
- **UI/UX Overhaul**: Penerapan palet warna *Claude Warm Editorial* (`#F8EDE3`, `#DFD3C3`, `#D0B8A8`, `#7D6E83`) pada seluruh modul antarmuka.
- **Status Deteksi Real-Time**: Penambahan kotak status deteksi interaktif pada halaman presensi kelas (`ambil_presensi.html`), dilengkapi indikator proses AI, live timer, kartu pengenalan mahasiswa, dan riwayat presensi.
- **Manajemen Foto Mahasiswa**: Integrasi modal edit profil mahasiswa dengan galeri foto multi-sudut dan sinkronisasi otomatis ke `arcface_embeddings.pkl`.
- **Optimalisasi Sinkronisasi Model**: Penanganan otomatis pembaruan embedding saat foto profil mahasiswa ditambah atau dihapus.

### Versi 1.0.0
- Rilis perdana sistem presensi berbasis YuNet dan ArcFace.
- Integrasi streaming RTSP Kamera IP Ezviz C6N dan webcam lokal.
- Fitur Multiple Check-in simultan dan penanganan normalisasi kontras CLAHE.
- Ekspor laporan rekapitulasi kehadiran ke format PDF dan Excel.

---

## Lisensi

Proyek ini didistribusikan di bawah lisensi **MIT License**. Lihat berkas [LICENSE](LICENSE) untuk informasi lebih lanjut.

---

## Penulis & Kontribusi

- **Dean Rama Prananta** (NIM: 22024151)
- Program Studi Sarjana Terapan (D4) Teknik Informatika
- Jurusan Teknik Elektro, **Politeknik Negeri Manado**
- Dosen Pembimbing: **Harson Kapoh, S.T., M.T.**
