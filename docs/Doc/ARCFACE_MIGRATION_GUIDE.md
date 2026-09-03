# ArcFace Migration Guide

## Tujuan
Dokumen ini menjelaskan migrasi dari embedding lama (`face_encodings.pkl` berbasis dlib) ke embedding baru ArcFace (`arcface_embeddings.pkl`).

## Ringkasan Arsitektur
- Detection: YuNet (existing)
- Encoding + Matching: ArcFace (InsightFace)
- Embedding store: `models/arcface_embeddings.pkl`

## Kenapa perlu migrasi ulang embedding?
Embedding dlib dan ArcFace berada pada ruang fitur yang berbeda, jadi **tidak bisa langsung dikonversi**. Dataset wajah perlu diproses ulang menggunakan ArcFace.

## Prasyarat
- Dependency ArcFace terpasang (`insightface`, `onnxruntime-gpu`)
- Folder dataset wajah tersedia (default: `uploads/faces/<student_id>/...`)
- Koneksi DB aktif (opsional, untuk mengambil nama mahasiswa)

## Konfigurasi `.env`
Pastikan minimal:

- `ARCFACE_EMBEDDINGS_FILE=arcface_embeddings.pkl`
- `FACE_MATCH_DISTANCE_THRESHOLD=0.45`
- `FACE_MIN_CONF_LARGE=0.60`
- `FACE_MIN_CONF_MEDIUM=0.55`
- `FACE_MIN_CONF_SMALL=0.48`

## Jalankan migrasi

```powershell
cd c:\Users\Admin\Desktop\Project\FINAL_DEAD\DEAD
C:/Users/Admin/Desktop/Project/FINAL_DEAD/.venv/Scripts/python.exe migrate_arcface_embeddings.py --dry-run
```

Jika hasil dry-run sudah benar, jalankan migrasi aktual:

```powershell
cd c:\Users\Admin\Desktop\Project\FINAL_DEAD\DEAD
C:/Users/Admin/Desktop/Project/FINAL_DEAD/.venv/Scripts/python.exe migrate_arcface_embeddings.py --reset
```

Migrasi satu mahasiswa saja:

```powershell
cd c:\Users\Admin\Desktop\Project\FINAL_DEAD\DEAD
C:/Users/Admin/Desktop/Project/FINAL_DEAD/.venv/Scripts/python.exe migrate_arcface_embeddings.py --student-id 22024151
```

## Validasi cepat
Setelah migrasi:
1. Jalankan aplikasi.
2. Uji `presensi_face` 3-5 kali untuk mahasiswa yang sudah dimigrasi.
3. Cek log confidence dan stabilitas hasil pada jarak jauh.

## Catatan GPU
Jika CUDA runtime di Windows belum lengkap, InsightFace akan fallback ke CPU otomatis.
Untuk aktivasi GPU penuh ONNX Runtime, pastikan CUDA 12 runtime + cuDNN yang sesuai sudah terpasang di sistem.
