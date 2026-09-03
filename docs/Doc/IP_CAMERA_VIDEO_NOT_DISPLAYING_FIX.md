# IP Camera Video Not Displaying Fix - November 20, 2025

## 🐛 Bug Report

**Issue**: IP Camera stream not displaying in video element, but backend detection works correctly.

**Symptoms**:
- ✅ Backend: Camera captures frames, face detection works, attendance updates
- ❌ Frontend: Video stream not visible (black screen or placeholder still showing)
- ✅ Status badge: Shows "Streaming Aktif" (green)
- ❌ Video element: Remains hidden or behind placeholder

## 🔍 Root Cause Analysis

### The Problem

After implementing absolute positioning fix for video overflow issue, the visibility logic became more complex:

**Old Code (Normal Flow)**:
```javascript
// Simple show/hide worked fine
placeholder.style.display = 'none';      // Hide placeholder
ipCameraStream.style.display = 'block';  // Show video
```

**New Code (Absolute Positioning)**:
```css
/* All elements stacked with position: absolute */
#cameraPlaceholder { position: absolute; z-index: 1; }
#ipCameraStream { position: absolute; z-index: 2; }
```

**The Issue**:
- Setting `display: none` on placeholder **not enough** with absolute positioning
- Placeholder may still occupy visual space or block pointer events
- Need to also set `visibility` and `opacity` for complete hiding
- Z-index layering requires higher values to ensure proper stacking

### Why Backend Still Worked

Backend uses **frame buffer** (`latest_frame_presensi`) which continuously captures frames:

```python
# Backend capture thread (always running)
def capture_loop():
    while True:
        ret, frame = capture_camera.read()
        if ret:
            latest_frame_presensi = frame  # Store in buffer
```

**Recognition flow**:
```
1. Frontend calls /capture_ip_frame (even if video not visible)
2. Backend reads from buffer (NOT from video element!)
3. Recognition runs successfully
4. Attendance updates correctly
```

So video display issue **doesn't affect** backend functionality!

## ✅ Solution: Triple-Layer Hiding

### Implementation

**For showing video**:
```javascript
// Hide placeholder COMPLETELY
placeholder.style.display = 'none';      // Remove from layout flow
placeholder.style.visibility = 'hidden'; // Hide from view
placeholder.style.opacity = '0';         // Make transparent

// Show video COMPLETELY
ipCameraStream.style.display = 'block';     // Add to layout flow
ipCameraStream.style.visibility = 'visible'; // Make visible
ipCameraStream.style.opacity = '1';          // Make opaque
```

**For hiding video**:
```javascript
// Hide video COMPLETELY
ipCameraStream.style.display = 'none';
ipCameraStream.style.visibility = 'hidden';
ipCameraStream.style.opacity = '0';

// Show placeholder COMPLETELY
placeholder.style.display = 'flex';
placeholder.style.visibility = 'visible';
placeholder.style.opacity = '1';
```

### CSS Initial State

```html
<div class="card-body position-relative" style="height: 500px; overflow: hidden;">
    <!-- Placeholder: Initially VISIBLE -->
    <div id="cameraPlaceholder" 
         class="position-absolute top-0 start-0 w-100 h-100" 
         style="z-index: 10; background-color: #343a40;">
        <!-- Content -->
    </div>
    
    <!-- IP Camera: Initially HIDDEN -->
    <img id="ipCameraStream" 
         class="position-absolute top-0 start-0" 
         style="display: none; 
                visibility: hidden; 
                opacity: 0; 
                width: 100%; 
                height: 100%; 
                object-fit: contain; 
                z-index: 20;">
    
    <!-- Webcam: Initially HIDDEN -->
    <video id="webcamVideoStream" 
           class="position-absolute top-0 start-0" 
           style="display: none; 
                  visibility: hidden; 
                  opacity: 0; 
                  width: 100%; 
                  height: 100%; 
                  object-fit: contain; 
                  z-index: 20;">
    </video>
</div>
```

**Key Changes**:
1. ✅ Placeholder: `z-index: 10` (lower layer)
2. ✅ Video elements: `z-index: 20` (upper layer)
3. ✅ Placeholder: Background color `#343a40` (dark gray)
4. ✅ Initial states explicitly set in HTML
5. ✅ Triple-layer hiding (display + visibility + opacity)

## 🎯 Why Triple-Layer Hiding?

### Display vs Visibility vs Opacity

| Property | Effect | Layout Impact | Pointer Events | Animation |
|----------|--------|---------------|----------------|-----------|
| `display: none` | Removed from flow | Yes (space removed) | Not clickable | Instant (no transition) |
| `visibility: hidden` | Invisible but space kept | No (space kept) | Not clickable | Instant (no transition) |
| `opacity: 0` | Transparent | No (space kept) | Still clickable! | Can transition |

**Why use all three?**

1. **`display: none`**: 
   - Completely remove from layout flow
   - Browser doesn't render it at all (performance)
   
2. **`visibility: hidden`**: 
   - Backup for absolute positioned elements
   - Ensures screen readers ignore it
   
3. **`opacity: 0`**: 
   - Extra insurance for visual hiding
   - Can transition smoothly if needed later

**Combined effect**: Element is **completely** hidden with no possibility of appearing.

## 🔄 Complete Flow

### Start IP Camera

```javascript
function startIPCameraStream() {
    const ipCameraStream = document.getElementById('ipCameraStream');
    const placeholder = document.getElementById('cameraPlaceholder');
    
    console.log('[IP Camera] Starting stream...');
    
    // STEP 1: Hide placeholder completely
    placeholder.style.display = 'none';
    placeholder.style.visibility = 'hidden';
    placeholder.style.opacity = '0';
    
    // STEP 2: Show video completely
    ipCameraStream.style.display = 'block';
    ipCameraStream.style.visibility = 'visible';
    ipCameraStream.style.opacity = '1';
    
    // STEP 3: Set video source (MJPEG stream endpoint)
    ipCameraStream.src = '/presensi_face/ip_stream?t=' + new Date().getTime();
    console.log('[IP Camera] Stream URL set:', ipCameraStream.src);
    
    // STEP 4: Update UI controls
    streamActive = true;
    startBtn.style.display = 'none';
    stopBtn.style.display = 'inline-block';
    statusBadge.innerHTML = 'Streaming Aktif';
    statusBadge.className = 'badge bg-success';
    
    // STEP 5: Start auto-detection
    startAutomaticRecognition();
}
```

### Stop IP Camera

```javascript
function stopIPCameraStream() {
    const ipCameraStream = document.getElementById('ipCameraStream');
    const placeholder = document.getElementById('cameraPlaceholder');
    
    console.log('[IP Camera] Stopping stream...');
    
    // STEP 1: Clear video source
    ipCameraStream.src = '';
    
    // STEP 2: Hide video completely
    ipCameraStream.style.display = 'none';
    ipCameraStream.style.visibility = 'hidden';
    ipCameraStream.style.opacity = '0';
    
    // STEP 3: Show placeholder completely
    placeholder.style.display = 'flex';
    placeholder.style.visibility = 'visible';
    placeholder.style.opacity = '1';
    
    // STEP 4: Update UI controls
    streamActive = false;
    startBtn.style.display = 'inline-block';
    stopBtn.style.display = 'none';
    statusBadge.innerHTML = 'Belum Aktif';
    statusBadge.className = 'badge bg-secondary';
    
    // STEP 5: Stop auto-detection
    if (recognitionInterval) {
        clearInterval(recognitionInterval);
        recognitionInterval = null;
    }
}
```

## 🧪 Testing

### Visual Verification

**Test 1: IP Camera Display**
```
1. Select "IP Camera (CCTV)" radio button
2. Click "Mulai Kamera"
3. Expected:
   ✅ Placeholder disappears immediately
   ✅ Video stream appears within 1-2 seconds
   ✅ Video fills entire card area (500px height)
   ✅ No black bars or overflow
   ✅ Status badge: "Streaming Aktif" (green)
```

**Test 2: Webcam Display**
```
1. Select "Webcam" radio button
2. Click "Mulai Kamera"
3. Allow browser permission
4. Expected:
   ✅ Placeholder disappears
   ✅ Webcam video appears
   ✅ Video is mirrored (front camera)
   ✅ Status badge: "Webcam Aktif" (green)
```

**Test 3: Switching Cameras**
```
1. Start IP Camera → Video shows ✅
2. Stop IP Camera → Placeholder shows ✅
3. Switch to Webcam → Webcam video shows ✅
4. Stop Webcam → Placeholder shows ✅
5. Switch to IP Camera → IP video shows ✅
```

### Console Debugging

**Check element visibility**:
```javascript
// Run in browser console
const ip = document.getElementById('ipCameraStream');
const placeholder = document.getElementById('cameraPlaceholder');

console.log('IP Camera:', {
    display: ip.style.display,
    visibility: ip.style.visibility,
    opacity: ip.style.opacity,
    zIndex: window.getComputedStyle(ip).zIndex,
    src: ip.src
});

console.log('Placeholder:', {
    display: placeholder.style.display,
    visibility: placeholder.style.visibility,
    opacity: placeholder.style.opacity,
    zIndex: window.getComputedStyle(placeholder).zIndex
});
```

**Expected when IP Camera active**:
```
IP Camera: {
    display: "block",
    visibility: "visible",
    opacity: "1",
    zIndex: "20",
    src: "http://127.0.0.1:5000/presensi_face/ip_stream?t=1234567890"
}

Placeholder: {
    display: "none",
    visibility: "hidden",
    opacity: "0",
    zIndex: "10"
}
```

## 📊 Before vs After

### Before Fix

| Aspect | State |
|--------|-------|
| IP Camera stream loads | ✅ Yes (backend) |
| Video element visible | ❌ No |
| Placeholder hidden | ⚠️ Partial (display:none only) |
| Recognition works | ✅ Yes (uses buffer) |
| Attendance updates | ✅ Yes |
| User experience | ❌ Bad (can't see video) |

### After Fix

| Aspect | State |
|--------|-------|
| IP Camera stream loads | ✅ Yes |
| Video element visible | ✅ Yes |
| Placeholder hidden | ✅ Complete (triple-layer) |
| Recognition works | ✅ Yes |
| Attendance updates | ✅ Yes |
| User experience | ✅ Good (see live video) |

## 🔧 Troubleshooting

### Video Still Not Showing

**Check 1: Element exists**
```javascript
document.getElementById('ipCameraStream')  // Should not be null
```

**Check 2: Stream endpoint working**
```
Visit: http://127.0.0.1:5000/presensi_face/ip_stream
Expected: Video stream in browser
```

**Check 3: CSS computed values**
```javascript
const ip = document.getElementById('ipCameraStream');
const computed = window.getComputedStyle(ip);
console.log('Computed:', {
    display: computed.display,        // Should be "block"
    visibility: computed.visibility,  // Should be "visible"
    opacity: computed.opacity,        // Should be "1"
    zIndex: computed.zIndex          // Should be "20"
});
```

**Check 4: Placeholder blocking**
```javascript
const placeholder = document.getElementById('cameraPlaceholder');
const rect = placeholder.getBoundingClientRect();
console.log('Placeholder rect:', rect);  // Should be outside viewport if hidden
```

### Black Screen But Controls Work

**Cause**: RTSP camera not accessible
**Solution**: Check `.env` file:
```env
IP_CAMERA_URL=rtsp://admin:password@192.168.0.100:554/stream
```

Test with VLC: `vlc rtsp://admin:password@192.168.0.100:554/stream`

## 📝 Summary

### Root Cause
- Absolute positioning requires triple-layer hiding (display + visibility + opacity)
- Simple `display: none` insufficient with z-index stacking

### Fix Applied
1. ✅ Added `visibility: hidden` when hiding elements
2. ✅ Added `opacity: 0` when hiding elements
3. ✅ Added explicit `visibility: visible` when showing elements
4. ✅ Added explicit `opacity: 1` when showing elements
5. ✅ Increased z-index: placeholder (10) → video (20)
6. ✅ Added background color to placeholder
7. ✅ Added console logging for debugging

### Files Modified
- `app/templates/ambil_presensi.html`:
  - Updated `startIPCameraStream()` function
  - Updated `stopIPCameraStream()` function
  - Updated `startWebcam()` function
  - Updated `stopWebcam()` function
  - Updated HTML initial state with triple-layer hiding

### Result
- ✅ IP Camera video now displays correctly
- ✅ Webcam video displays correctly
- ✅ Smooth switching between cameras
- ✅ Placeholder shows/hides correctly
- ✅ No visual glitches or overflow

**Status**: FIXED ✅
