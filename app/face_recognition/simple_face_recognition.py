import cv2
import numpy as np
import face_recognition as fr  # Renamed to avoid conflict with folder name
import pickle
import os
from datetime import datetime
import dlib

# Simple imports for basic functionality
try:
    from .face_aligner import FaceAligner
    from .anti_spoofing import AntiSpoofing
    from .face_augmenter import FaceAugmenter
except ImportError:
    # Fallback if modules are not available
    FaceAligner = None
    AntiSpoofing = None
    FaceAugmenter = None

# Import YuNet detector for fast, accurate detection at distance
try:
    from .yunet_detector import YuNetFaceDetector, get_yunet_detector
    YUNET_AVAILABLE = True
    print("[Face Recognition] ✅ YuNet detector available - optimized for long distance detection")
except ImportError as e:
    YUNET_AVAILABLE = False
    print(f"[Face Recognition] ⚠️ YuNet not available: {e}")

class CNNFaceRecognition:
    """
    Simplified face recognition system compatible with MySQL database
    """
    
    def __init__(self, model_path='models/', confidence_threshold=0.45):
        def _env_float(name, default, min_value=None, max_value=None):
            value = os.getenv(name)
            if value is None or str(value).strip() == '':
                result = default
            else:
                try:
                    result = float(value)
                except (ValueError, TypeError):
                    result = default

            if min_value is not None:
                result = max(min_value, result)
            if max_value is not None:
                result = min(max_value, result)
            return result

        self.model_path = model_path
        # Distance threshold (lower is stricter). Can be tuned from .env
        self.confidence_threshold = _env_float(
            'FACE_MATCH_DISTANCE_THRESHOLD',
            confidence_threshold,
            min_value=0.30,
            max_value=0.60
        )

        # Adaptive minimum confidence by face size category (for distant-face tuning)
        self.min_confidence_large = _env_float('FACE_MIN_CONF_LARGE', 0.60, min_value=0.40, max_value=0.95)
        self.min_confidence_medium = _env_float('FACE_MIN_CONF_MEDIUM', 0.55, min_value=0.35, max_value=0.90)
        self.min_confidence_small = _env_float('FACE_MIN_CONF_SMALL', 0.50, min_value=0.30, max_value=0.85)

        # Keep thresholds monotonic: large >= medium >= small
        self.min_confidence_large = max(
            self.min_confidence_large,
            self.min_confidence_medium,
            self.min_confidence_small
        )
        self.min_confidence_small = min(
            self.min_confidence_large,
            self.min_confidence_medium,
            self.min_confidence_small
        )
        self.min_confidence_medium = min(
            self.min_confidence_large,
            max(self.min_confidence_medium, self.min_confidence_small)
        )

        print(
            "[Face Recognition] Threshold config: "
            f"distance<{self.confidence_threshold:.3f}, "
            f"min_conf(large/medium/small)="
            f"{self.min_confidence_large:.2f}/{self.min_confidence_medium:.2f}/{self.min_confidence_small:.2f}"
        )
        
        # Initialize components if available
        self.face_aligner = FaceAligner() if FaceAligner else None
        self.anti_spoofing = AntiSpoofing() if AntiSpoofing else None
        self.augmenter = FaceAugmenter() if FaceAugmenter else None
        
        # Face detection and recognition
        try:
            self.face_detector = dlib.get_frontal_face_detector()
        except:
            self.face_detector = None
        
        # Initialize YuNet for fast detection (especially at distance)
        self.yunet_detector = None
        if YUNET_AVAILABLE:
            try:
                # Lower confidence for detecting distant/small faces
                self.yunet_detector = get_yunet_detector(conf_threshold=0.4)
                print("[Face Recognition] ✅ YuNet initialized for IP camera optimization")
            except Exception as e:
                print(f"[Face Recognition] ⚠️ YuNet init failed: {e}")
        
        # Model components
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)
        
        # Load existing encodings if available
        self.load_encodings()

    def _get_adaptive_min_confidence(self, face_size_ratio):
        """Return adaptive confidence threshold and label based on face size."""
        if face_size_ratio > 0.15:
            return self.min_confidence_large, "large/close"
        elif face_size_ratio > 0.08:
            return self.min_confidence_medium, "medium"
        return self.min_confidence_small, "small/far"
    
    def register_new_student(self, student_id, student_name, images_dir):
        """
        Register new student with multiple face images
        Returns: (success: bool, message: str)
        """
        try:
            # Process face images
            face_encodings = []
            valid_images = 0
            
            if not os.path.exists(images_dir):
                return False, "Images directory not found"
            
            # Process all images in directory
            for filename in os.listdir(images_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(images_dir, filename)
                    
                    # Load and process image
                    image = cv2.imread(image_path)
                    if image is None:
                        continue
                    
                    # Convert BGR to RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Extract face encodings
                    face_locations = fr.face_locations(rgb_image)
                    encodings = fr.face_encodings(rgb_image, face_locations)
                    
                    # QUALITY CONTROL: Only accept images with exactly one face
                    if len(face_locations) == 1 and encodings:
                        face_encodings.extend(encodings)
                        valid_images += 1
                    elif len(face_locations) > 1:
                        print(f"Warning: Multiple faces detected in {filename}, skipping")
                    elif len(face_locations) == 0:
                        print(f"Warning: No face detected in {filename}, skipping")
            
            if valid_images < 1:
                return False, "No valid face images found"
            
            # QUALITY ENHANCEMENT: Require minimum 3 images for better accuracy
            if valid_images < 3:
                return False, f"Please provide at least 3 clear face images (found {valid_images}). This improves recognition accuracy."
            
            # Calculate average encoding
            if len(face_encodings) > 1:
                avg_encoding = np.mean(face_encodings, axis=0)
            else:
                avg_encoding = face_encodings[0]
            
            # Store in memory (database will be handled by main app)
            student_key = f"{student_name}_{student_id}"
            
            # Check if already exists
            if student_key in self.known_face_names:
                # Update existing
                idx = self.known_face_names.index(student_key)
                self.known_face_encodings[idx] = avg_encoding
            else:
                # Add new
                self.known_face_encodings.append(avg_encoding)
                self.known_face_names.append(student_key)
            
            # Save to file for persistence
            self.save_encodings()
            
            return True, f"Successfully registered {student_name} with {valid_images} face images"
            
        except Exception as e:
            return False, f"Error registering student: {str(e)}"
    
    def recognize_face(self, image_input, require_liveness=True):
        """
        Recognize face from image with MANDATORY anti-spoofing protection
        Args:
            image_input: Can be image path (str) or image array (numpy.ndarray)
            require_liveness: Whether to require liveness detection (default: True)
        Returns: dict with recognition results
        """
        try:
            # Handle different input types
            if isinstance(image_input, str):
                # If input is a file path, load the image
                if not os.path.exists(image_input):
                    return {
                        'success': False,
                        'message': 'Image file not found'
                    }
                image = cv2.imread(image_input)
                if image is None:
                    return {
                        'success': False,
                        'message': 'Unable to load image file'
                    }
            else:
                # If input is already an image array
                image = image_input

            # Convert to RGB first (face_recognition expects RGB)
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image

            # ===== IMAGE ENHANCEMENT FOR IP CAMERA =====
            # Enhance RGB image for better detection at distance
            enhanced_image = self._enhance_for_detection(rgb_image)
            
            # MANDATORY ANTI-SPOOFING CHECK - ALWAYS ACTIVE
            if require_liveness:
                # Basic photo detection using multiple methods
                photo_detection_result = self._detect_photo_spoofing(image)
                
                if photo_detection_result['is_photo']:
                    return {
                        'success': False,
                        'message': f"🚨 PHOTO SPOOFING DETECTED! {photo_detection_result['reason']}",
                        'spoofing_detected': True,
                        'photo_detected': True,
                        'security_breach': True,
                        'detection_details': photo_detection_result
                    }
                
                # Advanced anti-spoofing if available
                if self.anti_spoofing:
                    # Extract face region for texture analysis
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    
                    face_region = None
                    if len(faces) > 0:
                        (x, y, w, h) = faces[0]
                        face_region = image[y:y+h, x:x+w]
                    
                    # Comprehensive liveness check
                    liveness_result = self.anti_spoofing.comprehensive_liveness_check(image, face_region)
                    
                    if not liveness_result['is_live']:
                        return {
                            'success': False,
                            'message': f"⚠️ LIVENESS CHECK FAILED! Confidence: {liveness_result['confidence']:.2f}",
                            'spoofing_detected': True,
                            'liveness_details': liveness_result,
                            'security_breach': True
                        }
                    
                    # Additional security checks
                    if liveness_result['blink_count'] < 2:
                        return {
                            'success': False,
                            'message': f"Please blink naturally at least 2 times (detected: {liveness_result['blink_count']})",
                            'requires_blinking': True,
                            'liveness_details': liveness_result
                        }
                    
                    if not liveness_result['movement_detected']:
                        return {
                            'success': False,
                            'message': "Please move your head slightly to confirm you're a real person",
                            'requires_movement': True,
                            'liveness_details': liveness_result
                        }
            
            # Convert to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # ===== ENHANCED DETECTION PIPELINE =====
            # Priority: YuNet (fast+accurate for distance) > HOG (fast) > CNN (accurate fallback)
            
            # Enhance image quality for better face detection
            enhanced_image = self._enhance_for_detection(rgb_image)
            
            # For YuNet, we need BGR format
            enhanced_bgr = cv2.cvtColor(enhanced_image, cv2.COLOR_RGB2BGR) if len(enhanced_image.shape) == 3 else enhanced_image
            
            face_locations = []
            detection_method = "unknown"
            
            import time
            
            # METHOD 0: YuNet (FASTEST + Best for distant faces)
            # YuNet is optimized for small/distant faces - perfect for CCTV at 6+ meters
            if self.yunet_detector is not None:
                print("[Face Detection] Method 0: Trying YuNet (optimized for distant faces)...")
                start_time = time.time()
                try:
                    # Use multi-scale for better small face detection
                    # Scale 1.5 = upscale 50% to catch small faces at distance
                    face_locations_yunet = self.yunet_detector.detect(enhanced_bgr, scale_factor=1.5)
                    elapsed = (time.time() - start_time) * 1000
                    
                    if len(face_locations_yunet) > 0:
                        face_locations = face_locations_yunet
                        detection_method = "YuNet"
                        print(f"[Face Detection] ✅ YuNet found {len(face_locations)} face(s) in {elapsed:.1f}ms - ULTRA FAST!")
                    else:
                        print(f"[Face Detection] ⚠️ YuNet found no faces ({elapsed:.1f}ms), trying HOG...")
                except Exception as e:
                    print(f"[Face Detection] ⚠️ YuNet failed: {str(e)}, trying HOG...")
            
            # METHOD 1: HOG Model (Fast fallback)
            if len(face_locations) == 0:
                print("[Face Detection] Method 1: Trying HOG model...")
                start_time = time.time()
                try:
                    face_locations_hog = fr.face_locations(
                        enhanced_image, 
                        model="hog",
                        number_of_times_to_upsample=1
                    )
                    elapsed = (time.time() - start_time) * 1000
                    
                    if len(face_locations_hog) > 0:
                        face_locations = face_locations_hog
                        detection_method = "HOG"
                        print(f"[Face Detection] ✅ HOG found {len(face_locations)} face(s) in {elapsed:.1f}ms")
                    else:
                        print(f"[Face Detection] ⚠️ HOG found no faces ({elapsed:.1f}ms), trying CNN...")
                except Exception as e:
                    print(f"[Face Detection] ⚠️ HOG failed: {str(e)}, trying CNN...")
            
            # METHOD 2: CNN Model (Accurate Fallback) - QUICK ONLY
            if len(face_locations) == 0:
                print("[Face Detection] Method 2: Trying CNN model (quick downscaled)...")
                start_time = time.time()
                
                try:
                    # Downscale AGGRESSIVELY for speed (0.3 = very fast)
                    scale = 0.3  # Aggressive downscale for speed
                    small = cv2.resize(enhanced_image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
                    small_locations = fr.face_locations(small, model="cnn", number_of_times_to_upsample=0)
                    
                    elapsed = time.time() - start_time
                    print(f"[Face Detection] Method 2 took {elapsed:.2f}s")
                    
                    if len(small_locations) > 0:
                        # scale coordinates back to original image size
                        face_locations = [(int(top/scale), int(right/scale), int(bottom/scale), int(left/scale))
                                          for top, right, bottom, left in small_locations]
                        detection_method = "CNN"
                        print(f"[Face Detection] ✅ CNN found {len(face_locations)} face(s)")
                    else:
                        # CRITICAL: If Method 2 fails, STOP HERE!
                        # Methods 3-4 will freeze for 5-21 seconds - NOT ACCEPTABLE
                        print("[Face Detection] ⚠️ CNN found no faces")
                        print("[Face Detection] ⏭️ SKIPPING Methods 3-4 to prevent freeze")
                        print("[Face Detection] 💡 TIP: Face the camera directly for best results")
                        return {
                            'success': False,
                            'message': 'No face detected. Please face the camera directly.'
                        }
                except Exception as e:
                    elapsed = time.time() - start_time
                    print(f"[Face Detection] ⚠️ CNN failed after {elapsed:.2f}s: {str(e)}")
                    return {
                        'success': False,
                        'message': 'Detection error. Please try again.'
                    }
            
            # METHOD 3 & 4: DISABLED - Causes 5-21 second freeze
            # These methods are too slow for realtime recognition
            # Better to return "no face" quickly than freeze the video
            # User can retry by adjusting position to trigger fast HOG detection
            
            # Log detection result
            if len(face_locations) > 0:
                print(f"[Face Detection] ✅ SUCCESS: {len(face_locations)} face(s) detected using {detection_method}")
            else:
                print(f"[Face Detection] ❌ FAILED: No face detected")
                print(f"[Face Detection] 💡 Methods tried: HOG + CNN (aggressive downscale)")
                print(f"[Face Detection] 💡 TIP: Face the camera directly and ensure good lighting")
            
            # Get face encodings for ALL detected faces
            face_encodings = fr.face_encodings(enhanced_image, face_locations)
            
            if not face_encodings:
                return {
                    'success': False,
                    'message': 'No face detected in image. Please move closer to the camera or ensure good lighting.'
                }
            
            # ===== MULTI-PERSON SUPPORT: Find YOUR face among multiple people =====
            print(f"[Face Recognition] Processing {len(face_encodings)} face(s) in frame...")
            
            # Track all matches found
            all_matches = []
            
            # Compare with known faces
            for idx, face_encoding in enumerate(face_encodings):
                if not self.known_face_encodings:
                    return {
                        'success': False,
                        'message': 'No registered faces found'
                    }
                
                # Calculate distances to all known faces
                face_distances = fr.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                best_distance = face_distances[best_match_index]
                
                print(f"[Face Recognition] Face #{idx+1}: Best match distance = {best_distance:.4f}")
                
                # Check if this face matches any registered person
                if best_distance < self.confidence_threshold:
                    student_info = self.known_face_names[best_match_index]
                    name, student_id = student_info.rsplit('_', 1)
                    confidence_score = 1 - best_distance
                    
                    # Calculate face size for adaptive threshold
                    top, right, bottom, left = face_locations[idx]
                    face_width = right - left
                    face_height = bottom - top
                    face_area = face_width * face_height
                    image_area = image.shape[0] * image.shape[1]
                    face_size_ratio = face_area / image_area
                    
                    # Adaptive minimum confidence
                    min_confidence, size_category = self._get_adaptive_min_confidence(face_size_ratio)
                    
                    print(f"[Face Recognition] Candidate: {name} (ID: {student_id})")
                    print(f"[Face Recognition] Confidence: {confidence_score:.2%}")
                    print(f"[Face Recognition] Face size: {face_size_ratio:.2%} ({size_category})")
                    print(f"[Face Recognition] Threshold: {min_confidence:.2%}")
                    
                    # Check if confidence meets adaptive threshold
                    if confidence_score >= min_confidence:
                        all_matches.append({
                            'name': name,
                            'student_id': student_id,
                            'confidence': confidence_score,
                            'distance': best_distance,
                            'face_size': face_size_ratio,
                            'face_index': idx
                        })
                        print(f"[Face Recognition] ✅ Valid match found!")
                    else:
                        print(f"[Face Recognition] ⚠️ Confidence too low: {confidence_score:.2%} < {min_confidence:.2%}")
                else:
                    print(f"[Face Recognition] ❌ Face #{idx+1}: No match (distance {best_distance:.4f} > {self.confidence_threshold})")
            
            # If no valid matches found
            if not all_matches:
                if len(face_encodings) > 1:
                    return {
                        'success': False,
                        'message': f'Found {len(face_encodings)} faces but none matched registered students. Please move closer to camera.'
                    }
                else:
                    return {
                        'success': False,
                        'message': 'Face not recognized. Please ensure good lighting and move closer to camera.'
                    }
            
            # If multiple registered people in frame, prepare all matches
            if len(all_matches) > 1:
                print(f"[Face Recognition] 🎯 Multiple matches found ({len(all_matches)} faces)!")
                # Sort by confidence (highest first)
                all_matches.sort(key=lambda x: x['confidence'], reverse=True)
                best_match = all_matches[0]
                print(f"[Face Recognition] Best match: {best_match['name']} with {best_match['confidence']:.2%} confidence")
                for i, match in enumerate(all_matches[1:], start=2):
                    print(f"[Face Recognition] Match #{i}: {match['name']} with {match['confidence']:.2%} confidence")
            else:
                best_match = all_matches[0]
            
            # ACCURACY ENHANCEMENT: Check for ambiguous matches 
            # ONLY for SINGLE face scenarios (skip for multiple faces)
            if len(all_matches) == 1:
                # Single face - check if it's ambiguous (could be confused with another person)
                if not self.known_face_encodings:
                    return {
                        'success': False,
                        'message': 'No registered faces found'
                    }
                
                face_encoding = face_encodings[best_match['face_index']]
                face_distances = fr.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                best_distance = face_distances[best_match_index]
                
                # Check if second-best match is too close (potential confusion)
                if len(face_distances) > 1:
                    sorted_distances = np.sort(face_distances)
                    if len(sorted_distances) > 1:
                        distance_gap = sorted_distances[1] - sorted_distances[0]
                        
                        # FIXED: More lenient ambiguous check
                        # Only reject if:
                        # 1. The gap between best and second-best is very small (< 0.08) AND
                        # 2. The best match distance is high (> 0.45, meaning low confidence) AND
                        # 3. The confidence is below 60%
                        is_ambiguous = (
                            distance_gap < 0.08 and 
                            best_distance > 0.45 and 
                            best_match['confidence'] < 0.60
                        )
                        
                        print(f"[Face Recognition] Ambiguous check:")
                        print(f"[Face Recognition]   - Best distance: {best_distance:.4f}")
                        print(f"[Face Recognition]   - Distance gap to second: {distance_gap:.4f}")
                        print(f"[Face Recognition]   - Best confidence: {best_match['confidence']:.2%}")
                        print(f"[Face Recognition]   - Is ambiguous: {is_ambiguous}")
                        
                        if is_ambiguous:
                            print(f"[Face Recognition] ⚠️ Rejecting due to ambiguous match")
                            return {
                                'success': False,
                                'message': 'Ambiguous recognition - multiple similar matches found. Please re-register with more diverse photos.'
                            }
                        else:
                            print(f"[Face Recognition] ✅ Ambiguous check passed - proceeding with recognition")
            else:
                # Multiple faces detected - SKIP ambiguous check
                # This is VALID scenario (multiple different people in frame)
                print(f"[Face Recognition] ✅ Multiple faces - skipping ambiguous check (this is expected!)")
            
            # Use the best match we found earlier
            name = best_match['name']
            student_id = best_match['student_id']
            confidence_score = best_match['confidence']
            face_size_ratio = best_match['face_size']
            
            # Determine size category
            min_confidence, size_category = self._get_adaptive_min_confidence(face_size_ratio)
            
            print(f"[Face Recognition] 🎉 FINAL RESULT:")
            print(f"[Face Recognition] Total faces detected: {len(all_matches)}")
            print(f"[Face Recognition] Primary: {name} (ID: {student_id}) - {confidence_score:.2%}")
            print(f"[Face Recognition] ✅ Recognition SUCCESS!")
            
            # Prepare all faces data for response
            all_faces_data = []
            for idx, match in enumerate(all_matches):
                face_data = {
                    'name': match['name'],
                    'student_id': match['student_id'],
                    'confidence': match['confidence'],
                    'distance': match['distance'],
                    'face_size': match['face_size'],
                    'position': idx + 1
                }
                all_faces_data.append(face_data)
                print(f"[Face Recognition]   #{idx+1}: {match['name']} - {match['confidence']:.2%}")
            
            return {
                'success': True,
                'faces_detected': len(all_matches),
                'multiple_faces': len(all_matches) > 1,
                'student': {
                    'name': name,
                    'student_id': student_id,
                    'id': student_id
                },
                'confidence': confidence_score,
                'distance': best_match['distance'],
                'all_faces': all_faces_data,  # NEW: Array of all detected faces
                'verification_details': {
                    'face_count': len(face_locations),
                    'detected_faces': len(all_matches),
                    'face_size_category': size_category,
                    'encoding_quality': 'excellent' if confidence_score > 0.8 else 'good' if confidence_score > 0.65 else 'acceptable',
                    'liveness_verified': require_liveness and self.anti_spoofing is not None,
                    'security_level': 'high' if require_liveness else 'basic'
                },
                'liveness_details': liveness_result if require_liveness and self.anti_spoofing else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Recognition error: {str(e)}"
            }
    
    def save_encodings(self):
        """Save face encodings to file"""
        try:
            encodings_path = os.path.join(self.model_path, 'face_encodings.pkl')
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(encodings_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving encodings: {e}")
            return False
    
    def load_encodings(self):
        """Load face encodings from file"""
        try:
            encodings_path = os.path.join(self.model_path, 'face_encodings.pkl')
            if os.path.exists(encodings_path):
                with open(encodings_path, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data.get('encodings', [])
                    self.known_face_names = data.get('names', [])
                return True
        except Exception as e:
            print(f"Error loading encodings: {e}")
            self.known_face_encodings = []
            self.known_face_names = []
            return False
    
    def _detect_photo_spoofing(self, image):
        """
        Detect if image is a photo/print rather than live capture
        Multiple detection methods for robust anti-spoofing
        """
        detection_result = {
            'is_photo': False,
            'confidence': 0.0,
            'reason': '',
            'methods': {}
        }
        
        try:
            # Method 1: Edge Density Analysis (Photos have sharp edges)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Photos typically have high edge density (>0.08)
            edge_suspicious = edge_density > 0.08
            detection_result['methods']['edge_density'] = {
                'value': edge_density,
                'suspicious': edge_suspicious,
                'threshold': 0.08
            }
            
            # Method 2: Color Saturation Analysis (Photos often oversaturated)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1]
            avg_saturation = np.mean(saturation)
            
            # Photos from screens/prints often oversaturated (>140) or undersaturated (<80)
            saturation_suspicious = avg_saturation > 140 or avg_saturation < 80
            detection_result['methods']['saturation'] = {
                'value': avg_saturation,
                'suspicious': saturation_suspicious,
                'normal_range': '80-140'
            }
            
            # Method 3: Texture Uniformity (Photos too uniform)
            texture_variance = np.var(gray)
            texture_suspicious = texture_variance < 500  # Too uniform
            detection_result['methods']['texture'] = {
                'value': texture_variance,
                'suspicious': texture_suspicious,
                'min_threshold': 500
            }
            
            # Method 4: Color Distribution Analysis
            b, g, r = cv2.split(image)
            color_ratios = {
                'rg_ratio': np.mean(r) / (np.mean(g) + 1),
                'rb_ratio': np.mean(r) / (np.mean(b) + 1),
                'gb_ratio': np.mean(g) / (np.mean(b) + 1)
            }
            
            # Unnatural color ratios indicate photos/screens
            unnatural_colors = (
                color_ratios['rg_ratio'] > 2.0 or color_ratios['rg_ratio'] < 0.8 or
                color_ratios['rb_ratio'] > 2.0 or color_ratios['rb_ratio'] < 0.9
            )
            detection_result['methods']['color_ratios'] = {
                'ratios': color_ratios,
                'suspicious': unnatural_colors
            }
            
            # Method 5: Frequency Domain Analysis (Screen patterns)
            f_transform = np.fft.fft2(gray)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)
            
            # Look for regular patterns (screen pixels)
            threshold = np.mean(magnitude_spectrum) + 2 * np.std(magnitude_spectrum)
            peaks = magnitude_spectrum > threshold
            peak_ratio = np.sum(peaks) / magnitude_spectrum.size
            
            # Too many regular patterns indicate screen/digital source
            pattern_suspicious = peak_ratio > 0.015
            detection_result['methods']['frequency_patterns'] = {
                'peak_ratio': peak_ratio,
                'suspicious': pattern_suspicious,
                'threshold': 0.015
            }
            
            # Method 6: Lighting Analysis (Photos have unnatural lighting)
            # Calculate lighting uniformity
            lighting_std = np.std(gray)
            lighting_mean = np.mean(gray)
            lighting_cv = lighting_std / (lighting_mean + 1)  # Coefficient of variation
            
            # Photos often have either too uniform or too varied lighting
            lighting_suspicious = lighting_cv < 0.15 or lighting_cv > 0.8
            detection_result['methods']['lighting'] = {
                'coefficient_variation': lighting_cv,
                'suspicious': lighting_suspicious,
                'normal_range': '0.15-0.8'
            }
            
            # Method 7: Digital Artifact Detection
            # Look for JPEG compression artifacts
            # Convert to LAB color space for better artifact detection
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l_channel = lab[:, :, 0]
            
            # Calculate local variance to detect compression blocks
            kernel = np.ones((8, 8), np.float32) / 64
            local_mean = cv2.filter2D(l_channel.astype(np.float32), -1, kernel)
            local_variance = cv2.filter2D((l_channel.astype(np.float32) - local_mean)**2, -1, kernel)
            
            # High variance in 8x8 blocks indicates JPEG artifacts
            artifact_score = np.mean(local_variance)
            artifact_suspicious = artifact_score > 100
            detection_result['methods']['digital_artifacts'] = {
                'artifact_score': artifact_score,
                'suspicious': artifact_suspicious,
                'threshold': 100
            }
            
            # Combine all methods for final decision
            suspicious_methods = sum([
                edge_suspicious,
                saturation_suspicious, 
                texture_suspicious,
                unnatural_colors,
                pattern_suspicious,
                lighting_suspicious,
                artifact_suspicious
            ])
            
            # If 3 or more methods detect suspicious patterns, classify as photo
            detection_result['is_photo'] = suspicious_methods >= 3
            detection_result['confidence'] = suspicious_methods / 7.0
            detection_result['suspicious_methods_count'] = suspicious_methods
            
            if detection_result['is_photo']:
                reasons = []
                if edge_suspicious: reasons.append("high edge density")
                if saturation_suspicious: reasons.append("abnormal color saturation")
                if texture_suspicious: reasons.append("too uniform texture")
                if unnatural_colors: reasons.append("unnatural color ratios")
                if pattern_suspicious: reasons.append("screen patterns detected")
                if lighting_suspicious: reasons.append("unnatural lighting")
                if artifact_suspicious: reasons.append("digital artifacts")
                
                detection_result['reason'] = f"Photo detected: {', '.join(reasons)}"
            else:
                detection_result['reason'] = "Live capture verified"
            
        except Exception as e:
            # If detection fails, err on the side of caution
            detection_result['is_photo'] = True
            detection_result['reason'] = f"Detection error - blocking for security: {str(e)}"
            detection_result['confidence'] = 1.0
        
        return detection_result
    
    def _enhance_for_detection(self, image, aggressive=False):
        """
        Enhance image quality for better face detection at distance (IP Camera)
        Improves detection of small/far faces from CCTV
        Expect and return RGB image (face_recognition uses RGB)
        """
        try:
            # Input is expected RGB; convert to grayscale explicitly from RGB
            if len(image.shape) == 3 and image.shape[2] == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image
            
            # 1. Adaptive Histogram Equalization (CLAHE) - Improve contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced_gray = clahe.apply(gray)
            
            # 2. Denoise while preserving edges
            denoised = cv2.fastNlMeansDenoising(enhanced_gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            
            # 3. Sharpen image to enhance features
            kernel_sharpening = np.array([[-1,-1,-1],
                                         [-1, 9,-1],
                                         [-1,-1,-1]])
            sharpened = cv2.filter2D(denoised, -1, kernel_sharpening)
            
            # Convert back to RGB and blend with original for natural look
            if len(image.shape) == 3 and image.shape[2] == 3:
                enhanced_rgb = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
                result = cv2.addWeighted(enhanced_rgb, 0.7, image, 0.3, 0)
            else:
                result = sharpened
            
            print("[Image Enhancement] Applied CLAHE, denoising, and sharpening for better detection")
            return result
            
        except Exception as e:
            print(f"[Image Enhancement] Error: {e}, using original image")
            return image
    
    def get_registered_count(self):
        """Get count of registered faces"""
        return len(self.known_face_names)
    
    def remove_student(self, student_id):
        """Remove student from face recognition system"""
        try:
            # Find and remove all entries for this student
            indices_to_remove = []
            for i, name in enumerate(self.known_face_names):
                if name.endswith(f"_{student_id}"):
                    indices_to_remove.append(i)
            
            # Remove in reverse order to maintain indices
            for i in reversed(indices_to_remove):
                del self.known_face_encodings[i]
                del self.known_face_names[i]
            
            # Save updated encodings
            self.save_encodings()
            return True
        except Exception as e:
            print(f"Error removing student: {e}")
            return False
