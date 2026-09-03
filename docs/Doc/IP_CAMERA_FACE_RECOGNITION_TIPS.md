# Tips Face Recognition dengan IP Camera (CCTV)

## 🔍 Mengapa IP Camera Sulit Mengenali Wajah?

IP Camera (CCTV) memiliki karakteristik berbeda dari webcam:

| Aspek | Webcam | IP Camera (CCTV) |
|-------|---------|------------------|
| **Jarak** | 30-50 cm (dekat) | 1-3 meter (jauh) |
| **Sudut** | Sejajar (eye-level) | Atas (top-down) |
| **Resolusi** | 720p dekat | 2K tapi jauh |
| **Lighting** | Konsisten | Bervariasi |
| **Ukuran Wajah** | Besar | Kecil |

## ✅ Solusi & Tips

### 1. **Posisi Optimal untuk IP Camera**

Untuk hasil terbaik dengan IP Camera:

- 📏 **Jarak**: 1-1.5 meter dari kamera
- 👀 **Sudut**: Hadap langsung ke kamera (tidak miring)
- 💡 **Lighting**: Pastikan wajah terang, hindari backlight
- 🎯 **Posisi Wajah**: Usahakan wajah mengisi 30-40% frame

### 2. **Setting yang Sudah Dioptimasi**

Sistem sudah dioptimalkan untuk IP Camera:
- ✅ Confidence threshold **diturunkan** dari 65% ke 55%
- ✅ Resolution **otomatis disesuaikan** (2K → 720p)
- ✅ JPEG quality **dioptimalkan** untuk streaming
- ✅ Detailed logging untuk debugging

### 3. **Monitoring Confidence Score**

Saat menggunakan IP Camera, perhatikan log di console terminal:

```
[Face Recognition] Match found: Dean Rama Prananta (ID: 22024151)
[Face Recognition] Confidence: 58.5% (distance: 0.4150)
[Face Recognition] Threshold: < 0.45
[Face Recognition] ✅ Recognition SUCCESS with 58.5% confidence
```

**Interpretasi:**
- **> 80%**: Excellent (wajah sangat jelas)
- **70-80%**: Good (wajah jelas)
- **60-70%**: Acceptable (wajah cukup jelas)
- **55-60%**: Minimum (wajah kurang jelas, tapi masih diterima)
- **< 55%**: Rejected (wajah tidak cukup jelas)

### 4. **Jika Masih Tidak Dikenali**

**Opsi A: Pindah Lebih Dekat ke Kamera**
- Dekati kamera hingga jarak 1 meter
- Pastikan wajah terlihat jelas di layar

**Opsi B: Improve Lighting**
- Tambah lampu di area kamera
- Hindari backlight (cahaya dari belakang)
- Gunakan soft light (cahaya lembut)

**Opsi C: Adjust Sudut**
- Pastikan wajah menghadap kamera
- Jangan miring atau menunduk
- Eye contact dengan kamera

**Opsi D: Re-register dengan IP Camera** (Advanced)
1. Gunakan IP Camera untuk mengambil foto registrasi
2. Ambil 3-5 foto dari jarak dan sudut yang berbeda
3. Dataset akan lebih compatible dengan IP Camera

### 5. **Troubleshooting**

#### ❌ "Face not recognized"
**Penyebab**: Distance terlalu besar atau confidence < 55%

**Solusi**:
```bash
# Cek console log untuk melihat actual confidence:
[Face Recognition] ❌ No match - distance 0.4800 >= threshold 0.45

# Jika distance hampir mendekati threshold (0.45-0.48):
# Dekati kamera atau improve lighting
```

#### ⚠️ "Recognition confidence too low"
**Penyebab**: Confidence 50-55% (borderline)

**Solusi**:
- Dekati kamera 20-30 cm
- Pastikan wajah menghadap langsung
- Improve lighting

#### 🔄 "Multiple similar matches"
**Penyebab**: Ada wajah mirip di database

**Solusi**:
- Dekati kamera untuk detail lebih jelas
- Pastikan hanya 1 wajah di frame

## 🎯 Best Practices

### Untuk Administrator:

1. **Mount Camera di Lokasi Strategis**
   - Eye level jika memungkinkan
   - Jarak 1-2 meter dari area presensi
   - Pencahayaan yang cukup

2. **Gunakan Substream untuk Streaming**
   ```env
   # Lebih stabil dan ringan
   RTSP_URL=rtsp://admin:password@ip:554/h264/ch1/sub/av_stream
   ```

3. **Monitor Console Logs**
   - Watch confidence scores
   - Identify problematic users
   - Adjust positioning if needed

### Untuk User (Mahasiswa/Dosen):

1. **Posisi Ideal**:
   - 📍 Berdiri 1-1.5 meter dari kamera
   - 👁️ Lihat langsung ke kamera
   - 💡 Pastikan wajah terang

2. **Tunggu 3 Detik**:
   - Sistem capture frame setiap 3 detik
   - Diam sejenak untuk hasil terbaik
   - Tunggu notifikasi sukses

3. **Jika Gagal**:
   - Coba lagi dengan posisi lebih dekat
   - Adjust sudut wajah
   - Pastikan lighting cukup

## 📊 Performance Monitoring

### Console Logs yang Perlu Diperhatikan:

```bash
# GOOD - High confidence
[Face Recognition] Confidence: 75.8% ← Excellent!
[Face Recognition] ✅ Recognition SUCCESS

# ACCEPTABLE - Medium confidence  
[Face Recognition] Confidence: 58.5% ← OK, tapi bisa lebih baik
[Face Recognition] ✅ Recognition SUCCESS

# REJECTED - Low confidence
[Face Recognition] Confidence: 52.3% ← Terlalu rendah
[Face Recognition] ⚠️ Low confidence: 52.3% < 55%

# NO MATCH - Distance too high
[Face Recognition] ❌ No match - distance 0.4800 >= threshold 0.45
```

## 🔧 Advanced Tuning

### Jika Ingin Menyesuaikan Threshold:

Edit file `app/face_recognition/simple_face_recognition.py`:

```python
# Line 25: Adjust confidence_threshold
def __init__(self, model_path='models/', confidence_threshold=0.45):
    # Nilai lebih KECIL = lebih strict (fewer false positives)
    # Nilai lebih BESAR = lebih loose (more matches, more false positives)
    
# Line 267: Adjust minimum confidence
if confidence_score < 0.55:  # Adjust value (0.50 - 0.70)
```

**Rekomendasi:**
- **High Security**: threshold=0.40, min_confidence=0.65
- **Balanced**: threshold=0.45, min_confidence=0.55 ← Current
- **Loose**: threshold=0.50, min_confidence=0.50

---

**Last Updated**: November 7, 2025  
**Version**: 1.0  
**Compatibility**: IP Camera Integration v2.0
