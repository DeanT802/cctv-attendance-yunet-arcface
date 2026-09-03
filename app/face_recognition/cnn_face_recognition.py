import cv2
import numpy as np
import face_recognition
import pickle
import os
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Dropout, Conv2D, MaxPooling2D, Flatten, Input
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import dlib

from .face_aligner import FaceAligner
from .anti_spoofing import AntiSpoofing
from .face_augmenter import FaceAugmenter

class CNNFaceRecognition:
    """
    Advanced CNN-based face recognition system with anti-spoofing
    """
    
    def __init__(self, model_path='models/', confidence_threshold=0.6):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        
        # Initialize components
        self.face_aligner = FaceAligner()
        self.anti_spoofing = AntiSpoofing()
        self.augmenter = FaceAugmenter()
        
        # Face detection and recognition
        self.face_detector = dlib.get_frontal_face_detector()
        
        # Model components
        self.cnn_model = None
        self.label_encoder = None
        self.known_face_encodings = []
        self.known_face_names = []
        
        # Ensure model directory exists
        os.makedirs(model_path, exist_ok=True)
        
        # Load existing model if available
        self.load_model()
    
    def create_cnn_model(self, num_classes, input_shape=(128, 128, 3)):
        """
        Create CNN model for face recognition
        """
        model = Sequential([
            # First Convolutional Block
            Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
            MaxPooling2D((2, 2)),
            
            # Second Convolutional Block
            Conv2D(64, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            
            # Third Convolutional Block
            Conv2D(128, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            
            # Fourth Convolutional Block
            Conv2D(256, (3, 3), activation='relu'),
            MaxPooling2D((2, 2)),
            
            # Flatten and Dense layers
            Flatten(),
            Dense(512, activation='relu'),
            Dropout(0.5),
            Dense(256, activation='relu'),
            Dropout(0.5),
            Dense(num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def preprocess_face_for_cnn(self, face_image):
        """
        Preprocess face image for CNN input
        """
        # Resize to model input size
        face_resized = cv2.resize(face_image, (128, 128))
        
        # Normalize pixel values
        face_normalized = face_resized.astype('float32') / 255.0
        
        # Add batch dimension
        face_batch = np.expand_dims(face_normalized, axis=0)
        
        return face_batch
    
    def extract_face_from_frame(self, frame):
        """
        Extract and align face from frame
        """
        # Detect faces
        faces = self.face_detector(frame)
        
        if len(faces) == 0:
            return None, None
        
        # Use the largest face
        face = max(faces, key=lambda rect: rect.width() * rect.height())
        
        # Extract face region
        x, y, w, h = face.left(), face.top(), face.width(), face.height()
        face_region = frame[y:y+h, x:x+w]
        
        # Align face
        aligned_faces = self.face_aligner.detect_and_align_faces(frame)
        
        if aligned_faces:
            return aligned_faces[0], face_region
        else:
            # Fallback to unaligned face
            return cv2.resize(face_region, (128, 128)), face_region
    
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
                    face_locations = face_recognition.face_locations(rgb_image)
                    encodings = face_recognition.face_encodings(rgb_image, face_locations)
                    
                    if encodings:
                        face_encodings.extend(encodings)
                        valid_images += 1
            
            if valid_images < 1:
                return False, "No valid face images found"
            
            # Calculate average encoding
            if len(face_encodings) > 1:
                avg_encoding = np.mean(face_encodings, axis=0)
            else:
                avg_encoding = face_encodings[0]
            
            # Store in memory (not database - database will be handled by main app)
            self.known_face_encodings.append(avg_encoding)
            self.known_face_names.append(f"{student_name}_{student_id}")
            
            # Save to file for persistence
            self.save_encodings()
            
            return True, f"Successfully registered {student_name} with {valid_images} face images"
            
        except Exception as e:
            return False, f"Error registering student: {str(e)}"
    
    def load_known_faces(self):
        """
        Load all registered faces from database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, face_encoding FROM students")
            results = cursor.fetchall()
            
            self.known_face_names = []
            self.known_face_encodings = []
            
            for name, encoding_blob in results:
                try:
                    encoding = pickle.loads(encoding_blob)
                    self.known_face_names.append(name)
                    self.known_face_encodings.append(encoding)
                except:
                    print(f"Error loading encoding for {name}")
            
            conn.close()
            print(f"Loaded {len(self.known_face_names)} known faces")
            
        except Exception as e:
            print(f"Error loading known faces: {e}")
    
    def recognize_face_with_antispoofing(self, frame):
        """
        Recognize face with anti-spoofing validation
        """
        result = {
            'name': 'Unknown',
            'confidence': 0.0,
            'is_live': False,
            'liveness_details': {},
            'face_detected': False,
            'anti_spoofing_passed': False
        }
        
        try:
            # Extract face from frame
            face, face_region = self.extract_face_from_frame(frame)
            
            if face is None:
                return result
            
            result['face_detected'] = True
            
            # Anti-spoofing check
            liveness_results = self.anti_spoofing.comprehensive_liveness_check(frame, face_region)
            result['is_live'] = liveness_results['is_live']
            result['liveness_details'] = liveness_results
            result['anti_spoofing_passed'] = liveness_results['is_live']
            
            # If anti-spoofing fails, return early
            if not liveness_results['is_live']:
                return result
            
            # Face recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_frame)
            
            if face_encodings and self.known_face_encodings:
                face_encoding = face_encodings[0]
                
                # Compare with known faces
                distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(distances)
                
                if distances[best_match_index] < (1 - self.confidence_threshold):
                    result['name'] = self.known_face_names[best_match_index]
                    result['confidence'] = 1 - distances[best_match_index]
            
        except Exception as e:
            print(f"Error in face recognition: {e}")
        
        return result
    
    def recognize_face(self, image_path):
        """
        Recognize face from image file path
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return {
                    'success': False,
                    'message': 'Could not load image'
                }
            
            # Load known faces if not already loaded
            if not self.known_face_encodings:
                self.load_known_faces()
            
            # Convert to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Find face encodings
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            if not face_encodings:
                return {
                    'success': False,
                    'message': 'No face detected in image'
                }
            
            if not self.known_face_encodings:
                return {
                    'success': False,
                    'message': 'No registered faces found in database'
                }
            
            # Compare with known faces
            face_encoding = face_encodings[0]
            distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(distances)
            confidence = 1 - distances[best_match_index]
            
            if confidence > self.confidence_threshold:
                # Get student info from database
                student_name = self.known_face_names[best_match_index]
                student_info = self.get_student_by_name(student_name)
                
                if student_info:
                    return {
                        'success': True,
                        'student': {
                            'student_id': student_info.get('id', ''),
                            'name': student_info.get('name', student_name),
                            'nama': student_info.get('name', student_name)  # For compatibility
                        },
                        'confidence': confidence,
                        'timestamp': datetime.now().strftime('%H:%M:%S')
                    }
            
            return {
                'success': False,
                'message': f'Face tidak dikenali (confidence: {confidence:.2f})'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error during recognition: {str(e)}'
            }
    
    def get_student_by_name(self, name):
        """
        Get student information by name from database
        """
        try:
            from app.database import Database
            db = Database()
            db.connect()
            
            query = "SELECT id, name, student_id FROM students WHERE name = %s"
            result = db.execute_query(query, (name,))
            
            if result:
                return {
                    'id': result[0]['id'],
                    'name': result[0]['name'],
                    'student_id': result[0]['student_id']
                }
            
            return None
            
        except Exception as e:
            print(f"Error getting student info: {e}")
            return None
    
    def mark_attendance_with_face(self, course_id, meeting_number, session_number):
        """
        Mark attendance using face recognition
        """
        # Initialize camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return False, "Could not access camera"
        
        # Load known faces
        self.load_known_faces()
        
        print("Face recognition attendance started. Press 'q' to quit.")
        
        # Reset anti-spoofing counters
        self.anti_spoofing.reset_counters()
        
        recognition_attempts = 0
        max_attempts = 100  # Maximum frames to try
        
        while recognition_attempts < max_attempts:
            ret, frame = cap.read()
            if not ret:
                break
            
            recognition_attempts += 1
            
            # Recognize face
            result = self.recognize_face_with_antispoofing(frame)
            
            # Display frame with results
            display_frame = frame.copy()
            
            # Draw face detection box if face detected
            if result['face_detected']:
                faces = self.face_detector(frame)
                for face in faces:
                    x, y, w, h = face.left(), face.top(), face.width(), face.height()
                    
                    # Color based on liveness
                    color = (0, 255, 0) if result['is_live'] else (0, 0, 255)
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), color, 2)
                    
                    # Display name and confidence
                    if result['anti_spoofing_passed'] and result['name'] != 'Unknown':
                        label = f"{result['name']} ({result['confidence']:.2f})"
                        cv2.putText(display_frame, label, (x, y-10), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Display liveness status
            liveness_text = "LIVE" if result['is_live'] else "NOT LIVE"
            liveness_color = (0, 255, 0) if result['is_live'] else (0, 0, 255)
            cv2.putText(display_frame, liveness_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, liveness_color, 2)
            
            # Display blink count
            blink_text = f"Blinks: {result['liveness_details'].get('blink_count', 0)}"
            cv2.putText(display_frame, blink_text, (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Face Recognition Attendance', display_frame)
            
            # Check for successful recognition
            if (result['anti_spoofing_passed'] and 
                result['name'] != 'Unknown' and 
                result['confidence'] > self.confidence_threshold):
                
                # Mark attendance in database
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    # Get student ID
                    cursor.execute("SELECT student_id FROM students WHERE name = ?", (result['name'],))
                    student_data = cursor.fetchone()
                    
                    if student_data:
                        student_id = student_data[0]
                        
                        # Mark attendance
                        cursor.execute("""
                            INSERT OR REPLACE INTO attendance_new 
                            (student_id, course_id, meeting_number, session_number, 
                             attendance_time, attendance_method)
                            VALUES (?, ?, ?, ?, ?, 'face_recognition')
                        """, (student_id, course_id, meeting_number, session_number, datetime.now()))
                        
                        conn.commit()
                        conn.close()
                        
                        cap.release()
                        cv2.destroyAllWindows()
                        
                        return True, f"Attendance marked for {result['name']}"
                
                except Exception as e:
                    print(f"Database error: {e}")
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        return False, "Face recognition failed or timeout"
    
    def save_model(self):
        """
        Save trained model and encodings
        """
        try:
            if self.cnn_model:
                self.cnn_model.save(os.path.join(self.model_path, 'cnn_face_model.h5'))
            
            if self.label_encoder:
                with open(os.path.join(self.model_path, 'label_encoder.pkl'), 'wb') as f:
                    pickle.dump(self.label_encoder, f)
            
            # Save face encodings
            with open(os.path.join(self.model_path, 'face_encodings.pkl'), 'wb') as f:
                pickle.dump({
                    'encodings': self.known_face_encodings,
                    'names': self.known_face_names
                }, f)
            
            print("Model saved successfully")
            
        except Exception as e:
            print(f"Error saving model: {e}")
    
    def load_model(self):
        """
        Load trained model and encodings
        """
        try:
            # Load CNN model
            model_file = os.path.join(self.model_path, 'cnn_face_model.h5')
            if os.path.exists(model_file):
                self.cnn_model = tf.keras.models.load_model(model_file)
            
            # Load label encoder
            encoder_file = os.path.join(self.model_path, 'label_encoder.pkl')
            if os.path.exists(encoder_file):
                with open(encoder_file, 'rb') as f:
                    self.label_encoder = pickle.load(f)
            
            # Load face encodings
            encodings_file = os.path.join(self.model_path, 'face_encodings.pkl')
            if os.path.exists(encodings_file):
                with open(encodings_file, 'rb') as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data['encodings']
                    self.known_face_names = data['names']
            else:
                # Load from database if file doesn't exist
                self.load_known_faces()
            
            print("Model loaded successfully")
            
        except Exception as e:
            print(f"Error loading model: {e}")
    
    def get_attendance_statistics(self, course_id):
        """
        Get attendance statistics for face recognition
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total students
            cursor.execute("SELECT COUNT(*) FROM students")
            total_students = cursor.fetchone()[0]
            
            # Face recognition attendances
            cursor.execute("""
                SELECT COUNT(*) FROM attendance_new 
                WHERE course_id = ? AND attendance_method = 'face_recognition'
            """, (course_id,))
            face_attendances = cursor.fetchone()[0]
            
            # Unique students with face recognition
            cursor.execute("""
                SELECT COUNT(DISTINCT student_id) FROM attendance_new 
                WHERE course_id = ? AND attendance_method = 'face_recognition'
            """, (course_id,))
            unique_face_students = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_students': total_students,
                'face_attendances': face_attendances,
                'unique_face_students': unique_face_students,
                'face_adoption_rate': (unique_face_students / total_students * 100) if total_students > 0 else 0
            }
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return None
