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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, 0.0
        
        # Calculate average edge density as proxy for distance
        edge_density = np.sum(edges > 0) / edges.size
        
        # Motion detection
        if self.prev_frame is not None:
            diff = cv2.absdiff(gray, self.prev_frame)
            motion = np.sum(diff > 30) / diff.size
        else:
            motion = 0.0
        
        self.prev_frame = gray.copy()
        
        # Combine metrics for distance estimation
        # Higher edge density and motion = closer object
        combined_score = (edge_density * 0.6 + motion * 0.4)
        
        # Map score to distance range (0-6 feet = 0-1.83 meters)
        if combined_score < 0.05:
            return None, 0.0
        
        distance = MAX_DISTANCE - (combined_score * MAX_DISTANCE)
        distance = np.clip(distance, MIN_DISTANCE, MAX_DISTANCE)
        confidence = np.clip(combined_score, 0.0, 1.0)
        
        # Apply confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
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
