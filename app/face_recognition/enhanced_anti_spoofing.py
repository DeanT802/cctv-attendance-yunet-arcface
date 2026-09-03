import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque
import math
import logging

logger = logging.getLogger(__name__)

class EnhancedAntiSpoofing:
    """
    Enhanced anti-spoofing system dengan multiple detection methods
    """
    
    def __init__(self):
        # MediaPipe Face Mesh untuk detailed face analysis
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Enhanced thresholds
        self.ear_threshold = 0.25
        self.ear_frames = 3
        self.blink_counter = 0
        self.total_blinks = 0
        self.last_blink_time = 0
        
        # Movement tracking with enhanced sensitivity
        self.movement_history = deque(maxlen=30)
        self.face_center_history = deque(maxlen=15)
        self.face_rotation_history = deque(maxlen=10)
        
        # Texture analysis parameters
        self.texture_threshold = 50
        self.quality_threshold = 30
        
        # Screen detection parameters
        self.screen_pattern_threshold = 0.01
        self.frequency_threshold = 0.05
        
        # Depth estimation parameters
        self.face_size_history = deque(maxlen=10)
        self.depth_variation_threshold = 0.02
        
        # Eye landmarks untuk blink detection
        self.left_eye_landmarks = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.right_eye_landmarks = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
        
        # Nose tip for depth analysis
        self.nose_tip_landmark = 1
        
        # Session tracking
        self.session_start_time = time.time()
        self.session_frames = 0
        
    def calculate_ear(self, eye_landmarks, face_landmarks):
        """
        Calculate Eye Aspect Ratio dengan improved accuracy
        """
        try:
            # Convert to numpy array for easier calculation
            points = np.array([[face_landmarks.landmark[i].x, face_landmarks.landmark[i].y] 
                              for i in eye_landmarks])
            
            # Enhanced EAR calculation dengan multiple points
            vertical_1 = np.linalg.norm(points[1] - points[5])
            vertical_2 = np.linalg.norm(points[2] - points[4])
            vertical_3 = np.linalg.norm(points[3] - points[6]) if len(points) > 6 else vertical_1
            horizontal = np.linalg.norm(points[0] - points[3])
            
            # Enhanced EAR dengan multiple vertical measurements
            ear = (vertical_1 + vertical_2 + vertical_3) / (3.0 * horizontal)
            return ear
        except:
            return 0.3  # Default nilai aman
    
    def detect_natural_blinks(self, frame):
        """
        Enhanced blink detection dengan natural timing validation
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        blink_detected = False
        current_time = time.time()
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Calculate EAR untuk kedua mata
                left_ear = self.calculate_ear(self.left_eye_landmarks, face_landmarks)
                right_ear = self.calculate_ear(self.right_eye_landmarks, face_landmarks)
                
                # Average EAR dengan weight adjustment
                ear = (left_ear + right_ear) / 2.0
                
                # Enhanced blink detection
                if ear < self.ear_threshold:
                    self.blink_counter += 1
                else:
                    if self.blink_counter >= self.ear_frames:
                        # Validate natural blink timing
                        time_since_last = current_time - self.last_blink_time
                        
                        # Natural blinks occur every 2-10 seconds
                        if time_since_last > 0.5 and time_since_last < 15:
                            self.total_blinks += 1
                            self.last_blink_time = current_time
                            blink_detected = True
                            logger.info(f"Natural blink detected. Total: {self.total_blinks}")
                    
                    self.blink_counter = 0
        
        return blink_detected, self.total_blinks
    
    def analyze_3d_depth(self, face_landmarks):
        """
        Analyze face depth untuk detect flat images
        """
        try:
            # Get nose tip coordinate (z-coordinate untuk depth)
            nose_tip = face_landmarks.landmark[self.nose_tip_landmark]
            
            # Calculate face size (distance between face corners)
            left_face = face_landmarks.landmark[234]  # Left face edge
            right_face = face_landmarks.landmark[454]  # Right face edge
            face_width = abs(right_face.x - left_face.x)
            
            # Track face size variations (real faces vary with movement)
            self.face_size_history.append(face_width)
            
            if len(self.face_size_history) >= 5:
                size_variance = np.var(list(self.face_size_history))
                
                # Real faces show depth variation with movement
                has_depth_variation = size_variance > self.depth_variation_threshold
                
                return has_depth_variation, size_variance
            
            return True, 0.0  # Assume real until we have enough data
            
        except:
            return False, 0.0
    
    def detect_screen_reflections(self, frame):
        """
        Detect screen reflections dan digital artifacts
        """
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect edges untuk find sharp digital boundaries
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # High edge density indicates digital artifacts
            is_digital = edge_density > 0.1
            
            # Analyze color saturation (photos often oversaturated)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            saturation = hsv[:, :, 1]
            avg_saturation = np.mean(saturation)
            
            # Oversaturated images indicate photos/screens
            oversaturated = avg_saturation > 150
            
            # Combine indicators
            screen_detected = is_digital or oversaturated
            
            return screen_detected, {
                'edge_density': edge_density,
                'saturation': avg_saturation,
                'is_digital': is_digital,
                'oversaturated': oversaturated
            }
            
        except:
            return False, {}
    
    def analyze_micro_movements(self, face_landmarks):
        """
        Analyze natural micro-movements yang ada pada orang hidup
        """
        try:
            # Track multiple facial points
            landmarks_to_track = [1, 33, 263, 61, 291]  # Nose, eyes, mouth corners
            current_positions = []
            
            for landmark_id in landmarks_to_track:
                lm = face_landmarks.landmark[landmark_id]
                current_positions.append([lm.x, lm.y])
            
            current_positions = np.array(current_positions)
            
            # Calculate center of tracked points
            face_center = np.mean(current_positions, axis=0)
            self.face_center_history.append(face_center)
            
            if len(self.face_center_history) >= 10:
                # Calculate micro-movement patterns
                positions = np.array(list(self.face_center_history))
                
                # Natural micro-movements (small, irregular)
                movement_variance = np.var(positions, axis=0)
                movement_magnitude = np.sum(movement_variance)
                
                # Check for natural irregularity (not too smooth, not too erratic)
                movement_diff = np.diff(positions, axis=0)
                movement_smoothness = np.var(np.linalg.norm(movement_diff, axis=1))
                
                # Real faces: some movement but not too smooth/erratic
                has_natural_movement = (0.0001 < movement_magnitude < 0.01 and 
                                      0.00001 < movement_smoothness < 0.001)
                
                return has_natural_movement, {
                    'movement_magnitude': movement_magnitude,
                    'movement_smoothness': movement_smoothness
                }
            
            return True, {}  # Assume natural until enough data
            
        except:
            return False, {}
    
    def detect_face_temperature_simulation(self, frame, face_region):
        """
        Simulate thermal analysis (detect living tissue characteristics)
        """
        try:
            if face_region is None or face_region.size == 0:
                return False, {}
            
            # Analyze color distribution (living skin has specific patterns)
            b, g, r = cv2.split(face_region)
            
            # Living skin shows specific RGB ratios
            avg_r = np.mean(r)
            avg_g = np.mean(g)
            avg_b = np.mean(b)
            
            # Calculate skin tone indicators
            rg_ratio = avg_r / (avg_g + 1)  # Avoid division by zero
            rb_ratio = avg_r / (avg_b + 1)
            
            # Living skin typically has 1.2 < rg_ratio < 1.8 and 1.1 < rb_ratio < 1.6
            has_living_skin_tone = (1.1 < rg_ratio < 2.0 and 1.05 < rb_ratio < 1.8)
            
            # Analyze texture uniformity (photos are too uniform)
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            texture_variance = np.var(gray_face)
            
            # Living skin has natural texture variance
            has_natural_texture = texture_variance > 100
            
            is_living = has_living_skin_tone and has_natural_texture
            
            return is_living, {
                'rg_ratio': rg_ratio,
                'rb_ratio': rb_ratio,
                'texture_variance': texture_variance,
                'has_living_skin_tone': has_living_skin_tone,
                'has_natural_texture': has_natural_texture
            }
            
        except:
            return True, {}  # Default to living if analysis fails
    
    def comprehensive_anti_spoofing_check(self, frame, face_region=None, duration_seconds=3):
        """
        Comprehensive anti-spoofing check dengan multiple layers
        """
        results = {
            'is_live': False,
            'confidence': 0.0,
            'security_level': 'high',
            'checks_passed': 0,
            'total_checks': 7,
            'details': {},
            'recommendations': []
        }
        
        try:
            self.session_frames += 1
            elapsed_time = time.time() - self.session_start_time
            
            # Minimum duration check
            if elapsed_time < duration_seconds:
                results['recommendations'].append(f"Continue for {duration_seconds - elapsed_time:.1f} more seconds")
                return results
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_mesh_results = self.face_mesh.process(rgb_frame)
            
            if not face_mesh_results.multi_face_landmarks:
                results['details']['error'] = "No face landmarks detected"
                return results
            
            face_landmarks = face_mesh_results.multi_face_landmarks[0]
            
            # Check 1: Natural Blinks (CRITICAL)
            blink_detected, total_blinks = self.detect_natural_blinks(frame)
            blink_passed = total_blinks >= 2
            results['details']['blinks'] = {
                'count': total_blinks,
                'natural_timing': blink_detected,
                'passed': blink_passed
            }
            if blink_passed:
                results['checks_passed'] += 1
            else:
                results['recommendations'].append("Please blink naturally at least 2 times")
            
            # Check 2: 3D Depth Analysis
            has_depth, depth_variance = self.analyze_3d_depth(face_landmarks)
            results['details']['depth'] = {
                'variance': depth_variance,
                'has_depth': has_depth,
                'passed': has_depth
            }
            if has_depth:
                results['checks_passed'] += 1
            else:
                results['recommendations'].append("Please move your head slightly forward/backward")
            
            # Check 3: Screen Detection
            screen_detected, screen_details = self.detect_screen_reflections(frame)
            screen_passed = not screen_detected
            results['details']['screen'] = {
                'detected': screen_detected,
                'details': screen_details,
                'passed': screen_passed
            }
            if screen_passed:
                results['checks_passed'] += 1
            else:
                results['recommendations'].append("Screen or photo detected - use your real face")
            
            # Check 4: Micro-movements
            has_micro_movement, movement_details = self.analyze_micro_movements(face_landmarks)
            results['details']['movement'] = {
                'natural': has_micro_movement,
                'details': movement_details,
                'passed': has_micro_movement
            }
            if has_micro_movement:
                results['checks_passed'] += 1
            else:
                results['recommendations'].append("Please move naturally - small head movements")
            
            # Check 5: Living Tissue Analysis
            is_living_tissue, tissue_details = self.detect_face_temperature_simulation(frame, face_region)
            results['details']['tissue'] = {
                'living': is_living_tissue,
                'details': tissue_details,
                'passed': is_living_tissue
            }
            if is_living_tissue:
                results['checks_passed'] += 1
            else:
                results['recommendations'].append("Skin tone analysis failed - ensure good lighting")
            
            # Check 6: Face Orientation Variety
            face_orientations = len(self.face_rotation_history)
            orientation_passed = face_orientations >= 3
            results['details']['orientation'] = {
                'variety_count': face_orientations,
                'passed': orientation_passed
            }
            if orientation_passed:
                results['checks_passed'] += 1
            else:
                results['recommendations'].append("Please turn your head slightly left/right")
            
            # Check 7: Temporal Consistency
            temporal_passed = self.session_frames >= 30  # At least 1 second at 30fps
            results['details']['temporal'] = {
                'frames_analyzed': self.session_frames,
                'passed': temporal_passed
            }
            if temporal_passed:
                results['checks_passed'] += 1
            
            # Calculate confidence based on checks passed
            results['confidence'] = results['checks_passed'] / results['total_checks']
            
            # Determine if live (require passing majority of checks)
            critical_checks_passed = (
                blink_passed and          # Must have natural blinks
                screen_passed and         # Must not be screen/photo
                is_living_tissue         # Must have living tissue characteristics
            )
            
            results['is_live'] = (
                critical_checks_passed and 
                results['checks_passed'] >= 5 and  # Pass at least 5/7 checks
                results['confidence'] >= 0.7
            )
            
            # Security level assessment
            if results['checks_passed'] >= 6:
                results['security_level'] = 'very_high'
            elif results['checks_passed'] >= 5:
                results['security_level'] = 'high'
            elif results['checks_passed'] >= 3:
                results['security_level'] = 'medium'
            else:
                results['security_level'] = 'low'
            
        except Exception as e:
            logger.error(f"Anti-spoofing error: {e}")
            results['details']['error'] = str(e)
        
        return results
    
    def reset_session(self):
        """
        Reset session untuk new attempt
        """
        self.blink_counter = 0
        self.total_blinks = 0
        self.last_blink_time = 0
        self.movement_history.clear()
        self.face_center_history.clear()
        self.face_rotation_history.clear()
        self.face_size_history.clear()
        self.session_start_time = time.time()
        self.session_frames = 0
        logger.info("Anti-spoofing session reset")
    
    def get_security_recommendations(self, failed_checks):
        """
        Get specific recommendations based on failed checks
        """
        recommendations = []
        
        if 'blinks' in failed_checks:
            recommendations.append("😊 Please blink naturally 2-3 times")
        if 'depth' in failed_checks:
            recommendations.append("📏 Move your head slightly closer/farther")
        if 'screen' in failed_checks:
            recommendations.append("🚫 Don't use photos or screens - show your real face")
        if 'movement' in failed_checks:
            recommendations.append("↔️ Move your head slightly left and right")
        if 'tissue' in failed_checks:
            recommendations.append("💡 Improve lighting for better face visibility")
        if 'orientation' in failed_checks:
            recommendations.append("🔄 Turn your head slightly in different directions")
        
        return recommendations