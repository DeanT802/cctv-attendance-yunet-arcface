#!/usr/bin/env python3
"""
IP Camera Diagnostic Tool
Analyze why IP camera cannot detect faces
"""

import cv2
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_ip_camera_detection():
    """Test IP camera connection and face detection capability"""
    
    rtsp_url = os.getenv('RTSP_URL', '')
    
    if not rtsp_url:
        print("❌ ERROR: No RTSP_URL in .env file")
        return
    
    print("=" * 70)
    print("🎥 IP CAMERA DIAGNOSTIC TOOL")
    print("=" * 70)
    print(f"\n📡 RTSP URL: {rtsp_url}")
    
    # Test 1: Connection
    print("\n[TEST 1] Testing connection...")
    try:
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
        
        if not cap.isOpened():
            print("❌ FAILED: Cannot open RTSP stream")
            return
        
        print("✅ SUCCESS: Connected to IP camera")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return
    
    # Test 2: Read Frame
    print("\n[TEST 2] Reading frame...")
    try:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("❌ FAILED: Cannot read frame")
            cap.release()
            return
        
        height, width, channels = frame.shape
        print(f"✅ SUCCESS: Frame captured")
        print(f"   Resolution: {width}x{height}")
        print(f"   Channels: {channels}")
        print(f"   Size: {frame.nbytes / 1024:.2f} KB")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        cap.release()
        return
    
    # Test 3: Image Quality
    print("\n[TEST 3] Analyzing image quality...")
    try:
        import numpy as np
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate brightness
        brightness = np.mean(gray)
        
        # Calculate contrast (standard deviation)
        contrast = np.std(gray)
        
        # Calculate sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        print(f"   Brightness: {brightness:.2f} (ideal: 80-180)")
        print(f"   Contrast: {contrast:.2f} (ideal: >30)")
        print(f"   Sharpness: {sharpness:.2f} (ideal: >100)")
        
        # Quality assessment
        quality_issues = []
        if brightness < 80:
            quality_issues.append("⚠️ Too dark")
        elif brightness > 180:
            quality_issues.append("⚠️ Too bright")
        
        if contrast < 30:
            quality_issues.append("⚠️ Low contrast")
        
        if sharpness < 100:
            quality_issues.append("⚠️ Blurry image")
        
        if quality_issues:
            print(f"\n   Quality Issues:")
            for issue in quality_issues:
                print(f"   {issue}")
        else:
            print("   ✅ Image quality looks good!")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    
    # Test 4: Face Detection (CNN)
    print("\n[TEST 4] Testing CNN face detection...")
    try:
        import face_recognition
        
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize to 640px width for testing
        if width > 640:
            scale = 640 / width
            new_width = 640
            new_height = int(height * scale)
            rgb_frame = cv2.resize(rgb_frame, (new_width, new_height))
            print(f"   Resized to: {new_width}x{new_height}")
        
        # Detect faces with CNN
        face_locations_cnn = face_recognition.face_locations(rgb_frame, model='cnn')
        print(f"   CNN detected: {len(face_locations_cnn)} face(s)")
        
        if face_locations_cnn:
            for i, (top, right, bottom, left) in enumerate(face_locations_cnn):
                face_width = right - left
                face_height = bottom - top
                print(f"   Face #{i+1}: {face_width}x{face_height} pixels")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    
    # Test 5: Face Detection (HOG)
    print("\n[TEST 5] Testing HOG face detection...")
    try:
        # Detect faces with HOG (faster)
        face_locations_hog = face_recognition.face_locations(rgb_frame, model='hog')
        print(f"   HOG detected: {len(face_locations_hog)} face(s)")
        
        if face_locations_hog:
            for i, (top, right, bottom, left) in enumerate(face_locations_hog):
                face_width = right - left
                face_height = bottom - top
                print(f"   Face #{i+1}: {face_width}x{face_height} pixels")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    
    # Test 6: Save Test Frame
    print("\n[TEST 6] Saving test frame...")
    try:
        test_dir = "test_frames"
        os.makedirs(test_dir, exist_ok=True)
        
        # Save original frame
        cv2.imwrite(f"{test_dir}/ip_camera_original.jpg", frame)
        print(f"   ✅ Saved: {test_dir}/ip_camera_original.jpg")
        
        # Save resized frame
        if width > 640:
            cv2.imwrite(f"{test_dir}/ip_camera_resized.jpg", cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR))
            print(f"   ✅ Saved: {test_dir}/ip_camera_resized.jpg")
        
        # Save with face rectangles (if detected)
        if face_locations_cnn or face_locations_hog:
            test_frame = rgb_frame.copy()
            
            # Draw CNN faces (green)
            for (top, right, bottom, left) in face_locations_cnn:
                cv2.rectangle(test_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(test_frame, "CNN", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Draw HOG faces (blue)
            for (top, right, bottom, left) in face_locations_hog:
                cv2.rectangle(test_frame, (left, top), (right, bottom), (255, 0, 0), 2)
                cv2.putText(test_frame, "HOG", (left, top + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            
            cv2.imwrite(f"{test_dir}/ip_camera_detected.jpg", cv2.cvtColor(test_frame, cv2.COLOR_RGB2BGR))
            print(f"   ✅ Saved: {test_dir}/ip_camera_detected.jpg")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    
    # Cleanup
    cap.release()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ Connection: OK")
    print(f"✅ Frame Reading: OK")
    print(f"📐 Resolution: {width}x{height}")
    
    if quality_issues:
        print(f"\n⚠️ Image Quality Issues:")
        for issue in quality_issues:
            print(f"   {issue}")
    else:
        print(f"\n✅ Image Quality: Good")
    
    total_faces = len(face_locations_cnn) + len(face_locations_hog)
    if total_faces == 0:
        print(f"\n❌ Face Detection: FAILED (0 faces detected)")
        print(f"\n🔍 Possible Reasons:")
        print(f"   1. No person in camera view")
        print(f"   2. Person too far from camera")
        print(f"   3. Poor lighting conditions")
        print(f"   4. Image quality issues")
        print(f"   5. Camera angle not ideal")
    else:
        print(f"\n✅ Face Detection: SUCCESS ({total_faces} method(s) detected faces)")
    
    print(f"\n💡 Recommendations:")
    if brightness < 80:
        print(f"   - Increase room lighting (too dark)")
    elif brightness > 180:
        print(f"   - Reduce lighting or adjust camera exposure (too bright)")
    
    if contrast < 30:
        print(f"   - Improve camera focus and contrast settings")
    
    if sharpness < 100:
        print(f"   - Clean camera lens")
        print(f"   - Adjust camera focus")
        print(f"   - Reduce camera shake/vibration")
    
    if total_faces == 0:
        print(f"   - Move closer to camera (2-3 meters optimal)")
        print(f"   - Face camera directly")
        print(f"   - Ensure face is well-lit")
        print(f"   - Remove obstacles between face and camera")
    
    print(f"\n📁 Check saved frames in '{test_dir}/' folder")
    print("=" * 70)


if __name__ == "__main__":
    print("\n🚀 Starting IP Camera Diagnostic Tool...\n")
    
    try:
        test_ip_camera_detection()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Diagnostic complete!\n")
