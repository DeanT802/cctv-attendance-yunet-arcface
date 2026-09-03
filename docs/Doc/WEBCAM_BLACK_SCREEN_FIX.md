# Webcam Black Screen Fix - November 20, 2025

## 🐛 Bug Report

**Issue**: Webcam status shows "Webcam Aktif" (green badge) but video stream displays black screen with small thumbnail icon in bottom-left corner.

**Root Cause**: Using `<img>` tag for both IP Camera and Webcam streams. MediaStream from `getUserMedia()` requires `<video>` element, not `<img>`.

## 🔍 Analysis

### Original Implementation (WRONG)

```html
<!-- Single img element for both sources -->
<img id="videoStream" 
     src="" 
     class="img-fluid" 
     style="display: none; max-height: 600px; width: 100%;"
     alt="IP Camera Stream">
```

```javascript
// Webcam: Setting srcObject on img element (DOESN'T WORK!)
const videoStream = document.getElementById('videoStream');
videoStream.srcObject = stream;  // ❌ img doesn't support srcObject
```

### Why It Failed

1. **`<img>` vs `<video>`**
   - `<img>` only accepts static image URLs via `src` attribute
   - `<img>` does NOT support `srcObject` or MediaStream
   - `<video>` required for live MediaStream from webcam

2. **Missing autoplay**
   - Video element needs explicit `play()` call or `autoplay` attribute
   - Without this, video stays paused (black screen)

3. **Element Confusion**
   - Same element ID used for both IP Camera (img src) and Webcam (MediaStream)
   - Incompatible approaches caused conflicts

## ✅ Solution

### 1. Separate Elements for Different Sources

```html
<div class="card-body p-0 bg-dark text-center" style="min-height: 400px;">
    <!-- Placeholder (shown when no camera active) -->
    <div id="cameraPlaceholder" class="d-flex align-items-center justify-content-center" style="height: 400px;">
        <div class="text-white">
            <i class="bi bi-camera-video" style="font-size: 4rem;"></i>
            <p class="mt-3">Klik tombol di bawah untuk memulai kamera</p>
        </div>
    </div>
    
    <!-- For IP Camera: img tag with src URL -->
    <img id="ipCameraStream" 
         src="" 
         class="img-fluid" 
         style="display: none; max-height: 600px; width: 100%;"
         alt="IP Camera Stream">
    
    <!-- For Webcam: video tag with srcObject -->
    <video id="webcamVideoStream" 
           class="img-fluid" 
           style="display: none; max-height: 600px; width: 100%;"
           autoplay 
           playsinline
           muted></video>
</div>
```

**Key Attributes**:
- `autoplay`: Auto-start video playback when stream attached
- `playsinline`: For mobile Safari (prevents fullscreen)
- `muted`: Required for autoplay in many browsers (security policy)

### 2. Updated JavaScript - IP Camera

```javascript
function startIPCameraStream() {
    const ipCameraStream = document.getElementById('ipCameraStream');  // ✅ Use img element
    const placeholder = document.getElementById('cameraPlaceholder');
    
    // Hide placeholder, show img
    placeholder.style.display = 'none';
    ipCameraStream.style.display = 'block';
    
    // Set img src to MJPEG stream endpoint
    ipCameraStream.src = '/presensi_face/ip_stream?t=' + new Date().getTime();
    
    streamActive = true;
    startAutomaticRecognition();
}

function stopIPCameraStream() {
    const ipCameraStream = document.getElementById('ipCameraStream');
    
    // Clear img src
    ipCameraStream.src = '';
    ipCameraStream.style.display = 'none';
    
    streamActive = false;
}
```

### 3. Updated JavaScript - Webcam

```javascript
async function startWebcam() {
    const webcamVideo = document.getElementById('webcamVideoStream');  // ✅ Use video element
    const placeholder = document.getElementById('cameraPlaceholder');
    
    try {
        // Request webcam access
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user'
            } 
        });
        
        webcamStream = stream;
        
        // Set video srcObject to MediaStream
        webcamVideo.srcObject = stream;
        
        // ✅ CRITICAL: Wait for video to load and play
        await new Promise((resolve) => {
            webcamVideo.onloadedmetadata = () => {
                webcamVideo.play().then(resolve);
            };
        });
        
        // Show video, hide placeholder
        webcamVideo.style.display = 'block';
        placeholder.style.display = 'none';
        
        streamActive = true;
        startAutomaticRecognition();
        
    } catch (error) {
        console.error('[Webcam Error]', error);
        // Handle permission denied, no camera, etc.
    }
}

function stopWebcam() {
    const webcamVideo = document.getElementById('webcamVideoStream');
    
    // Stop all media tracks
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
    }
    
    // Clear video srcObject
    webcamVideo.srcObject = null;
    webcamVideo.style.display = 'none';
    
    streamActive = false;
}
```

### 4. Updated Frame Capture (Webcam)

```javascript
async function captureAndRecognize() {
    try {
        let endpoint = '/presensi_face/capture_ip_frame';
        let requestBody = { meeting_id: meetingId };
        
        if (currentCameraSource === 'webcam') {
            const webcamVideo = document.getElementById('webcamVideoStream');  // ✅ Correct element
            
            if (!webcamVideo || !webcamVideo.srcObject) {
                console.error('[Recognition] Webcam video not ready');
                return;
            }
            
            // Create canvas and draw current video frame
            const canvas = document.createElement('canvas');
            canvas.width = webcamVideo.videoWidth;
            canvas.height = webcamVideo.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(webcamVideo, 0, 0);
            
            // Convert to base64
            const frameBase64 = canvas.toDataURL('image/jpeg', 0.9).split(',')[1];
            
            endpoint = '/presensi_face/capture_webcam_frame';
            requestBody = {
                meeting_id: meetingId,
                frame: frameBase64
            };
        }
        
        // Send to backend...
    } catch (error) {
        console.error('[Recognition] Error:', error);
    }
}
```

## 📊 Before vs After

| Aspect | Before (BROKEN) | After (FIXED) |
|--------|----------------|---------------|
| **Element** | `<img id="videoStream">` | `<img id="ipCameraStream">` + `<video id="webcamVideoStream">` |
| **IP Camera** | `img.src = url` ✅ | `img.src = url` ✅ |
| **Webcam** | `img.srcObject = stream` ❌ | `video.srcObject = stream` ✅ |
| **Autoplay** | None | `autoplay playsinline muted` |
| **Play Call** | None | `await video.play()` |
| **Result** | Black screen | ✅ Live video |

## 🎯 Testing

### Test Webcam Display

1. **Navigate to presensi page**
2. **Expand face recognition section**
3. **Select "Webcam" radio button**
4. **Click "Mulai Kamera"**
5. **Verify**:
   - ✅ Browser permission dialog appears
   - ✅ After "Allow", video stream displays IMMEDIATELY
   - ✅ Video shows live webcam feed (not black screen)
   - ✅ Video is mirrored (front camera)
   - ✅ Status badge: "Webcam Aktif" (green)

### Test IP Camera (Regression)

1. **Stop webcam if active**
2. **Select "IP Camera (CCTV)" radio button**
3. **Click "Mulai Kamera"**
4. **Verify**:
   - ✅ MJPEG stream displays correctly
   - ✅ No webcam video visible
   - ✅ Status badge: "Streaming Aktif" (green)

### Test Switching

1. **Start IP Camera** → ✅ Works
2. **Stop IP Camera** → ✅ Stream stops
3. **Switch to Webcam** → ✅ Works
4. **Stop Webcam** → ✅ Stream stops, camera LED off
5. **Switch back to IP Camera** → ✅ Works

## 🔧 Technical Details

### MediaStream API

```javascript
// getUserMedia returns MediaStream object
const stream = await navigator.mediaDevices.getUserMedia({ video: true });

// MediaStream can ONLY be assigned to <video> or <audio> elements
videoElement.srcObject = stream;

// Must call play() for video to start
await videoElement.play();

// Stop stream when done
stream.getTracks().forEach(track => track.stop());
```

### Video Element Attributes

```html
<video 
    autoplay          <!-- Auto-start playback when srcObject set -->
    playsinline       <!-- Don't fullscreen on iOS -->
    muted            <!-- Required for autoplay in Chrome -->
    controls={false}  <!-- Hide player controls -->
></video>
```

### Canvas Frame Capture

```javascript
// Create canvas matching video dimensions
const canvas = document.createElement('canvas');
canvas.width = video.videoWidth;   // Actual video resolution
canvas.height = video.videoHeight;

// Draw current video frame
const ctx = canvas.getContext('2d');
ctx.drawImage(video, 0, 0);

// Export as base64
const base64 = canvas.toDataURL('image/jpeg', 0.9).split(',')[1];
```

## 🚨 Common Pitfalls

### 1. Using img for MediaStream
```javascript
// ❌ WRONG
const img = document.getElementById('myImg');
img.srcObject = stream;  // Does nothing, black screen
```

### 2. Forgetting to play()
```javascript
// ❌ Video stays paused (black)
video.srcObject = stream;

// ✅ Video plays
video.srcObject = stream;
await video.play();
```

### 3. Not stopping tracks
```javascript
// ❌ Camera LED stays on even after "stop"
video.srcObject = null;

// ✅ Properly release camera
stream.getTracks().forEach(track => track.stop());
video.srcObject = null;
```

### 4. Missing muted attribute
```javascript
// ❌ May not autoplay (browser blocks unmuted autoplay)
<video autoplay></video>

// ✅ Will autoplay
<video autoplay muted></video>
```

## 📝 Summary

### Root Cause
Using `<img>` element for webcam MediaStream (incompatible).

### Fix
- ✅ Separate `<img>` for IP Camera (static MJPEG stream)
- ✅ Separate `<video>` for Webcam (live MediaStream)
- ✅ Proper autoplay attributes
- ✅ Explicit `play()` call
- ✅ Updated all JavaScript references

### Files Modified
- `app/templates/ambil_presensi.html`:
  - HTML: Added separate video element
  - JavaScript: Updated all camera functions

### Result
- ✅ Webcam displays live video (no black screen)
- ✅ IP Camera still works correctly
- ✅ Smooth switching between sources
- ✅ Proper camera resource management

**Status**: FIXED ✅
