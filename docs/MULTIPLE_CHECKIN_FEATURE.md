# Fitur Multiple Check-in (Absensi Berulang)

## 📋 Deskripsi
Fitur Multiple Check-in adalah sistem absensi berulang yang mengharuskan mahasiswa untuk melakukan scan wajah beberapa kali selama perkuliahan berlangsung. Tujuannya adalah untuk mencegah mahasiswa yang hanya hadir di awal perkuliahan kemudian meninggalkan kelas tanpa mengikuti pembelajaran hingga selesai.

## 🎯 Tujuan
- **Mencegah mahasiswa kabur**: Mahasiswa tidak bisa hanya scan wajah di awal lalu pergi
- **Meningkatkan kedisiplinan**: Memastikan mahasiswa hadir penuh selama perkulianan
- **Monitoring real-time**: Dosen bisa melihat progress kehadiran mahasiswa secara real-time
- **Data akurat**: Mendapatkan data kehadiran yang lebih akurat dengan multiple verification points

## ⚙️ Konfigurasi

### A. Pengaturan di Jadwal (Schedule)
Saat membuat jadwal baru, dosen dapat mengaktifkan dan mengkonfigurasi multiple check-in:

1. **Enable/Disable**: Toggle switch untuk mengaktifkan fitur
2. **Interval Checkpoint**: 
   - 20 menit (untuk kelas singkat)
   - 30 menit (standar untuk kelas 2 jam)
   - 45 menit (untuk kelas 3 jam)
   - 60 menit (untuk kelas panjang)
   - 90 menit (untuk kelas sangat panjang)

3. **Jumlah Checkpoint**: 2-5 kali check-in
4. **Live Preview**: Menampilkan jadwal checkpoint secara real-time

**Contoh Konfigurasi:**
- Kuliah: 08:00 - 10:00 (2 jam)
- Interval: 30 menit
- Jumlah: 4 checkpoint
- Hasil: Checkpoint di 08:00, 08:30, 09:00, 09:30

### B. Pengaturan Default
Jika checkpoint tidak diaktifkan:
- `checkpoint_enabled = 0`
- `checkpoint_interval = 30` (menit)
- `total_checkpoints = 1`

## 🗄️ Database Schema

### 1. Tabel `schedule_settings`
Menyimpan pengaturan checkpoint untuk setiap jadwal:
```sql
CREATE TABLE schedule_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    schedule_id INT NOT NULL,
    setting_key VARCHAR(100) NOT NULL,  -- 'checkpoint_enabled', 'checkpoint_interval', 'total_checkpoints'
    setting_value TEXT,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id) ON DELETE CASCADE,
    UNIQUE KEY unique_setting (schedule_id, setting_key)
);
```

### 2. Tabel `attendance_checkpoints`
Mencatat setiap checkpoint yang telah dilakukan mahasiswa:
```sql
CREATE TABLE attendance_checkpoints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    attendance_id INT NOT NULL,
    checkpoint_number INT NOT NULL,      -- 1, 2, 3, 4, dst
    checkpoint_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    detection_method VARCHAR(50) DEFAULT 'face_recognition',
    confidence_score DECIMAL(5,2) DEFAULT NULL,
    notes TEXT DEFAULT NULL,
    FOREIGN KEY (attendance_id) REFERENCES attendance(id) ON DELETE CASCADE,
    UNIQUE KEY unique_checkpoint (attendance_id, checkpoint_number)
);
```

### 3. Modifikasi Tabel `course_meetings`
Menambahkan kolom checkpoint settings:
```sql
ALTER TABLE course_meetings
ADD COLUMN checkpoint_interval INT DEFAULT 30,
ADD COLUMN total_checkpoints INT DEFAULT 1,
ADD COLUMN checkpoint_enabled TINYINT(1) DEFAULT 0;
```

### 4. Modifikasi Tabel `attendance`
Menambahkan summary checkpoint:
```sql
ALTER TABLE attendance
ADD COLUMN checkpoints_completed INT DEFAULT 0,
ADD COLUMN checkpoint_status VARCHAR(50) DEFAULT 'pending',  -- full, good, partial, poor
ADD COLUMN first_checkpoint_time DATETIME DEFAULT NULL,
ADD COLUMN last_checkpoint_time DATETIME DEFAULT NULL;
```

## 📊 Status Checkpoint

Sistem menghitung status kehadiran berdasarkan persentase checkpoint yang diselesaikan:

| Status | Persentase | Keterangan | Badge Color |
|--------|-----------|------------|-------------|
| **Full** | 100% | Semua checkpoint selesai | 🟢 Hijau (success) |
| **Good** | ≥75% | Minimal 3 dari 4 checkpoint | 🔵 Biru (info) |
| **Partial** | ≥50% | Minimal 2 dari 4 checkpoint | 🟡 Kuning (warning) |
| **Poor** | <50% | Kurang dari 50% checkpoint | 🔴 Merah (danger) |

**Contoh:**
- 4/4 checkpoint = **Full** (100%)
- 3/4 checkpoint = **Good** (75%)
- 2/4 checkpoint = **Partial** (50%)
- 1/4 checkpoint = **Poor** (25%)

## 🎨 User Interface

### A. Halaman Tambah Jadwal (`tambah_jadwal.html`)
**Komponen:**
1. Card "Pengaturan Absensi Berulang"
2. Toggle switch untuk enable/disable
3. Dropdown interval checkpoint
4. Dropdown jumlah checkpoint
5. Live preview menampilkan:
   - Jadwal checkpoint dengan waktu
   - Validasi (✅ valid / ⚠️ invalid)
   - Durasi kuliah dan ringkasan

**Preview Real-time:**
```
✅ Checkpoint 1: 08:00
✅ Checkpoint 2: 08:30
✅ Checkpoint 3: 09:00
✅ Checkpoint 4: 09:30

Durasi Kuliah: 120 menit (2.0 jam)
Checkpoint Valid: 4 dari 4
✅ Semua checkpoint dalam rentang waktu kuliah
```

### B. Halaman Ambil Presensi (`ambil_presensi.html`)
**Komponen:**
1. **Alert Peringatan**: Menginformasikan mahasiswa tentang multiple check-in
2. **3 Info Cards**:
   - **Checkpoint Aktif**: Menampilkan checkpoint saat ini (contoh: "2 / 4")
   - **Countdown Timer**: Waktu ke checkpoint berikutnya (format MM:SS)
   - **Progress Bar**: Jumlah mahasiswa yang sudah check-in
3. **Timeline Checkpoint**:
   - Checkpoint selesai: Badge hijau dengan ✅
   - Checkpoint aktif: Badge biru dengan 🔵
   - Checkpoint belum dimulai: Badge abu-abu dengan ⭕

**Screenshot Timeline:**
```
[✅ Checkpoint 1]  [🔵 Checkpoint 2]  [⭕ Checkpoint 3]  [⭕ Checkpoint 4]
  08:00-08:30       08:30-09:00        09:00-09:30        09:30-10:00
    Selesai         Aktif Sekarang   Belum Dimulai     Belum Dimulai
```

### C. Tabel Attendance
**Tambahan Kolom:**
- Badge checkpoint di kolom status
- Contoh: `Hadir [✅ 3/4 Good]`

## 🔧 Backend Methods

### Database Class Methods

#### 1. `add_schedule()`
**Parameter tambahan:**
- `checkpoint_enabled` (bool): Aktifkan checkpoint
- `checkpoint_interval` (int): Interval dalam menit
- `total_checkpoints` (int): Jumlah checkpoint

**Fungsi:**
Menyimpan pengaturan checkpoint ke tabel `schedule_settings` saat membuat jadwal baru.

#### 2. `create_course_meeting()`
**Modifikasi:**
Membaca pengaturan checkpoint dari `schedule_settings` dan menerapkannya ke `course_meetings` yang baru dibuat.

#### 3. `mark_checkpoint_attendance()`
```python
def mark_checkpoint_attendance(student_id, meeting_id, checkpoint_number, 
                               method='face_recognition', confidence=None, notes=None)
```
**Fungsi:**
- Mencari/membuat record attendance
- Insert/update record ke `attendance_checkpoints`
- Update summary di tabel `attendance`
- Return True/False

#### 4. `get_student_checkpoint_status()`
```python
def get_student_checkpoint_status(student_id, meeting_id)
```
**Return:**
```python
{
    'checkpoints_completed': 3,
    'total_checkpoints': 4,
    'checkpoint_status': 'good',
    'completed_checkpoints': [1, 2, 3]
}
```

#### 5. `get_current_checkpoint_number()`
```python
def get_current_checkpoint_number(meeting_id)
```
**Fungsi:**
Menghitung checkpoint aktif berdasarkan waktu yang telah berlalu sejak meeting dimulai.

**Algoritma:**
```
elapsed_minutes = (now - meeting_start_time) / 60
checkpoint_number = (elapsed_minutes / interval) + 1
return min(checkpoint_number, total_checkpoints)
```

#### 6. `get_meeting_checkpoint_summary()`
```python
def get_meeting_checkpoint_summary(meeting_id)
```
**Return:** Summary semua mahasiswa dalam meeting (untuk laporan)

## 🌐 API Endpoints

### POST `/api/record_checkpoint`
**Deskripsi:** Mencatat checkpoint attendance saat wajah terdeteksi

**Request Body:**
```json
{
    "student_id": "21024001",
    "meeting_id": 123,
    "checkpoint_number": 2,
    "confidence": 0.95,
    "method": "face_recognition"
}
```

**Response Success:**
```json
{
    "success": true,
    "message": "Checkpoint 2 recorded successfully",
    "checkpoints_completed": 2,
    "total_checkpoints": 4,
    "checkpoint_status": "partial"
}
```

**Response Error:**
```json
{
    "success": false,
    "error": "Student not found: 21024001"
}
```

## 💻 JavaScript Functions

### Checkpoint Timer Functions

#### 1. `getCurrentCheckpoint()`
Menghitung checkpoint aktif berdasarkan waktu yang telah berlalu.

#### 2. `getTimeToNextCheckpoint()`
Menghitung waktu tersisa hingga checkpoint berikutnya (dalam menit dan detik).

#### 3. `updateCheckpointUI()`
Update semua elemen UI checkpoint (current checkpoint, countdown, timeline).

#### 4. `recordCheckpoint(studentId, checkpointNumber, confidence)`
Memanggil API `/api/record_checkpoint` untuk mencatat checkpoint.

#### 5. `updateStudentCheckpointProgress()`
Update badge checkpoint di tabel attendance untuk mahasiswa tertentu.

#### 6. `updateOverallCheckpointProgress()`
Update progress bar keseluruhan di checkpoint info card.

## 🔄 Alur Kerja (Workflow)

### 1. Pembuatan Jadwal
```
Dosen → Form Tambah Jadwal → Aktifkan Checkpoint → Pilih Interval & Jumlah 
→ Live Preview → Submit → Data disimpan ke schedule_settings
```

### 2. Pembuatan Meeting
```
Sistem → Baca schedule_settings → Buat course_meeting dengan checkpoint settings
→ Meeting siap dengan checkpoint enabled
```

### 3. Proses Attendance
```
Meeting dimulai → Checkpoint timer mulai berjalan
→ Face recognition aktif → Wajah terdeteksi
→ markStudentPresent() → recordCheckpoint() 
→ API /api/record_checkpoint → Database mark_checkpoint_attendance()
→ Update UI (badge + progress bar)
```

### 4. Real-time Display
```
Setiap 1 detik:
- Update current checkpoint number
- Update countdown timer
- Update timeline visualization
- Update progress bar
```

## 📈 Use Cases

### Use Case 1: Kelas 2 Jam dengan 4 Checkpoint
**Setting:**
- Waktu: 08:00 - 10:00
- Interval: 30 menit
- Total: 4 checkpoint

**Timeline:**
1. **08:00 - 08:30**: Checkpoint 1 aktif
2. **08:30 - 09:00**: Checkpoint 2 aktif
3. **09:00 - 09:30**: Checkpoint 3 aktif
4. **09:30 - 10:00**: Checkpoint 4 aktif

**Skenario:**
- Mahasiswa A scan di 08:05, 08:35, 09:05, 09:35 → **Full (4/4)** ✅
- Mahasiswa B scan di 08:05, 08:35, 09:05 → **Good (3/4)** 🔵
- Mahasiswa C scan di 08:05, 09:05 → **Partial (2/4)** 🟡
- Mahasiswa D scan di 08:05 saja → **Poor (1/4)** 🔴

### Use Case 2: Kelas 3 Jam dengan 4 Checkpoint
**Setting:**
- Waktu: 13:00 - 16:00
- Interval: 45 menit
- Total: 4 checkpoint

**Timeline:**
1. **13:00 - 13:45**: Checkpoint 1
2. **13:45 - 14:30**: Checkpoint 2
3. **14:30 - 15:15**: Checkpoint 3
4. **15:15 - 16:00**: Checkpoint 4

## 🐛 Troubleshooting

### Problem 1: Checkpoint tidak terecord
**Kemungkinan penyebab:**
- API endpoint error
- Database connection gagal
- Student ID tidak ditemukan

**Solusi:**
```javascript
// Check browser console untuk error
// Check server logs untuk database error
// Verify student_id exists in students table
```

### Problem 2: Timer tidak update
**Kemungkinan penyebab:**
- JavaScript tidak load
- Meeting date format salah
- Checkpoint tidak enabled

**Solusi:**
```javascript
// Check console: "[Checkpoint System] Initialized with settings: ..."
// Verify current_meeting.checkpoint_enabled = true
// Check meeting_date format: 'YYYY-MM-DD HH:MM:SS'
```

### Problem 3: Progress bar tidak update
**Kemungkinan penyebab:**
- recordCheckpoint() tidak dipanggil
- API response tidak include checkpoint data
- Element ID tidak ditemukan

**Solusi:**
```javascript
// Check console: "[Checkpoint] ✅ Recorded checkpoint X for student Y"
// Verify API response contains: checkpoints_completed, total_checkpoints, checkpoint_status
// Check element exists: getElementById('checkpoint-progress-bar')
```

## 📝 Testing Checklist

- [ ] Buat jadwal baru dengan checkpoint enabled
- [ ] Verifikasi live preview menampilkan checkpoint dengan benar
- [ ] Buat meeting dari jadwal tersebut
- [ ] Verifikasi meeting memiliki checkpoint settings
- [ ] Buka halaman ambil presensi
- [ ] Verifikasi checkpoint info card muncul
- [ ] Verifikasi current checkpoint dihitung dengan benar
- [ ] Verifikasi countdown timer berjalan
- [ ] Verifikasi timeline visualization update
- [ ] Start face recognition
- [ ] Detect student face beberapa kali (simulasi checkpoint berbeda)
- [ ] Verifikasi checkpoint terecord di database
- [ ] Verifikasi badge checkpoint muncul di tabel
- [ ] Verifikasi progress bar update
- [ ] Submit attendance
- [ ] Check laporan presensi
- [ ] Verifikasi checkpoint details tampil

## 🚀 Future Enhancements

1. **Email Notification**: Kirim email ke mahasiswa yang miss checkpoint
2. **SMS Reminder**: SMS 5 menit sebelum checkpoint berikutnya
3. **Checkpoint History**: Tampilkan riwayat checkpoint per mahasiswa
4. **Analytics Dashboard**: Grafik checkpoint completion rate
5. **Auto-adjust Interval**: Sistem otomatis adjust interval berdasarkan durasi kuliah
6. **Checkpoint Penalties**: Kurangi nilai jika miss checkpoint
7. **Makeup Checkpoint**: Izinkan mahasiswa untuk makeup missed checkpoint
8. **Export Checkpoint Report**: Export detailed checkpoint report ke Excel/PDF

## 📚 Related Files

### Backend
- `app/database.py`: Database methods untuk checkpoint
- `app/routes.py`: API endpoint `/api/record_checkpoint`
- `database/multiple_checkin_schema.sql`: Database schema

### Frontend
- `app/templates/tambah_jadwal.html`: Form konfigurasi checkpoint
- `app/templates/ambil_presensi.html`: Checkpoint timer dan UI
- `app/templates/laporan_presensi.html`: Laporan checkpoint (TODO)

### Database
- `schedule_settings`: Menyimpan pengaturan checkpoint per jadwal
- `attendance_checkpoints`: Menyimpan record checkpoint per mahasiswa
- `course_meetings`: Menyimpan settings checkpoint per meeting
- `attendance`: Menyimpan summary checkpoint per mahasiswa

## 👥 Contributors
- **Feature Design**: Based on user requirement to prevent students from leaving class early
- **Implementation**: Complete full-stack implementation with database, backend API, and frontend UI
- **Testing**: Comprehensive testing checklist provided

## 📄 License
Part of the Face Recognition Attendance System project.

---

**Last Updated**: December 2025
**Version**: 1.0.0
**Status**: ✅ Implementation Complete (Frontend + Backend + Database)
