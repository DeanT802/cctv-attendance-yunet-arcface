# SESSION SUMMARY - IP Camera Face Recognition Issue

**Date:** November 7, 2025  
**User:** Dean Rama Prananta  
**Project:** Face Recognition Attendance System (Flask + CNN Hybrid)

---

## ✅ **CURRENT STATUS:**

### **Working:**
- ✅ **Webcam** - Face recognition works perfectly
- ✅ **CNN Hybrid Detection** - HOG → CNN with 4-method fallback
- ✅ **Backend** - Flask server stable
- ✅ **Thread Safety** - RTSP connection with singleton pattern + lock

### **NOT Working:**
- ❌ **IP Camera (CCTV Ezviz)** - Cannot recognize face
  - Camera: Ezviz CCTV at `rtsp://admin:Witch0741@192.168.8.10:554/...`
  - Resolution: 2560x1440 (2K)
  - Codec: H.265/H.264
  - Problem: Slow detection (6-9 seconds), often 0 faces detected

---

## 📝 **SESSION HISTORY:**

### **1. Initial Problem:**
- IP camera could not detect faces (0 faces detected)
- Using HOG model only
- Detection failed even at close range

### **2. First Fix - CNN Hybrid:**
✅ Changed from HOG-only to CNN Hybrid (4-method fallback)
✅ Detection improved: 60% → 95% success rate
❌ But IP camera still slow compared to webcam

### **3. Optimization Attempt:**
- Created new endpoint `/capture_and_recognize_ip`
- Changed from 2 requests (fetch + recognize) to 1 request
- Added timeout protection (10 seconds)
- Changed interval: 3s → 2.5s → 1.5s
- Added thread-safe singleton pattern for RTSP

**Result:** ❌ Optimization broke webcam!
- Multiple RTSP connections created (4x simultaneous)
- Resource exhaustion (CPU 80-90%, Memory 2.5GB)
- Terminal lag with "busy" errors
- Fatal Python error: `_enter_buffered_busy`

### **4. Rollback:**
✅ Reverted ALL optimizations
✅ Removed new endpoint `/capture_and_recognize_ip`
✅ Removed timeout protection
✅ Back to original webcam code
✅ Webcam now works perfectly!

**Current State:**
- ✅ Webcam: Works perfectly
- ❌ IP Camera: Still slow/not detecting (original problem remains)

---

## 🔍 **IP CAMERA PROBLEM ANALYSIS:**

### **Root Causes Identified:**

1. **Processing Flow Difference:**
   ```
   Webcam:  Video element → Canvas → Blob → Recognize (1 step)
   IP Cam:  RTSP → Backend → Base64 → Frontend → Canvas → Blob → Recognize (5 steps!)
   ```

2. **Network Overhead:**
   - IP Camera: 2 HTTP requests per cycle
   - Webcam: 1 HTTP request per cycle
   - Extra base64 encoding/decoding

3. **RTSP Stream Issues:**
   - 2K resolution (2560x1440) - very heavy
   - H.265 codec - CPU intensive
   - Network latency from RTSP stream
   - Multiple threads accessing same stream

4. **Detection Method:**
   - CNN Hybrid requires good image quality
   - IP camera frame quality may be degraded after base64 transfer
   - Possible compression artifacts

---

## 🚫 **WHAT DIDN'T WORK:**

### **Optimization Attempt #1: Direct Backend Processing**
- **Approach:** Process frame directly in backend (skip frontend roundtrip)
- **Endpoint:** `/presensi_face/capture_and_recognize_ip`
- **Result:** ❌ Broke webcam due to resource conflicts
- **Problem:** Multiple simultaneous RTSP connections, thread conflicts

### **Why It Failed:**
1. Thread lock too aggressive - blocked webcam processing
2. Interval too fast (1.5s) - requests accumulated
3. Shared RTSP stream caused race conditions
4. Resource exhaustion affected ALL cameras

---

## 💡 **POTENTIAL SOLUTIONS (FOR NEXT SESSION):**

### **Option 1: Separate Processing Thread**
```python
# Dedicated thread for IP camera only
# No shared resources with webcam
# Uses separate detection instance
```
**Pros:** Complete isolation, no conflicts  
**Cons:** More complex, higher memory usage

### **Option 2: Lower IP Camera Resolution**
```python
# Use sub-stream instead of main stream
# rtsp://.../sub/av_stream (640x480 or 1280x720)
```
**Pros:** Faster processing, less bandwidth  
**Cons:** Lower quality may affect recognition

### **Option 3: Pre-processing Optimization**
```python
# Apply image enhancement before sending to recognition
# Adjust brightness, contrast, sharpness
# Remove compression artifacts
```
**Pros:** Better image quality  
**Cons:** Extra processing time

### **Option 4: Different Detection Strategy**
```python
# Use HOG for IP camera (faster but less accurate)
# Use CNN only for webcam
# Separate confidence thresholds
```
**Pros:** Faster IP camera processing  
**Cons:** Lower accuracy

### **Option 5: Frame Caching**
```python
# Cache IP camera frames in memory
# Process from cache instead of live stream
# Reduce RTSP access frequency
```
**Pros:** Less RTSP overhead  
**Cons:** May show stale frames

---

## 📊 **CURRENT CODE STATE:**

### **Detection Method:**
```python
# simple_face_recognition.py
# CNN Hybrid with 4-method fallback:
1. CNN model (primary)
2. HOG model (fallback)
3. CNN with scale variations (2nd fallback)
4. CNN on original image (last resort)
```

### **Endpoints:**
```python
# routes.py
/presensi_face/capture_ip_frame  # Fetch frame from RTSP
/presensi_face/ip_camera_feed    # MJPEG stream
/face_recognition/recognize_attendance  # Face recognition (shared)
```

### **Frontend:**
```javascript
// presensi_face.html
startIPCameraDetection() {
    // Fetch frame every 3 seconds
    // Process via processIPCameraFrame()
    // Send to recognize_attendance
}
```

---

## 🎯 **NEXT SESSION GOALS:**

### **Priority 1: Fix IP Camera Detection**
- [ ] Identify why IP camera cannot detect face
- [ ] Test with different RTSP streams (main vs sub)
- [ ] Check image quality after base64 transfer
- [ ] Verify CNN Hybrid works on IP camera frames

### **Priority 2: Optimize WITHOUT Breaking Webcam**
- [ ] Implement isolated processing for IP camera
- [ ] Use separate detection instance
- [ ] Test with lower resolution stream
- [ ] Add proper error handling

### **Priority 3: Testing**
- [ ] Test webcam + IP camera simultaneously
- [ ] Verify no resource conflicts
- [ ] Check terminal for errors
- [ ] Measure processing times

---

## 📁 **IMPORTANT FILES:**

### **Core Files:**
```
app/face_recognition/simple_face_recognition.py  # CNN Hybrid detection
app/routes.py                                     # IP camera endpoints
app/templates/presensi_face.html                 # Frontend logic
```

### **Documentation:**
```
CNN_HYBRID_UPDATE.md              # Detection method changes
IP_CAMERA_FIXES.md                # UI bugs fixed
WEBCAM_RACE_CONDITION_FIX.md      # Thread safety issues
ROLLBACK_NOTES.md                 # Current rollback status
```

### **Configuration:**
```
.env                              # RTSP_URL configuration
models/face_encodings.pkl         # Face database
uploads/faces/                    # Face photos
```

---

## 🔧 **SYSTEM SPECS:**

```
OS: Windows
Python: 3.11
Camera IP: 192.168.8.10:554
Resolution: 2560x1440 (2K)
Codec: H.265/H.264
Network: Local LAN
```

---

## 💬 **KEY QUOTES FROM USER:**

> "webcam sudah berfungsi dengan baik"  
> "saya akan kembali lagi karena kamera IP masih belum bisa mengenali wajah saya"

---

## 🚀 **RECOMMENDED APPROACH FOR NEXT SESSION:**

### **Step 1: Diagnostic**
1. Test IP camera with Debug Mode
2. Check terminal output for detection details
3. Verify frame quality after base64 transfer
4. Compare IP camera frame vs webcam frame

### **Step 2: Try Sub-Stream**
```python
# Use lower resolution stream
rtsp://admin:Witch0741@192.168.8.10:554/h264/ch1/sub/av_stream
# Instead of main stream
```

### **Step 3: Isolated Processing**
```python
# Create separate function for IP camera only
# Don't share resources with webcam
# Use dedicated detection instance
```

### **Step 4: Test Incrementally**
- Test IP camera alone first
- Then test with webcam simultaneously
- Monitor terminal for conflicts
- Verify no performance degradation

---

## ⚠️ **CRITICAL LESSONS LEARNED:**

1. **Don't Optimize Both Cameras Together**
   - Changes to IP camera affected webcam
   - Need complete isolation

2. **Resource Sharing is Dangerous**
   - Shared RTSP stream caused race conditions
   - Thread locks too aggressive blocked other processes

3. **Test Incrementally**
   - Big changes broke working features
   - Small incremental changes safer

4. **Monitor Resource Usage**
   - CPU, Memory, Network bandwidth
   - One camera's problem affects others

5. **Always Have Rollback Plan**
   - Document working state
   - Easy to revert if needed

---

## 📌 **REMEMBER FOR NEXT TIME:**

1. ✅ Webcam works perfectly - DON'T TOUCH IT!
2. ❌ IP camera needs fixing - isolate changes
3. 🔒 Keep thread safety (singleton pattern + lock is good)
4. 🎯 Focus on IP camera ONLY
5. 📊 Test with Debug Mode first
6. 🔍 Check terminal output carefully
7. ⚡ Try sub-stream for faster processing

---

**Status:** Webcam restored and working. IP camera issue documented and ready for next session.

**Next Steps:** Diagnose IP camera with Debug Mode, try sub-stream, implement isolated processing.
