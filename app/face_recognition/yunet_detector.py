"""
YuNet Face Detector - Ultra-fast and accurate face detection
Optimized for:
- Long distance detection (up to 6+ meters)
- Low resolution streams (substream/CCTV)
- Real-time performance (<10ms per frame)

Model: YuNet (OpenCV DNN)
Size: ~230KB (very lightweight)
Speed: ~2-5ms per frame on CPU
"""

import cv2
import numpy as np
import os

class YuNetFaceDetector:
    """
    YuNet face detector using OpenCV's DNN module
    Excellent for detecting small/distant faces in real-time
    """
    
    def __init__(self, model_path=None, conf_threshold=0.6, nms_threshold=0.3, top_k=5000):
        """
        Initialize YuNet detector
        
        Args:
            model_path: Path to YuNet ONNX model
            conf_threshold: Confidence threshold (lower = more detections, more false positives)
            nms_threshold: Non-maximum suppression threshold
            top_k: Maximum number of faces to detect
        """
        if model_path is None:
            # Default path
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            model_path = os.path.join(base_dir, 'models', 'face_detection_yunet_2023mar.onnx')
        
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        self.detector = None
        self.input_size = (320, 320)  # Default, will be updated based on image
        
        self._load_model()
    
    def _load_model(self):
        """Load YuNet model"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"YuNet model not found at: {self.model_path}")
        
        try:
            self.detector = cv2.FaceDetectorYN.create(
                self.model_path,
                "",
                self.input_size,
                self.conf_threshold,
                self.nms_threshold,
                self.top_k
            )
            print(f"[YuNet] ✅ Model loaded successfully from {self.model_path}")
            print(f"[YuNet] Settings: conf={self.conf_threshold}, nms={self.nms_threshold}, top_k={self.top_k}")
        except Exception as e:
            print(f"[YuNet] ❌ Failed to load model: {e}")
            raise
    
    def set_input_size(self, width, height):
        """Update input size for the detector"""
        self.input_size = (width, height)
        if self.detector:
            self.detector.setInputSize(self.input_size)
    
    def detect(self, image, scale_factor=1.0):
        """
        Detect faces in image
        
        Args:
            image: BGR image (OpenCV format)
            scale_factor: Scale factor for detection (1.0 = original size, >1.0 = upscale for small faces)
        
        Returns:
            List of face locations in (top, right, bottom, left) format (compatible with face_recognition)
        """
        if self.detector is None:
            print("[YuNet] ⚠️ Detector not initialized")
            return []
        
        try:
            h, w = image.shape[:2]
            
            # Optionally upscale image for better small face detection
            if scale_factor != 1.0:
                new_w = int(w * scale_factor)
                new_h = int(h * scale_factor)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                h, w = new_h, new_w
            
            # Update input size to match image
            self.set_input_size(w, h)
            
            # Detect faces
            _, faces = self.detector.detect(image)
            
            if faces is None:
                return []
            
            # Convert to face_recognition format (top, right, bottom, left)
            face_locations = []
            for face in faces:
                # YuNet returns: x, y, w, h, landmarks..., confidence
                x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                confidence = face[14] if len(face) > 14 else face[-1]
                
                # Scale back if we upscaled
                if scale_factor != 1.0:
                    x = int(x / scale_factor)
                    y = int(y / scale_factor)
                    fw = int(fw / scale_factor)
                    fh = int(fh / scale_factor)
                
                # Convert to (top, right, bottom, left) format
                top = y
                right = x + fw
                bottom = y + fh
                left = x
                
                face_locations.append((top, right, bottom, left))
                print(f"[YuNet] Face detected: conf={confidence:.2f}, box=({left},{top},{right},{bottom})")
            
            return face_locations
            
        except Exception as e:
            print(f"[YuNet] ❌ Detection error: {e}")
            return []
    
    def detect_with_landmarks(self, image, scale_factor=1.0):
        """
        Detect faces with 5-point landmarks
        
        Returns:
            List of dicts with 'box', 'confidence', and 'landmarks'
        """
        if self.detector is None:
            return []
        
        try:
            h, w = image.shape[:2]
            
            if scale_factor != 1.0:
                new_w = int(w * scale_factor)
                new_h = int(h * scale_factor)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                h, w = new_h, new_w
            
            self.set_input_size(w, h)
            _, faces = self.detector.detect(image)
            
            if faces is None:
                return []
            
            results = []
            for face in faces:
                x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
                
                # 5 landmarks: right_eye, left_eye, nose, right_mouth, left_mouth
                landmarks = {
                    'right_eye': (int(face[4]), int(face[5])),
                    'left_eye': (int(face[6]), int(face[7])),
                    'nose': (int(face[8]), int(face[9])),
                    'right_mouth': (int(face[10]), int(face[11])),
                    'left_mouth': (int(face[12]), int(face[13]))
                }
                
                confidence = face[14] if len(face) > 14 else face[-1]
                
                # Scale back if needed
                if scale_factor != 1.0:
                    x = int(x / scale_factor)
                    y = int(y / scale_factor)
                    fw = int(fw / scale_factor)
                    fh = int(fh / scale_factor)
                    landmarks = {k: (int(v[0]/scale_factor), int(v[1]/scale_factor)) 
                                for k, v in landmarks.items()}
                
                results.append({
                    'box': (y, x + fw, y + fh, x),  # top, right, bottom, left
                    'confidence': confidence,
                    'landmarks': landmarks
                })
            
            return results
            
        except Exception as e:
            print(f"[YuNet] ❌ Detection with landmarks error: {e}")
            return []
    
    def set_confidence_threshold(self, threshold):
        """Dynamically adjust confidence threshold"""
        self.conf_threshold = threshold
        if self.detector:
            self.detector.setScoreThreshold(threshold)
        print(f"[YuNet] Confidence threshold set to {threshold}")
    
    def detect_multi_scale(self, image, scales=[1.0, 1.5, 2.0]):
        """
        Detect faces at multiple scales for better small face detection
        Useful for detecting faces at 6+ meters distance
        
        Args:
            image: BGR image
            scales: List of scale factors to try
        
        Returns:
            Combined list of face locations (deduplicated)
        """
        all_faces = []
        
        for scale in scales:
            faces = self.detect(image, scale_factor=scale)
            all_faces.extend(faces)
        
        # Remove duplicates (faces that overlap significantly)
        if len(all_faces) <= 1:
            return all_faces
        
        # Non-maximum suppression
        unique_faces = self._nms_faces(all_faces)
        return unique_faces
    
    def _nms_faces(self, faces, iou_threshold=0.5):
        """Remove overlapping face detections"""
        if not faces:
            return []
        
        # Convert to numpy array for easier computation
        boxes = np.array([[f[3], f[0], f[1], f[2]] for f in faces])  # x1, y1, x2, y2
        
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = np.arange(len(boxes))
        
        keep = []
        while len(order) > 0:
            i = order[0]
            keep.append(i)
            
            if len(order) == 1:
                break
            
            # Compute IoU
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            
            intersection = w * h
            iou = intersection / (areas[i] + areas[order[1:]] - intersection)
            
            # Keep boxes with IoU less than threshold
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return [faces[i] for i in keep]


# Singleton instance for reuse
_yunet_instance = None

def get_yunet_detector(conf_threshold=0.5):
    """Get or create YuNet detector instance"""
    global _yunet_instance
    if _yunet_instance is None:
        try:
            _yunet_instance = YuNetFaceDetector(conf_threshold=conf_threshold)
        except Exception as e:
            print(f"[YuNet] Failed to initialize: {e}")
            return None
    return _yunet_instance


# Quick test
if __name__ == "__main__":
    import time
    
    # Test with webcam
    detector = YuNetFaceDetector(conf_threshold=0.5)
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        start = time.time()
        faces = detector.detect(frame)
        elapsed = (time.time() - start) * 1000
        
        # Draw faces
        for (top, right, bottom, left) in faces:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        cv2.putText(frame, f"YuNet: {elapsed:.1f}ms, Faces: {len(faces)}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("YuNet Face Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
