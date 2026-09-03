import os
import sys
import pickle
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import cv2
import numpy as np

# Optional components (keep compatibility with existing architecture)
try:
    from .face_aligner import FaceAligner
except ImportError:
    FaceAligner = None

try:
    from .anti_spoofing import AntiSpoofing
except ImportError:
    AntiSpoofing = None

try:
    from .face_augmenter import FaceAugmenter
except ImportError:
    FaceAugmenter = None

try:
    from .yunet_detector import get_yunet_detector
    YUNET_AVAILABLE = True
except ImportError:
    YUNET_AVAILABLE = False


class CNNFaceRecognition:
    """
    ArcFace-based recognition engine with backward-compatible class name.
    This allows full migration from dlib/face_recognition without breaking routes.
    """

    def __init__(self, model_path='models/', confidence_threshold=0.45, 
                 use_clahe=True, use_yunet=True, use_arcface=True):
        self.model_path = model_path
        os.makedirs(model_path, exist_ok=True)

        self.use_clahe = use_clahe
        self.use_yunet = use_yunet
        self.use_arcface = use_arcface

        # Feature switches / thresholds from env
        self.distance_threshold = self._env_float(
            'FACE_MATCH_DISTANCE_THRESHOLD', confidence_threshold, min_value=0.20, max_value=0.80
        )
        self.min_confidence_large = self._env_float('FACE_MIN_CONF_LARGE', 0.60, min_value=0.30, max_value=0.99)
        self.min_confidence_medium = self._env_float('FACE_MIN_CONF_MEDIUM', 0.55, min_value=0.30, max_value=0.99)
        self.min_confidence_small = self._env_float('FACE_MIN_CONF_SMALL', 0.48, min_value=0.25, max_value=0.99)

        # Keep monotonic thresholds: large >= medium >= small
        self.min_confidence_large = max(self.min_confidence_large, self.min_confidence_medium, self.min_confidence_small)
        self.min_confidence_small = min(self.min_confidence_large, self.min_confidence_medium, self.min_confidence_small)
        self.min_confidence_medium = min(self.min_confidence_large, max(self.min_confidence_medium, self.min_confidence_small))

        # ArcFace embeddings store path (new store, does not overwrite dlib encodings)
        self.embeddings_file = os.getenv('ARCFACE_EMBEDDINGS_FILE', 'arcface_embeddings.pkl')
        self.embeddings_path = os.path.join(self.model_path, self.embeddings_file)

        # Keep old property names for compatibility with diagnostics/routes
        self.known_face_encodings: List[np.ndarray] = []
        self.known_face_names: List[str] = []

        # Optional helpers
        self.face_aligner = FaceAligner() if FaceAligner else None
        self.anti_spoofing = AntiSpoofing() if AntiSpoofing else None
        self.augmenter = FaceAugmenter() if FaceAugmenter else None
        self._dll_dir_handles = []

        self.yunet_detector = None
        if YUNET_AVAILABLE:
            try:
                self.yunet_detector = get_yunet_detector(conf_threshold=0.35)
                print('[ArcFace] ✅ YuNet detector initialized')
            except Exception as e:
                print(f'[ArcFace] ⚠️ YuNet init failed: {e}')

        self.arcface_app = self._init_arcface_app()
        self.load_encodings()

        print(
            '[ArcFace] Config: '
            f'distance<{self.distance_threshold:.3f}, '
            f'min_conf(large/medium/small)='
            f'{self.min_confidence_large:.2f}/{self.min_confidence_medium:.2f}/{self.min_confidence_small:.2f}, '
            f'embeddings={self.embeddings_file}'
        )

    @staticmethod
    def _env_float(name, default, min_value=None, max_value=None):
        value = os.getenv(name)
        if value is None or str(value).strip() == '':
            result = default
        else:
            try:
                result = float(value)
            except (TypeError, ValueError):
                result = default

        if min_value is not None:
            result = max(min_value, result)
        if max_value is not None:
            result = min(max_value, result)
        return result

    def _init_arcface_app(self):
        import insightface
        import onnxruntime as ort
    
        self._configure_windows_cuda_dll_paths()
    
        try:
            ort.preload_dlls(directory="")
            ort.print_debug_info()
        except Exception as e:
            print(f"[ArcFace] preload_dlls skipped/failed: {e}")
    
        available = ort.get_available_providers()
    
        preferred = [
            "CUDAExecutionProvider",
            "DmlExecutionProvider",
            "CPUExecutionProvider",
        ]
    
        providers = [p for p in preferred if p in available]
    
        cuda_options = {
            "device_id": 0,
            "arena_extend_strategy": "kNextPowerOfTwo",
            "gpu_mem_limit": 6 * 1024 * 1024 * 1024,
            "cudnn_conv_algo_search": "EXHAUSTIVE",
            "do_copy_in_default_stream": True,
        }
    
        final_providers = []
        for p in providers:
            if p == "CUDAExecutionProvider":
                final_providers.append((p, cuda_options))
            else:
                final_providers.append(p)
    
        print(f"[ArcFace] ONNX available providers: {available}")
        print(f"[ArcFace] ONNX selected providers: {final_providers}")
    
        app = insightface.app.FaceAnalysis(
            name="buffalo_l",
            providers=final_providers
        )
    
        app.prepare(ctx_id=0, det_size=(640, 640))
    
        print("[ArcFace] InsightFace initialized")
        return app

    def _configure_windows_cuda_dll_paths(self):
        import os
        import sys
        import site

        candidate_roots = site.getsitepackages() + [os.path.dirname(sys.executable)]

        dll_dirs = [
            r"nvidia\cuda_runtime\bin",
            r"nvidia\cuda_nvrtc\bin",
            r"nvidia\cublas\bin",
            r"nvidia\cufft\bin",
            r"nvidia\curand\bin",
            r"nvidia\cudnn\bin",
        ]

        added = []

        for root in candidate_roots:
            for rel in dll_dirs:
                path = os.path.join(root, rel)
                if os.path.isdir(path):
                    os.add_dll_directory(path)
                    os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
                    added.append(path)

        print(f"[ArcFace] Added DLL search paths: {added}")

    @staticmethod
    def _normalize_embedding(emb):
        emb = np.asarray(emb, dtype=np.float32)
        norm = np.linalg.norm(emb)
        if norm <= 1e-12:
            return emb
        return emb / norm

    def _get_adaptive_min_confidence(self, face_size_ratio):
        if face_size_ratio > 0.15:
            return self.min_confidence_large, 'large/close'
        if face_size_ratio > 0.08:
            return self.min_confidence_medium, 'medium'
        return self.min_confidence_small, 'small/far'

    def _face_size_ratio(self, face_box: Tuple[int, int, int, int], image_shape):
        top, right, bottom, left = face_box
        face_w = max(0, right - left)
        face_h = max(0, bottom - top)
        area = face_w * face_h
        image_area = max(1, image_shape[0] * image_shape[1])
        return area / image_area

    def _apply_clahe_lab(self, bgr_image):
        """Apply CLAHE on LAB L-channel and return enhanced BGR image."""
        try:
            lab_img = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
            l_channel, a_channel, b_channel = cv2.split(lab_img)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_l = clahe.apply(l_channel)
            enhanced_lab = cv2.merge((enhanced_l, a_channel, b_channel))
            return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        except Exception as e:
            print(f"[ArcFace] CLAHE preprocessing failed: {e}")
            return bgr_image

    @staticmethod
    def _clip_box_xyxy(left, top, right, bottom, image_shape):
        """Clip x1,y1,x2,y2 box to image boundaries."""
        height, width = image_shape[:2]
        left = int(max(0, min(width - 1, left)))
        right = int(max(0, min(width - 1, right)))
        top = int(max(0, min(height - 1, top)))
        bottom = int(max(0, min(height - 1, bottom)))
        if right <= left or bottom <= top:
            return None
        return left, top, right, bottom

    @staticmethod
    def _normalize_landmarks(landmarks):
        """Convert YuNet landmark output into np.ndarray shape (5, 2)."""
        if landmarks is None:
            return None
        pts = np.asarray(landmarks, dtype=np.float32)
        if pts.size == 10:
            return pts.reshape(5, 2)
        if pts.shape == (5, 2):
            return pts
        return None

    def _normalize_yunet_detection(self, det: Any, image_shape):
        """
        Normalize multiple possible YuNet detector outputs to:
        {box: (top,right,bottom,left), bbox_xyxy, landmarks, detection_confidence}

        Supported shapes:
        - dict with box/bbox, landmarks/kps, confidence/score/det_score
        - OpenCV FaceDetectorYN row: [x, y, w, h, l0x, l0y, ..., l4x, l4y, score]
        - tuple/list: (left, top, right, bottom, confidence, landmarks)
        """
        confidence = 1.0
        landmarks = None

        if isinstance(det, dict):
            raw_box = det.get('box') or det.get('bbox') or det.get('bbox_xyxy')
            confidence = float(det.get('confidence', det.get('score', det.get('det_score', 1.0))))
            landmarks = det.get('landmarks', det.get('kps', det.get('keypoints')))

            if raw_box is None:
                return None

            box = list(map(float, np.asarray(raw_box).flatten().tolist()))
            # Existing project report says YuNet wrapper may return (top,right,bottom,left).
            if len(box) >= 4 and det.get('box') is not None and not det.get('bbox_xyxy'):
                top, right, bottom, left = box[:4]
            else:
                left, top, right, bottom = box[:4]

        else:
            arr = np.asarray(det, dtype=np.float32).flatten()
            if arr.size >= 15:
                # Native OpenCV YuNet: x, y, w, h, 5 landmarks (x,y), score
                x, y, w, h = arr[:4]
                left, top, right, bottom = x, y, x + w, y + h
                landmarks = arr[4:14].reshape(5, 2)
                confidence = float(arr[14])
            elif arr.size >= 4:
                left, top, right, bottom = arr[:4]
                confidence = float(arr[4]) if arr.size >= 5 else 1.0
                landmarks = arr[5:15].reshape(5, 2) if arr.size >= 15 else None
            else:
                return None

        clipped = self._clip_box_xyxy(left, top, right, bottom, image_shape)
        if clipped is None:
            return None

        left, top, right, bottom = clipped
        landmarks = self._normalize_landmarks(landmarks)

        return {
            'box': (top, right, bottom, left),
            'bbox_xyxy': np.array([left, top, right, bottom], dtype=np.float32),
            'landmarks': landmarks,
            'detection_confidence': confidence,
        }

    def _detect_faces_yunet(self, enhanced_bgr):
        """Run YuNet only. Do not use InsightFace internal detector here."""
        if self.yunet_detector is None:
            print('[ArcFace] ❌ YuNet detector is not available')
            return []
    
        # ─── Resize gambar besar agar YuNet tidak false-positive ───
        h, w = enhanced_bgr.shape[:2]
        MAX_DIM = 1280
        scale_back = 1.0
        if max(h, w) > MAX_DIM:
            scale_back = max(h, w) / MAX_DIM
            new_w = int(w / scale_back)
            new_h = int(h / scale_back)
            work_img = cv2.resize(enhanced_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
            print(f'[ArcFace] Resized {w}x{h} → {new_w}x{new_h} (scale_back={scale_back:.2f})')
        else:
            work_img = enhanced_bgr
            scale_back = 1.0
    
        # ─── Akses cv2.FaceDetectorYN langsung (punya landmarks raw) ───
        underlying = getattr(self.yunet_detector, 'detector', None)
        if underlying is None:
            print('[ArcFace] ❌ underlying cv2.FaceDetectorYN not found')
            return []
    
        try:
            wh, ww = work_img.shape[:2]
            underlying.setInputSize((ww, wh))
            _, faces_raw = underlying.detect(work_img)
        except Exception as e:
            print(f'[ArcFace] YuNet detect() failed: {e}')
            return []
    
        if faces_raw is None:
            print('[ArcFace] YuNet: no faces detected')
            return []
    
        normalized = []
        for det in faces_raw:
            # Scale koordinat kembali ke ukuran gambar original
            if scale_back != 1.0:
                det = det.copy()
                # x, y, w, h
                det[0] *= scale_back
                det[1] *= scale_back
                det[2] *= scale_back
                det[3] *= scale_back
                # 5 landmarks (index 4-13)
                det[4:14] *= scale_back
    
            item = self._normalize_yunet_detection(det, enhanced_bgr.shape)
            if item is not None:
                normalized.append(item)
    
        print(f'[ArcFace] YuNet raw detections: {len(faces_raw)}, normalized: {len(normalized)}')
        return normalized

    def _extract_embedding_from_yunet_face(self, image_bgr, face_data: Dict[str, Any]):
        """
        Extract ArcFace embedding from a YuNet-detected face.

        This uses InsightFace recognition model only. Detection is supplied by YuNet
        through bbox + 5 landmarks, so self.arcface_app.get(image) is intentionally
        not used here.
        """
        landmarks = face_data.get('landmarks')
        if landmarks is None:
            print('[ArcFace] YuNet face skipped: 5 landmarks are required for ArcFace alignment')
            return None

        try:
            from insightface.app.common import Face
        except Exception as e:
            print(f'[ArcFace] Unable to import InsightFace Face class: {e}')
            return None

        try:
            recognition_model = self.arcface_app.models.get('recognition')
            if recognition_model is None:
                print('[ArcFace] InsightFace recognition model not found')
                return None

            face_obj = Face(
                bbox=face_data['bbox_xyxy'],
                kps=np.asarray(landmarks, dtype=np.float32),
                det_score=float(face_data.get('detection_confidence', 1.0)),
            )
            recognition_model.get(image_bgr, face_obj)

            emb = getattr(face_obj, 'normed_embedding', None)
            if emb is None:
                emb = getattr(face_obj, 'embedding', None)
            if emb is None:
                return None
            return self._normalize_embedding(emb)
        except Exception as e:
            print(f'[ArcFace] ArcFace embedding extraction failed: {e}')
            return None

    def _extract_faces_arcface(self, bgr_image):
        """
        Return list of dict: box(top,right,bottom,left), embedding(normalized),
        detection_confidence, detector.
        """
        if getattr(self, 'use_clahe', True):
            enhanced_bgr = self._apply_clahe_lab(bgr_image)
        else:
            enhanced_bgr = bgr_image

        use_yunet = getattr(self, 'use_yunet', True)
        use_arcface = getattr(self, 'use_arcface', True)

        extracted = []

        if use_arcface and not use_yunet:
            # 1. ArcFace detector (SCRFD) + ArcFace Recognizer
            if hasattr(self, 'arcface_app') and self.arcface_app is not None:
                faces = self.arcface_app.get(enhanced_bgr)
                for f in faces:
                    emb = getattr(f, 'normed_embedding', getattr(f, 'embedding', None))
                    if emb is None: continue
                    bbox = f.bbox.astype(int).tolist()
                    box = (bbox[1], bbox[2], bbox[3], bbox[0]) # top, right, bottom, left
                    extracted.append({
                        'box': box,
                        'embedding': self._normalize_embedding(emb),
                        'detection_confidence': float(getattr(f, 'det_score', 1.0)),
                        'landmarks': getattr(f, 'kps', None),
                        'detector': 'scrfd',
                    })
        elif use_arcface and use_yunet:
            # 2. YuNet detector + ArcFace Recognizer (The default)
            yunet_faces = self._detect_faces_yunet(enhanced_bgr)
            for face_data in yunet_faces:
                emb = self._extract_embedding_from_yunet_face(enhanced_bgr, face_data)
                if emb is None: continue
                extracted.append({
                    'box': face_data['box'],
                    'embedding': emb,
                    'detection_confidence': float(face_data.get('detection_confidence', 1.0)),
                    'landmarks': face_data.get('landmarks'),
                    'detector': 'yunet',
                })
        elif not use_arcface and use_yunet:
            # 3. YuNet detector + dlib/face_recognition Recognizer
            import face_recognition
            yunet_faces = self._detect_faces_yunet(enhanced_bgr)
            rgb_image = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
            
            for face_data in yunet_faces:
                box = face_data['box'] # (top, right, bottom, left)
                encodings = face_recognition.face_encodings(rgb_image, [box])
                if encodings:
                    emb = self._normalize_embedding(encodings[0])
                    extracted.append({
                        'box': box,
                        'embedding': emb,
                        'detection_confidence': float(face_data.get('detection_confidence', 1.0)),
                        'landmarks': face_data.get('landmarks'),
                        'detector': 'yunet+dlib',
                    })
        elif not use_arcface and not use_yunet:
            # 4. dlib detector + dlib recognizer (Classic mode)
            import face_recognition
            rgb_image = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
            boxes = face_recognition.face_locations(rgb_image)
            if boxes:
                encodings = face_recognition.face_encodings(rgb_image, boxes)
                for box, emb in zip(boxes, encodings):
                    extracted.append({
                        'box': box,
                        'embedding': self._normalize_embedding(emb),
                        'detection_confidence': 1.0,
                        'landmarks': None,
                        'detector': 'dlib/hog',
                    })
                    
        return extracted

    def _enhance_for_detection(self, image, aggressive=False):
        """Compatibility helper kept for routes/diagnostics; returns RGB image."""
        try:
            if len(image.shape) == 3 and image.shape[2] == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image

            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced_gray = clahe.apply(gray)
            denoised = cv2.fastNlMeansDenoising(enhanced_gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
            kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened = cv2.filter2D(denoised, -1, kernel_sharpening)

            if len(image.shape) == 3 and image.shape[2] == 3:
                enhanced_rgb = cv2.cvtColor(sharpened, cv2.COLOR_GRAY2RGB)
                return cv2.addWeighted(enhanced_rgb, 0.7, image, 0.3, 0)
            return sharpened
        except Exception:
            return image

    def register_new_student(self, student_id, student_name, images_dir):
        """Register student by averaging ArcFace embeddings from valid images."""
        try:
            if not os.path.exists(images_dir):
                return False, 'Images directory not found'

            embeddings = []
            valid_images = 0

            for filename in os.listdir(images_dir):
                if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    continue

                image_path = os.path.join(images_dir, filename)
                image = cv2.imread(image_path)
                if image is None:
                    continue

                faces = self._extract_faces_arcface(image)
                if len(faces) == 1:
                    embeddings.append(faces[0]['embedding'])
                    valid_images += 1
                elif len(faces) > 1:
                    print(f'[ArcFace] Warning: Multiple faces in {filename}, skipped')
                else:
                    print(f'[ArcFace] Warning: No face found in {filename}, skipped')

            if valid_images < 1:
                return False, 'No valid face images found'

            if valid_images < 3:
                return False, f'Please provide at least 3 clear face images (found {valid_images})'

            avg_embedding = self._normalize_embedding(np.mean(np.array(embeddings), axis=0))
            student_key = f'{student_name}_{student_id}'

            if student_key in self.known_face_names:
                idx = self.known_face_names.index(student_key)
                self.known_face_encodings[idx] = avg_embedding
            else:
                self.known_face_names.append(student_key)
                self.known_face_encodings.append(avg_embedding)

            self.save_encodings()
            return True, f'Successfully registered {student_name} with ArcFace using {valid_images} images'

        except Exception as e:
            return False, f'Error registering student: {str(e)}'

    def recognize_face(self, image_input, require_liveness=True):
        """Recognize one or more faces using ArcFace embeddings + cosine similarity."""
        try:
            if isinstance(image_input, str):
                if not os.path.exists(image_input):
                    return {'success': False, 'message': 'Image file not found'}
                bgr_image = cv2.imread(image_input)
                if bgr_image is None:
                    return {'success': False, 'message': 'Unable to load image file'}
            else:
                bgr_image = image_input

            if bgr_image is None:
                return {'success': False, 'message': 'Invalid image input'}

            faces = self._extract_faces_arcface(bgr_image)
            if not faces:
                return {
                    'success': False,
                    'message': 'No face detected in image. Please move closer to the camera or ensure good lighting.'
                }

            if not self.known_face_encodings:
                return {'success': False, 'message': 'No registered faces found'}

            known_matrix = np.vstack(self.known_face_encodings).astype(np.float32)
            min_similarity = max(0.0, 1.0 - self.distance_threshold)

            all_matches = []

            for idx, face in enumerate(faces):
                emb = face['embedding']
                similarities = known_matrix @ emb  # cosine sim because normalized
                best_idx = int(np.argmax(similarities))
                best_similarity = float(similarities[best_idx])

                confidence_score = max(0.0, min(1.0, best_similarity))
                distance_score = 1.0 - best_similarity

                face_size_ratio = self._face_size_ratio(face['box'], bgr_image.shape)
                min_conf, size_category = self._get_adaptive_min_confidence(face_size_ratio)

                print(f'[ArcFace] Face #{idx+1}: best_similarity={best_similarity:.4f}, confidence={confidence_score:.2%}, size={size_category}')

                if best_similarity < min_similarity:
                    print(f'[ArcFace] ❌ below similarity threshold: {best_similarity:.4f} < {min_similarity:.4f}')
                    continue

                if confidence_score < min_conf:
                    print(f'[ArcFace] ❌ below adaptive confidence: {confidence_score:.2%} < {min_conf:.2%}')
                    continue

                student_info = self.known_face_names[best_idx]
                name, student_id = student_info.rsplit('_', 1)

                # Get lighting score
                top, right, bottom, left = face['box']
                face_crop = bgr_image[max(0, top):max(0, bottom), max(0, left):max(0, right)]
                if face_crop.size > 0:
                    hsv = cv2.cvtColor(face_crop, cv2.COLOR_BGR2HSV)
                    lighting_score = float(np.mean(hsv[:, :, 2]))
                else:
                    lighting_score = 127.0

                detection_confidence = float(face.get('detection_confidence', 1.0))
                all_matches.append({
                    'name': name,
                    'student_id': student_id,
                    'confidence': confidence_score,  # backward-compatible alias for recognition_score
                    'recognition_score': confidence_score,
                    'similarity': best_similarity,
                    'distance': distance_score,
                    'detection_confidence': detection_confidence,
                    'threshold': max(min_similarity, min_conf),
                    'face_size': face_size_ratio,
                    'lighting_score': lighting_score,
                    'face_index': idx,
                    'detector': face.get('detector', 'yunet')
                })

            if not all_matches:
                if len(faces) > 1:
                    return {
                        'success': False,
                        'message': f'Found {len(faces)} faces but none matched registered students. Please move closer to camera.'
                    }
                return {
                    'success': False,
                    'message': 'Face not recognized. Please ensure good lighting and move closer to camera.'
                }

            # Best candidate: highest confidence
            all_matches.sort(key=lambda x: x['confidence'], reverse=True)
            best_match = all_matches[0]

            # Light ambiguous check (ArcFace similarities very close)
            if len(self.known_face_encodings) > 1:
                emb = faces[best_match['face_index']]['embedding']
                similarities = known_matrix @ emb
                sorted_sims = np.sort(similarities)[::-1]
                if len(sorted_sims) > 1:
                    sim_gap = float(sorted_sims[0] - sorted_sims[1])
                    is_ambiguous = sim_gap < 0.03 and best_match['confidence'] < 0.62
                    if is_ambiguous:
                        return {
                            'success': False,
                            'message': 'Ambiguous recognition - multiple similar matches found. Please re-register with more diverse photos.'
                        }

            name = best_match['name']
            student_id = best_match['student_id']
            confidence_score = best_match['confidence']
            recognition_score = best_match['recognition_score']
            detection_confidence = best_match['detection_confidence']
            applied_threshold = best_match['threshold']
            face_size_ratio = best_match['face_size']
            lighting_score = best_match['lighting_score']
            _, size_category = self._get_adaptive_min_confidence(face_size_ratio)

            all_faces_data = []
            for i, m in enumerate(all_matches, start=1):
                all_faces_data.append({
                    'name': m['name'],
                    'student_id': m['student_id'],
                    'confidence': m['confidence'],
                    'recognition_score': m['recognition_score'],
                    'similarity': m['similarity'],
                    'distance': m['distance'],
                    'detection_confidence': m['detection_confidence'],
                    'threshold': m['threshold'],
                    'face_size': m['face_size'],
                    'lighting_score': m['lighting_score'],
                    'detector': m['detector'],
                    'position': i
                })

            return {
                'success': True,
                'faces_detected': len(all_matches),
                'multiple_faces': len(all_matches) > 1,
                'student': {
                    'name': name,
                    'student_id': student_id,
                    'id': student_id
                },
                'confidence': confidence_score,  # backward-compatible alias
                'recognition_score': recognition_score,
                'similarity': best_match['similarity'],
                'distance': best_match['distance'],
                'detection_confidence': detection_confidence,
                'threshold': applied_threshold,
                'face_size': face_size_ratio,
                'lighting_score': lighting_score,
                'all_faces': all_faces_data,
                'verification_details': {
                    'engine': 'yunet+arcface',
                    'detector': 'yunet',
                    'recognizer': 'arcface',
                    'face_count': len(faces),
                    'detected_faces': len(all_matches),
                    'face_size_category': size_category,
                    'encoding_quality': 'excellent' if confidence_score > 0.8 else 'good' if confidence_score > 0.65 else 'acceptable',
                    'liveness_verified': False,
                    'security_level': 'basic'
                },
                'liveness_details': None
            }

        except Exception as e:
            return {'success': False, 'message': f'Recognition error: {str(e)}'}

    def save_encodings(self):
        try:
            data = {
                'version': 1,
                'engine': 'arcface',
                'encodings': self.known_face_encodings,
                'names': self.known_face_names
            }
            with open(self.embeddings_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f'[ArcFace] Error saving encodings: {e}')
            return False

    def load_encodings(self):
        try:
            if os.path.exists(self.embeddings_path):
                with open(self.embeddings_path, 'rb') as f:
                    data = pickle.load(f)
                self.known_face_encodings = data.get('encodings', [])
                self.known_face_names = data.get('names', [])
                return True
            self.known_face_encodings = []
            self.known_face_names = []
            return False
        except Exception as e:
            print(f'[ArcFace] Error loading encodings: {e}')
            self.known_face_encodings = []
            self.known_face_names = []
            return False

    def get_registered_count(self):
        return len(self.known_face_names)

    def remove_student(self, student_id):
        try:
            idxs = [i for i, name in enumerate(self.known_face_names) if name.endswith(f'_{student_id}')]
            for i in reversed(idxs):
                del self.known_face_names[i]
                del self.known_face_encodings[i]
            self.save_encodings()
            return True
        except Exception as e:
            print(f'[ArcFace] Error removing student: {e}')
            return False
