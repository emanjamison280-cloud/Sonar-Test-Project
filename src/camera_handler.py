"""Camera capture and frame preprocessing"""

import cv2
import numpy as np
from config.config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS


class CameraHandler:
    """Handles webcam capture and frame preprocessing"""
    
    def __init__(self, camera_index=CAMERA_INDEX):
        self.cap = cv2.VideoCapture(camera_index)
        self.setup_camera()
        
    def setup_camera(self):
        """Configure camera settings"""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        
    def get_frame(self):
        """
        Capture and return a frame from camera
        
        Returns:
            frame: Captured frame or None if failed
            success: Boolean indicating if frame was successfully captured
        """
        success, frame = self.cap.read()
        return frame, success
    
    def preprocess_frame(self, frame):
        """
        Preprocess frame for sonar detection
        
        Args:
            frame: Raw camera frame
            
        Returns:
            processed_frame: Enhanced frame
        """
        # Improve contrast using CLAHE
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        processed = cv2.merge([l, a, b])
        processed = cv2.cvtColor(processed, cv2.COLOR_LAB2BGR)
        
        return processed
    
    def release(self):
        """Release camera resource"""
        self.cap.release()
