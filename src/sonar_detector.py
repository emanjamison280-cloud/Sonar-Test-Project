"""Sonar detection module for distance estimation using webcam"""

import cv2
import numpy as np
from config.config import (
    MAX_DISTANCE, MIN_DISTANCE, DISTANCE_THRESHOLD, CONFIDENCE_THRESHOLD
)


class SonarDetector:
    """Detects depth/distance from webcam input using motion and contrast analysis"""
    
    def __init__(self):
        self.prev_frame = None
        self.detected_distances = []
        self.wave_history = []
        self.frame_count = 0
        
    def estimate_distance(self, frame):
        """
        Estimate distance based on frame analysis.
        Uses edge detection and motion to simulate sonar ranging.
        
        Args:
            frame: Input frame from camera
            
        Returns:
            distance: Estimated distance in meters (0-6 feet)
            confidence: Confidence level of detection (0-1)
        """
        self.frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection with more sensitive thresholds
        edges = cv2.Canny(blurred, 30, 100)
        
        # Dilate edges to connect nearby edges
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Calculate edge density as proxy for distance
        edge_density = np.sum(edges > 0) / edges.size
        
        # Motion detection - compare with previous frame
        motion_score = 0.0
        if self.prev_frame is not None:
            diff = cv2.absdiff(blurred, self.prev_frame)
            # More sensitive motion threshold
            motion = np.sum(diff > 15) / diff.size
            motion_score = motion
        
        self.prev_frame = blurred.copy()
        
        # Combined score: favor motion detection
        # If there's movement, it's a strong detection
        combined_score = (edge_density * 0.3 + motion_score * 0.7)
        
        # Lower threshold for detection
        if combined_score < 0.02:
            return None, 0.0
        
        # Map score to distance range
        # Higher score = more motion/edges = object is closer
        distance = MAX_DISTANCE * (1.0 - np.clip(combined_score, 0, 1.0))
        distance = np.clip(distance, MIN_DISTANCE, MAX_DISTANCE)
        confidence = np.clip(combined_score, 0.0, 1.0)
        
        # Lower confidence threshold for better detection
        if confidence < 0.05:
            return None, confidence
        
        return distance, confidence
    
    def get_detected_distances(self):
        """Return list of recently detected distances"""
        return self.detected_distances.copy()
    
    def add_detection(self, distance, confidence):
        """Add a new detection to history"""
        if distance is not None:
            self.detected_distances.append({
                'distance': distance,
                'confidence': confidence
            })
            # Keep only last 30 detections
            if len(self.detected_distances) > 30:
                self.detected_distances.pop(0)
    
    def get_average_distance(self, window_size=5):
        """Get averaged distance from recent detections"""
        if not self.detected_distances:
            return None
        
        recent = self.detected_distances[-window_size:]
        distances = [d['distance'] for d in recent]
        return np.mean(distances) if distances else None
