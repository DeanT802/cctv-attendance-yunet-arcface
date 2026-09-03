# 🔧 Video Visibility Diagnostic Guide

## Problem: Video Tidak Muncul Meskipun Backend Bekerja

Jika Anda mengalami issue di mana:
- ✅ Backend merespon dengan baik (detection works)
- ✅ Console log menunjukkan "Streaming Aktif"
- ✅ Status badge berubah hijau
- ❌ Video tetap tidak terlihat (layar hitam atau placeholder masih muncul)

**Ikuti langkah-langkah di bawah ini!**

---

## 🚀 Step 1: Hard Refresh Browser (WAJIB!)

Masalah paling umum adalah **browser cache** yang menyimpan CSS/JS lama.

### Chrome / Edge:
```
Tekan: Ctrl + Shift + Delete
Pilih: "Cached images and files"
Klik: "Clear data"

ATAU lebih cepat:
Tekan: Ctrl + F5 (hard refresh)
```

### Firefox:
```
Tekan: Ctrl + Shift + Delete
Pilih: "Cache"
Klik: "Clear Now"

ATAU lebih cepat:
Tekan: Ctrl + Shift + R (hard refresh)
```

### Safari (Mac):
```
Command + Option + E (Empty Cache)
Command + R (Reload)
```

---

## 🔍 Step 2: Jalankan Diagnostic Tool

### Cara Pakai:

1. **Buka Browser Console**:
   - Tekan `F12` (Windows/Linux)
   - Atau `Cmd + Option + I` (Mac)
   - Atau klik kanan → "Inspect" → Tab "Console"

2. **Copy Script**:
   - Buka file: `diagnose_video_visibility.js`
   - Copy SELURUH isi file (Ctrl + A, Ctrl + C)

3. **Paste ke Console**:
   - Paste script ke console browser (Ctrl + V)
   - Tekan `Enter`

4. **Baca Output**:
   - Tool akan menampilkan diagnostic lengkap
   - Cari tanda ❌ (error) dan ⚠️ (warning)
   - Baca recommendations di bagian akhir

### Contoh Output Normal (Working):

```
==========================================================
VIDEO ELEMENT DIAGNOSTIC TOOL
==========================================================

📋 ELEMENT EXISTENCE CHECK
----------------------------------------------------------
IP Camera element: ✅ EXISTS
Webcam video element: ✅ EXISTS
Placeholder element: ✅ EXISTS
Container element: ✅ EXISTS

📹 IP CAMERA DIAGNOSTICS
----------------------------------------------------------
Inline Styles:
  display: block
  visibility: visible
  opacity: 1
  z-index: 100

Computed Styles (Final):
  display: block ✅
  visibility: visible ✅
  opacity: 1 ✅
  z-index: 100
  position: absolute

Dimensions & Position:
  width: 640px ✅
  height: 480px ✅
  top: 150px
  left: 200px

Image Source:
  src: http://192.168.8.4:5000/presensi_face/ip_stream?t=1732435200000
  complete: false
  naturalWidth: 0
  naturalHeight: 0

🔢 Z-INDEX STACKING ORDER
----------------------------------------------------------
Placeholder z-index: 1
IP Camera z-index: 100
Webcam Video z-index: 100
✅ Z-index stacking correct (video > placeholder)

🌐 BACKEND STREAM CHECK
----------------------------------------------------------
Testing IP Camera stream endpoint...
✅ Backend stream endpoint accessible
   Status: 200
   Content-Type: multipart/x-mixed-replace; boundary=frame

📊 DIAGNOSTIC SUMMARY
----------------------------------------------------------
✅ No critical issues found!
```

### Contoh Output Bermasalah:

```
📹 IP CAMERA DIAGNOSTICS
----------------------------------------------------------
Computed Styles (Final):
  display: none ❌        <-- MASALAH!
  visibility: hidden ❌   <-- MASALAH!
  opacity: 0 ❌           <-- MASALAH!

Dimensions & Position:
  width: 0px ❌ (COLLAPSED!)    <-- MASALAH!
  height: 0px ❌ (COLLAPSED!)   <-- MASALAH!

❌ ISSUES FOUND:
  1. IP Camera display is "none" - should be "block" when active
  2. IP Camera has zero dimensions - element is collapsed!
```

---

## 🛠️ Step 3: Manual Debugging (Jika Masih Gagal)

### Test 1: Cek Element di DevTools

1. **Buka DevTools** (F12)
2. **Klik tab "Elements"**
3. **Cari element**: `<img id="ipCameraStream">`
4. **Lihat Computed styles** (tab "Computed" di kanan)

**Harus terlihat**:
- `display: block` ✅
- `visibility: visible` ✅
- `opacity: 1` ✅
- `z-index: 100` ✅
- `width: XXXpx` (bukan 0!) ✅
- `height: XXXpx` (bukan 0!) ✅

### Test 2: Force Show Manual di Console

Paste kode ini di console:

```javascript
// Force show IP Camera
const ip = document.getElementById('ipCameraStream');
ip.style.setProperty('display', 'block', 'important');
ip.style.setProperty('visibility', 'visible', 'important');
ip.style.setProperty('opacity', '1', 'important');
ip.style.setProperty('z-index', '9999', 'important');
ip.style.setProperty('position', 'absolute', 'important');
ip.style.setProperty('top', '0', 'important');
ip.style.setProperty('left', '0', 'important');
ip.style.setProperty('width', '100%', 'important');
ip.style.setProperty('height', '100%', 'important');
ip.classList.remove('d-none', 'invisible');

console.log('Force show applied!');
console.log('Computed display:', window.getComputedStyle(ip).display);
console.log('Dimensions:', ip.getBoundingClientRect());
```

**Jika masih tidak muncul**: Masalah bukan di CSS, kemungkinan:
- Image src tidak loading (cek Network tab)
- RTSP backend error (cek terminal Python)
- Parent container collapsed

### Test 3: Cek Image Loading

```javascript
const ip = document.getElementById('ipCameraStream');
console.log('Image src:', ip.src);
console.log('Image complete:', ip.complete);
console.log('Image naturalWidth:', ip.naturalWidth);

// Listen for errors
ip.onerror = () => console.error('❌ Image failed to load!');
ip.onload = () => console.log('✅ Image loaded!');
```

### Test 4: Test Backend Stream Endpoint

**Buka di browser tab baru**:
```
http://192.168.8.4:5000/presensi_face/ip_stream
```

**Expected**: Video stream muncul langsung (MJPEG continuous stream)

**Jika error**:
- `Connection refused`: Backend tidak running
- `404 Not Found`: Route salah
- `500 Internal Server Error`: RTSP camera error (cek .env file)

---

## 🔧 Step 4: Common Fixes

### Fix 1: Clear All Cache

**Chrome DevTools**:
1. Klik kanan pada Refresh button (sambil DevTools terbuka)
2. Pilih "Empty Cache and Hard Reload"

**Manual**:
1. Settings → Privacy → Clear browsing data
2. Pilih "Cached images and files" + "Cookies"
3. Time range: "All time"
4. Clear data

### Fix 2: Disable Browser Extensions

Beberapa extension bisa block video:
- AdBlock / uBlock Origin
- Privacy Badger
- NoScript

**Test**: Buka dalam **Incognito/Private mode** (Ctrl + Shift + N)

### Fix 3: Check RTSP Camera Connection

**Edit `.env` file**:
```env
IP_CAMERA_URL=rtsp://admin:password@192.168.0.100:554/stream
```

**Test dengan VLC**:
```
Media → Open Network Stream
Network URL: rtsp://admin:password@192.168.0.100:554/stream
Play
```

**Jika VLC tidak bisa konek**: Masalah di kamera, bukan di code!

### Fix 4: Check Flask Logs

Buka terminal yang running `python run.py`, cari error:
```
ERROR: RTSP stream connection failed
ERROR: Could not connect to camera
WARNING: Frame capture timeout
```

**Restart Flask**:
```bash
# Stop: Ctrl + C
# Start:
python run.py
```

---

## 📊 Checklist Troubleshooting

Ikuti urutan ini:

- [ ] **Hard refresh browser** (Ctrl + F5)
- [ ] **Clear cache completely**
- [ ] **Test in Incognito mode**
- [ ] **Run diagnostic tool** (`diagnose_video_visibility.js`)
- [ ] **Check console for errors** (F12 → Console tab)
- [ ] **Inspect element** (F12 → Elements → cari `ipCameraStream`)
- [ ] **Check computed styles** (display, visibility, opacity, z-index)
- [ ] **Check dimensions** (width/height harus > 0)
- [ ] **Test backend endpoint** (http://IP:5000/presensi_face/ip_stream)
- [ ] **Check RTSP camera** (test dengan VLC)
- [ ] **Check Flask logs** (terminal output)
- [ ] **Restart Flask** jika perlu

---

## 🆘 Jika Masih Gagal

### Scenario 1: Display = block, tapi tetap tidak terlihat

**Possible causes**:
1. Element di luar viewport (position wrong)
2. Transparent atau blend mode issue
3. Parent overflow hidden

**Fix**:
```javascript
const ip = document.getElementById('ipCameraStream');
ip.style.setProperty('transform', 'none', 'important');
ip.style.setProperty('background-color', 'red', 'important'); // Test visibility
```

### Scenario 2: Dimensions = 0x0

**Cause**: Parent container collapsed atau CSS conflict

**Fix**:
```javascript
const container = document.querySelector('.card-body.position-relative');
console.log('Container height:', container.offsetHeight); // Should be 500px

// Force container size
container.style.height = '500px';
container.style.minHeight = '500px';
```

### Scenario 3: Backend stream endpoint error

**Check .env**:
```bash
cat .env | grep IP_CAMERA
```

**Test RTSP**:
```bash
# With ffplay (jika terinstall)
ffplay -rtsp_transport tcp "rtsp://admin:password@192.168.0.100:554/stream"
```

---

## 📝 Summary

**Most common issues** (90% of cases):
1. ❌ **Browser cache** → Fix: Ctrl + F5
2. ❌ **CSS not applied** → Fix: Use `!important` (already done!)
3. ❌ **Element hidden by class** → Fix: Remove `.d-none`, `.invisible`
4. ❌ **Z-index too low** → Fix: Set to 100+ (already done!)

**Backend issues** (10% of cases):
5. ❌ **RTSP camera offline** → Fix: Check camera IP/credentials
6. ❌ **Flask not running** → Fix: Restart `python run.py`

**Hardware/Network issues** (rare):
7. ❌ **Firewall blocking RTSP** → Fix: Allow port 554
8. ❌ **Camera firmware issue** → Fix: Reboot camera

---

## ✅ Expected Result After Fix

Setelah semua fix diterapkan:

1. ✅ **Hard refresh** (Ctrl + F5)
2. ✅ **Pilih "IP Camera (CCTV)"**
3. ✅ **Klik "Mulai Kamera"**
4. ✅ **Video muncul dalam 1-2 detik**
5. ✅ **Placeholder hilang sempurna**
6. ✅ **Face detection works**
7. ✅ **Attendance updates real-time**

**Console output**:
```
[IP Camera] Starting stream...
[IP Camera] Stream URL set: /presensi_face/ip_stream?t=...
[IP Camera] Element computed style: block
[IP Camera] Element computed z-index: 100
[IP Camera] Element computed visibility: visible
[IP Camera] Element computed opacity: 1
```

**Visual result**: Video stream penuh layar di dalam card! 🎉

---

## 📞 Need More Help?

Jika masih belum solve:

1. **Copy FULL diagnostic output** dari `diagnose_video_visibility.js`
2. **Screenshot** area video (yang tidak muncul)
3. **Copy console errors** (F12 → Console → screenshot semua error merah)
4. **Copy Flask terminal output** (20 baris terakhir)
5. **Share semua info di atas** untuk debug lebih lanjut

Good luck! 🚀
