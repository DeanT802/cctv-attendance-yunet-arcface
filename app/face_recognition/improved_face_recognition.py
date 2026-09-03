import cv2
import numpy as np
import face_recognition
import pickle
import os
from datetime import datetime
import dlib
import logging

# Setup logging untuk debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ImprovedCNNFaceRecognition:
    """
    Improved face recognition system with enhanced accuracy and security
    """
    
    def __init__(self, model_path='models/', confidence_threshold=0.45, strict_mode=True):
        self.model_path = model_path
        # CRITICAL: Lower threshold for better security (0.45 instead of 0.6)
        self.confidence_threshold = confidence_threshold
        self.strict_mode = strict_mode  # Enable strict verification mode
        
        # Multi-level thresholds for different scenarios
        self.thresholds = {
            'strict': 0.35,      # Very strict for high security
            'normal': 0.45,      # Normal threshold
            'relaxed': 0.55      # More permissive
        }
        
        # Initialize components if available
        self.face_aligner = FaceAligner() if FaceAligner else None
        self.anti_spoofing = AntiSpoofing() if AntiSpoofing else None
        self.augmenter = FaceAugmenter() if FaceAugmenter else None
        
        # Face detection and recognition
        try:
            self.face_detector = dlib.get_frontal_face_detector()
        except:
            self.face_detector = None
        
        # Model components
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Recognition history for verification
        self.recognition_history = {}
        
        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)
        
        # Load existing encodings if available
        self.load_encodings()
    
    def register_new_student(self, student_id, student_name, images_dir, min_images=5):
        """
        Enhanced student registration with quality control
        Returns: (success: bool, message: str)
        """
        try:
            # Process face images with quality control
            face_encodings = []
            valid_images = 0
            quality_scores = []
            
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
                    
                    # Image quality check
                    quality_score = self._assess_image_quality(image)
                    if quality_score < 0.5:  # Skip low quality images
                        logger.warning(f"Skipping low quality image: {filename}")
                        continue
                    
                    # Convert BGR to RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Extract face encodings with validation
                    face_locations = face_recognition.face_locations(rgb_image, model="cnn")
                    encodings = face_recognition.face_encodings(rgb_image, face_locations, model="large")
                    
                    if encodings and len(face_locations) == 1:  # Ensure only one face per image
                        face_encodings.extend(encodings)
                        quality_scores.append(quality_score)
                        valid_images += 1
                    else:
                        logger.warning(f"Invalid face count in {filename}: {len(face_locations)} faces")
            
            if valid_images < min_images:
                return False, f"Need at least {min_images} high-quality face images, found {valid_images}"
            
            # Calculate weighted average encoding based on quality scores
            if len(face_encodings) > 1:
                weights = np.array(quality_scores)
                weights = weights / np.sum(weights)  # Normalize weights
                avg_encoding = np.average(face_encodings, axis=0, weights=weights)
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
            
            logger.info(f"Successfully registered {student_name} with {valid_images} images")
            return True, f"Successfully registered {student_name} with {valid_images} high-quality face images"
            
        except Exception as e:
            logger.error(f"Error registering student: {str(e)}")
            return False, f"Error registering student: {str(e)}"
    
    def _assess_image_quality(self, image):
        """
        Assess image quality for face recognition
        Returns: quality score (0-1)
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Sharpness (Laplacian variance)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000.0, 1.0)  # Normalize
            
            # Brightness check
            mean_brightness = np.mean(gray)
            brightness_score = 1.0 - abs(mean_brightness - 128) / 128.0
            
            # Contrast check
            contrast = gray.std()
            contrast_score = min(contrast / 64.0, 1.0)
            
            # Combined quality score
            quality = (sharpness_score * 0.5 + brightness_score * 0.3 + contrast_score * 0.2)
            
            return quality
            
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return 0.0
    
    def recognize_face_enhanced(self, image_input, require_anti_spoofing=True, multi_verification=True):
        """
        Enhanced face recognition with multiple security layers
        Args:
            image_input: Can be image path (str) or image array (numpy.ndarray)
            require_anti_spoofing: Whether to require liveness detection
            multi_verification: Whether to require multiple verification attempts
        Returns: dict with enhanced recognition results
        """
        try:
            # Handle different input types
            if isinstance(image_input, str):
                if not os.path.exists(image_input):
                    return {'success': False, 'message': 'Image file not found'}
                image = cv2.imread(image_input)
                if image is None:
                    return {'success': False, 'message': 'Unable to load image file'}
            else:
                image = image_input
            
            # Convert to RGB if needed
            if len(image.shape) == 3 and image.shape[2] == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = image
            
            # Step 1: Anti-spoofing check (if required and available)
            liveness_result = {'is_live': True, 'confidence': 1.0}
            if require_anti_spoofing and self.anti_spoofing:
                liveness_result = self.anti_spoofing.comprehensive_liveness_check(image)
                if not liveness_result['is_live']:
                    return {
                        'success': False,
                        'message': 'Liveness detection failed - possible spoofing attempt',
                        'liveness': liveness_result
                    }
            
            # Step 2: Image quality assessment
            quality_score = self._assess_image_quality(image)
            if quality_score < 0.3:
                return {
                    'success': False,
                    'message': f'Image quality too low: {quality_score:.2f}',
                    'quality_score': quality_score
                }
            
            # Step 3: Face detection with CNN model for better accuracy
            face_locations = face_recognition.face_locations(rgb_image, model="cnn")
            if not face_locations:
                return {'success': False, 'message': 'No face detected in image'}
            
            if len(face_locations) > 1:
                return {'success': False, 'message': 'Multiple faces detected - please ensure only one person in frame'}
            
            # Step 4: Face encoding extraction with large model
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations, model="large")
            if not face_encodings:
                return {'success': False, 'message': 'Failed to extract face features'}
            
            # Step 5: Enhanced face comparison
            face_encoding = face_encodings[0]
            
            if not self.known_face_encodings:
                return {'success': False, 'message': 'No registered faces found'}
            
            # Calculate distances with enhanced metrics
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            
            # Find best matches (top 3)
            sorted_indices = np.argsort(face_distances)
            best_matches = []
            
            for i in range(min(3, len(sorted_indices))):
                idx = sorted_indices[i]
                distance = face_distances[idx]
                confidence = 1 - distance
                
                best_matches.append({
                    'index': idx,
                    'distance': distance,
                    'confidence': confidence,
                    'student_info': self.known_face_names[idx]
                })
            
            # Apply dynamic threshold based on quality and liveness
            dynamic_threshold = self._calculate_dynamic_threshold(quality_score, liveness_result['confidence'])
            
            best_match = best_matches[0]
            
            # Step 6: Enhanced verification logic
            if best_match['distance'] < dynamic_threshold:
                # Additional verification for strict mode
                if self.strict_mode and len(best_matches) > 1:
                    # Check if the second best match is too close (potential confusion)
                    second_best = best_matches[1]
                    distance_gap = second_best['distance'] - best_match['distance']
                    
                    if distance_gap < 0.1:  # If matches are too close, require higher confidence
                        if best_match['confidence'] < 0.7:
                            return {
                                'success': False,
                                'message': 'Ambiguous recognition - multiple similar matches found',
                                'best_matches': best_matches[:2],
                                'requires_manual_verification': True
                            }
                
                # Multi-verification check
                student_info = best_match['student_info']
                if multi_verification:
                    verification_result = self._multi_verification_check(student_info, best_match['confidence'])
                    if not verification_result['verified']:
                        return {
                            'success': False,
                            'message': verification_result['message'],
                            'requires_additional_verification': True
                        }
                
                # Parse student information
                name, student_id = student_info.rsplit('_', 1)
                
                # Log successful recognition
                self._log_recognition(student_id, best_match['confidence'], quality_score)
                
                return {
                    'success': True,
                    'student': {
                        'name': name,
                        'student_id': student_id,
                        'id': student_id
                    },
                    'confidence': best_match['confidence'],
                    'quality_score': quality_score,
                    'liveness': liveness_result,
                    'distance': best_match['distance'],
                    'dynamic_threshold': dynamic_threshold,
                    'verification_method': 'enhanced_cnn'
                }
            
            # Recognition failed
            return {
                'success': False,
                'message': f'Face not recognized (confidence: {best_match["confidence"]:.2f}, required: {1-dynamic_threshold:.2f})',
                'best_confidence': best_match['confidence'],
                'required_confidence': 1-dynamic_threshold,
                'quality_score': quality_score,
                'liveness': liveness_result
            }
            
        except Exception as e:
            logger.error(f"Recognition error: {str(e)}")
            return {'success': False, 'message': f"Recognition error: {str(e)}"}
    
    def _calculate_dynamic_threshold(self, quality_score, liveness_confidence):
        """
        Calculate dynamic threshold based on image quality and liveness confidence
        """
        base_threshold = self.confidence_threshold
        
        # Adjust threshold based on quality
        if quality_score < 0.5:
            base_threshold -= 0.05  # Stricter for low quality
        elif quality_score > 0.8:
            base_threshold += 0.03  # More lenient for high quality
        
        # Adjust threshold based on liveness confidence
        if liveness_confidence < 0.8:
            base_threshold -= 0.03  # Stricter for uncertain liveness
        
        # Ensure threshold stays within reasonable bounds
        return max(0.3, min(0.6, base_threshold))
    
    def _multi_verification_check(self, student_info, confidence):
        """
        Multi-verification check for enhanced security
        """
        current_time = datetime.now()
        
        # Check recognition history
        if student_info in self.recognition_history:
            last_recognition = self.recognition_history[student_info]
            time_diff = (current_time - last_recognition['timestamp']).total_seconds()
            
            # If same person recognized within 30 seconds, require higher confidence
            if time_diff < 30 and confidence < 0.75:
                return {
                    'verified': False,
                    'message': 'Recent recognition detected - higher confidence required'
                }
        
        # Update recognition history
        self.recognition_history[student_info] = {
            'timestamp': current_time,
            'confidence': confidence
        }
        
        return {'verified': True, 'message': 'Verification passed'}
    
    def _log_recognition(self, student_id, confidence, quality_score):
        """
        Log recognition attempt for analysis
        """
        logger.info(f"Recognition: Student {student_id}, Confidence: {confidence:.3f}, Quality: {quality_score:.3f}")
    
    def get_recognition_statistics(self):
        """
        Get statistics about recognition performance
        """
        return {
            'total_registered': len(self.known_face_names),
            'threshold_settings': self.thresholds,
            'current_threshold': self.confidence_threshold,
            'strict_mode': self.strict_mode,
            'recognition_history_count': len(self.recognition_history)
        }
    
    def update_threshold(self, new_threshold, mode='normal'):
        """
        Update recognition threshold dynamically
        """
        if mode in self.thresholds:
            self.confidence_threshold = self.thresholds[mode]
        else:
            self.confidence_threshold = new_threshold
        
        logger.info(f"Threshold updated to {self.confidence_threshold} (mode: {mode})")
    
    # Keep existing methods for compatibility
    def recognize_face(self, image_input):
        """Backward compatibility wrapper"""
        return self.recognize_face_enhanced(image_input, require_anti_spoofing=False, multi_verification=False)
    
    def save_encodings(self):
        """Save face encodings to file with metadata"""
        try:
            encodings_path = os.path.join(self.model_path, 'face_encodings_enhanced.pkl')
            data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names,
                'metadata': {
                    'version': '2.0',
                    'timestamp': datetime.now().isoformat(),
                    'threshold': self.confidence_threshold,
                    'strict_mode': self.strict_mode
                }
            }
            with open(encodings_path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Encodings saved: {len(self.known_face_encodings)} faces")
            return True
        except Exception as e:
            logger.error(f"Error saving encodings: {e}")
            return False
    
    def load_encodings(self):
        """Load face encodings from file with metadata"""
        try:
            # Try enhanced format first
            encodings_path = os.path.join(self.model_path, 'face_encodings_enhanced.pkl')
            if not os.path.exists(encodings_path):
                # Fallback to old format
                encodings_path = os.path.join(self.model_path, 'face_encodings.pkl')
            
            if os.path.exists(encodings_path):
                with open(encodings_path, 'rb') as f:
                    data = pickle.load(f)
                    
                    if isinstance(data, dict):
                        self.known_face_encodings = data.get('encodings', [])
                        self.known_face_names = data.get('names', [])
                        
                        # Load metadata if available
                        metadata = data.get('metadata', {})
                        if 'threshold' in metadata:
                            self.confidence_threshold = metadata['threshold']
                        if 'strict_mode' in metadata:
                            self.strict_mode = metadata['strict_mode']
                    else:
                        # Old format compatibility
                        self.known_face_encodings = data.get('encodings', [])
                        self.known_face_names = data.get('names', [])
                
                logger.info(f"Encodings loaded: {len(self.known_face_encodings)} faces")
                return True
        except Exception as e:
            logger.error(f"Error loading encodings: {e}")
            self.known_face_encodings = []
            self.known_face_names = []
            return False
    
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
            logger.info(f"Removed student {student_id} from recognition system")
            return True
        except Exception as e:
            logger.error(f"Error removing student: {e}")
            return False