"""
Dataset Quality Analyzer
Analyze face recognition dataset quality and provide recommendations
"""

import os
import cv2
import face_recognition
import numpy as np
from pathlib import Path

def analyze_dataset(student_id="22024151"):
    """Analyze dataset quality for a student"""
    
    dataset_path = f"uploads/faces/{student_id}"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset folder not found: {dataset_path}")
        return
    
    images = [f for f in os.listdir(dataset_path) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    print("="*80)
    print(f"📊 DATASET QUALITY ANALYSIS - Student ID: {student_id}")
    print("="*80)
    print(f"\n📁 Total images: {len(images)}")
    print(f"📂 Location: {dataset_path}\n")
    
    results = []
    face_sizes = []
    brightnesses = []
    sharpnesses = []
    
    for idx, img_name in enumerate(images, 1):
        img_path = os.path.join(dataset_path, img_name)
        
        try:
            # Load image
            image = cv2.imread(img_path)
            if image is None:
                print(f"❌ {idx}. {img_name}: Failed to load")
                continue
                
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            face_locations = face_recognition.face_locations(rgb_image, model="hog")
            
            # Calculate image metrics
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            if len(face_locations) == 0:
                status = "❌ NO FACE DETECTED"
                face_size = 0
                quality = "BAD"
            elif len(face_locations) > 1:
                status = "⚠️  MULTIPLE FACES"
                top, right, bottom, left = face_locations[0]
                face_width = right - left
                face_height = bottom - top
                face_size = (face_width * face_height) / (image.shape[0] * image.shape[1])
                quality = "POOR"
            else:
                top, right, bottom, left = face_locations[0]
                face_width = right - left
                face_height = bottom - top
                face_size = (face_width * face_height) / (image.shape[0] * image.shape[1])
                
                # Quality assessment
                if face_size < 0.05:
                    status = "⚠️  FACE TOO SMALL"
                    quality = "POOR"
                elif face_size < 0.10:
                    status = "⚠️  FACE SMALL"
                    quality = "OK"
                elif face_size > 0.40:
                    status = "⚠️  FACE TOO CLOSE"
                    quality = "OK"
                else:
                    status = "✅ GOOD"
                    quality = "GOOD"
                
                # Check brightness
                if brightness < 80:
                    status += " (TOO DARK)"
                    quality = "POOR" if quality == "GOOD" else quality
                elif brightness > 200:
                    status += " (TOO BRIGHT)"
                    quality = "POOR" if quality == "GOOD" else quality
                
                # Check sharpness
                if sharpness < 100:
                    status += " (BLURRY)"
                    quality = "POOR"
                
                face_sizes.append(face_size)
                brightnesses.append(brightness)
                sharpnesses.append(sharpness)
            
            results.append({
                'name': img_name,
                'status': status,
                'quality': quality,
                'face_size': face_size,
                'brightness': brightness,
                'sharpness': sharpness,
                'faces_count': len(face_locations)
            })
            
            # Print result
            print(f"{idx:2d}. {img_name:40s} {status:30s} | Size: {face_size:5.1%} | Bright: {brightness:3.0f} | Sharp: {sharpness:6.0f}")
            
        except Exception as e:
            print(f"❌ {idx}. {img_name}: Error - {str(e)}")
    
    # Summary Statistics
    print("\n" + "="*80)
    print("📈 DATASET STATISTICS")
    print("="*80)
    
    good_count = sum(1 for r in results if r['quality'] == 'GOOD')
    ok_count = sum(1 for r in results if r['quality'] == 'OK')
    poor_count = sum(1 for r in results if r['quality'] in ['POOR', 'BAD'])
    
    print(f"\n✅ GOOD quality:  {good_count:2d} images ({good_count/len(results)*100:.1f}%)")
    print(f"⚠️  OK quality:    {ok_count:2d} images ({ok_count/len(results)*100:.1f}%)")
    print(f"❌ POOR quality:  {poor_count:2d} images ({poor_count/len(results)*100:.1f}%)")
    
    if face_sizes:
        print(f"\n📏 Face Size Statistics:")
        print(f"   Average: {np.mean(face_sizes)*100:.1f}% of image")
        print(f"   Min:     {np.min(face_sizes)*100:.1f}% of image")
        print(f"   Max:     {np.max(face_sizes)*100:.1f}% of image")
        print(f"   Ideal:   15-35% of image")
    
    if brightnesses:
        print(f"\n💡 Brightness Statistics:")
        print(f"   Average: {np.mean(brightnesses):.0f} (0-255)")
        print(f"   Min:     {np.min(brightnesses):.0f}")
        print(f"   Max:     {np.max(brightnesses):.0f}")
        print(f"   Ideal:   100-180")
    
    if sharpnesses:
        print(f"\n🎯 Sharpness Statistics:")
        print(f"   Average: {np.mean(sharpnesses):.0f}")
        print(f"   Min:     {np.min(sharpnesses):.0f}")
        print(f"   Max:     {np.max(sharpnesses):.0f}")
        print(f"   Ideal:   >200 (sharp)")
    
    # Recommendations
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)
    
    if good_count < 5:
        print("\n❌ CRITICAL: Less than 5 GOOD quality images!")
        print("   → You need at least 5-10 high-quality images for reliable recognition")
        print("   → Current GOOD images: Only", good_count)
    elif good_count < 10:
        print("\n⚠️  WARNING: Only", good_count, "GOOD quality images")
        print("   → Recommended: 10-15 high-quality images for best accuracy")
    else:
        print("\n✅ Dataset size is adequate (", good_count, "GOOD images)")
    
    if face_sizes:
        avg_size = np.mean(face_sizes)
        if avg_size < 0.10:
            print("\n⚠️  WARNING: Faces are too SMALL in images")
            print("   → Move CLOSER to camera when capturing")
            print("   → Ideal: Face should be 15-35% of image")
        elif avg_size > 0.40:
            print("\n⚠️  WARNING: Faces are too CLOSE/LARGE in images")
            print("   → Move slightly AWAY from camera")
            print("   → Ideal: Face should be 15-35% of image")
    
    if brightnesses:
        avg_bright = np.mean(brightnesses)
        if avg_bright < 100:
            print("\n⚠️  WARNING: Images are too DARK")
            print("   → Improve lighting conditions")
            print("   → Use natural light or bright indoor lighting")
        elif avg_bright > 180:
            print("\n⚠️  WARNING: Images are too BRIGHT/OVEREXPOSED")
            print("   → Reduce lighting or avoid direct sunlight")
    
    if sharpnesses:
        avg_sharp = np.mean(sharpnesses)
        if avg_sharp < 200:
            print("\n⚠️  WARNING: Images are BLURRY")
            print("   → Keep phone/camera steady when capturing")
            print("   → Ensure autofocus has locked before capture")
            print("   → Clean camera lens")
    
    # Specific recommendations
    print("\n" + "="*80)
    print("🎯 HOW TO IMPROVE YOUR DATASET")
    print("="*80)
    
    print("""
1. 📸 CAPTURE NEW IMAGES WITH:
   ✅ Good lighting (natural light or bright indoor)
   ✅ Face 15-35% of image (arm's length distance)
   ✅ Clear focus (not blurry)
   ✅ Face camera directly
   ✅ Neutral expression + slight variations

2. 📐 VARIATION IS KEY:
   ✅ 5-7 images: Front view, neutral expression
   ✅ 2-3 images: Slight head tilt (left/right)
   ✅ 2-3 images: Slight smile
   ✅ 1-2 images: Different lighting conditions
   ✅ 1-2 images: With glasses (if you wear them)

3. ❌ AVOID:
   ❌ Multiple people in frame
   ❌ Side profile (>45° angle)
   ❌ Extreme facial expressions
   ❌ Hands covering face
   ❌ Very dark or very bright images
   ❌ Blurry/out-of-focus images

4. 🗑️ DELETE POOR IMAGES:
   → Remove images marked as POOR or BAD quality
   → Keep only GOOD and OK quality images
   → Quality over quantity!

5. 🔄 RE-REGISTER:
   → After improving dataset, re-register in system
   → This will regenerate face encodings with better data
""")
    
    print("="*80)
    print("📋 IMAGES TO REVIEW/DELETE:")
    print("="*80)
    
    poor_images = [r for r in results if r['quality'] in ['POOR', 'BAD']]
    if poor_images:
        for img in poor_images:
            print(f"❌ {img['name']:40s} - {img['status']}")
        print(f"\n→ Consider deleting these {len(poor_images)} images and replacing with better quality")
    else:
        print("✅ No poor quality images found!")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        student_id = sys.argv[1]
    else:
        student_id = "22024151"  # Default
    
    analyze_dataset(student_id)
