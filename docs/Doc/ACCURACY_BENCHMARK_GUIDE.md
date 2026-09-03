# Panduan Benchmark Akurasi (Lighting Conditions)

Dokumen ini membantu Anda mengambil data akurasi berdasarkan kondisi pencahayaan menggunakan engine ArcFace.

## 1) Struktur Dataset yang Disarankan

```
datasets/benchmark/
  good/
    22024151/
      img1.jpg
      img2.jpg
  medium/
    22024151/
      img3.jpg
  low/
    22024151/
      img4.jpg
```

**Keterangan:**
- Folder `good`, `medium`, `low` mewakili kondisi pencahayaan.
- Subfolder adalah `student_id`.

## 2) Jalankan Benchmark

```powershell
cd c:\Users\Admin\Desktop\Project\FINAL_DEAD\DEAD
C:/Users/Admin/Desktop/Project/FINAL_DEAD/.venv/Scripts/python.exe benchmark_face_recognition.py --dataset datasets/benchmark
```

Output akan tersimpan di:
```
outputs/benchmark/
  benchmark_details_YYYYMMDD_HHMMSS.csv
  benchmark_summary_YYYYMMDD_HHMMSS.json
```

## 3) Format Output

### benchmark_details_*.csv
Berisi hasil per gambar:
- `file_path`, `lighting`, `student_id`, `predicted_id`, `confidence`, `status`.

### benchmark_summary_*.json
Ringkasan total dan per lighting:
- `accuracy_percent`
- `by_lighting_accuracy`

## 4) Benchmark Berulang Setelah Menambah Wajah Baru

**Ya, bisa.** Anda tinggal:
1. Tambahkan data baru ke dataset benchmark.
2. Jalankan kembali script benchmark.

Saran untuk konsistensi jurnal:
- Simpan semua hasil benchmark per tanggal.
- Catat jumlah mahasiswa saat pengujian.

## 5) Tips Pengambilan Data

- Minimal 10–15 sampel per lighting untuk setiap mahasiswa.
- Jaga jarak dan pose konsisten saat uji.
- Gunakan lighting yang realistis (kelas pagi/siang/sore).
