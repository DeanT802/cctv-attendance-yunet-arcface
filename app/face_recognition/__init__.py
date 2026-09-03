"""
Advanced Face Recognition Module for Attendance System.

Primary engine: ArcFace (InsightFace)
Fallback engine: legacy dlib/face_recognition implementation
"""

# Import components individually to avoid import errors
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

# Use ArcFace as primary
try:
    from .arcface_recognition import CNNFaceRecognition
except ImportError:
    # Fallback to legacy dlib engine if ArcFace dependency is unavailable
    try:
        from .simple_face_recognition import CNNFaceRecognition
    except ImportError:
        try:
            from .cnn_face_recognition import CNNFaceRecognition
        except ImportError:
            CNNFaceRecognition = None

__all__ = [
    'FaceAligner',
    'AntiSpoofing',
    'FaceAugmenter',
    'CNNFaceRecognition'
]

__version__ = '1.0.0'
__author__ = 'Attendance System'
__description__ = 'ArcFace-first Face Recognition with backward-compatible fallback'
