# Face Recognition System Configuration

# Security and Accuracy Settings
FACE_RECOGNITION_CONFIG = {
    # Recognition Thresholds
    'confidence_threshold': 0.45,  # Lower = more strict (fewer false positives)
    'min_confidence_for_attendance': 0.65,  # Minimum confidence for attendance marking
    
    # Registration Requirements
    'min_registration_images': 3,  # Minimum images required for registration
    'recommended_registration_images': 5,  # Recommended for best accuracy
    
    # Security Features
    'require_single_face_only': True,  # Reject images with multiple faces
    'check_ambiguous_matches': True,   # Check for similar matches
    'ambiguous_threshold': 0.15,      # Distance threshold for ambiguous detection
    
    # Image Quality
    'min_image_quality': 0.3,         # Minimum image quality score
    'recommended_image_quality': 0.6,  # Recommended quality
    
    # Anti-Spoofing
    'enable_anti_spoofing': True,      # Enable liveness detection
    'require_liveness_check': False,   # Set to True for production
    'liveness_confidence_threshold': 0.8,
    
    # Performance
    'use_cnn_model': False,           # Use CNN model for detection (slower but more accurate)
    'use_large_model': False,         # Use large model for encoding (slower but more accurate)
    'face_detection_model': 'hog',    # 'hog' (fast) or 'cnn' (accurate)
    'face_encoding_model': 'small',   # 'small' (fast) or 'large' (accurate)
    
    # Logging and Debugging
    'enable_detailed_logging': True,
    'log_recognition_attempts': True,
    'save_failed_attempts': False,     # Save images of failed attempts for analysis
    
    # Dynamic Thresholds
    'enable_dynamic_threshold': True,  # Adjust threshold based on image quality
    'quality_threshold_adjustment': 0.05,  # How much to adjust based on quality
    
    # Time-based Security
    'min_time_between_recognitions': 10,  # Seconds between recognitions for same person
    'max_attempts_per_minute': 5,         # Maximum recognition attempts per minute
    
    # Database Settings
    'attendance_method': 'face_recognition',
    'confidence_decimal_places': 3,
    
    # UI Settings
    'show_confidence_to_user': True,
    'show_debug_info': False,  # Set to True for troubleshooting
    'display_recognition_details': True
}

# Error Messages
ERROR_MESSAGES = {
    'no_face_detected': 'No face detected. Please ensure your face is clearly visible.',
    'multiple_faces': 'Multiple faces detected. Please ensure only one person is in the frame.',
    'low_confidence': 'Recognition confidence too low. Please ensure good lighting and face the camera directly.',
    'ambiguous_match': 'Ambiguous recognition detected. Please re-register with more diverse photos.',
    'not_registered': 'Face not recognized. Please register first.',
    'poor_image_quality': 'Image quality too low. Please ensure good lighting and clear image.',
    'liveness_failed': 'Liveness detection failed. Please blink naturally and move slightly.',
    'too_frequent': 'Too many recognition attempts. Please wait a moment.',
    'system_error': 'System error occurred. Please try again or contact support.'
}

# Success Messages
SUCCESS_MESSAGES = {
    'registration_complete': 'Face registration completed successfully with {count} images.',
    'attendance_marked': 'Attendance marked successfully for {name} with {confidence:.1%} confidence.',
    'recognition_successful': 'Face recognized: {name} (Confidence: {confidence:.1%})'
}

# Validation Rules
VALIDATION_RULES = {
    'image_formats': ['.jpg', '.jpeg', '.png'],
    'max_image_size_mb': 10,
    'min_image_resolution': (100, 100),
    'max_image_resolution': (2048, 2048),
    'required_face_size_pixels': 50  # Minimum face size in pixels
}

# Performance Profiles
PERFORMANCE_PROFILES = {
    'fast': {
        'face_detection_model': 'hog',
        'face_encoding_model': 'small',
        'confidence_threshold': 0.5,
        'enable_anti_spoofing': False,
        'use_dynamic_threshold': False
    },
    'balanced': {
        'face_detection_model': 'hog',
        'face_encoding_model': 'small',
        'confidence_threshold': 0.45,
        'enable_anti_spoofing': True,
        'use_dynamic_threshold': True
    },
    'accurate': {
        'face_detection_model': 'cnn',
        'face_encoding_model': 'large',
        'confidence_threshold': 0.4,
        'enable_anti_spoofing': True,
        'use_dynamic_threshold': True,
        'min_registration_images': 5
    },
    'secure': {
        'face_detection_model': 'cnn',
        'face_encoding_model': 'large',
        'confidence_threshold': 0.35,
        'min_confidence_for_attendance': 0.75,
        'enable_anti_spoofing': True,
        'require_liveness_check': True,
        'use_dynamic_threshold': True,
        'min_registration_images': 5,
        'check_ambiguous_matches': True
    },
    # PROFILE KHUSUS untuk kondisi kelas dengan:
    # - Jarak jauh (wajah kecil)
    # - Backlight / pencahayaan buruk
    # - Substream / resolusi rendah
    'classroom': {
        'face_detection_model': 'cnn',  # CNN lebih baik untuk wajah kecil
        'face_encoding_model': 'large',  # Large model lebih akurat
        'confidence_threshold': 0.55,    # Lebih toleran
        'min_confidence_for_attendance': 0.50,  # Lebih rendah untuk kondisi sulit
        'enable_anti_spoofing': False,   # Disable untuk kecepatan
        'use_dynamic_threshold': True,
        'check_ambiguous_matches': False,  # Disable untuk kondisi sulit
        'min_registration_images': 3,
        'required_face_size_pixels': 30,   # Terima wajah lebih kecil
        'enable_image_enhancement': True,  # Aktifkan enhancement
        'upsample_times': 2               # Upscale frame untuk deteksi lebih baik
    }
}

def get_config(profile='balanced'):
    """
    Get configuration for specified performance profile
    """
    base_config = FACE_RECOGNITION_CONFIG.copy()
    
    if profile in PERFORMANCE_PROFILES:
        base_config.update(PERFORMANCE_PROFILES[profile])
    
    return base_config

def update_config(config_updates):
    """
    Update configuration with new values
    """
    FACE_RECOGNITION_CONFIG.update(config_updates)
    return FACE_RECOGNITION_CONFIG