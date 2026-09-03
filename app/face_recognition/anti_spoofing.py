import cv2
import numpy as np
import mediapipe as mp
import time
from collections import deque
import math

class AntiSpoofing:
    """
    Advanced anti-spoofing and liveness detection system
    """
    
    def __init__(self):
        # MediaPipe Face Mesh for detailed face analysis
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Eye aspect ratio tracking for blink detection
        self.ear_threshold = 0.25
        self.ear_frames = 3
        self.blink_counter = 0
        self.total_blinks = 0
        
        # Movement tracking
        self.movement_history = deque(maxlen=30)
        self.face_center_history = deque(maxlen=10)
        
        # Texture analysis parameters
        self.texture_threshold = 50
        
        # Eye landmarks for blink detection
        self.left_eye_landmarks = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.right_eye_landmarks = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    
    def calculate_ear(self, eye_landmarks, face_landmarks):
        """
        Calculate Eye Aspect Ratio for blink detection
        """
        # Convert to numpy array for easier calculation
        points = np.array([[face_landmarks.landmark[i].x, face_landmarks.landmark[i].y] 
                          for i in eye_landmarks])
        
        # Calculate distances
        vertical_1 = np.linalg.norm(points[1] - points[5])
        vertical_2 = np.linalg.norm(points[2] - points[4])
        horizontal = np.linalg.norm(points[0] - points[3])
        
        # Eye aspect ratio
        ear = (vertical_1 + vertical_2) / (2.0 * horizontal)
        return ear
    
    def detect_blinks(self, frame):
        """
        Detect blinks in real-time
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        blink_detected = False
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Calculate EAR for both eyes
                left_ear = self.calculate_ear(self.left_eye_landmarks, face_landmarks)
                right_ear = self.calculate_ear(self.right_eye_landmarks, face_landmarks)
                
                # Average EAR
                ear = (left_ear + right_ear) / 2.0
                
                # Check if blink occurred
                if ear < self.ear_threshold:
                    self.blink_counter += 1
                else:
                    if self.blink_counter >= self.ear_frames:
                        self.total_blinks += 1
                        blink_detected = True
                    self.blink_counter = 0
        
        return blink_detected, self.total_blinks
    
    def analyze_texture(self, face_region):
        """
        Analyze texture patterns to detect printed photos or screens
        """
        # Convert to grayscale
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance (focus measure)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate Local Binary Pattern variance
        lbp = self.calculate_lbp(gray)
        lbp_var = np.var(lbp)
        
        # Frequency domain analysis
        freq_score = self.analyze_frequency_domain(gray)
        
        # Combine scores
        texture_score = (laplacian_var + lbp_var + freq_score) / 3
        
        is_real = texture_score > self.texture_threshold
        return is_real, texture_score
    
    def calculate_lbp(self, gray_image, radius=1, n_points=8):
        """
        Calculate Local Binary Pattern
        """
        lbp = np.zeros_like(gray_image)
        
        for i in range(radius, gray_image.shape[0] - radius):
            for j in range(radius, gray_image.shape[1] - radius):
                center = gray_image[i, j]
                binary_string = ""
                
                for p in range(n_points):
                    angle = 2 * np.pi * p / n_points
                    x = int(i + radius * np.cos(angle))
                    y = int(j + radius * np.sin(angle))
                    
                    if gray_image[x, y] >= center:
                        binary_string += "1"
                    else:
                        binary_string += "0"
                
                lbp[i, j] = int(binary_string, 2)
        
        return lbp
    
    def analyze_frequency_domain(self, gray_image):
        """
        Analyze frequency domain characteristics
        """
        # Apply FFT
        f_transform = np.fft.fft2(gray_image)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.log(np.abs(f_shift) + 1)
        
        # Calculate high frequency content
        h, w = magnitude_spectrum.shape
        center_h, center_w = h // 2, w // 2
        
        # Define high frequency region (outer 30% of spectrum)
        mask = np.zeros((h, w))
        outer_radius = min(h, w) // 3
        inner_radius = outer_radius // 2
        
        y, x = np.ogrid[:h, :w]
        distance = np.sqrt((x - center_w)**2 + (y - center_h)**2)
        mask[(distance > inner_radius) & (distance < outer_radius)] = 1
        
        high_freq_energy = np.sum(magnitude_spectrum * mask)
        total_energy = np.sum(magnitude_spectrum)
        
        freq_ratio = high_freq_energy / total_energy if total_energy > 0 else 0
        return freq_ratio * 1000  # Scale for better comparison
    
    def detect_movement(self, frame):
        """
        Detect natural head movement
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        movement_score = 0
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Get face center
                landmarks = face_landmarks.landmark
                face_center_x = np.mean([lm.x for lm in landmarks])
                face_center_y = np.mean([lm.y for lm in landmarks])
                
                current_center = (face_center_x, face_center_y)
                self.face_center_history.append(current_center)
                
                # Calculate movement variance
                if len(self.face_center_history) >= 5:
                    centers = np.array(self.face_center_history)
                    movement_variance = np.var(centers, axis=0)
                    movement_score = np.sum(movement_variance)
        
        self.movement_history.append(movement_score)
        
        # Calculate overall movement score
        if len(self.movement_history) >= 10:
            avg_movement = np.mean(list(self.movement_history))
            return avg_movement > 0.001, avg_movement
        
        return False, movement_score
    
    def detect_screen_patterns(self, frame):
        """
        Detect screen patterns (moiré patterns, pixel structure)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply FFT to detect regular patterns
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # Look for peaks in frequency domain (indicating regular patterns)
        # Threshold to find significant peaks
        threshold = np.mean(magnitude_spectrum) + 2 * np.std(magnitude_spectrum)
        peaks = magnitude_spectrum > threshold
        
        # Count peaks (more peaks = more likely to be a screen)
        peak_count = np.sum(peaks)
        total_pixels = magnitude_spectrum.size
        peak_ratio = peak_count / total_pixels
        
        # Screen detected if too many regular patterns
        is_screen = peak_ratio > 0.01
        
        return is_screen, peak_ratio
    
    def comprehensive_liveness_check(self, frame, face_region=None):
        """
        Comprehensive liveness detection combining multiple methods
        """
        results = {
            'is_live': False,
            'confidence': 0.0,
            'blink_detected': False,
            'blink_count': 0,
            'movement_detected': False,
            'texture_real': False,
            'no_screen_patterns': True,
            'scores': {}
        }
        
        try:
            # Blink detection
            blink_detected, total_blinks = self.detect_blinks(frame)
            results['blink_detected'] = blink_detected
            results['blink_count'] = total_blinks
            
            # Movement detection
            movement_detected, movement_score = self.detect_movement(frame)
            results['movement_detected'] = movement_detected
            results['scores']['movement'] = movement_score
            
            # Texture analysis (if face region provided)
            if face_region is not None:
                texture_real, texture_score = self.analyze_texture(face_region)
                results['texture_real'] = texture_real
                results['scores']['texture'] = texture_score
            else:
                results['texture_real'] = True  # Assume real if no face region
                results['scores']['texture'] = self.texture_threshold + 10
            
            # Screen pattern detection
            no_screen, screen_score = self.detect_screen_patterns(frame)
            results['no_screen_patterns'] = not no_screen
            results['scores']['screen'] = screen_score
            
            # Calculate overall confidence
            confidence_factors = []
            
            # Blink factor (more blinks = more confidence)
            blink_factor = min(total_blinks / 3.0, 1.0)  # Max confidence at 3 blinks
            confidence_factors.append(blink_factor * 0.3)
            
            # Movement factor
            movement_factor = 1.0 if movement_detected else 0.0
            confidence_factors.append(movement_factor * 0.25)
            
            # Texture factor
            texture_factor = 1.0 if results['texture_real'] else 0.0
            confidence_factors.append(texture_factor * 0.25)
            
            # Screen pattern factor
            screen_factor = 1.0 if results['no_screen_patterns'] else 0.0
            confidence_factors.append(screen_factor * 0.2)
            
            # Overall confidence
            results['confidence'] = sum(confidence_factors)
            
            # Determine if live (require multiple positive indicators)
            live_indicators = sum([
                total_blinks >= 2,  # At least 2 blinks
                movement_detected,  # Natural movement
                results['texture_real'],  # Real texture
                results['no_screen_patterns']  # No screen patterns
            ])
            
            results['is_live'] = live_indicators >= 3 and results['confidence'] > 0.7
            
        except Exception as e:
            print(f"Error in liveness detection: {e}")
        
        return results
    
    def reset_counters(self):
        """
        Reset all counters for new session
        """
        self.blink_counter = 0
        self.total_blinks = 0
        self.movement_history.clear()
        self.face_center_history.clear()
