import cv2
import numpy as np
import albumentations as A
from albumentations.pytorch import ToTensorV2
import random
from PIL import Image, ImageEnhance
import os

class FaceAugmenter:
    """
    Advanced data augmentation for face recognition training
    """
    
    def __init__(self, output_size=(128, 128)):
        self.output_size = output_size
        
        # Define augmentation pipeline
        self.augmentation_pipeline = A.Compose([
            # Geometric transformations
            A.Rotate(limit=15, p=0.7),
            A.HorizontalFlip(p=0.5),
            A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=10, p=0.7),
            
            # Color and lighting augmentations
            A.RandomBrightnessContrast(brightness_limit=0.2, contrast_limit=0.2, p=0.7),
            A.HueSaturationValue(hue_shift_limit=10, sat_shift_limit=20, val_shift_limit=20, p=0.6),
            A.CLAHE(clip_limit=2.0, tile_grid_size=(8, 8), p=0.5),
            A.RandomGamma(gamma_limit=(80, 120), p=0.5),
            
            # Noise and blur
            A.GaussNoise(var_limit=(10.0, 50.0), p=0.4),
            A.OneOf([
                A.MotionBlur(blur_limit=3, p=0.3),
                A.GaussianBlur(blur_limit=3, p=0.3),
                A.MedianBlur(blur_limit=3, p=0.3),
            ], p=0.4),
            
            # Weather and environmental effects
            A.OneOf([
                A.RandomShadow(shadow_roi=(0, 0.5, 1, 1), num_shadows_lower=1, num_shadows_upper=2, p=0.3),
                A.RandomSunFlare(flare_roi=(0, 0, 1, 0.5), angle_lower=0, angle_upper=1, p=0.2),
            ], p=0.3),
            
            # Resize to output size
            A.Resize(height=output_size[0], width=output_size[1]),
            
            # Normalization
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        # Lighter augmentation for validation
        self.validation_pipeline = A.Compose([
            A.Resize(height=output_size[0], width=output_size[1]),
            A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    
    def augment_image(self, image, training=True):
        """
        Apply augmentation to a single image
        """
        if isinstance(image, str):
            image = cv2.imread(image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        if training:
            augmented = self.augmentation_pipeline(image=image)
        else:
            augmented = self.validation_pipeline(image=image)
        
        return augmented['image']
    
    def create_augmented_dataset(self, input_dir, output_dir, augmentations_per_image=10):
        """
        Create augmented dataset from input directory
        """
        os.makedirs(output_dir, exist_ok=True)
        
        for student_id in os.listdir(input_dir):
            student_input_path = os.path.join(input_dir, student_id)
            student_output_path = os.path.join(output_dir, student_id)
            
            if not os.path.isdir(student_input_path):
                continue
            
            os.makedirs(student_output_path, exist_ok=True)
            
            image_files = [f for f in os.listdir(student_input_path) 
                          if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            for image_file in image_files:
                image_path = os.path.join(student_input_path, image_file)
                
                try:
                    # Load original image
                    image = cv2.imread(image_path)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Save original
                    original_output = os.path.join(student_output_path, f"original_{image_file}")
                    cv2.imwrite(original_output, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
                    
                    # Generate augmented versions
                    for i in range(augmentations_per_image):
                        augmented = self.augment_image(image, training=True)
                        
                        # Convert back to BGR for saving
                        if augmented.dtype == np.float32 or augmented.dtype == np.float64:
                            # Denormalize
                            mean = np.array([0.485, 0.456, 0.406])
                            std = np.array([0.229, 0.224, 0.225])
                            augmented = augmented * std + mean
                            augmented = np.clip(augmented * 255, 0, 255).astype(np.uint8)
                        
                        augmented_bgr = cv2.cvtColor(augmented, cv2.COLOR_RGB2BGR)
                        
                        # Save augmented image
                        base_name = os.path.splitext(image_file)[0]
                        ext = os.path.splitext(image_file)[1]
                        augmented_name = f"{base_name}_aug_{i:03d}{ext}"
                        augmented_path = os.path.join(student_output_path, augmented_name)
                        
                        cv2.imwrite(augmented_path, augmented_bgr)
                        
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
        
        print(f"Augmented dataset created in {output_dir}")
    
    def generate_hard_negatives(self, face_images, num_negatives=100):
        """
        Generate hard negative samples for training
        """
        hard_negatives = []
        
        for _ in range(num_negatives):
            # Random crop from face images
            img = random.choice(face_images)
            h, w = img.shape[:2]
            
            # Random crop that doesn't contain the full face
            crop_size = min(h, w) // 3
            x = random.randint(0, w - crop_size)
            y = random.randint(0, h - crop_size)
            
            crop = img[y:y+crop_size, x:x+crop_size]
            crop_resized = cv2.resize(crop, self.output_size)
            
            hard_negatives.append(crop_resized)
        
        return hard_negatives
    
    def apply_lighting_variations(self, image):
        """
        Apply various lighting conditions
        """
        variations = []
        
        # Original
        variations.append(image)
        
        # Brightness variations
        for factor in [0.7, 0.8, 1.2, 1.3]:
            bright = cv2.convertScaleAbs(image, alpha=factor, beta=0)
            variations.append(bright)
        
        # Contrast variations
        for factor in [0.8, 1.2]:
            contrast = cv2.convertScaleAbs(image, alpha=factor, beta=0)
            variations.append(contrast)
        
        # Gamma correction
        for gamma in [0.8, 1.2]:
            gamma_corrected = np.power(image / 255.0, gamma)
            gamma_corrected = np.uint8(gamma_corrected * 255)
            variations.append(gamma_corrected)
        
        return variations
    
    def simulate_camera_conditions(self, image):
        """
        Simulate different camera and environmental conditions
        """
        conditions = []
        
        # Original
        conditions.append(image)
        
        # Add noise (simulating low-light conditions)
        noise = np.random.normal(0, 25, image.shape).astype(np.uint8)
        noisy = cv2.add(image, noise)
        conditions.append(noisy)
        
        # Blur (simulating motion or focus issues)
        blurred = cv2.GaussianBlur(image, (3, 3), 0)
        conditions.append(blurred)
        
        # Color temperature variations
        # Warmer (more red/yellow)
        warm = image.copy().astype(np.float32)
        warm[:, :, 0] *= 1.1  # Blue channel
        warm[:, :, 2] *= 0.9  # Red channel
        warm = np.clip(warm, 0, 255).astype(np.uint8)
        conditions.append(warm)
        
        # Cooler (more blue)
        cool = image.copy().astype(np.float32)
        cool[:, :, 0] *= 0.9  # Blue channel
        cool[:, :, 2] *= 1.1  # Red channel
        cool = np.clip(cool, 0, 255).astype(np.uint8)
        conditions.append(cool)
        
        return conditions
