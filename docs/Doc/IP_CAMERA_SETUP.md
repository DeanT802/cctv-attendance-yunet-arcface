# IP Camera (CCTV) Integration Guide

## Overview
Sistem face recognition sekarang mendukung dua sumber kamera:
1. **Webcam** - Kamera bawaan laptop/komputer
2. **IP Camera (CCTV)** - Kamera CCTV melalui RTSP stream (Ezviz, Hikvision, dll)

## Konfigurasi IP Camera

### 1. Setup RTSP URL di File .env

Edit file `.env` dan tambahkan/update konfigurasi RTSP URL:

```env
RTSP_URL=rtsp://admin@192.168.8.10:554/h264/ch1/main/av_stream
```

**Format RTSP URL:**
```
rtsp://[username]:[password]@[ip_address]:[port]/[stream_path]
```

**Contoh untuk berbagai brand CCTV:**

- **Ezviz:**
  ```
  rtsp://admin@192.168.8.10:554/h264/ch1/main/av_stream
  ```

- **Hikvision:**
  ```
  rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101
  ```

- **Dahua:**
  ```
  rtsp://admin:password@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0
  ```

- **TP-Link:**
  ```
  rtsp://admin:password@192.168.1.100:554/stream1
  ```

### 2. Verifikasi Koneksi CCTV

Sebelum menggunakan di aplikasi, test koneksi CCTV dengan VLC Media Player:

1. Buka **VLC Media Player**
2. Klik **Media** → **Open Network Stream**
3. Masukkan RTSP URL Anda
4. Klik **Play**

Jika video muncul, berarti RTSP URL sudah benar.

### 3. Pengaturan Jaringan

Pastikan:
- ✅ Komputer dan CCTV berada dalam jaringan yang sama
- ✅ Port RTSP (biasanya 554) tidak diblokir firewall
- ✅ RTSP stream diaktifkan di pengaturan CCTV
- ✅ Username dan password CCTV benar

## Cara Menggunakan

### Di Menu Presensi Face Recognition

1. **Buka halaman Presensi Face**
   ```
   http://localhost:5000/presensi_face
   ```

2. **Pilih Sumber Kamera**
   - Klik tombol **"Webcam"** untuk menggunakan kamera laptop
   - Klik tombol **"IP Camera (CCTV)"** untuk menggunakan CCTV

3. **Mulai Real-Time Recognition**
   - Klik tombol **"Mulai Real-Time Recognition"**
   - Sistem akan otomatis terhubung ke sumber kamera yang dipilih

4. **Lakukan Presensi**
   - Hadapkan wajah ke kamera
   - Sistem akan otomatis mendeteksi dan mencatat presensi Anda
   - Tidak perlu menekan tombol capture manual

## Fitur yang Tetap Berfungsi

Semua fitur face recognition tetap berfungsi normal dengan IP Camera:

✅ **Face Detection** - Deteksi wajah real-time
✅ **Face Recognition** - Pengenalan wajah mahasiswa
✅ **Anti-Spoofing** - Deteksi liveness (gerakan alami, kedipan)
✅ **Confidence Score** - Tingkat keyakinan pengenalan
✅ **Real-time Preview** - Live feed dari kamera
✅ **Multiple Students** - Support banyak mahasiswa terdaftar

## Troubleshooting

### IP Camera tidak terdeteksi

**Problem:** Tombol "IP Camera (CCTV)" disabled

**Solusi:**
1. Cek apakah RTSP_URL sudah dikonfigurasi di file `.env`
2. Cek koneksi jaringan ke CCTV
3. Test RTSP URL di VLC Player
4. Restart aplikasi setelah mengubah `.env`

### Video tidak muncul/blank

**Problem:** Kamera terhubung tapi video tidak tampil

**Solusi:**
1. Cek apakah stream path sudah benar
2. Gunakan stream main (bukan sub stream)
3. Cek bandwidth jaringan
4. Reduce resolusi stream di pengaturan CCTV

### Koneksi lambat/lag

**Problem:** Video terputus-putus atau delay tinggi

**Solusi:**
1. Gunakan sub stream dengan resolusi lebih rendah
2. Cek bandwidth jaringan
3. Kurangi jumlah device yang akses CCTV bersamaan
4. Pastikan jaringan stabil (gunakan kabel LAN jika WiFi tidak stabil)

### Error "Cannot connect to IP camera"

**Solusi:**
1. Pastikan CCTV dan komputer dalam satu network
2. Ping IP address CCTV: `ping 192.168.8.10`
3. Cek firewall tidak memblokir port 554
4. Pastikan RTSP service aktif di CCTV
5. Coba restart CCTV

## Keunggulan IP Camera Mode

### 📹 **Jangkauan Lebih Luas**
- Tidak terbatas pada jarak webcam
- Bisa dipasang di posisi strategis (pintu masuk, ruang kelas)
- Satu CCTV untuk monitoring area lebih luas

### 🎯 **Kualitas Lebih Baik**
- Resolusi lebih tinggi (Full HD/4K)
- Low light performance lebih baik
- Optical zoom untuk detail lebih jelas

### 🔒 **Keamanan Lebih Tinggi**
- CCTV dilindungi dari gangguan fisik
- Recording tersimpan di DVR/NVR
- Backup footage untuk audit

### ⚡ **Efisiensi**
- Tidak perlu komputer di setiap lokasi presensi
- CCTV yang sudah ada bisa dimanfaatkan
- Centralized monitoring dari server

## Spesifikasi Teknis

### Requirements
- RTSP-compatible IP Camera
- Network connectivity (LAN/WiFi)
- Port 554 (RTSP default)
- H.264/H.265 video codec support

### Tested Cameras
- ✅ Ezviz C6N
- ✅ Hikvision DS-2CD series
- ✅ Dahua IPC-HFW series
- ✅ TP-Link Tapo C200

### Performance
- **Latency:** < 2 seconds
- **Frame Rate:** 15-30 FPS
- **Resolution:** Support up to 1080p
- **Bandwidth:** 2-8 Mbps (depends on quality)

## API Endpoints Baru

Untuk developer yang ingin integrasi:

### Check IP Camera Availability
```http
GET /presensi_face/check_ip_camera
```

Response:
```json
{
  "available": true,
  "message": "IP Camera connected successfully",
  "url": "192.168.8.10:554"
}
```

### IP Camera Feed Stream
```http
GET /presensi_face/ip_camera_feed
```

Returns: MJPEG stream (multipart/x-mixed-replace)

### Capture Frame from IP Camera
```http
POST /presensi_face/capture_ip_frame
```

Response:
```json
{
  "success": true,
  "frame": "base64_encoded_image_data"
}
```

## Security Notes

⚠️ **Penting untuk Keamanan:**

1. **Ganti default password** CCTV Anda
2. **Jangan expose** RTSP URL ke publik
3. **Gunakan VLAN** terpisah untuk CCTV jika memungkinkan
4. **Enable encryption** jika CCTV support RTSPS
5. **Update firmware** CCTV secara berkala

## Support

Jika mengalami masalah:
1. Cek log aplikasi di folder `logs/`
2. Cek console browser untuk error JavaScript
3. Verifikasi konfigurasi di file `.env`
4. Contact IT support dengan screenshot error

---

**Created:** November 2025
**Version:** 1.0
**Compatibility:** Face Recognition System v2.0+
