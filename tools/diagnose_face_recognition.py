#!/usr/bin/env python3
"""
IP Camera Face Recognition Diagnostic Tool
Uses actual project's face recognition system
"""

import cv2
import os
import sys
import traceback
from dotenv import load_dotenv

# Ensure project root is importable (avoid shadowing external `face_recognition` package)
PROJECT_ROOT = os.path.dirname(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load environment variables
load_dotenv()

def test_with_actual_system():
    """Test IP camera with actual face recognition system"""
    
    rtsp_url = os.getenv('RTSP_URL', '')
    
    if not rtsp_url:
        print("❌ ERROR: No RTSP_URL in .env file")
        return
    
    print("=" * 70)
    print("🎥 IP CAMERA FACE RECOGNITION DIAGNOSTIC")
    print("=" * 70)
    print(f"\n📡 RTSP URL: {rtsp_url}")
    
    # Import actual face recognition system
    print("\n[INIT] Loading face recognition system...")
    try:
        from app.face_recognition import CNNFaceRecognition
        
        # Initialize face recognition
        face_system = CNNFaceRecognition()
        print("✅ Face recognition system loaded")
        
        # Load face encodings
        if face_system.load_encodings():
            print(f"✅ Face encodings loaded: {len(face_system.known_face_encodings)} faces in database")
        else:
            print("⚠️ No face encodings found - will only test detection, not recognition")
        
    except Exception as e:
        print(f"❌ FAILED to load face recognition system: {e}")
        traceback.print_exc()
        return
    
    # Test 1: Connection
    print("\n[TEST 1] Connecting to IP camera...")
    try:
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 10000)
        
        if not cap.isOpened():
            print("❌ FAILED: Cannot open RTSP stream")
            return
        
        print("✅ Connected to IP camera")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return
    
    # Test 2: Capture Frame
    print("\n[TEST 2] Capturing frame...")
    try:
        ret, frame = cap.read()
        
        if not ret or frame is None:
            print("❌ FAILED: Cannot read frame")
            cap.release()
            return
        
        height, width, channels = frame.shape
        print(f"✅ Frame captured: {width}x{height}")
        
        # Resize to 640px width (same as production)
        if width > 640:
            scale = 640 / width
            new_width = 640
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
            print(f"✅ Resized to: {new_width}x{new_height}")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        cap.release()
        return
    
    # Test 3: Save frame temporarily
    print("\n[TEST 3] Saving test frame...")
    try:
        test_dir = "test_frames"
        os.makedirs(test_dir, exist_ok=True)
        test_path = os.path.join(test_dir, "ip_camera_test.jpg")
        
        cv2.imwrite(test_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print(f"✅ Saved: {test_path}")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        cap.release()
        return

    # Test 3.5: Long-distance suitability (face size in pixels)
    print("\n[TEST 3.5] Evaluating long-distance suitability...")
    try:
        # Use YuNet directly if available, fallback to dlib detector API in face_recognition
        face_boxes = []

        if getattr(face_system, 'yunet_detector', None) is not None:
            face_boxes = face_system.yunet_detector.detect(frame, scale_factor=1.5)
            print(f"   YuNet detected: {len(face_boxes)} face(s)")
        else:
            import face_recognition
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_boxes = face_recognition.face_locations(rgb, model='hog')
            print(f"   HOG detected: {len(face_boxes)} face(s)")

        if face_boxes:
            frame_area = frame.shape[0] * frame.shape[1]
            for i, (top, right, bottom, left) in enumerate(face_boxes, start=1):
                fw = right - left
                fh = bottom - top
                farea = fw * fh
                ratio = farea / frame_area

                if fh >= 120:
                    suitability = "Excellent"
                elif fh >= 100:
                    suitability = "Good"
                elif fh >= 80:
                    suitability = "Borderline"
                else:
                    suitability = "Too Small"

                print(f"   Face #{i}: {fw}x{fh}px (area ratio {ratio:.2%}) -> {suitability}")
                if suitability in ("Borderline", "Too Small"):
                    print("      ⚠️ Suggestion: move closer / use ROI zoom / improve camera placement")
        else:
            print("   ⚠️ No faces detected for size analysis")

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    
    # Test 4: Face Detection with CNN Hybrid
    print("\n[TEST 4] Testing face detection (CNN Hybrid)...")
    print("   This uses the ACTUAL detection method from your project")
    print("   Method: CNN → HOG → CNN-Upscaled → CNN-Downscaled → CNN-Original")
    
    try:
        # Use actual face detection method
        result = face_system.recognize_face(test_path, require_liveness=False)
        
        print(f"\n   Detection Result:")
        print(f"   - Success: {result.get('success', False)}")
        print(f"   - Faces detected: {result.get('faces_detected', 0)}")
        print(f"   - Detection method: {result.get('detection_method', 'unknown')}")
        
        if result.get('success'):
            print(f"   - Recognized: {result.get('student', {}).get('name', 'Unknown')}")
            print(f"   - Student ID: {result.get('student', {}).get('student_id', 'Unknown')}")
            print(f"   - Confidence: {result.get('confidence', 0):.2%}")
        else:
            print(f"   - Message: {result.get('message', 'No message')}")
        
        # Get debug info if available
        if 'debug_info' in result:
            print(f"\n   Debug Info:")
            debug = result['debug_info']
            for key, value in debug.items():
                print(f"   - {key}: {value}")
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    cap.release()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ IP Camera Connection: OK")
    print(f"✅ Frame Capture: OK")
    print(f"📐 Resolution: {width}x{height} (after resize)")
    
    message_text = str(result.get('message', '')).lower()

    if result.get('success'):
        print(f"\n✅ Face Recognition: SUCCESS")
        print(f"   Recognized: {result.get('student', {}).get('name', 'Unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.2%}")
        print(f"   Method: {result.get('detection_method', 'unknown')}")
    elif "Recognition error:" in str(result.get('message', '')):
        print(f"\n⚠️ Recognition Pipeline Error")
        print(f"   Message: {result.get('message', 'Unknown error')}")
        print(f"   Note: Detection may still be working; this indicates runtime/import issue in recognition stage.")
    elif result.get('faces_detected', 0) > 0:
        print(f"\n⚠️ Face Detection: SUCCESS but Recognition FAILED")
        print(f"   Faces detected: {result.get('faces_detected', 0)}")
        print(f"   Method: {result.get('detection_method', 'unknown')}")
        print(f"   Reason: {result.get('message', 'Unknown')}")
        print(f"\n💡 Possible reasons:")
        print(f"   - Face not in database")
        print(f"   - Confidence too low")
        print(f"   - Face angle not ideal")
        print(f"   - Lighting changed from registration photos")
    elif "not recognized" in message_text or "no face detected" in message_text:
        print(f"\n⚠️ Face Detection likely SUCCESS but Recognition FAILED")
        print(f"   Reason: {result.get('message', 'Unknown')}")
        print(f"\n💡 Interpretation:")
        print(f"   - Camera and detector are working")
        print(f"   - Face size/quality may be too low for stable embedding match")
        print(f"   - This is common for long-distance faces")
    else:
        print(f"\n❌ Face Detection: FAILED (0 faces detected)")
        print(f"   Method attempted: {result.get('detection_method', 'unknown')}")
        print(f"\n💡 Possible reasons:")
        print(f"   - No person in camera view")
        print(f"   - Person too far from camera (optimal: 2-3 meters)")
        print(f"   - Face not facing camera directly")
        print(f"   - Poor lighting conditions")
        print(f"   - Camera angle too steep")
    
    print(f"\n📁 Test frame saved in '{test_dir}/' folder")
    print(f"   You can manually check: {test_path}")
    print("=" * 70)


if __name__ == "__main__":
    print("\n🚀 Starting IP Camera Face Recognition Diagnostic...\n")
    
    try:
        test_with_actual_system()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        traceback.print_exc()
    
    print("\n✅ Diagnostic complete!\n")
