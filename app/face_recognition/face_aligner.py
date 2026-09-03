import cv2
import numpy as np
import dlib
import os
from imutils import face_utils
import math

class FaceAligner:
    """
    Face Alignment using Dlib landmarks for preprocessing
    """
    
    def __init__(self, predictor_path="app/static/models/shape_predictor_68_face_landmarks.dat"):
        self.predictor_path = predictor_path
        self.detector = dlib.get_frontal_face_detector()
        
        # Download predictor if not exists
        if not os.path.exists(predictor_path):
            print("Face landmarks predictor not found. Please download shape_predictor_68_face_landmarks.dat")
            print("From: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
            self.predictor = None
        else:
            self.predictor = dlib.shape_predictor(predictor_path)
    
    def align_face(self, image, face_width=256, left_eye_desired=(0.35, 0.35)):
        """
        Align face using eye landmarks
        """
        if self.predictor is None:
            return image
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect faces
        faces = self.detector(gray)
        
        if len(faces) == 0:
            return image
        
        # Use the first detected face
        face = faces[0]
        
        # Get facial landmarks
        landmarks = self.predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)
        
        # Extract eye coordinates
        left_eye_pts = landmarks[36:42]  # Left eye landmarks
        right_eye_pts = landmarks[42:48]  # Right eye landmarks
        
        # Compute eye centers
        left_eye_center = left_eye_pts.mean(axis=0).astype("int")
        right_eye_center = right_eye_pts.mean(axis=0).astype("int")
        
        # Compute angle between eyes
        dy = right_eye_center[1] - left_eye_center[1]
        dx = right_eye_center[0] - left_eye_center[0]
        angle = np.degrees(np.arctan2(dy, dx))
        
        # Compute desired right eye position
        right_eye_desired = (1.0 - left_eye_desired[0], left_eye_desired[1])
        
        # Determine scale
        dist = np.sqrt((dx ** 2) + (dy ** 2))
        desired_dist = (right_eye_desired[0] - left_eye_desired[0]) * face_width
        scale = desired_dist / dist
        
        # Compute center point between eyes
        eyes_center = ((left_eye_center[0] + right_eye_center[0]) // 2,
                      (left_eye_center[1] + right_eye_center[1]) // 2)
        
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(eyes_center, angle, scale)
        
        # Update translation component
        tx = face_width * 0.5
        ty = face_width * left_eye_desired[1]
        M[0, 2] += (tx - eyes_center[0])
        M[1, 2] += (ty - eyes_center[1])
        
        # Apply transformation
        aligned = cv2.warpAffine(image, M, (face_width, face_width),
                               flags=cv2.INTER_CUBIC)
        
        return aligned
    
    def detect_and_align_faces(self, image, face_width=256):
        """
        Detect and align all faces in image
        """
        if self.predictor is None:
            return []
        
        # Convert to grayscale for detection
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect faces
        faces = self.detector(gray)
        aligned_faces = []
        
        for face in faces:
            # Get facial landmarks
            landmarks = self.predictor(gray, face)
            landmarks = face_utils.shape_to_np(landmarks)
            
            # Extract face region
            (x, y, w, h) = face_utils.rect_to_bb(face)
            face_img = image[y:y+h, x:x+w]
            
            # Align face
            aligned_face = self.align_face(face_img, face_width)
            aligned_faces.append({
                'face': aligned_face,
                'landmarks': landmarks,
                'bbox': (x, y, w, h)
            })
        
        return aligned_faces
    
    def get_face_landmarks(self, image):
        """
        Get 68 facial landmarks
        """
        if self.predictor is None:
            return []
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect faces
        faces = self.detector(gray)
        landmarks_list = []
        
        for face in faces:
            landmarks = self.predictor(gray, face)
            landmarks = face_utils.shape_to_np(landmarks)
            landmarks_list.append(landmarks)
        
        return landmarks_list
    
    def draw_landmarks(self, image, landmarks):
        """
        Draw facial landmarks on image
        """
        output = image.copy()
        
        for (x, y) in landmarks:
            cv2.circle(output, (x, y), 2, (0, 255, 0), -1)
        
        return output
